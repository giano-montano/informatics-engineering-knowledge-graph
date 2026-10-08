import sqlite3

import pytest

from iekg.core.auditor import AuditReport, RuleResult
from iekg.core.batch import Batch, NodeFact
from iekg.operational_store import (
    COMPLETED,
    FAILED,
    LOAD,
    PENDING,
    REJECTED,
    RUNNING,
    STOPPED_BY_AUDIT,
    WRITTEN_NOT_PERSISTED,
    Discard,
    Extraction,
    OperationalStore,
)

CLEAN = AuditReport((RuleResult("RI-01", 0, ()),))
REPORT = AuditReport((
    RuleResult("RI-01", 0, ()),
    RuleResult("RI-08", 2, ("a (Concept) is not part of any Topic", "b (Topic) is not part of any KnowledgeUnit")),
))


def record(store, report):
    report_id = store.open_audit_report(origin=LOAD)
    store.complete_audit_report(report_id, report)
    return report_id


def test_the_latest_report_reads_back_as_recorded(tmp_path):
    with OperationalStore(tmp_path / "ops" / "operational.sqlite") as store:
        assert store.latest_audit_report() is None
        record(store, CLEAN)
        report_id = record(store, REPORT)
        latest = store.latest_audit_report()
    assert latest.id == report_id
    assert latest.origin == LOAD and latest.run_id is None
    assert latest.report == REPORT
    assert not latest.clean and latest.report.violations == 2


def test_an_open_report_is_the_latest_and_is_not_clean(tmp_path):
    with OperationalStore(tmp_path / "operational.sqlite") as store:
        record(store, CLEAN)
        report_id = store.open_audit_report(origin=LOAD)
        latest = store.latest_audit_report()
    assert latest.id == report_id
    assert latest.report is None and not latest.clean


def test_a_clean_report_completed_after_an_open_one_is_clean(tmp_path):
    with OperationalStore(tmp_path / "operational.sqlite") as store:
        store.open_audit_report(origin=LOAD)
        record(store, CLEAN)
        assert store.latest_audit_report().clean


def test_a_report_is_completed_only_once(tmp_path):
    with OperationalStore(tmp_path / "operational.sqlite") as store:
        report_id = record(store, CLEAN)
        with pytest.raises(ValueError, match="not open"):
            store.complete_audit_report(report_id, REPORT)
        assert store.latest_audit_report().report == CLEAN


def test_the_store_survives_reopening_and_uses_wal(tmp_path):
    path = tmp_path / "operational.sqlite"
    with OperationalStore(path) as store:
        record(store, REPORT)
    with OperationalStore(path) as store:
        assert store.latest_audit_report().report == REPORT
    with sqlite3.connect(path) as connection:
        assert connection.execute("PRAGMA journal_mode").fetchone() == ("wal",)


def test_an_unknown_origin_is_refused(tmp_path):
    with OperationalStore(tmp_path / "operational.sqlite") as store, pytest.raises(ValueError):
        store.open_audit_report(origin="manual")


# --- Runs -------------------------------------------------------------------


def new_run(store, key="doc-1", course="1INF25"):
    return store.create_run(
        resource_key=key, resource_type="Sílabo", course_code=course, course_name="Curso", file_name=f"{key}.pdf",
    )


def test_runs_are_taken_oldest_first_and_only_once(tmp_path):
    with OperationalStore(tmp_path / "operational.sqlite") as store:
        first, second = new_run(store, "a"), new_run(store, "b")
        assert store.get_run(first).status == PENDING
        taken = store.take_pending_run()
        assert (taken.id, taken.status, taken.resource_type) == (first, RUNNING, "Sílabo")
        assert store.take_pending_run().id == second
        assert store.take_pending_run() is None


