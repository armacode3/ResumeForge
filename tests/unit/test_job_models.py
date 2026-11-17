"""Strict schemas and stable job evidence identifiers."""

from copy import deepcopy
from typing import Any

import pytest
from pydantic import ValidationError

from resumeforge.jobs import JobRequirements
from resumeforge.jobs.models import JobItem, QuotedFact


def test_sample_requirements_preserve_categories_and_round_trip(
    job_payload: dict[str, Any],
) -> None:
    requirements = JobRequirements.model_validate(job_payload)

    assert requirements.company is not None
    assert requirements.company.text == "Example Systems"
    assert len(requirements.required_qualifications) == 2
    assert len(requirements.preferred_qualifications) == 1
    assert requirements.frameworks[0].text == "FastAPI"
    assert requirements.domain_terms == []
    assert JobRequirements.model_validate_json(requirements.model_dump_json()) == requirements


@pytest.mark.parametrize("version", [True, "1", 0, 2, 1.0])
def test_version_is_integer_one(empty_job_payload: dict[str, Any], version: object) -> None:
    empty_job_payload["schema_version"] = version
    with pytest.raises(ValidationError):
        JobRequirements.model_validate(empty_job_payload)


@pytest.mark.parametrize("field", ["company", "job_title", *JobRequirements.ITEM_FIELDS])
def test_all_fields_must_be_explicit(empty_job_payload: dict[str, Any], field: str) -> None:
    del empty_job_payload[field]
    with pytest.raises(ValidationError, match="Field required"):
        JobRequirements.model_validate(empty_job_payload)


@pytest.mark.parametrize("text", ["", " \n", "Invented knowledge"])
def test_blank_or_paraphrased_facts_rejected(text: str) -> None:
    with pytest.raises(ValidationError):
        QuotedFact(text=text, source_quote="Experience writing Python programs.")


@pytest.mark.parametrize("identifier", ["job_", "job_Invalid", "job_has-dash", "x" * 81])
def test_invalid_identifiers(identifier: str) -> None:
    with pytest.raises(ValidationError):
        JobItem(id=identifier, text="Python", source_quote="Python")


def test_identifiers_are_unique_across_sections(job_payload: dict[str, Any]) -> None:
    job_payload["programming_languages"][0]["id"] = job_payload["responsibilities"][0]["id"]
    with pytest.raises(ValidationError, match="IDs must be unique"):
        JobRequirements.model_validate(job_payload)


def test_duplicate_text_in_same_section_rejected(job_payload: dict[str, Any]) -> None:
    duplicate = deepcopy(job_payload["responsibilities"][0])
    duplicate["id"] = "job_duplicate"
    job_payload["responsibilities"].append(duplicate)
    with pytest.raises(ValidationError, match="Duplicate item text"):
        JobRequirements.model_validate(job_payload)


@pytest.mark.parametrize("location", ["root", "item", "metadata"])
def test_unknown_fields_rejected_without_input_values(
    job_payload: dict[str, Any], location: str
) -> None:
    target = {
        "root": job_payload,
        "item": job_payload["responsibilities"][0],
        "metadata": job_payload["company"],
    }[location]
    target["unsupported_field"] = "synthetic-private-input"
    with pytest.raises(ValidationError, match="Extra inputs") as error:
        JobRequirements.model_validate(job_payload)
    assert "synthetic-private-input" not in str(error.value)


def test_collections_types_and_limits(empty_job_payload: dict[str, Any]) -> None:
    empty_job_payload["responsibilities"] = "Python"
    with pytest.raises(ValidationError):
        JobRequirements.model_validate(empty_job_payload)
    empty_job_payload["responsibilities"] = [
        {"id": f"job_{index}", "text": "Python", "source_quote": "Python"} for index in range(201)
    ]
    with pytest.raises(ValidationError, match="at most 200"):
        JobRequirements.model_validate(empty_job_payload)
