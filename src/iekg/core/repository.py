"""Graph repository: empties and initializes the base, and writes batches.

Every write is a fixed-form template built from the graph schema that only
receives values (ADR-003, ADR-005). The form of the write is what prevents
RI-02, RI-03, RI-04, RI-06, RI-09, RM-01 and RM-03; the uniqueness constraints,
together with MERGE by key, prevent RI-01.
"""

from collections import Counter, defaultdict
from collections.abc import Mapping
from dataclasses import dataclass

from neo4j import Driver, ManagedTransaction, Transaction

from iekg.core.batch import Batch, Snapshot, label_of
from iekg.graph_schema import (
    ADMITTED_PAIRS,
    ALL_LABELS,
    EDGE_TYPES,
    INSTITUTIONAL,
    KEY,
    KNOWLEDGE_ELEMENT,
    KNOWLEDGE_ELEMENT_SUBCLASSES,
    LAYER,
    LAYERS,
    NODE_CLASSES,
    NODE_PROPERTIES,
    PROVENANCE,
    REFERENCE,
)

Tx = Transaction | ManagedTransaction


class WriteMismatch(Exception):
    """A write did not produce what was expected; its transaction is rolled back."""


@dataclass(frozen=True)
class WriteResult:
    nodes_created: int
    relationships_created: int
    labels_added: int
    properties_set: int


def constraint_name(label: str) -> str:
    return f"{_identifier(label, ALL_LABELS)}_{KEY}_unique"


def _identifier(name: str, declared: tuple[str, ...]) -> str:
    # Labels and edge types are interpolated into Cypher, which takes no
    # parameters there; only declared names get in.
    if name not in declared:
        raise ValueError(f"{name!r} is not declared in the graph schema")
    return name


def _quote(name: str) -> str:
    return "`" + name.replace("`", "``") + "`"


def _node_template(label: str) -> str:
    labels = _identifier(label, NODE_CLASSES)
    if label in KNOWLEDGE_ELEMENT_SUBCLASSES:
        labels += f":{KNOWLEDGE_ELEMENT}"
    assignments = "".join(
        f", n.{name} = row.properties.{name}"
        for name in NODE_PROPERTIES[label]
        if name not in (KEY, LAYER)
    )
    # ON CREATE only: an existing node keeps its properties, its layer and its
    # provenance (annex, write conditions 4 and 5).
    return (
        "UNWIND $rows AS row "
        f"MERGE (n:{labels} {{{KEY}: row.key}}) "
        f"ON CREATE SET n.{LAYER} = $layer{assignments} "
        "RETURN count(n) AS written"
    )


def _edge_template(edge_type: str, source: str, target: str) -> str:
    # Endpoints are matched by a label with a uniqueness constraint, so the
    # lookup goes through the index; an endpoint with another class is not found.
    return (
        "UNWIND $rows AS row "
        f"MATCH (a:{_identifier(source, NODE_CLASSES)} {{{KEY}: row.source}}) "
        f"MATCH (b:{_identifier(target, NODE_CLASSES)} {{{KEY}: row.target}}) "
        f"MERGE (a)-[r:{_identifier(edge_type, EDGE_TYPES)}]->(b) "
        f"ON CREATE SET r.{PROVENANCE} = $provenance "
        "RETURN count(r) AS written"
    )


_NODE_TEMPLATES: Mapping[str, str] = {label: _node_template(label) for label in NODE_CLASSES}
_EDGE_TEMPLATES: Mapping[tuple[str, str, str], str] = {
    (edge_type, source, target): _edge_template(edge_type, source, target)
    for edge_type, pairs in ADMITTED_PAIRS.items()
    for source, target in pairs
}


