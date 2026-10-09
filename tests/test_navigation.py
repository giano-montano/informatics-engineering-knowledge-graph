"""The navigation queries on a small graph written inside the rolled-back transaction.

Every pattern is checked for its result, its evidence and its provenance, and
for never returning an edge the graph does not have.
"""

from types import SimpleNamespace

import pytest

from iekg.api import navigation
from iekg.api.navigation import (
    MAX_DEPTH,
    MAX_NEIGHBORS,
    MAX_NEIGHBORS_OF_NEIGHBOR,
    Subgraph,
    fetch_in,
    lucene_query,
    stopwords_in,
    words,
)
from iekg.core.batch import Batch, EdgeFact, NodeFact, Snapshot
from iekg.core.repository import read_snapshot_in, write_batch_in
from iekg.graph_schema import (
    CONCEPT,
    COURSE,
    COURSE_CODE,
    HAS_PREREQUISITE,
    HAS_RESOURCE_TYPE,
    INSTITUTIONAL,
    IS_ABOUT,
    KEY,
    KNOWLEDGE_AREA,
    KNOWLEDGE_UNIT,
    LEARNING_RESOURCE,
    PART_OF,
    PREF_LABEL_ES,
    REFERENCE,
    REQUIRES_CONCEPT,
    RESOURCE_LOCATOR,
    RESOURCE_TYPE,
    SPECIALIZES,
    TEACHES_CONCEPT,
    TOPIC,
    WAS_DERIVED_FROM,
)

# --- Words of a search (no Neo4j) -------------------------------------------


@pytest.mark.parametrize("text, expected", [
    ("Árboles", ["arboles"]),
    ("  PROGRAMACIÓN   orientada ", ["programacion", "orientada"]),
    ("cliente-servidor", ["cliente", "servidor"]),
    ("C++ (punteros)", ["c", "punteros"]),
    ("1INF33", ["1inf33"]),
    ("Ñandú über", ["nandu", "uber"]),
    ("Node.js, IEEE 802.11 y O’Reilly", ["node.js", "ieee", "802.11", "y", "o'reilly"]),
    ("snake_case. Fin.", ["snake_case", "fin"]),
    ("+-&&||!(){}[]^\"~*?:\\/", []),
])
def test_the_words_of_a_search_are_folded_and_split_like_the_index(text, expected):
    assert words(text) == expected


@pytest.mark.parametrize("text, expected", [
    ("arbol binario", "+arbol* +binario*"),
    ("Programación orientada a objetos", "+programacion* +orientada* a* +objetos*"),
    ("an", "an*"),
    ("datos datos", "+datos*"),
    ('ar* OR "x', "+ar* or* +x*"),
    ("¿?", None),
])
def test_a_search_requires_every_word_by_prefix_but_the_stop_words(text, expected):
    assert lucene_query(text, frozenset({"a", "an", "or"})) == expected


# --- A small graph ------------------------------------------------------------


def _write(tx, nodes, edges, *, layer=INSTITUTIONAL, provenance=None):
    snapshot = read_snapshot_in(tx) if layer == INSTITUTIONAL else Snapshot()
    write_batch_in(tx, Batch(nodes=tuple(nodes), edges=tuple(edges)), snapshot, layer=layer, provenance=provenance)


def _named(key, label, name, **properties):
    return NodeFact(key, label, {PREF_LABEL_ES: name, **properties})


