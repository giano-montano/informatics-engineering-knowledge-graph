"""Negative test for the integrity queries.

A query finding nothing in clean data proves nothing. Here every kind of
violation is injected on purpose and the matching query is required to find it.

Each test runs inside a transaction that is rolled back, so the violation
never persists and the backbone stays intact. That is why explicit
transactions are used instead of create-then-delete.
"""

from __future__ import annotations

import pytest
from neo4j.exceptions import Neo4jError

from iekg import integrity, rules
from iekg.db import DATABASE, driver


@pytest.fixture(scope="module")
def spec():
    return rules.load()


@pytest.fixture(scope="module")
def queries(spec):
    return {rid: c.rstrip().rstrip(";") for rid, c in integrity.compile_queries(spec)}


@pytest.fixture
def tx():
    d = driver()
    with d.session(database=DATABASE) as s:
        t = s.begin_transaction()
        try:
            yield t
        finally:
            t.rollback()      # the injected violation never persists
    d.close()


def entities(tx, queries, rule_id) -> set[str]:
    return {row["entity"] for row in tx.run(queries[rule_id])}


# ---------------------------------------------------------------------------
# Positive control: with nothing injected, no rule may fire
# ---------------------------------------------------------------------------

def test_clean_backbone_violates_no_rule(tx, queries):
    fired = {rid for rid in queries if list(tx.run(queries[rid]))}
    assert fired == set()


# ---------------------------------------------------------------------------
# disjoint_labels
# ---------------------------------------------------------------------------

def test_detects_two_disjoint_labels(tx, queries):
    tx.run("CREATE (:KnowledgeElement:Topic:Concept {iri:'urn:test:double'})")
    assert "urn:test:double" in entities(tx, queries, "ke-disjoint-subtypes")


def test_detects_knowledge_element_without_subtype(tx, queries):
    tx.run("CREATE (:KnowledgeElement {iri:'urn:test:orphan'})")
    assert "urn:test:orphan" in entities(tx, queries, "ke-disjoint-subtypes")


def test_detects_overlapping_root_types(tx, queries):
    tx.run("CREATE (:KnowledgeElement:Topic:LearningResource {iri:'urn:test:root'})")
    assert "urn:test:root" in entities(tx, queries, "disjoint-root-types")


# ---------------------------------------------------------------------------
# functional_relationship
# ---------------------------------------------------------------------------

def test_detects_unit_with_two_areas(tx, queries):
    tx.run(
        "CREATE (ku:KnowledgeElement:KnowledgeUnit {iri:'urn:test:ku2'}) "
        "CREATE (a:KnowledgeElement:KnowledgeArea {iri:'urn:test:ka1'}) "
        "CREATE (b:KnowledgeElement:KnowledgeArea {iri:'urn:test:ka2'}) "
        "CREATE (ku)-[:PART_OF]->(a) CREATE (ku)-[:PART_OF]->(b)"
    )
    assert "urn:test:ku2" in entities(tx, queries, "ku-in-single-ka")


def test_detects_unit_without_area(tx, queries):
    tx.run("CREATE (:KnowledgeElement:KnowledgeUnit {iri:'urn:test:ku0'})")
    assert "urn:test:ku0" in entities(tx, queries, "ku-in-single-ka")


# ---------------------------------------------------------------------------
# domain_range
# ---------------------------------------------------------------------------

def test_detects_part_of_between_disallowed_pair(tx, queries):
    tx.run(
        "CREATE (c:KnowledgeElement:Concept {iri:'urn:test:c'}) "
        "CREATE (k:KnowledgeElement:KnowledgeArea {iri:'urn:test:ka3'}) "
        "CREATE (c)-[:PART_OF]->(k)"          # Concept -> KnowledgeArea skips a level
    )
    assert "urn:test:c -> urn:test:ka3" in entities(tx, queries, "part-of-pairs")


def test_detects_derivation_outside_range(tx, queries):
    tx.run(
        "CREATE (a:KnowledgeElement:KnowledgeUnit {iri:'urn:test:ku3'}) "
        "CREATE (b:KnowledgeElement:Concept {iri:'urn:test:c2'}) "
        "CREATE (a)-[:WAS_DERIVED_FROM]->(b)"  # target is not a :LearningResource
    )
    assert "urn:test:ku3 -> urn:test:c2" in entities(
        tx, queries, "derived-from-resource"
    )


def test_detects_prerequisite_between_non_concepts(tx, queries):
    tx.run(
        "CREATE (a:KnowledgeElement:KnowledgeUnit {iri:'urn:test:ku4'}) "
        "CREATE (b:KnowledgeElement:KnowledgeUnit {iri:'urn:test:ku5'}) "
        "CREATE (a)-[:HAS_PREREQUISITE]->(b)"
    )
    assert "urn:test:ku4 -> urn:test:ku5" in entities(
        tx, queries, "prerequisite-between-concepts"
    )


# ---------------------------------------------------------------------------
# acyclicity
# ---------------------------------------------------------------------------

def test_detects_part_of_cycle(tx, queries):
    tx.run(
        "CREATE (a:KnowledgeElement:KnowledgeUnit {iri:'urn:test:cycle-a'}) "
        "CREATE (b:KnowledgeElement:KnowledgeArea {iri:'urn:test:cycle-b'}) "
        "CREATE (a)-[:PART_OF]->(b) CREATE (b)-[:PART_OF]->(a)"
    )
    assert {"urn:test:cycle-a", "urn:test:cycle-b"} & entities(
        tx, queries, "part-of-dag"
    )


def test_detects_prerequisite_cycle(tx, queries):
    tx.run(
        "CREATE (a:KnowledgeElement:Concept {iri:'urn:test:p1'}) "
        "CREATE (b:KnowledgeElement:Concept {iri:'urn:test:p2'}) "
        "CREATE (c:KnowledgeElement:Concept {iri:'urn:test:p3'}) "
        "CREATE (a)-[:HAS_PREREQUISITE]->(b) "
        "CREATE (b)-[:HAS_PREREQUISITE]->(c) "
        "CREATE (c)-[:HAS_PREREQUISITE]->(a)"
    )
    assert entities(tx, queries, "prerequisites-dag")


# ---------------------------------------------------------------------------
# unique_key: the only rule with a native constraint, so the violation never
# gets written. What is tested is that the database rejects it.
# ---------------------------------------------------------------------------

def test_native_constraint_rejects_duplicate_iri(tx):
    existing = tx.run(
        "MATCH (n:KnowledgeElement) RETURN n.iri AS iri LIMIT 1"
    ).single()["iri"]

    with pytest.raises(Neo4jError):
        tx.run(
            "CREATE (:KnowledgeElement:KnowledgeUnit {iri:$iri})", iri=existing
        ).consume()


# ---------------------------------------------------------------------------
# The backbone must be untouched after every rollback
# ---------------------------------------------------------------------------

def test_backbone_is_still_intact():
    d = driver()
    try:
        with d.session(database=DATABASE) as s:
            counts = {
                row["label"]: row["n"]
                for row in s.run(
                    "MATCH (n) UNWIND labels(n) AS label "
                    "RETURN label, count(*) AS n"
                )
            }
    finally:
        d.close()

    assert counts.get("KnowledgeArea") == 17
    assert counts.get("KnowledgeUnit") == 162
    assert counts.get("LearningResource") == 1
    assert "Topic" not in counts and "Concept" not in counts
