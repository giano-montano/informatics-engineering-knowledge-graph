"""Worker entry point: ``iekg-worker`` (ADR-007).

Processes the pending runs one after another while the audit gate is open, and
ends when there are none left. The API launches it as a child process.
"""

import os
import sys
from collections.abc import Sequence

# PydanticAI prints an advertising banner on the first run; the worker's
# output is the run log.
os.environ.setdefault("PYDANTIC_AI_NO_BANNER", "1")

from neo4j import GraphDatabase
from openai import AsyncOpenAI
from pydantic_ai.models.openai import OpenAIChatModel, OpenAIChatModelSettings
from pydantic_ai.providers.openai import OpenAIProvider

from iekg.fact_store import FactStore
from iekg.ingestion.extractor import LanguageModelExtractor
from iekg.ingestion.orchestrator import Neo4jGraph, Orchestrator
from iekg.operational_store import OperationalStore
from iekg.settings import ProviderSettings, Settings, SettingsError


def build_extractor(provider: ProviderSettings) -> LanguageModelExtractor:
    # The client's own retries are the bounded retries on transient provider
    # errors (ADR-010): timeouts, rate limits, 5xx and dropped connections.
    client = AsyncOpenAI(
        base_url=provider.base_url,
        api_key=provider.api_key,
        max_retries=provider.max_retries,
        timeout=provider.timeout_seconds,
    )
    model = OpenAIChatModel(provider.model, provider=OpenAIProvider(openai_client=client))
    model_settings = OpenAIChatModelSettings()
    if provider.temperature is not None:
        model_settings["temperature"] = provider.temperature
    if provider.reasoning_effort is not None:
        model_settings["openai_reasoning_effort"] = provider.reasoning_effort
    record = {
        "base_url": provider.base_url,
        "temperature": provider.temperature,
        "reasoning_effort": provider.reasoning_effort,
        "max_retries": provider.max_retries,
    }
    return LanguageModelExtractor(model, model_settings=dict(model_settings), settings_record=record)


def main(argv: Sequence[str] | None = None) -> int:
    try:
        settings = Settings.from_environment()
        provider = ProviderSettings.from_environment()
    except SettingsError as error:
        print(f"error: {error}", file=sys.stderr)
        return 3
    extractor = build_extractor(provider)
    with (
        GraphDatabase.driver(settings.neo4j_uri, auth=(settings.neo4j_user, settings.neo4j_password)) as driver,
        OperationalStore(settings.operational_db) as store,
    ):
        Orchestrator(
            store=store,
            graph=Neo4jGraph(driver, settings.neo4j_database),
            extractor=extractor,
            facts=FactStore(settings.facts_dir),
            documents=settings.documents_dir,
            public_base_url=settings.public_base_url,
        ).run_pending()
    return 0


if __name__ == "__main__":
    sys.exit(main())
