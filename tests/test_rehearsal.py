"""The rehearsal mode of the operator flow (ADR-013, amendment 2026-11).

The rehearsal worker runs on a real SQLite store under ``tmp_path`` and never
touches Neo4j; the API runs on the fakes of ``test_api``.
"""

from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from iekg.api.app import ApiContext, create_app
from iekg.core.auditor import AuditReport, RuleResult
from iekg.ingestion.orchestrator import document_path
from iekg.ingestion.rehearsal import REHEARSAL_MODEL, rehearse, seed_rehearsal_store
from iekg.operational_store import COMPLETED, INGESTION, PENDING, OperationalStore
from iekg.settings import RehearsalSettings
from test_api import AUTH, TOKEN, FakeGraph, FakeNavigation, FakeWorker, submit

CLEAN = AuditReport((RuleResult("RI-01", 0, ()),))
DIRTY = AuditReport((RuleResult("RI-08", 1, ("x (Topic) is not part of any KnowledgeUnit",)),))


def store_with_report(path, report):
    store = OperationalStore(path)
    report_id = store.open_audit_report(origin=INGESTION)
    store.complete_audit_report(report_id, report)
    return store


def pending_run(store, key="k1"):
    return store.create_run(resource_key=key, resource_type="syllabus", course_code="1INF33",
                            course_name="Bases de Datos", file_name="silabo.pdf")


# --- Rehearsal worker -------------------------------------------------------


def test_the_rehearsal_walks_a_pending_run_to_completed_marked_as_simulated(tmp_path):
    with store_with_report(tmp_path / "ensayo.sqlite", CLEAN) as store:
        run_id = pending_run(store)
        pauses = []
        assert rehearse(store, lambda: pauses.append(1)) == 1
        run = store.get_run(run_id)
    assert run.status == COMPLETED
    assert run.model == REHEARSAL_MODEL
    assert run.finished_at is not None
    assert len(pauses) == 3


def test_the_rehearsal_keeps_runs_pending_with_the_gate_closed_by_violations(tmp_path):
    with store_with_report(tmp_path / "ensayo.sqlite", DIRTY) as store:
        run_id = pending_run(store)
        assert rehearse(store, lambda: None) == 0
        assert store.get_run(run_id).status == PENDING


def test_the_rehearsal_keeps_runs_pending_without_any_audit_report(tmp_path):
    with OperationalStore(tmp_path / "ensayo.sqlite") as store:
        run_id = pending_run(store)
        assert rehearse(store, lambda: None) == 0
        assert store.get_run(run_id).status == PENDING


# --- Seeding the rehearsal store -------------------------------------------


def test_the_rehearsal_store_starts_as_a_copy_of_the_real_one(tmp_path):
    real = tmp_path / "operational.sqlite"
    with store_with_report(real, CLEAN) as store:
        pending_run(store)
    seed_rehearsal_store(real, tmp_path / "ensayo" / "operational.sqlite")
    with OperationalStore(tmp_path / "ensayo" / "operational.sqlite") as copy:
        assert [run.resource_key for run in copy.list_runs()] == ["k1"]
        assert copy.latest_audit_report().clean


def test_seeding_leaves_an_existing_rehearsal_store_as_it_is(tmp_path):
    real, rehearsal = tmp_path / "operational.sqlite", tmp_path / "ensayo.sqlite"
    with store_with_report(real, CLEAN) as store:
        pending_run(store, "real")
    with store_with_report(rehearsal, CLEAN) as store:
        pending_run(store, "rehearsed")
    seed_rehearsal_store(real, rehearsal)
    with OperationalStore(rehearsal) as copy:
        assert [run.resource_key for run in copy.list_runs()] == ["rehearsed"]


def test_seeding_without_a_real_store_leaves_the_rehearsal_store_to_start_empty(tmp_path):
    rehearsal = tmp_path / "ensayo" / "operational.sqlite"
    seed_rehearsal_store(tmp_path / "missing.sqlite", rehearsal)
    assert not rehearsal.exists()
    assert rehearsal.parent.is_dir()


def test_seeding_does_not_change_the_real_store(tmp_path):
    real = tmp_path / "operational.sqlite"
    with store_with_report(real, CLEAN) as store:
        pending_run(store)
    before = real.read_bytes()
    seed_rehearsal_store(real, tmp_path / "ensayo.sqlite")
    with OperationalStore(tmp_path / "ensayo.sqlite") as copy:
        rehearse(copy, lambda: None)
    assert real.read_bytes() == before


# --- Settings ---------------------------------------------------------------


@pytest.mark.parametrize("value, enabled", [
    ("1", True), ("true", True), ("Yes", True), ("on", True),
    ("", False), ("0", False), ("false", False), ("no", False),
])
def test_the_rehearsal_flag_reads_the_usual_spellings(monkeypatch, value, enabled):
    monkeypatch.setenv("IEKG_REHEARSAL", value)
    assert RehearsalSettings.from_environment().enabled is enabled


def test_the_rehearsal_stores_live_under_their_own_folder(monkeypatch, tmp_path):
    monkeypatch.setenv("IEKG_REHEARSAL_DIR", str(tmp_path / "ensayo"))
    settings = RehearsalSettings.from_environment()
    assert settings.operational_db == tmp_path / "ensayo" / "operational.sqlite"
    assert settings.documents_dir == tmp_path / "ensayo" / "documents"


# --- API in rehearsal mode --------------------------------------------------


@pytest.fixture
def rehearsal_api(tmp_path):
    context = ApiContext(
        TOKEN, tmp_path / "ensayo" / "operational.sqlite", tmp_path / "documents", FakeWorker(),
        FakeGraph(), FakeNavigation(), uploads_dir=tmp_path / "ensayo" / "documents", rehearsal=True,
    )
    with TestClient(create_app(context)) as client:
        yield client, context


def test_the_api_reports_rehearsal_mode(rehearsal_api):
    client, _ = rehearsal_api
    assert client.get("/api/mode", headers=AUTH).json() == {"rehearsal": True}


def test_a_rehearsed_upload_is_kept_apart_from_the_documents_the_graph_serves(rehearsal_api, tmp_path):
    client, context = rehearsal_api
    response = submit(SimpleNamespace(client=client))
    assert response.status_code == 202
    with context.store() as store:
        key = store.get_run(response.json()["run_id"]).resource_key
    assert document_path(tmp_path / "ensayo" / "documents", key).is_file()
    assert not document_path(tmp_path / "documents", key).exists()
