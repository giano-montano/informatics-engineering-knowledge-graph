"""Navigation queries: the derivations of R1's step 5, the search and the detail of a node.

Every query returns a piece of the graph as stored, ``{nodes, edges}``, with no
edge or node the API makes up. Each one first gathers the nodes it reaches and
then, in the same query, the edges between them: a variable-length match that
returns paths enumerates them all, while one that returns distinct nodes
visits each node once. Every node comes with its ``WAS_DERIVED_FROM`` edges
and the resources they point to, and every edge with provenance with its
resource among the nodes (RF-17).

A query is built apart from its execution, so the measurement of AC-05 runs
exactly what the routes run. Labels and edge types come from the graph schema;
everything else is a parameter. Only reads.
"""

import re
import unicodedata
from collections.abc import Mapping
from dataclasses import dataclass, field, replace
from typing import Literal

from neo4j import Driver, NotificationDisabledCategory, ResultSummary

from iekg.core.repository import Tx
from iekg.graph_schema import (
    CONCEPT,
    COURSE,
    COURSE_CODE,
    DESCRIPTION,
    EDGE_TYPES,
    HAS_PREREQUISITE,
    HAS_RESOURCE_TYPE,
    IS_ABOUT,
    KEY,
    KNOWLEDGE_AREA,
    KNOWLEDGE_ELEMENT,
    LAYER,
    LEARNING_RESOURCE,
    NODE_CLASSES,
    PART_OF,
    PREF_LABEL_EN,
    PREF_LABEL_ES,
    PROVENANCE,
    REQUIRES_CONCEPT,
    RESOURCE_LOCATOR,
    SEARCH_ANALYZER,
    SEARCH_INDEX,
    SPECIALIZES,
    TEACHES_CONCEPT,
    TOP_LEVEL_LABELS,
    TOPIC,
    WAS_DERIVED_FROM,
)

# Bounds of the responses (design of the navigation routes, sections 4 and 9).
# Provisional: the measurement reports the depth reached in the pilot.
MAX_DEPTH = 10
MAX_NEIGHBORS = 25
MAX_NEIGHBORS_OF_NEIGHBOR = 5
MAX_SEARCH_RESULTS = 20

Grain = Literal["topic", "course", "area"]
GRAINS: tuple[Grain, ...] = ("topic", "course", "area")


@dataclass(frozen=True)
class Query:
    text: str
    parameters: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class GraphNode:
    key: str
    label: str
    layer: str | None
    name_es: str | None
    name_en: str | None
    course_code: str | None = None
    locator: str | None = None
    # What the pattern says about the node; None where it does not apply.
    depth: int | None = None
    score: float | None = None
    more_neighbors: bool | None = None
    # Only the node a detail is about carries it.
    has_description: bool = False
    description: str | None = None


@dataclass(frozen=True)
class GraphEdge:
    type: str
    source: str
    target: str
    provenance: str | None


@dataclass(frozen=True)
class Subgraph:
    nodes: tuple[GraphNode, ...] = ()
    edges: tuple[GraphEdge, ...] = ()


@dataclass(frozen=True)
class Fetched:
    """A subgraph, or None if the starting node is not there, with the summary
    the server returned: its timings are what AC-05 measures."""

    subgraph: Subgraph | None
    summary: ResultSummary


def _types(*edge_types: str) -> str:
    # Interpolated into Cypher, which takes no parameters there.
    for edge_type in edge_types:
        if edge_type not in EDGE_TYPES:
            raise ValueError(f"{edge_type!r} is not declared in the graph schema")
    return "|".join(edge_types)


def _node(node: str) -> str:
    properties = (KEY, LAYER, PREF_LABEL_ES, PREF_LABEL_EN, COURSE_CODE, RESOURCE_LOCATOR)
    return "{" + ", ".join(f"{name}: {node}.{name}" for name in properties) + f", labels: labels({node})}}"


def _any_of(*labels: str) -> str:
    """Match ``start`` by key under each label with a uniqueness constraint,
    so the lookup goes through the index."""
    branches = " UNION ".join(f"MATCH (start:{label} {{{KEY}: $key}}) RETURN start" for label in labels)
    return f"CALL () {{ {branches} }}\n"