@pytest.fixture
def g(tx, new_key):
    """area <- unit1 <- topic1 <- c1, c2 and area <- unit2 <- topic2 <- c3 .. c6.

    c2 -> c1 -> c3 -> c4 and c2 -> c4 (from syllabus2) by HAS_PREREQUISITE;
    c6 -> c5 -> c3 by SPECIALIZES. Course z teaches c1, c2 and requires c3;
    course x teaches c3, c4. syllabus1 is about z, topic1 and topic2.
    """
    names = ("area unit1 unit2 cs2023 syllabus1 syllabus2 kind z x topic1 topic2 "
             "c1 c2 c3 c4 c5 c6").split()
    k = SimpleNamespace(**{name: new_key() for name in names})
    _write(tx, [
        _named(k.area, KNOWLEDGE_AREA, "Área"),
        _named(k.unit1, KNOWLEDGE_UNIT, "Unidad 1"),
        _named(k.unit2, KNOWLEDGE_UNIT, "Unidad 2"),
        _named(k.cs2023, LEARNING_RESOURCE, "CS2023", **{RESOURCE_LOCATOR: "https://example.org/cs2023"}),
    ], [
        EdgeFact(PART_OF, k.unit1, k.area),
        EdgeFact(PART_OF, k.unit2, k.area),
        *(EdgeFact(WAS_DERIVED_FROM, key, k.cs2023) for key in (k.area, k.unit1, k.unit2)),
    ], layer=REFERENCE)
    _write(tx, [
        _named(k.syllabus1, LEARNING_RESOURCE, "Sílabo Z", **{RESOURCE_LOCATOR: "http://localhost/resources/1"}),
        _named(k.kind, RESOURCE_TYPE, "Sílabo"),
        _named(k.z, COURSE, "Curso Z", **{COURSE_CODE: "ZZZ"}),
        _named(k.x, COURSE, "Curso X", **{COURSE_CODE: "XXX"}),
        _named(k.topic1, TOPIC, "Tema 1"),
        _named(k.topic2, TOPIC, "Tema 2"),
        *(_named(getattr(k, f"c{i}"), CONCEPT, f"Concepto {i}") for i in range(1, 7)),
    ], [
        EdgeFact(HAS_RESOURCE_TYPE, k.syllabus1, k.kind),
        EdgeFact(IS_ABOUT, k.syllabus1, k.z),
        EdgeFact(IS_ABOUT, k.syllabus1, k.topic1),
        EdgeFact(IS_ABOUT, k.syllabus1, k.topic2),
        EdgeFact(PART_OF, k.topic1, k.unit1),
        EdgeFact(PART_OF, k.topic2, k.unit2),
        EdgeFact(PART_OF, k.c1, k.topic1),
        EdgeFact(PART_OF, k.c2, k.topic1),
        *(EdgeFact(PART_OF, getattr(k, f"c{i}"), k.topic2) for i in range(3, 7)),
        EdgeFact(HAS_PREREQUISITE, k.c2, k.c1),
        EdgeFact(HAS_PREREQUISITE, k.c1, k.c3),
        EdgeFact(HAS_PREREQUISITE, k.c3, k.c4),
        EdgeFact(SPECIALIZES, k.c5, k.c3),
        EdgeFact(SPECIALIZES, k.c6, k.c5),
        EdgeFact(TEACHES_CONCEPT, k.z, k.c1),
        EdgeFact(TEACHES_CONCEPT, k.z, k.c2),
        EdgeFact(REQUIRES_CONCEPT, k.z, k.c3),
        EdgeFact(TEACHES_CONCEPT, k.x, k.c3),
        EdgeFact(TEACHES_CONCEPT, k.x, k.c4),
    ], provenance=k.syllabus1)
    # A second syllabus asserts an edge between nodes the first one created.
    _write(tx, [_named(k.syllabus2, LEARNING_RESOURCE, "Sílabo X", **{RESOURCE_LOCATOR: "http://localhost/resources/2"})],
           [EdgeFact(HAS_PREREQUISITE, k.c2, k.c4)], provenance=k.syllabus2)
    return k


def fetch(tx, query) -> Subgraph:
    subgraph = fetch_in(tx, query).subgraph
    assert subgraph is not None
    assert_as_stored(tx, subgraph)
    return subgraph


def assert_as_stored(tx, subgraph: Subgraph) -> None:
    """Every edge is in the graph as returned; every edge's provenance and every
    node's derivations come with it (RF-17)."""
    present = {node.key for node in subgraph.nodes}
    assert len(present) == len(subgraph.nodes)
    for edge in subgraph.edges:
        assert {edge.source, edge.target} <= present
        stored = tx.run(
            f"MATCH (a {{{KEY}: $source}})-[r]->(b {{{KEY}: $target}}) WHERE type(r) = $type "
            "RETURN r.provenance AS provenance",
            source=edge.source, target=edge.target, type=edge.type,
        ).single()
        assert stored is not None, f"{edge} is not in the graph"
        assert stored["provenance"] == edge.provenance
        if edge.provenance is not None:
            assert edge.provenance in present
    returned = {(e.source, e.target) for e in subgraph.edges if e.type == WAS_DERIVED_FROM}
    for node in subgraph.nodes:
        stored = tx.run(
            f"MATCH (n {{{KEY}: $key}})-[:{WAS_DERIVED_FROM}]->(r) RETURN r.{KEY} AS resource", key=node.key,
        ).value()
        assert {(node.key, resource) for resource in stored} <= returned