def test_a_written_run_moves_through_its_states(tmp_path):
    with OperationalStore(tmp_path / "operational.sqlite") as store:
        run_id = new_run(store)
        store.take_pending_run()
        store.record_extraction(run_id, Extraction("model-x-2026", {"temperature": 0}, "v1", 1))
        report_id = store.open_audit_report(origin="ingestion", run_id=str(run_id))
        store.attach_audit_report(run_id, report_id)
        store.mark_written(run_id)
        assert store.get_run(run_id).status == WRITTEN_NOT_PERSISTED
        store.finish_run(run_id, clean=True)
        run = store.get_run(run_id)
    assert (run.status, run.model, run.model_settings, run.prompt_version, run.content_retries) == (
        COMPLETED, "model-x-2026", {"temperature": 0}, "v1", 1,
    )
    assert run.audit_report_id == report_id and run.finished_at is not None


def test_a_written_run_with_a_dirty_audit_is_stopped(tmp_path):
    with OperationalStore(tmp_path / "operational.sqlite") as store:
        run_id = new_run(store)
        store.take_pending_run()
        store.mark_written(run_id)
        store.finish_run(run_id, clean=False)
        assert store.get_run(run_id).status == STOPPED_BY_AUDIT


def test_a_rejected_run_keeps_every_discard_and_the_whole_batch(tmp_path):
    batch = Batch(nodes=(NodeFact("t", "Topic", {"prefLabelEs": "Búsqueda"}),))
    discards = [Discard("RI-08", "t", "new Topic has no PART_OF edge"), Discard("RM-04", "a -> b", "cycle")]
    with OperationalStore(tmp_path / "operational.sqlite") as store:
        run_id = new_run(store)
        store.take_pending_run()
        store.reject_run(run_id, discards, batch=batch)
        assert store.get_run(run_id).status == REJECTED
        assert store.discards_of(run_id) == discards
        assert store.rejected_output_of(run_id) == (batch, None)


def test_a_run_rejected_before_it_had_a_batch_keeps_the_raw_output(tmp_path):
    with OperationalStore(tmp_path / "operational.sqlite") as store:
        run_id = new_run(store)
        store.take_pending_run()
        store.reject_run(run_id, [Discard("EX-01", "output", "missing field")], raw_output="{not json")
        assert store.rejected_output_of(run_id) == (None, "{not json")


def test_a_rejection_needs_a_discard_and_something_rejected(tmp_path):
    with OperationalStore(tmp_path / "operational.sqlite") as store:
        run_id = new_run(store)
        store.take_pending_run()
        with pytest.raises(ValueError, match="at least one discard"):
            store.reject_run(run_id, [], raw_output="x")
        with pytest.raises(sqlite3.IntegrityError):
            store.reject_run(run_id, [Discard("EX-01", "output", "m")])
        # The failed rejection left nothing behind.
        assert store.get_run(run_id).status == RUNNING and store.discards_of(run_id) == []


def test_a_failed_run_keeps_its_error_and_no_discard(tmp_path):
    with OperationalStore(tmp_path / "operational.sqlite") as store:
        run_id = new_run(store)
        store.take_pending_run()
        store.fail_run(run_id, "provider unavailable")
        run = store.get_run(run_id)
        assert (run.status, run.error) == (FAILED, "provider unavailable")
        assert store.discards_of(run_id) == []


@pytest.mark.parametrize("step", [
    lambda store, run_id: store.mark_written(run_id),
    lambda store, run_id: store.fail_run(run_id, "x"),
    lambda store, run_id: store.finish_run(run_id, clean=True),
    lambda store, run_id: store.reject_run(run_id, [Discard("EX-01", "o", "m")], raw_output="x"),
])
def test_a_run_does_not_skip_states(tmp_path, step):
    with OperationalStore(tmp_path / "operational.sqlite") as store:
        run_id = new_run(store)
        with pytest.raises(ValueError, match="is not"):
            step(store, run_id)
        assert store.get_run(run_id).status == PENDING


def test_a_document_is_the_resource_of_one_run_only(tmp_path):
    with OperationalStore(tmp_path / "operational.sqlite") as store:
        new_run(store, "doc")
        with pytest.raises(sqlite3.IntegrityError):
            new_run(store, "doc")
