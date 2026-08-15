"""Model registry: logical name -> configured PydanticAI model.

Interprets lab/models.yaml the way rules.py interprets schema_rules.yaml. The
point is that no experiment ever names a provider string: it asks for
`workhorse` or `reasoner` and the catalog decides what that is today.

PydanticAI is the abstraction layer, per the thesis (R4 tooling table). This
module resolves catalog entries onto it and applies three corrections that
findings/0004 measured as necessary:

  inline_schema_defs  Pydantic emits `$defs`/`$ref` for nested models. The
                      Google and OpenRouter profiles inline those; Groq's does
                      not, and Groq's tool calling fails on them. Measured
                      0/5 -> 5/5 on gpt-oss-120b.
  thinking            Qwen3's reasoning output interferes with emitting the
                      tool call. Disabling it: 2/5 -> 5/5, tokens 1419 -> 588.
  retries             Gemini answers 503 under load and Groq 429 over quota.
                      Both are transient and belong in the transport, not in
                      every caller.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

import httpx
import yaml
from dotenv import load_dotenv
from pydantic_ai.exceptions import ModelAPIError
from pydantic_ai.models import Model
from pydantic_ai.models.fallback import FallbackModel
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.models.groq import GroqModel
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.profiles import InlineDefsJsonSchemaTransformer
from pydantic_ai.providers.google import GoogleProvider
from pydantic_ai.providers.groq import GroqProvider
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.retries import AsyncTenacityTransport, RetryConfig, wait_retry_after
from pydantic_ai.settings import ModelSettings
from tenacity import retry_if_exception_type, stop_after_attempt, wait_exponential

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CATALOG = ROOT / "lab" / "models.yaml"

# Providers reachable with an OpenAI-compatible endpoint need a base_url;
# the natively supported ones must not carry one.
_OPENAI_COMPATIBLE = {"nvidia"}
_NATIVE = {"google-gla", "groq"}

# Server-side transients worth absorbing in the transport.
#
# 429 IS DELIBERATELY ABSENT, and it used to be here. Measured 2026-08-15, for
# two independent reasons:
#
#   it lies    the transport closes the response before re-raising, so the
#              provider SDK never sees a status at all and reports
#              `APIConnectionError: Connection error`. A rate limit arriving
#              disguised as a network fault cost most of a debugging session.
#              With 429 out of this set the same call fails as
#              `ModelHTTPError: status_code: 429` with the body attached.
#   it hurts   Groq's ceiling is tokens per minute. Retrying an identical
#              3K-token prompt does not wait for room, it consumes more of the
#              budget it is waiting for. Quota is paced by the caller, not
#              retried by the transport.
#
# Surfacing it also makes it a ModelAPIError, which is what FallbackModel
# switches on: a quota-exhausted Gemini now falls over to its stand-in instead
# of being retried into the same wall.
#
# A 413 is not here either: Groq rejects an oversized max_tokens reservation up
# front, and retrying an identical request would just fail identically.
_RETRYABLE_STATUS = {500, 502, 503, 504}


class CatalogError(RuntimeError):
    """The catalog is malformed, or a key it names is missing from the env."""


@dataclass(frozen=True)
class ModelEntry:
    name: str
    provider: str
    model_id: str
    api_key_env: str
    tier: str
    limits: str = ""
    notes: str = ""
    base_url: str | None = None
    inline_schema_defs: bool = False
    thinking: bool | None = None
    max_tokens: int | None = None
    fallback_to: str | None = None
    # Declared, not guessed. A staged pipeline has to wait for room instead of
    # retrying into a ceiling; 0 means no known limit and no pacing.
    tokens_per_minute: int = 0


@dataclass(frozen=True)
class EmbeddingEntry:
    name: str
    provider: str
    model_id: str
    api_key_env: str
    dimensions: int
    query_task_type: str
    document_task_type: str
    requests_per_minute: int = 100
    notes: str = ""


@dataclass(frozen=True)
class Catalog:
    models: dict[str, ModelEntry]
    comparison_matrix: tuple[str, ...]
    embeddings: dict[str, EmbeddingEntry] = field(default_factory=dict)

    def embedding(self, name: str) -> EmbeddingEntry:
        try:
            return self.embeddings[name]
        except KeyError:
            known = ", ".join(sorted(self.embeddings)) or "none"
            raise CatalogError(f"unknown embedding model '{name}'; catalog has: {known}") from None

    def entry(self, name: str) -> ModelEntry:
        try:
            return self.models[name]
        except KeyError:
            known = ", ".join(sorted(self.models))
            raise CatalogError(f"unknown model '{name}'; catalog has: {known}") from None

    def by_tier(self, tier: str) -> tuple[ModelEntry, ...]:
        return tuple(e for e in self.models.values() if e.tier == tier)


def load(path: Path | None = None) -> Catalog:
    """Read and validate the catalog. Does not touch the network or the env."""
    path = path or DEFAULT_CATALOG
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))

    if raw.get("version") != 1:
        raise CatalogError(f"unsupported catalog version: {raw.get('version')!r}")

    models: dict[str, ModelEntry] = {}
    for name, cfg in (raw.get("models") or {}).items():
        provider = cfg.get("provider")
        if provider not in _NATIVE | _OPENAI_COMPATIBLE:
            raise CatalogError(f"{name}: unsupported provider {provider!r}")
        if provider in _OPENAI_COMPATIBLE and not cfg.get("base_url"):
            raise CatalogError(f"{name}: provider {provider!r} requires base_url")
        models[name] = ModelEntry(
            name=name,
            provider=provider,
            model_id=cfg["model_id"],
            api_key_env=cfg["api_key_env"],
            tier=cfg.get("tier", "iteration"),
            limits=cfg.get("limits", ""),
            notes=(cfg.get("notes") or "").strip(),
            base_url=cfg.get("base_url"),
            inline_schema_defs=bool(cfg.get("inline_schema_defs", False)),
            thinking=cfg.get("thinking"),
            max_tokens=cfg.get("max_tokens"),
            fallback_to=cfg.get("fallback_to"),
            tokens_per_minute=int(cfg.get("tokens_per_minute", 0)),
        )

    for name, entry in models.items():
        if entry.fallback_to and entry.fallback_to not in models:
            raise CatalogError(f"{name}: fallback_to names absent model "
                               f"{entry.fallback_to!r}")
        if entry.fallback_to == name:
            raise CatalogError(f"{name}: fallback_to points at itself")

    matrix = tuple(raw.get("comparison_matrix") or ())
    unknown = [n for n in matrix if n not in models]
    if unknown:
        raise CatalogError(f"comparison_matrix names absent models: {unknown}")

    embeddings: dict[str, EmbeddingEntry] = {}
    for name, cfg in (raw.get("embeddings") or {}).items():
        if cfg.get("provider") not in _NATIVE | _OPENAI_COMPATIBLE:
            raise CatalogError(f"{name}: unsupported provider {cfg.get('provider')!r}")
        embeddings[name] = EmbeddingEntry(
            name=name,
            provider=cfg["provider"],
            model_id=cfg["model_id"],
            api_key_env=cfg["api_key_env"],
            dimensions=int(cfg["dimensions"]),
            query_task_type=cfg["query_task_type"],
            document_task_type=cfg["document_task_type"],
            requests_per_minute=int(cfg.get("requests_per_minute", 100)),
            notes=(cfg.get("notes") or "").strip(),
        )

    return Catalog(models=models, comparison_matrix=matrix, embeddings=embeddings)


def _api_key(entry: ModelEntry) -> str:
    load_dotenv(ROOT / ".env")
    key = os.getenv(entry.api_key_env)
    if not key:
        raise CatalogError(
            f"{entry.name}: {entry.api_key_env} is unset. "
            f"Copy .env.example to .env and fill it in."
        )
    return key


def api_key(entry: ModelEntry | EmbeddingEntry) -> str:
    """The key an entry names, for callers that talk to a provider SDK
    directly instead of through PydanticAI (embeddings do)."""
    return _api_key(entry)


def _raise_on_retryable(response: httpx.Response) -> None:
    """Turn a retryable status into the exception the retry policy watches for."""
    if response.status_code in _RETRYABLE_STATUS:
        response.raise_for_status()


def retrying_client(attempts: int = 5) -> httpx.AsyncClient:
    """HTTP client that backs off on 429/5xx, honouring Retry-After when sent.

    Lives in the transport so a multi-stage pipeline is not written around the
    provider having a bad minute.
    """
    transport = AsyncTenacityTransport(
        config=RetryConfig(
            retry=retry_if_exception_type(httpx.HTTPStatusError),
            wait=wait_retry_after(
                fallback_strategy=wait_exponential(multiplier=2, max=60),
                max_wait=120,
            ),
            stop=stop_after_attempt(attempts),
            reraise=True,
        ),
        validate_response=_raise_on_retryable,
    )
    return httpx.AsyncClient(transport=transport, timeout=180.0)


def _profile_for(entry: ModelEntry, base):
    """Force ref inlining when the catalog asks for it.

    PydanticAI picks the schema transformer from the model id's vendor prefix,
    not from whoever is serving it. `openai/gpt-oss-120b` on Groq therefore
    gets the OpenAI transformer, which keeps `$defs`/`$ref` because OpenAI
    supports them -- while Groq's tool calling does not. findings/0004.
    """
    if not entry.inline_schema_defs or base is None:
        return base
    return type(base)(
        {**dict(base), "json_schema_transformer": InlineDefsJsonSchemaTransformer}
    )


def _settings_for(entry: ModelEntry) -> ModelSettings | None:
    settings: dict = {}
    if entry.thinking is not None:
        settings["thinking"] = entry.thinking
    if entry.max_tokens is not None:
        settings["max_tokens"] = entry.max_tokens
    return ModelSettings(**settings) if settings else None


def _bare(entry: ModelEntry, attempts: int) -> Model:
    key = _api_key(entry)
    client = retrying_client(attempts)
    settings = _settings_for(entry)

    if entry.provider == "google-gla":
        cls, provider = GoogleModel, GoogleProvider(api_key=key, http_client=client)
    elif entry.provider == "groq":
        cls, provider = GroqModel, GroqProvider(api_key=key, http_client=client)
    else:
        # OpenAI-compatible endpoints (NVIDIA NIM). Model ids drift between the
        # docs and the live API, so a 404 here usually means a stale model_id.
        cls = OpenAIChatModel
        provider = OpenAIProvider(base_url=entry.base_url, api_key=key, http_client=client)

    # Start from the profile the provider would have chosen, then override only
    # what the catalog asks for. Rebuilding it from scratch would silently drop
    # the vendor defaults (thinking support, reasoning-effort mapping).
    profile = _profile_for(entry, provider.model_profile(entry.model_id))
    return cls(entry.model_id, provider=provider, settings=settings, profile=profile)


def build(name: str, catalog: Catalog | None = None, attempts: int = 5) -> Model:
    """Resolve a logical name to a ready-to-use PydanticAI model.

    If the entry declares `fallback_to`, the result is a FallbackModel that
    switches providers when the first one raises an API error rather than
    failing the whole run.
    """
    catalog = catalog or load()
    entry = catalog.entry(name)
    model = _bare(entry, attempts)

    if entry.fallback_to:
        alt = _bare(catalog.entry(entry.fallback_to), attempts)
        # `fallback_on` defaults to ModelAPIError, and the retrying transport
        # raises httpx.HTTPStatusError, which is not one. Measured 2026-08-14:
        # with the default, a 429 on gemini-3.7-flash propagated and killed the
        # run while gemini-3.6-flash was answering normally. The fallback was
        # declared, tested by reading the code, and inert in practice.
        return FallbackModel(
            model, alt, fallback_on=(ModelAPIError, httpx.HTTPStatusError)
        )
    return model
