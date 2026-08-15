"""Second interpreter backend: rules -> Cypher.

Compiles schema/schema_rules.yaml into readable, versionable .cypher
artifacts. It does NOT execute anything: it writes files. Running them is a
separate, explicit step.

Every emitted query returns the same shape -(rule, entity, detail)- so the
runner can treat them uniformly. A query returning zero rows means the rule
is satisfied.
"""

from __future__ import annotations

import re
from pathlib import Path

from iekg.rules import Spec

IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _safe_ident(name: str, known: set[str] | None = None) -> str:
    """Labels and relationship types are interpolated into Cypher, not
    parameterised (Cypher has no parameters there). Validate against the spec."""
    if not IDENTIFIER.match(name):
        raise ValueError(f"invalid Cypher identifier: {name!r}")
    if known is not None and name not in known:
        raise ValueError(f"{name!r} is not declared in the class mapping")
    return name


def _join_list(list_expr: str) -> str:
    """Cypher 5 has no native list-to-string and toString() rejects lists.
    reduce() keeps the emitted Cypher free of any APOC dependency."""
    return (
        f"reduce(acc = '', x IN {list_expr} | "
        f"acc + CASE WHEN acc = '' THEN '' ELSE ', ' END + x)"
    )


def _header(rule: dict) -> str:
    lines = [f"// rule: {rule['id']}  ({rule['type']})"]
    if rule.get("owl_source"):
        lines.append(f"// source: {rule['owl_source']}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# One compiler per rule type
# ---------------------------------------------------------------------------

def _c_unique_key(rule: dict, spec: Spec) -> str:
    prop = _safe_ident(rule["property"])
    blocks = []
    for label in rule["labels"]:
        lab = _safe_ident(label, spec.known_labels())
        blocks.append(
            f"MATCH (n:{lab})\n"
            f"WITH n.{prop} AS key, count(*) AS occurrences\n"
            f"WHERE key IS NULL OR occurrences > 1\n"
            f"RETURN '{rule['id']}' AS rule, "
            f"coalesce(toString(key), '<null>') AS entity, "
            f"':{lab} with null or repeated {prop} ' + toString(occurrences) AS detail"
        )
    return "\nUNION\n".join(blocks) + ";"


def _c_disjoint_labels(rule: dict, spec: Spec) -> str:
    known = spec.known_labels()
    candidates = [_safe_ident(l, known) for l in rule["labels"]]
    cypher_list = "[" + ", ".join(f"'{l}'" for l in candidates) + "]"
    # Unquoted version: the list also goes inside a string literal in the
    # message, where single quotes would break it.
    plain_list = ", ".join(candidates)
    exact = rule.get("cardinality") == "exactly_one"

    anchor = f":{_safe_ident(rule['within'], known)}" if rule.get("within") else ""
    comparison = "<> 1" if exact else "> 1"
    wording = "must have exactly one" if exact else "must have at most one"

    return (
        f"MATCH (n{anchor})\n"
        f"WITH n, [l IN labels(n) WHERE l IN {cypher_list}] AS found\n"
        f"WHERE size(found) {comparison}\n"
        f"RETURN '{rule['id']}' AS rule, "
        f"coalesce(n.iri, '<no iri>') AS entity, "
        f"'{wording} of ({plain_list}), has: ' + {_join_list('found')} AS detail;"
    )


def _c_functional_relationship(rule: dict, spec: Spec) -> str:
    known = spec.known_labels()
    rel_type = _safe_ident(rule["relationship"])
    from_label = _safe_ident(rule["from"], known)
    to_label = _safe_ident(rule["to"], known)
    exact = rule.get("cardinality") == "exactly_one"
    comparison = "<> 1" if exact else "> 1"

    return (
        f"MATCH (a:{from_label})\n"
        f"OPTIONAL MATCH (a)-[:{rel_type}]->(b:{to_label})\n"
        f"WITH a, count(DISTINCT b) AS targets\n"
        f"WHERE targets {comparison}\n"
        f"RETURN '{rule['id']}' AS rule, "
        f"coalesce(a.iri, '<no iri>') AS entity, "
        f"'points to ' + toString(targets) + ' :{to_label} via {rel_type}' AS detail;"
    )


def _c_existential_relationship(rule: dict, spec: Spec) -> str:
    known = spec.known_labels()
    rel_type = _safe_ident(rule["relationship"])
    from_label = _safe_ident(rule["from"], known)
    to_label = _safe_ident(rule["to"], known)

    # A pattern predicate, not OPTIONAL MATCH + count: only existence matters
    # here, and the negated pattern stops at the first hit.
    return (
        f"MATCH (a:{from_label})\n"
        f"WHERE NOT (a)-[:{rel_type}]->(:{to_label})\n"
        f"RETURN '{rule['id']}' AS rule, "
        f"coalesce(a.iri, '<no iri>') AS entity, "
        f"'is not part of any :{to_label} via {rel_type}' AS detail;"
    )


def _c_domain_range(rule: dict, spec: Spec) -> str:
    known = spec.known_labels()
    rel_type = _safe_ident(rule["relationship"])

    if rule.get("allowed_pairs"):
        alternatives = " OR ".join(
            f"(a:{_safe_ident(s, known)} AND b:{_safe_ident(t, known)})"
            for s, t in rule["allowed_pairs"]
        )
        condition = f"NOT ({alternatives})"
    else:
        parts = []
        if rule.get("domain"):
            dom = " OR ".join(f"a:{_safe_ident(l, known)}" for l in rule["domain"])
            parts.append(f"NOT ({dom})")
        if rule.get("range"):
            rng = " OR ".join(f"b:{_safe_ident(l, known)}" for l in rule["range"])
            parts.append(f"NOT ({rng})")
        condition = " OR ".join(parts)

    return (
        f"MATCH (a)-[:{rel_type}]->(b)\n"
        f"WHERE {condition}\n"
        f"RETURN '{rule['id']}' AS rule, "
        f"coalesce(a.iri, '<no iri>') + ' -> ' + coalesce(b.iri, '<no iri>') AS entity, "
        f"'{rel_type} between (' + {_join_list('labels(a)')} + ') and (' "
        f"+ {_join_list('labels(b)')} + ')' AS detail;"
    )


def _c_acyclicity(rule: dict, spec: Spec) -> str:
    rel_type = _safe_ident(rule["relationship"])
    depth = int(rule.get("max_depth", 10))
    # Cypher's relationship uniqueness guarantees termination; the explicit
    # bound additionally avoids pointless traversal on large graphs.
    return (
        f"MATCH cycle = (n)-[:{rel_type}*1..{depth}]->(n)\n"
        f"RETURN '{rule['id']}' AS rule, "
        f"coalesce(n.iri, '<no iri>') AS entity, "
        f"'{rel_type} cycle of length ' + toString(length(cycle)) AS detail\n"
        f"LIMIT 25;"
    )


_COMPILERS = {
    "unique_key": _c_unique_key,
    "disjoint_labels": _c_disjoint_labels,
    "functional_relationship": _c_functional_relationship,
    "existential_relationship": _c_existential_relationship,
    "domain_range": _c_domain_range,
    "acyclicity": _c_acyclicity,
}


# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------

def compile_queries(spec: Spec) -> list[tuple[str, str]]:
    """Return [(rule_id, cypher)] for rules with an integrity query."""
    out = []
    for rule in spec.rules:
        if "integrity_query" not in rule.get("enforcement", []):
            continue
        compiler = _COMPILERS.get(rule["type"])
        if compiler is None:
            raise ValueError(f"rule type without a compiler: {rule['type']}")
        out.append((rule["id"], f"{_header(rule)}\n{compiler(rule, spec)}"))
    return out


def compile_constraints(spec: Spec) -> str:
    """DDL for the native constraints. Uniqueness only: see findings/0001."""
    lines = ["// Native constraints. Uniqueness is the only one portable to",
             "// Community Edition; see lab/findings/0001.", ""]
    for rule in spec.rules_of_type("unique_key"):
        if "native" not in rule.get("enforcement", []):
            continue
        prop = _safe_ident(rule["property"])
        for label in rule["labels"]:
            lab = _safe_ident(label, spec.known_labels())
            name = f"{rule['id'].replace('-', '_')}_{lab}"
            lines.append(
                f"CREATE CONSTRAINT {name} IF NOT EXISTS\n"
                f"FOR (n:{lab}) REQUIRE n.{prop} IS UNIQUE;"
            )
    return "\n".join(lines) + "\n"


def write_artifacts(spec: Spec, target_dir: Path) -> list[Path]:
    target_dir.mkdir(parents=True, exist_ok=True)
    (target_dir / "integrity").mkdir(exist_ok=True)

    written = [target_dir / "constraints.cypher"]
    written[0].write_text(compile_constraints(spec), encoding="utf-8")

    for rule_id, cypher in compile_queries(spec):
        path = target_dir / "integrity" / f"{rule_id}.cypher"
        path.write_text(cypher + "\n", encoding="utf-8")
        written.append(path)
    return written
