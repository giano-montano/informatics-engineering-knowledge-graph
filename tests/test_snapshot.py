"""The snapshot read, inside a transaction that is rolled back."""

import pytest

from iekg.core.batch import Batch, EdgeFact, NodeFact
from iekg.core.repository import SnapshotError, read_snapshot_in, write_batch_in
from iekg.graph_schema import (
    CONCEPT,
    HAS_PREREQUISITE,
    INSTITUTIONAL,
    KNOWLEDGE_AREA,
    KNOWLEDGE_UNIT,
    LEARNING_RESOURCE,
    PART_OF,
    PREF_LABEL_EN,
    PREF_LABEL_ES,
    REFERENCE,
    RESOURCE_LOCATOR,
    TOPIC,
    WAS_DERIVED_FROM,
)

pytestmark = pytest.mark.neo4j


@pytest.fixture
def written(tx, new_key):
    """A reference unit in its area, and a document's topic and concepts under it."""
    area, unit, doc, topic, first, second = (new_key() for _ in range(6))
    write_batch_in(tx, Batch(
        nodes=(NodeFact(area, KNOWLEDGE_AREA), NodeFact(unit, KNOWLEDGE_UNIT, {PREF_LABEL_EN: "Search"})),
        edges=(EdgeFact(PART_OF, unit, area),),
    ), read_snapshot_in(tx), layer=REFERENCE)
    batch = Batch(
        nodes=(
            NodeFact(doc, LEARNING_RESOURCE, {RESOURCE_LOCATOR: f"http://localhost/recursos/{doc}"}),
            NodeFact(topic, TOPIC, {PREF_LABEL_ES: "Búsqueda"}),
            NodeFact(first, CONCEPT),
            NodeFact(second, CONCEPT),
        ),
        edges=(
            EdgeFact(PART_OF, topic, unit),
            EdgeFact(PART_OF, first, topic),
            EdgeFact(PART_OF, second, topic),
            EdgeFact(HAS_PREREQUISITE, second, first),
        ),
    )
    write_batch_in(tx, batch, read_snapshot_in(tx), layer=INSTITUTIONAL, provenance=doc)
    return {"area": area, "unit": unit, "doc": doc, "topic": topic, "batch": batch}


def test_the_snapshot_holds_every_node_with_its_class_layer_labels_and_area(tx, written):
    nodes = read_snapshot_in(tx).nodes
    unit = nodes[written["unit"]]
    assert (unit.label, unit.layer, unit.pref_label_en, unit.area) == (
        KNOWLEDGE_UNIT, REFERENCE, "Search", written["area"],
    )
    topic = nodes[written["topic"]]
    assert (topic.label, topic.layer, topic.pref_label_es, topic.area) == (TOPIC, INSTITUTIONAL, "Búsqueda", None)
    assert nodes[written["area"]].area is None


def test_the_snapshot_holds_the_acyclic_edges_and_the_partonomy_of_topics_and_concepts(tx, written):
    edges = set(read_snapshot_in(tx).edges)
    assert set(written["batch"].edges) <= edges
    assert EdgeFact(PART_OF, written["unit"], written["area"]) not in edges
    assert not any(edge.type == WAS_DERIVED_FROM for edge in edges)


def test_writing_a_batch_again_on_its_snapshot_creates_nothing(tx, written):
    again = write_batch_in(tx, written["batch"], read_snapshot_in(tx), layer=INSTITUTIONAL, provenance=written["doc"])
    assert (again.nodes_created, again.relationships_created) == (0, 0)


@pytest.mark.parametrize("statement", [
    "CREATE (:Topic:Concept:KnowledgeElement {key: $key, layer: 'institutional'})",
    "CREATE (:Topic:KnowledgeElement {key: $key})",
    "CREATE (:Topic:KnowledgeElement {key: $key, layer: 'draft'})",
    "CREATE (:KnowledgeElement {key: $key, layer: 'reference'})",
    "CREATE (:Topic:KnowledgeElement {key: 7, layer: 'institutional'})",
    "CREATE (u:KnowledgeUnit:KnowledgeElement {key: $key, layer: 'reference'})"
    " CREATE (u)-[:PART_OF]->(:KnowledgeArea:KnowledgeElement {key: $key + 'a', layer: 'reference'})"
    " CREATE (u)-[:PART_OF]->(:KnowledgeArea:KnowledgeElement {key: $key + 'b', layer: 'reference'})",
])
def test_a_node_the_snapshot_cannot_represent_stops_the_read(tx, new_key, statement):
    tx.run(statement, key=new_key()).consume()
    with pytest.raises(SnapshotError):
        read_snapshot_in(tx)
