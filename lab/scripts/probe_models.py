"""Capability probe: what each catalogued model can actually do.

Not a trivia quiz. Each check maps to a property the ingestion pipeline
depends on, so a failure here predicts a specific downstream failure:

  reach        the key works and the model id is live (ids drift silently)
  reasoning    resists a naive-proportionality trap instead of pattern-matching
  structured   returns a valid nested object, not prose wrapped in JSON
  abstention   returns EMPTY when the text lacks the answer  <- precision risk
  crosslingual reads Spanish, emits an English canonical label <- linking risk

`abstention` and `crosslingual` are the two that matter most: R4 is graded on
extraction precision, and the syllabi are Spanish while the CS2023 backbone is
English.

The probe deliberately uses INVENTED text, never lab/docs/syllabus/. Showing
real extractions before the gold annotation exists would destroy its blindness.

Usage:
  uv run python lab/scripts/probe_models.py              # comparison_matrix
  uv run python lab/scripts/probe_models.py workhorse    # named models
  uv run python lab/scripts/probe_models.py --tier iteration
"""

from __future__ import annotations

import argparse
import sys
import time
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from pydantic import BaseModel, Field  # noqa: E402
from pydantic_ai import Agent  # noqa: E402

from iekg import llm  # noqa: E402

# Invented fragment. Deliberately NOT the Databases syllabus under test, and
# deliberately missing any mention of prerequisites so `abstention` has
# something real to abstain from.
SAMPLE = """\
Curso: Redes de Computadoras (1INF99)
Sumilla: El curso presenta el modelo de capas TCP/IP. Se estudia el
direccionamiento IP, el enrutamiento entre sistemas autonomos y el control
de congestion en la capa de transporte.
"""


class Topic(BaseModel):
    label_es: str = Field(description="Label exactly as written in the source")
    label_en: str = Field(description="Canonical English label for graph linking")
    concepts: list[str] = Field(description="Concepts under this topic, English")


class Extraction(BaseModel):
    topics: list[Topic]


class FlatExtraction(BaseModel):
    """Same information as Extraction with no nested model.

    Pydantic renders a nested BaseModel as `$defs` + `$ref`, and some providers
    cannot resolve that inside a tool-call schema. Parallel arrays are uglier
    but produce a schema with no references, which isolates whether a failure
    is about structured output as such or only about nesting.
    """

    topic_labels_es: list[str] = Field(description="Labels as written in the source")
    topic_labels_en: list[str] = Field(description="Canonical English labels, same order")


class Prerequisites(BaseModel):
    course_codes: list[str] = Field(
        description="Prerequisite course codes stated in the text. "
        "Empty list if the text states none."
    )


@dataclass
class Result:
    check: str
    passed: bool | None  # None = could not be judged automatically
    detail: str
    seconds: float
    tokens: int
    reasoning: int = 0


def _usage(run) -> tuple[int, int]:
    """(total tokens, reasoning tokens). `usage` is a property, not a method.

    Reasoning tokens are broken out because on Groq's free tier they are what
    collides with the 8K TPM ceiling: a verbose reasoner can spend more budget
    thinking than the whole request is allowed to consume.
    """
    # Not every provider populates the reasoning breakdown, so it is optional.
    u = run.usage
    return u.total_tokens or 0, getattr(u, "output_reasoning_tokens", 0) or 0


def _timed(agent: Agent, prompt: str):
    start = time.perf_counter()
    run = agent.run_sync(prompt)
    total, reasoning = _usage(run)
    return run, time.perf_counter() - start, total, reasoning


