"""Tests for the pipeline machinery. No network, no database.

What is worth testing here is everything that happens around the model call:
the composition, the minting, the emitted Cypher and the rule violations the
extraction produces. The model call itself is measured by the probe, not
asserted by a test.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from iekg import abox as abox_mod
from iekg import contracts, gold, linking, llm, pipeline, rules

DOCUMENT = abox_mod.SourceDocument(
    code="1TEST99", term="2026-2", path=Path("lab/docs/syllabus/fake.pdf"), title="Test"
)


@pytest.fixture(scope="module")
def spec():
    return rules.load()


@pytest.fixture(scope="module")
def catalog():
    return llm.load()


def extraction(links: str | None = "KU-DM-Modeling") -> contracts.Extraction:
    return contracts.Extraction(
        topics=[
            contracts.LinkedTopic(
                label_es="Modelado de datos",
                label_en="Data Modeling",
                links_to_ku=links,
                concepts=[
                    contracts.ConceptOut(label_es="Modelo entidad-relación",
                                         label_en="Entity-Relationship Model"),
                ],
            )
        ]
    )


# ---------------------------------------------------------------------------
# Composition
# ---------------------------------------------------------------------------

def test_every_declared_stage_exists():
    for name, config in pipeline.load_pipelines().items():
        for stage in config.stages:
            assert stage in pipeline.STAGES, f"{name} names unknown stage {stage}"


def test_the_ladder_adds_one_thing_per_rung():
    """P0..P3 are a ladder, not four systems: each rung must extend the one
    below. If a rung drops a stage, a result difference stops being
    attributable and the whole comparison design is void."""
    configs = pipeline.load_pipelines()
    order = ["P0", "P1", "P2", "P3"]
    for lower, upper in zip(order, order[1:]):
        assert len(configs[upper].stages) >= len(configs[lower].stages), (
            f"{upper} has fewer stages than {lower}"
        )
    # The one variable P3 isolates is how linking is done, not that it exists.
    assert "link_lexical" in configs["P2"].stages
    assert "link_retrieval" in configs["P3"].stages
    assert "link_lexical" not in configs["P3"].stages


def test_only_the_baseline_runs_unconstrained():
    configs = pipeline.load_pipelines()
    assert "verbalize" not in configs["P0"].stages
    for name in ("P1", "P2", "P3"):
        assert "verbalize" in configs[name].stages


def test_pipelines_only_coin_classes_with_an_iri_prefix(spec):
    for config in pipeline.load_pipelines().values():
        for owl_class in config.coinable:
            assert spec.iri_prefix(owl_class)


# ---------------------------------------------------------------------------
# Minting and the A-box
# ---------------------------------------------------------------------------

def test_minting_is_deterministic_across_surface_forms(spec):
    """MERGE is only idempotent if the same thing mints the same IRI. Case,
    accents and stray spacing are presentation, not identity."""
    first = abox_mod.mint(spec, "Topic", "Data  Modeling")
    second = abox_mod.mint(spec, "Topic", "DATA MODELING")
    assert first == second
    assert first.startswith(spec.namespace + "T-")


def test_scoping_iris_separates_two_documents(spec):
    unscoped = abox_mod.mint(spec, "Concept", "Normalization")
    scoped = abox_mod.mint(spec, "Concept", "Normalization", scope="1INF33")
    assert unscoped != scoped


def test_a_linked_extraction_violates_nothing(spec):
    result = abox_mod.build(extraction(), DOCUMENT, spec)
    assert result.violations == ()
    assert result.conformance == 1.0


def test_an_unlinked_topic_is_reported_not_swallowed(spec):
    """P0 to P2 will produce these by the dozen. The count is the measurement,
    so it must reach the artifact rather than being silently tolerated."""
    result = abox_mod.build(extraction(links=None), DOCUMENT, spec)
    assert "topic-in-ku" in result.by_rule()
    assert result.conformance < 1.0


def test_the_backbone_endpoint_is_quoted_never_written(spec):
    result = abox_mod.build(extraction(), DOCUMENT, spec)
    written = {n.iri for n in result.nodes}
    ku = spec.namespace + "KU-DM-Modeling"
    assert ku not in written
    assert ku in {n.iri for n in result.context}


def test_emitted_cypher_merges_coined_and_matches_backbone(spec):
    result = abox_mod.build(extraction(), DOCUMENT, spec)
    cypher = abox_mod.to_cypher(result, DOCUMENT, spec)
    assert "MERGE (n:KnowledgeElement:Topic {iri: row.iri})" in cypher
    # The only way a reference node could be created is a MERGE naming it.
    assert "KU-DM-Modeling" in cypher
    for line in cypher.splitlines():
        if "KU-DM-Modeling" in line:
            assert not line.strip().startswith("MERGE (n:")


def test_emitted_cypher_escapes_a_hostile_label(spec):
    """Labels come from a model reading a PDF. A quote in one must not be able
    to close a Cypher string literal."""
    hostile = contracts.Extraction(
        topics=[
            contracts.LinkedTopic(
                label_es='Bases "de" datos\\', label_en="Databases",
                links_to_ku="KU-DM-Core",
            )
        ]
    )
    cypher = abox_mod.to_cypher(abox_mod.build(hostile, DOCUMENT, spec), DOCUMENT, spec)
    assert '\\"de\\"' in cypher


# ---------------------------------------------------------------------------
# The unconstrained baseline's reader
# ---------------------------------------------------------------------------

def test_reads_json_wrapped_in_prose():
    text = 'Sure! Here you go:\n```json\n{"topics": [{"label": "Databases"}]}\n```\nHope it helps.'
    result = contracts.parse_unconstrained(text)
    assert [t.label_en for t in result.topics] == ["Databases"]
    assert not result.unparsed


def test_reads_a_bare_list_of_strings():
    result = contracts.parse_unconstrained('["Databases", "Normalization"]')
    assert len(result.topics) == 2


def test_keeps_what_it_cannot_read():
    """The cost of not constraining has to be a number, not an exception."""
    result = contracts.parse_unconstrained("The course covers databases and SQL.")
    assert result.topics == []
    assert result.unparsed


# ---------------------------------------------------------------------------
# Linking
# ---------------------------------------------------------------------------

def test_lexical_matches_only_exactly(spec):
    entries = gold.read_backbone(spec)
    assert linking.lexical("data modeling", entries).key == "KU-DM-Modeling"
    assert linking.lexical("Modelado de datos", entries).key is None
    # A control that quietly does fuzzy matching is not a control.
    assert linking.lexical("Data Model", entries).key is None


def test_retrieval_abstains_when_the_lead_is_thin():
    candidates = (
        linking.Candidate("KU-DM-Modeling", "Data Modeling", 0.733),
        linking.Candidate("KU-DM-Relational", "Relational Databases", 0.708),
    )
    decision = linking.decide(candidates, threshold=0.62, margin=0.03)
    assert decision.key is None
    assert "review" in decision.reason
    # The candidates survive the abstention: a reviewer needs to see them.
    assert len(decision.candidates) == 2


def test_retrieval_accepts_a_clear_lead():
    candidates = (
        linking.Candidate("KU-DM-Modeling", "Data Modeling", 0.733),
        linking.Candidate("KU-AR-Quantum", "Quantum Architectures", 0.560),
    )
    assert linking.decide(candidates, threshold=0.62, margin=0.03).key == "KU-DM-Modeling"


def test_retrieval_rejects_below_the_floor():
    candidates = (linking.Candidate("KU-DM-Modeling", "Data Modeling", 0.40),)
    assert linking.decide(candidates, threshold=0.62, margin=0.03).key is None


def test_the_embedding_model_is_declared_in_the_catalog(catalog):
    for config in pipeline.load_pipelines().values():
        assert catalog.embedding(config.embedding_model).dimensions > 0


# ---------------------------------------------------------------------------
# The verbalised ontology
# ---------------------------------------------------------------------------

def test_the_prompt_states_what_may_not_be_created(spec):
    from iekg import verbalize

    text = verbalize.build(spec, ["Topic", "Concept"])
    assert "never create" in text
    for fixed in ("KnowledgeArea", "KnowledgeUnit"):
        assert fixed in text


def test_the_prompt_carries_the_existential_constraints(spec):
    from iekg import verbalize

    text = verbalize.build(spec, ["Topic", "Concept"])
    assert "Every Topic is linked to at least one KnowledgeUnit" in text
