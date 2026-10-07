"""Operational store (SQLite): run state, discards and audit reports.

Lives outside the graph database, so a load does not erase the evidence of
AC-01 and AC-02. For now it holds the audit reports; runs and discards come
with the ingestion. The latest report is what the worker's audit gate reads
(ADR-007).

A write path opens its report before it touches the graph and completes it
with the audit. A path that stops in between leaves its report open, and an
open report is not clean: the gate stays closed until a later path completes
a clean one.
"""

import json
import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from types import TracebackType

from iekg.core.auditor import AuditReport, RuleResult

# Write paths that close with an audit (ADR-005).
LOAD = "load"
INGESTION = "ingestion"
REAPPLICATION = "reapplication"
ORIGINS = (LOAD, INGESTION, REAPPLICATION)

_SCHEMA = f"""
CREATE TABLE IF NOT EXISTS audit_reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL,
    origin TEXT NOT NULL CHECK (origin IN ({", ".join(f"'{o}'" for o in ORIGINS)})),
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


def _now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")
