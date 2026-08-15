"""Tests for the model catalog interpreter.

Never touches the network or a real API key: these check that a malformed
catalog is rejected loudly rather than producing a half-configured model at
call time, which is the failure mode that wastes a scarce free-tier quota.
"""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from iekg import llm


def write(tmp_path: Path, body: str) -> Path:
    path = tmp_path / "models.yaml"
    path.write_text(textwrap.dedent(body), encoding="utf-8")
    return path


VALID = """\
    version: 1
    models:
      workhorse:
        provider: google-gla
        model_id: gemini-3.7-flash
        api_key_env: GOOGLE_AI_STUDIO_API_KEY
        tier: iteration
      frontier:
        provider: nvidia
        model_id: z-ai/glm-5.2
        api_key_env: NVIDIA_BUILD_API_KEY
        base_url: https://integrate.api.nvidia.com/v1
        tier: final
    comparison_matrix: [workhorse]
    """


def test_loads_valid_catalog(tmp_path):
    catalog = llm.load(write(tmp_path, VALID))
    assert set(catalog.models) == {"workhorse", "frontier"}
    assert catalog.comparison_matrix == ("workhorse",)
    assert catalog.entry("workhorse").model_id == "gemini-3.7-flash"


def test_by_tier_separates_scarce_from_renewable(tmp_path):
    catalog = llm.load(write(tmp_path, VALID))
    assert [e.name for e in catalog.by_tier("iteration")] == ["workhorse"]
    assert [e.name for e in catalog.by_tier("final")] == ["frontier"]


def test_unknown_model_names_the_alternatives(tmp_path):
    catalog = llm.load(write(tmp_path, VALID))
    with pytest.raises(llm.CatalogError, match="frontier, workhorse"):
        catalog.entry("nope")


def test_rejects_unsupported_provider(tmp_path):
    path = write(tmp_path, VALID.replace("provider: google-gla", "provider: acme"))
    with pytest.raises(llm.CatalogError, match="unsupported provider"):
        llm.load(path)


def test_openai_compatible_provider_requires_base_url(tmp_path):
    # VALID is dedented inside write(), so the target keeps its raw indentation.
    path = write(
        tmp_path,
        VALID.replace("        base_url: https://integrate.api.nvidia.com/v1\n", ""),
    )
    with pytest.raises(llm.CatalogError, match="requires base_url"):
        llm.load(path)


def test_rejects_unknown_version(tmp_path):
    path = write(tmp_path, VALID.replace("version: 1", "version: 2"))
    with pytest.raises(llm.CatalogError, match="unsupported catalog version"):
        llm.load(path)


def test_comparison_matrix_must_name_real_models(tmp_path):
    path = write(tmp_path, VALID.replace("comparison_matrix: [workhorse]",
                                         "comparison_matrix: [workhorse, ghost]"))
    with pytest.raises(llm.CatalogError, match="ghost"):
        llm.load(path)


def test_missing_api_key_is_reported_before_any_call(tmp_path, monkeypatch):
    catalog = llm.load(write(tmp_path, VALID))
    monkeypatch.setattr(llm, "load_dotenv", lambda *a, **k: None)
    monkeypatch.delenv("GOOGLE_AI_STUDIO_API_KEY", raising=False)
    with pytest.raises(llm.CatalogError, match="GOOGLE_AI_STUDIO_API_KEY is unset"):
        llm.build("workhorse", catalog)


def test_shipped_catalog_is_valid():
    """The real lab/models.yaml must parse: a typo there breaks every run."""
    catalog = llm.load()
    assert catalog.comparison_matrix
    for name in catalog.comparison_matrix:
        assert catalog.entry(name).tier == "iteration", (
            f"{name} is in the comparison matrix but is not iteration tier; "
            "comparing pipelines must not burn scarce quota"
        )
