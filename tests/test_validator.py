import pytest

from iekg.core.batch import Batch, EdgeFact, NodeFact, Snapshot, SnapshotNode
from iekg.core.rules import RI_05, RI_08, RI_10, RM_02, RM_04, RM_05
from iekg.core.validator import INGESTION_RULES, LOAD_RULES, validate
from iekg.graph_schema import (
    CONCEPT,
    COURSE,
    HAS_PREREQUISITE,
    INSTITUTIONAL,
    KNOWLEDGE_AREA,
    KNOWLEDGE_UNIT,
    LEARNING_RESOURCE,
    PART_OF,
    REFERENCE,
    RESOURCE_LOCATOR,
    SPECIALIZES,
    TEACHES_CONCEPT,
    TOPIC,
)

UNIT = SnapshotNode(KNOWLEDGE_UNIT, REFERENCE)
LOCATOR = {RESOURCE_LOCATOR: "https://example.org/syllabus.pdf"}
EMPTY = Snapshot()


def rules_of(violations):
    return [violation.rule for violation in violations]


def ingest(batch, snapshot=EMPTY):
    return validate(batch, snapshot, layer=INSTITUTIONAL, rules=INGESTION_RULES)


def load(batch):
    return validate(batch, Snapshot(), layer=REFERENCE, rules=LOAD_RULES)


def test_a_valid_batch_has_no_violations():
    snapshot = Snapshot(nodes={"ku": UNIT})
    batch = Batch(
        nodes=(NodeFact("t", TOPIC), NodeFact("c", CONCEPT), NodeFact("doc", LEARNING_RESOURCE, LOCATOR)),
        edges=(EdgeFact(PART_OF, "t", "ku"), EdgeFact(PART_OF, "c", "t")),
    )
    assert ingest(batch, snapshot) == []


# RI-05


def test_an_edge_type_outside_the_schema_is_rejected():
    batch = Batch(nodes=(NodeFact("a", CONCEPT), NodeFact("b", CONCEPT)), edges=(EdgeFact("RELATED_TO", "a", "b"),))
    assert RI_05 in rules_of(load(batch))


def test_a_pair_not_admitted_for_the_type_is_rejected():
    batch = Batch(
        nodes=(NodeFact("area", KNOWLEDGE_AREA), NodeFact("unit", KNOWLEDGE_UNIT)),
        edges=(EdgeFact(PART_OF, "area", "unit"), EdgeFact(PART_OF, "unit", "area")),
    )
    violations = load(batch)
    assert [v.fact for v in violations] == ["(area)-[:PART_OF]->(unit)"]


def test_an_edge_to_a_node_that_does_not_exist_is_rejected():
    batch = Batch(nodes=(NodeFact("unit", KNOWLEDGE_UNIT),), edges=(EdgeFact(PART_OF, "unit", "nowhere"),))
    assert rules_of(load(batch)) == [RI_05]


# RI-08


def test_a_new_node_without_its_partonomy_edge_is_rejected():
    batch = Batch(nodes=(NodeFact("c", CONCEPT),))
    assert rules_of(ingest(batch)) == [RI_08]


def test_a_partonomy_edge_to_the_wrong_level_does_not_anchor():
    snapshot = Snapshot(nodes={"ku": UNIT})
    batch = Batch(nodes=(NodeFact("c", CONCEPT),), edges=(EdgeFact(PART_OF, "c", "ku"),))
    assert sorted(rules_of(ingest(batch, snapshot))) == [RI_05, RI_08]


def test_an_existing_node_needs_no_new_partonomy_edge():
    snapshot = Snapshot(nodes={"t": SnapshotNode(TOPIC, INSTITUTIONAL)})
    assert ingest(Batch(nodes=(NodeFact("t", TOPIC),)), snapshot) == []


def test_the_load_leaves_anchoring_to_the_audit():
    # Annex, Table 3: in the load, RI-08 is only detected by the audit.
    assert load(Batch(nodes=(NodeFact("unit", KNOWLEDGE_UNIT),))) == []


# RI-10 and RM-05


def test_a_locator_that_is_not_an_http_uri_is_rejected():
    batch = Batch(nodes=(NodeFact("doc", LEARNING_RESOURCE, {RESOURCE_LOCATOR: "file:///tmp/a.pdf"}),))
    assert rules_of(load(batch)) == [RI_10]


