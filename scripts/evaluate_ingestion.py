"""Development aid: measure the extraction test cases, CP-01 to CP-14.

Not an entry point of the system. It reads the accepted batches from the fact
store and compares them with the reference annotation, by the matching rules
of the thesis (section 5.2.5). How each measure is computed, and what the
thesis leaves open, is in casos-de-prueba/calculo-de-las-medidas-del-evaluador.md.

    uv run python scripts/evaluate_ingestion.py cases --from-run 5
    uv run python scripts/evaluate_ingestion.py cases --isolated --hide-held-out
    uv run python scripts/evaluate_ingestion.py review --workbook FILLED.xlsx
    uv run python scripts/evaluate_ingestion.py review --from-run 5
    uv run python scripts/evaluate_ingestion.py agreement --review-dir A --other-review-dir B

Reports go to var/measurements/, with Markdown tables on the console.
"""

import argparse
import ast
import csv
import json
import sys
from collections import Counter, defaultdict
from collections.abc import Iterable, Iterator, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from difflib import SequenceMatcher
from functools import cached_property
from pathlib import Path
from typing import Any

from iekg.core.batch import Batch
from iekg.graph_schema import CONCEPT, PART_OF, PREF_LABEL_ES, TOPIC
from iekg.ingestion.normalization import normalize_label
from iekg.operational_store import REJECTED

THRESHOLD = 0.75
MAX_ATTEMPTS = 3
# Never used to tune the prompt: the reviewer extracts the same two.
HELD_OUT = ("1INF27", "1INF37")

# The annotation's word for each class of item.
KIND_OF = {TOPIC: "tema", CONCEPT: "concepto"}
MANDATORY = "obligatoria"

GOLD = Path("casos-de-prueba/gold/gold_consolidado.tsv")
COMPOUND_HEADINGS = Path("casos-de-prueba/gold/scripts_consolidacion/idglobal.py")
REVIEW_DIR = Path("casos-de-prueba/revision")
MEASUREMENTS = Path("var/measurements")

# The columns of the extraction sheet the reviewer fills.
_REVIEW_NAME, _REVIEW_KIND, _REVIEW_TEXT, _REVIEW_COMMENT = "Tema o concepto", "Tipo", "Texto del sílabo", "Comentario"


# --- The annotation ----------------------------------------------------------


@dataclass(frozen=True)
class Entry:
    syllabus: str
    global_id: str
    id: str
    kind: str
    level: str
    label: str
    aliases: tuple[str, ...]
    evidence: str


@dataclass(frozen=True)
class Gold:
    entries: tuple[Entry, ...]
    meta: str = ""

    @cached_property
    def syllabi(self) -> tuple[str, ...]:
        """In the order of the test cases, which is the order of the file."""
        return tuple(dict.fromkeys(entry.syllabus for entry in self.entries))

    def case_of(self, syllabus: str) -> str:
        return f"CP-{self.syllabi.index(syllabus) + 1:02d}"

    @cached_property
    def names(self) -> Mapping[str, frozenset[str]]:
        """The names of each notion: labels and aliases of all its entries, in any syllabus."""
        names: dict[str, set[str]] = defaultdict(set)
        for entry in self.entries:
            names[entry.global_id].update(normalize_label(name) for name in (entry.label, *entry.aliases))
        return {global_id: frozenset(found) for global_id, found in names.items()}

    def entries_of(self, syllabus: str) -> tuple[Entry, ...]:
        return self._by_syllabus.get(syllabus, ())

    def candidates_of(self, syllabus: str) -> Mapping[str, tuple[Entry, ...]]:
        """By normalized name, the entries of ``syllabus`` whose notion has that name."""
        return self._candidates.get(syllabus, {})

    def mandatory_notions_of(self, syllabus: str) -> dict[str, Entry]:
        """The notions with a mandatory entry in ``syllabus``, each with its first one."""
        notions: dict[str, Entry] = {}
        for entry in self.entries_of(syllabus):
            if entry.level == MANDATORY:
                notions.setdefault(entry.global_id, entry)
        return notions

    @cached_property
    def _by_syllabus(self) -> Mapping[str, tuple[Entry, ...]]:
        grouped: dict[str, list[Entry]] = defaultdict(list)
        for entry in self.entries:
            grouped[entry.syllabus].append(entry)
        return {syllabus: tuple(entries) for syllabus, entries in grouped.items()}

    @cached_property
    def _candidates(self) -> Mapping[str, Mapping[str, tuple[Entry, ...]]]:
        result = {}
        for syllabus, entries in self._by_syllabus.items():
            by_name: dict[str, list[Entry]] = defaultdict(list)
            for entry in entries:
                for name in self.names[entry.global_id]:
                    by_name[name].append(entry)
            result[syllabus] = {name: tuple(found) for name, found in by_name.items()}
        return result


def load_gold(path: Path) -> Gold:
    with open(path, encoding="utf-8", newline="") as file:
        meta = file.readline().strip()
        # The notes hold plain double quotes: the file is tab-separated, never quoted.
        rows = list(csv.DictReader(file, delimiter="\t", quoting=csv.QUOTE_NONE))
    return Gold(
        tuple(
            Entry(
                syllabus=row["silabo"],
                global_id=row["id_global"],
                id=row["id"],
                kind=row["tipo"],
                level=row["nivel"],
                label=row["etiqueta"],
                aliases=tuple(alias for alias in row["alias"].split("|") if alias.strip()),
                evidence=row["evidencia"],
            )
            for row in rows
        ),
        meta,
    )


def load_compound_headings(path: Path) -> frozenset[str]:
    """The entries of headings that name more than one piece of knowledge.

    They live only as the constant ``COMPUESTOS`` of the script that assigned
    the global identifiers; reading it there keeps a single list. The script
    is parsed, not run.
    """
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "COMPUESTOS" for target in node.targets
        ):
            value = node.value
            if isinstance(value, ast.Call) and isinstance(value.func, ast.Attribute) and value.func.attr == "split":
                value = value.func.value
            if isinstance(value, ast.Constant) and isinstance(value.value, str):
                return frozenset(value.value.split())
    raise ValueError(f"{path}: no COMPUESTOS written as a string of entry ids")


# --- The items of a batch ----------------------------------------------------


@dataclass(frozen=True)
class Item:
    key: str
    label: str
    name: str


class UnknownEndpoint(Exception):
    """An edge reaches a node that is in no earlier batch nor in the reference layer."""


