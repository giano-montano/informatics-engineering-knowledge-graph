"""Build commands: ``iekg-build load``.

The load empties the graph database, initializes it and writes the reference
layer from the backbone TTL, and closes with an audit whose report goes to the
operational store (ADR-004, ADR-005). Everything that can reject the load runs
before the base is touched: a broken TTL leaves the graph as it was.

Exit codes: 0 loaded with a clean audit; 1 loaded, but the audit found
violations; 2 rejected before touching the base; 3 failed (see the message for
the state of the base). A load that fails after touching the base leaves its
audit report open, which keeps the worker's audit gate closed (ADR-007).
"""

import argparse
import sqlite3
import sys
from collections.abc import Callable, Sequence

from neo4j import Driver, GraphDatabase
from neo4j.exceptions import DriverError, Neo4jError

from iekg.build_tools.projection import ProjectionError, check_tbox, project_backbone, read_turtle
from iekg.core.auditor import AuditReport, audit_database
from iekg.core.batch import Batch, Snapshot
from iekg.core.repository import GraphRepository, WriteMismatch
from iekg.core.rules import STATEMENTS
from iekg.core.validator import LOAD_RULES, validate
from iekg.graph_schema import REFERENCE
from iekg.operational_store import LOAD, OperationalStore
from iekg.settings import Settings, SettingsError

EXIT_CLEAN = 0
EXIT_VIOLATIONS = 1
EXIT_REJECTED = 2
EXIT_FAILED = 3

Output = Callable[[str], None]


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="iekg-build",
        description="Build processes of the graph. Run them with the system stopped (ADR-007).",
    )
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser(
        "load",
        help="empty the graph database and write the reference layer from the backbone TTL",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.parse_args(argv)
    try:
        settings = Settings.from_environment()
    except SettingsError as error:
        print(f"error: {error}", file=sys.stderr)
        return EXIT_FAILED
    return load(settings)


def load(settings: Settings, out: Output = print) -> int:
    try:
        out(f"Reading the T-Box: {settings.tbox_path}")
        tbox = read_turtle(settings.tbox_path)
        check_tbox(tbox, str(settings.tbox_path))
        out(f"  {len(tbox)} triples, every construct covered by Table 1")

        out(f"Projecting the backbone: {settings.backbone_path}")
        backbone = read_turtle(settings.backbone_path)
        batch = project_backbone(backbone, str(settings.backbone_path))
        out(f"  {len(backbone)} triples -> {len(batch.nodes)} nodes, {len(batch.edges)} edges")
    except ProjectionError as error:
        out(f"Rejected: {error}. The graph database was not touched.")
        for problem in error.problems:
            out(f"  {problem.construct}\n    {problem.message}")
        return EXIT_REJECTED

    # The load starts from an empty base, so it validates on an empty snapshot.
    snapshot = Snapshot()
    out(f"Validating ({', '.join(LOAD_RULES)})")
    violations = validate(batch, snapshot, layer=REFERENCE, rules=LOAD_RULES)
    if violations:
        out(f"Rejected: {len(violations)} violation(s). The graph database was not touched.")
        for violation in violations:
            out(f"  {violation.rule}  {violation.fact}\n    {violation.message}")
        return EXIT_REJECTED
    out("  no violations")

    target = f"{settings.neo4j_uri}, database {settings.neo4j_database}"
    with GraphDatabase.driver(settings.neo4j_uri, auth=(settings.neo4j_user, settings.neo4j_password)) as driver:
        try:
            driver.verify_connectivity()
        except (DriverError, Neo4jError) as error:
            out(f"Failed: cannot reach {target}: {error}. The graph database was not touched.")
            return EXIT_FAILED
        # Opened before the base is touched: if the load stops halfway, the
        # open report keeps the audit gate closed (ADR-007).
        try:
            with OperationalStore(settings.operational_db) as store:
                report_id = store.open_audit_report(origin=LOAD)
        except sqlite3.Error as error:
            out(f"Failed: cannot record in {settings.operational_db}: {error}. The graph database was not touched.")
            return EXIT_FAILED
        report = _write_and_audit(driver, settings.neo4j_database, batch, target, out)
        if report is None:
            out(f"Audit report {report_id} is left open, so the audit gate stays closed.")
            return EXIT_FAILED

    _print_report(report, out)
    try:
        with OperationalStore(settings.operational_db) as store:
            store.complete_audit_report(report_id, report)
    except sqlite3.Error as error:
        out(f"Failed to complete audit report {report_id}: {error}. It is left open, so the audit gate stays closed.")
        return EXIT_FAILED
    verdict = "clean" if report.clean else f"{report.violations} violation(s)"
    out(f"Audit report {report_id} recorded in {settings.operational_db}: {verdict}")
    return EXIT_CLEAN if report.clean else EXIT_VIOLATIONS


def _write_and_audit(driver: Driver, database: str, batch: Batch, target: str, out: Output) -> AuditReport | None:
    """Empty the base, write ``batch`` and audit the result; None if a step fails."""
    repository = GraphRepository(driver, database)
    out(f"Emptying and initializing {target}")
    try:
        constraints = repository.reset()
    except (DriverError, Neo4jError) as error:
        out(f"Failed while emptying the base: {error}. Its state is unknown; run the load again.")
        return None
    out(f"  {constraints} uniqueness constraints")

    out("Writing the reference layer in one transaction")
    try:
        result = repository.write_batch(batch, Snapshot(), layer=REFERENCE)
    except (WriteMismatch, DriverError, Neo4jError) as error:
        out(f"Failed: {error}. The write was rolled back and the base is left empty.")
        return None
    out(f"  committed: {result.nodes_created} nodes, {result.relationships_created} edges")

    try:
        nodes, edges = repository.count_elements()
        out("  " + ", ".join(f"{label} {n}" for label, n in nodes.items()))
        out("  " + ", ".join(f"{edge_type} {n}" for edge_type, n in edges.items()))
        out("Auditing")
        return audit_database(driver, database)
    except (DriverError, Neo4jError) as error:
        out(f"Failed after the write: {error}. The reference layer is written, but not audited.")
        return None


def _print_report(report: AuditReport, out: Output) -> None:
    for result in report.results:
        status = "ok" if result.violations == 0 else f"{result.violations} violation(s)"
        out(f"  {result.rule}  {status:<16} {STATEMENTS[result.rule]}")
        for element in result.sample:
            out(f"      {element}")
        if result.violations > len(result.sample):
            out(f"      ... and {result.violations - len(result.sample)} more")


if __name__ == "__main__":
    sys.exit(main())
