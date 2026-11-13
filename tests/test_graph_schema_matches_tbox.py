"""The hand-written graph schema against the T-Box (ADR-008).

Each check derives from the TTL what one part of ``graph_schema`` declares,
reading it as Table 1 of the annex does, and compares. The mappings of the
projection are the bridge: which property becomes which edge type, and in
which direction. Every check also has to fail on a copy of the TTL altered on
purpose, or it would prove nothing.

Out of scope: transitivity, functionality (RI-07) and acyclicity are logic of
the audit queries, not data of the schema.
"""

from collections import defaultdict

import pytest
from conftest import TBOX
from rdflib import OWL, RDF, RDFS, Graph, URIRef
from rdflib.collection import Collection

from iekg.build_tools.projection import CLASS_LABELS, DATA_PROPERTIES, EDGE_TYPES_BY_PROPERTY, IE, read_turtle
from iekg.core.rules import REQUIRED_PARENT
from iekg.graph_schema import (
    ADMITTED_PAIRS,
    ALL_LABELS,
    EDGE_TYPES,
    KNOWLEDGE_ELEMENT,
    KNOWLEDGE_ELEMENT_SUBCLASSES,
    LAYER,
    NODE_PROPERTIES,
    PART_OF,
    TOP_LEVEL_LABELS,
)

LABEL_OF = {**CLASS_LABELS, IE.KnowledgeElement: KNOWLEDGE_ELEMENT}


def only(graph: Graph, subject, predicate):
    values = list(graph.objects(subject, predicate))
    assert len(values) == 1, f"{subject} has {len(values)} values for {predicate}"
    return values[0]


def label_of(term) -> str:
    assert term in LABEL_OF, f"{term} is not a class the schema knows"
    return LABEL_OF[term]


def members(graph: Graph, subject, predicate) -> list:
    return list(Collection(graph, only(graph, subject, predicate)))


def labels(graph: Graph, expression) -> frozenset[str]:
    """The node labels a class expression admits. A union expands, and so
    does an abstract class, into its disjoint union (Table 1)."""
    for predicate in (OWL.unionOf, OWL.disjointUnionOf):
        if (expression, predicate, None) in graph:
            return frozenset().union(*(labels(graph, m) for m in members(graph, expression, predicate)))
    return frozenset({label_of(expression)})


# --- Checks ---------------------------------------------------------------------


def check_classes(graph: Graph) -> None:
    named = {c for c in graph.subjects(RDF.type, OWL.Class) if isinstance(c, URIRef)}
    assert named == set(LABEL_OF)
    assert {LABEL_OF[c] for c in named} == set(ALL_LABELS)
    # "Clase": each label is named after its class.
    assert all(str(c).rsplit("#", 1)[1] == LABEL_OF[c] for c in named)


def check_hierarchy(graph: Graph) -> None:
    subclasses = {label_of(m) for m in members(graph, IE.KnowledgeElement, OWL.disjointUnionOf)}
    assert subclasses == set(KNOWLEDGE_ELEMENT_SUBCLASSES)
    asserted = {label_of(c) for c in graph.subjects(RDFS.subClassOf, IE.KnowledgeElement)}
    assert asserted == set(KNOWLEDGE_ELEMENT_SUBCLASSES)
    groups = {
        frozenset(label_of(m) for m in members(graph, axiom, OWL.members))
        for axiom in graph.subjects(RDF.type, OWL.AllDisjointClasses)
    }
    assert groups == {frozenset(KNOWLEDGE_ELEMENT_SUBCLASSES), frozenset(TOP_LEVEL_LABELS)}


def check_object_properties(graph: Graph) -> None:
    """Every object property is asserted, or the inverse of one that is; never both."""
    declared = set(graph.subjects(RDF.type, OWL.ObjectProperty))
    asserted = set(EDGE_TYPES_BY_PROPERTY)
    assert asserted <= declared, f"not object properties of the T-Box: {asserted - declared}"
    partners = defaultdict(set)
    for a, b in graph.subject_objects(OWL.inverseOf):
        partners[a].add(b)
        partners[b].add(a)
    for prop in declared:
        if prop in asserted:
            assert not partners[prop] & asserted, f"{prop} and its inverse are both asserted"
        else:
            assert partners[prop] & asserted, f"{prop} is neither asserted nor the inverse of an asserted property"


def derived_pairs(graph: Graph) -> dict[str, frozenset[tuple[str, str]]]:
    pairs = defaultdict(set)
    for prop, edge_type in EDGE_TYPES_BY_PROPERTY.items():
        # "Subpropiedad de partonomía": each admitted pair belongs to one
        # sub-property, so the super-property adds none of its own.
        if any(EDGE_TYPES_BY_PROPERTY.get(sub) == edge_type for sub in graph.subjects(RDFS.subPropertyOf, prop)):
            continue
        domain, range_ = labels(graph, only(graph, prop, RDFS.domain)), labels(graph, only(graph, prop, RDFS.range))
        pairs[edge_type] |= {(source, target) for source in domain for target in range_}
    return {edge_type: frozenset(found) for edge_type, found in pairs.items()}


def check_pairs(graph: Graph) -> None:
    pairs = derived_pairs(graph)
    assert set(pairs) == set(EDGE_TYPES)
    for edge_type in EDGE_TYPES:
        assert pairs[edge_type] == ADMITTED_PAIRS[edge_type], edge_type


