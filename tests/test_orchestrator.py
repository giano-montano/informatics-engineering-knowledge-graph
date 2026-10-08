"""The run cycle, on a fake extractor.

Failure paths run on an in-memory graph that can be told to fail. The written
path runs on Neo4j inside a transaction that is rolled back.
"""

from dataclasses import dataclass, field
from uuid import uuid4

import pytest
from neo4j.exceptions import ServiceUnavailable

from iekg.core.auditor import AuditReport, RuleResult, audit
from iekg.core.batch import EdgeFact, NodeFact, Snapshot, SnapshotNode
from iekg.core.repository import WriteMismatch, WriteResult, read_snapshot_in, write_batch_in
from iekg.fact_store import FactStore
from iekg.graph_schema import (
    CONCEPT,
    INSTITUTIONAL,
    KNOWLEDGE_UNIT,
    PART_OF,
    PREF_LABEL_ES,
    REFERENCE,
    TOPIC,
)
from iekg.ingestion.declared import SYLLABUS, ExtractedFacts, course_key
from iekg.ingestion.extraction import EX_02, NonConformingOutput, ProviderFailure
from iekg.ingestion.orchestrator import Orchestrator
from iekg.operational_store import (
    COMPLETED,
    FAILED,
    LOAD,
    PENDING,
    REJECTED,
    STOPPED_BY_AUDIT,
    WRITTEN_NOT_PERSISTED,
    Discard,
    Extraction,
    OperationalStore,
)

CLEAN = AuditReport((RuleResult("RI-01", 0, ()),))
DIRTY = AuditReport((RuleResult("RI-08", 1, ("x (Topic) is not part of any KnowledgeUnit",)),))
EXTRACTION = Extraction("model-2026-01-01", {"temperature": 0}, "prompt-v1", 0)
UNIT = "ku"


def facts_under(unit):
    topic, concept = str(uuid4()), str(uuid4())
    return ExtractedFacts(
        nodes=(NodeFact(topic, TOPIC, {PREF_LABEL_ES: "Búsqueda"}), NodeFact(concept, CONCEPT)),
        edges=(EdgeFact(PART_OF, topic, unit), EdgeFact(PART_OF, concept, topic)),
        taught=(concept,),
    )


@dataclass
class FakeExtractor:
    """Returns, or raises, one outcome per call."""

    outcomes: list = field(default_factory=list)

    def extract(self, document, snapshot):
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome, EXTRACTION


@dataclass
class FakeGraph:
    snapshot: Snapshot = field(default_factory=lambda: Snapshot(nodes={UNIT: SnapshotNode(KNOWLEDGE_UNIT, REFERENCE)}))
    write_error: Exception | None = None
    audits: list = field(default_factory=lambda: [CLEAN])
    written: list = field(default_factory=list)

    def read_snapshot(self):
        return self.snapshot

    def write_batch(self, batch, snapshot, *, layer, provenance):
        if self.write_error:
            raise self.write_error
        self.written.append(batch)
        return WriteResult(len(batch.nodes), len(batch.edges), 0, 0)

    def audit(self):
        outcome = self.audits.pop(0) if len(self.audits) > 1 else self.audits[0]
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


@pytest.fixture
def store(tmp_path):
    with OperationalStore(tmp_path / "operational.sqlite") as store:
        yield store


def open_gate(store):
    store.complete_audit_report(store.open_audit_report(origin=LOAD), CLEAN)


def submit(store, n=1):
    return [
        store.create_run(resource_key=str(uuid4()), resource_type=SYLLABUS, course_code=f"1INF{i:02d}",
                         course_name=f"Curso {i}", file_name=f"{i}.pdf")
        for i in range(n)
    ]


def orchestrator(store, tmp_path, graph, *outcomes):
    return Orchestrator(store, graph, FakeExtractor(list(outcomes)), FactStore(tmp_path / "facts"),
                        tmp_path / "documents", "http://localhost:8000", out=lambda _: None)


def statuses(store):
    return [run.status for run in store.list_runs()]


# --- The audit gate ----------------------------------------------------------

def test_without_any_audit_report_the_gate_is_closed(store, tmp_path):
    submit(store)
    orchestrator(store, tmp_path, FakeGraph(), facts_under(UNIT)).run_pending()
    assert statuses(store) == [PENDING]


@pytest.mark.parametrize("close", [
    lambda store: store.open_audit_report(origin=LOAD),
    lambda store: store.complete_audit_report(store.open_audit_report(origin=LOAD), DIRTY),
])
def test_an_open_or_dirty_latest_report_keeps_the_runs_pending(store, tmp_path, close):
    open_gate(store)
    close(store)
    submit(store)
    orchestrator(store, tmp_path, FakeGraph(), facts_under(UNIT)).run_pending()
    assert statuses(store) == [PENDING]


# --- Outcomes of a run ---------------------------------------------------------

def test_a_written_run_completes_and_saves_exactly_the_written_batch(store, tmp_path):
    open_gate(store)
    [run_id] = submit(store)
    graph = FakeGraph()
    orchestrator(store, tmp_path, graph, facts_under(UNIT)).run_pending()
    run = store.get_run(run_id)
    assert (run.status, run.model, run.content_retries) == (COMPLETED, EXTRACTION.model, 0)
    saved = FactStore(tmp_path / "facts").load(run_id)
    assert (saved.batch, saved.provenance, saved.layer) == (graph.written[0], run.resource_key, INSTITUTIONAL)
    assert store.latest_audit_report().run_id == str(run_id) and store.latest_audit_report().clean