def write_batch_in(
    tx: Tx,
    batch: Batch,
    snapshot: Snapshot,
    *,
    layer: str,
    provenance: str | None = None,
) -> WriteResult:
    """Write ``batch`` inside ``tx`` and check that it produced what was expected.

    The write path fixes the layer of the new nodes and the provenance of the
    new edges: the load writes the reference layer without provenance, and the
    ingestion the institutional layer with the document it read (RM-01, RM-03).
    Raises ``WriteMismatch`` if the counters do not match; the caller's
    transaction must then be rolled back.
    """
    if layer not in LAYERS:
        raise ValueError(f"unknown layer {layer!r}")
    if (layer == INSTITUTIONAL) != (provenance is not None):
        raise ValueError("institutional writes carry provenance, and reference writes do not")

    node_rows: dict[str, list[dict]] = defaultdict(list)
    for node in batch.nodes:
        if node.label not in _NODE_TEMPLATES:
            raise ValueError(f"{node.key}: {node.label!r} is not a node class")
        undeclared = set(node.properties) - (set(NODE_PROPERTIES[node.label]) - {KEY, LAYER})
        if undeclared:
            raise ValueError(f"{node.key}: undeclared properties {sorted(undeclared)}")
        node_rows[node.label].append({"key": node.key, "properties": dict(node.properties)})

    edge_rows: dict[tuple[str, str, str], list[dict]] = defaultdict(list)
    for edge in batch.edges:
        group = (edge.type, label_of(edge.source, batch, snapshot), label_of(edge.target, batch, snapshot))
        if group not in _EDGE_TEMPLATES:
            raise ValueError(f"{edge.describe()}: {group[1]} -> {group[2]} is not admitted for {edge.type}")
        edge_rows[group].append({"source": edge.source, "target": edge.target})

    counters: Counter[str] = Counter()

    def run(query: str, rows: list[dict], **parameters) -> int:
        result = tx.run(query, rows=rows, **parameters)
        written = result.single(strict=True)["written"]
        summary = result.consume().counters
        counters.update(
            nodes_created=summary.nodes_created,
            relationships_created=summary.relationships_created,
            labels_added=summary.labels_added,
            properties_set=summary.properties_set,
        )
        return written

    for label in sorted(node_rows):
        run(_NODE_TEMPLATES[label], node_rows[label], layer=layer)
    expected_nodes = sum(1 for node in batch.nodes if node.key not in snapshot.nodes)
    if counters["nodes_created"] != expected_nodes:
        # A node the snapshot did not have already existed: someone else wrote.
        raise WriteMismatch(f"expected {expected_nodes} new nodes, created {counters['nodes_created']}")

    for group in sorted(edge_rows):
        rows = edge_rows[group]
        written = run(_EDGE_TEMPLATES[group], rows, provenance=provenance)
        if written != len(rows):
            raise WriteMismatch(f"{group[0]} {group[1]} -> {group[2]}: {len(rows)} edges sent, {written} written")

    return WriteResult(
        nodes_created=counters["nodes_created"],
        relationships_created=counters["relationships_created"],
        labels_added=counters["labels_added"],
        properties_set=counters["properties_set"],
    )


class GraphRepository:
    def __init__(self, driver: Driver, database: str) -> None:
        self._driver = driver
        self._database = database

    def reset(self) -> int:
        """Empty the base and create the uniqueness constraints; return how many.

        Schema commands cannot share a transaction with data writes, so each
        runs on its own.
        """
        with self._driver.session(database=self._database) as session:
            session.execute_write(lambda tx: tx.run("MATCH (n) DETACH DELETE n").consume())
            for name in session.run("SHOW CONSTRAINTS YIELD name RETURN name").value():
                session.run(f"DROP CONSTRAINT {_quote(name)}").consume()
            # Lookup indexes are Neo4j's own; every other index goes.
            for name in session.run("SHOW INDEXES YIELD name, type WHERE type <> 'LOOKUP' RETURN name").value():
                session.run(f"DROP INDEX {_quote(name)}").consume()
            # Neo4j compares schema, not names, on IF NOT EXISTS: after the drops
            # above, a plain CREATE is what guarantees these exact names.
            for label in ALL_LABELS:
                session.run(
                    f"CREATE CONSTRAINT {constraint_name(label)} "
                    f"FOR (n:{label}) REQUIRE n.{KEY} IS UNIQUE"
                ).consume()
        return len(ALL_LABELS)

    def write_batch(
        self,
        batch: Batch,
        snapshot: Snapshot,
        *,
        layer: str = REFERENCE,
        provenance: str | None = None,
    ) -> WriteResult:
        """Write ``batch`` in a single transaction: commit, or roll back and raise."""
        with self._driver.session(database=self._database) as session:
            return session.execute_write(
                write_batch_in, batch, snapshot, layer=layer, provenance=provenance
            )

    def count_elements(self) -> tuple[dict[str, int], dict[str, int]]:
        """Nodes per label and edges per type, as the base holds them now."""
        with self._driver.session(database=self._database) as session:
            nodes = session.run(
                "MATCH (n) UNWIND labels(n) AS label RETURN label, count(*) AS n ORDER BY label"
            ).data()
            edges = session.run(
                "MATCH ()-[r]->() RETURN type(r) AS type, count(*) AS n ORDER BY type"
            ).data()
        return {row["label"]: row["n"] for row in nodes}, {row["type"]: row["n"] for row in edges}
