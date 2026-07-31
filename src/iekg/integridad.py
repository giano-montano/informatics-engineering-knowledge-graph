"""Segundo backend del interprete: reglas -> Cypher.

Compila schema/reglas_esquema.yaml a artefactos .cypher legibles y
versionables. NO ejecuta nada: escribe archivos. Ejecutarlos es un paso
aparte y explicito.

Toda consulta emitida devuelve la misma forma -(regla, entidad, detalle)-
para que el ejecutor las trate de manera uniforme. Una consulta que devuelve
cero filas es una regla satisfecha.
"""

from __future__ import annotations

import re
from pathlib import Path

from iekg.reglas import Espec

IDENTIFICADOR = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _seguro(nombre: str, conocidos: set[str] | None = None) -> str:
    """Las etiquetas y tipos van interpolados en el Cypher, no parametrizados
    (Cypher no admite parametros ahi). Se validan contra la especificacion."""
    if not IDENTIFICADOR.match(nombre):
        raise ValueError(f"identificador no valido para Cypher: {nombre!r}")
    if conocidos is not None and nombre not in conocidos:
        raise ValueError(f"{nombre!r} no esta declarado en el mapeo de clases")
    return nombre


def _unir(expresion_lista: str) -> str:
    """Cypher 5 no tiene funcion nativa de lista a cadena y toString() no
    acepta listas. Se usa reduce para no depender de APOC en lo emitido."""
    return (
        f"reduce(acc = '', x IN {expresion_lista} | "
        f"acc + CASE WHEN acc = '' THEN '' ELSE ', ' END + x)"
    )


def _cabecera(regla: dict) -> str:
    lineas = [f"// regla: {regla['id']}  ({regla['type']})"]
    if regla.get("origen_owl"):
        lineas.append(f"// origen: {regla['origen_owl']}")
    return "\n".join(lineas)


# ---------------------------------------------------------------------------
# Un compilador por tipo de regla
# ---------------------------------------------------------------------------

def _c_clave_unica(regla: dict, espec: Espec) -> str:
    prop = _seguro(regla["propiedad"])
    bloques = []
    for label in regla["labels"]:
        lab = _seguro(label, espec.etiquetas_conocidas())
        bloques.append(
            f"MATCH (n:{lab})\n"
            f"WITH n.{prop} AS clave, count(*) AS repeticiones\n"
            f"WHERE clave IS NULL OR repeticiones > 1\n"
            f"RETURN '{regla['id']}' AS regla, "
            f"coalesce(toString(clave), '<null>') AS entidad, "
            f"':{lab} con {prop} nulo o repetido ' + toString(repeticiones) AS detalle"
        )
    return "\nUNION\n".join(bloques) + ";"


def _c_etiquetas_disjuntas(regla: dict, espec: Espec) -> str:
    conocidas = espec.etiquetas_conocidas()
    candidatas = [_seguro(l, conocidas) for l in regla["labels"]]
    lista = "[" + ", ".join(f"'{l}'" for l in candidatas) + "]"
    # Version sin comillas: la lista va tambien dentro de un literal de
    # cadena en el mensaje, y las comillas simples lo romperian.
    lista_texto = ", ".join(candidatas)
    exacta = regla.get("cardinalidad") == "exactamente_una"

    if regla.get("dentro_de"):
        ancla = f":{_seguro(regla['dentro_de'], conocidas)}"
    else:
        ancla = ""

    comparacion = "<> 1" if exacta else "> 1"
    explicacion = ("debe tener exactamente una" if exacta
                   else "debe tener a lo sumo una")

    return (
        f"MATCH (n{ancla})\n"
        f"WITH n, [l IN labels(n) WHERE l IN {lista}] AS halladas\n"
        f"WHERE size(halladas) {comparacion}\n"
        f"RETURN '{regla['id']}' AS regla, "
        f"coalesce(n.iri, '<sin iri>') AS entidad, "
        f"'{explicacion} de ({lista_texto}), tiene: ' + {_unir('halladas')} AS detalle;"
    )


def _c_relacion_funcional(regla: dict, espec: Espec) -> str:
    conocidas = espec.etiquetas_conocidas()
    tipo = _seguro(regla["relationship"])
    desde = _seguro(regla["from"], conocidas)
    hasta = _seguro(regla["to"], conocidas)
    exacta = regla.get("cardinalidad") == "exactamente_una"
    comparacion = "<> 1" if exacta else "> 1"

    return (
        f"MATCH (a:{desde})\n"
        f"OPTIONAL MATCH (a)-[:{tipo}]->(b:{hasta})\n"
        f"WITH a, count(DISTINCT b) AS destinos\n"
        f"WHERE destinos {comparacion}\n"
        f"RETURN '{regla['id']}' AS regla, "
        f"coalesce(a.iri, '<sin iri>') AS entidad, "
        f"'apunta a ' + toString(destinos) + ' :{hasta} via {tipo}' AS detalle;"
    )


