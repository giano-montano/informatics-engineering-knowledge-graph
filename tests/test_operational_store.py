import sqlite3

import pytest

from iekg.core.auditor import AuditReport, RuleResult
from iekg.operational_store import LOAD, OperationalStore

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
