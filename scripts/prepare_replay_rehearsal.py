"""Development aid: prepare the stores of a CA-11 rehearsal with the simulated provider.

Copies an operational store, its facts and its documents into a new folder, as
they were just before run ``--run`` started: that run and every later one are
removed, with their discards, outputs and audit reports. The PDF of that run is
left beside the stores, named by its course code, to be uploaded again. Then
``load`` and ``reapply`` on those stores give the graph that run saw, and
``scripts/replay_provider.py`` can answer it with the output it got.

The source is only read. The procedure is in ``web/README.md``.

    uv run python scripts/prepare_replay_rehearsal.py --source var/medicion-r4 --run 14 --target var/ensayo-ca11
"""

from __future__ import annotations

import argparse
import shutil
import sqlite3
import sys
from dataclasses import dataclass
from pathlib import Path

OPERATIONAL_DB = "operational.sqlite"


@dataclass(frozen=True)
class Prepared:
    kept_runs: int
    upload: Path
    course_code: str
    course_name: str
    resource_type: str


def _copy_store(source: Path, target: Path) -> None:
    reader = sqlite3.connect(f"{source.resolve().as_uri()}?mode=ro", uri=True)
    try:
        writer = sqlite3.connect(target)
        try:
            reader.backup(writer)
        finally:
            writer.close()
    finally:
        reader.close()


def _cut_store(path: Path, run_id: int) -> tuple[tuple, list[int], list[str]]:
    """Remove ``run_id`` and later runs; return what the cut run declared, the kept runs and their documents."""
    connection = sqlite3.connect(path)
    try:
        row = connection.execute(
            "SELECT resource_key, course_code, course_name, resource_type FROM runs WHERE id = ?", (run_id,)
        ).fetchone()
        if row is None:
            raise SystemExit(f"error: run {run_id} does not exist in {path}")
        removed = [r[0] for r in connection.execute("SELECT id FROM runs WHERE id >= ?", (run_id,))]
        marks = ", ".join("?" * len(removed))
        attached = [r[0] for r in connection.execute(
            f"SELECT audit_report_id FROM runs WHERE id IN ({marks}) AND audit_report_id IS NOT NULL", removed)]
        # Reports from the first one a removed run closed on, and any that names a removed run.
        reports = {r[0] for r in connection.execute(
            f"SELECT id FROM audit_reports WHERE run_id IN ({marks})", [str(i) for i in removed])}
        if attached:
            reports |= {r[0] for r in connection.execute(
                "SELECT id FROM audit_reports WHERE id >= ?", (min(attached),))}
        with connection:
            for table in ("discards", "rejected_outputs", "model_outputs"):
                connection.execute(f"DELETE FROM {table} WHERE run_id IN ({marks})", removed)
            connection.execute(f"DELETE FROM runs WHERE id IN ({marks})", removed)
            if reports:
                report_marks = ", ".join("?" * len(reports))
                connection.execute(f"DELETE FROM audit_rule_results WHERE report_id IN ({report_marks})", list(reports))
                connection.execute(f"DELETE FROM audit_reports WHERE id IN ({report_marks})", list(reports))
            # The next run and report take the numbers the removed ones had.
            for table in ("runs", "audit_reports"):
                connection.execute(
                    f"UPDATE sqlite_sequence SET seq = (SELECT coalesce(max(id), 0) FROM {table}) WHERE name = ?",
                    (table,),
                )
        kept = [r[0] for r in connection.execute("SELECT id FROM runs ORDER BY id")]
        keys = [r[0] for r in connection.execute("SELECT resource_key FROM runs")]
    finally:
        connection.close()
    return row, kept, keys


def prepare(source: Path, run_id: int, target: Path) -> Prepared:
    if target.exists() and any(target.iterdir()):
        raise SystemExit(f"error: {target} is not empty; choose a new folder")
    store = source / OPERATIONAL_DB
    if not store.is_file():
        raise SystemExit(f"error: no {OPERATIONAL_DB} in {source}")
    (target / "facts").mkdir(parents=True, exist_ok=True)
    (target / "documents").mkdir(exist_ok=True)
    _copy_store(store, target / OPERATIONAL_DB)
    (resource_key, course_code, course_name, resource_type), kept, keys = _cut_store(target / OPERATIONAL_DB, run_id)
    for kept_id in kept:
        facts = source / "facts" / f"run-{kept_id:06d}.json"
        if facts.is_file():
            shutil.copy2(facts, target / "facts" / facts.name)
    for key in keys:
        document = source / "documents" / f"{key}.pdf"
        if document.is_file():
            shutil.copy2(document, target / "documents" / document.name)
    upload = target / f"{course_code or 'document'}.pdf"
    shutil.copy2(source / "documents" / f"{resource_key}.pdf", upload)
    return Prepared(len(kept), upload, course_code or "", course_name or "", resource_type)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--source", type=Path, required=True, help="folder with operational.sqlite, facts/, documents/")
    parser.add_argument("--run", type=int, required=True, help="the run to rehearse; it and later runs are removed")
    parser.add_argument("--target", type=Path, required=True, help="a new folder for the rehearsal stores")
    arguments = parser.parse_args(argv)
    prepared = prepare(arguments.source, arguments.run, arguments.target)
    print(f"Prepared {arguments.target}: {prepared.kept_runs} runs kept, run {arguments.run} and later removed.")
    print(f"To upload: {prepared.upload}  ({prepared.resource_type}, {prepared.course_code}, {prepared.course_name})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
