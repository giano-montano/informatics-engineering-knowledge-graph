"""Typed extraction contracts, and the common shape every pipeline reduces to.

Two layers on purpose:

  the LLM-facing models     what a stage asks the model to return. They differ
                            per pipeline, because the pipelines exist to
                            compare different ways of asking.
  the comparison shape      `Extraction`, which every pipeline converges to.
                            Without it, P0's free text and P3's staged output
                            could not be scored by the same code, and any
                            difference between them would be unreadable.

Nesting is deliberate: `list[Topic]` is what a partonomy looks like, and it is
also what made Groq fail before findings/0004 forced `inline_schema_defs`.
Flattening the contract to dodge that would flatten the domain too.
"""

from __future__ import annotations

import json
import re
import unicodedata
from typing import Any

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Normalisation, shared by linking and by scoring
# ---------------------------------------------------------------------------

_SPACES = re.compile(r"\s+")


def normalise(label: str) -> str:
    """Fold a label to its comparison key.

    Accents, case and spacing are presentation, not identity. Models also emit
    U+202F and friends between words (findings/0004), and `str.split()` is the
    cheapest thing that treats every Unicode space alike.
    """
    decomposed = unicodedata.normalize("NFKD", label)
    stripped = "".join(c for c in decomposed if not unicodedata.combining(c))
    return _SPACES.sub(" ", stripped).strip().casefold()


def slug(label: str) -> str:
    """A stable IRI fragment for a coined element. Deterministic by design:
    the same label must mint the same IRI on every run, or MERGE duplicates."""
    key = normalise(label)
    ascii_only = key.encode("ascii", "ignore").decode()
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", ascii_only)).strip("-") or "unnamed"


# ---------------------------------------------------------------------------
# What the model is asked to return
# ---------------------------------------------------------------------------

class ConceptOut(BaseModel):
    """A concept as the model reports it."""

    label_es: str = Field(description="The concept exactly as written in the source")
    label_en: str = Field(
        description="Canonical English label. Translate; do not copy the Spanish."
    )
    evidence: str = Field(
        default="",
        description="Short verbatim quote from the source that supports this concept",
    )


class TopicOut(BaseModel):
    """A topic and the concepts taught under it."""

    label_es: str = Field(description="The topic exactly as written in the source")
    label_en: str = Field(
        description="Canonical English label. Translate; do not copy the Spanish."
    )
    concepts: list[ConceptOut] = Field(
        default_factory=list, description="Concepts that are part of this topic"
    )


class TopicsOnly(BaseModel):
    """First stage of the multi-pass pipelines: topics before concepts."""

    topics: list[TopicOut] = Field(description="Topics taught by this course")


class ConceptsOnly(BaseModel):
    """Second stage: the concepts of one already-extracted topic."""

    concepts: list[ConceptOut] = Field(description="Concepts part of the given topic")


class TypedExtraction(BaseModel):
    """Single constrained pass: the whole partonomy in one call."""

    topics: list[TopicOut] = Field(description="Topics taught by this course")


# ---------------------------------------------------------------------------
# The comparison shape
# ---------------------------------------------------------------------------

class LinkedTopic(BaseModel):
    """A topic after the linking stage has had its say."""

    label_es: str
    label_en: str
    concepts: list[ConceptOut] = Field(default_factory=list)
    # None means the stage found no acceptable anchor. That is a result, not a
    # gap: it measures how much of a syllabus CS2023 does not cover.
    links_to_ku: str | None = None
    link_score: float | None = None
    link_method: str = "none"


class Extraction(BaseModel):
    """What every pipeline hands to validation, minting and scoring."""

    topics: list[LinkedTopic] = Field(default_factory=list)
    # Text the model returned that could not be read as the contract. Empty for
    # every constrained pipeline; the whole point of the P0 baseline is that
    # here it is not.
    unparsed: list[str] = Field(default_factory=list)

    @property
    def concept_count(self) -> int:
        return sum(len(t.concepts) for t in self.topics)

    @property
    def linked_count(self) -> int:
        return sum(1 for t in self.topics if t.links_to_ku)


def from_topics(topics: list[TopicOut]) -> Extraction:
    return Extraction(
        topics=[
            LinkedTopic(label_es=t.label_es, label_en=t.label_en, concepts=t.concepts)
            for t in topics
        ]
    )


# ---------------------------------------------------------------------------
# Reading unconstrained output (the P0 baseline)
# ---------------------------------------------------------------------------

_FENCE = re.compile(r"```(?:json)?\s*(.*?)```", re.S)


def _candidate_payloads(text: str) -> list[str]:
    """Fenced blocks first, then the whole string, then the widest brace span.

    A model answering without a schema wraps JSON in prose, in fences, or in
    neither. Trying all three is what makes the baseline a fair one: P0 must
    fail because the model was not constrained, not because the reader gave up.
    """
    blocks = [m.group(1) for m in _FENCE.finditer(text)]
    blocks.append(text)
    for opening, closing in (("{", "}"), ("[", "]")):
        start, end = text.find(opening), text.rfind(closing)
        if 0 <= start < end:
            blocks.append(text[start : end + 1])
    return blocks


def _as_mentions(value: Any) -> list[dict]:
    """Best-effort read of whatever shape the model chose for a list of things."""
    if isinstance(value, dict):
        for key in ("topics", "concepts", "entities", "nodes", "items"):
            if key in value:
                return _as_mentions(value[key])
        return []
    if not isinstance(value, list):
        return []
    out = []
    for item in value:
        if isinstance(item, str):
            out.append({"label": item, "children": []})
        elif isinstance(item, dict):
            label = next(
                (
                    str(item[k])
                    for k in ("label_en", "label", "name", "topic", "concept", "title")
                    if isinstance(item.get(k), str)
                ),
                None,
            )
            if label:
                children = next(
                    (item[k] for k in ("concepts", "children", "subtopics") if k in item),
                    [],
                )
                out.append({"label": label, "children": _as_mentions(children)})
    return out


def parse_unconstrained(text: str) -> Extraction:
    """Read free-form output into the comparison shape, keeping what fails.

    Anything unreadable lands in `unparsed`, which is the P0 measurement: the
    cost of not constraining is a count, not an opinion.
    """
    for payload in _candidate_payloads(text):
        try:
            data = json.loads(payload)
        except (json.JSONDecodeError, TypeError):
            continue
        mentions = _as_mentions(data)
        if mentions:
            return Extraction(
                topics=[
                    LinkedTopic(
                        label_es=m["label"],
                        label_en=m["label"],
                        concepts=[
                            ConceptOut(label_es=c["label"], label_en=c["label"])
                            for c in m["children"]
                        ],
                    )
                    for m in mentions
                ]
            )
    return Extraction(unparsed=[text])
