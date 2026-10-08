"""Extractor: document and snapshot -> facts with resolved keys.

Docling reads the PDF; PydanticAI asks the model for an output typed by
``SyllabusOutput``; then deterministic code resolves every mention (ADR-003,
ADR-011). The model sees the vocabulary under short references (``K-001``,
``T-001``, ``C-001``) instead of the keys: shorter to copy, and the prefix
tells the class. A reference that is not in the vocabulary is EX-02; one of
another class than its place requires is EX-03; anything the output schema
refuses is EX-01. The three share the single content retry (ADR-010).
"""

import hashlib
import json
import os
import re
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from pydantic import BaseModel, Field, model_validator
from pydantic_ai import Agent, NativeOutput, capture_run_messages
from pydantic_ai.exceptions import ModelAPIError, UnexpectedModelBehavior
from pydantic_ai.messages import ModelMessage, ModelRequest, ModelResponse, RetryPromptPart, TextPart
from pydantic_ai.models import Model

from iekg.core.batch import EdgeFact, NodeFact, Snapshot
from iekg.graph_schema import (
    CONCEPT,
    HAS_PREREQUISITE,
    KNOWLEDGE_AREA,
    KNOWLEDGE_UNIT,
    PART_OF,
    PREF_LABEL_EN,
    PREF_LABEL_ES,
    SPECIALIZES,
    TOPIC,
)
from iekg.ingestion.declared import ExtractedFacts
from iekg.ingestion.extraction import EX_01, EX_02, EX_03, NonConformingOutput, ProviderFailure
from iekg.ingestion.normalization import normalize_label
from iekg.operational_store import Discard, Extraction

# --- Output schema --------------------------------------------------------------

_EXISTING = "Reference of the existing {kind} it is the same knowledge as, or null if it is new."


class ConceptMention(BaseModel):
    name: str = Field(description="The concept as the syllabus names it, in its language.")
    existing: str | None = Field(None, description=_EXISTING.format(kind="concept (C-…)"))


class TopicMention(BaseModel):
    name: str = Field(description="The topic as the syllabus names it, without numbering, chapter word or hours.")
    existing: str | None = Field(None, description=_EXISTING.format(kind="topic (T-…)"))
    knowledge_unit: str | None = Field(
        None, description="For a new topic, the reference (K-…) of the one knowledge unit it belongs to."
    )
    concepts: list[ConceptMention] = Field(description="The concepts the syllabus teaches under this topic.")


class RequiredConcept(BaseModel):
    name: str = Field(description="A concept the course needs and does not teach.")
    existing: str | None = Field(None, description=_EXISTING.format(kind="concept (C-…)"))
    topic: str | None = Field(
        None,
        description="For a new concept, the topic it belongs to: an existing topic (T-…) or a topic of this output.",
    )


class Prerequisite(BaseModel):
    concept: str = Field(description="A concept of this output, or an existing concept (C-…).")
    prerequisite: str = Field(description="The concept that must be learnt before it, named the same way.")


class Specialization(BaseModel):
    concept: str = Field(description="A concept of this output, or an existing concept (C-…).")
    generalization: str = Field(description="The more general concept it specializes, named the same way.")


class SyllabusOutput(BaseModel):
    """The topics and concepts of one syllabus."""

    topics: list[TopicMention] = Field(min_length=1)
    required_concepts: list[RequiredConcept] = []
    prerequisites: list[Prerequisite] = []
    specializations: list[Specialization] = []

    @model_validator(mode="after")
    def _check_structure(self) -> "SyllabusOutput":
        problems = []
        for topic in self.topics:
            if topic.existing is None and topic.knowledge_unit is None:
                problems.append(f"new topic {topic.name!r} has no knowledge_unit")
        topics = {normalize_label(topic.name) for topic in self.topics}
        for required in self.required_concepts:
            if required.existing is None:
                if required.topic is None:
                    problems.append(f"new required concept {required.name!r} has no topic")
                elif not _is_ref(required.topic) and normalize_label(required.topic) not in topics:
                    problems.append(f"required concept {required.name!r}: topic {required.topic!r} is not in the output")
        concepts = {normalize_label(c.name) for topic in self.topics for c in topic.concepts}
        concepts |= {normalize_label(c.name) for c in self.required_concepts}
        for relation in [*self.prerequisites, *self.specializations]:
            for end in _ends(relation):
                if not _is_ref(end) and normalize_label(end) not in concepts:
                    problems.append(f"relation end {end!r} is neither a concept of the output nor a C- reference")
        if problems:
            raise ValueError("; ".join(problems))
        return self


_REF = re.compile(r"[KTC]-\d+")


