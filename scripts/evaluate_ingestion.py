"""Development aid: measure the extraction test cases, CP-01 to CP-14.

Not an entry point of the system. It reads the accepted batches from the fact
store and compares them with the reference annotation, by the matching rules
of the thesis (section 5.2.5). How each measure is computed, and what the
thesis leaves open, is in casos-de-prueba/calculo-de-las-medidas-del-evaluador.md.

    uv run python scripts/evaluate_ingestion.py cases --from-run 5
    uv run python scripts/evaluate_ingestion.py cases --isolated --hide-held-out
    uv run python scripts/evaluate_ingestion.py review --from-run 5

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
from functools import cached_property
from pathlib import Path
from typing import Any

from iekg.core.batch import Batch
from iekg.graph_schema import CONCEPT, PREF_LABEL_ES, TOPIC
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
REVIEW = Path("casos-de-prueba/revision/hoja-de-extraccion.xlsx")
MEASUREMENTS = Path("var/measurements")

_REVIEW_NAME, _REVIEW_TEXT, _REVIEW_COMMENT = "Tema o concepto", "Texto del sílabo", "Comentario"


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
    precision = _ratio(counts["hits"], counts["items"])
    recall = _ratio(counts["recovered"], counts["mandatory_notions"])
    return {
        **counts,
        "false_positives": counts["items"] - counts["hits"],
        "precision": precision,
        "recall": recall,
        "f1": _f1(precision, recall),
        "type_agreement": _ratio(counts["type_matches"], counts["hits"]),
    }


def measure(matches: Sequence[Match], gold: Gold, syllabus: str) -> dict[str, Any]:
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
        }),
        "most_hits": most_hits([m.item for m in matches], gold, syllabus),
        "false_positive_items": [
            {"key": m.item.key, "label": m.item.label, "name": m.item.name} for m in matches if m.entry is None
        ],
        "missed_notions": [
            {"global_id": global_id, "entry": entry.id, "label": entry.label}
            for global_id, entry in mandatory.items() if global_id not in recovered
        ],
    }


_SUMMED = ("items", "hits", "mandatory_notions", "recovered", "type_matches")


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
                      "attempts": attempts_needed, "accepted": True, **measure(matches, gold, syllabus)})

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


@dataclass(frozen=True)
class ReviewRow:
    name: str
    text: str = ""
    comment: str = ""


def read_review(path: Path, syllabi: Sequence[str]) -> dict[str, list[ReviewRow]]:
    """The reviewer's rows, from the sheets named after a syllabus."""
    from openpyxl import load_workbook

    workbook = load_workbook(path, read_only=True, data_only=True)
    review = {}
    for sheet in workbook.worksheets:
        if sheet.title not in syllabi:
            continue
        rows = sheet.iter_rows(values_only=True)
        header = next((row for row in rows if _REVIEW_NAME in row), None)
        if header is None:
            raise ValueError(f"{path}: sheet {sheet.title} has no column {_REVIEW_NAME!r}")
        column = {title: index for index, title in enumerate(header) if title}

        def cell(row: tuple, title: str) -> str:
            value = row[column[title]] if title in column and column[title] < len(row) else None
            return str(value).strip() if value is not None else ""

        review[sheet.title] = [
            ReviewRow(cell(row, _REVIEW_NAME), cell(row, _REVIEW_TEXT), cell(row, _REVIEW_COMMENT))
            for row in rows if cell(row, _REVIEW_NAME)
        ]
    return review


def _proportion(numerator: int, denominator: int) -> dict[str, Any]:
    return {"count": numerator, "of": denominator, "proportion": _ratio(numerator, denominator)}


def compare_review(gold: Gold, syllabus: str, rows: Sequence[ReviewRow]) -> dict[str, Any]:
    """Reviewer against annotation, both ways, by normalized name: no type, no
    level, and no one-to-one."""
    by_name: dict[str, ReviewRow] = {}
    for row in rows:
        by_name.setdefault(normalize_label(row.name), row)
    candidates_of = gold.candidates_of(syllabus)
    notions: dict[str, Entry] = {}
    for entry in gold.entries_of(syllabus):
        notions.setdefault(entry.global_id, entry)
    extracted = {global_id for global_id in notions if gold.names[global_id] & by_name.keys()}
    registered = [name for name in by_name if name in candidates_of]
    return {
        "syllabus": syllabus,
        "reviewer_rows": len(rows),
        "repeated_rows": len(rows) - len(by_name),
        "reviewer_registered": _proportion(len(registered), len(by_name)),
        "notions_extracted": _proportion(len(extracted), len(notions)),
        "reviewer_only": [
            {"name": row.name, "text": row.text, "comment": row.comment}
            for name, row in by_name.items() if name not in candidates_of
        ],
        "annotation_only": [
            {"global_id": global_id, "entry": entry.id, "label": entry.label, "level": entry.level,
             "evidence": entry.evidence}
            for global_id, entry in notions.items() if global_id not in extracted
        ],
    }


def pipeline_against_review(items: Sequence[Item], rows: Sequence[ReviewRow]) -> dict[str, Any]:
    """The precision of a batch against the reviewer's names, without the annotation."""
    names = {normalize_label(row.name) for row in rows}
    found = [item for item in items if normalize_label(item.name) in names]
    return {
        "pipeline_registered": _proportion(len(found), len(items)),
        "pipeline_only": [
            {"key": item.key, "label": item.label, "name": item.name}
            for item in items if normalize_label(item.name) not in names
        ],
    }


