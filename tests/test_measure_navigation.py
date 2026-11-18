"""The measurement of AC-05: its statistics, and a run over a small graph written
inside the rolled-back transaction."""

from types import SimpleNamespace

import pytest

from measure_navigation import PATTERNS, measure, nearest_rank, summarize

from iekg.api.navigation import GRAINS
from iekg.core.batch import Batch, EdgeFact, NodeFact, Snapshot
from iekg.core.repository import read_snapshot_in, write_batch_in
from iekg.graph_schema import (
    CONCEPT,
    COURSE,
    COURSE_CODE,
    HAS_PREREQUISITE,
    INSTITUTIONAL,
    KNOWLEDGE_AREA,
    KNOWLEDGE_UNIT,
    LEARNING_RESOURCE,
    PART_OF,
    PREF_LABEL_ES,
    REFERENCE,
    REQUIRES_CONCEPT,
    RESOURCE_LOCATOR,
    SPECIALIZES,
    TEACHES_CONCEPT,
    TOPIC,
    WAS_DERIVED_FROM,
)

# --- Statistics (no Neo4j) ------------------------------------------------------


@pytest.mark.parametrize("times, expected", [
    (range(1, 21), 19),
    (range(1, 101), 95),
    (range(1, 102), 96),
    ([7], 7),
])
def test_the_95th_percentile_is_the_value_at_the_nearest_rank(times, expected):
    assert nearest_rank(sorted(times), 0.95) == expected


def test_a_pattern_passes_only_if_its_median_and_95th_percentile_are_under_a_second():
    assert summarize([1, 2, 3, 4]) == {"executions": 4, "median_ms": 2.5, "p95_ms": 4, "max_ms": 4, "passes": True}
    assert summarize([1] * 94 + [1000] * 6)["passes"] is False
    assert summarize([1000] * 51 + [1] * 49)["passes"] is False


def test_a_pattern_without_starting_nodes_has_no_figures():
    assert summarize([]) == {"executions": 0, "median_ms": None, "p95_ms": None, "max_ms": None, "passes": None}


# --- A run over a small graph ------------------------------------------------------


def _named(key, label, name, **properties):
    return NodeFact(key, label, {PREF_LABEL_ES: name, **properties})


@pytest.fixture
def g(tx, new_key):
    """area <- unit <- topic <- c1, c2; c2 requires and specializes c1.
    Course z teaches c2 and requires c1."""
    k = SimpleNamespace(**{name: new_key() for name in "area unit cs2023 syllabus z topic c1 c2".split()})
    write_batch_in(tx, Batch(nodes=(
        _named(k.area, KNOWLEDGE_AREA, "Área"),
        _named(k.unit, KNOWLEDGE_UNIT, "Unidad"),
        _named(k.cs2023, LEARNING_RESOURCE, "CS2023", **{RESOURCE_LOCATOR: "https://example.org/cs2023"}),
    ), edges=(
        EdgeFact(PART_OF, k.unit, k.area),
        EdgeFact(WAS_DERIVED_FROM, k.area, k.cs2023),
        EdgeFact(WAS_DERIVED_FROM, k.unit, k.cs2023),
    )), Snapshot(), layer=REFERENCE)
    write_batch_in(tx, Batch(nodes=(
        _named(k.syllabus, LEARNING_RESOURCE, "Sílabo Z", **{RESOURCE_LOCATOR: "http://localhost/resources/1"}),
        _named(k.z, COURSE, "Curso Z", **{COURSE_CODE: "ZZZ"}),
        _named(k.topic, TOPIC, "Tema"),
        _named(k.c1, CONCEPT, "Concepto 1"),
        _named(k.c2, CONCEPT, "Concepto 2"),
    ), edges=(
        EdgeFact(PART_OF, k.topic, k.unit),
        EdgeFact(PART_OF, k.c1, k.topic),
        EdgeFact(PART_OF, k.c2, k.topic),
        EdgeFact(HAS_PREREQUISITE, k.c2, k.c1),
        EdgeFact(SPECIALIZES, k.c2, k.c1),
        EdgeFact(TEACHES_CONCEPT, k.z, k.c2),
        EdgeFact(REQUIRES_CONCEPT, k.z, k.c1),
    )), read_snapshot_in(tx), layer=INSTITUTIONAL, provenance=k.syllabus)
    return k


