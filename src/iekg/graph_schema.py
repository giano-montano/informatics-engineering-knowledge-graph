"""Graph schema: the single declaration of what the graph admits (ADR-008).

Written by hand from Tables 1 and 2 of the annex on the transition to the
property graph and from Table 17 of the thesis. Data only: the logic that is
not data (unique key, provenance, anchoring, cycles) lives in ``iekg.core``.

Read by the extractor's output schema, the validator, the write templates and
the audit queries.
"""

from types import MappingProxyType

# --- Node labels: one per class, named after it (Table 1, "Clase") ---------

KNOWLEDGE_ELEMENT = "KnowledgeElement"
KNOWLEDGE_AREA = "KnowledgeArea"
KNOWLEDGE_UNIT = "KnowledgeUnit"
TOPIC = "Topic"
CONCEPT = "Concept"
COURSE = "Course"
LEARNING_RESOURCE = "LearningResource"
RESOURCE_TYPE = "ResourceType"

# Subsumption: nodes of these classes also carry KNOWLEDGE_ELEMENT (RI-02).
KNOWLEDGE_ELEMENT_SUBCLASSES = (KNOWLEDGE_AREA, KNOWLEDGE_UNIT, TOPIC, CONCEPT)

# Disjoint union: every node carries exactly one of these (RI-03).
TOP_LEVEL_LABELS = (KNOWLEDGE_ELEMENT, COURSE, LEARNING_RESOURCE, RESOURCE_TYPE)

# Classes a node is written as. KNOWLEDGE_ELEMENT is abstract.
NODE_CLASSES = KNOWLEDGE_ELEMENT_SUBCLASSES + (COURSE, LEARNING_RESOURCE, RESOURCE_TYPE)

ALL_LABELS = (KNOWLEDGE_ELEMENT,) + NODE_CLASSES

# --- Edge types (Table 2) ---------------------------------------------------

PART_OF = "PART_OF"
HAS_PREREQUISITE = "HAS_PREREQUISITE"
SPECIALIZES = "SPECIALIZES"
TEACHES_CONCEPT = "TEACHES_CONCEPT"
REQUIRES_CONCEPT = "REQUIRES_CONCEPT"
IS_ABOUT = "IS_ABOUT"
HAS_RESOURCE_TYPE = "HAS_RESOURCE_TYPE"
WAS_DERIVED_FROM = "WAS_DERIVED_FROM"

EDGE_TYPES = (
    PART_OF,
    HAS_PREREQUISITE,
    SPECIALIZES,
    TEACHES_CONCEPT,
    REQUIRES_CONCEPT,
    IS_ABOUT,
    HAS_RESOURCE_TYPE,
    WAS_DERIVED_FROM,
)

# The union "Course or KnowledgeElement" expands into five labels (Table 1,
# "Unión de clases").
_COURSE_OR_KNOWLEDGE_ELEMENT = KNOWLEDGE_ELEMENT_SUBCLASSES + (COURSE,)

# Admitted (source, target) pairs per edge type, in the direction of the
# asserted property (Table 2, RI-05).
ADMITTED_PAIRS = MappingProxyType({
    PART_OF: frozenset({
        (CONCEPT, TOPIC),
        (TOPIC, KNOWLEDGE_UNIT),
        (KNOWLEDGE_UNIT, KNOWLEDGE_AREA),
    }),
    HAS_PREREQUISITE: frozenset({(CONCEPT, CONCEPT)}),
    SPECIALIZES: frozenset({(CONCEPT, CONCEPT)}),
    TEACHES_CONCEPT: frozenset({(COURSE, CONCEPT)}),
    REQUIRES_CONCEPT: frozenset({(COURSE, CONCEPT)}),
    IS_ABOUT: frozenset((LEARNING_RESOURCE, label) for label in _COURSE_OR_KNOWLEDGE_ELEMENT),
    HAS_RESOURCE_TYPE: frozenset({(LEARNING_RESOURCE, RESOURCE_TYPE)}),
    WAS_DERIVED_FROM: frozenset((label, LEARNING_RESOURCE) for label in _COURSE_OR_KNOWLEDGE_ELEMENT),
})

# --- Properties (Table 1 and thesis Table 17) -------------------------------

KEY = "key"
LAYER = "layer"
PREF_LABEL_ES = "prefLabelEs"
PREF_LABEL_EN = "prefLabelEn"
DESCRIPTION = "description"
RESOURCE_LOCATOR = "resourceLocator"
COURSE_CODE = "courseCode"
PROVENANCE = "provenance"

# Layer values (RM-01).
REFERENCE = "reference"
INSTITUTIONAL = "institutional"
LAYERS = (REFERENCE, INSTITUTIONAL)

_EVERY_NODE = (KEY, LAYER, PREF_LABEL_ES, PREF_LABEL_EN, DESCRIPTION)

# Properties each label admits (RI-09). A node admits the union over its labels.
NODE_PROPERTIES = MappingProxyType({
    **{label: _EVERY_NODE for label in ALL_LABELS},
    LEARNING_RESOURCE: _EVERY_NODE + (RESOURCE_LOCATOR,),
    COURSE: _EVERY_NODE + (COURSE_CODE,),
})

# Properties an edge admits, by the layer of its source node (RI-09). Only the
# edges the ingestion writes carry provenance (thesis, Table 17), and those are
# exactly the edges that leave an institutional node (annex, write condition 6).
EDGE_PROPERTIES_BY_SOURCE_LAYER = MappingProxyType({
    REFERENCE: (),
    INSTITUTIONAL: (PROVENANCE,),
})

# Full-text index of the search by name (RF-18), created by the load. The
# analyzer ignores accents and case, so "arboles" finds "Árboles".
SEARCH_INDEX = "name_search"
SEARCH_LABELS = KNOWLEDGE_ELEMENT_SUBCLASSES + (COURSE,)
SEARCH_PROPERTIES = (PREF_LABEL_ES, PREF_LABEL_EN, COURSE_CODE)
SEARCH_ANALYZER = "standard-folding"

# Locator form (RI-10): an absolute URI with scheme http or https. The same
# pattern serves Python's re.fullmatch and Cypher's =~, which both match the
# whole string.
LOCATOR_PATTERN = r"(?i)https?://[^\s/?#]+(?:[/?#]\S*)?"
