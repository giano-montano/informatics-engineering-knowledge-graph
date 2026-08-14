"""Drift guard between the ontology and the LPG mapping.

The T-box artifact is generated from two files that are edited independently:
ontology/ontologia_informatica.ttl and schema/schema_rules.yaml. Nothing stops
them from drifting apart, and a mapping that silently stops covering a class
would make the emitted diagram lie. These tests fail when they diverge.

No database is touched: the T-box is not materialised in Neo4j.
"""

from __future__ import annotations

import pytest

from iekg import rules, tbox


@pytest.fixture(scope="module")
def spec():
    return rules.load()


@pytest.fixture(scope="module")
def box(spec):
    return tbox.read_tbox(None, spec)


def test_every_owl_class_is_projected(box, spec):
    missing = sorted(c for c in box.classes if not tbox.is_projected(c, spec))
    assert not missing, f"classes absent from the LPG mapping: {missing}"


def test_every_mapped_class_exists_in_the_ontology(box, spec):
    invented = sorted(set(spec.classes) - set(box.classes))
    assert not invented, f"mapped classes with no OWL class: {invented}"


def test_every_mapped_object_property_exists_in_the_ontology(box, spec):
    mapped = set(spec.object_properties) | set(spec.inverses)
    invented = sorted(mapped - set(box.object_properties))
    assert not invented, f"mapped properties with no OWL property: {invented}"


def test_declared_inverses_match_the_ontology(box, spec):
    """An inverse is not materialised, so its declaration is the only record
    of which OWL property it stands for. It must be a real owl:inverseOf."""
    for name in spec.inverses:
        axioms = box.object_properties[name]
        partner = axioms.inverse_of or next(
            (other for other, o in box.object_properties.items()
             if o.inverse_of == name), None
        )
        assert partner, f"{name} is declared as an inverse but OWL asserts no owl:inverseOf"


def test_transitive_relationships_come_from_transitive_properties(box, spec):
    """Every relationship type declared transitive in the spec must have at
    least one OWL property behind it carrying owl:TransitiveProperty."""
    for rel_type in spec.transitive:
        sources = [
            name for name, axioms in box.object_properties.items()
            if "transitive" in axioms.characteristics
            and tbox.projection_of(name, spec)[0] == rel_type
        ]
        assert sources, f"{rel_type} is declared transitive with no transitive OWL property"


def test_functional_property_has_its_cardinality_rule(box, spec):
    """owl:FunctionalProperty has no native counterpart in Neo4j, so it only
    survives as a functional_relationship rule. Losing the rule would lose
    the axiom silently."""
    functional = {
        name for name, axioms in box.object_properties.items()
        if "functional" in axioms.characteristics
    }
    covered = {
        (r["relationship"], r["from"], r["to"])
        for r in spec.rules_of_type("functional_relationship")
    }
    for name in functional:
        rel_type, _ = tbox.projection_of(name, spec)
        axioms = box.object_properties[name]
        expected = (rel_type, axioms.domain[0], axioms.range[0])
        assert expected in covered, f"{name} is functional with no rule covering {expected}"


def test_the_emitted_artifact_mentions_every_class(box, spec):
    text = tbox.emit(box, spec)
    for name in box.classes:
        assert name in text, f"{name} missing from the emitted diagram"
