"""The API on a fake worker launcher and a fake graph lookup.

The operational store is a real SQLite file under ``tmp_path``. The lookup of
a resource in Neo4j has its own test, marked ``neo4j``.
"""

import sys
from dataclasses import dataclass, field
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from iekg.api.app import ApiContext, create_app
from iekg.api.server import ChildWorker, resource_exists_in
from iekg.core.auditor import AuditReport, RuleResult
from iekg.core.batch import Batch, NodeFact, Snapshot
from iekg.core.repository import write_batch_in
from iekg.graph_schema import INSTITUTIONAL, KEY, LAYER, LEARNING_RESOURCE, REFERENCE, RESOURCE_LOCATOR
from iekg.ingestion.declared import SYLLABUS
from iekg.ingestion.orchestrator import NO_REPORT, REPORT_OPEN, REPORT_WITH_VIOLATIONS, document_path
from iekg.operational_store import INGESTION, LOAD, PENDING, Discard, OperationalStore

TOKEN = "s3cret-operator-token"
AUTH = {"Authorization": f"Bearer {TOKEN}"}
PDF = b"%PDF-1.7\n%fake body\n"
CLEAN = AuditReport((RuleResult("RI-01", 0, ()),))
DIRTY = AuditReport((RuleResult("RI-08", 1, ("x (Topic) is not part of any KnowledgeUnit",)),))


@dataclass
class FakeWorker:
    active: bool = False
    launches: int = 0

    def ensure_running(self) -> bool:
        if self.active:
            return False
        self.active, self.launches = True, self.launches + 1
        return True


@dataclass
class FakeGraph:
    resources: set[str] = field(default_factory=set)

    def has_resource(self, key: str) -> bool:
        return key in self.resources


@dataclass
class Api:
    client: TestClient
    context: ApiContext
    worker: FakeWorker
    graph: FakeGraph

    def store(self) -> OperationalStore:
        return self.context.store()


@pytest.fixture
def api(tmp_path) -> Api:
    worker, graph = FakeWorker(), FakeGraph()
    context = ApiContext(TOKEN, tmp_path / "operational.sqlite", tmp_path / "documents", worker, graph)
    with TestClient(create_app(context)) as client:
        yield Api(client, context, worker, graph)


def submit(api, content=PDF, file_name="silabo.pdf", headers=AUTH, **form):
    data = {"resource_type": SYLLABUS, "course_code": "1INF33", "course_name": "Bases de Datos"} | form
    return api.client.post(
        "/api/runs", headers=headers, data=data, files={"file": (file_name, content, "application/pdf")},
    )


# --- Operator token ---------------------------------------------------------


@pytest.mark.parametrize("method, path", [
    ("post", "/api/runs"),
    ("get", "/api/runs"),
    ("get", "/api/runs/1"),
    ("get", "/api/runs/1/discards"),
    ("get", "/api/audit-reports/latest"),
])
@pytest.mark.parametrize("headers", [
    {},
    {"Authorization": "Bearer wrong-token"},
    {"Authorization": f"Basic {TOKEN}"},
])
def test_every_operation_route_refuses_a_request_without_the_token(api, method, path, headers):
    response = getattr(api.client, method)(path, headers=headers)
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


def test_a_refused_submission_records_nothing_and_launches_nothing(api):
    assert submit(api, headers={"Authorization": "Bearer wrong-token"}).status_code == 401
    with api.store() as store:
        assert store.list_runs() == []
    assert api.worker.launches == 0


# --- Submission (RF-02) -----------------------------------------------------


def test_a_submission_records_a_pending_run_and_launches_the_worker(api):
    response = submit(api)
    assert response.status_code == 202
    assert response.json() == {"run_id": 1, "worker_launched": True}
    with api.store() as store:
        run = store.get_run(1)
    assert (run.status, run.file_name, run.course_code) == (PENDING, "silabo.pdf", "1INF33")
    assert document_path(api.context.documents_dir, run.resource_key).read_bytes() == PDF


