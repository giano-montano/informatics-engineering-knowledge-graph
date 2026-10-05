import sqlite3

import pytest

from iekg.core.auditor import AuditReport, RuleResult
from iekg.operational_store import LOAD, OperationalStore

REPORT = AuditReport((
    RuleResult("RI-01", 0, ()),
    RuleResult("RI-08", 2, ("a (Concept) is not part of any Topic", "b (Topic) is not part of any KnowledgeUnit")),
))


def test_the_latest_report_reads_back_as_recorded(tmp_path):
    with OperationalStore(tmp_path / "ops" / "operational.sqlite") as store:
        assert store.latest_audit_report() is None
        store.record_audit_report(AuditReport((RuleResult("RI-01", 0, ()),)), origin=LOAD)
        report_id = store.record_audit_report(REPORT, origin=LOAD)
        latest = store.latest_audit_report()
    assert latest.id == report_id
    assert latest.origin == LOAD and latest.run_id is None
    assert latest.report == REPORT
    assert not latest.report.clean and latest.report.violations == 2


def test_the_store_survives_reopening_and_uses_wal(tmp_path):
    path = tmp_path / "operational.sqlite"
    with OperationalStore(path) as store:
        store.record_audit_report(REPORT, origin=LOAD)
    with OperationalStore(path) as store:
        assert store.latest_audit_report().report == REPORT
    with sqlite3.connect(path) as connection:
        assert connection.execute("PRAGMA journal_mode").fetchone() == ("wal",)


def test_an_unknown_origin_is_refused(tmp_path):
    with OperationalStore(tmp_path / "operational.sqlite") as store, pytest.raises(ValueError):
        store.record_audit_report(REPORT, origin="manual")
