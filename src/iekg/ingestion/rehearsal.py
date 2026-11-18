"""The rehearsal worker: ``python -m iekg.ingestion.rehearsal`` (ADR-013, amendment 2026-11).

It takes the pending runs of the rehearsal store and walks each one through
the states of a run that writes cleanly, pausing at each step. It neither
reads the document nor calls the language model nor opens the graph: the
rehearsal checks the operator flow, not the extraction.
"""

import sqlite3
import sys
import time
from collections.abc import Callable
from pathlib import Path

from iekg.ingestion.orchestrator import has_work
from iekg.operational_store import Extraction, OperationalStore
from iekg.settings import RehearsalSettings

REHEARSAL_MODEL = "rehearsal (simulated)"
REHEARSAL_COMMAND = (sys.executable, "-m", "iekg.ingestion.rehearsal")


def seed_rehearsal_store(real: Path, rehearsal: Path) -> None:
    """Start the rehearsal store as a copy of the real one, unless it exists.

    The copy brings the real history and the latest audit report, so the
    panel shows the runs the graph came from and the gate open.
    """
    if rehearsal.exists():
        return
    rehearsal.parent.mkdir(parents=True, exist_ok=True)
    if not real.is_file():
        return
    source = sqlite3.connect(f"{real.resolve().as_uri()}?mode=ro", uri=True)
    try:
        target = sqlite3.connect(rehearsal)
        try:
            source.backup(target)
        finally:
            target.close()
    finally:
        source.close()


def rehearse(store: OperationalStore, pause: Callable[[], None]) -> int:
    """Walk every pending run to completed while the gate is open; return how many."""
    done = 0
    while has_work(store):
        run = store.take_pending_run()
        if run is None:
            break
        # Every pause falls while the run is running: in a real run, written
        # but not persisted lasts an instant, and the panel stops polling there.
        pause()
        store.record_extraction(run.id, Extraction(REHEARSAL_MODEL, {}, "rehearsal", 0, 0, 0))
        pause()
        pause()
        store.mark_written(run.id)
        store.finish_run(run.id, clean=True)
        print(f"Run {run.id}: rehearsed ({run.course_code}, {run.file_name}); nothing written")
        done += 1
    return done


def main() -> int:
    settings = RehearsalSettings.from_environment()
    with OperationalStore(settings.operational_db) as store:
        rehearse(store, lambda: time.sleep(settings.step_seconds))
    return 0


if __name__ == "__main__":
    sys.exit(main())