def nodes(subgraph: Subgraph, *labels: str) -> set[str]:
    return {n.key for n in subgraph.nodes if not labels or n.label in labels}


def edges(subgraph: Subgraph, *types: str) -> set[tuple[str, str, str]]:
    return {(e.type, e.source, e.target) for e in subgraph.edges if not types or e.type in types}


def depths(subgraph: Subgraph) -> dict[str, int]:
    return {n.key: n.depth for n in subgraph.nodes if n.depth is not None}


# --- RF-11 --------------------------------------------------------------------


@pytest.mark.neo4j
def test_the_prerequisites_of_a_concept_come_transitively_with_their_depth(tx, g):
    found = fetch(tx, navigation.concept_prerequisites(g.c2))
    assert depths(found) == {g.c2: 0, g.c1: 1, g.c4: 1, g.c3: 2}
    assert nodes(found, LEARNING_RESOURCE) == {g.syllabus1, g.syllabus2}
    assert edges(found, HAS_PREREQUISITE) == {
        (HAS_PREREQUISITE, g.c2, g.c1), (HAS_PREREQUISITE, g.c1, g.c3),
        (HAS_PREREQUISITE, g.c3, g.c4), (HAS_PREREQUISITE, g.c2, g.c4),
    }


@pytest.mark.neo4j
def test_the_prerequisites_stop_at_the_maximum_depth(tx, new_key):
    resource = new_key()
    chain = [new_key() for _ in range(MAX_DEPTH + 3)]
    _write(tx, [_named(resource, LEARNING_RESOURCE, "R", **{RESOURCE_LOCATOR: "http://localhost/r"}),
                *(_named(key, CONCEPT, key) for key in chain)],
           [EdgeFact(HAS_PREREQUISITE, a, b) for a, b in zip(chain, chain[1:])], provenance=resource)
    found = fetch(tx, navigation.concept_prerequisites(chain[0]))
    assert depths(found) == {key: i for i, key in enumerate(chain[:MAX_DEPTH + 1])}


@pytest.mark.neo4j
@pytest.mark.parametrize("query", [
    navigation.concept_prerequisites, navigation.concept_specializations, navigation.course_prerequisites,
    navigation.element_location, navigation.element_resources, navigation.node_detail,
    lambda key: navigation.learning_path(key, "topic"),
])
def test_a_key_that_is_not_in_the_graph_finds_nothing(tx, new_key, query):
    assert fetch_in(tx, query(new_key())).subgraph is None


@pytest.mark.neo4j
@pytest.mark.parametrize("query, wrong", [
    (navigation.concept_prerequisites, "z"),
    (navigation.concept_specializations, "topic1"),
    (navigation.course_prerequisites, "c1"),
    (navigation.element_location, "z"),
    (navigation.element_resources, "syllabus1"),
    (lambda key: navigation.learning_path(key, "course"), "syllabus1"),
])
def test_a_key_of_another_class_finds_nothing(tx, g, query, wrong):
    assert fetch_in(tx, query(getattr(g, wrong))).subgraph is None


# --- RF-12, PC2 ---------------------------------------------------------------


@pytest.mark.neo4j
def test_a_course_comes_with_what_it_teaches_and_requires_and_the_courses_that_teach_it(tx, g):
    found = fetch(tx, navigation.course_prerequisites(g.z))
    assert nodes(found, COURSE, CONCEPT) == {g.z, g.c1, g.c2, g.c3, g.x}
    assert edges(found, TEACHES_CONCEPT, REQUIRES_CONCEPT) == {
        (TEACHES_CONCEPT, g.z, g.c1), (TEACHES_CONCEPT, g.z, g.c2),
        (REQUIRES_CONCEPT, g.z, g.c3), (TEACHES_CONCEPT, g.x, g.c3),
    }