# Takes ``found``, a list of maps with the node under ``node`` and what the
# pattern says about it, and adds the edges between the nodes and their
# provenance.
_TAIL = f"""
WITH found, [f IN found | f.node] AS ns
WITH found, ns, {{among}} AS among,
     COLLECT {{ UNWIND ns AS a MATCH (a)-[r:{WAS_DERIVED_FROM}]->(:{LEARNING_RESOURCE}) RETURN r }} AS derivations
WITH found, among + derivations AS rels, [r IN derivations | endNode(r)] AS sources,
     [r IN among WHERE r.{PROVENANCE} IS NOT NULL | r.{PROVENANCE}] AS cited
WITH found, rels,
     sources + COLLECT {{ MATCH (s:{LEARNING_RESOURCE}) WHERE s.{KEY} IN cited RETURN s }} AS sources
RETURN [f IN found | f {{.*, node: {_node("f.node")}}}] AS found,
       [s IN sources | {_node("s")}] AS sources,
       [r IN rels | {{type: type(r), source: startNode(r).{KEY}, target: endNode(r).{KEY},
                      provenance: r.{PROVENANCE}}}] AS edges
"""


def _with_tail(head: str, among: str | None) -> str:
    """``among`` is the relationship type expression of the edges kept between
    the nodes; None keeps none."""
    collected = f"COLLECT {{ UNWIND ns AS a MATCH (a)-[r:{among}]->(b) WHERE b IN ns RETURN r }}" if among else "[]"
    return head + _TAIL.replace("{among}", collected)


def _closure(var: str, step: str, end: str, name: str) -> str:
    # min(length(path)) per end node keeps the breadth-first expansion that
    # prunes, like DISTINCT does; returning the paths would enumerate them all.
    return (
        f"CALL ({var}) {{ MATCH path = {step} WITH {end}, min(length(path)) AS depth "
        f"RETURN collect({{node: {end}, depth: depth}}) AS {name} }}\n"
    )


# --- RF-11: the prerequisites of a concept ----------------------------------

_CONCEPT_PREREQUISITES = _with_tail(
    f"MATCH (c:{CONCEPT} {{{KEY}: $key}})\n"
    + _closure("c", f"(c)-[:{HAS_PREREQUISITE}*1..{MAX_DEPTH}]->(p)", "p", "reached")
    + "WITH [{node: c, depth: 0}] + reached AS found\n",
    _types(HAS_PREREQUISITE),
)


def concept_prerequisites(key: str) -> Query:
    """The concept and its prerequisites, transitively up to ``MAX_DEPTH`` (RF-11)."""
    return Query(_CONCEPT_PREREQUISITES, {"key": key})


# --- RF-12, PC2: prerequisite between courses -------------------------------

_COURSE_PREREQUISITES = _with_tail(
    f"""MATCH (z:{COURSE} {{{KEY}: $key}})
WITH z,
     COLLECT {{ MATCH (z)-[:{TEACHES_CONCEPT}]->(c) RETURN c }} AS taught,
     COLLECT {{ MATCH (z)-[:{REQUIRES_CONCEPT}]->(c) RETURN c }} AS required
WITH z, taught, required,
     COLLECT {{ UNWIND required AS c MATCH (x:{COURSE})-[:{TEACHES_CONCEPT}]->(c) WHERE x <> z RETURN DISTINCT x }} AS preceding
WITH [n IN [z] + taught + required + preceding | {{node: n}}] AS found
""",
    _types(TEACHES_CONCEPT, REQUIRES_CONCEPT),
)


def course_prerequisites(key: str) -> Query:
    """What the course teaches and requires, and the courses that teach what it
    requires: X precedes Z if X teaches a concept Z requires (RF-12, PC2)."""
    return Query(_COURSE_PREREQUISITES, {"key": key})


# --- RF-13, PC3: location and composition -----------------------------------

_LOCATION = _with_tail(
    f"""MATCH (e:{KNOWLEDGE_ELEMENT} {{{KEY}: $key}})
WITH e,
     COLLECT {{ MATCH (e)-[:{PART_OF}*1..{MAX_DEPTH}]->(w) RETURN DISTINCT w }} AS wholes,
     COLLECT {{ MATCH (p)-[:{PART_OF}*1..{MAX_DEPTH}]->(e) RETURN DISTINCT p }} AS parts
WITH [n IN [e] + wholes + parts | {{node: n}}] AS found
""",
    # The prerequisites among the parts give the order to learn them in (PC4).
    _types(PART_OF, HAS_PREREQUISITE),
)


def element_location(key: str) -> Query:
    """What the element is part of, up to its area, and what is part of it (RF-13, PC3)."""
    return Query(_LOCATION, {"key": key})


