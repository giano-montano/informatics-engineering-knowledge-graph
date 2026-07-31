"""Verify both halves of the stack before projecting anything.

1. That the Python driver talks to the lab instance.
2. That rdflib parses both Turtle files and the census matches what is
   declared (17 KnowledgeArea, 162 KnowledgeUnit, 1 LearningResource).

Usage: uv run python lab/scripts/check_stack.py
"""

from __future__ import annotations

import sys
from pathlib import Path

from rdflib import OWL, RDF, Graph, Namespace

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from iekg.db import DATABASE, session  # noqa: E402

IE = Namespace("http://www.informatics-engineering-kms.org/ontology/informatic-engineering#")

ONTOLOGY = ROOT / "ontology" / "ontologia_informatica.ttl"
BACKBONE = ROOT / "ontology" / "backbone_cs2023.ttl"

EXPECTED = {"KnowledgeArea": 17, "KnowledgeUnit": 162, "LearningResource": 1}


def check_neo4j() -> bool:
    print("=== Neo4j connection ===")
    try:
        with session() as s:
            row = s.run(
                "CALL dbms.components() YIELD name, versions, edition "
                "RETURN versions[0] AS version, edition"
            ).single()
            print(f"  server        {row['version']} {row['edition']}, database '{DATABASE}'")
            gds = s.run("RETURN gds.version() AS v").single()["v"]
            print(f"  GDS           {gds}")
            n = s.run("MATCH (n) RETURN count(n) AS n").single()["n"]
            print(f"  current nodes {n}")
        return True
    except Exception as exc:  # noqa: BLE001
        print(f"  FAILED: {exc}")
        return False


def check_turtle() -> bool:
    print("\n=== Turtle parsing with rdflib ===")
    ok = True

    onto = Graph().parse(ONTOLOGY, format="turtle")
    classes = set(onto.subjects(RDF.type, OWL.Class))
    props = set(onto.subjects(RDF.type, OWL.ObjectProperty))
    print(f"  ontology      {len(onto)} triples, {len(classes)} classes, "
          f"{len(props)} object properties")

    bb = Graph().parse(BACKBONE, format="turtle")
    print(f"  backbone      {len(bb)} triples")

    for cls, expected in EXPECTED.items():
        found = len(set(bb.subjects(RDF.type, IE[cls])))
        ok &= found == expected
        print(f"  {'OK' if found == expected else 'MISMATCH':<13} "
              f"{cls}: {found} (expected {expected})")

    # The hierarchical relation the backbone does materialise.
    edges = len(set(bb.subject_objects(IE.knowledgeUnitInKnowledgeArea)))
    ok &= edges == 162
    print(f"  {'OK' if edges == 162 else 'MISMATCH':<13} "
          f"knowledgeUnitInKnowledgeArea: {edges} (expected 162)")

    return ok


if __name__ == "__main__":
    a = check_neo4j()
    b = check_turtle()
    print("\n" + ("Stack verified." if a and b else "There are failures, see above."))
    sys.exit(0 if a and b else 1)