@pytest.mark.neo4j
def test_a_course_that_requires_nothing_has_no_preceding_course(tx, g):
    found = fetch(tx, navigation.course_prerequisites(g.x))
    assert nodes(found, COURSE, CONCEPT) == {g.x, g.c3, g.c4}


# --- RF-13, PC3 ---------------------------------------------------------------


@pytest.mark.neo4j
def test_a_concept_is_located_up_to_its_area(tx, g):
    found = fetch(tx, navigation.element_location(g.c1))
    assert nodes(found) - nodes(found, LEARNING_RESOURCE) == {g.c1, g.topic1, g.unit1, g.area}
    assert edges(found, PART_OF) == {(PART_OF, g.c1, g.topic1), (PART_OF, g.topic1, g.unit1),
                                     (PART_OF, g.unit1, g.area)}
    # The reference nodes derive from CS2023, the institutional ones from the syllabus.
    assert nodes(found, LEARNING_RESOURCE) == {g.cs2023, g.syllabus1}


@pytest.mark.neo4j
def test_a_unit_comes_with_its_composition_and_the_order_of_its_concepts(tx, g):
    found = fetch(tx, navigation.element_location(g.unit1))
    assert nodes(found, KNOWLEDGE_AREA, KNOWLEDGE_UNIT, TOPIC, CONCEPT) == {g.area, g.unit1, g.topic1, g.c1, g.c2}
    # Only the prerequisites between its parts: c1 -> c3 leaves the unit.
    assert edges(found, HAS_PREREQUISITE) == {(HAS_PREREQUISITE, g.c2, g.c1)}


# --- RF-14, PC5 ---------------------------------------------------------------


@pytest.mark.neo4j
def test_the_resources_of_an_area_roll_up_over_its_parts(tx, g):
    found = fetch(tx, navigation.element_resources(g.area))
    assert nodes(found, KNOWLEDGE_UNIT, TOPIC, CONCEPT, COURSE) == {g.unit1, g.unit2, g.topic1, g.topic2}
    assert edges(found, IS_ABOUT) == {(IS_ABOUT, g.syllabus1, g.topic1), (IS_ABOUT, g.syllabus1, g.topic2)}
    assert edges(found, HAS_RESOURCE_TYPE) == {(HAS_RESOURCE_TYPE, g.syllabus1, g.kind)}


@pytest.mark.neo4j
def test_the_resources_of_a_course_are_those_about_it(tx, g):
    found = fetch(tx, navigation.element_resources(g.z))
    assert edges(found, IS_ABOUT) == {(IS_ABOUT, g.syllabus1, g.z)}


@pytest.mark.neo4j
def test_a_concept_has_no_resources_of_its_own(tx, g):
    found = fetch(tx, navigation.element_resources(g.c1))
    assert not edges(found, IS_ABOUT)
    # Its syllabus is there only as its provenance.
    assert edges(found) == {(WAS_DERIVED_FROM, g.c1, g.syllabus1)}


# --- RF-15, PC6 ---------------------------------------------------------------


@pytest.mark.neo4j
def test_a_course_lifts_its_prerequisites_to_the_courses_that_teach_them(tx, g):
    found = fetch(tx, navigation.learning_path(g.z, "course"))
    assert depths(found) == {g.z: 0, g.c1: 0, g.c2: 0, g.c3: 1, g.c4: 1, g.x: 1}
    assert edges(found, HAS_PREREQUISITE, TEACHES_CONCEPT) == {
        (HAS_PREREQUISITE, g.c1, g.c3), (HAS_PREREQUISITE, g.c2, g.c4), (HAS_PREREQUISITE, g.c3, g.c4),
        # Between two concepts inside the target: still an edge between the nodes.
        (HAS_PREREQUISITE, g.c2, g.c1),
        (TEACHES_CONCEPT, g.z, g.c1), (TEACHES_CONCEPT, g.z, g.c2),
        (TEACHES_CONCEPT, g.x, g.c3), (TEACHES_CONCEPT, g.x, g.c4),
    }