def test_a_non_conforming_output_rejects_the_run_and_the_worker_goes_on(store, tmp_path):
    open_gate(store)
    first, _ = submit(store, 2)
    discard = Discard(EX_02, "mention 'Grafos'", "key not in the snapshot")
    graph = FakeGraph()
    orchestrator(store, tmp_path, graph, NonConformingOutput([discard], '{"topics": []}', EXTRACTION),
                 facts_under(UNIT)).run_pending()
    assert statuses(store) == [REJECTED, COMPLETED]
    assert store.discards_of(first) == [discard]
    assert store.rejected_output_of(first) == (None, '{"topics": []}')
    assert store.get_run(first).model == EXTRACTION.model
    assert len(graph.written) == 1


def test_a_provider_failure_fails_the_run_without_discard(store, tmp_path):
    open_gate(store)
    [run_id] = submit(store)
    orchestrator(store, tmp_path, FakeGraph(), ProviderFailure("429 after 3 retries")).run_pending()
    run = store.get_run(run_id)
    assert (run.status, run.error) == (FAILED, "provider: 429 after 3 retries")
    assert store.discards_of(run_id) == []


def test_a_batch_with_violations_is_rejected_whole_and_not_written(store, tmp_path):
    open_gate(store)
    [run_id] = submit(store)
    unanchored = ExtractedFacts(nodes=(NodeFact("t", TOPIC),))
    graph = FakeGraph()
    orchestrator(store, tmp_path, graph, unanchored).run_pending()
    assert statuses(store) == [REJECTED]
    assert [d.rule for d in store.discards_of(run_id)] == ["RI-08"]
    batch, raw_output = store.rejected_output_of(run_id)
    assert "t" in batch.nodes_by_key and raw_output is None
    assert graph.written == []


def test_a_rolled_back_write_fails_the_run_audits_and_the_worker_goes_on(store, tmp_path):
    open_gate(store)
    first, _ = submit(store, 2)
    graph = FakeGraph(write_error=WriteMismatch("expected 3 new nodes, created 2"))
    orchestrator(store, tmp_path, graph, facts_under(UNIT), facts_under(UNIT)).run_pending()
    assert statuses(store) == [FAILED, FAILED]
    assert "expected 3 new nodes" in store.get_run(first).error
    assert store.latest_audit_report().clean
    assert list(FactStore(tmp_path / "facts").run_ids()) == []


def test_an_audit_that_cannot_run_leaves_the_report_open_and_stops_the_worker(store, tmp_path):
    open_gate(store)
    submit(store, 2)
    graph = FakeGraph(audits=[ServiceUnavailable("down")])
    orchestrator(store, tmp_path, graph, facts_under(UNIT), facts_under(UNIT)).run_pending()
    assert statuses(store) == [WRITTEN_NOT_PERSISTED, PENDING]
    assert "the facts are saved" in store.list_runs()[0].error
    assert store.latest_audit_report().report is None


def test_facts_that_cannot_be_saved_leave_the_run_written_not_persisted(store, tmp_path):
    open_gate(store)
    [run_id] = submit(store)
    (tmp_path / "facts").write_text("a file where the folder should be")
    orchestrator(store, tmp_path, FakeGraph(), facts_under(UNIT)).run_pending()
    run = store.get_run(run_id)
    assert run.status == WRITTEN_NOT_PERSISTED and "saving the facts" in run.error
    assert store.latest_audit_report().clean


def test_a_dirty_audit_stops_the_run_and_closes_the_gate(store, tmp_path):
    open_gate(store)
    submit(store, 2)
    graph = FakeGraph(audits=[DIRTY])
    orchestrator(store, tmp_path, graph, facts_under(UNIT), facts_under(UNIT)).run_pending()
    assert statuses(store) == [STOPPED_BY_AUDIT, PENDING]
    assert len(list(FactStore(tmp_path / "facts").run_ids())) == 1


# --- On Neo4j ----------------------------------------------------------------------

@dataclass
class TransactionGraph:
    """The graph core inside one transaction, which the fixture rolls back."""

    tx: object

    def read_snapshot(self):
        return read_snapshot_in(self.tx)

    def write_batch(self, batch, snapshot, *, layer, provenance):
        return write_batch_in(self.tx, batch, snapshot, layer=layer, provenance=provenance)

    def audit(self):
        return audit(self.tx)


@pytest.mark.neo4j
def test_two_syllabi_of_one_course_write_cleanly_and_share_the_course(store, tmp_path, tx):
    graph = TransactionGraph(tx)
    if not graph.audit().clean:
        pytest.skip("the base does not audit clean; run iekg-build load")
    unit = next(key for key, node in graph.read_snapshot().nodes.items() if node.label == KNOWLEDGE_UNIT)
    open_gate(store)
    first, _ = (
        store.create_run(resource_key=str(uuid4()), resource_type=SYLLABUS, course_code="TEST01",
                         course_name="Curso de prueba", file_name=f"{i}.pdf")
        for i in range(2)
    )
    orchestrator(store, tmp_path, graph, facts_under(unit), facts_under(unit)).run_pending()
    assert statuses(store) == [COMPLETED, COMPLETED]
    course = course_key("TEST01")
    resources = tx.run(
        "MATCH (r:LearningResource)-[:IS_ABOUT]->(:Course {key: $course}) RETURN count(r)", course=course
    ).single().value()
    assert resources == 2
    # Writing a saved batch again on the graph it left creates nothing (ADR-012).
    saved = FactStore(tmp_path / "facts").load(first)
    again = write_batch_in(tx, saved.batch, read_snapshot_in(tx), layer=INSTITUTIONAL, provenance=saved.provenance)
    assert (again.nodes_created, again.relationships_created) == (0, 0)
