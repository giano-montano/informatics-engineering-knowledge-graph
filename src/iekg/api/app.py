"""The API application: operation routes under ``/api`` and the documents under ``/resources``.

The API never writes in the graph (ADR-007). The operation routes record runs
and launch the worker; ``/resources`` only reads. What the tests replace —
the worker launcher and the graph lookup — comes in through ``ApiContext``.
"""

import secrets
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Protocol
from uuid import UUID

from fastapi import APIRouter, Depends, FastAPI, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from iekg.api.models import (
    AuditGate,
    AuditReportView,
    LatestAuditReport,
    RunDetail,
    RunDiscards,
    RunSummary,
    SubmittedRun,
)
from iekg.ingestion.orchestrator import document_path, gate_closed_by
from iekg.ingestion.submission import SubmissionError, submit_document
from iekg.operational_store import OperationalStore


class WorkerLauncher(Protocol):
    def ensure_running(self) -> bool:
        """Launch the worker unless one is active; True if this call launched it."""
        ...


class ResourceIndex(Protocol):
    def has_resource(self, key: str) -> bool:
        """Whether the graph has an institutional learning resource with this key."""
        ...


@dataclass(frozen=True)
class ApiContext:
    operator_token: str
    operational_db: Path
    documents_dir: Path
    worker: WorkerLauncher
    resources: ResourceIndex

    def store(self) -> OperationalStore:
        # Opened and closed inside each endpoint, not in a dependency: a sqlite3
        # connection refuses another thread, and FastAPI may run a dependency
        # and its endpoint in different threads of its pool.
        return OperationalStore(self.operational_db)


def create_app(context: ApiContext) -> FastAPI:
    app = FastAPI(
        title="IEKG API",
        summary="Knowledge graph of the Informatics Engineering curriculum: operation and documents.",
        version="0.1.0",
    )
    app.include_router(operations_router(context), prefix="/api")
    app.include_router(documents_router(context))
    return app


def _operator_guard(token: str):
    bearer = HTTPBearer(auto_error=False, description="The operator token (ADR-013).")

    def require_operator(credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)]) -> None:
        if credentials is None or not secrets.compare_digest(credentials.credentials.encode(), token.encode()):
            raise HTTPException(401, "missing or wrong operator token", headers={"WWW-Authenticate": "Bearer"})

    return require_operator


def operations_router(context: ApiContext) -> APIRouter:
    """Submission, run state, discards and audit report (RF-02, RF-03, RF-05, RF-23)."""
    router = APIRouter(tags=["operation"], dependencies=[Depends(_operator_guard(context.operator_token))])

    @router.post("/runs", status_code=202, responses={422: {"description": "Not a PDF, or a declaration it lacks"}})
    def submit_run(
        file: UploadFile,
        resource_type: Annotated[str, Form()],
        course_code: Annotated[str, Form()],
        course_name: Annotated[str, Form()],
    ) -> SubmittedRun:
        """Record a pending run for the document and launch the worker if none is active (ADR-007)."""
        with context.store() as store:
            try:
                run_id = submit_document(
                    store, context.documents_dir, file.file, file_name=file.filename or "",
                    resource_type=resource_type, course_code=course_code, course_name=course_name,
                )
            except SubmissionError as error:
                raise HTTPException(422, str(error)) from error
        return SubmittedRun(run_id=run_id, worker_launched=context.worker.ensure_running())

    @router.get("/runs")
    def list_runs() -> list[RunSummary]:
        with context.store() as store:
            return [RunSummary.of(run) for run in store.list_runs()]

    @router.get("/runs/{run_id}", responses={404: {"description": "No such run"}})
    def get_run(run_id: int) -> RunDetail:
        """The run as recorded, with the audit report that closed it if it wrote."""
        with context.store() as store:
            run = _run_or_404(store, run_id)
            report = store.audit_report(run.audit_report_id) if run.audit_report_id is not None else None
        return RunDetail.of(run, report)

    @router.get("/runs/{run_id}/discards", responses={404: {"description": "No such run"}})
    def get_discards(run_id: int) -> RunDiscards:
        """What a rejected run discarded; empty for a run that was not rejected."""
        with context.store() as store:
            _run_or_404(store, run_id)
            try:
                batch, raw_output = store.rejected_output_of(run_id)
            except KeyError:
                batch, raw_output = None, None
            return RunDiscards.of(store.discards_of(run_id), batch, raw_output)

    @router.get("/audit-reports/latest")
    def latest_audit_report() -> LatestAuditReport:
        """The latest audit report and the state of the audit gate it sets (ADR-007)."""
        with context.store() as store:
            latest = store.latest_audit_report()
        reason = gate_closed_by(latest)
        return LatestAuditReport(
            gate=AuditGate(state="closed" if reason else "open", reason=reason),
            report=AuditReportView.of(latest) if latest else None,
        )

    return router


def documents_router(context: ApiContext) -> APIRouter:
    """The document of each institutional learning resource, at its locator (RF-24, ADR-009). Public."""
    router = APIRouter(tags=["navigation"])

    @router.get(
        "/resources/{key}",
        response_class=FileResponse,
        responses={200: {"content": {"application/pdf": {}}}, 404: {"description": "Not a resource of the graph"}},
    )
    def get_document(key: UUID) -> FileResponse:
        """Served only while the graph has the resource: after a load, not until the reapplication."""
        path = document_path(context.documents_dir, str(key))
        if not context.resources.has_resource(str(key)) or not path.is_file():
            raise HTTPException(404, "no such resource")
        # No file name, so no Content-Disposition: the browser shows the PDF.
        return FileResponse(path, media_type="application/pdf")

    return router


def _run_or_404(store: OperationalStore, run_id: int):
    try:
        return store.get_run(run_id)
    except KeyError as error:
        raise HTTPException(404, f"run {run_id} does not exist") from error
