import re

import pytest

from iekg.core.auditor import query_for
from iekg.core.rules import ALL_RULES, STATEMENTS
from iekg.graph_schema import (
    ADMITTED_PAIRS,
    ALL_LABELS,
    EDGE_PROPERTIES_BY_SOURCE_LAYER,
    EDGE_TYPES,
    KNOWLEDGE_ELEMENT,
    LAYERS,
    LOCATOR_PATTERN,
    NODE_CLASSES,
    NODE_PROPERTIES,
    TOP_LEVEL_LABELS,
)


def test_eight_labels_and_eight_edge_types():
    assert len(ALL_LABELS) == len(set(ALL_LABELS)) == 8
    assert len(EDGE_TYPES) == len(set(EDGE_TYPES)) == 8


def test_admitted_pairs_join_node_classes():
    assert set(ADMITTED_PAIRS) == set(EDGE_TYPES)
    for pairs in ADMITTED_PAIRS.values():
        for source, target in pairs:
            assert source in NODE_CLASSES and target in NODE_CLASSES


def test_unions_expand_into_five_pairs():
    assert len(ADMITTED_PAIRS["IS_ABOUT"]) == 5
    assert len(ADMITTED_PAIRS["WAS_DERIVED_FROM"]) == 5


def test_knowledge_element_is_abstract():
    assert KNOWLEDGE_ELEMENT in TOP_LEVEL_LABELS
    assert KNOWLEDGE_ELEMENT not in NODE_CLASSES


def test_every_label_and_source_layer_declares_its_properties():
    assert set(NODE_PROPERTIES) == set(ALL_LABELS)
    assert set(EDGE_PROPERTIES_BY_SOURCE_LAYER) == set(LAYERS)
    names = {name for names in NODE_PROPERTIES.values() for name in names}
    names |= {name for names in EDGE_PROPERTIES_BY_SOURCE_LAYER.values() for name in names}
    assert all(re.fullmatch(r"[a-z][A-Za-z]*", name) for name in names)


@pytest.mark.parametrize("locator", [
    "https://dl.acm.org/doi/book/10.1145/3664191",
    "http://localhost:8000/recursos/abc",
    "HTTPS://example.org",
])
def test_locator_pattern_accepts_absolute_http_uris(locator):
    assert re.fullmatch(LOCATOR_PATTERN, locator)


@pytest.mark.parametrize("locator", [
    "ftp://example.org/file",
    "/recursos/abc",
    "https://",
    "https://example.org/with space",
    "urn:isbn:123",
])
def test_locator_pattern_rejects_anything_else(locator):
    assert not re.fullmatch(LOCATOR_PATTERN, locator)


def test_every_rule_has_a_statement_and_an_audit_query():
    assert len(ALL_RULES) == 15
    for rule in ALL_RULES:
        assert STATEMENTS[rule]
        assert "element" in query_for(rule)
