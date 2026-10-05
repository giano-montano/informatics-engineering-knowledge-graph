"""Integrity rules: their codes, their statements and the logic the validator
and the auditor share.

RI codes come from the annex on the transition to the property graph (Table 3)
and RM codes from the architecture chapter of the thesis (Table 19).
"""

from types import MappingProxyType

from iekg.graph_schema import (
    CONCEPT,
    HAS_PREREQUISITE,
    KNOWLEDGE_AREA,
    KNOWLEDGE_UNIT,
    SPECIALIZES,
    TOPIC,
)

RI_01 = "RI-01"
RI_02 = "RI-02"
RI_03 = "RI-03"
RI_04 = "RI-04"
RI_05 = "RI-05"
RI_06 = "RI-06"
RI_07 = "RI-07"
RI_08 = "RI-08"
RI_09 = "RI-09"
RI_10 = "RI-10"
RM_01 = "RM-01"
RM_02 = "RM-02"
RM_03 = "RM-03"
RM_04 = "RM-04"
RM_05 = "RM-05"

STATEMENTS = MappingProxyType({
    RI_01: "Every node has a non-null key, and no two nodes share a key",
    RI_02: "Every node carries its class label, and the four knowledge levels also carry KnowledgeElement",
    RI_03: "Every node has exactly one top-level class, and every KnowledgeElement exactly one level",
    RI_04: "Every edge has one of the eight declared types",
    RI_05: "Every edge joins a label pair admitted for its type, in the asserted direction",
    RI_06: "Between two nodes there is at most one edge of each type in each direction",
    RI_07: "No knowledge unit is part of more than one knowledge area",
    RI_08: "Every concept is part of a topic, every topic of a unit, every unit of an area",
    RI_09: "Nodes and edges carry only declared properties",
    RI_10: "A learning resource locator is an absolute URI with scheme http or https",
    RM_01: "Every node has a layer mark, reference or institutional",
    RM_02: "No edge goes from a reference node to an institutional node",
    RM_03: "Institutional topics, concepts and courses derive from a resource; ingested edges carry provenance",
    RM_04: "There are no prerequisite or specialization cycles",
    RM_05: "Every learning resource has a locator",
})

ALL_RULES = tuple(STATEMENTS)

# Anchoring (RI-08). The T-Box's existential restrictions give each class below
# KnowledgeArea exactly one parent class, the target of its partonomy pair.
REQUIRED_PARENT = MappingProxyType({
    CONCEPT: TOPIC,
    TOPIC: KNOWLEDGE_UNIT,
    KNOWLEDGE_UNIT: KNOWLEDGE_AREA,
})

# Edge types that must not form cycles (RM-04). Partonomy needs no such rule:
# its pairs only climb towards the area (annex, notes to Table 3).
ACYCLIC_EDGE_TYPES = (HAS_PREREQUISITE, SPECIALIZES)
