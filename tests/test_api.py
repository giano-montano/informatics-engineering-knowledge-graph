"""The API on a fake worker launcher, a fake graph lookup and fake navigation queries.

The operational store is a real SQLite file under ``tmp_path``. The lookup of
a resource in Neo4j has its own test, marked ``neo4j``; the navigation
queries have theirs in ``test_navigation.py``.
"""

import sys
import threading
from collections.abc import Callable
from contextlib import contextmanager
from dataclasses import dataclass, field
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from iekg.api import navigation
from iekg.api.app import ApiContext, create_app
from iekg.api.navigation import GraphEdge, GraphNode, Subgraph
from iekg.api.server import ChildWorker, resource_exists_in, should_relaunch
from iekg.core.auditor import AuditReport, RuleResult
from iekg.core.batch import Batch, NodeFact, Snapshot
from iekg.core.repository import write_batch_in
from iekg.graph_schema import (
    CONCEPT,
    COURSE,
    INSTITUTIONAL,
    KEY,
    LAYER,
    LEARNING_RESOURCE,
    REFERENCE,
    RESOURCE_LOCATOR,
    WAS_DERIVED_FROM,
)
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
    fails: bool = False
    # What another worker does before this launch fails.
    meanwhile: Callable[[], object] = lambda: None

    def ensure_running(self) -> bool:
        if self.active:
            return False
        if self.fails:
            self.meanwhile()
            raise OSError("cannot start the worker")
        self.active, self.launches = True, self.launches + 1
        return True


@dataclass
class FakeGraph:
    resources: set[str] = field(default_factory=set)

    def has_resource(self, key: str) -> bool:
        return key in self.resources


@dataclass
class FakeNavigation:
    """Answers every query with ``subgraph``; None stands for a key it does not find."""

    subgraph: Subgraph | None = field(default_factory=Subgraph)
    queries: list[navigation.Query] = field(default_factory=list)

    def fetch(self, query: navigation.Query) -> Subgraph | None:
        self.queries.append(query)
        return self.subgraph

    def stopwords(self) -> frozenset[str]:
        return frozenset({"a"})


@dataclass
class Api:
    client: TestClient
    context: ApiContext
    worker: FakeWorker
    graph: FakeGraph
    navigation: FakeNavigation

    def store(self) -> OperationalStore:
        return self.context.store()


@contextmanager
def serving(tmp_path, worker: FakeWorker):
    graph, nav = FakeGraph(), FakeNavigation()
    context = ApiContext(TOKEN, tmp_path / "operational.sqlite", tmp_path / "documents", worker, graph, nav)
    with TestClient(create_app(context)) as client:
        yield Api(client, context, worker, graph, nav)


@pytest.fixture
def api(tmp_path) -> Api:
    with serving(tmp_path, FakeWorker()) as api:
        yield api


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


def test_a_submission_whose_worker_cannot_be_launched_records_nothing(api):
    api.worker.fails = True
    response = submit(api)
    assert response.status_code == 503
    assert "nothing was recorded" in response.json()["detail"]
    with api.store() as store:
        assert store.list_runs() == []
    assert not any(api.context.documents_dir.glob("*"))


def test_a_submission_another_worker_took_before_the_launch_failed_is_accepted(api):
    def take():
        with api.store() as store:
            store.take_pending_run()

    api.worker.fails, api.worker.meanwhile = True, take
    response = submit(api)
    assert response.status_code == 202
    assert response.json() == {"run_id": 1, "worker_launched": False}


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


# --- Launch at start-up (ADR-007) -------------------------------------------


def leave(tmp_path, *, pending: int, gate_open: bool):
    with OperationalStore(tmp_path / "operational.sqlite") as store:
        if gate_open:
            store.complete_audit_report(store.open_audit_report(origin=LOAD), CLEAN)
        for _ in range(pending):
            store.create_run(resource_key=str(uuid4()), resource_type=SYLLABUS, course_code="1INF33",
                             course_name="Bases de Datos", file_name="silabo.pdf")


@pytest.mark.parametrize("pending, gate_open, launches", [(1, True, 1), (0, True, 0), (1, False, 0)])
def test_the_api_launches_the_worker_at_start_up_only_if_it_has_work(tmp_path, pending, gate_open, launches):
    leave(tmp_path, pending=pending, gate_open=gate_open)
    with serving(tmp_path, FakeWorker()) as api:
        assert api.worker.launches == launches


def test_the_api_starts_even_if_it_cannot_launch_the_worker(tmp_path):
    leave(tmp_path, pending=1, gate_open=True)
    with serving(tmp_path, FakeWorker(fails=True)) as api:
        assert [run["status"] for run in api.client.get("/api/runs", headers=AUTH).json()] == [PENDING]


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


# --- Navigation (RF-11 to RF-18) ----------------------------------------------

KEY_ROUTES = [
    ("/api/nodes", navigation.node_detail),
    ("/api/concepts/prerequisites", navigation.concept_prerequisites),
    ("/api/courses/prerequisites", navigation.course_prerequisites),
    ("/api/elements/location", navigation.element_location),
    ("/api/elements/resources", navigation.element_resources),
    ("/api/concepts/specializations", navigation.concept_specializations),
]
IRI = "https://example.org/cs2023#KA-AI"


