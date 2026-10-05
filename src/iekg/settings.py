"""Settings, read from the environment with ``.env`` as fallback.

Relative paths resolve against the working directory: run the commands from
the repository root, or set absolute paths.
"""

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import find_dotenv, load_dotenv


class SettingsError(Exception):
    pass


@dataclass(frozen=True)
class Settings:
    neo4j_uri: str
    neo4j_user: str
    neo4j_password: str
    neo4j_database: str
    tbox_path: Path
    backbone_path: Path
    operational_db: Path

    @classmethod
    def from_environment(cls) -> "Settings":
        # Variables already set win over .env, as in a container.
        load_dotenv(find_dotenv(usecwd=True))
        password = os.environ.get("NEO4J_PASSWORD")
        if not password:
            raise SettingsError("NEO4J_PASSWORD is not set; copy .env.example to .env and set it")
        return cls(
            neo4j_uri=os.environ.get("NEO4J_URI", "bolt://localhost:7687"),
            neo4j_user=os.environ.get("NEO4J_USER", "neo4j"),
            neo4j_password=password,
            neo4j_database=os.environ.get("NEO4J_DATABASE", "neo4j"),
            tbox_path=Path(os.environ.get("IEKG_TBOX", "ontology/ontologia_informatica.ttl")),
            backbone_path=Path(os.environ.get("IEKG_BACKBONE", "ontology/backbone_cs2023.ttl")),
            operational_db=Path(os.environ.get("IEKG_OPERATIONAL_DB", "var/operational.sqlite")),
        )