def review(
    gold: Gold,
    rows_of: Mapping[str, Sequence[ReviewRow]],
    attempts: Sequence[Attempt] = (),
    reference: Mapping[str, tuple[str, str]] | None = None,
) -> dict[str, Any]:
    accepted: dict[str, tuple[Attempt, list[Item]]] = {}
    for attempt, items in walk(attempts, reference or {}):
        if attempt.accepted and attempt.syllabus not in accepted:
            accepted[attempt.syllabus] = (attempt, items)
    syllabi = []
    for syllabus in gold.syllabi:
        if syllabus not in rows_of:
            continue
        compared = compare_review(gold, syllabus, rows_of[syllabus])
        compared["pipeline"] = None
        if syllabus in accepted:
            attempt, items = accepted[syllabus]
            compared["pipeline"] = {"run_id": attempt.run_id, **pipeline_against_review(items, rows_of[syllabus])}
        syllabi.append(compared)

    def summed(name: str, source: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
        parts = [part[name] for part in source]
        return _proportion(sum(p["count"] for p in parts), sum(p["of"] for p in parts))

    with_pipeline = [s["pipeline"] for s in syllabi if s["pipeline"]]
    return {
        "measured_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "syllabi": syllabi,
        "totals": {
            "reviewer_registered": summed("reviewer_registered", syllabi),
            "notions_extracted": summed("notions_extracted", syllabi),
            "pipeline_registered": summed("pipeline_registered", with_pipeline) if with_pipeline else None,
        },
    }


def discrepancy_rows(report: Mapping[str, Any]) -> list[list[str]]:
    """One row per discrepancy, with the category left for the adjudication."""
    rows = [["silabo", "lado", "nombre", "id_global", "nivel", "texto", "comentario", "categoria"]]
    for syllabus in report["syllabi"]:
        code = syllabus["syllabus"]
        rows += [[code, "revisor", d["name"], "", "", d["text"], d["comment"], ""] for d in syllabus["reviewer_only"]]
        rows += [[code, "anotacion", d["label"], d["global_id"], d["level"], d["evidence"], "", ""]
                 for d in syllabus["annotation_only"]]
    return rows


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


def review_markdown(report: Mapping[str, Any]) -> str:
    def cells(part: Mapping[str, Any] | None) -> tuple:
        return (f"{part['count']} / {part['of']}", part["proportion"]) if part else (None, None)

    header = ("Syllabus", "Reviewer rows", "Repeated", "Reviewer names the annotation has", "%",
              "Notions the reviewer extracted", "%", "Items the reviewer has", "%")
    rows = [(s["syllabus"], s["reviewer_rows"], s["repeated_rows"], *cells(s["reviewer_registered"]),
             *cells(s["notions_extracted"]), *cells(s["pipeline"] and s["pipeline"]["pipeline_registered"]))
            for s in report["syllabi"]]
    t = report["totals"]
    rows.append(("Total", None, None, *cells(t["reviewer_registered"]), *cells(t["notions_extracted"]),
                 *cells(t["pipeline_registered"])))
    return "\n".join(_table(header, rows))


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
    parser.add_argument("command", choices=("cases", "review"))
    parser.add_argument("--from-run", type=int, default=1, help="first run of the window (default: 1)")
    parser.add_argument("--to-run", type=int, help="last run of the window (default: the latest)")
    parser.add_argument("--isolated", action="store_true",
                        help="cases: measure each run alone, as made over the reference layer")
    parser.add_argument("--hide-held-out", action="store_true",
                        help=f"cases: do not evaluate nor write {' and '.join(HELD_OUT)}")
    parser.add_argument("--gold", type=Path, default=GOLD)
    parser.add_argument("--compound-headings", type=Path, default=COMPOUND_HEADINGS)
    parser.add_argument("--review", type=Path, default=REVIEW, help="review: the reviewer's workbook")
    parser.add_argument("--facts-dir", type=Path, default=Path("var/facts"))
    parser.add_argument("--operational-db", type=Path, default=Path("var/operational.sqlite"))
    parser.add_argument("--backbone", type=Path, default=Path("ontology/backbone_cs2023.ttl"))
    parser.add_argument("--output-dir", type=Path, default=MEASUREMENTS)
    args = parser.parse_args()

    gold = load_gold(args.gold)
    source = {"gold": str(args.gold), "gold_meta": gold.meta, "from_run": args.from_run, "to_run": args.to_run}
    # No store, no runs: the review still compares the reviewer with the annotation.
    attempts = (read_attempts(args.operational_db, args.facts_dir, args.from_run, args.to_run)
                if args.operational_db.exists() else [])
    reference = read_reference(args.backbone)
    stamp = f"{datetime.now():%Y%m%d-%H%M%S}"

    if args.command == "review":
        report = {**source, **review(gold, read_review(args.review, gold.syllabi), attempts, reference)}
        output = args.output_dir / f"review-{stamp}.json"
        _write(report, output)
        discrepancies = args.output_dir / f"review-discrepancies-{stamp}.tsv"
        with open(discrepancies, "w", encoding="utf-8", newline="") as file:
            csv.writer(file, delimiter="\t", quoting=csv.QUOTE_NONE, escapechar="\\").writerows(
                [[cell.replace("\t", " ").replace("\n", " ") for cell in row] for row in discrepancy_rows(report)])
        print(review_markdown(report))
        print(f"\nReport written to {output}\nDiscrepancies written to {discrepancies}")
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
