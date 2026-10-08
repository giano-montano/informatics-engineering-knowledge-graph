"""What the API returns: the shapes of its JSON responses, with examples."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from iekg.core.batch import Batch, batch_to_data
from iekg.operational_store import RUN_STATES, Discard, Run, StoredAuditReport

_STATES = ", ".join(RUN_STATES)


def _example(example: dict) -> ConfigDict:
    return ConfigDict(json_schema_extra={"examples": [example]})


class SubmittedRun(BaseModel):
    model_config = _example({"run_id": 7, "worker_launched": True})

    run_id: int
    worker_launched: bool = Field(description="False if a worker was already running: it takes the run in turn.")


class RunSummary(BaseModel):
    model_config = _example({
        "id": 7, "status": "completed", "created_at": "2026-10-08T15:02:11+00:00",
        "finished_at": "2026-10-08T15:03:40+00:00", "resource_type": "Sílabo", "course_code": "1INF33",
        "course_name": "Bases de Datos", "file_name": "silabo-1INF33.pdf",
    })

    id: int
    status: str = Field(description=f"One of: {_STATES} (ADR-010).")
    created_at: str
    finished_at: str | None
    resource_type: str
    course_code: str | None
    course_name: str | None
    file_name: str

    @classmethod
    def of(cls, run: Run) -> "RunSummary":
        return cls(**{name: getattr(run, name) for name in cls.model_fields})


class RuleResultView(BaseModel):
    rule: str
    violations: int
    sample: list[str] = Field(description="Up to a few of the violating nodes or edges.")


class AuditReportView(BaseModel):
    model_config = _example({
        "id": 12, "created_at": "2026-10-08T15:03:38+00:00", "origin": "ingestion", "run_id": "7",
        "completed": True, "violations": 0, "rules": [{"rule": "RI-01", "violations": 0, "sample": []}],
    })

    id: int
    created_at: str
    origin: str = Field(description="The write path that opened it: load, ingestion or reapplication.")
    run_id: str | None
    completed: bool = Field(description="False while the write path that opened it has not audited the graph.")
    violations: int | None = Field(description="Null while the report is open.")
    rules: list[RuleResultView]

    @classmethod
    def of(cls, stored: StoredAuditReport) -> "AuditReportView":
        report = stored.report
        return cls(
            id=stored.id, created_at=stored.created_at, origin=stored.origin, run_id=stored.run_id,
            completed=report is not None,
            violations=report.violations if report else None,
            rules=[RuleResultView(rule=r.rule, violations=r.violations, sample=list(r.sample))
                   for r in (report.results if report else ())],
        )


class RunDetail(BaseModel):
    id: int
    status: str = Field(description=f"One of: {_STATES} (ADR-010).")
    created_at: str
    started_at: str | None
    finished_at: str | None
    resource_key: str = Field(description="The key of the learning resource, and of its document.")
    resource_type: str
    course_code: str | None
    course_name: str | None
    file_name: str
    model: str | None = Field(description="The model as the provider named it (RF-25).")
    model_settings: dict | None
    prompt_version: str | None
    content_retries: int | None
    error: str | None
    audit_report: AuditReportView | None = Field(description="The report of the audit that closed the run, if any.")

    @classmethod
    def of(cls, run: Run, report: StoredAuditReport | None) -> "RunDetail":
        fields = {name: getattr(run, name) for name in cls.model_fields if name != "audit_report"}
        return cls(**fields, audit_report=AuditReportView.of(report) if report else None)


class DiscardView(BaseModel):
    rule: str = Field(description="The integrity rule (RI, RM) or the output check (EX) it violates.")
    fact: str
    message: str


class RunDiscards(BaseModel):
    model_config = _example({
        "discards": [{"rule": "RI-05", "fact": "(a)-[:PART_OF]->(b)", "message": "Concept PART_OF Course"}],
        "batch": {"nodes": [], "edges": []},
        "raw_output": None,
    })

    discards: list[DiscardView]
    batch: dict | None = Field(description="The whole candidate batch of a rejected run (RF-05).")
    raw_output: str | None = Field(description="The model's output when it never became a batch (EX-01).")

    @classmethod
    def of(cls, discards: list[Discard], batch: Batch | None, raw_output: str | None) -> "RunDiscards":
        return cls(
            discards=[DiscardView(rule=d.rule, fact=d.fact, message=d.message) for d in discards],
            batch=batch_to_data(batch) if batch else None,
            raw_output=raw_output,
        )


class AuditGate(BaseModel):
    state: Literal["open", "closed"]
    reason: str | None = Field(description="Why it is closed; null when open.")


class LatestAuditReport(BaseModel):
    model_config = _example({
        "gate": {"state": "closed", "reason": "latest report with violations"},
        "report": {"id": 12, "created_at": "2026-10-08T15:03:38+00:00", "origin": "ingestion", "run_id": "7",
                   "completed": True, "violations": 1,
                   "rules": [{"rule": "RI-08", "violations": 1, "sample": ["x (Topic) is not part of any KnowledgeUnit"]}]},
    })

    gate: AuditGate
    report: AuditReportView | None = Field(description="Null if no write path has recorded one yet.")
