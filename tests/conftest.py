"""Shared fixtures contain synthetic data only."""

from pathlib import Path
from typing import Any

import pytest

from resumeforge.profile import parse_profile


@pytest.fixture
def sample_path() -> Path:
    return Path(__file__).resolve().parents[1] / "examples/profiles/sample.md"


@pytest.fixture
def sample_source(sample_path: Path) -> str:
    return sample_path.read_text(encoding="utf-8")


@pytest.fixture
def sample_data(sample_source: str) -> dict[str, Any]:
    return parse_profile(sample_source).profile.model_dump()
