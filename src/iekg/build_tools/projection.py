"""Projection of the ontology TTL files into the reference-layer batch.

Implements Table 1 of the annex on the transition to the property graph. A
construct of either TTL without a row in that table is not projected in
silence: the load rejects it.

The T-Box is not projected: its declarations and axioms have no representation
of their own in the graph and live on as the graph schema and the integrity
rules. The load only checks that the T-Box uses no construct the table does not
cover. Whether the graph schema matches the T-Box's content is a separate test
(ADR-008).
"""

from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType

from rdflib import OWL, RDF, RDFS, BNode, Graph, Literal, Namespace, URIRef
from rdflib.namespace import DCTERMS, SKOS
from rdflib.term import Node

from iekg.core.batch import Batch, EdgeFact, NodeFact
from iekg.graph_schema import (
    CONCEPT,
    COURSE,
    DESCRIPTION,
    HAS_PREREQUISITE,
    HAS_RESOURCE_TYPE,
    IS_ABOUT,
    KNOWLEDGE_AREA,
    KNOWLEDGE_ELEMENT_SUBCLASSES,
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

IE = Namespace("http://www.informatics-engineering-kms.org/ontology/informatic-engineering#")

# "Clase": each named class becomes the label with its name. KnowledgeElement
# is abstract (disjoint union of its four subclasses); asserted next to one of
# them it adds nothing, because the write gives that label anyway ("Subsunción").
CLASS_LABELS = MappingProxyType({
    IE.KnowledgeArea: KNOWLEDGE_AREA,
    IE.KnowledgeUnit: KNOWLEDGE_UNIT,
    IE.Topic: TOPIC,
    IE.Concept: CONCEPT,
    IE.Course: COURSE,
    IE.LearningResource: LEARNING_RESOURCE,
    IE.ResourceType: RESOURCE_TYPE,
})

# "Propiedad de objeto afirmada" and "Subpropiedad de partonomía": the asserted
# properties, in the direction Table 2 fixes. The four partonomy properties
# collapse into one edge type. Inverse properties are not here: an assertion
# made with one is rejected rather than turned around.
EDGE_TYPES_BY_PROPERTY = MappingProxyType({
    IE.isPartOf: PART_OF,
    IE.conceptInTopic: PART_OF,
    IE.topicInKnowledgeUnit: PART_OF,
    IE.knowledgeUnitInKnowledgeArea: PART_OF,
    IE.hasPrerequisite: HAS_PREREQUISITE,
    IE.specializes: SPECIALIZES,
    IE.teachesConcept: TEACHES_CONCEPT,
    IE.requiresConcept: REQUIRES_CONCEPT,
    IE.isAbout: IS_ABOUT,
    IE.hasResourceType: HAS_RESOURCE_TYPE,
    IE.wasDerivedFrom: WAS_DERIVED_FROM,
})

# "Etiqueta de idioma": one property per language.
PREF_LABELS_BY_LANGUAGE = MappingProxyType({"es": PREF_LABEL_ES, "en": PREF_LABEL_EN})

# "Propiedad de datos" and "Anotaciones de otros vocabularios". The literal's
# datatype is not kept.
DATA_PROPERTIES = MappingProxyType({
    IE.resourceLocator: RESOURCE_LOCATOR,
    DCTERMS.description: DESCRIPTION,
})

# "Cabecera e importación": consumed, not projected.
_HEADER_PREDICATES = frozenset({OWL.imports, RDFS.comment})

# The T-Box constructs of Table 1: entity declarations, subsumption,
# existential restriction, disjoint union and disjointness, class union,
# inverse, sub-properties, transitive and functional properties, domain and
# range. Lists carry the members of unions and disjointness axioms.
_TBOX_TYPES = frozenset({
    OWL.Class,
    OWL.ObjectProperty,
    OWL.DatatypeProperty,
    OWL.AnnotationProperty,
    OWL.TransitiveProperty,
    OWL.FunctionalProperty,
    OWL.Restriction,
    OWL.AllDisjointClasses,
})
_TBOX_PREDICATES = frozenset({
    RDFS.subClassOf,
    RDFS.subPropertyOf,
    RDFS.domain,
    RDFS.range,
    OWL.inverseOf,
    OWL.disjointUnionOf,
    OWL.unionOf,
    OWL.members,
    OWL.onProperty,
    OWL.someValuesFrom,
    RDF.first,
    RDF.rest,
})


@dataclass(frozen=True)
class Problem:
    construct: str
    message: str


class ProjectionError(Exception):
    def __init__(self, source: str, problems: list[Problem]) -> None:
        super().__init__(f"{source}: {len(problems)} construct(s) rejected")
        self.source = source
        self.problems = problems


def read_turtle(path: Path) -> Graph:
    graph = Graph()
    graph.parse(path, format="turtle")
    return graph


def check_tbox(graph: Graph, source: str = "T-Box") -> None:
    """Reject any T-Box construct without a row in Table 1."""
    ontologies = set(graph.subjects(RDF.type, OWL.Ontology))
    problems = []
    for s, p, o in _sorted(graph):
        if s in ontologies and ((p, o) == (RDF.type, OWL.Ontology) or p in _HEADER_PREDICATES):
            continue
        if p == RDF.type:
            if o not in _TBOX_TYPES:
                problems.append(_problem(graph, (s, p, o), f"{_n3(graph, o)} is not a T-Box construct of Table 1"))
        elif p not in _TBOX_PREDICATES:
            problems.append(_problem(graph, (s, p, o), f"{_n3(graph, p)} is not a T-Box construct of Table 1"))
    if problems:
        raise ProjectionError(source, problems)


def project_backbone(graph: Graph, source: str = "backbone") -> Batch:
    """Project the backbone's individuals into the reference-layer batch."""
    ontologies = set(graph.subjects(RDF.type, OWL.Ontology))
    all_different = set(graph.subjects(RDF.type, OWL.AllDifferent))
    member_lists = _list_cells(graph, (o for s in all_different for o in graph.objects(s, OWL.distinctMembers)))
    individuals = {
        s for s, o in graph.subject_objects(RDF.type)
        if o == OWL.NamedIndividual or o in CLASS_LABELS or o == IE.KnowledgeElement
    }

    problems: list[Problem] = []
    classes: dict[Node, set[str]] = defaultdict(set)
    abstract: set[Node] = set()
    properties: dict[Node, dict[str, str]] = defaultdict(dict)
    # A set: the four partonomy properties collapse into one edge type, so the
    # same pair asserted with isPartOf and with a sub-property is one edge.
    edges: set[EdgeFact] = set()

    def reject(triple: tuple[Node, Node, Node], message: str) -> None:
        problems.append(_problem(graph, triple, message))

    def set_property(triple: tuple[Node, Node, Node], name: str, value: str) -> None:
        if name in properties[triple[0]]:
            reject(triple, f"second value for {name}")
        else:
            properties[triple[0]][name] = value

    for triple in _sorted(graph):
        s, p, o = triple
        if s in ontologies:
            # "Cabecera e importación".
            if not ((p, o) == (RDF.type, OWL.Ontology) or p in _HEADER_PREDICATES):
                reject(triple, "not part of an ontology header")
        elif s in all_different or s in member_lists:
            # "Individuos distintos": not projected; the unique key makes it redundant.
            if not ((p, o) == (RDF.type, OWL.AllDifferent) or p in (OWL.distinctMembers, RDF.first, RDF.rest)):
                reject(triple, "not part of an owl:AllDifferent axiom")
        elif s not in individuals:
            reject(triple, "no construct of Table 1 covers this triple")
        elif not isinstance(s, URIRef):
            reject(triple, "an individual needs an IRI to become a key")
        elif p == RDF.type:
            if o == OWL.NamedIndividual:
                continue
            if o == IE.KnowledgeElement:
                abstract.add(s)
            elif o in CLASS_LABELS:
                classes[s].add(CLASS_LABELS[o])
            else:
                reject(triple, f"{_n3(graph, o)} is not a class of the ontology")
        elif p == SKOS.prefLabel:
            if isinstance(o, Literal) and o.language in PREF_LABELS_BY_LANGUAGE:
                set_property(triple, PREF_LABELS_BY_LANGUAGE[o.language], str(o))
            else:
                reject(triple, f"a preferred label needs a language tag among {sorted(PREF_LABELS_BY_LANGUAGE)}")
        elif p in DATA_PROPERTIES:
            if isinstance(o, Literal):
                set_property(triple, DATA_PROPERTIES[p], str(o))
            else:
                reject(triple, f"{_n3(graph, p)} takes a literal")
        elif p == IE.layer:
            # The write path fixes the layer (RM-01): the load writes the
            # reference layer, so the TTL must agree with it.
            if str(o) != REFERENCE:
                reject(triple, f"the backbone only holds the {REFERENCE!r} layer")
        elif p in EDGE_TYPES_BY_PROPERTY:
            if isinstance(o, URIRef):
                edges.add(EdgeFact(EDGE_TYPES_BY_PROPERTY[p], str(s), str(o)))
            else:
                reject(triple, f"{_n3(graph, p)} takes an individual")
        else:
            reject(triple, f"{_n3(graph, p)} has no row in Table 1 for individuals")

    nodes = []
    for individual in sorted(i for i in individuals if isinstance(i, URIRef)):
        found = sorted(classes[individual])
        if len(found) != 1:
            # None is what HermiT cannot see under the open world (RI-03); two
            # cannot become a single node.
            if found:
                message = f"has several classes: {', '.join(found)}"
            elif individual in abstract:
                message = "is only a KnowledgeElement, which is abstract"
            else:
                message = "has no class"
            problems.append(Problem(_n3(graph, individual), message))
            continue
        if individual in abstract and found[0] not in KNOWLEDGE_ELEMENT_SUBCLASSES:
            problems.append(Problem(_n3(graph, individual), f"a {found[0]} is not a KnowledgeElement"))
            continue
        nodes.append(NodeFact(str(individual), found[0], properties[individual]))

    if problems:
        raise ProjectionError(source, problems)
    return Batch(nodes=tuple(nodes), edges=tuple(sorted(edges, key=lambda e: (e.type, e.source, e.target))))


def _list_cells(graph: Graph, heads: Iterable[Node]) -> set[Node]:
    cells: set[Node] = set()
    for head in heads:
        cell = head
        while isinstance(cell, BNode) and cell not in cells:
            cells.add(cell)
            cell = graph.value(cell, RDF.rest)
    return cells


def _sorted(graph: Graph) -> list[tuple[Node, Node, Node]]:
    # Deterministic order, so a rejected load lists its problems the same way.
    return sorted(graph, key=lambda triple: tuple(term.n3() for term in triple))


def _n3(graph: Graph, term: Node) -> str:
    return term.n3(graph.namespace_manager)


def _problem(graph: Graph, triple: tuple[Node, Node, Node], message: str) -> Problem:
    return Problem(" ".join(_n3(graph, term) for term in triple), message)