def _is_ref(text: str) -> bool:
    return _REF.fullmatch(text.strip()) is not None


def _ends(relation: Prerequisite | Specialization) -> tuple[str, str]:
    if isinstance(relation, Prerequisite):
        return relation.concept, relation.prerequisite
    return relation.concept, relation.generalization


# --- Prompt ---------------------------------------------------------------------------

INSTRUCTIONS = """\
You extract the knowledge structure of a university course syllabus for a curriculum knowledge graph.

- A topic is the title of a unit or chapter of the syllabus program that groups items. Name it as the \
syllabus does, but without numbering, the word "chapter" or "unit", weeks or hours: "CAPÍTULO 3 SQL DDL \
(3 horas)" is the topic "SQL DDL".
- A concept is each item inside a topic: one piece of knowledge, named as the syllabus names it. An item \
that names two pieces of knowledge gives two concepts. Concepts from the summary or the objectives that no \
topic groups go under the closest topic of this syllabus.
- Keep the language of the syllabus. Do not translate, summarize or invent knowledge the syllabus does not state.
- Every new topic belongs to exactly one knowledge unit of the vocabulary: the one whose subject it is, \
judged by the unit and its area. A topic that already exists keeps its unit.
- Reuse what exists: when a topic or concept is the same knowledge as one in the vocabulary, give its \
reference in "existing". Otherwise leave "existing" null.
- Required concepts are what the course needs and does not teach, as its requirements or prerequisites \
state. Prefer an existing concept; if there is none, add it as new and give the topic it belongs to.
- Prerequisites and specializations join concepts only when the syllabus supports them.
- References are only the ones listed in the vocabulary, copied exactly.
"""


def render_prompt(document_text: str, vocabulary_text: str) -> str:
    return f"# Vocabulary of the graph\n\n{vocabulary_text}\n\n# Syllabus\n\n{document_text}"


def prompt_version() -> str:
    """A digest of the instructions and the output schema: it changes whenever either does."""
    text = INSTRUCTIONS + json.dumps(SyllabusOutput.model_json_schema(), sort_keys=True)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]


# --- Vocabulary -------------------------------------------------------------------------

_PREFIX = {KNOWLEDGE_UNIT: "K", TOPIC: "T", CONCEPT: "C"}


@dataclass(frozen=True)
class Vocabulary:
    refs: dict[str, str]
    text: str


def build_vocabulary(snapshot: Snapshot) -> Vocabulary:
    parents = {edge.source: edge.target for edge in snapshot.edges if edge.type == PART_OF}

    def label(key: str | None) -> str:
        node = snapshot.nodes.get(key) if key else None
        if node is None:
            return "?"
        return " / ".join(dict.fromkeys(x for x in (node.pref_label_es, node.pref_label_en) if x)) or key

    refs: dict[str, str] = {}
    sections = []
    for kind, title in ((KNOWLEDGE_UNIT, "Knowledge units (area › unit)"), (TOPIC, "Existing topics"),
                        (CONCEPT, "Existing concepts")):
        keys = sorted((k for k, n in snapshot.nodes.items() if n.label == kind), key=lambda k: (
            label(snapshot.nodes[k].area) if kind == KNOWLEDGE_UNIT else "", label(k), k))
        lines = []
        for number, key in enumerate(keys, 1):
            ref = f"{_PREFIX[kind]}-{number:03d}"
            refs[ref] = key
            if kind == KNOWLEDGE_UNIT:
                lines.append(f"{ref}  {label(snapshot.nodes[key].area)} › {label(key)}")
            else:
                lines.append(f"{ref}  {label(key)}")
        sections.append((title, lines))
    # Where each existing topic and concept hangs, by reference.
    ref_of_key = {key: ref for ref, key in refs.items()}
    text = []
    for title, lines in sections:
        text.append(f"## {title}\n" + ("\n".join(lines) if lines else "(none)"))
    if parents:
        placement = sorted(
            f"{ref_of_key[child]} part of {ref_of_key[parent]}"
            for child, parent in parents.items() if child in ref_of_key and parent in ref_of_key
        )
        text.append("## Placement\n" + "\n".join(placement))
    return Vocabulary(refs, "\n\n".join(text))


# --- Linking ---------------------------------------------------------------------------


