"""Interpreter for the declarative schema rules file.

Reads schema/schema_rules.yaml and compiles it to pre-write validators. The
other half of the interpreter -emitting constraint DDL and integrity queries-
lives in integrity.py.

Deliberately NOT an ORM: it does not map classes to objects nor manage
sessions. It only turns a specification into checks.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Iterator

import yaml

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PATH = ROOT / "schema" / "schema_rules.yaml"


@dataclass(frozen=True)
class Node:
    iri: str
    labels: tuple[str, ...]
    props: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Edge:
    source: str
    rel_type: str
    target: str


@dataclass(frozen=True)
class Violation:
    rule: str
    entity: str
    detail: str

    def __str__(self) -> str:
        return f"[{self.rule}] {self.entity}: {self.detail}"


class Spec:
    """The loaded specification, with its validators."""

    def __init__(self, data: dict[str, Any]) -> None:
        self.version: int = data["version"]
        self.namespace: str = data["namespace"]
        self.classes: dict[str, list[str]] = data["classes"]
        self.object_properties: dict[str, dict] = data.get("object_properties", {})
        self.inverses: dict[str, dict] = data.get("inverses", {})
        self.transitive: list[str] = data.get("transitive", [])
        self.data_properties: dict[str, str] = data.get("data_properties", {})
        self.coined: dict[str, Any] = data.get("coined", {})
        self.rules: list[dict] = data.get("rules", [])

    # -- what the pipeline is allowed to write ------------------------------

    def coined_property(self, role: str) -> str:
        """Node property name for a role the pipeline writes (`canonical_label`...)."""
        try:
            return self.coined["properties"][role]
        except KeyError:
            raise ValueError(f"no coined property declared for role {role!r}") from None

    def iri_prefix(self, owl_class: str) -> str:
        try:
            return self.coined["iri_prefixes"][owl_class]
        except KeyError:
            raise ValueError(f"{owl_class} has no IRI prefix; it cannot be coined") from None

    @property
    def institutional_layer(self) -> str:
        return self.coined["layer_value"]

    # -- mapping lookups ----------------------------------------------------

    def labels_for(self, owl_class: str) -> tuple[str, ...] | None:
        v = self.classes.get(owl_class)
        return tuple(v) if v else None

    def data_property(self, predicate: str, language: str | None) -> str | None:
        """Node property for a literal, most specific first.

        `prefLabel@es` beats `prefLabel`. Without the language in the key, two
        SKOS literals of one property collapse onto one node property and the
        surviving one is whichever rdflib yielded last.
        """
        if language:
            tagged = self.data_properties.get(f"{predicate}@{language}")
            if tagged:
                return tagged
        return self.data_properties.get(predicate)

    def relationship_for(self, owl_property: str) -> str | None:
        d = self.object_properties.get(owl_property)
        return d["type"] if d else None

    def known_labels(self) -> set[str]:
        return {label for labels in self.classes.values() for label in labels}

    def indexed_labels(self) -> set[str]:
        """Labels with a uniqueness constraint, i.e. backed by an index."""
        return {
            label
            for r in self.rules_of_type("unique_key")
            if "native" in r.get("enforcement", [])
            for label in r["labels"]
        }

    def indexed_label(self, labels: tuple[str, ...]) -> str:
        """The label of this node usable for an index-backed lookup."""
        candidates = self.indexed_labels() & set(labels)
        if not candidates:
            raise ValueError(
                f"none of {sorted(labels)} has a uniqueness constraint; "
                f"the MATCH would scan the whole database"
            )
        return sorted(candidates)[0]

    def rules_of_type(self, rule_type: str) -> list[dict]:
        return [r for r in self.rules if r["type"] == rule_type]

    # -- pre-write validation -----------------------------------------------

    def validate(self, nodes: Iterable[Node], edges: Iterable[Edge],
                 context: Iterable[Node] = ()) -> list[Violation]:
        """Check `nodes` and `edges`; `context` only types edge endpoints.

        The ingestion pipeline writes institutional nodes that point at
        backbone nodes it must not touch. Those endpoints have to be known
        -otherwise every PART_OF looks like it lands nowhere- but they must not
        be judged: a KnowledgeUnit quoted without its KnowledgeArea edge is not
        an orphan, it is simply not the subject of this write.
        """
        nodes = list(nodes)
        edges = list(edges)
        by_iri = {n.iri: n for n in list(context)} | {n.iri: n for n in nodes}

        found: list[Violation] = []
        for rule in self.rules:
            if "pre_write" not in rule.get("enforcement", []):
                continue
            kind = rule["type"]
            if kind == "disjoint_labels":
                found += list(_disjoint_labels(rule, nodes))
            elif kind == "functional_relationship":
                found += list(_functional(rule, nodes, edges, by_iri))
            elif kind == "existential_relationship":
                found += list(_existential(rule, nodes, edges, by_iri))
            elif kind == "domain_range":
                found += list(_domain_range(rule, edges, by_iri))
        return found


# -- one validator per rule type --------------------------------------------


def _disjoint_labels(rule: dict, nodes: list[Node]) -> Iterator[Violation]:
    candidates = set(rule["labels"])
    within = rule.get("within")
    exact = rule.get("cardinality") == "exactly_one"

    for n in nodes:
        if within and within not in n.labels:
            continue
        found = candidates & set(n.labels)
        if len(found) > 1:
            yield Violation(rule["id"], n.iri,
                            f"has {len(found)} disjoint labels: {sorted(found)}")
        elif exact and not found:
            yield Violation(rule["id"], n.iri,
                            f"has none of {sorted(candidates)}")


def _functional(rule: dict, nodes: list[Node], edges: list[Edge],
                by_iri: dict[str, Node]) -> Iterator[Violation]:
    rel_type, from_label, to_label = rule["relationship"], rule["from"], rule["to"]
    exact = rule.get("cardinality") == "exactly_one"

    counts: dict[str, int] = {n.iri: 0 for n in nodes if from_label in n.labels}
    for e in edges:
        if e.rel_type != rel_type or e.source not in counts:
            continue
        target = by_iri.get(e.target)
        if target and to_label in target.labels:
            counts[e.source] += 1

    for iri, n in counts.items():
        if n > 1:
            yield Violation(rule["id"], iri, f"points to {n} {to_label}, must be 1")
        elif exact and n == 0:
            yield Violation(rule["id"], iri, f"points to no {to_label}")


def _existential(rule: dict, nodes: list[Node], edges: list[Edge],
                 by_iri: dict[str, Node]) -> Iterator[Violation]:
    """owl:someValuesFrom: at least one target of the right type.

    Separate from _functional because the two axioms bound opposite ends. A
    node with three anchors satisfies this and violates that.
    """
    rel_type, from_label, to_label = rule["relationship"], rule["from"], rule["to"]

    anchored = {
        e.source
        for e in edges
        if e.rel_type == rel_type
        and (target := by_iri.get(e.target)) is not None
        and to_label in target.labels
    }
    for n in nodes:
        if from_label in n.labels and n.iri not in anchored:
            yield Violation(rule["id"], n.iri,
                            f"is not part of any {to_label} via {rel_type}")


def _domain_range(rule: dict, edges: list[Edge],
                  by_iri: dict[str, Node]) -> Iterator[Violation]:
    rel_type = rule["relationship"]
    pairs = rule.get("allowed_pairs")
    domain = set(rule.get("domain", []))
    rng = set(rule.get("range", []))

    for e in edges:
        if e.rel_type != rel_type:
            continue
        source, target = by_iri.get(e.source), by_iri.get(e.target)
        if source is None or target is None:
            missing = e.source if source is None else e.target
            yield Violation(rule["id"], missing, "edge endpoint does not exist")
            continue

        ls_s, ls_t = set(source.labels), set(target.labels)
        if pairs:
            if not any(p[0] in ls_s and p[1] in ls_t for p in pairs):
                yield Violation(rule["id"], f"{e.source} -> {e.target}",
                                f"pair not allowed: {sorted(ls_s)} -> {sorted(ls_t)}")
        else:
            if domain and not (domain & ls_s):
                yield Violation(rule["id"], e.source,
                                f"outside domain {sorted(domain)}: {sorted(ls_s)}")
            if rng and not (rng & ls_t):
                yield Violation(rule["id"], e.target,
                                f"outside range {sorted(rng)}: {sorted(ls_t)}")


def load(path: Path | None = None) -> Spec:
    path = path or DEFAULT_PATH
    with path.open(encoding="utf-8") as fh:
        return Spec(yaml.safe_load(fh))
