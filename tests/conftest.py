"""Shared fixtures contain synthetic data only."""

import json
from pathlib import Path
from typing import Any

import pytest

from resumeforge.jobs import JobRequirements
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


@pytest.fixture
def job_path() -> Path:
    return Path(__file__).resolve().parents[1] / "examples/jobs/backend_intern.md"


@pytest.fixture
def job_text(job_path: Path) -> str:
    return job_path.read_text(encoding="utf-8")


@pytest.fixture
def mock_response_path(job_path: Path) -> Path:
    return job_path.with_suffix(".response.json")


@pytest.fixture
def job_payload(mock_response_path: Path) -> dict[str, Any]:
    payload: dict[str, Any] = json.loads(mock_response_path.read_text(encoding="utf-8"))
    return payload


@pytest.fixture
def empty_job_payload() -> dict[str, Any]:
    payload: dict[str, Any] = {"schema_version": 1, "company": None, "job_title": None}
    payload.update({name: [] for name in JobRequirements.ITEM_FIELDS})
    return payload