# --- RF-14, PC5: resources rolled up over the parts --------------------------

_RESOURCES = _with_tail(
    _any_of(KNOWLEDGE_ELEMENT, COURSE)
    + f"""WITH start AS x, COLLECT {{ MATCH (p)-[:{PART_OF}*1..{MAX_DEPTH}]->(start) RETURN DISTINCT p }} AS parts
WITH x, parts, [p IN parts WHERE EXISTS {{ (:{LEARNING_RESOURCE})-[:{IS_ABOUT}]->(p) }}] AS covered
WITH x, covered,
     COLLECT {{ UNWIND covered AS c MATCH (c)-[:{PART_OF}*1..{MAX_DEPTH}]->(w) WHERE w IN parts RETURN DISTINCT w }} AS between,
     COLLECT {{ UNWIND [x] + covered AS c MATCH (r:{LEARNING_RESOURCE})-[:{IS_ABOUT}]->(c) RETURN DISTINCT r }} AS resources
WITH x, covered, between, resources,
     COLLECT {{ UNWIND resources AS r MATCH (r)-[:{HAS_RESOURCE_TYPE}]->(t) RETURN DISTINCT t }} AS types
WITH [n IN [x] + covered + between + resources + types | {{node: n}}] AS found
""",
    _types(IS_ABOUT, PART_OF, HAS_RESOURCE_TYPE),
)


def element_resources(key: str) -> Query:
    """The resources about the element and about any of its parts, with the
    parts that lead to them and the resource types (RF-14, PC5)."""
    return Query(_RESOURCES, {"key": key})


# --- RF-15, PC6: prerequisite lifted to a grain -----------------------------

# A course target is not lifted to itself: what it teaches is inside it, so it
# is never a prerequisite.
_LIFT: Mapping[str, str] = {
    "topic": f"""UNWIND prerequisites AS q WITH q.node AS p, q.depth AS depth
    MATCH (p)-[:{PART_OF}]->(g:{TOPIC})
    WITH g, min(depth) AS depth RETURN collect({{node: g, depth: depth}}) AS lifted""",
    "area": f"""UNWIND prerequisites AS q WITH q.node AS p, q.depth AS depth
    CALL (p) {{ MATCH (p)-[:{PART_OF}*1..{MAX_DEPTH}]->(g) RETURN DISTINCT g }}
    WITH g, min(depth) AS depth
    RETURN collect(CASE WHEN g:{KNOWLEDGE_AREA} THEN {{node: g, depth: depth}} ELSE {{node: g}} END) AS lifted""",
    "course": f"""UNWIND prerequisites AS q WITH q.node AS p, q.depth AS depth
    MATCH (g:{COURSE})-[:{TEACHES_CONCEPT}]->(p)
    WITH g, min(depth) AS depth RETURN collect({{node: g, depth: depth}}) AS lifted""",
}


def _learning_path(grain: str) -> str:
    return _with_tail(
        _any_of(KNOWLEDGE_ELEMENT, COURSE)
        + f"""WITH start AS t, COLLECT {{ MATCH (p)-[:{PART_OF}*1..{MAX_DEPTH}]->(start) RETURN DISTINCT p }} AS parts
WITH t, parts,
     CASE WHEN t:{CONCEPT} THEN [t]
          ELSE [p IN parts WHERE p:{CONCEPT}] + COLLECT {{ MATCH (t)-[:{TEACHES_CONCEPT}]->(c) RETURN c }}
     END AS inside
CALL (inside) {{
    UNWIND inside AS c
    MATCH path = (c)-[:{HAS_PREREQUISITE}*1..{MAX_DEPTH}]->(p) WHERE NOT p IN inside
    WITH p, min(length(path)) AS depth
    RETURN collect({{node: p, depth: depth}}) AS prerequisites
}}
CALL (prerequisites) {{
    {_LIFT[grain]}
}}
WITH t, parts, inside, prerequisites, lifted, [q IN prerequisites | q.node] AS outside
WITH t, parts, prerequisites, lifted,
     [c IN inside WHERE EXISTS {{ (c)-[:{HAS_PREREQUISITE}]->(p) WHERE p IN outside }}] AS frontier
WITH t, prerequisites, lifted, frontier,
     COLLECT {{ UNWIND frontier AS f MATCH (f)-[:{PART_OF}*1..{MAX_DEPTH}]->(w) WHERE w IN parts RETURN DISTINCT w }} AS within
WITH [n IN [t] + frontier + within | {{node: n, depth: 0}}] + prerequisites + lifted AS found
""",
        _types(HAS_PREREQUISITE, PART_OF, TEACHES_CONCEPT),
    )