def test_a_learning_resource_without_locator_is_rejected():
    assert rules_of(load(Batch(nodes=(NodeFact("doc", LEARNING_RESOURCE),)))) == [RM_05]


# RM-02


def test_an_edge_from_the_reference_layer_into_the_institutional_one_is_rejected():
    snapshot = Snapshot(nodes={"course": SnapshotNode(COURSE, REFERENCE)})
    batch = Batch(nodes=(NodeFact("c", CONCEPT),), edges=(EdgeFact(TEACHES_CONCEPT, "course", "c"),))
    violations = validate(batch, snapshot, layer=INSTITUTIONAL, rules=[RM_02])
    assert rules_of(violations) == [RM_02]


def test_an_edge_from_the_institutional_layer_into_the_reference_one_is_admitted():
    snapshot = Snapshot(nodes={"ku": UNIT})
    batch = Batch(nodes=(NodeFact("t", TOPIC),), edges=(EdgeFact(PART_OF, "t", "ku"),))
    assert validate(batch, snapshot, layer=INSTITUTIONAL, rules=[RM_02]) == []


# RM-04


def concepts(*keys):
    return tuple(NodeFact(key, CONCEPT) for key in keys)


@pytest.mark.parametrize("edge_type", [HAS_PREREQUISITE, SPECIALIZES])
def test_a_cycle_inside_the_batch_is_rejected(edge_type):
    batch = Batch(
        nodes=concepts("a", "b", "c"),
        edges=(EdgeFact(edge_type, "a", "b"), EdgeFact(edge_type, "b", "c"), EdgeFact(edge_type, "c", "a")),
    )
    violations = validate(batch, Snapshot(), layer=INSTITUTIONAL, rules=[RM_04])
    assert [(v.rule, v.fact) for v in violations] == [(RM_04, "a -> b -> c")]


def test_a_cycle_closed_by_an_existing_edge_is_rejected():
    snapshot = Snapshot(
        nodes={"a": SnapshotNode(CONCEPT, INSTITUTIONAL), "b": SnapshotNode(CONCEPT, INSTITUTIONAL)},
        edges=(EdgeFact(HAS_PREREQUISITE, "a", "b"),),
    )
    batch = Batch(edges=(EdgeFact(HAS_PREREQUISITE, "b", "a"),))
    assert rules_of(validate(batch, snapshot, layer=INSTITUTIONAL, rules=[RM_04])) == [RM_04]


def test_a_self_loop_is_a_cycle():
    batch = Batch(nodes=concepts("a"), edges=(EdgeFact(SPECIALIZES, "a", "a"),))
    assert rules_of(validate(batch, Snapshot(), layer=INSTITUTIONAL, rules=[RM_04])) == [RM_04]


def test_a_diamond_is_not_a_cycle():
    batch = Batch(
        nodes=concepts("a", "b", "c", "d"),
        edges=tuple(EdgeFact(HAS_PREREQUISITE, s, t) for s, t in [("a", "b"), ("a", "c"), ("b", "d"), ("c", "d")]),
    )
    assert validate(batch, Snapshot(), layer=INSTITUTIONAL, rules=[RM_04]) == []


def test_cycles_of_different_types_do_not_mix():
    batch = Batch(
        nodes=concepts("a", "b"),
        edges=(EdgeFact(HAS_PREREQUISITE, "a", "b"), EdgeFact(SPECIALIZES, "b", "a")),
    )
    assert validate(batch, Snapshot(), layer=INSTITUTIONAL, rules=[RM_04]) == []


# The function itself


def test_every_violation_of_the_batch_is_reported():
    batch = Batch(
        nodes=(NodeFact("c", CONCEPT), NodeFact("doc", LEARNING_RESOURCE, {RESOURCE_LOCATOR: "nope"})),
        edges=(EdgeFact(PART_OF, "c", "nowhere"),),
    )
    assert sorted(rules_of(ingest(batch))) == [RI_05, RI_08, RI_10]


def test_unknown_rules_and_layers_are_refused():
    with pytest.raises(ValueError):
        validate(Batch(), Snapshot(), layer=REFERENCE, rules=["RI-01"])
    with pytest.raises(ValueError):
        validate(Batch(), Snapshot(), layer="other", rules=LOAD_RULES)


def test_a_batch_cannot_repeat_a_key():
    with pytest.raises(ValueError):
        Batch(nodes=(NodeFact("a", CONCEPT), NodeFact("a", TOPIC)))
