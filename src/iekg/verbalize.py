"""T-box -> prompt. The third backend of the same interpreter.

`integrity.py` compiles the rules to Cypher and `tbox.py` to a diagram; this
compiles the ontology to the English prose a model is asked to obey. All three
read the same two sources, so a prompt cannot drift away from the schema the
extraction is later validated against. That is the whole reason it is generated
instead of typed into a string literal.

The pattern -verbalise the whole ontology into the prompt- is Text2KGBench's
(Mihindukulasooriya et al., ISWC 2023). It is viable here only because this
T-box is small; it does not generalise to ontologies with hundreds of classes.
See lab/docs/research_pipelines.md.

English, unlike the other generated prose: it is read by a model alongside
identifiers that are themselves English.
"""

from __future__ import annotations

from pathlib import Path

from iekg.rules import Spec
from iekg.tbox import TBox, read_tbox


def _existential_sentences(tbox: TBox) -> list[str]:
    out = []
    for name, axioms in sorted(tbox.classes.items()):
        for prop, filler in axioms.existential:
            out.append(f"Every {name} is linked to at least one {filler} via {prop}.")
    return out


def _disjointness_sentences(tbox: TBox) -> list[str]:
    out = []
    for owner, members in sorted(tbox.disjoint_unions.items()):
        listed = ", ".join(members)
        out.append(
            f"Every {owner} is exactly one of: {listed}. These four are mutually "
            f"exclusive: nothing is both a Topic and a Concept."
        )
    for members in tbox.disjoint_sets:
        out.append(f"No individual is more than one of: {', '.join(members)}.")
    return out


def ontology_prompt(tbox: TBox, spec: Spec, coinable: list[str]) -> str:
    """The ontology as instructions: classes, relations, and what may be created."""
    fixed = [c for c in sorted(tbox.classes) if c not in coinable]

    lines = [
        "# ONTOLOGY",
        "",
        "You extract instances for a curriculum knowledge graph. The schema below",
        "is closed: anything outside it is discarded downstream, so proposing it",
        "only costs precision.",
        "",
        "## Classes",
        "",
    ]
    for name, axioms in sorted(tbox.classes.items()):
        parents = f" (a kind of {', '.join(axioms.superclasses)})" if axioms.superclasses else ""
        may = "you may create these" if name in coinable else "already exists, never create"
        lines.append(f"- {name}{parents} -- {may}")

    lines += ["", "## Relations", ""]
    for name, axioms in sorted(tbox.object_properties.items()):
        if name not in spec.object_properties:
            continue  # inverses would state the same fact twice
        domain = ", ".join(axioms.domain) or "?"
        rng = ", ".join(axioms.range) or "?"
        traits = f"  [{', '.join(axioms.characteristics)}]" if axioms.characteristics else ""
        lines.append(f"- {name}: {domain} -> {rng}{traits}")

    lines += ["", "## Constraints", ""]
    for sentence in _disjointness_sentences(tbox) + _existential_sentences(tbox):
        lines.append(f"- {sentence}")

    lines += [
        "",
        "## Scope",
        "",
        f"- You may only create: {', '.join(coinable)}.",
        f"- These are already in the graph and must never be created: {', '.join(fixed)}.",
        "- A Topic is a unit of curricular content, at the granularity of a section",
        "  of a syllabus. A Concept is a single idea, technique or artifact taught",
        "  inside a Topic.",
        "- Course logistics are not knowledge: instructors, schedules, grading",
        "  policies, attendance rules and bibliography entries are out of scope.",
        "- Extract only what the source states. If the source does not say it, it",
        "  does not exist. An invented element costs more than a missing one.",
    ]
    return "\n".join(lines)


def build(spec: Spec, coinable: list[str], tbox_path: Path | None = None) -> str:
    return ontology_prompt(read_tbox(tbox_path, spec), spec, coinable)
