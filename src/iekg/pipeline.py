"""Interpreter for lab/pipelines.yaml: a pipeline is a list of stages.

Fourth interpreter in the same shape as the other three. It reads the
declarative composition, runs the named stages in order over a shared context,
and writes every intermediate artifact to disk.

Two rules the design turns on:

  it emits, it does not load    a run produces JSON and .cypher under
                                build/runs/. Writing to Neo4j is a separate,
                                explicit step, so two runs are diffable and a
                                bad extraction is never a bad database.
  the blind gate is code        a run against a document whose reference
                                annotation is not sealed refuses to start.
                                Prose asking the operator to remember would
                                have been forgotten once, and once is enough
                                to invalidate the gold standard.
"""

from __future__ import annotations

import json
import os
import subprocess
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

import yaml

from iekg import abox as abox_mod
from iekg import contracts, gold, linking, llm, verbalize
from iekg.rules import Spec

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SPEC = ROOT / "lab" / "pipelines.yaml"
RUNS_DIR = ROOT / "build" / "runs"


class PipelineError(RuntimeError):
    """The composition is malformed, or a stage cannot run where it was placed."""


# ---------------------------------------------------------------------------
# The declarative side
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class PipelineSpec:
    name: str
    title: str
    adds: str
    isolates: str
    stages: tuple[str, ...]
    model: str
    embedding_model: str
    coinable: tuple[str, ...]
    options: dict[str, Any]


def load_pipelines(path: Path | None = None) -> dict[str, PipelineSpec]:
    raw = yaml.safe_load((path or DEFAULT_SPEC).read_text(encoding="utf-8"))
    if raw.get("version") != 1:
        raise PipelineError(f"unsupported pipelines version: {raw.get('version')!r}")

    defaults = raw.get("defaults") or {}
    out: dict[str, PipelineSpec] = {}
    for name, cfg in (raw.get("pipelines") or {}).items():
        stages = tuple(cfg.get("stages") or ())
        unknown = [s for s in stages if s not in STAGES]
        if unknown:
            raise PipelineError(f"{name}: unknown stage(s) {unknown}; "
                                f"known: {', '.join(sorted(STAGES))}")
        out[name] = PipelineSpec(
            name=name,
            title=cfg.get("title", ""),
            adds=cfg.get("adds", ""),
            isolates=cfg.get("isolates", ""),
            stages=stages,
            model=cfg.get("model", defaults.get("model")),
            embedding_model=cfg.get("embedding_model", defaults.get("embedding_model")),
            coinable=tuple(cfg.get("coinable", defaults.get("coinable", []))),
            options={**(defaults.get("options") or {}), **(cfg.get("options") or {})},
        )
    return out


# ---------------------------------------------------------------------------
# The running side
# ---------------------------------------------------------------------------

@dataclass
class StageRecord:
    stage: str
    seconds: float
    requests: int = 0
    tokens: int = 0
    note: str = ""


@dataclass
class RunContext:
    pipeline: PipelineSpec
    document: abox_mod.SourceDocument
    spec: Spec
    catalog: llm.Catalog
    out_dir: Path

    text: str = ""
    ontology: str = ""
    topics: list[contracts.TopicOut] = field(default_factory=list)
    extraction: contracts.Extraction | None = None
    abox: abox_mod.ABox | None = None
    link_report: list[dict] = field(default_factory=list)
    records: list[StageRecord] = field(default_factory=list)
    answered_by: set[str] = field(default_factory=set)

    _model: Any = None
    _backbone: list[gold.BackboneEntry] | None = None

    @property
    def model(self):
        if self._model is None:
            self._model = llm.build(self.pipeline.model, self.catalog)
        return self._model

    @property
    def backbone(self) -> list[gold.BackboneEntry]:
        if self._backbone is None:
            self._backbone = gold.read_backbone(self.spec)
        return self._backbone

    def option(self, key: str, default: Any = None) -> Any:
        return self.pipeline.options.get(key, default)

    def write(self, name: str, content: str) -> Path:
        path = self.out_dir / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def call(self, agent, prompt: str, record: StageRecord):
        """One model call, accounted. `usage` is a property, not a method:
        wrapping this in a broad except once turned a TypeError into a run
        that reported zero tokens for everything (findings/0004).

        The model that ANSWERED is recorded, not the one that was asked. A
        FallbackModel switches providers without saying so, and a run credited
        to the wrong model is worse than a failed one.
        """
        run = agent.run_sync(prompt)
        usage = run.usage
        record.requests += 1
        record.tokens += usage.total_tokens or 0
        answered = getattr(run.all_messages()[-1], "model_name", None)
        if answered:
            self.answered_by.add(answered)
        return run.output


Stage = Callable[[RunContext, StageRecord], None]