def _c_dominio_rango(regla: dict, espec: Espec) -> str:
    conocidas = espec.etiquetas_conocidas()
    tipo = _seguro(regla["relationship"])

    if regla.get("pares_permitidos"):
        alternativas = " OR ".join(
            f"(a:{_seguro(o, conocidas)} AND b:{_seguro(d, conocidas)})"
            for o, d in regla["pares_permitidos"]
        )
        condicion = f"NOT ({alternativas})"
    else:
        partes = []
        if regla.get("domain"):
            dom = " OR ".join(f"a:{_seguro(l, conocidas)}" for l in regla["domain"])
            partes.append(f"NOT ({dom})")
        if regla.get("range"):
            ran = " OR ".join(f"b:{_seguro(l, conocidas)}" for l in regla["range"])
            partes.append(f"NOT ({ran})")
        condicion = " OR ".join(partes)

    return (
        f"MATCH (a)-[:{tipo}]->(b)\n"
        f"WHERE {condicion}\n"
        f"RETURN '{regla['id']}' AS regla, "
        f"coalesce(a.iri, '<sin iri>') + ' -> ' + coalesce(b.iri, '<sin iri>') AS entidad, "
        f"'{tipo} entre (' + {_unir('labels(a)')} + ') y (' "
        f"+ {_unir('labels(b)')} + ')' AS detalle;"
    )


def _c_aciclicidad(regla: dict, espec: Espec) -> str:
    tipo = _seguro(regla["relationship"])
    prof = int(regla.get("profundidad_maxima", 10))
    # La unicidad de relaciones de Cypher garantiza terminacion; la cota
    # explicita evita ademas recorridos inutiles en grafos grandes.
    return (
        f"MATCH ciclo = (n)-[:{tipo}*1..{prof}]->(n)\n"
        f"RETURN '{regla['id']}' AS regla, "
        f"coalesce(n.iri, '<sin iri>') AS entidad, "
        f"'ciclo de {tipo} de longitud ' + toString(length(ciclo)) AS detalle\n"
        f"LIMIT 25;"
    )


_COMPILADORES = {
    "clave_unica": _c_clave_unica,
    "etiquetas_disjuntas": _c_etiquetas_disjuntas,
    "relacion_funcional": _c_relacion_funcional,
    "dominio_rango": _c_dominio_rango,
    "aciclicidad": _c_aciclicidad,
}


# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------

def compilar(espec: Espec) -> list[tuple[str, str]]:
    """Devuelve [(id_de_regla, cypher)] para las reglas con consulta de integridad."""
    salida = []
    for regla in espec.reglas:
        if "consulta_integridad" not in regla.get("enforcement", []):
            continue
        compilador = _COMPILADORES.get(regla["type"])
        if compilador is None:
            raise ValueError(f"tipo de regla sin compilador: {regla['type']}")
        salida.append((regla["id"], f"{_cabecera(regla)}\n{compilador(regla, espec)}"))
    return salida


def compilar_restricciones(espec: Espec) -> str:
    """DDL de las restricciones nativas. Solo unicidad: ver findings/0001."""
    lineas = ["// Restricciones nativas. Unicidad es la unica portable a",
              "// Community Edition; ver lab/findings/0001.", ""]
    for regla in espec.reglas_de_tipo("clave_unica"):
        if "nativa" not in regla.get("enforcement", []):
            continue
        prop = _seguro(regla["propiedad"])
        for label in regla["labels"]:
            lab = _seguro(label, espec.etiquetas_conocidas())
            nombre = f"{regla['id'].replace('-', '_')}_{lab}"
            lineas.append(
                f"CREATE CONSTRAINT {nombre} IF NOT EXISTS\n"
                f"FOR (n:{lab}) REQUIRE n.{prop} IS UNIQUE;"
            )
    return "\n".join(lineas) + "\n"


def escribir_artefactos(espec: Espec, destino: Path) -> list[Path]:
    destino.mkdir(parents=True, exist_ok=True)
    (destino / "integridad").mkdir(exist_ok=True)

    escritos = [destino / "restricciones.cypher"]
    escritos[0].write_text(compilar_restricciones(espec), encoding="utf-8")

    for regla_id, cypher in compilar(espec):
        ruta = destino / "integridad" / f"{regla_id}.cypher"
        ruta.write_text(cypher + "\n", encoding="utf-8")
        escritos.append(ruta)
    return escritos
