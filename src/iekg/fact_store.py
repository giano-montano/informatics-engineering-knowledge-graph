"""Fact store: one file per run that wrote, written once (ADR-012).

Each file holds exactly the batch the writer received, with its layer and
provenance, so the reapplication repeats the same writes as the ingestion. It
is also the accepted batch the test cases evaluate.
"""

import json
import os
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

from iekg.core.batch import Batch, batch_from_data, batch_to_data

_FORMAT = 1


@dataclass(frozen=True)
class StoredFacts:
    run_id: int
    layer: str
    provenance: str
    batch: Batch


class FactStore:
    def __init__(self, directory: Path) -> None:
        self._directory = directory

    def path_of(self, run_id: int) -> Path:
        # Zero-padded, so the names sort in the order of the runs.
        return self._directory / f"run-{run_id:06d}.json"

    def save(self, facts: StoredFacts) -> Path:
        """Write the file of a run; raise ``FileExistsError`` if it has one."""
        self._directory.mkdir(parents=True, exist_ok=True)
        path = self.path_of(facts.run_id)
        content = json.dumps(
            {
                "format": _FORMAT,
                "run_id": facts.run_id,
                "layer": facts.layer,
                "provenance": facts.provenance,
                **batch_to_data(facts.batch),
            },
            ensure_ascii=False,
            indent=1,
        )
        temporary = path.with_suffix(".tmp")
        with open(temporary, "w", encoding="utf-8") as file:
            file.write(content)
            file.flush()
            os.fsync(file.fileno())
        # A hard link appears whole or not at all, and never replaces a file.
        try:
            os.link(temporary, path)
        finally:
            temporary.unlink()
        return path

    def load(self, run_id: int) -> StoredFacts:
        data = json.loads(self.path_of(run_id).read_text(encoding="utf-8"))
        if data.get("format") != _FORMAT:
            raise ValueError(f"{self.path_of(run_id)}: unknown format {data.get('format')!r}")
        return StoredFacts(data["run_id"], data["layer"], data["provenance"], batch_from_data(data))

    def run_ids(self) -> Iterator[int]:
        """The runs with a file, in the order they ran."""
        if not self._directory.exists():
            return iter(())
        return iter(sorted(int(path.stem.removeprefix("run-")) for path in self._directory.glob("run-*.json")))