def probe(name: str, catalog: llm.Catalog) -> list[Result]:
    model = llm.build(name, catalog)
    results: list[Result] = []

    # 1. reach ---------------------------------------------------------------
    agent = Agent(model)
    run, secs, toks, rsn = _timed(agent, "Reply with exactly: OK")
    ok = "OK" in run.output.upper()
    results.append(Result("reach", ok, run.output.strip()[:60], secs, toks, rsn))

    # 2. reasoning -----------------------------------------------------------
    # Drying is parallel, not serial: the answer stays 3 hours. Models that
    # pattern-match on "3->30" answer 30.
    run, secs, toks, rsn = _timed(
        agent,
        "Three shirts hung in the sun take 3 hours to dry. "
        "How long do 30 shirts take, hung the same way? Answer in one sentence.",
    )
    # Models emit U+202F (narrow no-break space) between number and unit, so a
    # naive substring match scores a correct answer as wrong.
    text = " ".join(run.output.lower().split())
    ok = "3 hour" in text or "three hour" in text
    results.append(Result("reasoning", ok, run.output.strip()[:80], secs, toks, rsn))

    # 3. structured ----------------------------------------------------------
    typed = Agent(model, output_type=Extraction)
    extraction: Extraction | None = None
    try:
        run, secs, toks, rsn = _timed(
            typed,
            "Extract the topics from this course description.\n\n" + SAMPLE,
        )
        extraction = run.output
        n_t = len(extraction.topics)
        n_c = sum(len(t.concepts) for t in extraction.topics)
        results.append(
            Result("structured", n_t > 0, f"{n_t} topics / {n_c} concepts", secs, toks, rsn)
        )
    except Exception as exc:  # schema refused, malformed JSON, unsupported mode
        results.append(Result("structured", False, f"{type(exc).__name__}"[:90], 0.0, 0))
        # Nesting is the usual culprit. Retry flat to tell the two apart.
        try:
            flat = Agent(model, output_type=FlatExtraction)
            run, secs, toks, rsn = _timed(
                flat, "Extract the topics from this course description.\n\n" + SAMPLE
            )
            n = len(run.output.topic_labels_es)
            results.append(
                Result(
                    "structured-flat",
                    n > 0,
                    f"{n} topics — NESTED SCHEMA IS THE PROBLEM, not structured output",
                    secs,
                    toks,
                    rsn,
                )
            )
        except Exception as exc2:
            results.append(
                Result("structured-flat", False, f"{type(exc2).__name__}"[:90], 0.0, 0)
            )
        return results

    # 4. abstention ----------------------------------------------------------
    # SAMPLE states no prerequisites. Anything non-empty is invention.
    prereq = Agent(model, output_type=Prerequisites)
    try:
        run, secs, toks, rsn = _timed(
            prereq,
            "List the prerequisite course codes stated in this text. "
            "If none are stated, return an empty list.\n\n" + SAMPLE,
        )
        found = run.output.course_codes
        results.append(
            Result(
                "abstention",
                not found,
                "correctly empty" if not found else f"INVENTED {found}",
                secs,
                toks,
                rsn,
            )
        )
    except Exception as exc:
        results.append(Result("abstention", False, f"{type(exc).__name__}"[:90], 0.0, 0))

    # 5. crosslingual --------------------------------------------------------
    # Reuses the extraction from check 3: no extra call, and the pairs are
    # reported rather than graded. Whether "enrutamiento" became "routing"
    # and not "enrutamiento" verbatim is a judgement the probe should not fake.
    pairs = [f"{t.label_es!r}->{t.label_en!r}" for t in extraction.topics[:3]]
    results.append(Result("crosslingual", None, "; ".join(pairs)[:110], 0.0, 0))

    return results


def main() -> int:
    # Models emit characters cp1252 cannot encode (U+202F and friends), which
    # would crash the report rather than the model under test.
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("models", nargs="*", help="logical names from lab/models.yaml")
    parser.add_argument("--tier", help="probe every model of this tier instead")
    args = parser.parse_args()

    catalog = llm.load()
    if args.tier:
        names = [e.name for e in catalog.by_tier(args.tier)]
    else:
        names = args.models or list(catalog.comparison_matrix)

    if not names:
        print("No models selected.")
        return 1

    failures = 0
    for name in names:
        entry = catalog.entry(name)
        print(f"\n=== {name}  ({entry.provider} · {entry.model_id})")
        print(f"    tier={entry.tier}  limits={entry.limits}")
        try:
            results = probe(name, catalog)
        except Exception as exc:
            print(f"    UNREACHABLE  {type(exc).__name__}: {exc}"[:200])
            failures += 1
            continue

        for r in results:
            mark = {True: "pass", False: "FAIL", None: "n/a "}[r.passed]
            rsn = f"(+{r.reasoning} rsn)" if r.reasoning else ""
            print(
                f"    [{mark}] {r.check:<13} {r.seconds:5.1f}s "
                f"{r.tokens:>6}tok {rsn:>12}  {r.detail}"
            )
        failures += sum(1 for r in results if r.passed is False)

    print(f"\n{failures} failed check(s).")
    print("Note: 'crosslingual' is reported, not graded. Read the pairs yourself.")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
