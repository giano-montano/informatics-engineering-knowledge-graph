"""Graph repository: empties and initializes the base, reads the snapshot and
writes batches.

Every write is a fixed-form template built from the graph schema that only
receives values (ADR-003, ADR-005). The form of the write is what prevents
RI-02, RI-03, RI-04, RI-06, RI-09, RM-01 and RM-03, and the layer boundary
(annex, write condition 6); the uniqueness constraints, together with MERGE by
key, prevent RI-01.
"""

from collections import Counter, defaultdict
from collections.abc import Mapping
from dataclasses import dataclass

from neo4j import Driver, ManagedTransaction, NotificationDisabledCategory, Transaction

from iekg.core.batch import Batch, EdgeFact, Snapshot, SnapshotNode, label_of
from iekg.core.rules import ACYCLIC_EDGE_TYPES, DERIVED_FROM_RESOURCE
from iekg.graph_schema import (
    ADMITTED_PAIRS,
    ALL_LABELS,
    CONCEPT,
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
    NODE_CLASSES,
    NODE_PROPERTIES,
    PART_OF,
    PREF_LABEL_EN,
    PREF_LABEL_ES,
    PROVENANCE,
    SEARCH_ANALYZER,
    SEARCH_INDEX,
    SEARCH_LABELS,
    SEARCH_PROPERTIES,
    TOPIC,
    WAS_DERIVED_FROM,
)

Tx = Transaction | ManagedTransaction


class WriteMismatch(Exception):
    """A write did not produce what was expected; its transaction is rolled back."""


class SnapshotError(Exception):
    """The graph holds something the snapshot cannot represent.

    The audit gate only lets a run start on a clean graph, so this means the
    graph changed outside the write paths.
    """


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
    # The source must also have the layer of the write: the load's edges leave
    # reference nodes, and the ingestion's leave institutional ones (annex,
    # write condition 6), so neither can write an edge the other owns.
    return (
        "UNWIND $rows AS row "
        f"MATCH (a:{_identifier(source, NODE_CLASSES)} {{{KEY}: row.source, {LAYER}: $layer}}) "
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
    ``provenance`` is the key of that document's learning resource: every new
    topic, concept and course gets its ``WAS_DERIVED_FROM`` edge to it in this
    same write. Raises ``WriteMismatch`` if the counters do not match; the
    caller's transaction must then be rolled back.
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

    # RM-03 for nodes. Only new ones: an existing node keeps the provenance it
    # was created with (ADR-006). The reapplication repeats this same write on
    # the same graph state, so it derives the same edges (ADR-012).
    if layer == INSTITUTIONAL:
        edges = set(batch.edges)
        for node in batch.nodes:
            derivation = EdgeFact(WAS_DERIVED_FROM, node.key, provenance)
            if node.label in DERIVED_FROM_RESOURCE and node.key not in snapshot.nodes and derivation not in edges:
                group = (WAS_DERIVED_FROM, node.label, LEARNING_RESOURCE)
                edge_rows[group].append({"source": node.key, "target": provenance})

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
        written = run(_EDGE_TEMPLATES[group], rows, provenance=provenance, layer=layer)
        if written != len(rows):
            raise WriteMismatch(
                f"{group[0]} {group[1]} -> {group[2]}: {len(rows)} edges sent, {written} written"
                f" (an endpoint is missing, or a source is not in the {layer} layer)"
            )

    return WriteResult(
        nodes_created=counters["nodes_created"],
        relationships_created=counters["relationships_created"],
        labels_added=counters["labels_added"],
        properties_set=counters["properties_set"],
    )


_SNAPSHOT_NODES = f"""
    MATCH (n)
    RETURN n.{KEY} AS key, [label IN labels(n) WHERE label IN $classes] AS classes,
           n.{LAYER} AS layer, n.{PREF_LABEL_ES} AS es, n.{PREF_LABEL_EN} AS en,
           COLLECT {{ MATCH (n:{KNOWLEDGE_UNIT})-[:{PART_OF}]->(a:{KNOWLEDGE_AREA}) RETURN a.{KEY} }} AS areas
"""

# The acyclic edges are for the validator; where existing topics and concepts
# hang is for the extractor.
_SNAPSHOT_EDGES = f"""
    MATCH (a)-[r]->(b) WHERE type(r) IN $acyclic
    RETURN type(r) AS type, a.{KEY} AS source, b.{KEY} AS target
    UNION ALL
    MATCH (a:{TOPIC}|{CONCEPT})-[r:{PART_OF}]->(b)
    RETURN type(r) AS type, a.{KEY} AS source, b.{KEY} AS target
"""


def read_snapshot_in(tx: Tx) -> Snapshot:
    """Read the snapshot a run starts from (ADR-011)."""
    nodes: dict[str, SnapshotNode] = {}
    for row in tx.run(_SNAPSHOT_NODES, classes=list(NODE_CLASSES)):
        key, classes, layer, areas = row["key"], row["classes"], row["layer"], row["areas"]
        if not isinstance(key, str):
            raise SnapshotError(f"a node has key {key!r}")
        if len(classes) != 1 or layer not in LAYERS or len(areas) > 1:
            raise SnapshotError(f"{key}: classes {classes}, layer {layer!r}, areas {areas}")
        nodes[key] = SnapshotNode(classes[0], layer, row["es"], row["en"], areas[0] if areas else None)
    edges = tuple(
        EdgeFact(row["type"], row["source"], row["target"])
        for row in tx.run(_SNAPSHOT_EDGES, acyclic=list(ACYCLIC_EDGE_TYPES))
    )
    return Snapshot(nodes=nodes, edges=edges)


class GraphRepository:
    def __init__(self, driver: Driver, database: str) -> None:
        self._driver = driver
        self._database = database

    def reset(self) -> int:
        """Empty the base and create the uniqueness constraints and the search index.

        Returns how many constraints it created.

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
            session.run(
                f"CREATE FULLTEXT INDEX {SEARCH_INDEX} FOR (n:{'|'.join(SEARCH_LABELS)}) "
                f"ON EACH [{', '.join(f'n.{name}' for name in SEARCH_PROPERTIES)}] "
                f"OPTIONS {{indexConfig: {{`fulltext.analyzer`: '{SEARCH_ANALYZER}'}}}}"
            ).consume()
        return len(ALL_LABELS)

    def read_snapshot(self) -> Snapshot:
        """Read the snapshot in one read transaction, so it is one state."""
        # An empty base does not know the labels and properties yet.
        with self._driver.session(
            database=self._database,
            notifications_disabled_categories=[NotificationDisabledCategory.UNRECOGNIZED],
        ) as session:
            return session.execute_read(read_snapshot_in)

    def write_batch(
        self,
        batch: Batch,
        snapshot: Snapshot,
        *,
        layer: str,
        provenance: str | None = None,
    ) -> WriteResult:
        """Write ``batch`` in a single transaction: commit, or roll back and raise.

        ``layer`` has no default: a path that forgot it would write its nodes as
        reference ones, and no rule tells a reference topic from a backbone node.
        """
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
