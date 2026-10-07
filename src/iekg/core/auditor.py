"""Auditor: one Cypher query per rule over the whole graph, and its report.

Runs at the close of the load, of every ingestion and of the reapplication
(ADR-005, RF-09). Each query returns one ``element`` row per violation, named
so that a person can find it in the graph.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

from neo4j import Driver, ManagedTransaction, NotificationDisabledCategory, Transaction

from iekg.core.rules import (
    ACYCLIC_EDGE_TYPES,
    ALL_RULES,
    DERIVED_FROM_RESOURCE,
    REQUIRED_PARENT,
    RI_01,
    RI_02,
    RI_03,
    RI_04,
    RI_05,
    RI_06,
    RI_07,
    RI_08,
    RI_09,
    RI_10,
    RM_01,
    RM_02,
    RM_03,
    RM_04,
    RM_05,
)
from iekg.graph_schema import (
    ADMITTED_PAIRS,
    ALL_LABELS,
    EDGE_PROPERTIES_BY_SOURCE_LAYER,
    EDGE_TYPES,
    INSTITUTIONAL,
    KEY,
    KNOWLEDGE_AREA,
    KNOWLEDGE_ELEMENT,
    KNOWLEDGE_ELEMENT_SUBCLASSES,
    KNOWLEDGE_UNIT,
    LAYER,
    LAYERS,
    LEARNING_RESOURCE,
    LOCATOR_PATTERN,
    NODE_PROPERTIES,
    PART_OF,
    PROVENANCE,
    REFERENCE,
    RESOURCE_LOCATOR,
    TOP_LEVEL_LABELS,
    WAS_DERIVED_FROM,
)

Tx = Transaction | ManagedTransaction

SAMPLE_SIZE = 20


@dataclass(frozen=True)
class RuleResult:
    rule: str
    violations: int
    sample: tuple[str, ...]


@dataclass(frozen=True)
class AuditReport:
    results: tuple[RuleResult, ...]

    @property
    def violations(self) -> int:
        return sum(result.violations for result in self.results)

    @property
    def clean(self) -> bool:
        return self.violations == 0


def _node(variable: str) -> str:
    # The key names the node; a node without one is named by its element id.
    return f"coalesce(toStringOrNull({variable}.{KEY}), elementId({variable}))"


def _edge(source: str, edge_type_expression: str, target: str) -> str:
    return f"'(' + {_node(source)} + ')-[:' + {edge_type_expression} + ']->(' + {_node(target)} + ')'"


def _join(list_expression: str) -> str:
    # Cypher 5 has no list-to-string function and toString() rejects lists.
    return f"reduce(text = '', item IN {list_expression} | text + ' ' + item)"


_QUERIES: Mapping[str, str] = MappingProxyType({
    RI_01: f"""
        MATCH (n) WHERE n.{KEY} IS NULL
        RETURN {_node('n')} + ' has no key' AS element
        UNION ALL
        MATCH (n) WHERE n.{KEY} IS NOT NULL
        WITH n.{KEY} AS key, count(*) AS copies WHERE copies > 1
        RETURN coalesce(toStringOrNull(key), '<non-scalar key>') + ' is the key of '
               + toString(copies) + ' nodes' AS element
    """,
    RI_02: f"""
        MATCH (n)
        WITH n, labels(n) AS labels
        WHERE none(label IN labels WHERE label IN $all_labels)
           OR any(label IN labels WHERE NOT label IN $all_labels)
           OR (any(label IN labels WHERE label IN $knowledge_levels)
               AND NOT '{KNOWLEDGE_ELEMENT}' IN labels)
        RETURN {_node('n')} + ' has labels' + {_join('labels')} AS element
    """,
    RI_03: f"""
        MATCH (n)
        WITH n, labels(n) AS labels
        WITH n, labels,
             size([label IN labels WHERE label IN $top_level_labels]) AS top_level,
             size([label IN labels WHERE label IN $knowledge_levels]) AS levels
        WHERE top_level <> 1 OR ('{KNOWLEDGE_ELEMENT}' IN labels AND levels <> 1)
        RETURN {_node('n')} + ' has labels' + {_join('labels')} AS element
    """,
    RI_04: f"""
        MATCH (a)-[r]->(b) WHERE NOT type(r) IN $edge_types
        RETURN {_edge('a', 'type(r)', 'b')} AS element
    """,
    RI_05: f"""
        MATCH (a)-[r]->(b) WHERE type(r) IN $edge_types
        WITH a, r, b, labels(a) AS source_labels, labels(b) AS target_labels
        WHERE none(pair IN $admitted_pairs
                   WHERE pair[0] = type(r) AND pair[1] IN source_labels AND pair[2] IN target_labels)
        RETURN {_edge('a', 'type(r)', 'b')} + ' joins' + {_join('source_labels')}
               + ' to' + {_join('target_labels')} AS element
    """,
    RI_06: f"""
        MATCH (a)-[r]->(b)
        WITH a, b, type(r) AS edge_type, count(r) AS copies WHERE copies > 1
        RETURN {_edge('a', 'edge_type', 'b')} + ' appears ' + toString(copies) + ' times' AS element
    """,
    RI_07: f"""
        MATCH (unit:{KNOWLEDGE_UNIT})-[:{PART_OF}]->(area:{KNOWLEDGE_AREA})
        WITH unit, count(DISTINCT area) AS areas WHERE areas > 1
        RETURN {_node('unit')} + ' is part of ' + toString(areas) + ' areas' AS element
    """,
    RI_08: "\nUNION ALL\n".join(
        f"""
        MATCH (n:{child}) WHERE NOT EXISTS {{ (n)-[:{PART_OF}]->(:{parent}) }}
        RETURN {_node('n')} + ' ({child}) is not part of any {parent}' AS element
        """
        for child, parent in REQUIRED_PARENT.items()
    ),
    RI_09: f"""
        MATCH (n)
        WITH n, reduce(declared = [], label IN labels(n)
                       | declared + coalesce($node_properties[label], [])) AS declared
        WITH n, [name IN keys(n) WHERE NOT name IN declared] AS undeclared
        WHERE size(undeclared) > 0
        RETURN {_node('n')} + ' has undeclared properties' + {_join('undeclared')} AS element
        UNION ALL
        MATCH (a)-[r]->(b)
        WITH a, r, b, CASE WHEN a.{LAYER} IS :: STRING THEN $edge_properties[a.{LAYER}] END AS declared
        WITH a, r, b, [name IN keys(r) WHERE NOT name IN coalesce(declared, [])] AS undeclared
        WHERE size(undeclared) > 0
        RETURN {_edge('a', 'type(r)', 'b')} + ' has undeclared properties'
               + {_join('undeclared')} AS element
    """,
    RI_10: f"""
        MATCH (n:{LEARNING_RESOURCE}) WHERE n.{RESOURCE_LOCATOR} IS NOT NULL
          AND NOT CASE WHEN n.{RESOURCE_LOCATOR} IS :: STRING
                       THEN n.{RESOURCE_LOCATOR} =~ $locator_pattern
                       ELSE false END
        RETURN {_node('n')} + ' has locator '
               + coalesce(toStringOrNull(n.{RESOURCE_LOCATOR}), '<non-scalar>') AS element
    """,
    RM_01: f"""
        MATCH (n) WHERE NOT coalesce(n.{LAYER} IN $layers, false)
        RETURN {_node('n')} + ' has layer '
               + coalesce(toStringOrNull(n.{LAYER}), '<none>') AS element
    """,
    RM_02: f"""
        MATCH (a)-[r]->(b) WHERE a.{LAYER} = '{REFERENCE}' AND b.{LAYER} = '{INSTITUTIONAL}'
        RETURN {_edge('a', 'type(r)', 'b')} AS element
    """,
    RM_03: f"""
        MATCH (n) WHERE n.{LAYER} = '{INSTITUTIONAL}'
          AND any(label IN labels(n) WHERE label IN $derived_from_resource)
          AND NOT EXISTS {{ (n)-[:{WAS_DERIVED_FROM}]->(:{LEARNING_RESOURCE}) }}
        RETURN {_node('n')} + ' does not derive from any {LEARNING_RESOURCE}' AS element
        UNION ALL
        MATCH (a)-[r]->(b) WHERE a.{LAYER} = '{INSTITUTIONAL}' AND r.{PROVENANCE} IS NULL
        RETURN {_edge('a', 'type(r)', 'b')} + ' has no provenance' AS element
    """,
    # A path does not repeat edges, so the expansion ends even on a cycle.
    RM_04: "\nUNION ALL\n".join(
        f"""
        MATCH (n) WHERE EXISTS {{ (n)-[:{edge_type}*1..]->(n) }}
        RETURN {_node('n')} + ' is on a {edge_type} cycle' AS element
        """
        for edge_type in ACYCLIC_EDGE_TYPES
    ),
    RM_05: f"""
        MATCH (n:{LEARNING_RESOURCE}) WHERE n.{RESOURCE_LOCATOR} IS NULL
        RETURN {_node('n')} + ' has no locator' AS element
    """,
})

_PARAMETERS = MappingProxyType({
    "all_labels": list(ALL_LABELS),
    "top_level_labels": list(TOP_LEVEL_LABELS),
    "knowledge_levels": list(KNOWLEDGE_ELEMENT_SUBCLASSES),
    "edge_types": list(EDGE_TYPES),
    "admitted_pairs": sorted([edge_type, source, target]
                             for edge_type, pairs in ADMITTED_PAIRS.items()
                             for source, target in pairs),
    "node_properties": {label: list(names) for label, names in NODE_PROPERTIES.items()},
    "edge_properties": {layer: list(names) for layer, names in EDGE_PROPERTIES_BY_SOURCE_LAYER.items()},
    "derived_from_resource": list(DERIVED_FROM_RESOURCE),
    "locator_pattern": LOCATOR_PATTERN,
    "layers": list(LAYERS),
    "sample_size": SAMPLE_SIZE,
})


def query_for(rule: str) -> str:
    """The audit query of ``rule``, wrapped to return a count and a sample."""
    return (
        f"CALL () {{ {_QUERIES[rule]} }} "
        "WITH element ORDER BY element "
        "RETURN count(element) AS violations, collect(element)[..$sample_size] AS sample"
    )


def audit_rule(tx: Tx, rule: str) -> RuleResult:
    record = tx.run(query_for(rule), **_PARAMETERS).single(strict=True)
    return RuleResult(rule, record["violations"], tuple(record["sample"]))


def audit(tx: Tx) -> AuditReport:
    return AuditReport(tuple(audit_rule(tx, rule) for rule in ALL_RULES))


def audit_database(driver: Driver, database: str) -> AuditReport:
    """Audit the whole graph in one read transaction, so the report is one state."""
    # The queries name every declared label, type and property, including the
    # ones the graph does not hold yet; the server would warn about each.
    with driver.session(
        database=database,
        notifications_disabled_categories=[NotificationDisabledCategory.UNRECOGNIZED],
    ) as session:
        return session.execute_read(audit)
