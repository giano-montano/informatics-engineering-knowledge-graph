"""The extractor without the provider: linking, EX codes and the content retry.

The model is PydanticAI's ``FunctionModel``, which answers what each test says.
"""

import copy
import json
from itertools import count

import httpx
import pytest
from openai import AsyncOpenAI
from pydantic import ValidationError
from pydantic_ai import models
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.exceptions import ModelHTTPError
from pydantic_ai.messages import ModelResponse, TextPart
from pydantic_ai.models.function import FunctionModel
from pydantic_ai.usage import RequestUsage

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


def filled(data):
    """``data`` with an evidence for every mention and a rationale for every relation that lacks one.

    The evidence differs from the name, so a test sees it if it leaks into a fact.
    """
    data = copy.deepcopy(data)
    for topic in data.get("topics", []):
        topic.setdefault("evidence", f"{topic.get('name')} (cita)")
        for concept in topic.get("concepts", []):
            concept.setdefault("evidence", f"{concept.get('name')} (cita)")
    for kind in ("required_concepts", "prerequisites", "specializations"):
        for relation in data.get(kind, []):
            relation.setdefault("rationale", "Una frase.")
    return data


def syllabus(data):
    return SyllabusOutput.model_validate(filled(data))


def output(**fields):
    return syllabus({"topics": [{"name": "Búsqueda heurística", "knowledge_unit": "K-001",
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


@pytest.mark.parametrize("a, b", [
    ("red", "redes"), ("función", "funciones"), ("interfaz", "interfaces"), ("unidad", "unidades"),
    ("árbol", "árboles"), ("carácter", "caracteres"), ("régimen", "regímenes"), ("switch", "switches"),
    ("clúster", "clústeres"), ("router", "routers"), ("VLAN", "VLANs"), ("variable", "variables"),
])
def test_singular_and_plural_normalize_alike(a, b):
    assert normalize_label(a) == normalize_label(b)


@pytest.mark.parametrize("a, b", [
    ("HTTPS", "HTTP"), ("IPS", "IP"), ("IDS", "ID"), ("FTPS", "FTP"), ("SMTPS", "SMTP"),
    ("IMAPS", "IMAP"), ("LDAPS", "LDAP"), ("POP3S", "POP3"), ("bus", "bu"),
])
def test_a_protected_word_does_not_meet_its_cut_form(a, b):
    assert normalize_label(a) != normalize_label(b)


@pytest.mark.parametrize("a, b", [
    ("C++", "C"), ("C#", "C"), ("C++", "C#"), ("F#", "F"), ("Árboles B+", "Árbol B"), ("C++11", "C 11"),
])
def test_a_plus_or_hash_after_a_letter_is_part_of_the_name(a, b):
    assert normalize_label(a) != normalize_label(b)


@pytest.mark.parametrize("a, b", [
    ("Lenguaje C++", "lenguaje c++"), ("Java y C#.", "java y c#"), ("Árboles B+", "arbol b+"),
    # Anywhere else they are punctuation.
    ("HTML+CSS", "HTML CSS"), ("HTML + CSS", "HTML CSS"), ("3+4", "3 4"), ("Tema #3", "tema 3"),
    ("C + +", "C"), ("C++x", "C x"),
])
def test_a_plus_or_hash_elsewhere_is_punctuation(a, b):
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
    facts = link(syllabus({"topics": [
        {"name": "Teoría de grafos", "existing": "T-001", "knowledge_unit": "K-001",
         "concepts": [{"name": "MST", "existing": "C-001"}]},
    ]}))
    assert facts.nodes == (NodeFact("topic", TOPIC, {PREF_LABEL_ES: "Grafos"}),
                           NodeFact("concept", CONCEPT, {PREF_LABEL_ES: "Árbol de expansión",
                                                         PREF_LABEL_EN: "Spanning tree"}))
    # The existing concept gets a further PART_OF to this topic; here it is the one it had.
    assert facts.edges == (EdgeFact(PART_OF, "concept", "topic"),)


def test_a_mention_marked_new_links_by_label_to_a_node_of_the_same_class():
    facts = link(syllabus({"topics": [
        {"name": "GRAFOS", "knowledge_unit": "K-001", "concepts": [{"name": "Spanning trees"}, {"name": "Grafos"}]},
    ]}))
    keys_by_label = {node.label: node.key for node in facts.nodes if node.key in SNAPSHOT.nodes}
    assert keys_by_label == {TOPIC: "topic", CONCEPT: "concept"}
    # A concept named like the topic is another node: the classes are disjoint.
    assert NodeFact("new-1", CONCEPT, {PREF_LABEL_ES: "Grafos"}) in facts.nodes


def test_repeated_mentions_merge_into_one_node_and_one_edge():
    facts = link(syllabus({"topics": [
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
    facts = link(syllabus({
        "topics": [{"name": "Grafos", "existing": "T-001", "concepts": [{"name": "MST", "existing": "C-001"}]}],
        "required_concepts": [{"name": "MST", "existing": "C-001"}],
    }))
    assert facts.taught == ("concept",) and facts.required == ()


# Concepts other courses teach, for the required ones a heading may name.
TAUGHT_ELSEWHERE = Snapshot(
    nodes={
        **SNAPSHOT.nodes,
        "virt": SnapshotNode(CONCEPT, INSTITUTIONAL, "Virtualización", "Virtualization"),
        "cloud": SnapshotNode(CONCEPT, INSTITUTIONAL, "Computación en la nube"),
        "graph": SnapshotNode(CONCEPT, INSTITUTIONAL, "Grafo"),
        "c": SnapshotNode(CONCEPT, INSTITUTIONAL, "C"),
    },
    edges=SNAPSHOT.edges,
)


def link_requiring(topics, *required):
    vocabulary = build_vocabulary(TAUGHT_ELSEWHERE)
    ref = {key: ref for ref, key in vocabulary.refs.items()}
    out = syllabus({
        "topics": [{"name": name, "knowledge_unit": "K-001", "concepts": []} for name in topics],
        "required_concepts": [{"name": name, "existing": ref[key]} for name, key in required],
    })
    return link_output(out, TAUGHT_ELSEWHERE, vocabulary, keys())


def test_a_required_concept_a_heading_names_is_taught_under_that_topic():
    # The case of 1INF35 (requisitos-funcionales-de-referencia, §8).
    facts = link_requiring(["Virtualización y computación en la nube"],
                           ("Virtualización", "virt"), ("Computación en la nube", "cloud"))
    assert facts.taught == ("virt", "cloud") and facts.required == ()
    assert EdgeFact(PART_OF, "virt", "new-1") in facts.edges and EdgeFact(PART_OF, "cloud", "new-1") in facts.edges


def test_a_heading_names_the_concept_by_its_label_in_the_graph_too():
    facts = link_requiring(["Virtualization: concepts"], ("Máquinas virtuales", "virt"))
    assert facts.taught == ("virt",) and facts.required == ()


def test_a_required_concept_named_in_two_headings_hangs_from_both():
    facts = link_requiring(["Árboles y grafos", "Recorridos: grafos"], ("Grafo", "graph"))
    assert facts.taught == ("graph",)
    assert {EdgeFact(PART_OF, "graph", "new-1"), EdgeFact(PART_OF, "graph", "new-2")} <= set(facts.edges)


@pytest.mark.parametrize("topic, required", [
    # Inside a segment, not a segment: the course builds on graphs.
    ("Algoritmos sobre grafos", ("Grafo", "graph")),
    # The language C is not C#.
    ("Lenguajes de programación: Java y C#", ("C", "c")),
])
def test_a_required_concept_only_inside_a_segment_stays_required(topic, required):
    facts = link_requiring([topic], required)
    assert facts.taught == () and facts.required == (required[1],)
    assert not [edge for edge in facts.edges if edge.source == required[1]]


RELATED = {
    "topics": [{"name": "Búsqueda heurística", "knowledge_unit": "K-001", "concepts": [{"name": "A*"}]}],
    "required_concepts": [{"name": "Spanning tree", "existing": "C-001"}],
    "prerequisites": [{"concept": "A*", "prerequisite": "spanning trees"}],
    "specializations": [{"concept": "A*", "generalization": "C-001"}],
}


def test_relations_join_concepts_of_the_output_and_existing_ones():
    facts = link(syllabus(RELATED))
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


@pytest.mark.parametrize("item, field", [
    (lambda data: data["topics"][0], "evidence"),
    (lambda data: data["topics"][0]["concepts"][0], "evidence"),
    (lambda data: data["required_concepts"][0], "rationale"),
    (lambda data: data["prerequisites"][0], "rationale"),
    (lambda data: data["specializations"][0], "rationale"),
])
def test_a_mention_without_evidence_or_a_relation_without_rationale_is_ex_01(item, field):
    data = filled(RELATED)
    del item(data)[field]
    with pytest.raises(ValidationError, match=f"{field}\n  Field required"):
        SyllabusOutput.model_validate(data)


# --- The model run and the content retry ------------------------------------------------

VALID = output().model_dump()
UNKNOWN_UNIT = filled({"topics": [{"name": "X", "knowledge_unit": "K-999", "concepts": []}]})
NO_UNIT = filled({"topics": [{"name": "X", "concepts": []}]})
# What each scripted response reports it consumed.
USAGE = RequestUsage(input_tokens=30_000, output_tokens=2_000)


def scripted(*answers):
    """A model that answers each request with the next of ``answers``."""
    remaining = list(answers)
    calls = []

    def answer(messages, info):
        calls.append(messages)
        next_answer = remaining.pop(0)
        if isinstance(next_answer, Exception):
            raise next_answer
        return ModelResponse(parts=[TextPart(json.dumps(next_answer))], usage=USAGE)

    return FunctionModel(answer, model_name="scripted-model"), calls


def extractor(model):
    return LanguageModelExtractor(model, model_settings={}, settings_record={"reasoning_effort": "low"},
                                  reader=lambda path: "SÍLABO", new_key=keys())


def test_the_output_schema_is_sent_strict_to_an_openai_compatible_server(tmp_path):
    # Without strict=True PydanticAI sends this schema with strict false, because
    # of its defaulted fields, and the provider would not enforce it (ADR-015).
    sent = []

    def server(request):
        sent.append(json.loads(request.content))
        return httpx.Response(200, json={
            "id": "x", "object": "chat.completion", "created": 0, "model": "served-model",
            "choices": [{"index": 0, "finish_reason": "stop",
                         "message": {"role": "assistant", "content": json.dumps(VALID)}}],
            "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
        })

    client = AsyncOpenAI(api_key="test", http_client=httpx.AsyncClient(transport=httpx.MockTransport(server)))
    model = OpenAIChatModel("any-model", provider=OpenAIProvider(openai_client=client))
    with models.override_allow_model_requests(True):
        extractor(model).extract(tmp_path / "doc.pdf", SNAPSHOT)
    response_format = sent[0]["response_format"]
    assert response_format["type"] == "json_schema"
    assert response_format["json_schema"]["strict"] is True


def test_a_conforming_output_yields_facts_and_records_how_it_was_asked(tmp_path):
    model, calls = scripted(VALID)
    facts, extraction = extractor(model).extract(tmp_path / "doc.pdf", SNAPSHOT)
    assert isinstance(facts, ExtractedFacts) and len(calls) == 1
    # FunctionModel names every response after itself; the name the provider
    # answers with is checked against the real provider.
    assert (extraction.model, extraction.content_retries) == ("scripted-model", 0)
    assert extraction.model_settings == {"reasoning_effort": "low", "requested_model": "scripted-model"}
    assert len(extraction.prompt_version) == 12
    assert (extraction.input_tokens, extraction.output_tokens) == (30_000, 2_000)
    # The output, evidence included, goes with the record; the facts carry none of it.
    assert extraction.output == VALID
    assert "Búsqueda heurística (cita)" not in repr(facts)


@pytest.mark.parametrize("first", [NO_UNIT, UNKNOWN_UNIT, {"not": "the schema"}])
def test_one_non_conforming_output_is_retried_once_with_its_error(tmp_path, first):
    model, calls = scripted(first, VALID)
    facts, extraction = extractor(model).extract(tmp_path / "doc.pdf", SNAPSHOT)
    assert extraction.content_retries == 1 and len(calls) == 2
    assert facts.nodes[0].properties == {PREF_LABEL_ES: "Búsqueda heurística"}
    # The retry is paid too.
    assert (extraction.input_tokens, extraction.output_tokens) == (60_000, 4_000)


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
    # It never became facts: the raw output is what is kept.
    assert caught.value.extraction.output is None
    assert caught.value.extraction.content_retries == 1
    assert (caught.value.extraction.input_tokens, caught.value.extraction.output_tokens) == (60_000, 4_000)


def test_a_provider_error_is_a_provider_failure(tmp_path):
    model, _ = scripted(ModelHTTPError(status_code=502, model_name="scripted-model", body="usage limit"))
    with pytest.raises(ProviderFailure, match="502"):
        extractor(model).extract(tmp_path / "doc.pdf", SNAPSHOT)
