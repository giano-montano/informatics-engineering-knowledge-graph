"""The write templates, inside a transaction that is rolled back."""

import pytest

from iekg.core.batch import Batch, EdgeFact, NodeFact, Snapshot, SnapshotNode
from iekg.core.repository import WriteMismatch, write_batch_in
from iekg.graph_schema import (
    CONCEPT,
    COURSE,
    INSTITUTIONAL,
    KNOWLEDGE_AREA,
    KNOWLEDGE_UNIT,
    LEARNING_RESOURCE,
    PART_OF,
    PREF_LABEL_ES,
    REFERENCE,
    RESOURCE_LOCATOR,
    TEACHES_CONCEPT,
    TOPIC,
    WAS_DERIVED_FROM,
)

pytestmark = pytest.mark.neo4j


def reference_batch(area, unit, standard):
    return Batch(
        nodes=(
            NodeFact(area, KNOWLEDGE_AREA, {PREF_LABEL_ES: "Área"}),
            NodeFact(unit, KNOWLEDGE_UNIT),
            NodeFact(standard, LEARNING_RESOURCE, {RESOURCE_LOCATOR: "https://example.org/standard"}),
        ),
        edges=(EdgeFact(PART_OF, unit, area), EdgeFact(WAS_DERIVED_FROM, unit, standard)),
    )


def test_a_batch_is_written_with_its_labels_layer_and_properties(tx, new_key):
    area, unit, standard = new_key(), new_key(), new_key()
    result = write_batch_in(tx, reference_batch(area, unit, standard), Snapshot(), layer=REFERENCE)
    assert (result.nodes_created, result.relationships_created) == (3, 2)
    record = tx.run(
        "MATCH (u {key: $unit})-[:PART_OF]->(a {key: $area}) RETURN labels(u) AS labels, a",
        unit=unit, area=area,
    ).single(strict=True)
    assert sorted(record["labels"]) == ["KnowledgeElement", "KnowledgeUnit"]
    assert dict(record["a"]) == {"key": area, "layer": REFERENCE, PREF_LABEL_ES: "Área"}


def test_writing_the_same_batch_twice_creates_nothing_new(tx, new_key):
    batch = reference_batch(new_key(), new_key(), new_key())
    write_batch_in(tx, batch, Snapshot(), layer=REFERENCE)
    snapshot = Snapshot(nodes={node.key: SnapshotNode(node.label, REFERENCE) for node in batch.nodes})
    again = write_batch_in(tx, batch, snapshot, layer=REFERENCE)
    assert (again.nodes_created, again.relationships_created) == (0, 0)


def test_institutional_edges_get_the_provenance_of_the_write(tx, new_key):
    doc, course, concept, topic = new_key(), new_key(), new_key(), new_key()
    batch = Batch(
        nodes=(
            NodeFact(doc, LEARNING_RESOURCE, {RESOURCE_LOCATOR: "http://localhost/recursos/x"}),
            NodeFact(course, COURSE),
            NodeFact(topic, TOPIC),
            NodeFact(concept, CONCEPT),
        ),
        edges=(EdgeFact(TEACHES_CONCEPT, course, concept), EdgeFact(WAS_DERIVED_FROM, course, doc)),
    )
    write_batch_in(tx, batch, Snapshot(), layer=INSTITUTIONAL, provenance=doc)
    rows = tx.run(
        "MATCH ({key: $course})-[r]->() RETURN r.provenance AS provenance", course=course
    ).value()
    assert rows == [doc, doc]
    assert tx.run("MATCH (n {key: $topic}) RETURN n.layer", topic=topic).single().value() == INSTITUTIONAL


def test_an_edge_whose_endpoint_is_missing_rolls_back(tx, new_key):
    unit, area = new_key(), new_key()
    # The snapshot claims the area exists; the base does not have it.
    snapshot = Snapshot(nodes={area: SnapshotNode(KNOWLEDGE_AREA, REFERENCE)})
    batch = Batch(nodes=(NodeFact(unit, KNOWLEDGE_UNIT),), edges=(EdgeFact(PART_OF, unit, area),))
    with pytest.raises(WriteMismatch, match="1 edges sent, 0 written"):
        write_batch_in(tx, batch, snapshot, layer=REFERENCE)


def test_a_node_that_already_existed_unannounced_rolls_back(tx, new_key):
    key = new_key()
    tx.run("CREATE (:Course {key: $key, layer: 'institutional'})", key=key).consume()
    batch = Batch(nodes=(NodeFact(key, COURSE),))
    with pytest.raises(WriteMismatch, match="expected 1 new nodes, created 0"):
        write_batch_in(tx, batch, Snapshot(), layer=INSTITUTIONAL, provenance=new_key())


@pytest.mark.parametrize("batch, layer, provenance, message", [
    (Batch(nodes=(NodeFact("x", COURSE, {"credits": "4"}),)), INSTITUTIONAL, "doc", "undeclared"),
    (Batch(nodes=(NodeFact("x", COURSE, {RESOURCE_LOCATOR: "https://a.b"}),)), INSTITUTIONAL, "doc", "undeclared"),
    (Batch(nodes=(NodeFact("x", "KnowledgeElement"),)), REFERENCE, None, "not a node class"),
    (
        Batch(nodes=(NodeFact("x", COURSE), NodeFact("y", COURSE)), edges=(EdgeFact(PART_OF, "x", "y"),)),
        INSTITUTIONAL, "doc", "not admitted",
    ),
    (Batch(nodes=(NodeFact("x", COURSE),)), INSTITUTIONAL, None, "provenance"),
    (Batch(nodes=(NodeFact("x", COURSE),)), REFERENCE, "doc", "provenance"),
])
def test_the_form_of_the_write_refuses_what_the_schema_does_not_admit(tx, batch, layer, provenance, message):
    with pytest.raises(ValueError, match=message):
        write_batch_in(tx, batch, Snapshot(), layer=layer, provenance=provenance)
