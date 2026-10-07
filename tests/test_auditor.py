"""Negative tests of the audit: inject each violation, require that its query
finds it. A query that finds nothing on clean data proves nothing.

Everything runs inside a transaction that is rolled back.
"""

import pytest

from iekg.core.auditor import audit, audit_rule
from iekg.core.batch import Batch, EdgeFact, NodeFact, Snapshot, SnapshotNode
from iekg.core.repository import write_batch_in
from iekg.core.rules import ALL_RULES
from iekg.graph_schema import (
    CONCEPT,
    COURSE,
    COURSE_CODE,
    HAS_PREREQUISITE,
    HAS_RESOURCE_TYPE,
    INSTITUTIONAL,
    IS_ABOUT,
    KNOWLEDGE_AREA,
    KNOWLEDGE_UNIT,
    LEARNING_RESOURCE,
    PART_OF,
    PREF_LABEL_EN,
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

pytestmark = pytest.mark.neo4j

# Each case writes a violation of one rule; $a, $b and $c are fresh keys.
INJECTIONS = {
    "RI-01 node without key": ("RI-01", "CREATE (:Course {layer: 'institutional'})"),
    "RI-01 shared key": (
        "RI-01",
        "CREATE (:Course {key: $a, layer: 'institutional'}), (:ResourceType {key: $a, layer: 'institutional'})",
    ),
    "RI-02 undeclared label": ("RI-02", "CREATE (:Course:Syllabus {key: $a, layer: 'institutional'})"),
    "RI-02 level without KnowledgeElement": ("RI-02", "CREATE (:Topic {key: $a, layer: 'institutional'})"),
    "RI-02 no label": ("RI-02", "CREATE ({key: $a, layer: 'institutional'})"),
    "RI-03 two top-level classes": ("RI-03", "CREATE (:Course:ResourceType {key: $a, layer: 'institutional'})"),
    "RI-03 two levels": (
        "RI-03",
        "CREATE (:KnowledgeElement:Topic:Concept {key: $a, layer: 'institutional'})",
    ),
    "RI-03 abstract only": ("RI-03", "CREATE (:KnowledgeElement {key: $a, layer: 'institutional'})"),
    "RI-04 undeclared edge type": (
        "RI-04",
        "CREATE (:Course {key: $a, layer: 'institutional'})-[:RELATED_TO {provenance: $c}]->"
        "(:Course {key: $b, layer: 'institutional'})",
    ),
    "RI-05 pair not admitted": (
        "RI-05",
        "CREATE (:Course {key: $a, layer: 'institutional'})-[:PART_OF {provenance: $c}]->"
        "(:Course {key: $b, layer: 'institutional'})",
    ),
    "RI-05 wrong direction": (
        "RI-05",
        "CREATE (:KnowledgeArea:KnowledgeElement {key: $a, layer: 'reference'})-[:PART_OF]->"
        "(:KnowledgeUnit:KnowledgeElement {key: $b, layer: 'reference'})",
    ),
    "RI-06 parallel edges": (
        "RI-06",
        "CREATE (a:Course {key: $a, layer: 'institutional'}),"
        " (b:Concept:KnowledgeElement {key: $b, layer: 'institutional'}),"
        " (a)-[:TEACHES_CONCEPT {provenance: $c}]->(b), (a)-[:TEACHES_CONCEPT {provenance: $c}]->(b)",
    ),
    "RI-07 unit in two areas": (
        "RI-07",
        "CREATE (u:KnowledgeUnit:KnowledgeElement {key: $a, layer: 'reference'}),"
        " (u)-[:PART_OF]->(:KnowledgeArea:KnowledgeElement {key: $b, layer: 'reference'}),"
        " (u)-[:PART_OF]->(:KnowledgeArea:KnowledgeElement {key: $c, layer: 'reference'})",
    ),
    "RI-08 orphan concept": ("RI-08", "CREATE (:Concept:KnowledgeElement {key: $a, layer: 'institutional'})"),
    "RI-08 orphan topic": ("RI-08", "CREATE (:Topic:KnowledgeElement {key: $a, layer: 'institutional'})"),
    "RI-08 orphan unit": ("RI-08", "CREATE (:KnowledgeUnit:KnowledgeElement {key: $a, layer: 'reference'})"),
    "RI-09 undeclared node property": (
        "RI-09",
        "CREATE (:Course {key: $a, layer: 'institutional', credits: 4})",
    ),
    "RI-09 property of another class": (
        "RI-09",
        "CREATE (:Course {key: $a, layer: 'institutional', resourceLocator: 'https://example.org'})",
    ),
    "RI-09 undeclared edge property": (
        "RI-09",
        "CREATE (:Course {key: $a, layer: 'institutional'})-[:TEACHES_CONCEPT {provenance: $c, weight: 1}]->"
        "(:Concept:KnowledgeElement {key: $b, layer: 'institutional'})",
    ),
    "RI-09 provenance on an edge from a reference node": (
        "RI-09",
        "CREATE (:KnowledgeUnit:KnowledgeElement {key: $a, layer: 'reference'})-[:PART_OF {provenance: $c}]->"
        "(:KnowledgeArea:KnowledgeElement {key: $b, layer: 'reference'})",
    ),
    "RI-10 other scheme": (
        "RI-10",
        "CREATE (:LearningResource {key: $a, layer: 'institutional', resourceLocator: 'ftp://example.org/a'})",
    ),
    "RI-10 not a URI": (
        "RI-10",
        "CREATE (:LearningResource {key: $a, layer: 'institutional', resourceLocator: 'syllabus.pdf'})",
    ),
    "RI-10 not a string": (
        "RI-10",
        "CREATE (:LearningResource {key: $a, layer: 'institutional', resourceLocator: 42})",
    ),
    "RM-01 no layer": ("RM-01", "CREATE (:Course {key: $a})"),
    "RM-01 unknown layer": ("RM-01", "CREATE (:Course {key: $a, layer: 'draft'})"),
    "RM-02 reference into institutional": (
        "RM-02",
        "CREATE (:Course {key: $a, layer: 'reference'})-[:TEACHES_CONCEPT]->"
        "(:Concept:KnowledgeElement {key: $b, layer: 'institutional'})",
    ),
    "RM-03 node without derivation": (
        "RM-03",
        "CREATE (:Course {key: $a, layer: 'institutional'})",
    ),
    "RM-03 edge without provenance": (
        "RM-03",
        "CREATE (:LearningResource {key: $a, layer: 'institutional', resourceLocator: 'https://example.org'})"
        "-[:HAS_RESOURCE_TYPE]->(:ResourceType {key: $b, layer: 'institutional'})",
    ),
    "RM-04 prerequisite cycle": (
        "RM-04",
        "CREATE (a:Concept:KnowledgeElement {key: $a, layer: 'institutional'}),"
        " (b:Concept:KnowledgeElement {key: $b, layer: 'institutional'}),"
        " (a)-[:HAS_PREREQUISITE {provenance: $c}]->(b), (b)-[:HAS_PREREQUISITE {provenance: $c}]->(a)",
    ),
    "RM-04 specialization self-loop": (
        "RM-04",
        "CREATE (a:Concept:KnowledgeElement {key: $a, layer: 'institutional'}),"
        " (a)-[:SPECIALIZES {provenance: $c}]->(a)",
    ),
    "RM-05 resource without locator": ("RM-05", "CREATE (:LearningResource {key: $a, layer: 'reference'})"),
}


def test_every_rule_has_a_negative_test():
    assert {rule for rule, _ in INJECTIONS.values()} == set(ALL_RULES)


@pytest.mark.parametrize("case", INJECTIONS)
def test_the_audit_detects_an_injected_violation(tx, new_key, case):
    rule, injection = INJECTIONS[case]
    before = audit_rule(tx, rule).violations
    tx.run(injection, a=new_key(), b=new_key(), c=new_key()).consume()
    assert audit_rule(tx, rule).violations > before


def test_what_the_repository_writes_raises_no_violation(tx, new_key):
    """No false positives: a well-formed piece of each layer passes every rule."""
    before = {result.rule: result.violations for result in audit(tx).results}
    area, unit, standard = new_key(), new_key(), new_key()
    doc, kind, course, topic, concept, other = (new_key() for _ in range(6))

    reference = Batch(
        nodes=(
            NodeFact(area, KNOWLEDGE_AREA, {PREF_LABEL_EN: "Area", PREF_LABEL_ES: "Área"}),
            NodeFact(unit, KNOWLEDGE_UNIT),
            NodeFact(standard, LEARNING_RESOURCE, {RESOURCE_LOCATOR: "https://example.org/standard"}),
        ),
        edges=(
            EdgeFact(PART_OF, unit, area),
            EdgeFact(WAS_DERIVED_FROM, unit, standard),
            EdgeFact(WAS_DERIVED_FROM, area, standard),
        ),
    )
    write_batch_in(tx, reference, Snapshot(), layer=REFERENCE)

    institutional = Batch(
        nodes=(
            NodeFact(doc, LEARNING_RESOURCE, {RESOURCE_LOCATOR: "http://localhost:8000/recursos/x"}),
            NodeFact(kind, RESOURCE_TYPE, {PREF_LABEL_ES: "Sílabo"}),
            NodeFact(course, COURSE, {COURSE_CODE: "1INF27"}),
            NodeFact(topic, TOPIC),
            NodeFact(concept, CONCEPT),
            NodeFact(other, CONCEPT),
        ),
        edges=(
            EdgeFact(HAS_RESOURCE_TYPE, doc, kind),
            EdgeFact(PART_OF, topic, unit),
            EdgeFact(PART_OF, concept, topic),
            EdgeFact(PART_OF, other, topic),
            EdgeFact(HAS_PREREQUISITE, concept, other),
            EdgeFact(SPECIALIZES, concept, other),
            EdgeFact(TEACHES_CONCEPT, course, concept),
            EdgeFact(REQUIRES_CONCEPT, course, other),
            EdgeFact(IS_ABOUT, doc, course),
            # The course brings its derivation; the write derives the others.
            EdgeFact(WAS_DERIVED_FROM, course, doc),
        ),
    )
    snapshot = Snapshot(nodes={unit: SnapshotNode(KNOWLEDGE_UNIT, REFERENCE)})
    write_batch_in(tx, institutional, snapshot, layer=INSTITUTIONAL, provenance=doc)

    after = {result.rule: result.violations for result in audit(tx).results}
    assert after == before
