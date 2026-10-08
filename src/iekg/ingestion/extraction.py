"""What the orchestrator expects of an extractor, and how an extraction ends.

An extraction ends in one of three ways (ADR-010): facts with resolved keys;
an output that is still not conforming after the one content retry, which
rejects the run with a discard; or a provider failure once the bounded retries
are spent, which fails it without one.
"""

from pathlib import Path
from typing import Protocol

from iekg.core.batch import Snapshot
from iekg.ingestion.declared import ExtractedFacts
from iekg.operational_store import Discard, Extraction

# Non-conforming output (ADR-010). Not integrity rules: no audit query checks them.
EX_01 = "EX-01"
EX_02 = "EX-02"
EX_03 = "EX-03"

EX_STATEMENTS = {
    EX_01: "The output does not fit the output schema",
    EX_02: "A linked mention brings a key that is not in the snapshot",
    EX_03: "An existing key has another class than its place in the output requires",
}


class ProviderFailure(Exception):
    """The provider kept failing after the bounded retries: the run fails."""

    def __init__(self, message: str, extraction: Extraction | None = None) -> None:
        super().__init__(message)
        self.extraction = extraction


class NonConformingOutput(Exception):
    """The output was not conforming twice: the run is rejected."""

    def __init__(self, discards: list[Discard], raw_output: str, extraction: Extraction) -> None:
        super().__init__(f"{len(discards)} non-conforming item(s): {', '.join(d.rule for d in discards)}")
        self.discards = discards
        self.raw_output = raw_output
        self.extraction = extraction


class Extractor(Protocol):
    def extract(self, document: Path, snapshot: Snapshot) -> tuple[ExtractedFacts, Extraction]:
        """Read ``document`` and return its facts, with keys resolved against ``snapshot``.

        Raises ``NonConformingOutput`` or ``ProviderFailure``.
        """
        ...
