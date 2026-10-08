"""The extractor without the provider: linking, EX codes and the content retry.

The model is PydanticAI's ``FunctionModel``, which answers what each test says.
"""

import json
from itertools import count

import pytest
from pydantic import ValidationError
from pydantic_ai import models
from pydantic_ai.exceptions import ModelHTTPError
from pydantic_ai.messages import ModelResponse, TextPart
from pydantic_ai.models.function import FunctionModel

from iekg.core.batch import EdgeFact, NodeFact, Snapshot, SnapshotNode
from iekg.graph_schema import (
    CONCEPT,
    HAS_PREREQUISITE,
    INSTITUTIONAL,
    KNOWLEDGE_AREA,
    KNOWLEDGE_UNIT,
    PART_OF,
    PREF_LABEL_EN,
    PREF_LABEL_ES,
    REFERENCE,
    SPECIALIZES,
    TOPIC,
)
from iekg.ingestion.declared import ExtractedFacts
from iekg.ingestion.extraction import EX_01, EX_02, EX_03, NonConformingOutput, ProviderFailure
from iekg.ingestion.extractor import (
    LanguageModelExtractor,
    SyllabusOutput,
    build_vocabulary,
    link_output,
)
from iekg.ingestion.normalization import normalize_label

models.ALLOW_MODEL_REQUESTS = False

# K-001 is the unit; T-001 the existing topic; C-001 the existing concept.
SNAPSHOT = Snapshot(
    nodes={
        "ka": SnapshotNode(KNOWLEDGE_AREA, REFERENCE, "Inteligencia Artificial", "Artificial Intelligence"),
        "ku": SnapshotNode(KNOWLEDGE_UNIT, REFERENCE, "Búsqueda", "Search", area="ka"),
        "topic": SnapshotNode(TOPIC, INSTITUTIONAL, "Grafos"),
        "concept": SnapshotNode(CONCEPT, INSTITUTIONAL, "Árbol de expansión", "Spanning tree"),
    },
    edges=(EdgeFact(PART_OF, "topic", "ku"), EdgeFact(PART_OF, "concept", "topic")),
)
VOCABULARY = build_vocabulary(SNAPSHOT)


def keys():
    numbers = count(1)
    return lambda: f"new-{next(numbers)}"


def output(**fields):
    return SyllabusOutput.model_validate({"topics": [{"name": "Búsqueda heurística", "knowledge_unit": "K-001",
                                                      "concepts": [{"name": "A*"}]}], **fields})


def link(out):
    return link_output(out, SNAPSHOT, VOCABULARY, keys())


# --- Normalization ---------------------------------------------------------------

@pytest.mark.parametrize("a, b", [
    ("Bases de Datos", "base de dato"),
    ("Árbol de expansión", "arbol de expansion"),
    ("SQL: DDL", "sql ddl"),
    ("  lenguaje_de   programación ", "lenguaje de programacion"),
])
def test_labels_that_name_the_same_thing_normalize_alike(a, b):
    assert normalize_label(a) == normalize_label(b)


# --- Vocabulary -------------------------------------------------------------------

def test_the_vocabulary_shows_each_unit_with_its_area_and_where_nodes_hang():
    assert VOCABULARY.refs == {"K-001": "ku", "T-001": "topic", "C-001": "concept"}
    assert "K-001  Inteligencia Artificial / Artificial Intelligence › Búsqueda / Search" in VOCABULARY.text
    assert "C-001 part of T-001" in VOCABULARY.text and "T-001 part of K-001" in VOCABULARY.text


def test_the_vocabulary_shows_the_existing_relations_between_concepts():
    snapshot = Snapshot(
        nodes={**SNAPSHOT.nodes, "dfs": SnapshotNode(CONCEPT, INSTITUTIONAL, "DFS")},
        edges=(*SNAPSHOT.edges, EdgeFact(HAS_PREREQUISITE, "dfs", "concept"), EdgeFact(SPECIALIZES, "dfs", "concept")),
    )
    vocabulary = build_vocabulary(snapshot)
    # Concepts sort by label, and "DFS" comes before "Árbol de expansión".
    assert vocabulary.refs["C-001"] == "dfs"
    assert "C-001 requires C-002" in vocabulary.text
    assert "C-001 is a kind of C-002" in vocabulary.text


# --- Linking ------------------------------------------------------------------------

def test_new_mentions_get_new_keys_and_their_partonomy():
    facts = link(output())
    assert facts.nodes == (NodeFact("new-1", TOPIC, {PREF_LABEL_ES: "Búsqueda heurística"}),
                           NodeFact("new-2", CONCEPT, {PREF_LABEL_ES: "A*"}))
    assert facts.edges == (EdgeFact(PART_OF, "new-1", "ku"), EdgeFact(PART_OF, "new-2", "new-1"))
    assert facts.taught == ("new-2",) and facts.required == ()


