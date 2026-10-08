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
    facts_dir: Path
    documents_dir: Path
    # The base of the locators of uploaded documents (ADR-009). It is written
    # into the graph and the fact store, so it must be the one students reach.
    public_base_url: str

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
            facts_dir=Path(os.environ.get("IEKG_FACTS_DIR", "var/facts")),
            documents_dir=Path(os.environ.get("IEKG_DOCUMENTS_DIR", "var/documents")),
            public_base_url=os.environ.get("IEKG_PUBLIC_BASE_URL", "http://localhost:8000"),
        )


@dataclass(frozen=True)
class ProviderSettings:
    """The language model provider: any server with the OpenAI Chat Completions API.

    Read only by the worker, so the build processes run without it.
    """

    model: str
    api_key: str
    base_url: str | None
    reasoning_effort: str | None
    temperature: float | None
    max_retries: int
    timeout_seconds: float

    @classmethod
    def from_environment(cls) -> "ProviderSettings":
        load_dotenv(find_dotenv(usecwd=True))
        missing = [name for name in ("IEKG_LLM_MODEL", "IEKG_LLM_API_KEY") if not os.environ.get(name)]
        if missing:
            raise SettingsError(f"{', '.join(missing)} not set; see .env.example")
        temperature = os.environ.get("IEKG_LLM_TEMPERATURE")
        return cls(
            model=os.environ["IEKG_LLM_MODEL"],
            api_key=os.environ["IEKG_LLM_API_KEY"],
            base_url=os.environ.get("IEKG_LLM_BASE_URL") or None,
            reasoning_effort=os.environ.get("IEKG_LLM_REASONING_EFFORT") or None,
            temperature=float(temperature) if temperature else None,
            max_retries=int(os.environ.get("IEKG_LLM_MAX_RETRIES", "3")),
            timeout_seconds=float(os.environ.get("IEKG_LLM_TIMEOUT_SECONDS", "900")),
        )


@dataclass(frozen=True)
class ApiSettings:
    """What only the API reads: the operator token (ADR-013) and where it listens."""

    operator_token: str
    host: str
    port: int

    @classmethod
    def from_environment(cls) -> "ApiSettings":
        load_dotenv(find_dotenv(usecwd=True))
        token = os.environ.get("IEKG_OPERATOR_TOKEN", "").strip()
        if not token:
            # Without it the operation routes would be open to anyone (ADR-013).
            raise SettingsError("IEKG_OPERATOR_TOKEN is not set; see .env.example")
        return cls(
            operator_token=token,
            host=os.environ.get("IEKG_API_HOST", "127.0.0.1"),
            port=int(os.environ.get("IEKG_API_PORT", "8000")),
        )