def _in(tx):
    return lambda work, *args: work(tx, *args)


@pytest.mark.neo4j
def test_every_pattern_starts_from_every_node_of_its_classes(tx, g):
    starts = {pattern.code: set(tx.run(pattern.starts).value()) for pattern in PATTERNS}
    assert {g.z} <= starts["PC2"] and not {g.c1, g.topic} & starts["PC2"]
    for code in ("PC3", "PC7"):
        assert {g.c1, g.c2} <= starts[code] and not {g.z, g.topic} & starts[code]
    for code in ("PC5", "PC6"):
        assert {g.z, g.area, g.unit, g.topic, g.c1, g.c2} <= starts[code]
    assert not any(g.syllabus in keys for keys in starts.values())


@pytest.mark.neo4j
@pytest.mark.parametrize("code", [pattern.code for pattern in PATTERNS])
def test_a_pattern_runs_a_warm_up_and_then_every_round_from_every_starting_node(tx, g, code):
    keys = {"PC2": [g.z], "PC3": [g.c1, g.c2], "PC5": [g.z, g.topic], "PC6": [g.z, g.topic], "PC7": [g.c1, g.c2]}
    starts = {pattern.code: [] for pattern in PATTERNS} | {code: keys[code]}
    measured = next(p for p in measure(_in(tx), starts, rounds=2)["patterns"] if p["pattern"] == code)
    expected = [(key, grain) for key in keys[code] for grain in (GRAINS if code == "PC6" else [None])]
    assert [(run["key"], run["grain"]) for run in measured["runs"]] == expected
    assert measured["starting_nodes"] == len(keys[code])
    assert all(len(run["ms"]) == 2 for run in measured["runs"])
    assert measured["executions"] == 2 * len(expected)
    assert measured["cold_ms"] == measured["runs"][0]["warmup_ms"]
    assert measured["passes"] is True


@pytest.mark.neo4j
def test_the_report_carries_the_greatest_depth_reached_and_the_plans(tx, g):
    starts = {"PC2": [g.z], "PC3": [g.c2], "PC5": [g.unit], "PC6": [g.c2], "PC7": [g.c2]}
    patterns = {p["pattern"]: p for p in measure(_in(tx), starts, rounds=1)["patterns"]}
    assert patterns["PC6"]["max_depth"] == 1
    assert patterns["PC7"]["max_depth"] == 1
    assert patterns["PC3"]["max_depth"] is None
    assert [plan["grain"] for plan in patterns["PC6"]["plans"]] == ["topic", "course", "area"]
    # Section 3 of the design: pruned expansions, and nothing reads the whole base.
    for pattern in patterns.values():
        for plan in pattern["plans"]:
            assert plan["operators"]
            assert plan["unpruned_expansions"] == [] and plan["full_scans"] == []


@pytest.mark.neo4j
def test_the_report_carries_the_size_of_the_graph_and_the_engine(tx, g):
    report = measure(_in(tx), {pattern.code: [] for pattern in PATTERNS}, rounds=1)
    assert report["graph"]["nodes_by_label"][CONCEPT] >= 2
    assert report["graph"]["edges_by_type"][SPECIALIZES] >= 1
    assert report["graph"]["edges"] == sum(report["graph"]["edges_by_type"].values())
    assert report["engine"]["version"] and report["engine"]["edition"]
    assert report["engine"]["processors"] >= 1
    assert all(p["executions"] == 0 and p["passes"] is None for p in report["patterns"])
