"""Interprete del archivo declarativo de reglas de esquema.

Lee schema/reglas_esquema.yaml y lo compila a validadores previos a la
escritura. La otra mitad del interprete -emitir Cypher de restricciones y de
consultas de integridad- vive en integridad.py.

Deliberadamente NO es un ORM: no mapea clases a objetos ni gestiona sesiones.
Solo traduce una especificacion a comprobaciones.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Iterator

import yaml

RAIZ = Path(__file__).resolve().parents[2]
RUTA_POR_DEFECTO = RAIZ / "schema" / "reglas_esquema.yaml"


@dataclass(frozen=True)
class Nodo:
    iri: str
    labels: tuple[str, ...]
    props: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Arista:
    desde: str
    tipo: str
    hasta: str


@dataclass(frozen=True)
class Violacion:
    regla: str
    entidad: str
    detalle: str

    def __str__(self) -> str:
        return f"[{self.regla}] {self.entidad}: {self.detalle}"


class Espec:
    """La especificacion cargada, con sus validadores."""

    def __init__(self, datos: dict[str, Any]) -> None:
        self.version: int = datos["version"]
        self.namespace: str = datos["namespace"]
        self.clases: dict[str, list[str]] = datos["clases"]
        self.propiedades_objeto: dict[str, dict] = datos.get("propiedades_objeto", {})
        self.inversas: dict[str, dict] = datos.get("inversas", {})
        self.transitivas: list[str] = datos.get("transitivas", [])
        self.propiedades_dato: dict[str, str] = datos.get("propiedades_dato", {})
        self.reglas: list[dict] = datos.get("reglas", [])

    # -- consultas al mapeo -------------------------------------------------

    def labels_de(self, clase_owl: str) -> tuple[str, ...] | None:
        v = self.clases.get(clase_owl)
        return tuple(v) if v else None

    def relacion_de(self, propiedad_owl: str) -> str | None:
        d = self.propiedades_objeto.get(propiedad_owl)
        return d["tipo"] if d else None

    def etiquetas_conocidas(self) -> set[str]:
        return {lab for labs in self.clases.values() for lab in labs}

    def etiquetas_indexadas(self) -> set[str]:
        """Etiquetas con restriccion de unicidad, o sea con indice respaldante."""
        return {
            lab
            for r in self.reglas_de_tipo("clave_unica")
            if "nativa" in r.get("enforcement", [])
            for lab in r["labels"]
        }

    def label_indexado(self, labels: tuple[str, ...]) -> str:
        """La etiqueta de este nodo que sirve para buscarlo por indice."""
        candidatas = self.etiquetas_indexadas() & set(labels)
        if not candidatas:
            raise ValueError(
                f"ninguna etiqueta de {sorted(labels)} tiene restriccion de "
                f"unicidad; el MATCH escanearia la base"
            )
        return sorted(candidatas)[0]

    def reglas_de_tipo(self, tipo: str) -> list[dict]:
        return [r for r in self.reglas if r["type"] == tipo]

    # -- validacion previa a la escritura -----------------------------------

    def validar(self, nodos: Iterable[Nodo], aristas: Iterable[Arista]) -> list[Violacion]:
        nodos = list(nodos)
        aristas = list(aristas)
        por_iri = {n.iri: n for n in nodos}

        v: list[Violacion] = []
        for regla in self.reglas:
            if "pre_escritura" not in regla.get("enforcement", []):
                continue
            tipo = regla["type"]
            if tipo == "etiquetas_disjuntas":
                v += list(_disjuntas(regla, nodos))
            elif tipo == "relacion_funcional":
                v += list(_funcional(regla, nodos, aristas, por_iri))
            elif tipo == "dominio_rango":
                v += list(_dominio_rango(regla, aristas, por_iri))
        return v


# -- validadores por tipo de regla ------------------------------------------


def _disjuntas(regla: dict, nodos: list[Nodo]) -> Iterator[Violacion]:
    candidatas = set(regla["labels"])
    dentro = regla.get("dentro_de")
    exacta = regla.get("cardinalidad") == "exactamente_una"

    for n in nodos:
        if dentro and dentro not in n.labels:
            continue
        halladas = candidatas & set(n.labels)
        if len(halladas) > 1:
            yield Violacion(regla["id"], n.iri,
                            f"tiene {len(halladas)} etiquetas disjuntas: {sorted(halladas)}")
        elif exacta and not halladas:
            yield Violacion(regla["id"], n.iri,
                            f"no tiene ninguna de {sorted(candidatas)}")


def _funcional(regla: dict, nodos: list[Nodo], aristas: list[Arista],
               por_iri: dict[str, Nodo]) -> Iterator[Violacion]:
    tipo, desde_lab, hasta_lab = regla["relationship"], regla["from"], regla["to"]
    exacta = regla.get("cardinalidad") == "exactamente_una"

    cuenta: dict[str, int] = {n.iri: 0 for n in nodos if desde_lab in n.labels}
    for a in aristas:
        if a.tipo != tipo or a.desde not in cuenta:
            continue
        destino = por_iri.get(a.hasta)
        if destino and hasta_lab in destino.labels:
            cuenta[a.desde] += 1

    for iri, n in cuenta.items():
        if n > 1:
            yield Violacion(regla["id"], iri, f"apunta a {n} {hasta_lab}, debe ser 1")
        elif exacta and n == 0:
            yield Violacion(regla["id"], iri, f"no apunta a ningun {hasta_lab}")


def _dominio_rango(regla: dict, aristas: list[Arista],
                   por_iri: dict[str, Nodo]) -> Iterator[Violacion]:
    tipo = regla["relationship"]
    pares = regla.get("pares_permitidos")
    dominio = set(regla.get("domain", []))
    rango = set(regla.get("range", []))

    for a in aristas:
        if a.tipo != tipo:
            continue
        origen, destino = por_iri.get(a.desde), por_iri.get(a.hasta)
        if origen is None or destino is None:
            faltante = a.desde if origen is None else a.hasta
            yield Violacion(regla["id"], faltante, "extremo de la arista no existe")
            continue

        ls_o, ls_d = set(origen.labels), set(destino.labels)
        if pares:
            if not any(p[0] in ls_o and p[1] in ls_d for p in pares):
                yield Violacion(regla["id"], f"{a.desde} -> {a.hasta}",
                                f"par no permitido: {sorted(ls_o)} -> {sorted(ls_d)}")
        else:
            if dominio and not (dominio & ls_o):
                yield Violacion(regla["id"], a.desde,
                                f"fuera de dominio {sorted(dominio)}: {sorted(ls_o)}")
            if rango and not (rango & ls_d):
                yield Violacion(regla["id"], a.hasta,
                                f"fuera de rango {sorted(rango)}: {sorted(ls_d)}")


def cargar(ruta: Path | None = None) -> Espec:
    ruta = ruta or RUTA_POR_DEFECTO
    with ruta.open(encoding="utf-8") as fh:
        return Espec(yaml.safe_load(fh))
