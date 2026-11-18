from collections import Counter

import pytest
from conftest import BACKBONE, TBOX

from iekg.build_tools.projection import ProjectionError, check_tbox, project_backbone, read_turtle
from iekg.core.batch import Snapshot
from iekg.core.validator import LOAD_RULES, validate
from iekg.graph_schema import (
    KNOWLEDGE_AREA,
    KNOWLEDGE_UNIT,
    LEARNING_RESOURCE,
    PART_OF,
    PREF_LABEL_EN,
    PREF_LABEL_ES,
    REFERENCE,
    RESOURCE_LOCATOR,
    WAS_DERIVED_FROM,
)

IE = "http://www.informatics-engineering-kms.org/ontology/informatic-engineering#"
CS2023 = IE + "CS2023"


@pytest.fixture(scope="module")
def batch():
    return project_backbone(read_turtle(BACKBONE))


def altered(tmp_path, original, extra_turtle):
    """A copy of a TTL file with some Turtle appended; its prefixes still apply."""
    path = tmp_path / original.name
    path.write_text(original.read_text(encoding="utf-8") + "\n" + extra_turtle + "\n", encoding="utf-8")
    return read_turtle(path)


def test_the_tbox_uses_only_constructs_of_table_1():
    check_tbox(read_turtle(TBOX))


def test_the_backbone_projects_into_180_nodes_and_341_edges(batch):
    assert Counter(node.label for node in batch.nodes) == {
        KNOWLEDGE_AREA: 17,
        KNOWLEDGE_UNIT: 162,
        LEARNING_RESOURCE: 1,
    }
    assert Counter(edge.type for edge in batch.edges) == {PART_OF: 162, WAS_DERIVED_FROM: 179}


def test_keys_are_iris_and_labels_have_one_property_per_language(batch):
    for node in batch.nodes:
        assert node.key.startswith(IE)
        assert node.properties[PREF_LABEL_ES] and node.properties[PREF_LABEL_EN]
    resource = batch.nodes_by_key[CS2023]
    assert resource.properties[RESOURCE_LOCATOR] == "https://dl.acm.org/doi/book/10.1145/3664191"
    assert resource.properties[PREF_LABEL_EN] == "Computer Science Curricula 2023"


def test_every_unit_is_part_of_an_area_and_everything_derives_from_cs2023(batch):
    labels = {node.key: node.label for node in batch.nodes}
    for edge in batch.edges:
        if edge.type == PART_OF:
            assert (labels[edge.source], labels[edge.target]) == (KNOWLEDGE_UNIT, KNOWLEDGE_AREA)
        else:
            assert edge.target == CS2023


def test_the_backbone_passes_the_load_validation(batch):
    assert validate(batch, Snapshot(), layer=REFERENCE, rules=LOAD_RULES) == []


def test_partonomy_sub_properties_collapse_into_one_edge(tmp_path):
    graph = altered(tmp_path, BACKBONE, ":KU-AI-Search :isPartOf :KA-AI .")
    assert len(project_backbone(graph).edges) == 341


@pytest.mark.parametrize("extra, message", [
    (':KA-AI rdfs:label "Artificial Intelligence" .', "no row in Table 1"),
    (":KA-AI :hasPart :KU-AI-Search .", "no row in Table 1"),
    (':KA-AI skos:prefLabel "no language" .', "language tag"),
    (':KA-AI skos:prefLabel "Otra etiqueta"@es .', "second value"),
    (':KA-AI skos:prefLabel "Intelligence artificielle"@fr .', "language tag"),
    (':KA-AI :layer "institutional" .', "reference"),
    (":KA-AI :wasDerivedFrom \"CS2023\" .", "takes an individual"),
    (":KA-AI rdf:type :KnowledgeUnit .", "several classes"),
    (":KA-X rdf:type owl:NamedIndividual .", "has no class"),
    (":KA-X rdf:type owl:NamedIndividual , :KnowledgeElement .", "abstract"),
    (":Foo :bar :Baz .", "no construct of Table 1"),
])
def test_a_backbone_construct_without_a_row_is_rejected(tmp_path, extra, message):
    with pytest.raises(ProjectionError) as rejected:
        project_backbone(altered(tmp_path, BACKBONE, extra))
    assert any(message in problem.message for problem in rejected.value.problems)


@pytest.mark.parametrize("extra", [
    ":Concept owl:equivalentClass :Topic .",
    ':Concept rdfs:label "Concept" .',
    ":someone rdf:type owl:NamedIndividual .",
    ":hasPrerequisite rdf:type owl:SymmetricProperty .",
])
def test_a_tbox_construct_without_a_row_is_rejected(tmp_path, extra):
    with pytest.raises(ProjectionError):
        check_tbox(altered(tmp_path, TBOX, extra))
