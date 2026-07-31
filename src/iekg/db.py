"""Neo4j connection.

Credentials come from .env, never from code. The lab instance is the one
docker-compose.yml brings up at the repository root.
"""

from __future__ import annotations

import os
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from dotenv import load_dotenv
from neo4j import Driver, GraphDatabase

ROOT = Path(__file__).resolve().parents[2]

DEFAULT_URI = "bolt://localhost:7687"
DEFAULT_USER = "neo4j"

# Community Edition allows a single user database, and the final deployment
# targets Community. Everything lives in `neo4j`; nothing depends on
# multi-database.
DATABASE = "neo4j"


def _password() -> str:
    load_dotenv(ROOT / ".env")
    pw = os.getenv("NEO4J_PASSWORD")
    if not pw:
        raise RuntimeError(
            "NEO4J_PASSWORD is missing. Copy .env.example to .env and set the "
            "lab instance password."
        )
    return pw


def driver() -> Driver:
    uri = os.getenv("NEO4J_URI", DEFAULT_URI)
    user = os.getenv("NEO4J_USER", DEFAULT_USER)
    return GraphDatabase.driver(uri, auth=(user, _password()))


@contextmanager
def session() -> Iterator:
    """Session against the lab database, closing both session and driver."""
    d = driver()
    try:
        with d.session(database=DATABASE) as s:
            yield s
    finally:
        d.close()
