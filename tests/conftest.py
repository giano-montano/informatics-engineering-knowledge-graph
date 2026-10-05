from collections.abc import Callable, Iterator
from pathlib import Path
from uuid import uuid4

import pytest
from neo4j import Driver, GraphDatabase, Transaction
from neo4j.exceptions import Neo4jError, ServiceUnavailable

from iekg.settings import Settings, SettingsError

ROOT = Path(__file__).resolve().parent.parent
TBOX = ROOT / "ontology" / "ontologia_informatica.ttl"
BACKBONE = ROOT / "ontology" / "backbone_cs2023.ttl"


@pytest.fixture
def new_key() -> Callable[[], str]:
    """Keys that cannot collide with anything in the base."""
    return lambda: f"test:{uuid4()}"


@pytest.fixture(scope="session")
def neo4j() -> Iterator[tuple[Driver, str]]:
    try:
        settings = Settings.from_environment()
    except SettingsError as error:
        pytest.skip(str(error))
    driver = GraphDatabase.driver(settings.neo4j_uri, auth=(settings.neo4j_user, settings.neo4j_password))
    try:
        driver.verify_connectivity()
    except (ServiceUnavailable, Neo4jError, OSError) as error:
        driver.close()
        pytest.skip(f"Neo4j is not reachable at {settings.neo4j_uri}: {error}")
    yield driver, settings.neo4j_database
    driver.close()


@pytest.fixture
def tx(neo4j: tuple[Driver, str]) -> Iterator[Transaction]:
    """A transaction that is always rolled back, so the base is left intact."""
    driver, database = neo4j
    with driver.session(database=database) as session:
        transaction = session.begin_transaction()
        try:
            yield transaction
        finally:
            transaction.close()