def test_a_submission_while_the_worker_runs_does_not_launch_another(api):
    submit(api)
    response = submit(api)
    assert response.json() == {"run_id": 2, "worker_launched": False}
    assert api.worker.launches == 1


@pytest.mark.parametrize("content, file_name", [(b"just text", "silabo.pdf"), (PDF, "silabo.txt")])
def test_a_submission_that_is_not_a_pdf_is_refused(api, content, file_name):
    response = submit(api, content=content, file_name=file_name)
    assert response.status_code == 422
    assert "not a PDF" in response.json()["detail"]
    assert api.worker.launches == 0


@pytest.mark.parametrize("form, detail", [
    ({"resource_type": "Libro"}, "unknown resource type"),
    ({"course_code": "  "}, "code and the name"),
    ({"course_name": "   "}, "code and the name"),
])
def test_a_submission_with_a_wrong_declaration_is_refused(api, form, detail):
    response = submit(api, **form)
    assert response.status_code == 422
    assert detail in response.json()["detail"]
    with api.store() as store:
        assert store.list_runs() == []


@pytest.mark.parametrize("field", ["resource_type", "course_code", "course_name"])
def test_a_submission_that_leaves_out_a_declared_field_is_refused(api, field):
    data = {"resource_type": SYLLABUS, "course_code": "1INF33", "course_name": "Bases de Datos"}
    del data[field]
    response = api.client.post("/api/runs", headers=AUTH, data=data, files={"file": ("silabo.pdf", PDF)})
    assert response.status_code == 422
    assert [error["loc"] for error in response.json()["detail"]] == [["body", field]]
    with api.store() as store:
        assert store.list_runs() == []


def test_a_submission_without_a_file_is_refused(api):
    response = api.client.post("/api/runs", headers=AUTH, data={"resource_type": SYLLABUS})
    assert response.status_code == 422


# --- Runs and discards (RF-03, RF-05) ---------------------------------------


def test_the_runs_are_listed_in_order(api):
    submit(api)
    submit(api, course_code="1INF25", course_name="Algoritmia")
    runs = api.client.get("/api/runs", headers=AUTH).json()
    assert [(r["id"], r["course_code"], r["status"]) for r in runs] == [(1, "1INF33", PENDING), (2, "1INF25", PENDING)]


def test_a_run_comes_with_the_audit_report_that_closed_it(api):
    submit(api)
    with api.store() as store:
        run = store.take_pending_run()
        report_id = store.open_audit_report(origin=INGESTION, run_id=str(run.id))
        store.attach_audit_report(run.id, report_id)
        store.complete_audit_report(report_id, DIRTY)
    body = api.client.get("/api/runs/1", headers=AUTH).json()
    assert body["resource_key"] == run.resource_key
    assert body["audit_report"]["id"] == report_id
    assert body["audit_report"]["violations"] == 1
    assert body["audit_report"]["rules"] == [
        {"rule": "RI-08", "violations": 1, "sample": ["x (Topic) is not part of any KnowledgeUnit"]},
    ]


def test_a_run_without_an_audit_has_no_report(api):
    submit(api)
    assert api.client.get("/api/runs/1", headers=AUTH).json()["audit_report"] is None


@pytest.mark.parametrize("path", ["/api/runs/99", "/api/runs/99/discards"])
def test_a_run_that_does_not_exist_is_not_found(api, path):
    assert api.client.get(path, headers=AUTH).status_code == 404


def test_a_rejected_run_shows_its_discards_and_its_batch(api):
    submit(api)
    batch = Batch(nodes=(NodeFact("a", "Concept"),))
    with api.store() as store:
        store.take_pending_run()
        store.reject_run(1, [Discard("RI-08", "a", "a (Concept) is not part of any Topic")], batch=batch)
    body = api.client.get("/api/runs/1/discards", headers=AUTH).json()
    assert body["discards"] == [{"rule": "RI-08", "fact": "a", "message": "a (Concept) is not part of any Topic"}]
    assert body["batch"] == {"nodes": [{"key": "a", "label": "Concept", "properties": {}}], "edges": []}
    assert body["raw_output"] is None