@pytest.mark.neo4j
def test_a_topic_lifts_its_prerequisites_to_their_topics(tx, g):
    found = fetch(tx, navigation.learning_path(g.topic1, "topic"))
    assert depths(found) == {g.topic1: 0, g.c1: 0, g.c2: 0, g.c3: 1, g.c4: 1, g.topic2: 1}
    assert {(s, t) for _, s, t in edges(found, PART_OF)} == {
        (g.c1, g.topic1), (g.c2, g.topic1), (g.c3, g.topic2), (g.c4, g.topic2),
    }


@pytest.mark.neo4j
def test_a_unit_lifts_its_prerequisites_to_their_area_through_topic_and_unit(tx, g):
    found = fetch(tx, navigation.learning_path(g.unit1, "area"))
    assert depths(found) == {g.unit1: 0, g.topic1: 0, g.c1: 0, g.c2: 0, g.c3: 1, g.c4: 1, g.area: 1}
    assert {g.topic2, g.unit2} <= nodes(found)
    assert (PART_OF, g.unit2, g.area) in edges(found)


@pytest.mark.neo4j
def test_a_concept_lifts_only_what_lies_outside_it(tx, g):
    found = fetch(tx, navigation.learning_path(g.c3, "topic"))
    assert depths(found) == {g.c3: 0, g.c4: 1, g.topic2: 1}


@pytest.mark.neo4j
def test_an_area_whose_prerequisites_are_all_inside_it_needs_nothing(tx, g):
    found = fetch(tx, navigation.learning_path(g.area, "area"))
    assert depths(found) == {g.area: 0}


# --- RF-16, PC7 ---------------------------------------------------------------


@pytest.mark.neo4j
def test_the_specialization_closure_goes_both_ways(tx, g):
    found = fetch(tx, navigation.concept_specializations(g.c5))
    assert depths(found) == {g.c5: 0, g.c3: 1, g.c6: 1}
    found = fetch(tx, navigation.concept_specializations(g.c6))
    assert depths(found) == {g.c6: 0, g.c5: 1, g.c3: 2}
    assert edges(found, SPECIALIZES) == {(SPECIALIZES, g.c6, g.c5), (SPECIALIZES, g.c5, g.c3)}


# --- Detail of a node -----------------------------------------------------------


@pytest.mark.neo4j
def test_the_detail_of_a_node_brings_its_neighbors_but_not_by_derivation(tx, g):
    found = fetch(tx, navigation.node_detail(g.c1))
    by_key = {n.key: n for n in found.nodes}
    focus = by_key[g.c1]
    assert focus.has_description and focus.depth is None
    assert {g.topic1, g.c3, g.c2, g.z} <= nodes(found)
    # What derives from CS2023 is not its neighbor: it would bring the whole backbone.
    found = fetch(tx, navigation.node_detail(g.cs2023))
    assert nodes(found) == {g.cs2023} and not found.edges


@pytest.mark.neo4j
def test_the_detail_of_a_node_keeps_a_fixed_number_of_neighbors_in_a_fixed_order(tx, g, new_key):
    focus, resource = new_key(), new_key()
    parts = [new_key() for _ in range(MAX_NEIGHBORS + 5)]
    _write(tx, [_named(resource, LEARNING_RESOURCE, "R", **{RESOURCE_LOCATOR: "http://localhost/r"}),
                _named(focus, TOPIC, "Foco"),
                *(_named(key, CONCEPT, f"Parte {i:02}") for i, key in enumerate(parts))],
           [EdgeFact(PART_OF, focus, g.unit1), *(EdgeFact(PART_OF, key, focus) for key in parts)],
           provenance=resource)
    found = fetch(tx, navigation.node_detail(focus))
    # Outgoing first: the unit it is part of survives the cut.
    assert nodes(found, CONCEPT) == set(parts[:MAX_NEIGHBORS - 1])
    assert g.unit1 in nodes(found)
    by_key = {n.key: n for n in found.nodes}
    assert by_key[focus].more_neighbors
    again = fetch(tx, navigation.node_detail(focus))
    assert (set(again.nodes), set(again.edges)) == (set(found.nodes), set(found.edges))