class _Linker:
    """Resolves the mentions of one output into nodes and edges, or into discards."""

    def __init__(self, snapshot: Snapshot, vocabulary: Vocabulary, new_key: Callable[[], str]) -> None:
        self.snapshot = snapshot
        self.vocabulary = vocabulary
        self.new_key = new_key
        self.discards: list[Discard] = []
        self.nodes: dict[str, NodeFact] = {}
        self.edges: list[EdgeFact] = []
        # Existing nodes by normalized label, per class, for mentions marked as new.
        self.by_label: dict[tuple[str, str], str] = {}
        for key, node in sorted(snapshot.nodes.items()):
            for text in (node.pref_label_es, node.pref_label_en):
                if text and node.label in (TOPIC, CONCEPT):
                    self.by_label.setdefault((node.label, normalize_label(text)), key)
        # Mentions of this output, merged by normalized label, per class.
        self.minted: dict[tuple[str, str], str] = {}

    def resolve(self, ref: str, label: str, place: str) -> str | None:
        """The key of an existing node; None, with a discard, if the reference does not fit."""
        key = self.vocabulary.refs.get(ref.strip())
        if key is None:
            self.discards.append(Discard(EX_02, f"{place}: {ref!r}", "the reference is not in the vocabulary"))
            return None
        actual = self.snapshot.nodes[key].label
        if actual != label:
            self.discards.append(Discard(EX_03, f"{place}: {ref!r}", f"the reference is a {actual}, not a {label}"))
            return None
        return key

    def node(self, label: str, name: str, existing: str | None, place: str) -> str | None:
        if existing is not None:
            key = self.resolve(existing, label, place)
            if key is None:
                return None
        else:
            normalized = normalize_label(name)
            key = self.by_label.get((label, normalized)) or self.minted.get((label, normalized))
            if key is None:
                key = self.minted[(label, normalized)] = self.new_key()
        if key not in self.nodes:
            self.nodes[key] = self._fact(key, label, name)
        return key

    def _fact(self, key: str, label: str, name: str) -> NodeFact:
        # A linked node is named in the batch as the graph names it.
        existing = self.snapshot.nodes.get(key)
        if existing is None:
            return NodeFact(key, label, {PREF_LABEL_ES: name.strip()})
        labels = {PREF_LABEL_ES: existing.pref_label_es, PREF_LABEL_EN: existing.pref_label_en}
        return NodeFact(key, label, {prop: value for prop, value in labels.items() if value is not None})

    def link(self, output: SyllabusOutput) -> ExtractedFacts | None:
        topics: dict[str, str] = {}
        concepts: dict[str, str] = {}
        taught: list[str] = []
        for topic in output.topics:
            place = f"topic {topic.name!r}"
            key = self.node(TOPIC, topic.name, topic.existing, place)
            if key is None:
                continue
            topics.setdefault(normalize_label(topic.name), key)
            # A topic that already exists keeps its unit.
            if key not in self.snapshot.nodes and topic.knowledge_unit is not None:
                unit = self.resolve(topic.knowledge_unit, KNOWLEDGE_UNIT, f"{place}, knowledge_unit")
                if unit is not None:
                    self.edges.append(EdgeFact(PART_OF, key, unit))
            for concept in topic.concepts:
                concept_key = self.node(CONCEPT, concept.name, concept.existing, f"concept {concept.name!r}")
                if concept_key is not None:
                    concepts.setdefault(normalize_label(concept.name), concept_key)
                    self.edges.append(EdgeFact(PART_OF, concept_key, key))
                    taught.append(concept_key)

        required: list[str] = []
        for concept in output.required_concepts:
            place = f"required concept {concept.name!r}"
            key = self.node(CONCEPT, concept.name, concept.existing, place)
            if key is None:
                continue
            concepts.setdefault(normalize_label(concept.name), key)
            required.append(key)
            if key not in self.snapshot.nodes and concept.topic is not None:
                topic = (self.resolve(concept.topic, TOPIC, f"{place}, topic") if _is_ref(concept.topic)
                         else topics.get(normalize_label(concept.topic)))
                if topic is not None:
                    self.edges.append(EdgeFact(PART_OF, key, topic))

        for edge_type, relations in ((HAS_PREREQUISITE, output.prerequisites), (SPECIALIZES, output.specializations)):
            for relation in relations:
                ends = [
                    self.resolve(end, CONCEPT, f"relation end {end!r}") if _is_ref(end)
                    else concepts.get(normalize_label(end))
                    for end in _ends(relation)
                ]
                if None not in ends:
                    self.edges.append(EdgeFact(edge_type, ends[0], ends[1]))

        if self.discards:
            return None
        taught = list(dict.fromkeys(taught))
        # A concept the course teaches is not one it requires.
        required = [key for key in dict.fromkeys(required) if key not in taught]
        return ExtractedFacts(
            nodes=tuple(self.nodes.values()),
            edges=tuple(dict.fromkeys(self.edges)),
            taught=tuple(taught),
            required=tuple(required),
        )