@pytest.mark.parametrize("path, query", KEY_ROUTES)
def test_a_navigation_route_runs_its_query_without_the_token(api, path, query):
    response = api.client.get(path, params={"key": IRI})
    assert response.status_code == 200
    assert response.json() == {"nodes": [], "edges": []}
    assert api.navigation.queries == [query(IRI)]


@pytest.mark.parametrize("grain", ["topic", "course", "area"])
def test_the_learning_path_runs_with_its_grain(api, grain):
    assert api.client.get("/api/learning-path", params={"key": IRI, "grain": grain}).status_code == 200
    assert api.navigation.queries == [navigation.learning_path(IRI, grain)]


@pytest.mark.parametrize("path, params", [(path, {}) for path, _ in KEY_ROUTES] + [
    ("/api/learning-path", {"grain": "topic"}),
])
def test_a_key_the_graph_does_not_have_is_not_found(api, path, params):
    api.navigation.subgraph = None
    response = api.client.get(path, params={"key": IRI, **params})
    assert response.status_code == 404
    assert "with this key" in response.json()["detail"]


@pytest.mark.parametrize("path, params", [
    ("/api/nodes", {}),
    ("/api/nodes", {"key": ""}),
    ("/api/learning-path", {"key": IRI}),
    ("/api/learning-path", {"key": IRI, "grain": "unit"}),
    ("/api/search", {}),
    ("/api/search", {"q": ""}),
    ("/api/search", {"q": "x" * 201}),
])
def test_a_navigation_route_refuses_wrong_parameters(api, path, params):
    assert api.client.get(path, params=params).status_code == 422
    assert api.navigation.queries == []


def test_the_search_sends_every_word_as_a_prefix(api):
    assert api.client.get("/api/search", params={"q": "Orientada a OBJETOS"}).status_code == 200
    [query] = api.navigation.queries
    assert query.parameters["lucene"] == "+orientada* a* +objetos*"


def test_a_search_without_words_finds_nothing_and_asks_nothing(api):
    response = api.client.get("/api/search", params={"q": "+-*?"})
    assert response.json() == {"nodes": [], "edges": []}
    assert api.navigation.queries == []


def test_a_node_carries_only_what_applies_to_its_class(api):
    api.navigation.subgraph = Subgraph(
        nodes=(
            GraphNode("c", CONCEPT, INSTITUTIONAL, "Punteros", None, depth=1),
            GraphNode("z", COURSE, INSTITUTIONAL, "Algoritmia", None, course_code="1INF99", depth=0),
            GraphNode("r", LEARNING_RESOURCE, INSTITUTIONAL, "Sílabo 1INF99", None, locator="http://h/resources/r"),
            GraphNode("t", CONCEPT, INSTITUTIONAL, "Árboles", None, more_neighbors=False,
                      has_description=True, description=None),
        ),
        edges=(GraphEdge(WAS_DERIVED_FROM, "c", "r", "r"),),
    )
    body = api.client.get("/api/nodes", params={"key": "c"}).json()
    common = {"name_en": None, "layer": INSTITUTIONAL}
    assert body["nodes"] == [
        {"key": "c", "label": CONCEPT, "name_es": "Punteros", **common, "depth": 1},
        {"key": "z", "label": COURSE, "name_es": "Algoritmia", **common, "course_code": "1INF99", "depth": 0},
        {"key": "r", "label": LEARNING_RESOURCE, "name_es": "Sílabo 1INF99", **common,
         "locator": "http://h/resources/r"},
        {"key": "t", "label": CONCEPT, "name_es": "Árboles", **common, "description": None,
         "more_neighbors": False},
    ]
    assert body["edges"] == [{"type": WAS_DERIVED_FROM, "source": "c", "target": "r", "provenance": "r"}]


# --- Real adapters ----------------------------------------------------------


def test_the_child_worker_is_launched_again_only_once_the_last_one_ended():
    worker = ChildWorker(lambda: False, [sys.executable, "-c", "import time; time.sleep(1)"])
    assert worker.ensure_running()
    assert not worker.ensure_running()
    worker._process.wait(timeout=10)
    assert worker.ensure_running()
    worker._process.wait(timeout=10)


@pytest.mark.parametrize("exit_code, work, relaunch", [(0, True, True), (0, False, False), (3, True, False)])
def test_a_worker_is_relaunched_only_after_a_clean_end_with_work_left(exit_code, work, relaunch):
    assert should_relaunch(exit_code, lambda: work) == relaunch


def test_the_child_worker_relaunches_itself_while_there_is_work():
    answers, asked_twice = [True, False], threading.Event()

    def has_work():
        answer = answers.pop(0)
        if not answers:
            asked_twice.set()
        return answer

    worker = ChildWorker(has_work, [sys.executable, "-c", "pass"])
    assert worker.ensure_running()
    # Asked a second time only once a second child ended.
    assert asked_twice.wait(timeout=10)


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
