"""Operational store (SQLite): run state, discards and audit reports.

Lives outside the graph database, so a load does not erase the evidence of
AC-01 and AC-02. It holds the ingestion runs, the discards of the rejected
ones and the audit reports. The latest report is what the worker's audit gate
reads (ADR-007).

A write path opens its report before it touches the graph and completes it
with the audit. A path that stops in between leaves its report open, and an
open report is not clean: the gate stays closed until a later path completes
a clean one.
"""

import json
import sqlite3
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from types import TracebackType

from iekg.core.auditor import AuditReport, RuleResult
from iekg.core.batch import Batch, batch_from_data, batch_to_data

# Write paths that close with an audit (ADR-005).
LOAD = "load"
INGESTION = "ingestion"
REAPPLICATION = "reapplication"
ORIGINS = (LOAD, INGESTION, REAPPLICATION)

# Run states (ADR-010).
PENDING = "pending"
RUNNING = "running"
COMPLETED = "completed"
REJECTED = "rejected"
FAILED = "failed"
WRITTEN_NOT_PERSISTED = "written_not_persisted"
STOPPED_BY_AUDIT = "stopped_by_audit"
RUN_STATES = (PENDING, RUNNING, COMPLETED, REJECTED, FAILED, WRITTEN_NOT_PERSISTED, STOPPED_BY_AUDIT)


def _in(values: Iterable[str]) -> str:
    return ", ".join(f"'{value}'" for value in values)


_SCHEMA = f"""
CREATE TABLE IF NOT EXISTS audit_reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL,
    origin TEXT NOT NULL CHECK (origin IN ({_in(ORIGINS)})),
    run_id TEXT,
    completed_at TEXT,
    violations INTEGER,
    CHECK ((completed_at IS NULL) = (violations IS NULL))
);
CREATE TABLE IF NOT EXISTS audit_rule_results (
    report_id INTEGER NOT NULL REFERENCES audit_reports (id),
    rule TEXT NOT NULL,
    violations INTEGER NOT NULL,
    sample TEXT NOT NULL,
    PRIMARY KEY (report_id, rule)
);
CREATE TABLE IF NOT EXISTS runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    status TEXT NOT NULL CHECK (status IN ({_in(RUN_STATES)})),
    created_at TEXT NOT NULL,
    started_at TEXT,
    finished_at TEXT,
    resource_key TEXT NOT NULL UNIQUE,
    resource_type TEXT NOT NULL,
    course_code TEXT,
    course_name TEXT,
    file_name TEXT NOT NULL,
    -- What answered and how it was asked (RF-25), set when the extractor ends.
    model TEXT,
    model_settings TEXT,
    prompt_version TEXT,
    content_retries INTEGER,
    error TEXT,
    audit_report_id INTEGER REFERENCES audit_reports (id)
);
CREATE TABLE IF NOT EXISTS discards (
    run_id INTEGER NOT NULL REFERENCES runs (id),
    ordinal INTEGER NOT NULL,
    rule TEXT NOT NULL,
    fact TEXT NOT NULL,
    message TEXT NOT NULL,
    PRIMARY KEY (run_id, ordinal)
);
-- The whole candidate batch of a rejected run, or the raw output of the model
-- when it never became one (EX-01).
CREATE TABLE IF NOT EXISTS rejected_outputs (
    run_id INTEGER PRIMARY KEY REFERENCES runs (id),
    batch TEXT,
    raw_output TEXT,
    CHECK (batch IS NOT NULL OR raw_output IS NOT NULL)
);
"""


@dataclass(frozen=True)
class StoredAuditReport:
    """A report as recorded. ``report`` is None while it is open."""

    id: int
    created_at: str
    origin: str
    run_id: str | None
    report: AuditReport | None

    @property
    def clean(self) -> bool:
        return self.report is not None and self.report.clean


@dataclass(frozen=True)
class Run:
    id: int
    status: str
    created_at: str
    started_at: str | None
    finished_at: str | None
    resource_key: str
    resource_type: str
    course_code: str | None
    course_name: str | None
    file_name: str
    model: str | None
    model_settings: Mapping | None
    prompt_version: str | None
    content_retries: int | None
    error: str | None
    audit_report_id: int | None


