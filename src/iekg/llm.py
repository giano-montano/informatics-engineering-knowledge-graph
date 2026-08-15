"""Model registry: logical name -> configured PydanticAI model.

Interprets lab/models.yaml the way rules.py interprets schema_rules.yaml. The
point is that no experiment ever names a provider string: it asks for
`workhorse` or `reasoner` and the catalog decides what that is today.

PydanticAI is the abstraction layer, per the thesis (R4 tooling table). This
module only resolves catalog entries onto it; it deliberately wraps nothing,
because a wrapper over an already model-agnostic API would be dead weight.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import yaml
from dotenv import load_dotenv
from pydantic_ai.models import Model
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.models.groq import GroqModel
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.google import GoogleProvider
from pydantic_ai.providers.groq import GroqProvider
from pydantic_ai.providers.openai import OpenAIProvider

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CATALOG = ROOT / "lab" / "models.yaml"

# Providers reachable with an OpenAI-compatible endpoint need a base_url;
# the natively supported ones must not carry one.
_OPENAI_COMPATIBLE = {"nvidia"}
_NATIVE = {"google-gla", "groq"}


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


@dataclass(frozen=True)
class Catalog:
    models: dict[str, ModelEntry]
    comparison_matrix: tuple[str, ...]

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
        )

    matrix = tuple(raw.get("comparison_matrix") or ())
    unknown = [n for n in matrix if n not in models]
    if unknown:
        raise CatalogError(f"comparison_matrix names absent models: {unknown}")

    return Catalog(models=models, comparison_matrix=matrix)


def _api_key(entry: ModelEntry) -> str:
    load_dotenv(ROOT / ".env")
    key = os.getenv(entry.api_key_env)
    if not key:
        raise CatalogError(
            f"{entry.name}: {entry.api_key_env} is unset. "
            f"Copy .env.example to .env and fill it in."
        )
    return key


def build(name: str, catalog: Catalog | None = None) -> Model:
    """Resolve a logical name to a ready-to-use PydanticAI model."""
    catalog = catalog or load()
    entry = catalog.entry(name)
    key = _api_key(entry)

    if entry.provider == "google-gla":
        return GoogleModel(entry.model_id, provider=GoogleProvider(api_key=key))
    if entry.provider == "groq":
        return GroqModel(entry.model_id, provider=GroqProvider(api_key=key))
    # OpenAI-compatible endpoints (NVIDIA NIM). Model ids drift between the
    # docs and the live API, so a 404 here usually means a stale model_id.
    return OpenAIChatModel(
        entry.model_id,
        provider=OpenAIProvider(base_url=entry.base_url, api_key=key),
    )
