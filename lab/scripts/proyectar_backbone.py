"""Proyecta el backbone CS2023 a Neo4j y verifica conteos.

Corre la proyeccion DOS VECES a proposito: si el MERGE es idempotente, la
segunda pasada no debe cambiar ningun conteo. Esa es la prueba, no una
afirmacion del README.

Uso: uv run python lab/scripts/proyectar_backbone.py [--limpiar]
"""

from __future__ import annotations

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "src"))

from iekg import reglas  # noqa: E402
from iekg.db import sesion  # noqa: E402
from iekg.proyector import ErrorDeValidacion, proyectar  # noqa: E402

BACKBONE = RAIZ / "ontology" / "backbone_cs2023.ttl"

ESPERADO = {
    "KnowledgeArea": 17,
    "KnowledgeUnit": 162,
    "LearningResource": 1,
    "KnowledgeElement": 179,
}
ESPERADO_ARISTAS = {"PART_OF": 162, "WAS_DERIVED_FROM": 179}


def censo(s) -> tuple[dict[str, int], dict[str, int]]:
    nodos = {
        f["label"]: f["n"]
        for f in s.run(
            "MATCH (n) UNWIND labels(n) AS label "
            "RETURN label, count(*) AS n ORDER BY label"
        )
    }
    rels = {
        f["tipo"]: f["n"]
        for f in s.run(
            "MATCH ()-[r]->() RETURN type(r) AS tipo, count(*) AS n ORDER BY tipo"
        )
    }
    return nodos, rels


def main() -> int:
    espec = reglas.cargar()
    print(f"Especificacion v{espec.version}: {len(espec.reglas)} reglas, "
          f"{len(espec.clases)} clases mapeadas")

    with sesion() as s:
        if "--limpiar" in sys.argv:
            s.run("MATCH (n) DETACH DELETE n")
            print("Base vaciada.")

        try:
            r1 = proyectar(s, BACKBONE, espec)
        except ErrorDeValidacion as exc:
            print(f"\nValidacion previa fallo con {len(exc.violaciones)} violaciones:")
            for v in exc.violaciones[:20]:
                print(f"  {v}")
            return 1

        print(f"\nPasada 1  leidos {r1['leidos']}  escritos {r1['escritos']}")
        print(f"          restricciones: {len(r1['restricciones'])}")
        nodos1, rels1 = censo(s)

        r2 = proyectar(s, BACKBONE, espec)
        print(f"Pasada 2  leidos {r2['leidos']}  escritos {r2['escritos']}")
        nodos2, rels2 = censo(s)

        print("\n=== conteos en la base ===")
        ok = True
        for label, esperado in ESPERADO.items():
            hallado = nodos1.get(label, 0)
            marca = "OK" if hallado == esperado else "DISCREPANCIA"
            ok &= hallado == esperado
            print(f"  {marca:<13} :{label} = {hallado} (esperado {esperado})")
        for tipo, esperado in ESPERADO_ARISTAS.items():
            hallado = rels1.get(tipo, 0)
            marca = "OK" if hallado == esperado else "DISCREPANCIA"
            ok &= hallado == esperado
            print(f"  {marca:<13} -[:{tipo}]-> = {hallado} (esperado {esperado})")

        print("\n=== idempotencia (pasada 1 vs pasada 2) ===")
        if nodos1 == nodos2 and rels1 == rels2:
            print("  OK            la segunda pasada no cambio nada")
        else:
            ok = False
            print(f"  DISCREPANCIA  nodos {nodos1} -> {nodos2}")
            print(f"                rels  {rels1} -> {rels2}")

    print("\n" + ("Backbone proyectado y verificado." if ok else "Hay discrepancias."))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
