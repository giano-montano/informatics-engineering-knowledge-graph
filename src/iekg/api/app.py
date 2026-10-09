"""The API application: operation and navigation routes under ``/api``, and the documents under ``/resources``.

The API never writes in the graph (ADR-007). The operation routes record runs
and launch the worker; the navigation routes and ``/resources`` only read.
What the tests replace — the worker launcher, the graph lookup and the
navigation queries — comes in through ``ApiContext``.
"""

import secrets
import sys
from contextlib import asynccontextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Protocol
from uuid import UUID

from fastapi import APIRouter, Depends, FastAPI, Form, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from iekg.api.models import (
    AuditGate,
    AuditReportView,
    LatestAuditReport,
    RunDetail,
    RunDiscards,
    RunSummary,
    SubgraphView,
    SubmittedRun,
)
from iekg.api import navigation
from iekg.api.navigation import Grain, Subgraph
from iekg.ingestion.orchestrator import document_path, gate_closed_by, has_work
from iekg.ingestion.submission import SubmissionError, submit_document, withdraw_submission
from iekg.operational_store import OperationalStore


class WorkerLauncher(Protocol):
    def ensure_running(self) -> bool:
        """Launch the worker unless one is active; True if this call launched it.

        Raises ``OSError`` if the process cannot be started.
        """
        ...


class ResourceIndex(Protocol):
    def has_resource(self, key: str) -> bool:
        """Whether the graph has an institutional learning resource with this key."""
        ...


class GraphNavigation(Protocol):
    def fetch(self, query: navigation.Query) -> Subgraph | None:
        """The subgraph the query returns; None if its starting node is not there."""
        ...

    def stopwords(self) -> frozenset[str]:
        """The stop words of the search index's analyzer."""
        ...


@dataclass(frozen=True)
class ApiContext:
    operator_token: str
    operational_db: Path
    documents_dir: Path
    worker: WorkerLauncher
    resources: ResourceIndex
    navigation: GraphNavigation

    def store(self) -> OperationalStore:
        # Opened and closed inside each endpoint, not in a dependency: a sqlite3
        # connection refuses another thread, and FastAPI may run a dependency
        # and its endpoint in different threads of its pool.
        return OperationalStore(self.operational_db)


def work_waiting(operational_db: Path) -> bool:
    """Whether a worker launched now would take a run (ADR-007)."""
    with OperationalStore(operational_db) as store:
        return has_work(store)


def create_app(context: ApiContext) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # Picks up what stayed pending with the gate closed: the build
        # processes run with the system stopped (ADR-007).
        if work_waiting(context.operational_db):
            try:
                context.worker.ensure_running()
            except OSError as error:
                print(f"error: could not launch the worker: {error}", file=sys.stderr)
        yield

    app = FastAPI(
        title="IEKG API",
        summary="Knowledge graph of the Informatics Engineering curriculum: operation, navigation and documents.",
        version="0.1.0",
        lifespan=lifespan,
    )
    app.include_router(operations_router(context), prefix="/api")
    app.include_router(navigation_router(context), prefix="/api")
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

    @router.post("/runs", status_code=202, responses={
        422: {"description": "Not a PDF, or a declaration it lacks"},
        503: {"description": "The worker could not be launched; nothing was recorded"},
    })
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
        try:
            launched = context.worker.ensure_running()
        except OSError as error:
            # All or nothing: a run no worker will take is withdrawn (ADR-007).
            with context.store() as store:
                withdrawn = withdraw_submission(store, context.documents_dir, run_id)
            if withdrawn:
                raise HTTPException(
                    503, f"could not launch the worker ({error}); nothing was recorded, submit the document again",
                ) from error
            launched = False
        return SubmittedRun(run_id=run_id, worker_launched=launched)

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


Key = Annotated[str, Query(min_length=1, description="The key of the node; an IRI in the reference layer.")]
_NOT_FOUND = {404: {"description": "No node of the expected class with this key"}}


def navigation_router(context: ApiContext) -> APIRouter:
    """The derivations of R1's step 5, the search and the detail of a node (RF-11 to RF-18). Public.

    Every route returns a piece of the graph as stored, with the provenance of
    each node and edge among its nodes (RF-17).
    """
    router = APIRouter(tags=["navigation"])

    def get(path: str):
        # Only what applies to each node is sent (see NodeView).
        return router.get(path, responses=_NOT_FOUND, response_model_exclude_unset=True)

    def subgraph(query: navigation.Query, expected: str) -> SubgraphView:
        found = context.navigation.fetch(query)
        if found is None:
            raise HTTPException(404, f"no {expected} with this key")
        return SubgraphView.of(found)

    @router.get("/search", response_model_exclude_unset=True)
    def search(
        q: Annotated[str, Query(min_length=1, max_length=200, description="Words of a name or a course code.")],
    ) -> SubgraphView:
        """Knowledge elements and courses whose names or code start with every word, by score (RF-18).

        Accents and case are ignored. At most ``MAX_SEARCH_RESULTS`` nodes.
        """
        query = navigation.search(q, context.navigation.stopwords())
        if query is None:
            return SubgraphView(nodes=[], edges=[])
        return SubgraphView.of(context.navigation.fetch(query) or Subgraph())

    @get("/nodes")
    def node_detail(key: Key) -> SubgraphView:
        """The node with its properties, its direct neighbors and a few of theirs, by any edge but WAS_DERIVED_FROM."""
        return subgraph(navigation.node_detail(key), "node")

    @get("/concepts/prerequisites")
    def concept_prerequisites(key: Key) -> SubgraphView:
        """The prerequisites of a concept, transitively and with bounded depth (RF-11)."""
        return subgraph(navigation.concept_prerequisites(key), "concept")

    @get("/courses/prerequisites")
    def course_prerequisites(key: Key) -> SubgraphView:
        """What a course teaches and requires, and the courses that teach what it requires (RF-12)."""
        return subgraph(navigation.course_prerequisites(key), "course")

    @get("/elements/location")
    def element_location(key: Key) -> SubgraphView:
        """What a knowledge element is part of, up to its area, and what is part of it (RF-13)."""
        return subgraph(navigation.element_location(key), "knowledge element")

    @get("/elements/resources")
    def element_resources(key: Key) -> SubgraphView:
        """The learning resources about an element or a course, and about any of its parts (RF-14)."""
        return subgraph(navigation.element_resources(key), "knowledge element or course")

    @get("/learning-path")
    def learning_path(
        key: Key,
        grain: Annotated[Grain, Query(description="The unit of the answer: topics, courses or areas.")],
    ) -> SubgraphView:
        """What to learn before a concept, topic, unit, area or course, lifted to the grain (RF-15).

        ``depth`` is 0 inside the target; for a prerequisite, its distance from
        the target, and for a node of the grain, that of its nearest prerequisite.
        """
        return subgraph(navigation.learning_path(key, grain), "knowledge element or course")

    @get("/concepts/specializations")
    def concept_specializations(key: Key) -> SubgraphView:
        """What a concept is a kind of, and what is a kind of it, transitively (RF-16)."""
        return subgraph(navigation.concept_specializations(key), "concept")

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
