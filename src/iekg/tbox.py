"""T-box reader and diagram emitter.

Reads the OWL schema (ontology/ontologia_informatica.ttl) with rdflib and
annotates every class and property with the LPG mapping declared in
schema/schema_rules.yaml. The result is emitted as a Mermaid diagram.

Why outside the database: the T-box is not materialised in Neo4j. Labels and
relationship types already carry the class and property identity, so meta
nodes would restate what the graph says and add hubs that hide the data.
Everything the labels cannot carry -disjointness, cardinality, transitivity,
inverses- is emitted here instead, as a versionable artifact.

Emits, does not execute: same contract as integrity.py.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from rdflib import OWL, RDF, RDFS, BNode, Graph, URIRef

from iekg.rules import Spec

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_TBOX = ROOT / "ontology" / "ontologia_informatica.ttl"


@dataclass(frozen=True)
class ClassAxioms:
    name: str
    superclasses: tuple[str, ...] = ()
    # (property, filler) from `subClassOf [ someValuesFrom ... ]`
    existential: tuple[tuple[str, str], ...] = ()


@dataclass(frozen=True)
class PropertyAxioms:
    name: str
    domain: tuple[str, ...] = ()
    range: tuple[str, ...] = ()
    sub_property_of: tuple[str, ...] = ()
    inverse_of: str | None = None
    characteristics: tuple[str, ...] = ()


@dataclass
class TBox:
    namespace: str
    classes: dict[str, ClassAxioms] = field(default_factory=dict)
    object_properties: dict[str, PropertyAxioms] = field(default_factory=dict)
    data_properties: dict[str, PropertyAxioms] = field(default_factory=dict)
    # Each entry is a set of pairwise-disjoint classes.
    disjoint_sets: list[tuple[str, ...]] = field(default_factory=list)
    # Class -> members of its owl:disjointUnionOf, a stronger axiom: the
    # members are disjoint AND they cover the union.
    disjoint_unions: dict[str, tuple[str, ...]] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Turtle -> TBox
# ---------------------------------------------------------------------------

_CHARACTERISTICS = {
    OWL.TransitiveProperty: "transitive",
    OWL.FunctionalProperty: "functional",
    OWL.InverseFunctionalProperty: "inverse functional",
    OWL.SymmetricProperty: "symmetric",
    OWL.AsymmetricProperty: "asymmetric",
    OWL.IrreflexiveProperty: "irreflexive",
}


def read_tbox(path: Path | None, spec: Spec) -> TBox:
    g = Graph().parse(path or DEFAULT_TBOX, format="turtle")
    ns = spec.namespace
    tbox = TBox(namespace=ns)

    def local(term) -> str | None:
        """Local name of an IRI in our namespace; None for anything else."""
        if not isinstance(term, URIRef):
            return None
        text = str(term)
        return text.removeprefix(ns) if text.startswith(ns) else None

    def rdf_list(head) -> list:
        """Materialise an rdf:List; rdflib exposes it only as linked nodes."""
        items = []
        while head and head != RDF.nil:
            items += list(g.objects(head, RDF.first))
            head = g.value(head, RDF.rest)
        return items

    def class_expression(term) -> tuple[str, ...]:
        """Named class -> itself. owl:unionOf blank node -> its members.
        Anything else (restrictions used as domain) -> empty."""
        name = local(term)
        if name:
            return (name,)
        if isinstance(term, BNode):
            union = g.value(term, OWL.unionOf)
            if union:
                return tuple(n for n in map(local, rdf_list(union)) if n)
        return ()

    # -- classes ------------------------------------------------------------
    for subject in g.subjects(RDF.type, OWL.Class):
        name = local(subject)
        if not name:
            continue  # blank-node class expressions are read in context
        supers: list[str] = []
        existential: list[tuple[str, str]] = []
        for parent in g.objects(subject, RDFS.subClassOf):
            parent_name = local(parent)
            if parent_name:
                supers.append(parent_name)
            elif isinstance(parent, BNode):
                prop = local(g.value(parent, OWL.onProperty))
                filler = local(g.value(parent, OWL.someValuesFrom))
                if prop and filler:
                    existential.append((prop, filler))
        tbox.classes[name] = ClassAxioms(
            name=name,
            superclasses=tuple(sorted(supers)),
            existential=tuple(sorted(existential)),
        )

    # -- properties ---------------------------------------------------------
    for rdf_type, target in ((OWL.ObjectProperty, tbox.object_properties),
                             (OWL.DatatypeProperty, tbox.data_properties),
                             (OWL.AnnotationProperty, tbox.data_properties)):
        for subject in g.subjects(RDF.type, rdf_type):
            name = local(subject)
            if not name:
                continue
            domain: list[str] = []
            for term in g.objects(subject, RDFS.domain):
                domain += class_expression(term)
            ranges: list[str] = []
            for term in g.objects(subject, RDFS.range):
                ranges += class_expression(term) or ([str(term)] if isinstance(term, URIRef) else [])
            supers = [n for n in map(local, g.objects(subject, RDFS.subPropertyOf)) if n]
            inverse = next((n for n in map(local, g.objects(subject, OWL.inverseOf)) if n), None)
            traits = tuple(
                label for term, label in _CHARACTERISTICS.items()
                if (subject, RDF.type, term) in g
            )
            target[name] = PropertyAxioms(
                name=name,
                domain=tuple(domain),
                range=tuple(ranges),
                sub_property_of=tuple(sorted(supers)),
                inverse_of=inverse,
                characteristics=tuple(sorted(traits)),
            )

    # -- disjointness -------------------------------------------------------
    for subject in g.subjects(RDF.type, OWL.AllDisjointClasses):
        members = tuple(n for n in map(local, rdf_list(g.value(subject, OWL.members))) if n)
        if members:
            tbox.disjoint_sets.append(members)

    for subject, union in g.subject_objects(OWL.disjointUnionOf):
        name = local(subject)
        members = tuple(n for n in map(local, rdf_list(union)) if n)
        if name and members:
            tbox.disjoint_unions[name] = members

    return tbox


# ---------------------------------------------------------------------------
# TBox + Spec -> Mermaid
# ---------------------------------------------------------------------------

# Status wording is Spanish because it lands in generated prose, not in
# console output; see docs/estandares-de-codigo.md.
_TRAIT_TEXT = {
    "transitive": "transitiva",
    "functional": "funcional",
    "inverse functional": "inversa funcional",
    "symmetric": "simétrica",
    "asymmetric": "asimétrica",
    "irreflexive": "irreflexiva",
}

_STATUS_TEXT = {
    "materialised": "se escribe",
    "inverse": "no se escribe: se recorre al revés",
    "unmapped": "no se proyecta",
}


def projection_of(prop: str, spec: Spec) -> tuple[str, str]:
    """How an OWL property reaches the graph: (relationship type, status)."""
    mapped = spec.object_properties.get(prop)
    if mapped:
        return mapped["type"], "materialised"
    inverse = spec.inverses.get(prop)
    if inverse:
        return inverse["of"], "inverse"
    return "", "unmapped"


def _labels_of(owl_class: str, spec: Spec) -> str:
    labels = spec.labels_for(owl_class)
    if labels:
        return ":" + ":".join(labels)
    # A class may be projected without being instantiable: KnowledgeElement is
    # a disjoint union, so it reaches the graph only as an extra label on its
    # members. It has no entry of its own in the mapping.
    if owl_class in spec.known_labels():
        return f":{owl_class} (abstracta)"
    return "not projected"


def is_projected(owl_class: str, spec: Spec) -> bool:
    return bool(spec.labels_for(owl_class)) or owl_class in spec.known_labels()


def class_diagram(tbox: TBox, spec: Spec) -> str:
    """Class hierarchy, with the LPG label set each class projects to."""
    lines = ["graph BT"]
    for name in sorted(tbox.classes):
        lines.append(f'    {name}["<b>{name}</b><br/><code>{_labels_of(name, spec)}</code>"]')
    for name, axioms in sorted(tbox.classes.items()):
        for parent in axioms.superclasses:
            lines.append(f"    {name} -->|subClassOf| {parent}")
    # Disjointness has no LPG counterpart; it survives only as an integrity
    # query, so it is drawn as a note rather than as an edge.
    for owner, members in sorted(tbox.disjoint_unions.items()):
        node = f"DU_{owner}"
        lines.append(f'    {node}("disjointUnionOf<br/>{" | ".join(members)}"):::axiom')
        lines.append(f"    {node} -.-> {owner}")
    lines.append("    classDef axiom fill:#fff3cd,stroke:#d39e00,stroke-dasharray:3 3;")
    return "\n".join(lines)


def property_diagram(tbox: TBox, spec: Spec) -> str:
    """Object properties as edges between classes, labelled with the LPG type."""
    lines = ["graph LR"]
    drawn: set[str] = set()

    def node(name: str) -> str:
        if name not in drawn:
            drawn.add(name)
            lines.append(f'    {name}["<b>{name}</b>"]')
        return name

    for name, axioms in sorted(tbox.object_properties.items()):
        rel_type, status = projection_of(name, spec)
        if status != "materialised":
            continue  # inverses would draw the same fact twice
        traits = f" [{', '.join(axioms.characteristics)}]" if axioms.characteristics else ""
        for source in axioms.domain or ("?",):
            for target in axioms.range or ("?",):
                lines.append(
                    f'    {node(source)} -->|"{name}<br/>:{rel_type}{traits}"| {node(target)}'
                )
    return "\n".join(lines)


def mapping_table(tbox: TBox, spec: Spec) -> str:
    """OWL property -> relationship type, and whether it is written."""
    rows = ["| Propiedad OWL | Dominio | Rango | En el grafo | Estado |",
            "|---|---|---|---|---|"]
    for name, axioms in sorted(tbox.object_properties.items()):
        rel_type, status = projection_of(name, spec)
        rows.append(
            f"| `{name}` | {', '.join(axioms.domain) or '—'} "
            f"| {', '.join(axioms.range) or '—'} "
            f"| {f'`-[:{rel_type}]->`' if rel_type else '—'} | {_STATUS_TEXT[status]} |"
        )
    return "\n".join(rows)


def emit(tbox: TBox, spec: Spec) -> str:
    """The whole artifact: diagrams plus the axioms labels cannot carry."""
    parts = [
        "# T-box de la ontología, proyectada al modelo de Neo4j",
        "",
        "**Artefacto generado.** No editar a mano: lo emite",
        "`lab/scripts/emit_tbox_diagram.py` desde `ontology/ontologia_informatica.ttl`",
        "y `schema/schema_rules.yaml`. Se regenera con",
        "`uv run python lab/scripts/emit_tbox_diagram.py`.",
        "",
        "La T-box **no está materializada en Neo4j**: las etiquetas y los tipos de",
        "arista ya identifican clase y propiedad. Lo que las etiquetas no pueden",
        "cargar —disyunción, cardinalidad, transitividad, inversas— vive aquí.",
        "",
        "## 1. Jerarquía de clases",
        "",
        "Cada caja muestra la clase OWL y el juego de etiquetas al que se proyecta.",
        "",
        "```mermaid",
        class_diagram(tbox, spec),
        "```",
        "",
        "## 2. Propiedades de objeto",
        "",
        "Sólo las materializadas: una inversa dibujaría el mismo hecho dos veces.",
        "",
        "```mermaid",
        property_diagram(tbox, spec),
        "```",
        "",
        "## 3. Mapeo completo OWL → LPG",
        "",
        mapping_table(tbox, spec),
        "",
        "## 4. Axiomas sin contraparte nativa",
        "",
        "Ninguno de estos existe como restricción en Neo4j (ver `findings/0001`:",
        "sólo la unicidad sobrevive a Community). Se comprueban con las consultas",
        "de integridad de `build/integrity/`.",
        "",
    ]

    for owner, members in sorted(tbox.disjoint_unions.items()):
        parts.append(f"- `{owner}` es **unión disjunta** de {', '.join(f'`{m}`' for m in members)}: "
                     f"todo individuo lleva exactamente una de esas etiquetas.")
    for members in tbox.disjoint_sets:
        parts.append(f"- **Disjuntas entre sí**: {', '.join(f'`{m}`' for m in members)}.")
    for name, axioms in sorted(tbox.object_properties.items()):
        if axioms.characteristics:
            rel_type, _ = projection_of(name, spec)
            target = f"`{rel_type}`" if rel_type else "sin proyección"
            traits = ", ".join(_TRAIT_TEXT.get(t, t) for t in axioms.characteristics)
            parts.append(f"- `{name}` es una propiedad {traits} → {target}.")
    for name, axioms in sorted(tbox.classes.items()):
        for prop, filler in axioms.existential:
            parts.append(f"- Todo `{name}` está en al menos un `{filler}` vía `{prop}` "
                         f"(existencial; bajo mundo abierto el razonador no lo detecta).")

    return "\n".join(parts) + "\n"


def write_artifact(spec: Spec, target: Path, tbox_path: Path | None = None) -> Path:
    tbox = read_tbox(tbox_path, spec)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(emit(tbox, spec), encoding="utf-8")
    return target