@dataclass(frozen=True)
class Extraction:
    """How a run's extraction was made, as RF-25 asks to record it."""

    model: str
    model_settings: Mapping
    prompt_version: str
    content_retries: int


@dataclass(frozen=True)
class Discard:
    rule: str
    fact: str
    message: str


_RUN_COLUMNS = (
    "id, status, created_at, started_at, finished_at, resource_key, resource_type, course_code, course_name,"
    " file_name,"
    " model, model_settings, prompt_version, content_retries, error, audit_report_id"
)


class OperationalStore:
    def __init__(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        # The timeout is the wait on a lock: the API, the worker and the build
        # processes all open this file.
        self._connection = sqlite3.connect(path, timeout=30)
        self._connection.execute("PRAGMA journal_mode = WAL")
        self._connection.execute("PRAGMA foreign_keys = ON")
        self._connection.executescript(_SCHEMA)

    def __enter__(self) -> "OperationalStore":
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.close()

    def close(self) -> None:
        self._connection.close()

    # --- Audit reports ------------------------------------------------------

    def open_audit_report(self, *, origin: str, run_id: str | None = None) -> int:
        """Record that ``origin`` is about to touch the graph; return the report id."""
        if origin not in ORIGINS:
            raise ValueError(f"unknown origin {origin!r}")
        with self._connection:
            cursor = self._connection.execute(
                "INSERT INTO audit_reports (created_at, origin, run_id) VALUES (?, ?, ?)",
                (_now(), origin, run_id),
            )
        return cursor.lastrowid

    def complete_audit_report(self, report_id: int, report: AuditReport) -> None:
        with self._connection:
            cursor = self._connection.execute(
                "UPDATE audit_reports SET completed_at = ?, violations = ? WHERE id = ? AND completed_at IS NULL",
                (_now(), report.violations, report_id),
            )
            if cursor.rowcount != 1:
                raise ValueError(f"audit report {report_id} is not open")
            self._connection.executemany(
                "INSERT INTO audit_rule_results (report_id, rule, violations, sample) VALUES (?, ?, ?, ?)",
                [(report_id, r.rule, r.violations, json.dumps(list(r.sample))) for r in report.results],
            )

    def latest_audit_report(self) -> StoredAuditReport | None:
        row = self._connection.execute(
            "SELECT id, created_at, origin, run_id, completed_at FROM audit_reports ORDER BY id DESC LIMIT 1"
        ).fetchone()
        if row is None:
            return None
        report_id, created_at, origin, run_id, completed_at = row
        if completed_at is None:
            return StoredAuditReport(report_id, created_at, origin, run_id, None)
        results = tuple(
            RuleResult(rule, violations, tuple(json.loads(sample)))
            for rule, violations, sample in self._connection.execute(
                "SELECT rule, violations, sample FROM audit_rule_results WHERE report_id = ? ORDER BY rule",
                (report_id,),
            )
        )
        return StoredAuditReport(report_id, created_at, origin, run_id, AuditReport(results))

    # --- Runs ---------------------------------------------------------------

    def create_run(
        self,
        *,
        resource_key: str,
        resource_type: str,
        course_code: str | None,
        course_name: str | None,
        file_name: str,
    ) -> int:
        """Record a pending run with what the operator declared; return its id."""
        with self._connection:
            cursor = self._connection.execute(
                "INSERT INTO runs (status, created_at, resource_key, resource_type, course_code, course_name,"
                " file_name) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (PENDING, _now(), resource_key, resource_type, course_code, course_name, file_name),
            )
        return cursor.lastrowid

    def take_pending_run(self) -> Run | None:
        """Mark the oldest pending run as running and return it; None if there is none."""
        with self._connection:
            row = self._connection.execute(
                "UPDATE runs SET status = ?, started_at = ?"
                " WHERE id = (SELECT min(id) FROM runs WHERE status = ?)"
                f" RETURNING {_RUN_COLUMNS}",
                (RUNNING, _now(), PENDING),
            ).fetchone()
        return _run(row) if row else None

    def get_run(self, run_id: int) -> Run:
        row = self._connection.execute(f"SELECT {_RUN_COLUMNS} FROM runs WHERE id = ?", (run_id,)).fetchone()
        if row is None:
            raise KeyError(f"run {run_id} does not exist")
        return _run(row)

    def list_runs(self) -> list[Run]:
        return [_run(row) for row in self._connection.execute(f"SELECT {_RUN_COLUMNS} FROM runs ORDER BY id")]

    def record_extraction(self, run_id: int, extraction: Extraction) -> None:
        with self._connection:
            self._update_run(
                run_id, (RUNNING,),
                model=extraction.model,
                model_settings=json.dumps(dict(extraction.model_settings), sort_keys=True),
                prompt_version=extraction.prompt_version,
                content_retries=extraction.content_retries,
            )

    def reject_run(
        self,
        run_id: int,
        discards: Iterable[Discard],
        *,
        batch: Batch | None = None,
        raw_output: str | None = None,
    ) -> None:
        """Mark the run rejected, with one discard per violation and what was rejected."""
        discards = list(discards)
        if not discards:
            raise ValueError("a rejected run has at least one discard")
        with self._connection:
            self._update_run(run_id, (RUNNING,), status=REJECTED, finished_at=_now())
            self._connection.executemany(
                "INSERT INTO discards (run_id, ordinal, rule, fact, message) VALUES (?, ?, ?, ?, ?)",
                [(run_id, i, d.rule, d.fact, d.message) for i, d in enumerate(discards)],
            )
            self._connection.execute(
                "INSERT INTO rejected_outputs (run_id, batch, raw_output) VALUES (?, ?, ?)",
                (run_id, json.dumps(batch_to_data(batch), ensure_ascii=False) if batch else None, raw_output),
            )

    def fail_run(self, run_id: int, error: str) -> None:
        with self._connection:
            self._update_run(run_id, (RUNNING,), status=FAILED, finished_at=_now(), error=error)

    def attach_audit_report(self, run_id: int, report_id: int) -> None:
        with self._connection:
            self._update_run(run_id, (RUNNING,), audit_report_id=report_id)

    def record_written_error(self, run_id: int, error: str) -> None:
        """What stopped a committed run before its audit closed it."""
        with self._connection:
            self._update_run(run_id, (WRITTEN_NOT_PERSISTED,), error=error)

    def mark_written(self, run_id: int) -> None:
        """The batch is committed and its facts are not saved yet."""
        with self._connection:
            self._update_run(run_id, (RUNNING,), status=WRITTEN_NOT_PERSISTED)

    def finish_run(self, run_id: int, *, clean: bool) -> None:
        """Close a written run with the verdict of its audit."""
        with self._connection:
            self._update_run(
                run_id, (WRITTEN_NOT_PERSISTED,),
                status=COMPLETED if clean else STOPPED_BY_AUDIT, finished_at=_now(),
            )

    def discards_of(self, run_id: int) -> list[Discard]:
        return [
            Discard(*row)
            for row in self._connection.execute(
                "SELECT rule, fact, message FROM discards WHERE run_id = ? ORDER BY ordinal", (run_id,)
            )
        ]

    def rejected_output_of(self, run_id: int) -> tuple[Batch | None, str | None]:
        row = self._connection.execute(
            "SELECT batch, raw_output FROM rejected_outputs WHERE run_id = ?", (run_id,)
        ).fetchone()
        if row is None:
            raise KeyError(f"run {run_id} has no rejected output")
        batch, raw_output = row
        return (batch_from_data(json.loads(batch)) if batch else None), raw_output

    def _update_run(self, run_id: int, expected: tuple[str, ...], **columns) -> None:
        # A run only moves forward: an update from an unexpected state is a bug.
        assignments = ", ".join(f"{name} = ?" for name in columns)
        cursor = self._connection.execute(
            f"UPDATE runs SET {assignments} WHERE id = ? AND status IN ({', '.join('?' * len(expected))})",
            (*columns.values(), run_id, *expected),
        )
        if cursor.rowcount != 1:
            raise ValueError(f"run {run_id} is not {' or '.join(expected)}")


def _run(row: tuple) -> Run:
    values = list(row)
    values[11] = json.loads(values[11]) if values[11] is not None else None
    return Run(*values)


def _now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")
