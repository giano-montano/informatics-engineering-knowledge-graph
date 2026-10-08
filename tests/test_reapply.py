"""The reapplication: which runs it repeats, when it refuses, and how it writes.

The command tests replace the driver and the repository, so they never write
to a real base. The write tests run inside a transaction that is rolled back,
which cannot empty the base: reapplying after a load is verified by running it.
"""

from dataclasses import dataclass, field, replace
from uuid import uuid4

import pytest
from neo4j.exceptions import ServiceUnavailable
from test_commands import CLEAN, UNREACHABLE, FakeDriver

from iekg.build_tools import commands
from iekg.build_tools.commands import EXIT_CLEAN, EXIT_FAILED, EXIT_REJECTED, reapply, reapply_runs
from iekg.core.auditor import audit
from iekg.core.batch import Batch, NodeFact, Snapshot, SnapshotNode
from iekg.core.repository import WriteResult, read_snapshot_in, write_batch_in
from iekg.fact_store import FactStore, StoredFacts
from iekg.graph_schema import INSTITUTIONAL, KNOWLEDGE_UNIT, REFERENCE, TOPIC
from iekg.ingestion.declared import SYLLABUS, Declaration, assemble_batch
from iekg.operational_store import REAPPLICATION, OperationalStore
from test_orchestrator import facts_under


@dataclass
class FakeRepository:
    snapshot: Snapshot = field(default_factory=Snapshot)
    fail: bool = False
    written: list = field(default_factory=list)

    def read_snapshot(self):
        return self.snapshot

    def write_batch(self, batch, snapshot, *, layer, provenance):
        if self.fail:
            raise ServiceUnavailable("lost the connection")
        self.written.append(provenance)
        return WriteResult(len(batch.nodes), len(batch.edges), 0, 0)


@pytest.fixture
def base(monkeypatch, tmp_path):
    repository = FakeRepository()
    monkeypatch.setattr(commands.GraphDatabase, "driver", FakeDriver)
    monkeypatch.setattr(commands, "GraphRepository", lambda driver, database: repository)
    monkeypatch.setattr(commands, "audit_database", lambda driver, database: CLEAN)
    settings = replace(UNREACHABLE, operational_db=tmp_path / "ops.sqlite", facts_dir=tmp_path / "facts")
    return settings, repository


def record_runs(settings, *final_states):
    """One written run per state, each with its fact file; return their resource keys."""
    keys = []
    with OperationalStore(settings.operational_db) as store:
        for clean in final_states:
            key = str(uuid4())
            run_id = store.create_run(resource_key=key, resource_type=SYLLABUS, course_code="X",
                                      course_name="X", file_name="x.pdf")
            store.take_pending_run()
            store.mark_written(run_id)
            store.finish_run(run_id, clean=clean)
            FactStore(settings.facts_dir).save(StoredFacts(run_id, INSTITUTIONAL, key, Batch()))
            keys.append(key)
    return keys


def run(settings):
    lines = []
    return reapply(settings, out=lines.append), "\n".join(lines)


def latest_report(settings):
    with OperationalStore(settings.operational_db) as store:
        return store.latest_audit_report()


def test_the_runs_are_repeated_in_order_skipping_the_ones_the_audit_stopped(base):
    settings, repository = base
    first, stopped, third = record_runs(settings, True, False, True)
    code, output = run(settings)
    assert code == EXIT_CLEAN, output
    assert repository.written == [first, third]
    report = latest_report(settings)
    assert report.origin == REAPPLICATION and report.clean


def test_without_facts_nothing_is_touched(base):
    settings, repository = base
    code, output = run(settings)
    assert code == EXIT_CLEAN and "No facts" in output
    assert latest_report(settings) is None


def test_a_fact_file_without_its_run_is_refused(base):
    settings, repository = base
    FactStore(settings.facts_dir).save(StoredFacts(5, INSTITUTIONAL, "doc", Batch()))
    code, output = run(settings)
    assert code == EXIT_REJECTED and "belongs to no run" in output
    assert repository.written == [] and latest_report(settings) is None


def test_a_graph_that_already_has_an_institutional_layer_is_refused(base):
    settings, repository = base
    record_runs(settings, True)
    repository.snapshot = Snapshot(nodes={"t": SnapshotNode(TOPIC, INSTITUTIONAL)})
    code, output = run(settings)
    assert code == EXIT_REJECTED and "right after a load" in output
    assert repository.written == [] and latest_report(settings) is None


def test_a_failed_write_leaves_the_gate_closed(base):
    settings, repository = base
    record_runs(settings, True)
    repository.fail = True
    code, output = run(settings)
    assert code == EXIT_FAILED and "left open" in output
    assert latest_report(settings).report is None


@dataclass
class TransactionRepository:
    tx: object

    def read_snapshot(self):
        return read_snapshot_in(self.tx)

    def write_batch(self, batch, snapshot, *, layer, provenance):
        return write_batch_in(self.tx, batch, snapshot, layer=layer, provenance=provenance)


@pytest.mark.neo4j
def test_repeating_written_batches_on_the_graph_they_left_changes_nothing(tx, tmp_path):
    repository = TransactionRepository(tx)
    snapshot = repository.read_snapshot()
    unit = next(key for key, node in snapshot.nodes.items()
                if node.label == KNOWLEDGE_UNIT and node.layer == REFERENCE)
    before = {result.rule: result.violations for result in audit(tx).results}
    facts = FactStore(tmp_path)
    # Two syllabi of one course, as the ingestion assembled them; the second
    # links to the course and the resource type the first created.
    for run_id in (1, 2):
        resource = str(uuid4())
        batch = assemble_batch(Declaration(resource, SYLLABUS, "TEST02", "Curso"), facts_under(unit),
                               repository.read_snapshot(), public_base_url="http://localhost:8000")
        repository.write_batch(batch, repository.read_snapshot(), layer=INSTITUTIONAL, provenance=resource)
        facts.save(StoredFacts(run_id, INSTITUTIONAL, resource, batch))
    lines = []
    reapply_runs(repository, facts, [1, 2], lines.append)
    assert lines == ["Run 1: 0 nodes, 0 edges", "Run 2: 0 nodes, 0 edges"]
    assert {result.rule: result.violations for result in audit(tx).results} == before


@pytest.mark.neo4j
def test_a_batch_written_by_the_reapplication_must_match_its_counters(tx, tmp_path):
    repository = TransactionRepository(tx)
    resource = str(uuid4())
    facts = FactStore(tmp_path)
    # A fact file whose provenance resource is missing cannot be repeated.
    facts.save(StoredFacts(1, INSTITUTIONAL, resource, Batch(nodes=(NodeFact(str(uuid4()), TOPIC),))))
    with pytest.raises(commands.WriteMismatch):
        reapply_runs(repository, facts, [1], lambda line: None)