def test_a_referenced_node_keeps_its_key_and_its_graph_name_and_a_topic_gets_no_new_unit():
    facts = link(SyllabusOutput.model_validate({"topics": [
        {"name": "Teoría de grafos", "existing": "T-001", "knowledge_unit": "K-001",
         "concepts": [{"name": "MST", "existing": "C-001"}]},
    ]}))
    assert facts.nodes == (NodeFact("topic", TOPIC, {PREF_LABEL_ES: "Grafos"}),
                           NodeFact("concept", CONCEPT, {PREF_LABEL_ES: "Árbol de expansión",
                                                         PREF_LABEL_EN: "Spanning tree"}))
    # The existing concept gets a further PART_OF to this topic; here it is the one it had.
    assert facts.edges == (EdgeFact(PART_OF, "concept", "topic"),)


def test_a_mention_marked_new_links_by_label_to_a_node_of_the_same_class():
    facts = link(SyllabusOutput.model_validate({"topics": [
        {"name": "GRAFOS", "knowledge_unit": "K-001", "concepts": [{"name": "Spanning trees"}, {"name": "Grafos"}]},
    ]}))
    keys_by_label = {node.label: node.key for node in facts.nodes if node.key in SNAPSHOT.nodes}
    assert keys_by_label == {TOPIC: "topic", CONCEPT: "concept"}
    # A concept named like the topic is another node: the classes are disjoint.
    assert NodeFact("new-1", CONCEPT, {PREF_LABEL_ES: "Grafos"}) in facts.nodes


def test_repeated_mentions_merge_into_one_node_and_one_edge():
    facts = link(SyllabusOutput.model_validate({"topics": [
        {"name": "Búsqueda", "knowledge_unit": "K-001", "concepts": [{"name": "A*"}]},
        {"name": "búsquedas", "knowledge_unit": "K-001", "concepts": [{"name": "a*"}]},
    ]}))
    assert [node.key for node in facts.nodes] == ["new-1", "new-2"]
    assert facts.edges == (EdgeFact(PART_OF, "new-1", "ku"), EdgeFact(PART_OF, "new-2", "new-1"))


def test_required_concepts_are_existing_ones_and_add_no_partonomy():
    facts = link(output(required_concepts=[{"name": "Spanning tree", "existing": "C-001"}]))
    assert facts.required == ("concept",)
    assert not [edge for edge in facts.edges if edge.source == "concept"]


def test_a_required_concept_the_course_also_teaches_is_only_taught():
    facts = link(SyllabusOutput.model_validate({
        "topics": [{"name": "Grafos", "existing": "T-001", "concepts": [{"name": "MST", "existing": "C-001"}]}],
        "required_concepts": [{"name": "MST", "existing": "C-001"}],
    }))
    assert facts.taught == ("concept",) and facts.required == ()


def test_relations_join_concepts_of_the_output_and_existing_ones():
    facts = link(output(
        required_concepts=[{"name": "Spanning tree", "existing": "C-001"}],
        prerequisites=[{"concept": "A*", "prerequisite": "spanning trees"}],
        specializations=[{"concept": "A*", "generalization": "C-001"}],
    ))
    assert EdgeFact(HAS_PREREQUISITE, "new-2", "concept") in facts.edges
    assert EdgeFact(SPECIALIZES, "new-2", "concept") in facts.edges


@pytest.mark.parametrize("fields, place", [
    ({"topics": [{"name": "X", "existing": "T-999", "concepts": []}]}, "topic 'X'"),
    ({"topics": [{"name": "X", "knowledge_unit": "K-999", "concepts": []}]}, "topic 'X', knowledge_unit"),
    ({"topics": [{"name": "X", "existing": "T-001", "concepts": [{"name": "Y", "existing": "C-999"}]}]},
     "concept 'Y'"),
    ({"required_concepts": [{"name": "Y", "existing": "C-999"}]}, "required concept 'Y'"),
    ({"prerequisites": [{"concept": "A*", "prerequisite": "C-999"}]}, "relation end 'C-999'"),
])
def test_a_reference_outside_the_vocabulary_is_ex_02(fields, place):
    [discard] = link(output(**fields))
    assert (discard.rule, discard.fact) == (EX_02, f"{place}: {fields_ref(fields)!r}")


def fields_ref(fields):
    return next(word for word in json.dumps(fields).replace('"', " ").split() if word.endswith("-999"))


