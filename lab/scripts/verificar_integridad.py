"""Compila las reglas a Cypher y ejecuta las consultas de integridad.

La compilacion y la ejecucion son pasos separados a proposito: los .cypher
quedan escritos en build/ para leerlos, versionarlos y citarlos, y solo
despues se ejecutan.

Uso: uv run python lab/scripts/verificar_integridad.py [--solo-emitir]
"""

from __future__ import annotations

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "src"))

from iekg import integridad, reglas  # noqa: E402
from iekg.db import sesion  # noqa: E402

DESTINO = RAIZ / "build"


def main() -> int:
    espec = reglas.cargar()
    escritos = integridad.escribir_artefactos(espec, DESTINO)

    print(f"=== artefactos emitidos en {DESTINO.relative_to(RAIZ)} ===")
    for ruta in escritos:
        print(f"  {ruta.relative_to(RAIZ)}")

    if "--solo-emitir" in sys.argv:
        return 0

    consultas = integridad.compilar(espec)
    print(f"\n=== ejecutando {len(consultas)} consultas de integridad ===")

    total = 0
    with sesion() as s:
        for regla_id, cypher in consultas:
            # Cypher admite comentarios //, asi que la cabecera se deja tal
            # cual; solo estorba el punto y coma final.
            filas = list(s.run(cypher.rstrip().rstrip(";")))
            if filas:
                total += len(filas)
                print(f"  VIOLA    {regla_id}: {len(filas)} casos")
                for f in filas[:5]:
                    print(f"             {f['entidad']} -- {f['detalle']}")
            else:
                print(f"  OK       {regla_id}")

    print(f"\n{'Integridad satisfecha.' if total == 0 else f'{total} violaciones.'}")
    return 0 if total == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