def link_output(
    output: SyllabusOutput,
    snapshot: Snapshot,
    vocabulary: Vocabulary,
    new_key: Callable[[], str] = lambda: str(uuid4()),
) -> ExtractedFacts | list[Discard]:
    """Resolve every mention: the facts, or the EX-02 and EX-03 discards."""
    linker = _Linker(snapshot, vocabulary, new_key)
    facts = linker.link(output)
    return facts if facts is not None else linker.discards


# --- Reading and asking -------------------------------------------------------------------


def read_document(path: Path) -> str:
    """The PDF as Markdown. Syllabi are digital PDFs, so OCR is off."""
    # torch.compile calls MSVC on Windows, which is not there (measured in the lab).
    os.environ.setdefault("TORCHDYNAMO_DISABLE", "1")
    from docling.datamodel.base_models import InputFormat
    from docling.datamodel.pipeline_options import PdfPipelineOptions
    from docling.document_converter import DocumentConverter, PdfFormatOption

    converter = DocumentConverter(
        format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=PdfPipelineOptions(do_ocr=False))}
    )
    return converter.convert(path).document.export_to_markdown()


# One content retry, shared by EX-01, EX-02 and EX-03 (ADR-010).
CONTENT_RETRIES = 1


class LanguageModelExtractor:
    def __init__(
        self,
        model: Model,
        *,
        model_settings: dict,
        settings_record: dict,
        reader: Callable[[Path], str] = read_document,
        new_key: Callable[[], str] = lambda: str(uuid4()),
    ) -> None:
        self._agent = Agent(
            model, output_type=NativeOutput(SyllabusOutput), instructions=INSTRUCTIONS, model_settings=model_settings
        )
        self._model_name = model.model_name
        self._settings_record = settings_record
        self._reader = reader
        self._new_key = new_key

    def extract(self, document: Path, snapshot: Snapshot) -> tuple[ExtractedFacts, Extraction]:
        text = self._reader(document)
        vocabulary = build_vocabulary(snapshot)
        history: list[ModelMessage] = []
        prompt = render_prompt(text, vocabulary.text)
        # Schema retries are PydanticAI's (retry prompts in the history); a
        # reference retry is ours. Both draw on the same budget.
        reference_retries = 0
        while True:
            used = _retries_in(history) + reference_retries
            output = self._ask(prompt, history, CONTENT_RETRIES - used)
            used = _retries_in(history) + reference_retries
            linked = link_output(output, snapshot, vocabulary, self._new_key)
            if isinstance(linked, ExtractedFacts):
                return linked, self._extraction(history, used)
            if used >= CONTENT_RETRIES:
                raise NonConformingOutput(linked, _last_text(history), self._extraction(history, used))
            reference_retries += 1
            prompt = "Some references do not fit. Answer again with the whole output corrected:\n" + "\n".join(
                f"- {d.fact}: {d.message}" for d in linked
            )

    def _ask(self, prompt: str, history: list[ModelMessage], budget: int) -> SyllabusOutput:
        """One agent run, which may spend ``budget`` schema retries; extends ``history``."""
        with capture_run_messages() as messages:
            try:
                result = self._agent.run_sync(prompt, message_history=list(history), retries={"output": budget})
            except UnexpectedModelBehavior as error:
                history[:] = messages
                raise NonConformingOutput(
                    [Discard(EX_01, "output", str(error.__cause__ or error))],
                    _last_text(history),
                    self._extraction(history, CONTENT_RETRIES),
                ) from error
            except ModelAPIError as error:
                history[:] = messages
                raise ProviderFailure(str(error), self._extraction(history, _retries_in(history))) from error
        history[:] = result.all_messages()
        return result.output

    def _extraction(self, history: Sequence[ModelMessage], retries: int) -> Extraction:
        # With typed output the last message may lack the model name: walk back.
        answered = next((m.model_name for m in reversed(history) if isinstance(m, ModelResponse) and m.model_name),
                        None)
        return Extraction(
            model=answered or self._model_name,
            model_settings={**self._settings_record, "requested_model": self._model_name},
            prompt_version=prompt_version(),
            content_retries=retries,
        )


def _retries_in(history: Iterable[ModelMessage]) -> int:
    return sum(
        1 for message in history if isinstance(message, ModelRequest)
        for part in message.parts if isinstance(part, RetryPromptPart)
    )


def _last_text(history: Sequence[ModelMessage]) -> str:
    for message in reversed(history):
        if isinstance(message, ModelResponse):
            text = "".join(part.content for part in message.parts if isinstance(part, TextPart))
            if text:
                return text
    return ""