@pytest.mark.parametrize("fields, place", [
    ({"topics": [{"name": "X", "existing": "C-001", "concepts": []}]}, "topic 'X'"),
    ({"topics": [{"name": "X", "existing": "K-001", "concepts": []}]}, "topic 'X'"),
    ({"topics": [{"name": "X", "knowledge_unit": "T-001", "concepts": []}]}, "topic 'X', knowledge_unit"),
    ({"topics": [{"name": "X", "existing": "T-001", "concepts": [{"name": "Y", "existing": "T-001"}]}]},
     "concept 'Y'"),
    ({"required_concepts": [{"name": "Y", "existing": "K-001"}]}, "required concept 'Y'"),
    ({"required_concepts": [{"name": "Y", "existing": "T-001"}]}, "required concept 'Y'"),
    ({"specializations": [{"concept": "A*", "generalization": "T-001"}]}, "relation end 'T-001'"),
])
def test_a_reference_of_another_class_is_ex_03(fields, place):
    [discard] = link(output(**fields))
    assert discard.rule == EX_03 and discard.fact.startswith(f"{place}: ")


@pytest.mark.parametrize("fields, message", [
    ({"topics": []}, "at least 1"),
    ({"topics": [{"name": "X", "concepts": []}]}, "has no knowledge_unit"),
    ({"required_concepts": [{"name": "Y"}]}, "existing\n  Field required"),
    ({"prerequisites": [{"concept": "A*", "prerequisite": "Dijkstra"}]}, "neither a concept"),
    ({"topics": [{"name": "X", "knowledge_unit": "K-001"}]}, "Field required"),
])
def test_what_the_output_schema_refuses_is_ex_01(fields, message):
    with pytest.raises(ValidationError, match=message):
        output(**fields)


# --- The model run and the content retry ------------------------------------------------

VALID = output().model_dump()
UNKNOWN_UNIT = {"topics": [{"name": "X", "knowledge_unit": "K-999", "concepts": []}]}
NO_UNIT = {"topics": [{"name": "X", "concepts": []}]}


def scripted(*answers):
    """A model that answers each request with the next of ``answers``."""
    remaining = list(answers)
    calls = []

    def answer(messages, info):
        calls.append(messages)
        next_answer = remaining.pop(0)
        if isinstance(next_answer, Exception):
            raise next_answer
        return ModelResponse(parts=[TextPart(json.dumps(next_answer))])

    return FunctionModel(answer, model_name="scripted-model"), calls


def extractor(model):
    return LanguageModelExtractor(model, model_settings={}, settings_record={"reasoning_effort": "low"},
                                  reader=lambda path: "SÍLABO", new_key=keys())


def test_a_conforming_output_yields_facts_and_records_how_it_was_asked(tmp_path):
    model, calls = scripted(VALID)
    facts, extraction = extractor(model).extract(tmp_path / "doc.pdf", SNAPSHOT)
    assert isinstance(facts, ExtractedFacts) and len(calls) == 1
    # FunctionModel names every response after itself; the name the provider
    # answers with is checked against the real provider.
    assert (extraction.model, extraction.content_retries) == ("scripted-model", 0)
    assert extraction.model_settings == {"reasoning_effort": "low", "requested_model": "scripted-model"}
    assert len(extraction.prompt_version) == 12


@pytest.mark.parametrize("first", [NO_UNIT, UNKNOWN_UNIT, {"not": "the schema"}])
def test_one_non_conforming_output_is_retried_once_with_its_error(tmp_path, first):
    model, calls = scripted(first, VALID)
    facts, extraction = extractor(model).extract(tmp_path / "doc.pdf", SNAPSHOT)
    assert extraction.content_retries == 1 and len(calls) == 2
    assert facts.nodes[0].properties == {PREF_LABEL_ES: "Búsqueda heurística"}


@pytest.mark.parametrize("answers, code", [
    ((NO_UNIT, NO_UNIT), EX_01),
    ((UNKNOWN_UNIT, UNKNOWN_UNIT), EX_02),
    ((NO_UNIT, UNKNOWN_UNIT), EX_02),
    ((UNKNOWN_UNIT, NO_UNIT), EX_01),
])
def test_a_second_non_conforming_output_rejects_with_its_code_and_raw_output(tmp_path, answers, code):
    model, calls = scripted(*answers)
    with pytest.raises(NonConformingOutput) as caught:
        extractor(model).extract(tmp_path / "doc.pdf", SNAPSHOT)
    assert len(calls) == 2
    assert [d.rule for d in caught.value.discards] == [code]
    assert json.loads(caught.value.raw_output) == answers[1]
    assert caught.value.extraction.content_retries == 1


def test_a_provider_error_is_a_provider_failure(tmp_path):
    model, _ = scripted(ModelHTTPError(status_code=502, model_name="scripted-model", body="usage limit"))
    with pytest.raises(ProviderFailure, match="502"):
        extractor(model).extract(tmp_path / "doc.pdf", SNAPSHOT)