def check_anchoring(graph: Graph) -> None:
    """The existential restrictions give the parent class of RI-08."""
    parents = {}
    for cls in graph.subjects(RDF.type, OWL.Class):
        for restriction in graph.objects(cls, RDFS.subClassOf):
            if (restriction, RDF.type, OWL.Restriction) in graph:
                assert EDGE_TYPES_BY_PROPERTY.get(only(graph, restriction, OWL.onProperty)) == PART_OF
                parents[label_of(cls)] = label_of(only(graph, restriction, OWL.someValuesFrom))
    assert parents == dict(REQUIRED_PARENT)


def check_data_properties(graph: Graph) -> None:
    declared = set(graph.subjects(RDF.type, OWL.DatatypeProperty))
    # The others (dcterms:description) come from other vocabularies, not the T-Box.
    assert declared == {p for p in DATA_PROPERTIES if str(p).startswith(str(IE))}
    for prop in declared:
        holders = {label for label, names in NODE_PROPERTIES.items() if DATA_PROPERTIES[prop] in names}
        assert holders == labels(graph, only(graph, prop, RDFS.domain)), prop
    # The layer mark, an annotation every node carries (RM-01).
    assert set(graph.subjects(RDF.type, OWL.AnnotationProperty)) == {IE.layer}
    assert str(IE.layer).rsplit("#", 1)[1] == LAYER
    assert all(LAYER in names for names in NODE_PROPERTIES.values())


CHECKS = (check_classes, check_hierarchy, check_object_properties, check_pairs, check_anchoring,
          check_data_properties)


# --- Tests -------------------------------------------------------------------------


@pytest.mark.parametrize("check", CHECKS, ids=lambda check: check.__name__)
def test_the_schema_says_what_the_tbox_says(check):
    check(read_turtle(TBOX))


def altered(tmp_path, old: str = "", new: str = "", extra: str = "") -> Graph:
    """A copy of the T-Box with ``old`` replaced once by ``new`` and ``extra`` appended."""
    text = TBOX.read_text(encoding="utf-8")
    if old:
        # Not an AssertionError: a negative test must not pass because its edit missed.
        if text.count(old) != 1:
            raise ValueError(f"{old!r} must occur once in the T-Box")
        text = text.replace(old, new)
    path = tmp_path / TBOX.name
    path.write_text(text + "\n" + extra + "\n", encoding="utf-8")
    return read_turtle(path)


@pytest.mark.parametrize("check, change", [
    (check_classes, {"extra": ":Syllabus rdf:type owl:Class ."}),
    (check_hierarchy, {"old": "owl:disjointUnionOf ( :Concept", "new": "owl:disjointUnionOf ( :Course :Concept"}),
    (check_hierarchy, {"old": "owl:members ( :Course", "new": "owl:members ( :Topic"}),
    (check_object_properties, {"extra": ":isTaughtIn rdf:type owl:ObjectProperty ."}),
    (check_object_properties, {"extra": ":specializes owl:inverseOf :hasPrerequisite ."}),
    (check_object_properties, {"old": ":wasDerivedFrom rdf:type owl:ObjectProperty",
                               "new": ":wasDerivedFrom rdf:type owl:DatatypeProperty"}),
    (check_pairs, {"old": "rdfs:range :Topic .", "new": "rdfs:range :KnowledgeUnit ."}),
    (check_pairs, {"extra": ":teachesConcept rdfs:range :Topic ."}),
    # The direction: teachesConcept declared from the concept to the course.
    (check_pairs, {"old": ":teachesConcept rdf:type owl:ObjectProperty ;\n"
                          "                rdfs:subPropertyOf owl:topObjectProperty ;\n"
                          "                rdfs:domain :Course ;\n"
                          "                rdfs:range :Concept .",
                   "new": ":teachesConcept rdf:type owl:ObjectProperty ;\n"
                          "                rdfs:subPropertyOf owl:topObjectProperty ;\n"
                          "                rdfs:domain :Concept ;\n"
                          "                rdfs:range :Course ."}),
    # A union with one class less admits fewer pairs.
    (check_pairs, {"old": ":isAbout rdf:type owl:ObjectProperty ;\n"
                          "         rdfs:subPropertyOf owl:topObjectProperty ;\n"
                          "         rdfs:domain :LearningResource ;\n"
                          "         rdfs:range [ rdf:type owl:Class ;\n"
                          "                      owl:unionOf ( :Course\n",
                   "new": ":isAbout rdf:type owl:ObjectProperty ;\n"
                          "         rdfs:subPropertyOf owl:topObjectProperty ;\n"
                          "         rdfs:domain :LearningResource ;\n"
                          "         rdfs:range [ rdf:type owl:Class ;\n"
                          "                      owl:unionOf ( \n"}),
    (check_anchoring, {"old": "owl:someValuesFrom :Topic", "new": "owl:someValuesFrom :KnowledgeUnit"}),
    (check_anchoring, {"old": "owl:onProperty :conceptInTopic", "new": "owl:onProperty :hasPrerequisite"}),
    (check_data_properties, {"extra": ":credits rdf:type owl:DatatypeProperty ; rdfs:domain :Course ."}),
    (check_data_properties, {"old": "rdfs:domain :LearningResource ;\n                 rdfs:range xsd:anyURI",
                             "new": "rdfs:domain :Course ;\n                 rdfs:range xsd:anyURI"}),
    (check_data_properties, {"extra": ":level rdf:type owl:AnnotationProperty ."}),
], ids=lambda value: value.__name__ if callable(value) else None)
def test_a_tbox_that_says_something_else_fails_the_check(tmp_path, check, change):
    with pytest.raises(AssertionError):
        check(altered(tmp_path, **change))
