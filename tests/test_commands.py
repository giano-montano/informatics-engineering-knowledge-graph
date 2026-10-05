"""The load rejects before touching the base. These tests point it at a port
where nothing listens: reaching the database would fail them."""

from dataclasses import replace
from pathlib import Path

from conftest import BACKBONE, TBOX

from iekg.build_tools.commands import EXIT_REJECTED, load
from iekg.settings import Settings

UNREACHABLE = Settings(
    neo4j_uri="bolt://127.0.0.1:1",
    neo4j_user="neo4j",
    neo4j_password="unused",
    neo4j_database="neo4j",
    tbox_path=TBOX,
    backbone_path=BACKBONE,
    operational_db=Path("unused.sqlite"),
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
