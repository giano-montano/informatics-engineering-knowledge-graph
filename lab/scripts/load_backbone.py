"""Project the CS2023 backbone into Neo4j and verify the counts.

Runs the projection TWICE on purpose: if MERGE is idempotent, the second
pass must not change any count. That is the proof, not a claim in a README.

Usage: uv run python lab/scripts/load_backbone.py [--reset]
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from iekg import rules  # noqa: E402
from iekg.db import session  # noqa: E402
from iekg.projector import ValidationError, project  # noqa: E402

BACKBONE = ROOT / "ontology" / "backbone_cs2023.ttl"

EXPECTED_NODES = {
    "KnowledgeArea": 17,
    "KnowledgeUnit": 162,
    "LearningResource": 1,
    "KnowledgeElement": 179,
}
EXPECTED_EDGES = {"PART_OF": 162, "WAS_DERIVED_FROM": 179}


def census(s) -> tuple[dict[str, int], dict[str, int]]:
    nodes = {
        row["label"]: row["n"]
        for row in s.run(
            "MATCH (n) UNWIND labels(n) AS label "
            "RETURN label, count(*) AS n ORDER BY label"
        )
    }
    edges = {
        row["type"]: row["n"]
        for row in s.run(
            "MATCH ()-[r]->() RETURN type(r) AS type, count(*) AS n ORDER BY type"
        )
    }
    return nodes, edges


def main() -> int:
    spec = rules.load()
    print(f"Spec v{spec.version}: {len(spec.rules)} rules, "
          f"{len(spec.classes)} mapped classes")

    with session() as s:
        if "--reset" in sys.argv:
            s.run("MATCH (n) DETACH DELETE n")
            print("Database emptied.")

        try:
            first = project(s, BACKBONE, spec)
        except ValidationError as exc:
            print(f"\nPre-write validation failed with {len(exc.violations)} violations:")
            for v in exc.violations[:20]:
                print(f"  {v}")
            return 1

        print(f"\nPass 1  read {first['read']}  written {first['written']}")
        print(f"        constraints: {len(first['constraints'])}")
        nodes_1, edges_1 = census(s)

        second = project(s, BACKBONE, spec)
        print(f"Pass 2  read {second['read']}  written {second['written']}")
        nodes_2, edges_2 = census(s)

        print("\n=== counts in the database ===")
        ok = True
        for label, expected in EXPECTED_NODES.items():
            found = nodes_1.get(label, 0)
            ok &= found == expected
            print(f"  {'OK' if found == expected else 'MISMATCH':<10} "
                  f":{label} = {found} (expected {expected})")
        for rel_type, expected in EXPECTED_EDGES.items():
            found = edges_1.get(rel_type, 0)
            ok &= found == expected
            print(f"  {'OK' if found == expected else 'MISMATCH':<10} "
                  f"-[:{rel_type}]-> = {found} (expected {expected})")

        print("\n=== idempotency (pass 1 vs pass 2) ===")
        if nodes_1 == nodes_2 and edges_1 == edges_2:
            print("  OK         the second pass changed nothing")
        else:
            ok = False
            print(f"  MISMATCH   nodes {nodes_1} -> {nodes_2}")
            print(f"             edges {edges_1} -> {edges_2}")

    print("\n" + ("Backbone projected and verified." if ok else "There are mismatches."))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