_LEARNING_PATHS: Mapping[str, str] = {grain: _learning_path(grain) for grain in GRAINS}


def learning_path(key: str, grain: Grain) -> Query:
    """What to learn before a concept, topic, unit, area or course, lifted to
    topics, courses or areas, with the evidence (RF-15, PC6).

    ``depth`` is 0 inside the target; for a prerequisite, its distance from the
    target, and for a topic, course or area of the grain, that of its nearest
    prerequisite.
    """
    return Query(_LEARNING_PATHS[grain], {"key": key})


# --- RF-16, PC7: specialization closure -------------------------------------

_SPECIALIZATIONS = _with_tail(
    f"MATCH (c:{CONCEPT} {{{KEY}: $key}})\n"
    + _closure("c", f"(c)-[:{SPECIALIZES}*1..{MAX_DEPTH}]->(g)", "g", "general")
    + _closure("c", f"(s)-[:{SPECIALIZES}*1..{MAX_DEPTH}]->(c)", "s", "specific")
    + "WITH [{node: c, depth: 0}] + general + specific AS found\n",
    _types(SPECIALIZES),
)


def concept_specializations(key: str) -> Query:
    """What the concept is a kind of, and what is a kind of it, transitively (RF-16, PC7)."""
    return Query(_SPECIALIZATIONS, {"key": key})


# --- Detail of a node --------------------------------------------------------

_NOT_DERIVATION = f"!{WAS_DERIVED_FROM}"

# Outgoing edges first, so a capped list keeps what the node is part of.
_DETAIL = _with_tail(
    _any_of(*TOP_LEVEL_LABELS)
    + f"""WITH start AS x
CALL (x) {{
    MATCH (x)-[r:{_NOT_DERIVATION}]-(n) WHERE n <> x
    WITH n, min(CASE WHEN startNode(r) = x THEN 0 ELSE 1 END) AS direction, min(type(r)) AS type
    ORDER BY direction, type, n.{PREF_LABEL_ES}, n.{KEY}
    LIMIT {MAX_NEIGHBORS}
    RETURN collect(n) AS direct
}}
CALL (x, direct) {{
    UNWIND direct AS d
    CALL (x, d, direct) {{
        MATCH (d)-[r:{_NOT_DERIVATION}]-(m) WHERE m <> x AND NOT m IN direct
        WITH m, min(CASE WHEN startNode(r) = d THEN 0 ELSE 1 END) AS direction, min(type(r)) AS type
        ORDER BY direction, type, m.{PREF_LABEL_ES}, m.{KEY}
        LIMIT {MAX_NEIGHBORS_OF_NEIGHBOR}
        RETURN m
    }}
    RETURN collect(DISTINCT m) AS second
}}
WITH x, [x] + direct + second AS ns
WITH [n IN ns | {{node: n, more_neighbors: EXISTS {{ (n)-[:{_NOT_DERIVATION}]-(y) WHERE NOT y IN ns }}}}]
     AS found, x
WITH [{{node: x, description: x.{DESCRIPTION}}}] + found AS found
""",
    _NOT_DERIVATION,
)


def node_detail(key: str) -> Query:
    """The node with its description, its direct neighbors and a few of theirs,
    by any edge but ``WAS_DERIVED_FROM``; the order is fixed when they are capped."""
    return Query(_DETAIL, {"key": key})


# --- RF-18: search by name ---------------------------------------------------

_SEARCH = _with_tail(
    """CALL db.index.fulltext.queryNodes($index, $lucene) YIELD node, score
WITH node, score ORDER BY score DESC, node.key LIMIT $limit
WITH collect({node: node, score: score}) AS found
""".replace("node.key", f"node.{KEY}"),
    # Results stand alone: the edges between them say nothing about the search.
    None,
)

_STOPWORDS = """
CALL db.index.fulltext.listAvailableAnalyzers() YIELD analyzer, stopwords
WHERE analyzer = $analyzer
RETURN stopwords
"""


