"""Declared facts: what the operator states when submitting a document.

None of it goes through the language model (ADR-009). The keys of the course
and the resource type derive from their code and name, so a second document of
the same course merges into the same node.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from uuid import UUID, uuid5

from iekg.core.batch import Batch, EdgeFact, NodeFact, Snapshot
from iekg.graph_schema import (
    COURSE,
    COURSE_CODE,
    HAS_RESOURCE_TYPE,
    IS_ABOUT,
    LEARNING_RESOURCE,
    PREF_LABEL_EN,
    PREF_LABEL_ES,
    REQUIRES_CONCEPT,
    RESOURCE_LOCATOR,
    RESOURCE_TYPE,
    TEACHES_CONCEPT,
)

# The only resource type of the MVP, and it implies a course.
SYLLABUS = "Sílabo"
RESOURCE_TYPES = (SYLLABUS,)

# Fixed forever: changing it changes every derived key.
_NAMESPACE = UUID("6f0c51c4-8d0e-4c4b-9a43-2a1f1d8f3b7e")


@dataclass(frozen=True)
class Declaration:
    resource_key: str
    resource_type: str
    course_code: str
    course_name: str


@dataclass(frozen=True)
class ExtractedFacts:
    """What the extractor returns, with every key resolved.

    ``nodes`` are topics and concepts, new or linked; ``edges`` join them to
    each other and to knowledge units. ``taught`` and ``required`` are the
    concepts the course teaches and needs; the course edges are added here,
    because the extractor does not know the course.
    """

    nodes: tuple[NodeFact, ...] = ()
    edges: tuple[EdgeFact, ...] = ()
    taught: tuple[str, ...] = ()
    required: tuple[str, ...] = ()


def normalize_course_code(code: str) -> str:
    return code.strip().upper()


def course_key(code: str) -> str:
    return str(uuid5(_NAMESPACE, f"course/{normalize_course_code(code)}"))


def resource_type_key(name: str) -> str:
    return str(uuid5(_NAMESPACE, f"resource-type/{name}"))


def locator(public_base_url: str, resource_key: str) -> str:
    return f"{public_base_url.rstrip('/')}/resources/{resource_key}"


def assemble_batch(
    declaration: Declaration,
    extracted: ExtractedFacts,
    snapshot: Snapshot,
    *,
    public_base_url: str,
) -> Batch:
    """The batch of a run: the extracted facts plus the declared ones.

    Repeated edges are merged here, so the batch never refuses them.
    """
    course = course_key(declaration.course_code)
    resource_type = resource_type_key(declaration.resource_type)
    resource = declaration.resource_key
    declared_nodes = (
        NodeFact(resource, LEARNING_RESOURCE, {
            PREF_LABEL_ES: f"{declaration.resource_type} {normalize_course_code(declaration.course_code)}",
            RESOURCE_LOCATOR: locator(public_base_url, resource),
        }),
        _as_in_graph(NodeFact(course, COURSE, {
            PREF_LABEL_ES: declaration.course_name.strip(),
            COURSE_CODE: normalize_course_code(declaration.course_code),
        }), snapshot),
        _as_in_graph(NodeFact(resource_type, RESOURCE_TYPE, {PREF_LABEL_ES: declaration.resource_type}), snapshot),
    )
    declared_edges = (
        EdgeFact(HAS_RESOURCE_TYPE, resource, resource_type),
        EdgeFact(IS_ABOUT, resource, course),
        *(EdgeFact(TEACHES_CONCEPT, course, key) for key in extracted.taught),
        *(EdgeFact(REQUIRES_CONCEPT, course, key) for key in extracted.required),
    )
    return Batch(
        nodes=declared_nodes + extracted.nodes,
        edges=tuple(dict.fromkeys(declared_edges + extracted.edges)),
    )


def _as_in_graph(node: NodeFact, snapshot: Snapshot) -> NodeFact:
    # An existing node keeps its labels (ON CREATE), and the batch says so, so
    # the fact store holds the names the graph has.
    existing = snapshot.nodes.get(node.key)
    if existing is None:
        return node
    labels: Mapping[str, str | None] = {PREF_LABEL_ES: existing.pref_label_es, PREF_LABEL_EN: existing.pref_label_en}
    properties = {name: value for name, value in node.properties.items() if name not in labels}
    properties.update({name: value for name, value in labels.items() if value is not None})
    return NodeFact(node.key, node.label, properties)
