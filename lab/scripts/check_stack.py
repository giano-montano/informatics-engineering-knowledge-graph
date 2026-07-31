"""Verifica las dos mitades del stack antes de proyectar nada.

1. Que el driver de Python habla con la instancia del laboratorio.
2. Que rdflib parsea los dos TTL y que el censo coincide con lo declarado
   (17 KnowledgeArea, 162 KnowledgeUnit, 1 LearningResource).

Uso: uv run python lab/scripts/check_stack.py
"""

from __future__ import annotations

import sys
from pathlib import Path

from rdflib import OWL, RDF, Graph, Namespace

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from iekg.db import BASE, sesion  # noqa: E402

RAIZ = Path(__file__).resolve().parents[2]
IE = Namespace("http://www.informatics-engineering-kms.org/ontology/informatic-engineering#")

ONTOLOGIA = RAIZ / "ontology" / "ontologia_informatica.ttl"
BACKBONE = RAIZ / "ontology" / "backbone_cs2023.ttl"

ESPERADO = {"KnowledgeArea": 17, "KnowledgeUnit": 162, "LearningResource": 1}


def check_neo4j() -> bool:
    print("=== conexion a Neo4j ===")
    try:
        with sesion() as s:
            fila = s.run(
                "CALL dbms.components() YIELD name, versions, edition "
                "RETURN versions[0] AS version, edition"
            ).single()
            print(f"  servidor      {fila['version']} {fila['edition']}, base '{BASE}'")
            gds = s.run("RETURN gds.version() AS v").single()["v"]
            print(f"  GDS           {gds}")
            n = s.run("MATCH (n) RETURN count(n) AS n").single()["n"]
            print(f"  nodos actuales {n}")
        return True
    except Exception as exc:  # noqa: BLE001
        print(f"  FALLO: {exc}")
        return False


def check_turtle() -> bool:
    print("\n=== parseo de Turtle con rdflib ===")
    ok = True

    onto = Graph().parse(ONTOLOGIA, format="turtle")
    clases = set(onto.subjects(RDF.type, OWL.Class))
    props = set(onto.subjects(RDF.type, OWL.ObjectProperty))
    print(f"  ontologia     {len(onto)} triples, {len(clases)} clases, "
          f"{len(props)} propiedades de objeto")

    bb = Graph().parse(BACKBONE, format="turtle")
    print(f"  backbone      {len(bb)} triples")

    for clase, esperado in ESPERADO.items():
        hallado = len(set(bb.subjects(RDF.type, IE[clase])))
        marca = "OK" if hallado == esperado else "DISCREPANCIA"
        if hallado != esperado:
            ok = False
        print(f"  {marca:<13} {clase}: {hallado} (esperado {esperado})")

    # La relacion jerarquica que el backbone si materializa.
    aristas = len(set(bb.subject_objects(IE.knowledgeUnitInKnowledgeArea)))
    print(f"  {'OK' if aristas == 162 else 'DISCREPANCIA':<13} "
          f"knowledgeUnitInKnowledgeArea: {aristas} (esperado 162)")
    if aristas != 162:
        ok = False

    return ok


if __name__ == "__main__":
    a = check_neo4j()
    b = check_turtle()
    print("\n" + ("Stack verificado." if a and b else "Hay fallos, revisar arriba."))
    sys.exit(0 if a and b else 1)
