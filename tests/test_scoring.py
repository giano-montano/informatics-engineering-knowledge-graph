"""Tests for the automatic scorer and for the bilingual backbone.

The scorer decides which runs look better, so a bug here would misrank the
whole comparison silently. What matters is that it stays honest: relaxed
matching must not be able to turn a miss into a hit, and a link must only be
judged on a topic that was actually found.
"""

from __future__ import annotations

import pytest

from iekg import contracts, gold, linking, rules, scoring


@pytest.fixture(scope="module")
def spec():
    return rules.load()


@pytest.fixture(scope="module")
def catalog(spec):
    return gold.read_backbone(spec)


ANNOTATION = """\
version: 1
document: {code: 1TEST99, term: "2026-2", source: fake.pdf}
annotator: claude-contraste
date: 2026-08-15
blind: true
topics:
  - label_es: "Modelo relacional"
    label_en: "The Relational Model"
    links_to_ku: KU-DM-Relational
    confidence: high
    concepts:
      - {label_es: "Reglas de integridad", label_en: "Integrity Rules"}
  - label_es: "Disparadores"
    label_en: "Database Triggers"
    links_to_ku: null
    confidence: low
    concepts: []
out_of_scope: ["Nombres de los docentes"]
"""


@pytest.fixture
def annotation(tmp_path, catalog):
    path = tmp_path / "a.yaml"
    path.write_text(ANNOTATION, encoding="utf-8")
    return gold.load_annotation(path, catalog)


def extracted(*topics) -> contracts.Extraction:
    return contracts.Extraction(
        topics=[
            contracts.LinkedTopic(label_es=es, label_en=en, links_to_ku=ku)
            for es, en, ku in topics
        ]
    )


# ---------------------------------------------------------------------------
# Matching
# ---------------------------------------------------------------------------

def test_exact_match_is_exact(annotation):
    report = scoring.score(
        extracted(("Modelo relacional", "Relational Model", "KU-DM-Relational")),
        annotation,
    )
    assert report["topics"]["exact"] == 1
    assert report["topics"]["precision_exact"] == 1.0


def test_a_descriptive_tail_misses_exact_and_hits_relaxed(annotation):
    """The gap between the two columns is the granularity measurement: the
    pipeline found the right thing and named it with the whole syllabus row."""
    report = scoring.score(
        extracted(("Modelo relacional: estructura, operaciones y reglas de integridad",
                   "Relational Model", "KU-DM-Relational")),
        annotation,
    )
    assert report["topics"]["exact"] == 0
    assert report["topics"]["relaxed"] == 1


def test_an_unrelated_topic_matches_nothing(annotation):
    report = scoring.score(
        extracted(("Política de asistencia", "Attendance Policy", None)), annotation
    )
    assert report["topics"]["relaxed"] == 0
    assert report["topics"]["precision_relaxed"] == 0.0


def test_noise_is_counted_against_the_out_of_scope_list(annotation):
    report = scoring.score(
        extracted(("Nombres de los docentes", "Instructor Names", None)), annotation
    )
    assert report["noise"]["count"] == 1


# ---------------------------------------------------------------------------
# Linking
# ---------------------------------------------------------------------------

def test_a_link_is_only_judged_on_a_topic_that_was_found(annotation):
    """Judging the link of a topic the reference never listed would score the
    extraction twice and the linking not at all."""
    report = scoring.score(
        extracted(("Cosa inventada", "Invented Thing", "KU-DM-Relational")), annotation
    )
    assert report["linking"]["judged"] == 0


def test_the_right_unit_scores_correct(annotation):
    report = scoring.score(
        extracted(("Modelo relacional", "Relational Model", "KU-DM-Relational")),
        annotation,
    )
    assert report["linking"] == {
        "judged": 1, "correct": 1, "wrong": 0, "abstained": 0,
        "expected_no_unit": 0, "accuracy": 1.0,
    }


def test_abstaining_where_the_reference_also_found_no_unit_is_correct(annotation):
    """`links_to_ku: null` in the reference means CS2023 does not cover it.
    A pipeline that abstains there agreed, and must be scored as agreeing."""
    report = scoring.score(extracted(("Disparadores", "Triggers", None)), annotation)
    assert report["linking"]["correct"] == 1
    assert report["linking"]["expected_no_unit"] == 1


def test_linking_a_topic_the_reference_left_unlinked_is_wrong(annotation):
    report = scoring.score(
        extracted(("Disparadores", "Triggers", "KU-DM-Core")), annotation
    )
    assert report["linking"]["wrong"] == 1


def test_the_report_says_it_is_not_the_gold(annotation):
    report = scoring.score(extracted(("x", "x", None)), annotation)
    assert report["is_gold"] is False
    assert "lower bound" in report["caveat"].lower()


# ---------------------------------------------------------------------------
# The bilingual backbone
# ---------------------------------------------------------------------------

def test_both_labels_survive_the_projection(catalog):
    """Two skos:prefLabel literals must reach two node properties. Keyed only
    by predicate, one silently overwrote the other and English disappeared."""
    modeling = next(e for e in catalog if e.key == "KU-DM-Modeling")
    assert modeling.label == "Data Modeling"
    assert modeling.label_es == "Modelado de Datos"
    assert modeling.area_label_es


def test_every_unit_has_both_labels(catalog):
    missing = [e.key for e in catalog if not e.label_es]
    assert not missing, f"units with no Spanish label: {missing[:5]}"


def test_lexical_linking_can_match_in_spanish(catalog):
    assert linking.lexical("modelado de datos", catalog, "es").key == "KU-DM-Modeling"
    # And the English side still works, so the option is a real choice.
    assert linking.lexical("data modeling", catalog, "en").key == "KU-DM-Modeling"


def test_the_embedded_text_follows_the_language(catalog):
    modeling = next(e for e in catalog if e.key == "KU-DM-Modeling")
    assert linking.document_text(modeling, "es") == "Modelado de Datos (Gestión de Datos)"
    assert linking.document_text(modeling, "en") == "Data Modeling (Data Management)"
