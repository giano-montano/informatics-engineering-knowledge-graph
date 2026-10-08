"""Run orchestrator: takes the pending runs one after another and drives each.

The cycle is the ``ingestion`` dynamic view of docs/architecture/views.c4:
audit gate, snapshot, extraction, declared facts, validation, write, fact
store and audit (ADR-007, ADR-010). The worker is the only writer while the
system is in service, so the snapshot stays current until the commit.
"""

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from neo4j import Driver
from neo4j.exceptions import DriverError, Neo4jError

from iekg.core.auditor import AuditReport, audit_database
from iekg.core.batch import Batch, Snapshot
from iekg.core.repository import GraphRepository, WriteResult
from iekg.core.validator import INGESTION_RULES, validate
from iekg.fact_store import FactStore, StoredFacts
from iekg.graph_schema import INSTITUTIONAL
from iekg.ingestion.declared import Declaration, assemble_batch
from iekg.ingestion.extraction import Extractor, NonConformingOutput, ProviderFailure
from iekg.operational_store import INGESTION, Discard, OperationalStore, Run, StoredAuditReport

Output = Callable[[str], None]


class Graph(Protocol):
    def read_snapshot(self) -> Snapshot: ...

    def write_batch(self, batch: Batch, snapshot: Snapshot, *, layer: str, provenance: str) -> WriteResult: ...

    def audit(self) -> AuditReport: ...


class Neo4jGraph:
    """The graph core over a running base: repository and auditor."""

    def __init__(self, driver: Driver, database: str) -> None:
        self._driver = driver
        self._database = database
        self._repository = GraphRepository(driver, database)

    def read_snapshot(self) -> Snapshot:
        return self._repository.read_snapshot()

    def write_batch(self, batch: Batch, snapshot: Snapshot, *, layer: str, provenance: str) -> WriteResult:
        return self._repository.write_batch(batch, snapshot, layer=layer, provenance=provenance)

    def audit(self) -> AuditReport:
        return audit_database(self._driver, self._database)


def document_path(documents: Path, resource_key: str) -> Path:
    return documents / f"{resource_key}.pdf"


# Why the audit gate is closed (ADR-007). The API reports the same reasons.
NO_REPORT = "no report recorded"
REPORT_OPEN = "latest report still open"
REPORT_WITH_VIOLATIONS = "latest report with violations"


def gate_closed_by(latest: StoredAuditReport | None) -> str | None:
    """Why the gate is closed given the latest report; None if it is open."""
    if latest is None:
        return NO_REPORT
    if latest.report is None:
        return REPORT_OPEN
    return None if latest.clean else REPORT_WITH_VIOLATIONS


@dataclass
class Orchestrator:
    store: OperationalStore
    graph: Graph
    extractor: Extractor
    facts: FactStore
    documents: Path
    public_base_url: str
    out: Output = print

    def run_pending(self) -> None:
        """Process pending runs while the audit gate is open and there are any."""
        while True:
            reason = gate_closed_by(self.store.latest_audit_report())
            if reason is not None:
                self.out(f"Audit gate closed ({reason}). Pending runs stay pending.")
                return
            run = self.store.take_pending_run()
            if run is None:
                return
            if not self.process(run):
                return

    def process(self, run: Run) -> bool:
        """Drive ``run`` to a final state; False if the worker must stop."""
        self.out(f"Run {run.id}: {run.resource_type} {run.course_code} ({run.file_name})")
        declaration = Declaration(run.resource_key, run.resource_type, run.course_code, run.course_name)
        try:
            snapshot = self.graph.read_snapshot()
        except Exception as error:
            return self._fail(run, f"reading the snapshot: {error!r}")

        try:
            extracted, extraction = self.extractor.extract(document_path(self.documents, run.resource_key), snapshot)
        except NonConformingOutput as error:
            self.store.record_extraction(run.id, error.extraction)
            self.store.reject_run(run.id, error.discards, raw_output=error.raw_output)
            self.out(f"  rejected: {error}")
            return True
        except ProviderFailure as error:
            if error.extraction is not None:
                self.store.record_extraction(run.id, error.extraction)
            return self._fail(run, f"provider: {error}")
        except Exception as error:
            return self._fail(run, f"extracting: {error!r}")
        self.store.record_extraction(run.id, extraction)

        try:
            batch = assemble_batch(declaration, extracted, snapshot, public_base_url=self.public_base_url)
        except ValueError as error:
            return self._fail(run, f"assembling the batch: {error}")
        violations = validate(batch, snapshot, layer=INSTITUTIONAL, rules=INGESTION_RULES)
        if violations:
            self.store.reject_run(run.id, [Discard(v.rule, v.fact, v.message) for v in violations], batch=batch)
            self.out(f"  rejected: {len(violations)} violation(s)")
            return True

        # Opened before the graph is touched: if the worker dies in between,
        # the open report keeps the gate closed (ADR-007).
        report_id = self.store.open_audit_report(origin=INGESTION, run_id=str(run.id))
        self.store.attach_audit_report(run.id, report_id)
        try:
            result = self.graph.write_batch(batch, snapshot, layer=INSTITUTIONAL, provenance=run.resource_key)
        except Exception as error:
            self._fail(run, f"writing: {error!r}")
            # The write was rolled back. Auditing the intact graph closes the
            # report, so the worker goes on with the next run (ADR-010).
            return self._audit(report_id) is not None
        self.store.mark_written(run.id)
        self.out(f"  committed: {result.nodes_created} nodes, {result.relationships_created} edges")

        persisted = True
        try:
            self.facts.save(StoredFacts(run.id, INSTITUTIONAL, run.resource_key, batch))
        except OSError as error:
            persisted = False
            self.store.record_written_error(run.id, f"saving the facts: {error!r}")
            self.out(f"  written, but its facts were not saved: {error}")

        report = self._audit(report_id)
        if report is None:
            if persisted:
                self.store.record_written_error(run.id, "auditing: the facts are saved, the audit did not run")
            return False
        if not persisted:
            return False
        self.store.finish_run(run.id, clean=report.clean)
        self.out("  completed" if report.clean else "  stopped by the audit: the audit gate closes")
        return True

    def _fail(self, run: Run, error: str) -> bool:
        self.store.fail_run(run.id, error)
        self.out(f"  failed: {error}")
        return True

    def _audit(self, report_id: int) -> AuditReport | None:
        """Audit and complete the report; None if the audit could not run."""
        try:
            report = self.graph.audit()
        except (DriverError, Neo4jError) as error:
            self.out(f"  audit failed: {error}. Report {report_id} is left open, so the audit gate closes.")
            return None
        self.store.complete_audit_report(report_id, report)
        self.out(f"  audit report {report_id}: {'clean' if report.clean else f'{report.violations} violation(s)'}")
        return report
