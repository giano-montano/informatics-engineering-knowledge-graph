"""An extraction against a reference annotation: how much of it is right.

What it is NOT: R4's acceptance criterion. The thesis says "verificación manual
de la precisión de entidades extraídas >= 75%". A human reading the syllabus
can see that an element the annotation never listed is nonetheless correct;
this cannot. Every number here is therefore a LOWER BOUND on precision, and its
job is to make a hundred runs comparable between themselves, not to replace the
one manual count that the criterion asks for.

Two matchers, reported side by side on purpose:

  exact    normalised equality. Unforgiving, and the only one that means
           "the pipeline produced the same label the annotator wrote".
  relaxed  half the content words in common. Forgiving of the tail a syllabus
           row drags along -"Modelo relacional: estructura y operaciones" vs
           "Modelo relacional"- which is a granularity difference, not an
           extraction error.

The GAP between the two is the measurement that matters for label granularity:
if relaxed is far above exact, the pipeline is finding the right things and
naming them badly, which is a different problem with a different fix.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from iekg.contracts import Extraction, normalise
from iekg.gold import Annotation, Mention

# Words that carry no discriminating content in either language. Kept short:
# a long stoplist starts deciding what the labels mean.
_NOISE = {
    "de", "del", "la", "las", "el", "los", "y", "e", "en", "a", "un", "una",
    "the", "of", "and", "in", "for", "to", "an",
}

RELAXED_THRESHOLD = 0.5


def _words(label: str) -> frozenset[str]:
    return frozenset(w for w in normalise(label).split() if w not in _NOISE)


def _overlap(a: str, b: str) -> float:
    """Share of the SMALLER label's words found in the other.

    Not Jaccard: a gold label of two words against an extracted label of eight
    would score low on Jaccard even when the two words are all there, and that
    is precisely the descriptive-tail case this has to see through.
    """
    wa, wb = _words(a), _words(b)
    if not wa or not wb:
        return 0.0
    return len(wa & wb) / min(len(wa), len(wb))


@dataclass(frozen=True)
class Match:
    extracted: str
    expected: str | None
    score: float
    kind: str  # exact | relaxed | none


def _best_match(label: str, candidates: list[str]) -> Match:
    for candidate in candidates:
        if normalise(label) == normalise(candidate):
            return Match(label, candidate, 1.0, "exact")
    best, best_score = None, 0.0
    for candidate in candidates:
        score = _overlap(label, candidate)
        if score > best_score:
            best, best_score = candidate, score
    if best is not None and best_score >= RELAXED_THRESHOLD:
        return Match(label, best, round(best_score, 3), "relaxed")
    return Match(label, None, round(best_score, 3), "none")


def _labels(mentions: tuple[Mention, ...]) -> list[str]:
    """Both languages are acceptable targets: the annotation carries the
    Spanish surface form and the English canonical one, and a pipeline that
    finds either has found the thing."""
    out = []
    for mention in mentions:
        out += [mention.label_es, mention.label_en]
    return out


@dataclass
class Score:
    extracted: int = 0
    expected: int = 0
    exact: int = 0
    relaxed: int = 0          # includes exact
    matches: list[Match] = field(default_factory=list)

    def _ratio(self, hits: int, total: int) -> float:
        return round(hits / total, 4) if total else 0.0

    @property
    def precision_exact(self) -> float:
        return self._ratio(self.exact, self.extracted)

    @property
    def precision_relaxed(self) -> float:
        return self._ratio(self.relaxed, self.extracted)

    @property
    def recall_exact(self) -> float:
        return self._ratio(len({m.expected for m in self.matches if m.kind == "exact"}),
                           self.expected)

    @property
    def recall_relaxed(self) -> float:
        return self._ratio(
            len({m.expected for m in self.matches if m.expected is not None}),
            self.expected,
        )

    def as_dict(self) -> dict:
        return {
            "extracted": self.extracted,
            "expected": self.expected,
            "exact": self.exact,
            "relaxed": self.relaxed,
            "precision_exact": self.precision_exact,
            "precision_relaxed": self.precision_relaxed,
            "recall_exact": self.recall_exact,
            "recall_relaxed": self.recall_relaxed,
        }


def _score(labels: list[str], expected: list[str], expected_count: int) -> Score:
    result = Score(extracted=len(labels), expected=expected_count)
    for label in labels:
        match = _best_match(label, expected)
        result.matches.append(match)
        if match.kind == "exact":
            result.exact += 1
            result.relaxed += 1
        elif match.kind == "relaxed":
            result.relaxed += 1
    return result


@dataclass
class LinkScore:
    """Only topics that matched a gold topic can have their link judged.

    Judging a link on a topic the annotation never listed would measure the
    extraction twice and the linking not at all.
    """

    judged: int = 0
    correct: int = 0
    wrong: int = 0
    abstained: int = 0
    expected_none: int = 0     # gold says no unit covers it
    detail: list[dict] = field(default_factory=list)

    @property
    def accuracy(self) -> float:
        return round(self.correct / self.judged, 4) if self.judged else 0.0

    def as_dict(self) -> dict:
        return {
            "judged": self.judged,
            "correct": self.correct,
            "wrong": self.wrong,
            "abstained": self.abstained,
            "expected_no_unit": self.expected_none,
            "accuracy": self.accuracy,
        }


def score(extraction: Extraction, annotation: Annotation) -> dict:
    """The whole comparison, ready to be written next to the run."""
    gold_topics = annotation.topics
    topic_targets = _labels(gold_topics)
    # Scored on the Spanish label: it is what a Spanish syllabus yields
    # verbatim, so it does not punish a bad translation twice. The matcher
    # accepts either language on the annotation's side.
    topics = _score(
        [t.label_es or t.label_en for t in extraction.topics],
        topic_targets,
        len(gold_topics),
    )

    all_gold_concepts = [c for group in annotation.concepts.values() for c in group]
    concepts = _score(
        [c.label_es or c.label_en for t in extraction.topics for c in t.concepts],
        _labels(tuple(all_gold_concepts)),
        len(all_gold_concepts),
    )

    # -- linking, only where the topic itself was found ----------------------
    by_label: dict[str, Mention] = {}
    for mention in gold_topics:
        by_label[normalise(mention.label_es)] = mention
        by_label[normalise(mention.label_en)] = mention

    links = LinkScore()
    for topic, match in zip(extraction.topics, topics.matches):
        if match.expected is None:
            continue
        expected = by_label.get(normalise(match.expected))
        if expected is None:
            continue
        if expected.links_to_ku is None:
            links.expected_none += 1
            # Abstaining where the annotation also found no unit is the right
            # answer, and it is scored as one.
            links.judged += 1
            if topic.links_to_ku is None:
                links.correct += 1
                links.abstained += 1
            else:
                links.wrong += 1
        else:
            links.judged += 1
            if topic.links_to_ku == expected.links_to_ku:
                links.correct += 1
            elif topic.links_to_ku is None:
                links.abstained += 1
            else:
                links.wrong += 1
        links.detail.append(
            {
                "extracted": topic.label_es,
                "matched_gold": match.expected,
                "match_kind": match.kind,
                "expected_ku": expected.links_to_ku,
                "got_ku": topic.links_to_ku,
                "score": topic.link_score,
            }
        )

    # -- noise: things the annotation explicitly did not want ----------------
    out_of_scope = list(annotation.out_of_scope)
    noise = []
    for topic in extraction.topics:
        match = _best_match(topic.label_es or topic.label_en, out_of_scope)
        if match.kind != "none":
            noise.append({"label": topic.label_es, "matched": match.expected})

    return {
        "annotator": annotation.annotator,
        "is_gold": annotation.annotator == "giano",
        "topics": topics.as_dict(),
        "concepts": concepts.as_dict(),
        "linking": links.as_dict(),
        "noise": {"count": len(noise), "hits": noise},
        "topic_matches": [
            {"extracted": m.extracted, "matched": m.expected,
             "kind": m.kind, "score": m.score}
            for m in topics.matches
        ],
        "linking_detail": links.detail,
        "caveat": (
            "Automatic, gold-based: an extraction absent from the annotation "
            "counts as wrong even when it is right. Lower bound on precision, "
            "not R4's manual figure."
        ),
    }