# ---------------------------------------------------------------------------
# Stages
# ---------------------------------------------------------------------------

_PLAIN_TEXT = {".txt", ".md"}


def stage_load(ctx: RunContext, record: StageRecord) -> None:
    """Document -> text, layout aware. Docling, per the thesis' Fase 2.

    A .txt or .md input is read as it stands: it is already the output this
    stage produces, and running a layout model over it would only add a
    dependency to a smoke test.
    """
    path = ctx.document.path
    if path.suffix.lower() in _PLAIN_TEXT:
        ctx.text = path.read_text(encoding="utf-8")
        record.note = f"{len(ctx.text)} chars (plain text, reader skipped)"
    else:
        # Load-bearing, not tidying: Docling's layout model runs under
        # torch.compile, whose inductor backend shells out to a C++ compiler.
        # On a Windows machine without MSVC it raises
        # `InvalidCxxCompiler: Compiler: cl is not found` and the conversion
        # fails outright. Disabling the compiler falls back to eager execution,
        # which is slower per page and works. Measured 2026-08-14: the 4-page
        # syllabus converts in 15 s.
        os.environ.setdefault("TORCHDYNAMO_DISABLE", "1")
        from docling.document_converter import DocumentConverter

        result = DocumentConverter().convert(path)
        ctx.text = result.document.export_to_markdown()
        record.note = f"{len(ctx.text)} chars"
    ctx.write("document.md", ctx.text)


def stage_verbalize(ctx: RunContext, record: StageRecord) -> None:
    """T-box -> prompt. No model call: it is a compilation, like the Cypher."""
    ctx.ontology = verbalize.build(ctx.spec, list(ctx.pipeline.coinable))
    ctx.write("ontology_prompt.md", ctx.ontology)
    record.note = f"{len(ctx.ontology)} chars"


_FREE_PROMPT = """\
Extract the concepts taught by this course and the relations between them.

Return your answer as JSON.

--- SOURCE ---
{text}
"""


def stage_extract_free(ctx: RunContext, record: StageRecord) -> None:
    """The unconstrained baseline: no schema, no type, no vocabulary.

    Deliberately no output_type. Handing this stage a Pydantic model would
    already be the constraint whose value the baseline exists to measure, and
    the comparison would start at P1 with no floor under it.
    """
    from pydantic_ai import Agent

    agent = Agent(ctx.model, retries=ctx.option("retries", 2))
    prompt = _FREE_PROMPT.format(text=ctx.text)
    ctx.write("prompts/extract_free.txt", prompt)
    output = ctx.call(agent, prompt, record)
    ctx.write("raw_free_output.txt", output)

    ctx.extraction = contracts.parse_unconstrained(output)
    record.note = (
        f"{len(ctx.extraction.topics)} topics / {ctx.extraction.concept_count} concepts"
        + ("  UNPARSEABLE" if ctx.extraction.unparsed else "")
    )


_TYPED_PROMPT = """\
{ontology}

# TASK

Extract the Topics of the course below, and the Concepts taught inside each
Topic, conforming to the ontology above.

Give every element two labels: `label_es` exactly as the source words it, and
`label_en` its canonical English label. The graph links on the English one, so
translating is part of the task, not decoration.

--- SOURCE ---
{text}
"""

_CONCEPTS_PROMPT = """\
{ontology}

# TASK

The Topic "{topic}" was extracted from the course below. List only the Concepts
taught inside THAT Topic. Ignore everything the source says about other topics.

If the source names no concept for it, return an empty list. An invented
concept costs more than a missing one.

--- SOURCE ---
{text}
"""


def _translation_validator():
    """Reflection, OneKE style: retry with the validation error attached.

    Only checks what the extraction stage actually controls. Anchoring a Topic
    to a knowledge unit is the linking stage's job, so demanding it here would
    make the model retry forever against a rule it cannot satisfy yet.
    """
    from pydantic_ai import ModelRetry

    def validate(output):
        topics = getattr(output, "topics", None) or []
        if topics and all(t.label_en.strip() == t.label_es.strip() for t in topics):
            raise ModelRetry(
                "Every label_en is identical to its label_es, so nothing was "
                "translated. label_en must be the canonical ENGLISH label."
            )
        return output

    return validate


def _typed_agent(ctx: RunContext, output_type):
    from pydantic_ai import Agent

    agent = Agent(ctx.model, output_type=output_type, retries=ctx.option("retries", 2))
    if ctx.option("reflect", False):
        agent.output_validator(_translation_validator())
    return agent