# By key, the class and the Spanish label of every node a batch may link.
Known = dict[str, tuple[str, str]]


def index_batch(known: Known, batch: Batch) -> None:
    for node in batch.nodes:
        known[node.key] = (node.label, node.properties.get(PREF_LABEL_ES, ""))


def items_of(batch: Batch, known: Mapping[str, tuple[str, str]]) -> list[Item]:
    """Every topic or concept the batch creates or links, once each: the nodes it
    creates in the order of the batch, then the existing ones in the order its
    edges first reach them."""
    items = [Item(n.key, n.label, n.properties.get(PREF_LABEL_ES, "")) for n in batch.nodes if n.label in KIND_OF]
    seen = set(batch.nodes_by_key)
    for edge in batch.edges:
        for key in (edge.source, edge.target):
            if key in seen:
                continue
            seen.add(key)
            if key not in known:
                raise UnknownEndpoint(f"{edge.describe()}: {key} is in no earlier batch nor in the reference layer")
            label, name = known[key]
            if label in KIND_OF:
                items.append(Item(key, label, name))
    return items


def outside_of(batch: Batch) -> frozenset[str]:
    """The nodes the batch reaches without placing them in the partonomy of its
    syllabus: a concept the course requires, or one that is only the end of a
    prerequisite or a specialization. A diagnostic; they are items all the same."""
    placed = {key for edge in batch.edges if edge.type == PART_OF for key in (edge.source, edge.target)}
    reached = set(batch.nodes_by_key) | {key for edge in batch.edges for key in (edge.source, edge.target)}
    return frozenset(reached - placed)


# --- Matching (thesis, 5.2.5.4) ----------------------------------------------


@dataclass(frozen=True)
class Match:
    item: Item
    entry: Entry | None


def match(items: Sequence[Item], gold: Gold, syllabus: str) -> list[Match]:
    """One to one, in the order of ``items``: each hit consumes an entry of the syllabus."""
    candidates_of = gold.candidates_of(syllabus)
    consumed: set[str] = set()
    matches = []
    for item in items:
        name = normalize_label(item.name)
        free = [entry for entry in candidates_of.get(name, ()) if entry.id not in consumed]
        if not free:
            matches.append(Match(item, None))
            continue
        # Tie-break: the entry with that very label, then the one of the same type, then the lowest id.
        chosen = min(free, key=lambda e: (normalize_label(e.label) != name, e.kind != KIND_OF[item.label], e.id))
        consumed.add(chosen.id)
        matches.append(Match(item, chosen))
    return matches


def most_hits(items: Sequence[Item], gold: Gold, syllabus: str) -> int:
    """The hits of the best order of the items: a maximum matching. A diagnostic of
    how much the order of the batch mattered, never the reported figure."""
    candidates_of = gold.candidates_of(syllabus)
    options = [[entry.id for entry in candidates_of.get(normalize_label(item.name), ())] for item in items]
    taken_by: dict[str, int] = {}

    def place(index: int, visited: set[str]) -> bool:
        for entry_id in options[index]:
            if entry_id in visited:
                continue
            visited.add(entry_id)
            if entry_id not in taken_by or place(taken_by[entry_id], visited):
                taken_by[entry_id] = index
                return True
        return False

    return sum(place(index, set()) for index in range(len(items)))


def _ratio(numerator: int, denominator: int) -> float | None:
    return numerator / denominator if denominator else None


def _f1(precision: float | None, recall: float | None) -> float | None:
    if precision is None or recall is None:
        return None
    return 2 * precision * recall / (precision + recall) if precision + recall else 0.0


def _with_ratios(counts: dict[str, Any]) -> dict[str, Any]:
    counts = {"outside_items": 0, "outside_hits": 0, **counts}
    precision = _ratio(counts["hits"], counts["items"])
    recall = _ratio(counts["recovered"], counts["mandatory_notions"])
    return {
        **counts,
        "false_positives": counts["items"] - counts["hits"],
        "precision": precision,
        "recall": recall,
        "f1": _f1(precision, recall),
        "type_agreement": _ratio(counts["type_matches"], counts["hits"]),
        # Diagnostic, never the indicator: the precision of the items the syllabus places.
        "placed_precision": _ratio(counts["hits"] - counts["outside_hits"],
                                   counts["items"] - counts["outside_items"]),
    }


def measure(
    matches: Sequence[Match], gold: Gold, syllabus: str, outside: frozenset[str] = frozenset()
) -> dict[str, Any]:
    hits = [m for m in matches if m.entry is not None]
    consumed = {m.entry.id for m in hits}
    mandatory = gold.mandatory_notions_of(syllabus)
    # A notion is recovered if any of its entries in the syllabus was consumed.
    recovered = {entry.global_id for entry in gold.entries_of(syllabus) if entry.id in consumed} & set(mandatory)
    return {
        **_with_ratios({
            "items": len(matches),
            "hits": len(hits),
            "mandatory_notions": len(mandatory),
            "recovered": len(recovered),
            "type_matches": sum(KIND_OF[m.item.label] == m.entry.kind for m in hits),
            "outside_items": sum(m.item.key in outside for m in matches),
            "outside_hits": sum(m.item.key in outside for m in hits),
        }),
        "most_hits": most_hits([m.item for m in matches], gold, syllabus),
        "false_positive_items": [
            {"key": m.item.key, "label": m.item.label, "name": m.item.name, "outside": m.item.key in outside}
            for m in matches if m.entry is None
        ],
        "missed_notions": [
            {"global_id": global_id, "entry": entry.id, "label": entry.label}
            for global_id, entry in mandatory.items() if global_id not in recovered
        ],
    }


_SUMMED = ("items", "hits", "mandatory_notions", "recovered", "type_matches", "outside_items", "outside_hits")


