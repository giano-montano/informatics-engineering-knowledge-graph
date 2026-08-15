"""Extraction -> A-box: mint, validate, emit Cypher. Never executes.

This is the module that keeps the thesis' structural claim true: the LLM
produces data, and deterministic code produces the Cypher. Nothing here calls
a model, and nothing here opens a session. It takes the JSON an extraction
stage returned and turns it into a file a human can read before anything is
written to the graph.

Two invariants it enforces by construction, not by prompt:

  the backbone is read-only    coined nodes are MERGEd, backbone endpoints are
                               only MATCHed. A statement that could create a
                               KnowledgeUnit is never emitted.
  minting is deterministic     the IRI comes from the canonical label through
                               `contracts.slug`, so re-running an identical
                               extraction re-merges instead of duplicating.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from iekg.contracts import Extraction, slug
from iekg.rules import Edge, Node, Spec, Violation


@dataclass(frozen=True)
class SourceDocument:
    """The syllabus, as the graph will remember it."""

    code: str
    term: str
    path: Path
    title: str = ""

    @property
    def key(self) -> str:
        return f"{self.code}-{self.term}"


@dataclass(frozen=True)
class ABox:
    nodes: tuple[Node, ...]          # coined, written with MERGE
    context: tuple[Node, ...]        # backbone endpoints, only matched
    edges: tuple[Edge, ...]
    violations: tuple[Violation, ...]

    @property
    def conformance(self) -> float:
        """Share of coined elements that break no rule.

        Text2KGBench's Ontology Conformance, adapted: there it is computed over
        triples against an ontology, here over nodes and edges against the
        rules compiled from that ontology. Reported alongside precision because
        precision alone rewards a pipeline that extracts three obvious things.
        """
        total = len(self.nodes) + len(self.edges)
        if not total:
            return 0.0
        offending = {v.entity for v in self.violations}
        return round(1 - min(len(offending), total) / total, 4)

    def by_rule(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for v in self.violations:
            counts[v.rule] = counts.get(v.rule, 0) + 1
        return counts


# ---------------------------------------------------------------------------
# Minting
# ---------------------------------------------------------------------------

def mint(spec: Spec, owl_class: str, label: str, *, scope: str = "") -> str:
    """IRI for a coined element. `scope` keeps two documents' elements apart.

    Whether to scope is an open question, not a detail: unscoped, two syllabi
    teaching 'Normalization' merge into one Concept, which is the behaviour the
    institutional layer eventually wants and also the behaviour that silently
    conflates two different things carrying the same name. It is a pipeline
    option so the comparison can measure it instead of assuming it.
    """
    fragment = f"{scope}-{slug(label)}" if scope else slug(label)
    return f"{spec.namespace}{spec.iri_prefix(owl_class)}{fragment}"


def _coined_node(spec: Spec, owl_class: str, iri: str, canonical: str,
                 source: str) -> Node:
    props = {
        spec.coined_property("canonical_label"): canonical,
        spec.coined_property("layer"): spec.institutional_layer,
    }
    if source and source != canonical:
        props[spec.coined_property("source_label")] = source
    return Node(iri=iri, labels=spec.labels_for(owl_class), props=props)


def build(extraction: Extraction, document: SourceDocument, spec: Spec, *,
          scope_iris: bool = False) -> ABox:
    """Turn a linked extraction into nodes, edges and their violations."""
    scope = document.code if scope_iris else ""

    resource_iri = mint(spec, "LearningResource", document.key)
    resource = Node(
        iri=resource_iri,
        labels=spec.labels_for("LearningResource"),
        props={
            spec.coined_property("canonical_label"): document.title or document.key,
            spec.coined_property("layer"): spec.institutional_layer,
            "resourceLocator": document.path.as_posix(),
        },
    )

    nodes: dict[str, Node] = {resource_iri: resource}
    edges: set[Edge] = set()
    context: dict[str, Node] = {}

    for topic in extraction.topics:
        topic_iri = mint(spec, "Topic", topic.label_en, scope=scope)
        nodes[topic_iri] = _coined_node(
            spec, "Topic", topic_iri, topic.label_en, topic.label_es
        )
        edges.add(Edge(topic_iri, "WAS_DERIVED_FROM", resource_iri))

        if topic.links_to_ku:
            ku_iri = f"{spec.namespace}{topic.links_to_ku}"
            # Quoted, never written: it belongs to the reference layer.
            context.setdefault(
                ku_iri, Node(iri=ku_iri, labels=spec.labels_for("KnowledgeUnit"))
            )
            edges.add(Edge(topic_iri, "PART_OF", ku_iri))

        for concept in topic.concepts:
            concept_iri = mint(spec, "Concept", concept.label_en, scope=scope)
            nodes[concept_iri] = _coined_node(
                spec, "Concept", concept_iri, concept.label_en, concept.label_es
            )
            edges.add(Edge(concept_iri, "PART_OF", topic_iri))
            edges.add(Edge(concept_iri, "WAS_DERIVED_FROM", resource_iri))

    ordered_nodes = tuple(nodes[k] for k in sorted(nodes))
    ordered_context = tuple(context[k] for k in sorted(context))
    ordered_edges = tuple(sorted(edges, key=lambda e: (e.rel_type, e.source, e.target)))

    return ABox(
        nodes=ordered_nodes,
        context=ordered_context,
        edges=ordered_edges,
        violations=tuple(spec.validate(ordered_nodes, ordered_edges, ordered_context)),
    )


# ---------------------------------------------------------------------------
# Cypher emission
# ---------------------------------------------------------------------------

def _literal(value: str) -> str:
    """Cypher string literal. json.dumps escapes quotes, backslashes and the
    control characters models keep emitting; Cypher reads the same escapes."""
    return json.dumps(value, ensure_ascii=False)


def _row(props: dict[str, str]) -> str:
    inner = ", ".join(f"{k}: {_literal(v)}" for k, v in sorted(props.items()))
    return "{" + inner + "}"


def to_cypher(abox: ABox, document: SourceDocument, spec: Spec) -> str:
    """The write, as a file. Reviewable before it is a change to the database."""
    known = {n.iri: n for n in abox.nodes} | {n.iri: n for n in abox.context}
    coined = {n.iri for n in abox.nodes}

    lines = [
        "// Generated by the ingestion pipeline. Do not edit by hand.",
        f"// source: {document.path.as_posix()}",
        "//",
        "// Coined nodes are MERGEd; backbone nodes are only MATCHed, so this",
        "// file cannot create a reference-layer node even if the extraction",
        "// asked for one. A row whose backbone endpoint does not exist is",
        "// simply not written.",
        "",
    ]

    by_labels: dict[tuple[str, ...], list[Node]] = {}
    for node in abox.nodes:
        by_labels.setdefault(node.labels, []).append(node)

    for labels, group in sorted(by_labels.items()):
        joined = ":".join(labels)
        rows = ",\n  ".join(_row({"iri": n.iri, **n.props}) for n in group)
        lines += [
            f"// {len(group)} x :{joined}",
            f"UNWIND [\n  {rows}\n] AS row",
            f"MERGE (n:{joined} {{iri: row.iri}})",
            "SET n += row;",
            "",
        ]

    by_shape: dict[tuple[str, str, str], list[Edge]] = {}
    for edge in abox.edges:
        source, target = known.get(edge.source), known.get(edge.target)
        if source is None or target is None:
            continue  # a dangling edge is already reported as a violation
        shape = (
            edge.rel_type,
            spec.indexed_label(source.labels),
            spec.indexed_label(target.labels),
        )
        by_shape.setdefault(shape, []).append(edge)

    for (rel_type, label_s, label_t), group in sorted(by_shape.items()):
        rows = ",\n  ".join(
            _row({"source": e.source, "target": e.target}) for e in group
        )
        writes = sum(1 for e in group if e.target in coined)
        note = "" if writes == len(group) else "  // targets the backbone: match only"
        lines += [
            f"// {len(group)} x -[:{rel_type}]->{note}",
            f"UNWIND [\n  {rows}\n] AS row",
            f"MATCH (a:{label_s} {{iri: row.source}})",
            f"MATCH (b:{label_t} {{iri: row.target}})",
            f"MERGE (a)-[:{rel_type}]->(b);",
            "",
        ]

    return "\n".join(lines)
