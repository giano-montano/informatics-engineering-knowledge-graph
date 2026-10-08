from iekg.core.batch import EdgeFact, NodeFact, Snapshot, SnapshotNode
from iekg.graph_schema import (
    CONCEPT,
    COURSE,
    COURSE_CODE,
    HAS_RESOURCE_TYPE,
    INSTITUTIONAL,
    IS_ABOUT,
    LEARNING_RESOURCE,
    PART_OF,
    PREF_LABEL_ES,
    REQUIRES_CONCEPT,
    RESOURCE_LOCATOR,
    RESOURCE_TYPE,
    TEACHES_CONCEPT,
    TOPIC,
)
from iekg.ingestion.declared import (
    SYLLABUS,
    Declaration,
    ExtractedFacts,
    assemble_batch,
    course_key,
    resource_type_key,
)

DECLARATION = Declaration("doc", SYLLABUS, " 1inf33 ", "Bases de Datos")
EXTRACTED = ExtractedFacts(
    nodes=(NodeFact("t", TOPIC), NodeFact("c", CONCEPT), NodeFact("r", CONCEPT)),
    edges=(EdgeFact(PART_OF, "t", "ku"), EdgeFact(PART_OF, "c", "t"), EdgeFact(PART_OF, "c", "t")),
    taught=("c",),
    required=("r",),
)


def test_derived_keys_depend_only_on_the_code_and_the_name():
    assert course_key("1INF33") == course_key(" 1inf33") != course_key("1INF34")
    assert resource_type_key(SYLLABUS) == resource_type_key("Sílabo") != course_key("Sílabo")


def test_the_batch_brings_the_declared_nodes_and_edges():
    batch = assemble_batch(DECLARATION, EXTRACTED, Snapshot(), public_base_url="https://kms.example/")
    course, kind = course_key("1INF33"), resource_type_key(SYLLABUS)
    nodes = batch.nodes_by_key
    assert nodes["doc"] == NodeFact("doc", LEARNING_RESOURCE, {
        PREF_LABEL_ES: "Sílabo 1INF33", RESOURCE_LOCATOR: "https://kms.example/recursos/doc",
    })
    assert nodes[course] == NodeFact(course, COURSE, {PREF_LABEL_ES: "Bases de Datos", COURSE_CODE: "1INF33"})
    assert nodes[kind] == NodeFact(kind, RESOURCE_TYPE, {PREF_LABEL_ES: SYLLABUS})
    assert {EdgeFact(HAS_RESOURCE_TYPE, "doc", kind), EdgeFact(IS_ABOUT, "doc", course),
            EdgeFact(TEACHES_CONCEPT, course, "c"), EdgeFact(REQUIRES_CONCEPT, course, "r")} <= set(batch.edges)


def test_repeated_edges_are_merged():
    batch = assemble_batch(DECLARATION, EXTRACTED, Snapshot(), public_base_url="http://localhost")
    assert batch.edges.count(EdgeFact(PART_OF, "c", "t")) == 1


def test_an_existing_course_keeps_the_name_it_has_in_the_graph():
    course = course_key("1INF33")
    snapshot = Snapshot(nodes={course: SnapshotNode(COURSE, INSTITUTIONAL, "Bases de datos (2025)")})
    batch = assemble_batch(DECLARATION, EXTRACTED, snapshot, public_base_url="http://localhost")
    assert batch.nodes_by_key[course].properties == {PREF_LABEL_ES: "Bases de datos (2025)", COURSE_CODE: "1INF33"}
