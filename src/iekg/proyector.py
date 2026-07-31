"""Proyeccion ontologia -> LPG, por codigo propio (sin neosemantics).

Lee un Turtle con rdflib, lo traduce a nodos y aristas segun el mapeo
declarado en schema/reglas_esquema.yaml, valida ANTES de escribir, y escribe
con MERGE idempotente: correrlo dos veces deja la base igual que correrlo una.
"""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

from rdflib import RDF, Graph, Literal, URIRef

from iekg.reglas import Arista, Espec, Nodo, Violacion

RAIZ = Path(__file__).resolve().parents[2]


class ErrorDeValidacion(RuntimeError):
    def __init__(self, violaciones: list[Violacion]) -> None:
        self.violaciones = violaciones
        super().__init__(f"{len(violaciones)} violaciones antes de escribir")


# ---------------------------------------------------------------------------
# RDF -> estructuras en memoria
# ---------------------------------------------------------------------------

def leer_turtle(ruta: Path, espec: Espec) -> tuple[list[Nodo], list[Arista]]:
    g = Graph().parse(ruta, format="turtle")
    ns = espec.namespace

    def local(u: URIRef) -> str:
        return str(u).removeprefix(ns)

    # -- nodos: un individuo por cada sujeto con una clase mapeada -----------
    labels_por_iri: dict[str, set[str]] = defaultdict(set)
    for sujeto, _, objeto in g.triples((None, RDF.type, None)):
        if not isinstance(sujeto, URIRef) or not isinstance(objeto, URIRef):
            continue
        labels = espec.labels_de(local(objeto))
        if labels:
            labels_por_iri[str(sujeto)].update(labels)

    # -- propiedades de dato -------------------------------------------------
    props_por_iri: dict[str, dict[str, Any]] = defaultdict(dict)
    for iri in labels_por_iri:
        for pred, obj in g.predicate_objects(URIRef(iri)):
            nombre = espec.propiedades_dato.get(str(pred))
            if nombre and isinstance(obj, Literal):
                props_por_iri[iri][nombre] = str(obj)

    nodos = [
        Nodo(iri=iri, labels=tuple(sorted(labels)), props=props_por_iri.get(iri, {}))
        for iri, labels in sorted(labels_por_iri.items())
    ]

    # -- aristas: solo propiedades de objeto mapeadas ------------------------
    aristas: list[Arista] = []
    for propiedad, cfg in espec.propiedades_objeto.items():
        pred = URIRef(ns + propiedad)
        for sujeto, objeto in g.subject_objects(pred):
            if isinstance(sujeto, URIRef) and isinstance(objeto, URIRef):
                aristas.append(Arista(str(sujeto), cfg["tipo"], str(objeto)))

    # Las inversas NO se leen: escribirlas duplicaria el hecho. Si el TTL las
    # afirmara explicitamente, se normalizan a la direccion canonica.
    for propiedad, cfg in espec.inversas.items():
        pred = URIRef(ns + propiedad)
        for sujeto, objeto in g.subject_objects(pred):
            if isinstance(sujeto, URIRef) and isinstance(objeto, URIRef):
                aristas.append(Arista(str(objeto), cfg["de"], str(sujeto)))

    # Deduplica: el mismo hecho pudo llegar por la propiedad y por su inversa.
    aristas = sorted(set(aristas), key=lambda a: (a.tipo, a.desde, a.hasta))
    return nodos, aristas


# ---------------------------------------------------------------------------
# Escritura idempotente
# ---------------------------------------------------------------------------

def aplicar_restricciones(sesion, espec: Espec) -> list[str]:
    """Crea las restricciones nativas. Solo unicidad: ver findings/0001."""
    aplicadas = []
    for regla in espec.reglas_de_tipo("clave_unica"):
        if "nativa" not in regla.get("enforcement", []):
            continue
        prop = regla["propiedad"]
        for label in regla["labels"]:
            nombre = f"{regla['id'].replace('-', '_')}_{label}"
            sesion.run(
                f"CREATE CONSTRAINT {nombre} IF NOT EXISTS "
                f"FOR (n:{label}) REQUIRE n.{prop} IS UNIQUE"
            )
            aplicadas.append(nombre)
    return aplicadas


def escribir(sesion, nodos: Iterable[Nodo], aristas: Iterable[Arista],
             espec: Espec) -> dict[str, int]:
    conocidas = espec.etiquetas_conocidas()

    # Agrupa por combinacion de etiquetas para emitir un MERGE tipado por
    # grupo. Evita el MERGE sin etiqueta, que escanearia toda la base.
    por_labels: dict[tuple[str, ...], list[dict]] = defaultdict(list)
    for n in nodos:
        desconocidas = set(n.labels) - conocidas
        if desconocidas:
            raise ValueError(f"etiqueta no declarada en el mapeo: {desconocidas}")
        por_labels[n.labels].append({"iri": n.iri, "props": n.props})

    escritos = 0
    for labels, filas in por_labels.items():
        etiquetas = ":".join(labels)
        res = sesion.run(
            f"UNWIND $filas AS f "
            f"MERGE (x:{etiquetas} {{iri: f.iri}}) "
            f"SET x += f.props "
            f"RETURN count(x) AS n",
            filas=filas,
        ).single()
        escritos += res["n"]

    # Agrupa aristas por (tipo, etiqueta indexada de cada extremo) para que el
    # MATCH use el indice de la restriccion de unicidad en vez de escanear.
    indexado = {n.iri: espec.label_indexado(n.labels) for n in nodos}
    por_forma: dict[tuple[str, str, str], list[dict]] = defaultdict(list)
    for a in aristas:
        clave = (a.tipo, indexado[a.desde], indexado[a.hasta])
        por_forma[clave].append({"desde": a.desde, "hasta": a.hasta})

    aristas_escritas = 0
    for (tipo, lab_a, lab_b), filas in por_forma.items():
        res = sesion.run(
            f"UNWIND $filas AS f "
            f"MATCH (a:{lab_a} {{iri: f.desde}}) "
            f"MATCH (b:{lab_b} {{iri: f.hasta}}) "
            f"MERGE (a)-[r:{tipo}]->(b) "
            f"RETURN count(r) AS n",
            filas=filas,
        ).single()
        aristas_escritas += res["n"]

    return {"nodos": escritos, "aristas": aristas_escritas}


def proyectar(sesion, ruta_ttl: Path, espec: Espec, *,
              validar: bool = True) -> dict[str, Any]:
    nodos, aristas = leer_turtle(ruta_ttl, espec)

    if validar:
        violaciones = espec.validar(nodos, aristas)
        if violaciones:
            raise ErrorDeValidacion(violaciones)

    restricciones = aplicar_restricciones(sesion, espec)
    conteos = escribir(sesion, nodos, aristas, espec)
    return {
        "leidos": {"nodos": len(nodos), "aristas": len(aristas)},
        "escritos": conteos,
        "restricciones": restricciones,
    }