def words(text: str) -> list[str]:
    """The words of ``text`` as the index holds them: no accents, lower case,
    split where the tokenizer splits.

    The tokenizer splits on anything but letters and digits, except a period,
    an apostrophe or an underscore between them ("node.js", "802.11",
    "o'reilly"). Wildcard terms skip the analyzer, so the query has to fold
    them itself; and none of those characters is Lucene syntax, so there is
    nothing to escape.
    """
    folded = "".join(
        ch for ch in unicodedata.normalize("NFD", text) if not unicodedata.combining(ch)
    )
    return re.findall(r"[^\W_]+(?:[._'][^\W_]+)*", folded.lower().replace("’", "'"))


def lucene_query(text: str, stopwords: frozenset[str]) -> str | None:
    """Every word as a prefix, and all of them required.

    A stop word is left optional: the analyzer drops it from the index, so
    requiring it would find nothing ("a" in "Programación orientada a objetos").
    None if the text has no words.
    """
    terms = [f"{word}*" if word in stopwords else f"+{word}*" for word in dict.fromkeys(words(text))]
    return " ".join(terms) or None


def search(text: str, stopwords: frozenset[str]) -> Query | None:
    """The nodes whose names or course code match every word of ``text`` by
    prefix, by score (RF-18); None if the text has no words."""
    lucene = lucene_query(text, stopwords)
    if lucene is None:
        return None
    return Query(_SEARCH, {"index": SEARCH_INDEX, "lucene": lucene, "limit": MAX_SEARCH_RESULTS})


def stopwords_in(tx: Tx) -> frozenset[str]:
    """The stop words of the search index's analyzer, as the server declares them."""
    record = tx.run(_STOPWORDS, analyzer=SEARCH_ANALYZER).single()
    if record is None:
        raise LookupError(f"the server has no analyzer {SEARCH_ANALYZER!r}")
    return frozenset(record["stopwords"])


# --- Execution ---------------------------------------------------------------


def fetch_in(tx: Tx, query: Query) -> Fetched:
    result = tx.run(query.text, query.parameters)
    record = result.single()
    summary = result.consume()
    return Fetched(_subgraph(record) if record is not None else None, summary)


def _subgraph(record) -> Subgraph:
    nodes: dict[str, GraphNode] = {}
    for found in record["found"]:
        node = _graph_node(found["node"], found)
        known = nodes.get(node.key)
        nodes[node.key] = _merge(known, node) if known else node
    for source in record["sources"]:
        nodes.setdefault(source[KEY], _graph_node(source, {}))
    edges = dict.fromkeys(
        GraphEdge(edge["type"], edge["source"], edge["target"], edge["provenance"]) for edge in record["edges"]
    )
    return Subgraph(tuple(nodes.values()), tuple(edges))


def _graph_node(projected: Mapping, about: Mapping) -> GraphNode:
    classes = [label for label in projected["labels"] if label in NODE_CLASSES]
    return GraphNode(
        key=projected[KEY],
        # RI-02 and RI-03: one class besides the abstract KnowledgeElement.
        label=classes[0] if len(classes) == 1 else KNOWLEDGE_ELEMENT,
        layer=projected[LAYER],
        name_es=projected[PREF_LABEL_ES],
        name_en=projected[PREF_LABEL_EN],
        course_code=projected[COURSE_CODE],
        locator=projected[RESOURCE_LOCATOR],
        depth=about.get("depth"),
        score=about.get("score"),
        more_neighbors=about.get("more_neighbors"),
        has_description="description" in about,
        description=about.get("description"),
    )


def _merge(known: GraphNode, other: GraphNode) -> GraphNode:
    # A node reached twice keeps its least depth and what either said of it.
    said = {name: value for name, value in vars(other).items() if value is not None and name != "depth"}
    said["has_description"] = known.has_description or other.has_description
    depths = [d for d in (known.depth, other.depth) if d is not None]
    return replace(known, **said, depth=min(depths) if depths else None)


class Neo4jNavigation:
    """Runs the navigation queries in read sessions."""

    def __init__(self, driver: Driver, database: str) -> None:
        self._driver = driver
        self._database = database
        self._stopwords: frozenset[str] | None = None

    def _session(self):
        # A base without institutional data does not know some labels and properties.
        return self._driver.session(
            database=self._database,
            notifications_disabled_categories=[NotificationDisabledCategory.UNRECOGNIZED],
        )

    def fetch(self, query: Query) -> Subgraph | None:
        with self._session() as session:
            return session.execute_read(fetch_in, query).subgraph

    def stopwords(self) -> frozenset[str]:
        if self._stopwords is None:
            with self._session() as session:
                self._stopwords = session.execute_read(stopwords_in)
        return self._stopwords
