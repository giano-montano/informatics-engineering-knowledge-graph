"""Blind reference annotation: catalog, template and validation.

The evaluation reference for the O2 comparison is annotated by hand BEFORE any
pipeline output exists. This module only produces the empty form and checks a
filled one; it never reads a syllabus and never writes an expected value.

Two artifacts:

  catalog   the backbone as a pick list (17 areas, 162 units with their
            identifiers). The annotator needs it to say which unit a topic
            should link to, and a free-typed identifier would not survive
            scoring.
  template  the form itself, YAML because the scorer has to read it back.

Validation is what keeps the reference usable: an identifier that is not in
the backbone, or a duplicated label, silently distorts precision later.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from iekg.projector import DEFAULT_BACKBONE, read_turtle
from iekg.rules import Spec

ROOT = Path(__file__).resolve().parents[2]
GOLD_DIR = ROOT / "lab" / "gold"


class AnnotationError(RuntimeError):
    """The filled annotation is not usable as a scoring reference."""


@dataclass(frozen=True)
class BackboneEntry:
    """One pickable target: a KnowledgeUnit under its KnowledgeArea.

    English stays canonical -it is what CS2023 says and what the IRI encodes-
    while the Spanish label is what a Spanish syllabus can be matched against
    without translating first. Both, not one.
    """

    key: str          # local name, e.g. KU-DM-Modeling
    label: str        # English prefLabel from CS2023
    area_key: str
    area_label: str
    iri: str
    label_es: str = ""
    area_label_es: str = ""

    def label_in(self, language: str) -> str:
        """The label to compare against, falling back to English.

        A missing Spanish label is not an error: the original monolingual
        backbone has none, and falling back keeps that file usable.
        """
        return (self.label_es or self.label) if language == "es" else self.label

    def area_label_in(self, language: str) -> str:
        return (self.area_label_es or self.area_label) if language == "es" else self.area_label


def read_backbone(spec: Spec, path: Path | None = None) -> list[BackboneEntry]:
    """The units of the backbone, each with the area it belongs to.

    Reuses the projector's reader so the catalog and the graph cannot disagree
    about what the backbone contains.
    """
    nodes, edges = read_turtle(path or DEFAULT_BACKBONE, spec)
    ns = spec.namespace
    by_iri = {n.iri: n for n in nodes}
    area_of = {
        e.source: e.target
        for e in edges
        if e.rel_type == "PART_OF" and "KnowledgeArea" in by_iri[e.target].labels
    }

    def label_of(iri: str, prop: str = "prefLabel") -> str:
        return by_iri[iri].props.get(prop, "" if prop != "prefLabel" else "<sin prefLabel>")

    entries = []
    for node in nodes:
        if "KnowledgeUnit" not in node.labels:
            continue
        area_iri = area_of.get(node.iri)
        if area_iri is None:
            raise AnnotationError(f"{node.iri}: unit with no area, backbone is broken")
        entries.append(
            BackboneEntry(
                key=node.iri.removeprefix(ns),
                label=label_of(node.iri),
                area_key=area_iri.removeprefix(ns),
                area_label=label_of(area_iri),
                iri=node.iri,
                label_es=label_of(node.iri, "prefLabelEs"),
                area_label_es=label_of(area_iri, "prefLabelEs"),
            )
        )
    return sorted(entries, key=lambda e: (e.area_label, e.label))


# ---------------------------------------------------------------------------
# Artifacts
# ---------------------------------------------------------------------------

# Generated prose is Spanish: it is read by the annotator, not by a console.
# See docs/estandares-de-codigo.md §1.

def catalog_markdown(entries: list[BackboneEntry]) -> str:
    lines = [
        "# Catálogo del backbone CS2023 — destinos de enlace",
        "",
        "**Artefacto generado.** No editar a mano: lo emite",
        "`lab/scripts/emit_annotation_template.py` desde",
        "`ontology/backbone_cs2023.ttl`.",
        "",
        f"{len({e.area_key for e in entries})} áreas y {len(entries)} unidades de",
        "conocimiento. Es la lista cerrada de valores admitidos en `links_to_ku`",
        "de una anotación de referencia: un identificador escrito a mano que no",
        "esté aquí hace fallar la validación, que es justo lo que se quiere.",
        "",
        "Las etiquetas están en inglés porque vienen de CS2023 y el enlace se hace",
        "contra ellas. El sílabo está en español; traducir es parte de la tarea.",
        "",
    ]
    current = None
    for entry in entries:
        if entry.area_key != current:
            current = entry.area_key
            lines += ["", f"## {entry.area_label}  (`{entry.area_key}`)", "",
                      "| Identificador | Unidad de conocimiento |", "|---|---|"]
        lines.append(f"| `{entry.key}` | {entry.label} |")
    return "\n".join(lines) + "\n"


_TEMPLATE_HEAD = """\
# Anotación de referencia CIEGA — {code} ({term})
#
# QUÉ ES. La lista de lo que TÚ esperas que un pipeline extraiga de este
# sílabo, escrita a mano y ANTES de ver ninguna salida de ningún modelo. Es la
# referencia contra la que se mide la precisión del resultado R4.
#
# POR QUÉ CIEGA. Si se anota después de leer una extracción, la anotación se
# contagia de lo que el modelo propuso y deja de ser un criterio independiente.
# Un jurado puede objetar eso y tendría razón. Mientras `blind: true` y este
# archivo no esté completo, ninguna sesión debe mostrar extracciones reales de
# {source_name}.
#
# CÓMO SE RELLENA.
#   1. Lee el sílabo entero.
#   2. Escribe los Temas que un lector humano sacaría de él, en el orden que
#      quieras. `label_es` tal como aparece; `label_en` la etiqueta canónica en
#      inglés, que es la que se compara contra el backbone.
#   3. Para cada Tema, la unidad de conocimiento del backbone a la que debería
#      enlazar: un identificador de `lab/gold/backbone-catalog.md`. Si crees
#      que ninguna encaja, deja `links_to_ku: null` y explica en `note`. Un
#      enlace vacío es un dato, no un hueco: mide cuánto del sílabo NO cubre
#      CS2023.
#   4. Los Conceptos de cada Tema. Si dudas de si algo es Tema o Concepto,
#      decide y sigue: la escala de la decisión también se está midiendo.
#   5. `confidence: low` en lo que dudes. Al puntuar se reporta aparte, así que
#      marcar duda no penaliza; ocultarla sí distorsiona.
#
# QUÉ NO VA AQUÍ.
#   - Prerrequisitos: fuera de esta primera comparación (handoff 2026-08-14).
#   - Cursos, docentes, evaluaciones, bibliografía: no son KnowledgeElement.
#   - Lo que un modelo podría sacar pero tú no pondrías: eso va en
#     `out_of_scope`, y es lo que permite medir el ruido.
#
# El recuento no importa. Que esté completo antes de la primera corrida, sí.

