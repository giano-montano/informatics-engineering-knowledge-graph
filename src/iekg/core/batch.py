"""Batch and snapshot: what the writer receives and what a run reads first."""

from collections import Counter
from collections.abc import Mapping
from dataclasses import dataclass, field
from functools import cached_property


@dataclass(frozen=True)
class NodeFact:
    """A node to write. ``label`` is its class; key and layer are not properties
    here: the key identifies the fact and the write path fixes the layer."""

    key: str
    label: str
    properties: Mapping[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class EdgeFact:
    """An edge to write, in the direction of the asserted property."""

    type: str
    source: str
    target: str

    def describe(self) -> str:
        return f"({self.source})-[:{self.type}]->({self.target})"


@dataclass(frozen=True)
class Batch:
    """The facts that are validated and written together (the annex's "lote")."""

    nodes: tuple[NodeFact, ...] = ()
    edges: tuple[EdgeFact, ...] = ()

    def __post_init__(self) -> None:
        repeated_keys = [key for key, n in Counter(n.key for n in self.nodes).items() if n > 1]
        if repeated_keys:
            raise ValueError(f"batch repeats node keys: {sorted(repeated_keys)}")
        repeated_edges = [e.describe() for e, n in Counter(self.edges).items() if n > 1]
        if repeated_edges:
            raise ValueError(f"batch repeats edges: {sorted(repeated_edges)}")

    @cached_property
    def nodes_by_key(self) -> Mapping[str, NodeFact]:
        return {node.key: node for node in self.nodes}


@dataclass(frozen=True)
class SnapshotNode:
    """A node as the graph has it. The validator and the writer read only
    ``label`` and ``layer``; the labels and the area are for the extractor."""

    label: str
    layer: str
    pref_label_es: str | None = None
    pref_label_en: str | None = None
    # The key of the knowledge area a knowledge unit is part of.
    area: str | None = None


@dataclass(frozen=True)
class Snapshot:
    """The graph as a run reads it before writing (ADR-011).

    Holds what the validator and the writer need: every node with its class and
    layer, and the edges that must not form cycles. For the extractor it also
    holds the labels of every node, the area of every knowledge unit and the
    partonomy edges of topics and concepts. A load starts from an empty
    snapshot, because it starts from an empty base.
    """

    nodes: Mapping[str, SnapshotNode] = field(default_factory=dict)
    edges: tuple[EdgeFact, ...] = ()


def label_of(key: str, batch: Batch, snapshot: Snapshot) -> str | None:
    """The class of ``key``: as the graph has it, else as the batch brings it."""
    if key in snapshot.nodes:
        return snapshot.nodes[key].label
    node = batch.nodes_by_key.get(key)
    return node.label if node else None


def batch_to_data(batch: Batch) -> dict:
    """The batch as plain data, for the fact store and the discards."""
    return {
        "nodes": [{"key": n.key, "label": n.label, "properties": dict(n.properties)} for n in batch.nodes],
        "edges": [{"type": e.type, "source": e.source, "target": e.target} for e in batch.edges],
    }


def batch_from_data(data: Mapping) -> Batch:
    return Batch(
        nodes=tuple(NodeFact(n["key"], n["label"], dict(n["properties"])) for n in data["nodes"]),
        edges=tuple(EdgeFact(e["type"], e["source"], e["target"]) for e in data["edges"]),
    )
