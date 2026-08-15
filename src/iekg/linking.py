"""Entity linking: a syllabus mention -> a backbone knowledge unit.

The fragile link, and the one the pipeline ladder exists to isolate. Two
mechanisms, deliberately kept as separate stages so the comparison can attribute
a difference to one of them:

  lexical    normalised exact match. Cheap, no model, near-zero recall against
             Spanish syllabus wording. It is the control, not a proposal.
  retrieval  cosine over embeddings, top-k candidates, then a decision rule.

Measured on 2026-08-14 with gemini-embedding-001 and asymmetric task types,
against three backbone labels:

    query "Modelado de datos: modelo entidad-relacion"
      Data Modeling                 0.733   <- correct
      Relational Databases          0.708   <- near miss, same area
      Quantum Architectures         0.560   <- unrelated

The correct answer beats the wrong one by 0.025 while clearing an unrelated
label by 0.17. A single absolute threshold cannot exploit that: any cut that
accepts 0.733 also accepts 0.708. So the decision rule here is a MARGIN over
the runner-up, and abstention when the margin is too small, which is the
routing to human review the design already anticipated. All k candidates are
kept in the artifact so a threshold can be re-swept without spending calls.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
import time
from dataclasses import dataclass
from pathlib import Path

from iekg import llm
from iekg.contracts import normalise
from iekg.gold import BackboneEntry

ROOT = Path(__file__).resolve().parents[2]
CACHE_DIR = ROOT / "build" / "embeddings"


@dataclass(frozen=True)
class Candidate:
    key: str
    label: str
    score: float


@dataclass(frozen=True)
class Decision:
    """What linking concluded, and why. `key is None` is a result, not a gap."""

    key: str | None
    score: float | None
    method: str
    candidates: tuple[Candidate, ...] = ()
    reason: str = ""


# ---------------------------------------------------------------------------
# Lexical: the control
# ---------------------------------------------------------------------------

def lexical(label: str, entries: list[BackboneEntry]) -> Decision:
    """Exact match after folding case, accents and spacing. Nothing else.

    No substring or fuzzy matching on purpose: a control that quietly does half
    the work of the mechanism under test stops being a control.
    """
    key = normalise(label)
    for entry in entries:
        if normalise(entry.label) == key:
            return Decision(entry.key, 1.0, "lexical", reason="exact label match")
    return Decision(None, None, "lexical", reason="no exact match")


# ---------------------------------------------------------------------------
# Retrieval
# ---------------------------------------------------------------------------

def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na and nb else 0.0


def document_text(entry: BackboneEntry) -> str:
    """What gets embedded for a backbone unit.

    The area is included because unit labels are ambiguous on their own:
    'Foundational Data Structures and Algorithms' and 'Data Modeling' read
    alike out of context, and the area is the context CS2023 already provides.
    """
    return f"{entry.label} ({entry.area_label})"


class EmbeddingIndex:
    """The backbone, embedded once and cached.

    Cached on disk keyed by model id and by the hash of the texts: 162 labels
    do not change between runs, and re-embedding them on every run would spend
    quota measuring nothing.
    """

    def __init__(self, entry: llm.EmbeddingEntry, entries: list[BackboneEntry],
                 *, cache_dir: Path | None = None) -> None:
        self.entry = entry
        self.entries = entries
        self.texts = [document_text(e) for e in entries]
        self.cache_dir = cache_dir or CACHE_DIR
        self._vectors: list[list[float]] | None = None

    @property
    def cache_path(self) -> Path:
        digest = hashlib.sha256("\n".join(self.texts).encode()).hexdigest()[:12]
        return self.cache_dir / f"{self.entry.model_id}-{digest}.json"

    def _client(self):
        from google import genai

        return genai.Client(api_key=llm.api_key(self.entry))

    # Batching hides nothing from the quota: measured on 2026-08-14, the free
    # tier counts each TEXT against EmbedContentRequestsPerMinute, not each
    # call. 162 labels in eleven batches of sixteen is 162 against a ceiling of
    # 100/min, so the index must be paced, not just chunked. It is built once
    # and cached, so the minute it costs is paid once.
    BATCH = 16
    ATTEMPTS = 4

    def _pace(self, count: int) -> float:
        return 60.0 * count / self.entry.requests_per_minute

    def _embed(self, texts: list[str], task_type: str) -> list[list[float]]:
        from google.genai import types

        client = self._client()
        config = types.EmbedContentConfig(task_type=task_type)
        out: list[list[float]] = []

        for start in range(0, len(texts), self.BATCH):
            chunk = texts[start : start + self.BATCH]
            for attempt in range(self.ATTEMPTS):
                try:
                    response = client.models.embed_content(
                        model=self.entry.model_id, contents=chunk, config=config
                    )
                    break
                except Exception as exc:  # noqa: BLE001 - retried on 429 only
                    message = str(exc)
                    if "429" not in message or attempt == self.ATTEMPTS - 1:
                        raise
                    # Google states the wait in the body, not in Retry-After.
                    hint = re.search(r"retry in ([\d.]+)s", message)
                    time.sleep(float(hint.group(1)) + 1 if hint else 2 ** attempt * 5)

            vectors = [e.values for e in response.embeddings]
            # Verified batch by batch: gemini-embedding-2 returns ONE embedding
            # for any number of inputs, and zipping would have shifted every
            # vector after the first onto the wrong label without raising.
            if len(vectors) != len(chunk):
                raise RuntimeError(
                    f"{self.entry.model_id} returned {len(vectors)} embeddings "
                    f"for {len(chunk)} inputs; the batch cannot be aligned"
                )
            out.extend(vectors)
            if start + self.BATCH < len(texts):
                time.sleep(self._pace(len(chunk)))
        return out

    def vectors(self) -> list[list[float]]:
        if self._vectors is not None:
            return self._vectors
        path = self.cache_path
        if path.exists():
            self._vectors = json.loads(path.read_text(encoding="utf-8"))["vectors"]
            return self._vectors

        self._vectors = self._embed(self.texts, self.entry.document_task_type)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(
                {
                    "model": self.entry.model_id,
                    "task_type": self.entry.document_task_type,
                    "keys": [e.key for e in self.entries],
                    "texts": self.texts,
                    "vectors": self._vectors,
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        return self._vectors

    def rank(self, queries: list[str], k: int = 5) -> list[tuple[Candidate, ...]]:
        """Top-k backbone units per query, best first. One API call per batch."""
        if not queries:
            return []
        vectors = self.vectors()
        embedded = self._embed(queries, self.entry.query_task_type)
        ranked = []
        for query_vector in embedded:
            scored = [
                Candidate(e.key, e.label, round(_cosine(query_vector, v), 4))
                for e, v in zip(self.entries, vectors)
            ]
            scored.sort(key=lambda c: -c.score)
            ranked.append(tuple(scored[:k]))
        return ranked


def decide(candidates: tuple[Candidate, ...], *, threshold: float,
           margin: float) -> Decision:
    """Accept the top candidate only if it clears the floor AND the runner-up.

    The margin is what the measurement above demands: absolute cosine barely
    separates the right unit from a plausible neighbour, so a lead over the
    second candidate carries more information than the score itself. Failing
    the margin abstains rather than guessing; abstentions are what a reviewer
    should be handed.
    """
    if not candidates:
        return Decision(None, None, "retrieval", reason="no candidates")
    best = candidates[0]
    runner_up = candidates[1].score if len(candidates) > 1 else 0.0

    if best.score < threshold:
        return Decision(None, best.score, "retrieval", candidates,
                        f"top score {best.score} below threshold {threshold}")
    if best.score - runner_up < margin:
        return Decision(None, best.score, "retrieval", candidates,
                        f"lead over runner-up {best.score - runner_up:.4f} "
                        f"below margin {margin}; sent to review")
    return Decision(best.key, best.score, "retrieval", candidates,
                    f"lead {best.score - runner_up:.4f} over {candidates[1].key}")
