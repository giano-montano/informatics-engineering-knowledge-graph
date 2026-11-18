"""The load rejects before touching the base, and a load that touches it
without finishing keeps the audit gate closed.

The rejection tests point the load at a port where nothing listens: reaching
the database would fail them. The gate tests replace the driver and the
repository, so they never empty a real base.
"""

from dataclasses import replace
from pathlib import Path

import pytest
from conftest import BACKBONE, TBOX
from neo4j.exceptions import ServiceUnavailable

from iekg.build_tools import commands
from iekg.build_tools.commands import EXIT_CLEAN, EXIT_FAILED, EXIT_REJECTED, load
from iekg.core.auditor import AuditReport, RuleResult
from iekg.operational_store import OperationalStore
from iekg.settings import Settings

UNREACHABLE = Settings(
    neo4j_uri="bolt://127.0.0.1:1",
    neo4j_user="neo4j",
    neo4j_password="unused",
    neo4j_database="neo4j",
    tbox_path=TBOX,
    backbone_path=BACKBONE,
    operational_db=Path("unused.sqlite"),
    facts_dir=Path("unused-facts"),
    documents_dir=Path("unused-documents"),
    public_base_url="http://localhost:8000",
)


def run(settings):
    lines = []
    return load(settings, out=lines.append), "\n".join(lines)


def test_a_construct_without_a_row_rejects_the_load(tmp_path):
    backbone = tmp_path / "backbone.ttl"
    backbone.write_text(BACKBONE.read_text(encoding="utf-8") + '\n:KA-AI rdfs:label "AI" .\n', encoding="utf-8")
    code, output = run(replace(UNREACHABLE, backbone_path=backbone, operational_db=tmp_path / "ops.sqlite"))
    assert code == EXIT_REJECTED
    assert "was not touched" in output and "rdfs:label" in output
    assert not (tmp_path / "ops.sqlite").exists()


def test_a_validation_violation_rejects_the_load(tmp_path):
    # Without its locator, CS2023 violates RM-05.
    text = BACKBONE.read_text(encoding="utf-8").replace(
        ':resourceLocator "https://dl.acm.org/doi/book/10.1145/3664191"^^xsd:anyURI ;', ""
    )
    backbone = tmp_path / "backbone.ttl"
    backbone.write_text(text, encoding="utf-8")
    code, output = run(replace(UNREACHABLE, backbone_path=backbone, operational_db=tmp_path / "ops.sqlite"))
    assert code == EXIT_REJECTED
    assert "RM-05" in output and "was not touched" in output


class FakeDriver:
    def __init__(self, *args, **kwargs):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        return False

    def verify_connectivity(self):
        pass


class FakeRepository:
    """Empties and writes nothing; ``fail_at`` names the step that raises."""

    fail_at = None

    def __init__(self, driver, database):
        pass

    def _step(self, name):
        if self.fail_at == name:
            raise ServiceUnavailable(f"lost the connection during {name}")

    def reset(self):
        self._step("reset")
        return 8

    def write_batch(self, batch, snapshot, *, layer):
        self._step("write")
        return type("Result", (), {"nodes_created": len(batch.nodes), "relationships_created": len(batch.edges)})

    def count_elements(self):
        self._step("count")
        return {}, {}


CLEAN = AuditReport((RuleResult("RI-01", 0, ()),))


@pytest.fixture
def fake_base(monkeypatch, tmp_path):
    monkeypatch.setattr(commands.GraphDatabase, "driver", FakeDriver)
    monkeypatch.setattr(commands, "GraphRepository", FakeRepository)
    monkeypatch.setattr(FakeRepository, "fail_at", None)
    monkeypatch.setattr(commands, "audit_database", lambda driver, database: CLEAN)
    return replace(UNREACHABLE, operational_db=tmp_path / "ops.sqlite")


def latest_report(settings):
    with OperationalStore(settings.operational_db) as store:
        return store.latest_audit_report()


def test_a_finished_load_completes_its_report(fake_base):
    code, output = run(fake_base)
    assert code == EXIT_CLEAN
    assert latest_report(fake_base).clean


@pytest.mark.parametrize("step", ["reset", "write", "count"])
def test_a_load_that_stops_after_touching_the_base_leaves_the_gate_closed(fake_base, monkeypatch, step):
    monkeypatch.setattr(FakeRepository, "fail_at", step)
    code, output = run(fake_base)
    assert code == EXIT_FAILED
    assert "gate stays closed" in output
    latest = latest_report(fake_base)
    assert latest.report is None and not latest.clean


def test_a_failed_audit_leaves_the_gate_closed(fake_base, monkeypatch):
    def audit_database(driver, database):
        raise ServiceUnavailable("lost the connection during the audit")

    monkeypatch.setattr(commands, "audit_database", audit_database)
    code, output = run(fake_base)
    assert code == EXIT_FAILED
    assert not latest_report(fake_base).clean


def test_a_store_that_cannot_complete_the_report_leaves_the_gate_closed(fake_base, monkeypatch):
    def complete_audit_report(self, report_id, report):
        raise commands.sqlite3.OperationalError("database is locked")

    monkeypatch.setattr(OperationalStore, "complete_audit_report", complete_audit_report)
    code, output = run(fake_base)
    assert code == EXIT_FAILED
    assert "gate stays closed" in output
    assert not latest_report(fake_base).clean


def test_a_store_that_cannot_open_the_report_stops_the_load_before_the_base(fake_base, monkeypatch):
    def open_audit_report(self, *, origin, run_id=None):
        raise commands.sqlite3.OperationalError("disk I/O error")

    monkeypatch.setattr(OperationalStore, "open_audit_report", open_audit_report)
    code, output = run(fake_base)
    assert code == EXIT_FAILED
    assert "was not touched" in output and "Emptying" not in output
