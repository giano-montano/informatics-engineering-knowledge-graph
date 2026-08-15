"""Cut a document down to the part a topic is about.

A staged pipeline asks one question per topic. Sending the whole syllabus with
each of them costs the same tokens ten times over, and on a provider that bills
tokens per minute it does not just cost more: it stalls. Measured 2026-08-15 --
eight concept calls carrying 12.6 KB each spent twenty-two minutes waiting on
Groq's 8K TPM ceiling, while the section each call actually needed was about
200 characters.

The window is found in the document's own headings, which is the one place its
structure is trustworthy: Docling emits them as Markdown, and a syllabus
chapter is exactly the span between two of them. Note the asymmetry with the
extraction prompt, which tells the model to IGNORE that scaffolding: the model
should not name a topic after a chapter heading, and the code should absolutely
use the heading to know where the chapter ends. Deterministic slicing is what
this layer is for.

Falling back to the whole document is always allowed and always reported: a
window found by mistake would hide half the source from the model, which is a
worse failure than a slow call.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from iekg.contracts import normalise

HEADING = re.compile(r"^(#{1,6})[ \t]*(.+?)[ \t]*$", re.M)

# Words that match everything and therefore discriminate nothing.
_NOISE = {
    "de", "del", "la", "las", "el", "los", "y", "e", "en", "a", "un", "una",
    "the", "of", "and", "in", "for", "to", "an", "horas", "hours", "capitulo",
    "chapter", "semana", "week", "unidad", "unit",
}

# Below this share of shared words, the best heading is not a match. Chosen so
# that a topic named after its chapter still lands, and an unrelated topic
# falls back to the full text instead of being silently truncated.
MATCH_THRESHOLD = 0.5


@dataclass(frozen=True)
class Section:
    level: int
    title: str
    start: int      # first character of the heading line
    end: int        # first character of the next heading of same or higher level


@dataclass(frozen=True)
class Window:
    text: str
    source: str     # the heading it came from, or "" when the whole document
    how: str        # "section" | "full"


def _words(label: str) -> frozenset[str]:
    return frozenset(w for w in normalise(label).split() if w not in _NOISE)


def _overlap(a: str, b: str) -> float:
    """Share of the shorter label's words present in the other one."""
    wa, wb = _words(a), _words(b)
    if not wa or not wb:
        return 0.0
    return len(wa & wb) / min(len(wa), len(wb))


def sections(markdown: str) -> list[Section]:
    """Every heading with the span it owns, up to the next heading of the same
    or higher level. A deeper heading belongs to the section above it."""
    found = [(m.start(), len(m.group(1)), m.group(2)) for m in HEADING.finditer(markdown)]
    out = []
    for i, (start, level, title) in enumerate(found):
        end = len(markdown)
        for next_start, next_level, _ in found[i + 1:]:
            if next_level <= level:
                end = next_start
                break
        out.append(Section(level=level, title=title, start=start, end=end))
    return out


def window(markdown: str, label: str) -> Window:
    """The section whose heading best matches `label`, or the whole document."""
    best, best_score = None, 0.0
    for section in sections(markdown):
        score = _overlap(label, section.title)
        if score > best_score:
            best, best_score = section, score

    if best is None or best_score < MATCH_THRESHOLD:
        return Window(text=markdown, source="", how="full")
    return Window(text=markdown[best.start:best.end], source=best.title, how="section")