version: 1

document:
  code: {code}
  term: "{term}"
  source: {source}

annotator: {annotator}
date: {date}          # fecha en que se CIERRA la anotación
blind: true           # pásalo a false si viste una extracción antes de cerrarla

# ---------------------------------------------------------------------------
# Temas esperados. Duplica el bloque tantas veces como haga falta.
# ---------------------------------------------------------------------------
topics:
"""

_TEMPLATE_TOPIC = """\
  - label_es: ""
    label_en: ""
    links_to_ku: null        # p.ej. KU-DM-Modeling, o null si ninguna encaja
    confidence: high         # high | low
    note: ""
    concepts:
      - label_es: ""
        label_en: ""
        confidence: high
"""

_TEMPLATE_TAIL = """
# ---------------------------------------------------------------------------
# Menciones que el sílabo contiene y que NO deben convertirse en Tema ni en
# Concepto. Mide el ruido: una extracción que las produzca resta precisión.
# Ejemplos del género: nombres de docentes, siglas de facultad, políticas de
# asistencia, títulos de libros.
# ---------------------------------------------------------------------------
out_of_scope: []

# Cualquier cosa que te haya costado decidir. Se cita en el finding.
notes: ""
"""


def template(code: str, term: str, source: Path, *, annotator: str,
             topic_slots: int) -> str:
    body = _TEMPLATE_HEAD.format(
        code=code,
        term=term,
        source=source.as_posix(),
        source_name=source.name,
        annotator=annotator,
        date="",
    )
    return body + _TEMPLATE_TOPIC * topic_slots + _TEMPLATE_TAIL


# ---------------------------------------------------------------------------
# Reading a filled annotation
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Mention:
    label_es: str
    label_en: str
    confidence: str
    links_to_ku: str | None = None
    note: str = ""


@dataclass(frozen=True)
class Annotation:
    code: str
    term: str
    source: str
    annotator: str
    date: str
    blind: bool
    topics: tuple[Mention, ...]
    # concepts keyed by the English label of their topic: the partonomy matters
    # for scoring, a flat list would hide misplacement.
    concepts: dict[str, tuple[Mention, ...]]
    out_of_scope: tuple[str, ...]
    notes: str

    @property
    def concept_count(self) -> int:
        return sum(len(v) for v in self.concepts.values())


def _mention(raw: dict[str, Any], where: str, *, linkable: bool) -> Mention:
    for field in ("label_es", "label_en"):
        if not (raw.get(field) or "").strip():
            raise AnnotationError(f"{where}: empty {field}")
    confidence = raw.get("confidence", "high")
    if confidence not in ("high", "low"):
        raise AnnotationError(f"{where}: confidence must be high or low, got {confidence!r}")
    return Mention(
        label_es=raw["label_es"].strip(),
        label_en=raw["label_en"].strip(),
        confidence=confidence,
        links_to_ku=(raw.get("links_to_ku") or None) if linkable else None,
        note=(raw.get("note") or "").strip(),
    )


def load_annotation(path: Path, catalog: list[BackboneEntry]) -> Annotation:
    """Read a filled template, refusing anything that would skew scoring."""
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if raw.get("version") != 1:
        raise AnnotationError(f"unsupported annotation version: {raw.get('version')!r}")

    known = {e.key for e in catalog}
    topics: list[Mention] = []
    concepts: dict[str, tuple[Mention, ...]] = {}

    entries = raw.get("topics") or []
    # An unfilled template parses fine and scores as an empty reference, which
    # would report a flattering 0 extractions expected. Refuse it outright.
    filled = [t for t in entries if (t.get("label_es") or "").strip()]
    if not filled:
        raise AnnotationError(f"{path.name}: no topic is filled in")

    for i, raw_topic in enumerate(filled, 1):
        topic = _mention(raw_topic, f"topic {i}", linkable=True)
        if topic.links_to_ku and topic.links_to_ku not in known:
            raise AnnotationError(
                f"topic {i} ({topic.label_en}): links_to_ku {topic.links_to_ku!r} "
                f"is not a backbone unit; see lab/gold/backbone-catalog.md"
            )
        if topic.label_en in concepts:
            raise AnnotationError(f"topic {i}: label_en {topic.label_en!r} is repeated")
        topics.append(topic)
        concepts[topic.label_en] = tuple(
            _mention(c, f"topic {i} concept {j}", linkable=False)
            for j, c in enumerate(raw_topic.get("concepts") or [], 1)
            if (c.get("label_es") or "").strip()
        )

    document = raw.get("document") or {}
    return Annotation(
        code=str(document.get("code", "")),
        term=str(document.get("term", "")),
        source=str(document.get("source", "")),
        annotator=str(raw.get("annotator", "")),
        date=str(raw.get("date") or ""),
        blind=bool(raw.get("blind", False)),
        topics=tuple(topics),
        concepts=concepts,
        out_of_scope=tuple(raw.get("out_of_scope") or ()),
        notes=str(raw.get("notes") or ""),
    )


# The only annotator whose annotation can ground R4's precision figure. Anyone
# else -- a second reader, or a model writing a contrast annotation -- produces
# a usable file that is NOT the gold standard, and every run made against one
# has to say so in its manifest.
CANONICAL_ANNOTATOR = "giano"


def read_seal(path: Path) -> Annotation | None:
    """The annotation at `path` if it is usable as a reference, else None.

    The gate every pipeline run checks before touching an annotated document:
    a missing, unfilled or unsealed annotation means no real extraction may be
    shown yet.
    """
    if not path.exists():
        return None
    try:
        from iekg import rules

        annotation = load_annotation(path, read_backbone(rules.load()))
    except (AnnotationError, KeyError, yaml.YAMLError):
        return None
    return annotation if annotation.blind and annotation.date else None


def is_sealed(path: Path) -> bool:
    return read_seal(path) is not None