def stage_extract_typed(ctx: RunContext, record: StageRecord) -> None:
    """One constrained pass: the whole partonomy in a single call."""
    if not ctx.ontology:
        raise PipelineError("extract_typed needs `verbalize` before it")

    prompt = _TYPED_PROMPT.format(ontology=ctx.ontology, text=ctx.text)
    ctx.write("prompts/extract_typed.txt", prompt)
    output = ctx.call(_typed_agent(ctx, contracts.TypedExtraction), prompt, record)

    ctx.topics = output.topics
    ctx.extraction = contracts.from_topics(output.topics)
    record.note = (
        f"{len(ctx.extraction.topics)} topics / {ctx.extraction.concept_count} concepts"
    )


def stage_extract_topics(ctx: RunContext, record: StageRecord) -> None:
    """First rung of the staged extraction: topics only, concepts later."""
    if not ctx.ontology:
        raise PipelineError("extract_topics needs `verbalize` before it")

    prompt = _TYPED_PROMPT.format(ontology=ctx.ontology, text=ctx.text)
    ctx.write("prompts/extract_topics.txt", prompt)
    output = ctx.call(_typed_agent(ctx, contracts.TopicsOnly), prompt, record)

    # Concepts arriving here are dropped on purpose: this stage exists to ask
    # only for topics, and keeping a by-product would blur what P2 isolates.
    ctx.topics = [contracts.TopicOut(label_es=t.label_es, label_en=t.label_en)
                  for t in output.topics]
    ctx.extraction = contracts.from_topics(ctx.topics)
    record.note = f"{len(ctx.topics)} topics"


def stage_extract_concepts(ctx: RunContext, record: StageRecord) -> None:
    """Second rung: one focused call per topic, SPIRES style."""
    if not ctx.topics:
        raise PipelineError("extract_concepts needs `extract_topics` before it")

    for topic in ctx.topics:
        prompt = _CONCEPTS_PROMPT.format(
            ontology=ctx.ontology, topic=topic.label_es, text=ctx.text
        )
        ctx.write(f"prompts/extract_concepts-{contracts.slug(topic.label_en)}.txt", prompt)
        output = ctx.call(_typed_agent(ctx, contracts.ConceptsOnly), prompt, record)
        topic.concepts = output.concepts

    ctx.extraction = contracts.from_topics(ctx.topics)
    record.note = f"{ctx.extraction.concept_count} concepts over {len(ctx.topics)} topics"


def _apply_links(ctx: RunContext, decisions: list[linking.Decision]) -> None:
    for topic, decision in zip(ctx.extraction.topics, decisions):
        topic.links_to_ku = decision.key
        topic.link_score = decision.score
        topic.link_method = decision.method
        ctx.link_report.append(
            {
                "topic_en": topic.label_en,
                "topic_es": topic.label_es,
                "decision": decision.key,
                "score": decision.score,
                "method": decision.method,
                "reason": decision.reason,
                "candidates": [
                    {"key": c.key, "label": c.label, "score": c.score}
                    for c in decision.candidates
                ],
            }
        )
    ctx.write("linking.json", json.dumps(ctx.link_report, ensure_ascii=False, indent=2))


def stage_link_lexical(ctx: RunContext, record: StageRecord) -> None:
    """The control: normalised exact match, no model, no retrieval."""
    if ctx.extraction is None:
        raise PipelineError("link_lexical needs an extraction stage before it")

    decisions = [linking.lexical(t.label_en, ctx.backbone) for t in ctx.extraction.topics]
    _apply_links(ctx, decisions)
    record.note = f"{ctx.extraction.linked_count}/{len(ctx.extraction.topics)} linked"


def stage_link_retrieval(ctx: RunContext, record: StageRecord) -> None:
    """Candidates by embedding, decided by threshold and margin over runner-up."""
    if ctx.extraction is None:
        raise PipelineError("link_retrieval needs an extraction stage before it")

    entry = ctx.catalog.embedding(ctx.pipeline.embedding_model)
    index = linking.EmbeddingIndex(entry, ctx.backbone)
    queries = [t.label_en for t in ctx.extraction.topics]
    ranked = index.rank(queries, k=int(ctx.option("candidates", 5)))
    record.requests += 1

    decisions = [
        linking.decide(
            candidates,
            threshold=float(ctx.option("threshold", 0.62)),
            margin=float(ctx.option("margin", 0.03)),
        )
        for candidates in ranked
    ]
    _apply_links(ctx, decisions)
    abstained = sum(1 for d in decisions if d.key is None and d.candidates)
    record.note = (f"{ctx.extraction.linked_count}/{len(queries)} linked, "
                   f"{abstained} sent to review")


