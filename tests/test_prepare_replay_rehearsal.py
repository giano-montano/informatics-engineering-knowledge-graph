"""The preparation of a CA-11 rehearsal: the stores as they were before a run."""

import sqlite3

import pytest

from prepare_replay_rehearsal import prepare
from iekg.core.auditor import AuditReport, RuleResult
from iekg.operational_store import INGESTION, LOAD, Discard, Extraction, OperationalStore

CLEAN = AuditReport((RuleResult("RI-01", 0, ()),))


def ingested(store, number, documents, facts):
    key = f"key-{number}"
    run_id = store.create_run(resource_key=key, resource_type="Sílabo", course_code=f"1INF{number:02d}",
                              course_name=f"Curso {number}", file_name=f"{number}.pdf")
    (documents / f"{key}.pdf").write_bytes(b"%PDF-1.7 " + key.encode())
    store.take_pending_run()
    store.record_extraction(run_id, Extraction("m", {}, "p", 0, 1, 1, output={"topics": []}))
    report = store.open_audit_report(origin=INGESTION, run_id=str(run_id))
    store.attach_audit_report(run_id, report)
    store.mark_written(run_id)
    store.complete_audit_report(report, CLEAN)
    store.finish_run(run_id, clean=True)
    (facts / f"run-{run_id:06d}.json").write_text("{}", encoding="utf-8")
    return run_id


@pytest.fixture
def source(tmp_path):
    root = tmp_path / "medicion"
    (root / "documents").mkdir(parents=True)
    (root / "facts").mkdir()
    with OperationalStore(root / "operational.sqlite") as store:
        load = store.open_audit_report(origin=LOAD)
        store.complete_audit_report(load, CLEAN)
        for number in (1, 2, 3):
            ingested(store, number, root / "documents", root / "facts")
    return root


def test_the_rehearsal_keeps_the_runs_before_the_cut_and_removes_the_rest(source, tmp_path):
    prepared = prepare(source, 2, tmp_path / "ensayo")
    assert prepared.kept_runs == 1
    with OperationalStore(tmp_path / "ensayo" / "operational.sqlite") as store:
        assert [run.id for run in store.list_runs()] == [1]
        assert store.latest_audit_report().clean
        assert store.model_output_of(2) is None
    assert sorted(p.name for p in (tmp_path / "ensayo" / "facts").iterdir()) == ["run-000001.json"]
    assert sorted(p.name for p in (tmp_path / "ensayo" / "documents").iterdir()) == ["key-1.pdf"]


def test_the_audit_reports_of_the_removed_runs_go_with_them(source, tmp_path):
    prepare(source, 2, tmp_path / "ensayo")
    connection = sqlite3.connect(tmp_path / "ensayo" / "operational.sqlite")
    origins = connection.execute("SELECT origin, run_id FROM audit_reports ORDER BY id").fetchall()
    orphans = connection.execute(
        "SELECT count(*) FROM audit_rule_results WHERE report_id NOT IN (SELECT id FROM audit_reports)").fetchone()
    connection.close()
    assert origins == [(LOAD, None), (INGESTION, "1")]
    assert orphans == (0,)


def test_the_next_run_takes_the_number_of_the_removed_one(source, tmp_path):
    prepare(source, 2, tmp_path / "ensayo")
    with OperationalStore(tmp_path / "ensayo" / "operational.sqlite") as store:
        assert store.create_run(resource_key="new", resource_type="Sílabo", course_code="1INF02",
                                course_name="Curso 2", file_name="2.pdf") == 2


def test_the_pdf_of_the_cut_run_is_left_to_upload_with_what_it_declared(source, tmp_path):
    prepared = prepare(source, 2, tmp_path / "ensayo")
    assert prepared.upload == tmp_path / "ensayo" / "1INF02.pdf"
    assert prepared.upload.read_bytes() == b"%PDF-1.7 key-2"
    assert (prepared.course_code, prepared.course_name, prepared.resource_type) == ("1INF02", "Curso 2", "Sílabo")


def test_the_source_is_not_changed(source, tmp_path):
    before = (source / "operational.sqlite").read_bytes()
    prepare(source, 2, tmp_path / "ensayo")
    assert (source / "operational.sqlite").read_bytes() == before
    assert len(list((source / "facts").iterdir())) == 3


def test_a_run_that_does_not_exist_is_refused(source, tmp_path):
    with pytest.raises(SystemExit, match="run 9 does not exist"):
        prepare(source, 9, tmp_path / "ensayo")


def test_a_folder_that_is_not_empty_is_refused(source, tmp_path):
    (tmp_path / "ensayo").mkdir()
    (tmp_path / "ensayo" / "keep.txt").write_text("x", encoding="utf-8")
    with pytest.raises(SystemExit, match="not empty"):
        prepare(source, 2, tmp_path / "ensayo")
