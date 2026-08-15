"""Tests for the blind reference annotation.

The gold standard grounds every precision number in R4, so the things worth
asserting are the ways it could quietly stop being usable: an empty form that
parses, a knowledge unit that does not exist, a repeated topic.
"""

from __future__ import annotations

import pytest

from iekg import gold, rules


@pytest.fixture(scope="module")
def spec():
    return rules.load()


@pytest.fixture(scope="module")
def catalog(spec):
    return gold.read_backbone(spec)


def write(tmp_path, body: str):
    path = tmp_path / "test.annotation.yaml"
    path.write_text(body, encoding="utf-8")
    return path


FILLED = """\
version: 1
document: {code: 1TEST99, term: "2026-2", source: fake.pdf}
annotator: giano
date: 2026-08-14
blind: true
topics:
  - label_es: "Modelado de datos"
    label_en: "Data Modeling"
    links_to_ku: KU-DM-Modeling
    confidence: high
    concepts:
      - {label_es: "Modelo entidad-relación", label_en: "Entity-Relationship Model"}
out_of_scope: ["Profesor del curso"]
"""


def test_the_catalog_covers_the_whole_backbone(catalog):
    assert len(catalog) == 162
    assert len({e.area_key for e in catalog}) == 17
    assert all(e.label and e.area_label for e in catalog)


def test_reads_a_filled_annotation(tmp_path, catalog):
    annotation = gold.load_annotation(write(tmp_path, FILLED), catalog)
    assert annotation.topics[0].links_to_ku == "KU-DM-Modeling"
    assert annotation.concept_count == 1
    assert annotation.blind


def test_an_empty_template_is_not_a_reference(tmp_path, catalog):
    """An unfilled form parses as valid YAML and would score as 'nothing was
    expected', which flatters every pipeline. It has to be refused."""
    from pathlib import Path

    body = gold.template("1TEST99", "2026-2", Path("fake.pdf"),
                         annotator="giano", topic_slots=3)
    with pytest.raises(gold.AnnotationError, match="no topic is filled"):
        gold.load_annotation(write(tmp_path, body), catalog)


def test_rejects_a_knowledge_unit_that_does_not_exist(tmp_path, catalog):
    body = FILLED.replace("KU-DM-Modeling", "KU-DM-Invented")
    with pytest.raises(gold.AnnotationError, match="not a backbone unit"):
        gold.load_annotation(write(tmp_path, body), catalog)


def test_rejects_a_repeated_topic(tmp_path, catalog):
    duplicate = """\
  - label_es: "Otra cosa"
    label_en: "Data Modeling"
    links_to_ku: null
    confidence: low
    concepts: []
"""
    body = FILLED.replace("out_of_scope:", duplicate + "out_of_scope:")
    with pytest.raises(gold.AnnotationError, match="repeated"):
        gold.load_annotation(write(tmp_path, body), catalog)


def test_an_unlinked_topic_is_allowed(tmp_path, catalog):
    """`links_to_ku: null` means CS2023 does not cover it. That is a
    measurement of the backbone's coverage, not a hole in the form."""
    body = FILLED.replace("links_to_ku: KU-DM-Modeling", "links_to_ku: null")
    annotation = gold.load_annotation(write(tmp_path, body), catalog)
    assert annotation.topics[0].links_to_ku is None


def test_an_unsealed_annotation_does_not_open_the_gate(tmp_path, catalog):
    body = FILLED.replace("date: 2026-08-14", "date:")
    assert not gold.is_sealed(write(tmp_path, body))


def test_a_missing_annotation_does_not_open_the_gate(tmp_path):
    assert not gold.is_sealed(tmp_path / "absent.yaml")
