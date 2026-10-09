"""API entry point: ``iekg-api`` (ADR-007).

Serves the application with uvicorn in a single process: the worker launcher
keeps the child in memory, so a second API process would launch a second
worker, and the single writer rests on there being one (ADR-007).
"""

import subprocess
import sys
import threading
from collections.abc import Callable, Sequence

import uvicorn
from neo4j import Driver, GraphDatabase, NotificationDisabledCategory

from iekg.api.app import ApiContext, create_app, work_waiting
from iekg.api.navigation import Neo4jNavigation
from iekg.core.repository import Tx
from iekg.graph_schema import INSTITUTIONAL, KEY, LAYER, LEARNING_RESOURCE
from iekg.settings import ApiSettings, Settings, SettingsError

WORKER_COMMAND = (sys.executable, "-m", "iekg.ingestion.worker")


def should_relaunch(exit_code: int, has_work: Callable[[], bool]) -> bool:
    """A worker that ended with an error is not relaunched: it would fail again in a loop (ADR-007)."""
    return exit_code == 0 and has_work()


class ChildWorker:
    """Launches the worker as a child process unless the last one is still running.

    A thread waits for each child and launches another when it ends cleanly
    with work left: a run that arrived while it was ending (ADR-007).
    """

    def __init__(self, has_work: Callable[[], bool], command: Sequence[str] = WORKER_COMMAND) -> None:
        self._has_work = has_work
        self._command = list(command)
        self._process: subprocess.Popen | None = None
        # Uploads and the waiting thread run in different threads; only one may launch.
        self._lock = threading.Lock()

    def ensure_running(self) -> bool:
        with self._lock:
            if self._process is not None and self._process.poll() is None:
                return False
            # Its output goes to the API's console: it is the run log.
            self._process = subprocess.Popen(self._command)
            threading.Thread(target=self._wait_for, args=(self._process,), daemon=True).start()
            return True

    def _wait_for(self, process: subprocess.Popen) -> None:
        if not should_relaunch(process.wait(), self._has_work):
            return
        try:
            self.ensure_running()
        except OSError as error:
            print(f"error: could not launch the worker again: {error}", file=sys.stderr)


_RESOURCE_EXISTS = f"""
RETURN EXISTS {{ MATCH (r:{LEARNING_RESOURCE} {{{KEY}: $key, {LAYER}: $layer}}) }} AS present
"""


def resource_exists_in(tx: Tx, key: str) -> bool:
    return tx.run(_RESOURCE_EXISTS, key=key, layer=INSTITUTIONAL).single()["present"]


class Neo4jResources:
    def __init__(self, driver: Driver, database: str) -> None:
        self._driver = driver
        self._database = database

    def has_resource(self, key: str) -> bool:
        # An empty base does not know the label and its properties yet.
        with self._driver.session(
            database=self._database,
            notifications_disabled_categories=[NotificationDisabledCategory.UNRECOGNIZED],
        ) as session:
            return session.execute_read(resource_exists_in, key)


def main() -> int:
    try:
        settings = Settings.from_environment()
        api = ApiSettings.from_environment()
    except SettingsError as error:
        print(f"error: {error}", file=sys.stderr)
        return 3
    with GraphDatabase.driver(settings.neo4j_uri, auth=(settings.neo4j_user, settings.neo4j_password)) as driver:
        app = create_app(ApiContext(
            operator_token=api.operator_token,
            operational_db=settings.operational_db,
            documents_dir=settings.documents_dir,
            worker=ChildWorker(lambda: work_waiting(settings.operational_db)),
            resources=Neo4jResources(driver, settings.neo4j_database),
            navigation=Neo4jNavigation(driver, settings.neo4j_database),
        ))
        # Passing the app object, not an import string, rules out more workers.
        uvicorn.run(app, host=api.host, port=api.port)
    return 0


if __name__ == "__main__":
    sys.exit(main())