@pytest.mark.neo4j
def test_the_detail_of_a_node_keeps_a_few_neighbors_of_each_neighbor(tx, g, new_key):
    focus, topic, resource = new_key(), new_key(), new_key()
    siblings = [new_key() for _ in range(MAX_NEIGHBORS_OF_NEIGHBOR + 3)]
    _write(tx, [_named(resource, LEARNING_RESOURCE, "R", **{RESOURCE_LOCATOR: "http://localhost/r"}),
                _named(topic, TOPIC, "Tema"), _named(focus, CONCEPT, "Foco"),
                *(_named(key, CONCEPT, f"Hermano {i:02}") for i, key in enumerate(siblings))],
           [EdgeFact(PART_OF, topic, g.unit1), EdgeFact(PART_OF, focus, topic),
            *(EdgeFact(PART_OF, key, topic) for key in siblings)],
           provenance=resource)
    found = fetch(tx, navigation.node_detail(focus))
    by_key = {n.key: n for n in found.nodes}
    # The topic's own neighbors: the unit first (outgoing), then its parts by name.
    assert nodes(found, KNOWLEDGE_UNIT, TOPIC, CONCEPT) - {focus, topic} == {
        g.unit1, *siblings[:MAX_NEIGHBORS_OF_NEIGHBOR - 1],
    }
    assert not by_key[focus].more_neighbors
    assert by_key[topic].more_neighbors


# --- RF-18 --------------------------------------------------------------------


@pytest.fixture
def named(tx, new_key):
    resource = new_key()
    k = SimpleNamespace(tree=new_key(), oop=new_key(), course=new_key(), resource=resource)
    _write(tx, [
        _named(resource, LEARNING_RESOURCE, "R", **{RESOURCE_LOCATOR: "http://localhost/r"}),
        _named(k.tree, TOPIC, "Árboles xilófagos binarios"),
        _named(k.oop, CONCEPT, "Programación xilófaga orientada a objetos"),
        _named(k.course, COURSE, "Xilofagia", **{COURSE_CODE: "9XIL99"}),
    ], [], provenance=resource)
    return k


def search(tx, text):
    query = navigation.search(text, stopwords_in(tx))
    return fetch(tx, query) if query else Subgraph()


@pytest.mark.neo4j
@pytest.mark.parametrize("text, expected", [
    ("XILÓFAG", {"tree", "oop", "course"}),
    ("arbol xilo", {"tree"}),
    ("xilof binarios objetos", set()),
    ("programación xilófaga orientada a objetos", {"oop"}),
    ("9xil99", {"course"}),
    ("xilofagia", {"course"}),
    ('xilo* AND (binarios" OR ~', {"tree"}),
])
def test_the_search_finds_every_word_by_prefix_ignoring_accents_and_case(tx, named, text, expected):
    found = search(tx, text)
    ours = {name for name in ("tree", "oop", "course") if getattr(named, name) in nodes(found)}
    assert ours == expected
    assert all(n.score is not None for n in found.nodes if n.label != LEARNING_RESOURCE)


@pytest.mark.neo4j
def test_a_search_result_comes_with_its_provenance(tx, named):
    found = search(tx, "arboles xilofagos")
    assert edges(found) == {(WAS_DERIVED_FROM, named.tree, named.resource)}


@pytest.mark.neo4j
def test_the_stop_words_are_those_of_the_index_analyzer(tx):
    assert {"a", "no", "the"} <= stopwords_in(tx)


@pytest.mark.neo4j
@pytest.mark.parametrize("name", [
    "Node.js en el servidor", "Protocolos TCP/IP", "Lenguaje C#", "Arquitectura cliente-servidor",
    "Web 2.0", "IEEE 802.11", "O’Reilly", "Aprendizaje no supervisado", "Programación orientada a objetos",
])
def test_a_name_typed_in_full_finds_itself(tx, new_key, name):
    key, resource = new_key(), new_key()
    _write(tx, [_named(resource, LEARNING_RESOURCE, "R", **{RESOURCE_LOCATOR: "http://localhost/r"}),
                _named(key, TOPIC, name)], [], provenance=resource)
    assert key in nodes(search(tx, name))