def test_a_run_that_was_not_rejected_has_no_discards(api):
    submit(api)
    body = api.client.get("/api/runs/1/discards", headers=AUTH).json()
    assert body == {"discards": [], "batch": None, "raw_output": None}


# --- Audit report and gate (RF-23) ------------------------------------------


def test_the_gate_is_open_after_a_clean_report(api):
    with api.store() as store:
        store.complete_audit_report(store.open_audit_report(origin=LOAD), CLEAN)
    body = api.client.get("/api/audit-reports/latest", headers=AUTH).json()
    assert body["gate"] == {"state": "open", "reason": None}
    assert body["report"]["origin"] == LOAD and body["report"]["completed"]


@pytest.mark.parametrize("reports, reason", [
    ((), NO_REPORT),
    ((CLEAN, None), REPORT_OPEN),
    ((CLEAN, DIRTY), REPORT_WITH_VIOLATIONS),
])
def test_the_gate_is_closed_as_the_worker_sees_it(api, reports, reason):
    with api.store() as store:
        for report in reports:
            report_id = store.open_audit_report(origin=LOAD)
            if report is not None:
                store.complete_audit_report(report_id, report)
    body = api.client.get("/api/audit-reports/latest", headers=AUTH).json()
    assert body["gate"] == {"state": "closed", "reason": reason}
    assert (body["report"] is None) == (not reports)


# --- Documents (RF-24) ------------------------------------------------------


def submitted_key(api):
    submit(api)
    with api.store() as store:
        return store.get_run(1).resource_key


def test_a_resource_of_the_graph_serves_its_document_without_the_token(api):
    key = submitted_key(api)
    api.graph.resources.add(key)
    response = api.client.get(f"/resources/{key}")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content == PDF


def test_a_document_whose_resource_is_not_in_the_graph_is_not_served(api):
    # Submitted but not ingested yet, or erased by a load before the reapplication.
    key = submitted_key(api)
    assert api.client.get(f"/resources/{key}").status_code == 404


def test_a_resource_of_the_graph_without_its_file_is_not_found(api):
    key = str(uuid4())
    api.graph.resources.add(key)
    assert api.client.get(f"/resources/{key}").status_code == 404


@pytest.mark.parametrize("key", ["not-a-uuid", "..%2Foperational.sqlite"])
def test_a_key_that_is_not_a_uuid_is_refused(api, key):
    assert api.client.get(f"/resources/{key}").status_code in (404, 422)


# --- Real adapters ----------------------------------------------------------


def test_the_child_worker_is_launched_again_only_once_the_last_one_ended():
    worker = ChildWorker([sys.executable, "-c", "import time; time.sleep(1)"])
    assert worker.ensure_running()
    assert not worker.ensure_running()
    worker._process.wait(timeout=10)
    assert worker.ensure_running()
    worker._process.wait(timeout=10)


@pytest.mark.neo4j
@pytest.mark.parametrize("layer, found", [(INSTITUTIONAL, True), (REFERENCE, False)])
def test_only_an_institutional_learning_resource_is_found(tx, new_key, layer, found):
    key = new_key()
    assert not resource_exists_in(tx, key)
    resource = NodeFact(key, LEARNING_RESOURCE, {RESOURCE_LOCATOR: f"http://localhost:8000/resources/{key}"})
    provenance = key if layer == INSTITUTIONAL else None
    write_batch_in(tx, Batch(nodes=(resource,)), Snapshot(), layer=layer, provenance=provenance)
    assert tx.run(f"MATCH (r {{{KEY}: $key}}) RETURN r.{LAYER} AS layer", key=key).single()["layer"] == layer
    assert resource_exists_in(tx, key) == found
