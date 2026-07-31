"""Ontology -> LPG projection, hand-written (no neosemantics).

Reads Turtle with rdflib, turns it into nodes and edges according to the
mapping declared in schema/schema_rules.yaml, validates BEFORE writing, and
writes with idempotent MERGE: running it twice leaves the same state as once.
"""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

from rdflib import RDF, Graph, Literal, URIRef

from iekg.rules import Edge, Node, Spec, Violation

ROOT = Path(__file__).resolve().parents[2]


class ValidationError(RuntimeError):
    def __init__(self, violations: list[Violation]) -> None:
        self.violations = violations
        super().__init__(f"{len(violations)} violations before writing")


# ---------------------------------------------------------------------------
# RDF -> in-memory structures
# ---------------------------------------------------------------------------

def read_turtle(path: Path, spec: Spec) -> tuple[list[Node], list[Edge]]:
    g = Graph().parse(path, format="turtle")
    ns = spec.namespace

    def local(u: URIRef) -> str:
        return str(u).removeprefix(ns)

    # -- nodes: one individual per subject with a mapped class --------------
    labels_by_iri: dict[str, set[str]] = defaultdict(set)
    for subject, _, obj in g.triples((None, RDF.type, None)):
        if not isinstance(subject, URIRef) or not isinstance(obj, URIRef):
            continue
        labels = spec.labels_for(local(obj))
        if labels:
            labels_by_iri[str(subject)].update(labels)

    # -- data properties ----------------------------------------------------
    props_by_iri: dict[str, dict[str, Any]] = defaultdict(dict)
    for iri in labels_by_iri:
        for pred, obj in g.predicate_objects(URIRef(iri)):
            name = spec.data_properties.get(str(pred))
            if name and isinstance(obj, Literal):
                props_by_iri[iri][name] = str(obj)

    nodes = [
        Node(iri=iri, labels=tuple(sorted(labels)), props=props_by_iri.get(iri, {}))
        for iri, labels in sorted(labels_by_iri.items())
    ]

    # -- edges: only mapped object properties -------------------------------
    edges: list[Edge] = []
    for prop, cfg in spec.object_properties.items():
        pred = URIRef(ns + prop)
        for subject, obj in g.subject_objects(pred):
            if isinstance(subject, URIRef) and isinstance(obj, URIRef):
                edges.append(Edge(str(subject), cfg["type"], str(obj)))

    # Inverses are NOT stored as such: writing them would duplicate the fact.
    # If the Turtle asserts one, it is normalised to the canonical direction.
    for prop, cfg in spec.inverses.items():
        pred = URIRef(ns + prop)
        for subject, obj in g.subject_objects(pred):
            if isinstance(subject, URIRef) and isinstance(obj, URIRef):
                edges.append(Edge(str(obj), cfg["of"], str(subject)))

    # Deduplicate: the same fact may arrive via a property and its inverse.
    edges = sorted(set(edges), key=lambda e: (e.rel_type, e.source, e.target))
    return nodes, edges


# ---------------------------------------------------------------------------
# Idempotent writing
# ---------------------------------------------------------------------------

def apply_constraints(session, spec: Spec) -> list[str]:
    """Create the native constraints. Uniqueness only: see findings/0001."""
    applied = []
    for rule in spec.rules_of_type("unique_key"):
        if "native" not in rule.get("enforcement", []):
            continue
        prop = rule["property"]
        for label in rule["labels"]:
            name = f"{rule['id'].replace('-', '_')}_{label}"
            session.run(
                f"CREATE CONSTRAINT {name} IF NOT EXISTS "
                f"FOR (n:{label}) REQUIRE n.{prop} IS UNIQUE"
            )
            applied.append(name)
    return applied


def write(session, nodes: Iterable[Node], edges: Iterable[Edge],
          spec: Spec) -> dict[str, int]:
    known = spec.known_labels()

    # Group by label set so each MERGE is typed: an unlabeled MERGE would
    # scan the whole database.
    by_labels: dict[tuple[str, ...], list[dict]] = defaultdict(list)
    for n in nodes:
        unknown = set(n.labels) - known
        if unknown:
            raise ValueError(f"label not declared in the mapping: {unknown}")
        by_labels[n.labels].append({"iri": n.iri, "props": n.props})

    written = 0
    for labels, rows in by_labels.items():
        joined = ":".join(labels)
        result = session.run(
            f"UNWIND $rows AS r "
            f"MERGE (x:{joined} {{iri: r.iri}}) "
            f"SET x += r.props "
            f"RETURN count(x) AS n",
            rows=rows,
        ).single()
        written += result["n"]

    # Group edges by (type, indexed label of each endpoint) so the MATCH uses
    # the uniqueness constraint's index instead of scanning.
    indexed = {n.iri: spec.indexed_label(n.labels) for n in nodes}
    by_shape: dict[tuple[str, str, str], list[dict]] = defaultdict(list)
    for e in edges:
        by_shape[(e.rel_type, indexed[e.source], indexed[e.target])].append(
            {"source": e.source, "target": e.target}
        )

    edges_written = 0
    for (rel_type, label_s, label_t), rows in by_shape.items():
        result = session.run(
            f"UNWIND $rows AS r "
            f"MATCH (a:{label_s} {{iri: r.source}}) "
            f"MATCH (b:{label_t} {{iri: r.target}}) "
            f"MERGE (a)-[rel:{rel_type}]->(b) "
            f"RETURN count(rel) AS n",
            rows=rows,
        ).single()
        edges_written += result["n"]

    return {"nodes": written, "edges": edges_written}


def project(session, turtle_path: Path, spec: Spec, *,
            validate: bool = True) -> dict[str, Any]:
    nodes, edges = read_turtle(turtle_path, spec)

    if validate:
        violations = spec.validate(nodes, edges)
        if violations:
            raise ValidationError(violations)

    constraints = apply_constraints(session, spec)
    counts = write(session, nodes, edges, spec)
    return {
        "read": {"nodes": len(nodes), "edges": len(edges)},
        "written": counts,
        "constraints": constraints,
    }