def total(cases: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """Sums of numerators and denominators, never means of percentages."""
    cases = list(cases)
    return {"cases": len(cases), **_with_ratios({name: sum(case[name] for case in cases) for name in _SUMMED})}


# --- Fusion (CP-14; thesis, 5.2.5.5) -----------------------------------------


def fusion(
    matched: Iterable[Sequence[Match]], compound_notions: frozenset[str] = frozenset()
) -> dict[str, Any]:
    """The fusion measures over the nodes of every case: each node gathers the
    global identifiers of the entries it consumed wherever it was an item."""
    nodes: dict[str, dict[str, Any]] = {}
    for matches in matched:
        for m in matches:
            if m.entry is not None:
                node = nodes.setdefault(m.item.key, {"label": m.item.label, "name": m.item.name, "global_ids": set()})
                node["global_ids"].add(m.entry.global_id)

    holders: dict[str, dict[str, list[str]]] = defaultdict(lambda: defaultdict(list))
    for key, node in nodes.items():
        for global_id in node["global_ids"]:
            holders[global_id][node["label"]].append(key)

    def described(key: str) -> dict[str, Any]:
        return {"key": key, "label": nodes[key]["label"], "name": nodes[key]["name"]}

    duplicates = [
        {"global_id": global_id, "label": label, "nodes": [described(key) for key in keys]}
        for global_id, by_label in sorted(holders.items())
        for label, keys in sorted(by_label.items()) if len(keys) > 1
    ]
    split = [
        {"global_id": global_id, "nodes": [described(key) for keys in by_label.values() for key in keys]}
        for global_id, by_label in sorted(holders.items()) if len(by_label) > 1
    ]
    wrong, excepted = [], []
    for key, node in nodes.items():
        if len(node["global_ids"]) < 2:
            continue
        # Not a wrong fusion if, compound headings aside, a single notion is left.
        left = node["global_ids"] - compound_notions
        (excepted if len(left) == 1 else wrong).append({**described(key), "global_ids": sorted(node["global_ids"])})
    return {
        "nodes_with_hits": len(nodes),
        "duplicated_notions": len({d["global_id"] for d in duplicates}),
        "surplus_nodes": sum(len(d["nodes"]) - 1 for d in duplicates),
        "split_notions": len(split),
        "wrong_fusions": len(wrong),
        "excepted_fusions": len(excepted),
        "duplicates": duplicates,
        "split": split,
        "wrong": wrong,
        "excepted": excepted,
    }


# --- The runs ----------------------------------------------------------------


@dataclass(frozen=True)
class Attempt:
    """A run that ended with something to judge. ``batch`` is the accepted batch,
    or the candidate one of a rejected run; None if that one is not readable."""

    run_id: int
    syllabus: str | None
    accepted: bool
    batch: Batch | None
    status: str = ""
    model: str | None = None
    prompt_version: str | None = None


def walk(
    attempts: Iterable[Attempt], reference: Mapping[str, tuple[str, str]], *, isolated: bool = False
) -> Iterator[tuple[Attempt, list[Item] | None]]:
    """Each attempt with its items, in the order of the runs. In a chain, every
    accepted batch adds its nodes to what the later ones may link; an isolated
    run sees the reference layer alone."""
    known: Known = dict(reference)
    for attempt in sorted(attempts, key=lambda a: a.run_id):
        if attempt.batch is None:
            yield attempt, None
            continue
        yield attempt, items_of(attempt.batch, reference if isolated else known)
        if attempt.accepted and not isolated:
            index_batch(known, attempt.batch)


def _run_fields(attempt: Attempt) -> dict[str, Any]:
    return {"run_id": attempt.run_id, "status": attempt.status, "model": attempt.model,
            "prompt_version": attempt.prompt_version}


def evaluate(
    gold: Gold,
    attempts: Sequence[Attempt],
    reference: Mapping[str, tuple[str, str]],
    *,
    isolated: bool = False,
    hide_held_out: bool = False,
    held_out: Sequence[str] = HELD_OUT,
    compound_headings: frozenset[str] = frozenset(),
) -> dict[str, Any]:
    hidden = set(held_out) if hide_held_out else set()
    cases: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    matched: list[list[Match]] = []
    warnings: list[str] = []
    accepted_syllabi: set[str] = set()
    rejections: Counter[str] = Counter()

    for attempt, items in walk(attempts, reference, isolated=isolated):
        syllabus = attempt.syllabus
        if syllabus not in gold.syllabi:
            if attempt.accepted:
                warnings.append(f"run {attempt.run_id} ({syllabus}) is not a test case; "
                                + ("skipped" if isolated else "its nodes count as existing"))
            continue
        if not isolated and syllabus in accepted_syllabi:
            warnings.append(f"run {attempt.run_id} comes after the accepted run of {syllabus}; not measured")
            continue
        if not attempt.accepted:
            rejections[syllabus] += 1
            if syllabus not in hidden:
                row = {"case": gold.case_of(syllabus), "syllabus": syllabus, **_run_fields(attempt),
                       "readable": items is not None}
                if items is not None:
                    measured = measure(match(items, gold, syllabus), gold, syllabus)
                    row.update({name: measured[name] for name in ("items", "hits", "false_positives", "precision")})
                rejected.append(row)
            continue
        accepted_syllabi.add(syllabus)
        if syllabus in hidden:
            continue
        matches = match(items, gold, syllabus)
        matched.append(matches)
        attempts_needed = None if isolated else rejections[syllabus] + 1
        if attempts_needed and attempts_needed > MAX_ATTEMPTS:
            warnings.append(f"{syllabus} needed {attempts_needed} attempts; the protocol allows {MAX_ATTEMPTS}")
        cases.append({"case": gold.case_of(syllabus), "syllabus": syllabus, **_run_fields(attempt),
                      "attempts": attempts_needed, "accepted": True,
                      **measure(matches, gold, syllabus, outside_of(attempt.batch))})

    if not isolated:
        # Rejected every time: out of the graph, and its mandatory notions were not recovered.
        for syllabus in gold.syllabi:
            if rejections[syllabus] and syllabus not in accepted_syllabi and syllabus not in hidden:
                cases.append({"case": gold.case_of(syllabus), "syllabus": syllabus, "run_id": None, "status": None,
                              "model": None, "prompt_version": None, "attempts": rejections[syllabus],
                              "accepted": False, **measure([], gold, syllabus)})
        cases.sort(key=lambda case: case["case"])

    # An isolated window may hold several runs of a syllabus: the total takes the last.
    counted = list({case["syllabus"]: case for case in cases}.values()) if isolated else cases
    totals = {
        "all": total(counted),
        "tuning": total(case for case in counted if case["syllabus"] not in held_out),
        "held_out": total(case for case in counted if case["syllabus"] in held_out),
    }
    attempted = accepted_syllabi | {syllabus for syllabus, n in rejections.items() if n}
    complete = not isolated and not hidden and attempted == set(gold.syllabi)
    precision = totals["all"]["precision"]
    if not isolated and not hidden and not complete:
        warnings.append("not every test case has a run in the window: no verdict, and the graph is not the final one")
    return {
        "measured_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "mode": "isolated" if isolated else "chain",
        "held_out": list(held_out),
        "hidden": sorted(hidden),
        "not_run": [s for s in gold.syllabi if s not in attempted and s not in hidden],
        "threshold": THRESHOLD,
        "passes": precision >= THRESHOLD if complete and precision is not None else None,
        "cases": cases,
        "totals": totals,
        "rejected_attempts": rejected,
        "fusion": None if isolated or hidden else fusion(
            matched, frozenset(e.global_id for e in gold.entries if e.id in compound_headings)),
        "warnings": warnings,
    }


# --- The reviewer's extraction -----------------------------------------------
# The rules are those of casos-de-prueba/protocolo-de-revision-de-la-anotacion.md.

REVIEWER, ANNOTATION = "revisor", "anotacion"
SAME_NOTION = "misma_nocion"
# The categories of the adjudication, by the side the unmatched row is on.
CATEGORIES = {
    REVIEWER: (SAME_NOTION, "omision", "criterio", "no_sustentada"),
    ANNOTATION: (SAME_NOTION, "no_extraida", "inclusion_indebida", "criterio"),
}
COMPARISON_COLUMNS = ("lado", "nombre", "id_global", "nivel", "texto", "comentario", "candidatos",
                      "categoria", "nocion", "alias_faltante", "justificacion", "regla")
PIPELINE_COLUMNS = ("clave", "tipo", "nombre", "candidatos", "fila_del_revisor", "justificacion")
# A notion in the list the author picks from: its identifier, then its label.
NOTION_SEPARATOR = " · "
MISSING_ALIAS_CHOICES = ("sí", "no")
CANDIDATES = 3
_SIMILAR = 0.5


@dataclass(frozen=True)
class ReviewRow:
    name: str
    kind: str = ""
    text: str = ""
    comment: str = ""


def extraction_path(directory: Path, syllabus: str) -> Path:
    return directory / f"extraccion_{syllabus}.tsv"


def comparison_path(directory: Path, syllabus: str) -> Path:
    return directory / f"comparacion_{syllabus}.xlsx"


def pipeline_comparison_path(directory: Path, syllabus: str) -> Path:
    return directory / f"comparacion_pipeline_{syllabus}.xlsx"


def _flat(value: Any) -> str:
    # A cell is one field of a tab-separated line.
    return " ".join(str(value).split()) if value is not None else ""


def write_tsv(path: Path, header: Sequence[str], rows: Iterable[Sequence[Any]]) -> None:
    """Never over a file that exists: it may hold the reviewer's rows or the author's adjudication."""
    with open(path, "x", encoding="utf-8", newline="") as file:
        for row in (header, *rows):
            file.write("\t".join(_flat(value) for value in row) + "\n")


def read_tsv(path: Path) -> list[dict[str, str]]:
    with open(path, encoding="utf-8", newline="") as file:
        return [{name: (value or "").strip() for name, value in row.items() if name}
                for row in csv.DictReader(file, delimiter="\t", quoting=csv.QUOTE_NONE)]


def write_adjudication(
    path: Path, header: Sequence[str], rows: Sequence[Sequence[Any]],
    choices: Mapping[str, Sequence[tuple[Sequence[str], Iterable[int]]]],
    listed: tuple[str, str, Sequence[str]] | None = None,
) -> None:
    """The file the author fills, as a workbook with drop-down lists. ``choices``
    gives, by column, each fixed list with the data rows (from 0) it applies
    to; ``listed`` is a column whose values come from a sheet of their own.
    Never over a file that exists, as with ``write_tsv``."""
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Font
    from openpyxl.worksheet.datavalidation import DataValidation

    if path.exists():
        raise FileExistsError(path)
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Adjudicación"
    sheet.append(list(header))
    for row in rows:
        sheet.append([_flat(value) for value in row])
    letter = {name: sheet.cell(row=1, column=index).column_letter for index, name in enumerate(header, start=1)}

    def restrict(column: str, formula: str, lines: Iterable[int]) -> None:
        # One range per run of consecutive lines.
        runs: list[list[int]] = []
        for line in sorted(lines):
            if runs and line == runs[-1][1] + 1:
                runs[-1][1] = line
            else:
                runs.append([line, line])
        if runs:
            validation = DataValidation(type="list", formula1=formula, allow_blank=True)
            for first, last in runs:
                validation.add(f"{letter[column]}{first}:{letter[column]}{last}")
            sheet.add_data_validation(validation)

    for column, lists in choices.items():
        for values, data_rows in lists:
            restrict(column, '"' + ",".join(values) + '"', (index + 2 for index in data_rows))
    if listed:
        column, title, values = listed
        source = workbook.create_sheet(title)
        source.append([column])
        for value in values:
            source.append([value])
        source.column_dimensions["A"].width = 70
        if values:
            restrict(column, f"'{title}'!$A$2:$A${len(values) + 1}", range(2, len(rows) + 2))
    for cell in sheet[1]:
        cell.font = Font(bold=True)
    for name, width in (("nombre", 40), ("texto", 50), ("candidatos", 45), ("nocion", 40),
                        ("fila_del_revisor", 40), ("justificacion", 50)):
        if name in letter:
            sheet.column_dimensions[letter[name]].width = width
    for line in sheet.iter_rows(min_row=2):
        for cell in line:
            cell.alignment = Alignment(wrap_text=True, vertical="top")
    sheet.freeze_panes = "C2"
    workbook.save(path)


def read_adjudication(path: Path) -> list[dict[str, str]]:
    """The first sheet of the file the author filled, one mapping per row."""
    from openpyxl import load_workbook

    rows = load_workbook(path, read_only=True, data_only=True).worksheets[0].iter_rows(values_only=True)
    header = [_flat(title) for title in next(rows, ())]
    return [{name: _flat(value) for name, value in zip(header, row) if name}
            for row in rows if any(_flat(value) for value in row)]


def _likeness(name: str, other: str) -> float:
    """Characters in common, or the words of the shorter name found in the
    longer one: "pila" is like "pila de llamada". Short words do not count."""
    words, other_words = ({word for word in n.split() if len(word) > 2} for n in (name, other))
    shared = len(words & other_words) / min(len(words), len(other_words)) if words and other_words else 0.0
    # Below a match of every character, so the same name still comes first.
    return max(SequenceMatcher(None, name, other).ratio(), 0.9 * shared)


def closest(name: str, options: Mapping[str, Iterable[str]]) -> list[str]:
    """The options whose names look most like ``name``, by their characters
    after normalizing. A hint to find a pair faster, never a category."""
    wanted = normalize_label(name)
    scored = [(max((_likeness(wanted, other) for other in names), default=0.0), option)
              for option, names in options.items()]
    scored.sort(key=lambda pair: -pair[0])
    return [option for score, option in scored[:CANDIDATES] if score >= _SIMILAR]


def export_review(workbook_path: Path, directory: Path, syllabi: Sequence[str]) -> list[Path]:
    """The reviewer's workbook as one file per syllabus, with its columns as
    delivered. Rows without content are left out."""
    from openpyxl import load_workbook

    written = []
    for sheet in load_workbook(workbook_path, read_only=True, data_only=True).worksheets:
        if sheet.title not in syllabi:
            continue
        rows = sheet.iter_rows(values_only=True)
        header = next((row for row in rows if _REVIEW_NAME in row), None)
        if header is None:
            raise ValueError(f"{workbook_path}: sheet {sheet.title} has no column {_REVIEW_NAME!r}")
        width = max(index for index, title in enumerate(header) if title) + 1
        # The first column is the row number the template already brings.
        filled = [row[:width] for row in rows if any(_flat(value) for value in row[1:width])]
        path = extraction_path(directory, sheet.title)
        write_tsv(path, header[:width], filled)
        written.append(path)
    return written


def read_review(directory: Path, syllabi: Sequence[str]) -> dict[str, list[ReviewRow]]:
    review = {}
    for syllabus in syllabi:
        path = extraction_path(directory, syllabus)
        if path.exists():
            review[syllabus] = [
                ReviewRow(row[_REVIEW_NAME], row.get(_REVIEW_KIND, ""), row.get(_REVIEW_TEXT, ""),
                          row.get(_REVIEW_COMMENT, ""))
                for row in read_tsv(path) if row.get(_REVIEW_NAME)
            ]
    return review


def _proportion(numerator: int, denominator: int) -> dict[str, Any]:
    return {"count": numerator, "of": denominator, "proportion": _ratio(numerator, denominator)}


def _is_marked(value: str) -> bool:
    return normalize_label(value) not in ("", "no")


def compare_review(
    gold: Gold, syllabus: str, rows: Sequence[ReviewRow], adjudication: Sequence[Mapping[str, str]] | None = None
) -> dict[str, Any]:
    """Reviewer against annotation, both ways, by normalized name: no type, no
    level, and no one-to-one. ``adjudication`` is the comparison file as the
    author filled it; without it, only the automatic matching is reported."""
    by_name: dict[str, ReviewRow] = {}
    for row in rows:
        by_name.setdefault(normalize_label(row.name), row)
    candidates_of = gold.candidates_of(syllabus)
    notions: dict[str, Entry] = {}
    for entry in gold.entries_of(syllabus):
        notions.setdefault(entry.global_id, entry)
    mandatory = set(gold.mandatory_notions_of(syllabus))
    extracted = {global_id for global_id in notions if gold.names[global_id] & by_name.keys()}
    registered = {name for name in by_name if name in candidates_of}
    # Descriptive: the reviewer has no rule for the type. A pair agrees if some
    # entry of the notion in the syllabus has the type the reviewer wrote.
    typed = [name for name in registered if by_name[name].kind.strip().lower() in KIND_OF.values()]
    agreeing = [name for name in typed
                if any(entry.kind == by_name[name].kind.strip().lower() for entry in candidates_of[name])]

    def level(global_id: str) -> str:
        return MANDATORY if global_id in mandatory else "aceptable"

    compared = {
        "syllabus": syllabus,
        "reviewer_rows": len(rows),
        "repeated_rows": len(rows) - len(by_name),
        "reviewer_registered": _proportion(len(registered), len(by_name)),
        "notions_extracted": _proportion(len(extracted), len(notions)),
        "mandatory_extracted": _proportion(len(extracted & mandatory), len(mandatory)),
        "acceptable_extracted": _proportion(len(extracted - mandatory), len(notions) - len(mandatory)),
        "type_agreement": _proportion(len(agreeing), len(typed)),
        "reviewer_only": [
            {"name": row.name, "text": row.text, "comment": row.comment}
            for name, row in by_name.items() if name not in registered
        ],
        "annotation_only": [
            {"global_id": global_id, "entry": entry.id, "label": entry.label, "level": level(global_id),
             "evidence": entry.evidence}
            for global_id, entry in notions.items() if global_id not in extracted
        ],
        "adjudicated": None,
    }
    if adjudication is None:
        return compared

    filled: dict[tuple[str, str], Mapping[str, str]] = {}
    for line in adjudication:
        side = line["lado"]
        if side not in CATEGORIES:
            raise ValueError(f"{syllabus}: unknown side {side!r}")
        if line["categoria"] and line["categoria"] not in CATEGORIES[side]:
            raise ValueError(f"{syllabus}: {line['nombre']!r} has the category {line['categoria']!r}; "
                             f"on the side {side} it is one of {', '.join(CATEGORIES[side])}")
        filled[side, normalize_label(line["nombre"]) if side == REVIEWER else line["id_global"]] = line

    counts = {side: Counter() for side in CATEGORIES}
    pending = missing_aliases = 0
    same: set[str] = set()
    for only in compared["reviewer_only"]:
        line = filled.get((REVIEWER, normalize_label(only["name"])), {})
        category = line.get("categoria", "")
        if category == SAME_NOTION:
            # As the author picked it from the list, or the bare identifier.
            notion = line["nocion"].split(NOTION_SEPARATOR)[0].strip()
            if notion not in notions:
                raise ValueError(f"{syllabus}: {only['name']!r} is the same as {line['nocion']!r}, "
                                 f"which is not a notion of the syllabus")
            same.add(notion)
            missing_aliases += _is_marked(line.get("alias_faltante", ""))
        counts[REVIEWER][category] += 1
        pending += not category
    for only in compared["annotation_only"]:
        # Paired by the author with a row of the reviewer: nothing else to classify.
        category = SAME_NOTION if only["global_id"] in same else filled.get(
            (ANNOTATION, only["global_id"]), {}).get("categoria", "")
        counts[ANNOTATION][category] += 1
        pending += not category
    compared["adjudicated"] = {
        "pending": pending,
        "reviewer_registered": _proportion(len(registered) + counts[REVIEWER][SAME_NOTION], len(by_name)),
        "notions_extracted": _proportion(len(extracted | same), len(notions)),
        "categories": {side: {category: counts[side][category] for category in CATEGORIES[side]}
                       for side in CATEGORIES},
        "missing_aliases": missing_aliases,
    }
    return compared


def notion_choices(gold: Gold, syllabus: str) -> dict[str, frozenset[str]]:
    """The notions of ``syllabus`` as the author picks them, each with its names."""
    choices: dict[str, frozenset[str]] = {}
    for entry in gold.entries_of(syllabus):
        choices.setdefault(f"{entry.global_id}{NOTION_SEPARATOR}{entry.label}", gold.names[entry.global_id])
    return choices


def comparison_rows(gold: Gold, compared: Mapping[str, Any]) -> list[list[str]]:
    """One row per discrepancy, with the columns of the adjudication left empty.
    A row of the reviewer lists the notions whose names look like it; a
    notion, the unmatched rows of the reviewer that look like it."""
    notions = notion_choices(gold, compared["syllabus"])
    rows = {d["name"]: {normalize_label(d["name"])} for d in compared["reviewer_only"]}
    return [
        *([REVIEWER, d["name"], "", "", d["text"], d["comment"], " | ".join(closest(d["name"], notions)),
           "", "", "", "", ""] for d in compared["reviewer_only"]),
        *([ANNOTATION, d["label"], d["global_id"], d["level"], d["evidence"], "",
           " | ".join(closest(d["label"], rows)), "", "", "", "", ""] for d in compared["annotation_only"]),
    ]


def write_comparison(path: Path, gold: Gold, compared: Mapping[str, Any]) -> None:
    rows = comparison_rows(gold, compared)
    write_adjudication(
        path, COMPARISON_COLUMNS, rows,
        {"categoria": [(categories, [i for i, row in enumerate(rows) if row[0] == side])
                       for side, categories in CATEGORIES.items()],
         "alias_faltante": [(MISSING_ALIAS_CHOICES, range(len(rows)))]},
        ("nocion", "Nociones", list(notion_choices(gold, compared["syllabus"]))),
    )


def pipeline_against_review(
    items: Sequence[Item], rows: Sequence[ReviewRow], adjudication: Sequence[Mapping[str, str]] | None = None
) -> dict[str, Any]:
    """The precision of a batch against the reviewer's names, without the
    annotation. With ``adjudication``, an item also hits if the author wrote
    the row of the reviewer that names the same."""
    names = {normalize_label(row.name) for row in rows}
    found = [item for item in items if normalize_label(item.name) in names]
    compared = {
        "pipeline_registered": _proportion(len(found), len(items)),
        "pipeline_only": [
            {"key": item.key, "label": item.label, "name": item.name}
            for item in items if normalize_label(item.name) not in names
        ],
        "adjudicated": None,
    }
    if adjudication is not None:
        paired = {line["clave"]: line["fila_del_revisor"] for line in adjudication if line["fila_del_revisor"]}
        for key, name in paired.items():
            if normalize_label(name) not in names:
                raise ValueError(f"{key}: {name!r} is not a row of the reviewer")
        same = sum(only["key"] in paired for only in compared["pipeline_only"])
        compared["adjudicated"] = {"pipeline_registered": _proportion(len(found) + same, len(items))}
    return compared


def pipeline_comparison_rows(compared: Mapping[str, Any], rows: Sequence[ReviewRow]) -> list[list[str]]:
    names = {row.name: {normalize_label(row.name)} for row in rows}
    return [[d["key"], d["label"], d["name"], " | ".join(closest(d["name"], names)), "", ""]
            for d in compared["pipeline_only"]]


def write_pipeline_comparison(path: Path, compared: Mapping[str, Any], rows: Sequence[ReviewRow]) -> None:
    write_adjudication(path, PIPELINE_COLUMNS, pipeline_comparison_rows(compared, rows), {},
                       ("fila_del_revisor", "Filas del revisor", list(dict.fromkeys(row.name for row in rows))))


def compare_reviewers(rows: Sequence[ReviewRow], others: Sequence[ReviewRow]) -> dict[str, Any]:
    """Two reviewers of one syllabus by normalized name, both ways: no
    annotation, no type, no adjudication. Rows that normalize alike count once."""
    names = {normalize_label(row.name) for row in rows}
    other = {normalize_label(row.name) for row in others}
    shared = names & other
    return {"names": len(names), "other_names": len(other), "shared": len(shared),
            "other_has": _proportion(len(shared), len(names)),
            "has_of_other": _proportion(len(shared), len(other))}


def agreement(
    rows_of: Mapping[str, Sequence[ReviewRow]], others_of: Mapping[str, Sequence[ReviewRow]]
) -> dict[str, Any]:
    syllabi = [{"syllabus": syllabus, **compare_reviewers(rows, others_of[syllabus])}
               for syllabus, rows in rows_of.items() if syllabus in others_of]
    return {
        "measured_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "syllabi": syllabi,
        "totals": {name: _proportion(sum(s[name]["count"] for s in syllabi), sum(s[name]["of"] for s in syllabi))
                   for name in ("other_has", "has_of_other")},
    }


def review(
    gold: Gold,
    rows_of: Mapping[str, Sequence[ReviewRow]],
    attempts: Sequence[Attempt] = (),
    reference: Mapping[str, tuple[str, str]] | None = None,
    adjudications: Mapping[str, Sequence[Mapping[str, str]]] | None = None,
    pipeline_adjudications: Mapping[str, Sequence[Mapping[str, str]]] | None = None,
) -> dict[str, Any]:
    accepted: dict[str, tuple[Attempt, list[Item]]] = {}
    for attempt, items in walk(attempts, reference or {}):
        if attempt.accepted and attempt.syllabus not in accepted:
            accepted[attempt.syllabus] = (attempt, items)
    syllabi = []
    for syllabus in gold.syllabi:
        if syllabus not in rows_of:
            continue
        compared = compare_review(gold, syllabus, rows_of[syllabus], (adjudications or {}).get(syllabus))
        compared["pipeline"] = None
        if syllabus in accepted:
            attempt, items = accepted[syllabus]
            compared["pipeline"] = {"run_id": attempt.run_id, **pipeline_against_review(
                items, rows_of[syllabus], (pipeline_adjudications or {}).get(syllabus))}
        syllabi.append(compared)

    def summed(name: str, source: Sequence[Mapping[str, Any] | None]) -> dict[str, Any] | None:
        # A total only where every syllabus has the figure.
        if not source or any(part is None for part in source):
            return None
        return _proportion(sum(p[name]["count"] for p in source), sum(p[name]["of"] for p in source))

    pipelines = [s["pipeline"] for s in syllabi]
    adjudicated = [s["adjudicated"] for s in syllabi]
    pipelines_adjudicated = [p and p["adjudicated"] for p in pipelines]
    return {
        "measured_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "syllabi": syllabi,
        "totals": {
            **{name: summed(name, syllabi) for name in (
                "reviewer_registered", "notions_extracted", "mandatory_extracted", "acceptable_extracted",
                "type_agreement")},
            "pipeline_registered": summed("pipeline_registered", pipelines),
            "adjudicated": {
                "reviewer_registered": summed("reviewer_registered", adjudicated),
                "notions_extracted": summed("notions_extracted", adjudicated),
                "pipeline_registered": summed("pipeline_registered", pipelines_adjudicated),
            },
        },
    }


# --- Output ------------------------------------------------------------------


def _cell(value: Any) -> str:
    if value is None:
        return "—"
    if isinstance(value, bool):
        return "yes" if value else "no"
    return f"{value:.1%}" if isinstance(value, float) else str(value)


def _table(header: Sequence[str], rows: Iterable[Sequence[Any]]) -> list[str]:
    return ["| " + " | ".join(header) + " |", "|" + "---|" * len(header),
            *("| " + " | ".join(_cell(value) for value in row) + " |" for row in rows)]


_MEASURES = ("items", "hits", "false_positives", "precision", "mandatory_notions", "recovered", "recall", "f1",
             "type_agreement")


def markdown(report: Mapping[str, Any]) -> str:
    header = ("Case", "Syllabus", "Run", "Attempts", "Items", "Hits", "False positives", "Precision",
              "Mandatory notions", "Recovered", "Recall", "F1", "Type agreement", "Most hits")
    rows = [(c["case"], c["syllabus"], c["run_id"], c["attempts"], *(c[m] for m in _MEASURES), c["most_hits"])
            for c in report["cases"]]
    rows += [(f"Total: {name}", f"{t['cases']} cases", None, None, *(t[m] for m in _MEASURES), None)
             for name, t in report["totals"].items() if t["cases"]]
    lines = [f"Mode: {report['mode']}.", "", *_table(header, rows), ""]
    everything = report["totals"]["all"]
    if everything["outside_items"]:
        lines.append(
            f"Diagnostic: {everything['outside_items']} items are concepts the batches only require or relate "
            f"({everything['outside_hits']} hits); without them the precision is "
            f"{_cell(everything['placed_precision'])}.")
    if report["hidden"]:
        lines.append(f"Hidden, not evaluated: {', '.join(report['hidden'])}.")
    if report["not_run"]:
        lines.append(f"Without a run in the window: {', '.join(report['not_run'])}.")
    if report["passes"] is not None:
        lines.append(f"Indicator of R4 (precision >= {THRESHOLD:.0%} over the 13 cases): "
                     f"{'passed' if report['passes'] else 'NOT passed'}.")
    if report["rejected_attempts"]:
        lines += ["", "Rejected attempts, apart from every total:", *_table(
            ("Case", "Syllabus", "Run", "Readable", "Items", "Hits", "Precision"),
            [(r["case"], r["syllabus"], r["run_id"], r["readable"], r.get("items"), r.get("hits"), r.get("precision"))
             for r in report["rejected_attempts"]])]
    if report["fusion"]:
        f = report["fusion"]
        lines += ["", f"CP-14 over {f['nodes_with_hits']} nodes with a hit: {f['duplicated_notions']} duplicated "
                  f"notions ({f['surplus_nodes']} surplus nodes), {f['split_notions']} split notions, "
                  f"{f['wrong_fusions']} wrong fusions, {f['excepted_fusions']} excepted."]
    lines += [f"Warning: {warning}." for warning in report["warnings"]]
    return "\n".join(lines)


def agreement_markdown(report: Mapping[str, Any]) -> str:
    def cells(part: Mapping[str, Any]) -> tuple:
        return f"{part['count']} / {part['of']}", part["proportion"]

    rows = [(s["syllabus"], s["names"], s["other_names"], s["shared"], *cells(s["other_has"]),
             *cells(s["has_of_other"])) for s in report["syllabi"]]
    t = report["totals"]
    rows.append(("Total", None, None, None, *cells(t["other_has"]), *cells(t["has_of_other"])))
    return "\n".join(_table(("Syllabus", "Names", "Other's names", "Shared", "Names the other has", "%",
                              "Other's names this one has", "%"), rows))


def review_markdown(report: Mapping[str, Any]) -> str:
    def cells(*parts: Mapping[str, Any] | None) -> tuple:
        return tuple(value for part in parts
                     for value in ((f"{part['count']} / {part['of']}", part["proportion"]) if part else (None, None)))

    measures = ("reviewer_registered", "notions_extracted", "mandatory_extracted", "acceptable_extracted",
                "type_agreement")
    header = ("Syllabus", "Reviewer rows", "Repeated", "Reviewer names the annotation has", "%",
              "Notions the reviewer extracted", "%", "Mandatory", "%", "Acceptable", "%", "Same type", "%",
              "Items the reviewer has", "%")
    rows = [(s["syllabus"], s["reviewer_rows"], s["repeated_rows"], *cells(*(s[m] for m in measures)),
             *cells(s["pipeline"] and s["pipeline"]["pipeline_registered"])) for s in report["syllabi"]]
    t = report["totals"]
    rows.append(("Total", None, None, *cells(*(t[m] for m in measures)), *cells(t["pipeline_registered"])))
    lines = _table(header, rows)

    after = [(s["syllabus"], s["adjudicated"], s["pipeline"] and s["pipeline"]["adjudicated"])
             for s in report["syllabi"]]
    if any(adjudicated or pipeline for _, adjudicated, pipeline in after):
        lines += ["", "After the adjudication:", *_table(
            ("Syllabus", "Pending", "Reviewer names the annotation has", "%", "Notions the reviewer extracted", "%",
             "Missing aliases", "Items the reviewer has", "%"),
            [*((syllabus, a and a["pending"], *cells(a and a["reviewer_registered"], a and a["notions_extracted"]),
                a and a["missing_aliases"], *cells(p and p["pipeline_registered"])) for syllabus, a, p in after),
             ("Total", None, *cells(t["adjudicated"]["reviewer_registered"], t["adjudicated"]["notions_extracted"]),
              None, *cells(t["adjudicated"]["pipeline_registered"]))])]
        for side in CATEGORIES:
            lines += ["", f"Categories, side {side}:", *_table(
                ("Syllabus", *CATEGORIES[side]),
                [(syllabus, *(a["categories"][side][c] for c in CATEGORIES[side])) for syllabus, a, _ in after if a])]
    return "\n".join(lines)


# --- Reading the stores ------------------------------------------------------


def read_attempts(operational_db: Path, facts_dir: Path, first: int, last: int | None) -> list[Attempt]:
    """The runs of the window that left something to judge: those with a file in
    the fact store, and the rejected ones with their candidate batch."""
    from iekg.fact_store import FactStore
    from iekg.operational_store import OperationalStore

    facts = FactStore(facts_dir)
    written = set(facts.run_ids())
    attempts = []
    with OperationalStore(operational_db) as store:
        for run in store.list_runs():
            if run.id < first or (last is not None and run.id > last):
                continue
            fields = {"run_id": run.id, "syllabus": run.course_code, "status": run.status, "model": run.model,
                      "prompt_version": run.prompt_version}
            if run.id in written:
                attempts.append(Attempt(accepted=True, batch=facts.load(run.id).batch, **fields))
            elif run.status == REJECTED:
                attempts.append(Attempt(accepted=False, batch=store.rejected_output_of(run.id)[0], **fields))
    return attempts


def read_reference(backbone: Path) -> Known:
    """The nodes of the reference layer, by the projection the load uses."""
    from iekg.build_tools.projection import project_backbone, read_turtle

    known: Known = {}
    index_batch(known, project_backbone(read_turtle(backbone)))
    return known


def _write(report: Mapping[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("command", choices=("cases", "review", "agreement"))
    parser.add_argument("--from-run", type=int, default=1, help="first run of the window (default: 1)")
    parser.add_argument("--to-run", type=int, help="last run of the window (default: the latest)")
    parser.add_argument("--isolated", action="store_true",
                        help="cases: measure each run alone, as made over the reference layer")
    parser.add_argument("--hide-held-out", action="store_true",
                        help=f"cases: do not evaluate nor write {' and '.join(HELD_OUT)}")
    parser.add_argument("--gold", type=Path, default=GOLD)
    parser.add_argument("--compound-headings", type=Path, default=COMPOUND_HEADINGS)
    parser.add_argument("--review-dir", type=Path, default=REVIEW_DIR,
                        help="review, agreement: where the extraction and the comparison files are")
    parser.add_argument("--other-review-dir", type=Path,
                        help="agreement: where the other reviewer's extraction is")
    parser.add_argument("--workbook", type=Path,
                        help="review: the workbook the reviewer filled; exported once to the review directory")
    parser.add_argument("--facts-dir", type=Path, default=Path("var/facts"))
    parser.add_argument("--operational-db", type=Path, default=Path("var/operational.sqlite"))
    parser.add_argument("--backbone", type=Path, default=Path("ontology/backbone_cs2023.ttl"))
    parser.add_argument("--output-dir", type=Path, default=MEASUREMENTS)
    args = parser.parse_args()

    gold = load_gold(args.gold)
    stamp = f"{datetime.now():%Y%m%d-%H%M%S}"
    if args.command == "agreement":
        if args.other_review_dir is None:
            parser.error("agreement needs --other-review-dir")
        report = {"review_dir": str(args.review_dir), "other_review_dir": str(args.other_review_dir),
                  **agreement(read_review(args.review_dir, gold.syllabi),
                              read_review(args.other_review_dir, gold.syllabi))}
        output = args.output_dir / f"agreement-{stamp}.json"
        _write(report, output)
        print(agreement_markdown(report))
        print(f"\nReport written to {output}")
        return 0
    source = {"gold": str(args.gold), "gold_meta": gold.meta, "from_run": args.from_run, "to_run": args.to_run}
    # No store, no runs: the review still compares the reviewer with the annotation.
    attempts = (read_attempts(args.operational_db, args.facts_dir, args.from_run, args.to_run)
                if args.operational_db.exists() else [])
    reference = read_reference(args.backbone)

    if args.command == "review":
        directory = args.review_dir
        if args.workbook:
            for path in export_review(args.workbook, directory, gold.syllabi):
                print(f"Extraction exported to {path}")
        rows_of = read_review(directory, gold.syllabi)
        if not rows_of:
            print(f"No extraction in {directory}; pass --workbook with the one the reviewer filled")
            return 2

        def filled(path_of) -> dict[str, list[dict[str, str]]]:
            return {s: read_adjudication(path_of(directory, s)) for s in rows_of if path_of(directory, s).exists()}

        report = {**source, **review(gold, rows_of, attempts, reference,
                                     filled(comparison_path), filled(pipeline_comparison_path))}
        # The files the author fills are written once and only read from then on.
        for compared in report["syllabi"]:
            syllabus = compared["syllabus"]
            path = comparison_path(directory, syllabus)
            if not path.exists():
                write_comparison(path, gold, compared)
                print(f"To adjudicate: {path}")
            path = pipeline_comparison_path(directory, syllabus)
            if compared["pipeline"] is not None and not path.exists():
                write_pipeline_comparison(path, compared["pipeline"], rows_of[syllabus])
                print(f"To adjudicate: {path}")
        output = args.output_dir / f"review-{stamp}.json"
        _write(report, output)
        print(review_markdown(report))
        print(f"\nReport written to {output}")
        return 0

    report = {**source, **evaluate(
        gold, attempts, reference, isolated=args.isolated, hide_held_out=args.hide_held_out,
        compound_headings=load_compound_headings(args.compound_headings))}
    output = args.output_dir / f"cp-extraction-{stamp}.json"
    _write(report, output)
    print(markdown(report))
    print(f"\nReport written to {output}")
    return 1 if report["passes"] is False else 0


if __name__ == "__main__":
    sys.exit(main())
