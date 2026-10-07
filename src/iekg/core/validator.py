"""Validator: schema, snapshot and batch -> list of violations.

A pure function: it reads neither the database nor anything outside its
arguments (ADR-011). It accumulates every violation of the batch, not only the
first one (ADR-010).
"""

import re
from collections import defaultdict
from collections.abc import Callable, Collection, Iterable
from dataclasses import dataclass

from iekg.core.batch import Batch, EdgeFact, Snapshot, label_of
from iekg.core.rules import (
    ACYCLIC_EDGE_TYPES,
    REQUIRED_PARENT,
    RI_05,
    RI_08,
    RI_10,
    RM_02,
    RM_04,
    RM_05,
)
from iekg.graph_schema import (
    ADMITTED_PAIRS,
    INSTITUTIONAL,
    LAYERS,
    LEARNING_RESOURCE,
    LOCATOR_PATTERN,
    PART_OF,
    REFERENCE,
    RESOURCE_LOCATOR,
)

# Rules the validator prevents on each write path (annex, Table 3; thesis,
# Table 21). In the load, RI-08 is only detected by the audit.
LOAD_RULES = (RI_05, RI_10, RM_02, RM_04, RM_05)
INGESTION_RULES = (RI_05, RI_08, RI_10, RM_02, RM_04, RM_05)


@dataclass(frozen=True)
class Violation:
    rule: str
    fact: str
    message: str


def validate(
    batch: Batch,
    snapshot: Snapshot,
    *,
    layer: str,
    rules: Collection[str],
) -> list[Violation]:
    """Check ``rules`` on ``batch`` as written on top of ``snapshot``.

    ``layer`` is the layer the write path gives to the batch's new nodes.
    """
    if layer not in LAYERS:
        raise ValueError(f"unknown layer {layer!r}")
    unknown = set(rules) - set(_CHECKS)
    if unknown:
        raise ValueError(f"the validator does not check {sorted(unknown)}")
    context = _Context(batch, snapshot, layer)
    violations: list[Violation] = []
    for rule, check in _CHECKS.items():
        if rule in rules:
            violations.extend(check(context))
    return violations


class _Context:
    def __init__(self, batch: Batch, snapshot: Snapshot, layer: str) -> None:
        self.batch = batch
        self.snapshot = snapshot
        self.layer = layer

    def label_of(self, key: str) -> str | None:
        return label_of(key, self.batch, self.snapshot)

    def layer_of(self, key: str) -> str | None:
        # An existing node keeps its layer: the write only sets it on creation.
        if key in self.snapshot.nodes:
            return self.snapshot.nodes[key].layer
        return self.layer if key in self.batch.nodes_by_key else None


def _check_admitted_pairs(context: _Context) -> Iterable[Violation]:
    for edge in context.batch.edges:
        pairs = ADMITTED_PAIRS.get(edge.type)
        if pairs is None:
            yield Violation(RI_05, edge.describe(), f"{edge.type} is not a declared edge type")
            continue
        source, target = context.label_of(edge.source), context.label_of(edge.target)
        if source is None:
            yield Violation(RI_05, edge.describe(), "the source node does not exist")
        if target is None:
            yield Violation(RI_05, edge.describe(), "the target node does not exist")
        if source and target and (source, target) not in pairs:
            yield Violation(RI_05, edge.describe(), f"{source} -> {target} is not admitted for {edge.type}")


def _check_anchoring(context: _Context) -> Iterable[Violation]:
    # Only new nodes need to bring their partonomy edge: an anchored node never
    # loses it, because the ingestion is cumulative (annex, notes to Table 3).
    parents = defaultdict(set)
    for edge in context.batch.edges:
        if edge.type == PART_OF:
            parents[edge.source].add(context.label_of(edge.target))
    for node in context.batch.nodes:
        parent = REQUIRED_PARENT.get(node.label)
        if parent and node.key not in context.snapshot.nodes and parent not in parents[node.key]:
            yield Violation(RI_08, node.key, f"new {node.label} has no {PART_OF} edge to a {parent}")


def _check_locator_form(context: _Context) -> Iterable[Violation]:
    for node in context.batch.nodes:
        locator = node.properties.get(RESOURCE_LOCATOR)
        if locator is not None and not re.fullmatch(LOCATOR_PATTERN, locator):
            yield Violation(RI_10, node.key, f"locator {locator!r} is not an absolute http or https URI")


def _check_layer_boundary(context: _Context) -> Iterable[Violation]:
    for edge in context.batch.edges:
        if context.layer_of(edge.source) == REFERENCE and context.layer_of(edge.target) == INSTITUTIONAL:
            yield Violation(RM_02, edge.describe(), "edge from a reference node to an institutional node")


def _check_cycles(context: _Context) -> Iterable[Violation]:
    for edge_type in ACYCLIC_EDGE_TYPES:
        edges = [e for e in context.snapshot.edges + context.batch.edges if e.type == edge_type]
        for cycle in _cycles(edges):
            yield Violation(RM_04, " -> ".join(cycle), f"{edge_type} cycle through {len(cycle)} node(s)")


def _check_locator_presence(context: _Context) -> Iterable[Violation]:
    for node in context.batch.nodes:
        if node.label == LEARNING_RESOURCE and RESOURCE_LOCATOR not in node.properties:
            yield Violation(RM_05, node.key, "learning resource without locator")


_CHECKS: dict[str, Callable[[_Context], Iterable[Violation]]] = {
    RI_05: _check_admitted_pairs,
    RI_08: _check_anchoring,
    RI_10: _check_locator_form,
    RM_02: _check_layer_boundary,
    RM_04: _check_cycles,
    RM_05: _check_locator_presence,
}


def _cycles(edges: Iterable[EdgeFact]) -> list[list[str]]:
    """Strongly connected components that contain a cycle, each sorted by key.

    Iterative Tarjan, so a long prerequisite chain cannot exhaust the stack.
    """
    successors: dict[str, set[str]] = defaultdict(set)
    for edge in edges:
        successors[edge.source].add(edge.target)
        successors.setdefault(edge.target, set())

    index: dict[str, int] = {}
    lowlink: dict[str, int] = {}
    on_stack: set[str] = set()
    stack: list[str] = []
    components: list[list[str]] = []

    for root in sorted(successors):
        if root in index:
            continue
        work = [(root, iter(sorted(successors[root])))]
        index[root] = lowlink[root] = len(index)
        stack.append(root)
        on_stack.add(root)
        while work:
            node, children = work[-1]
            child = next(children, None)
            if child is None:
                work.pop()
                if work:
                    parent = work[-1][0]
                    lowlink[parent] = min(lowlink[parent], lowlink[node])
                if lowlink[node] == index[node]:
                    component = []
                    while True:
                        member = stack.pop()
                        on_stack.discard(member)
                        component.append(member)
                        if member == node:
                            break
                    if len(component) > 1 or node in successors[node]:
                        components.append(sorted(component))
            elif child not in index:
                index[child] = lowlink[child] = len(index)
                stack.append(child)
                on_stack.add(child)
                work.append((child, iter(sorted(successors[child]))))
            elif child in on_stack:
                lowlink[node] = min(lowlink[node], index[child])
    return sorted(components)