def stage_build_abox(ctx: RunContext, record: StageRecord) -> None:
    """Mint, validate against the schema rules, emit Cypher. No model, no write."""
    if ctx.extraction is None:
        raise PipelineError("build_abox needs an extraction stage before it")

    ctx.abox = abox_mod.build(
        ctx.extraction, ctx.document, ctx.spec,
        scope_iris=bool(ctx.option("scope_iris", False)),
    )
    ctx.write("extraction.json", ctx.extraction.model_dump_json(indent=2))
    ctx.write("graph.cypher", abox_mod.to_cypher(ctx.abox, ctx.document, ctx.spec))
    ctx.write(
        "violations.json",
        json.dumps(
            {
                "conformance": ctx.abox.conformance,
                "by_rule": ctx.abox.by_rule(),
                "violations": [
                    {"rule": v.rule, "entity": v.entity, "detail": v.detail}
                    for v in ctx.abox.violations
                ],
            },
            ensure_ascii=False,
            indent=2,
        ),
    )
    record.note = (f"{len(ctx.abox.nodes)} nodes / {len(ctx.abox.edges)} edges, "
                   f"conformance {ctx.abox.conformance}")


STAGES: dict[str, Stage] = {
    "load": stage_load,
    "verbalize": stage_verbalize,
    "extract_free": stage_extract_free,
    "extract_typed": stage_extract_typed,
    "extract_topics": stage_extract_topics,
    "extract_concepts": stage_extract_concepts,
    "link_lexical": stage_link_lexical,
    "link_retrieval": stage_link_retrieval,
    "build_abox": stage_build_abox,
}


# ---------------------------------------------------------------------------
# Running one
# ---------------------------------------------------------------------------

def _git_sha() -> str:
    try:
        return subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"], cwd=ROOT,
            capture_output=True, text=True, check=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def run_dir(pipeline: PipelineSpec, document: abox_mod.SourceDocument) -> Path:
    return RUNS_DIR / f"{pipeline.name}-{pipeline.model}-{document.key}"


def run(pipeline: PipelineSpec, document: abox_mod.SourceDocument, spec: Spec,
        catalog: llm.Catalog, *, out_dir: Path | None = None,
        gate_bypassed: bool = False) -> RunContext:
    """Execute the stages in order and leave the whole run on disk."""
    ctx = RunContext(
        pipeline=pipeline,
        document=document,
        spec=spec,
        catalog=catalog,
        out_dir=out_dir or run_dir(pipeline, document),
    )
    ctx.out_dir.mkdir(parents=True, exist_ok=True)

    started = datetime.now(timezone.utc)
    for name in pipeline.stages:
        record = StageRecord(stage=name, seconds=0.0)
        clock = time.perf_counter()
        try:
            STAGES[name](ctx, record)
        finally:
            record.seconds = round(time.perf_counter() - clock, 2)
            ctx.records.append(record)

    entry = catalog.entry(pipeline.model)
    manifest = {
        "pipeline": {
            "name": pipeline.name,
            "title": pipeline.title,
            "adds": pipeline.adds,
            "isolates": pipeline.isolates,
            "stages": list(pipeline.stages),
            "options": pipeline.options,
            "coinable": list(pipeline.coinable),
        },
        "model": {
            "logical_name": pipeline.model,
            "provider": entry.provider,
            "model_id": entry.model_id,
            "tier": entry.tier,
            "thinking": entry.thinking,
            "inline_schema_defs": entry.inline_schema_defs,
            "fallback_to": entry.fallback_to,
            # What actually answered. More than one id here means the fallback
            # fired mid-run, and the run is not attributable to one model.
            "answered_by": sorted(ctx.answered_by),
            "fallback_fired": sorted(ctx.answered_by) not in ([], [entry.model_id]),
        },
        "embedding_model": pipeline.embedding_model,
        "document": {
            "code": document.code,
            "term": document.term,
            "path": document.path.as_posix(),
        },
        "started_utc": started.isoformat(timespec="seconds"),
        "git_sha": _git_sha(),
        # Held constant across the comparison and recorded because it is a
        # variable nobody controlled: a different reader is a different run.
        "pdf_reader": _docling_version(),
        "blind_gate_bypassed": gate_bypassed,
        "stages": [
            {"stage": r.stage, "seconds": r.seconds, "requests": r.requests,
             "tokens": r.tokens, "note": r.note}
            for r in ctx.records
        ],
        "totals": {
            "seconds": round(sum(r.seconds for r in ctx.records), 2),
            "requests": sum(r.requests for r in ctx.records),
            "tokens": sum(r.tokens for r in ctx.records),
            "topics": len(ctx.extraction.topics) if ctx.extraction else 0,
            "concepts": ctx.extraction.concept_count if ctx.extraction else 0,
            "linked": ctx.extraction.linked_count if ctx.extraction else 0,
            "conformance": ctx.abox.conformance if ctx.abox else None,
        },
    }
    ctx.write("manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))
    return ctx


def _docling_version() -> str:
    try:
        from importlib.metadata import version

        return f"docling {version('docling')}"
    except Exception:  # noqa: BLE001 - absent optional dependency, not a failure
        return "docling (version unknown)"
