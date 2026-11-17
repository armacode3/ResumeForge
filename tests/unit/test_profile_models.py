"""Schema, identifier, date and evidence-graph contracts."""

from copy import deepcopy
from typing import Any

import pytest
from pydantic import ValidationError

from resumeforge.profile.models import Accomplishment, ProfileEntry, UserProfile, VerifiedBullet


def test_complete_profile_and_json_round_trip(sample_data: dict[str, Any]) -> None:
    profile = UserProfile.model_validate(sample_data)

    assert len(profile.entries()) == 8
    assert profile.skills.languages == ["Python", "SQL"]
    assert profile.coursework == ["Data Structures", "Databases"]
    assert profile.verified_bullets[0].accomplishment_ids == ["acc_api"]
    assert UserProfile.model_validate_json(profile.model_dump_json()) == profile


@pytest.mark.parametrize("value", [0, 2, True, "1", 1.0])
def test_schema_version_is_explicit_strict_integer_one(value: object) -> None:
    with pytest.raises(ValidationError):
        UserProfile.model_validate({"schema_version": value, "person": {"name": "Example"}})


@pytest.mark.parametrize("field", ["schema_version", "person"])
def test_required_root_fields(sample_data: dict[str, Any], field: str) -> None:
    del sample_data[field]
    with pytest.raises(ValidationError, match=field):
        UserProfile.model_validate(sample_data)


@pytest.mark.parametrize("section", ["education", "accomplishments", "verified_bullets"])
def test_duplicate_ids_rejected(sample_data: dict[str, Any], section: str) -> None:
    sample_data[section].append(deepcopy(sample_data[section][0]))
    with pytest.raises(ValidationError, match="duplicate ID"):
        UserProfile.model_validate(sample_data)


@pytest.mark.parametrize("identifier", ["exp_", "exp_Uppercase", "exp_has-dash", " exp_space"])
def test_malformed_identifiers_rejected(identifier: str) -> None:
    with pytest.raises(ValidationError):
        ProfileEntry(id=identifier, title="Example")


def test_section_specific_prefix_enforced(sample_data: dict[str, Any]) -> None:
    sample_data["projects"][0]["id"] = "exp_wrong_section"
    with pytest.raises(ValidationError, match="projects IDs must start with proj_"):
        UserProfile.model_validate(sample_data)


@pytest.mark.parametrize("field", ["id", "title"])
def test_entry_required_fields(field: str) -> None:
    data = {"id": "exp_demo", "title": "Example"}
    del data[field]
    with pytest.raises(ValidationError, match=field):
        ProfileEntry.model_validate(data)


@pytest.mark.parametrize("date", ["2025-13", "2025-00", "0000-01", "2025-1", "2025-01-01"])
def test_invalid_month_dates_rejected(date: str) -> None:
    with pytest.raises(ValidationError):
        ProfileEntry(id="exp_demo", title="Example", start_date=date)


def test_reversed_dates_rejected_but_expected_graduation_allowed() -> None:
    with pytest.raises(ValidationError, match="end_date must not precede"):
        ProfileEntry(id="edu_demo", title="Example", start_date="2025-01", end_date="2024-12")
    assert ProfileEntry(id="edu_demo", title="Example", end_date="2030-05").end_date == "2030-05"
    assert ProfileEntry(id="exp_demo", title="Example", end_date="present").end_date == "present"


@pytest.mark.parametrize("field", ["name", "email", "links"])
def test_invalid_contact_data(sample_data: dict[str, Any], field: str) -> None:
    sample_data["person"][field] = {
        "name": "  ",
        "email": "not-an-email",
        "links": ["file:///etc"],
    }[field]
    with pytest.raises(ValidationError):
        UserProfile.model_validate(sample_data)


@pytest.mark.parametrize("location", ["root", "person", "entry"])
def test_unknown_fields_rejected(sample_data: dict[str, Any], location: str) -> None:
    target = {
        "root": sample_data,
        "person": sample_data["person"],
        "entry": sample_data["experiences"][0],
    }[location]
    target["typo"] = "synthetic-private-value"
    with pytest.raises(ValidationError, match="Extra inputs are not permitted") as error:
        UserProfile.model_validate(sample_data)
    assert "synthetic-private-value" not in str(error.value)


def test_unknown_entry_reference_rejected(sample_data: dict[str, Any]) -> None:
    sample_data["accomplishments"][0]["entry_id"] = "exp_missing"
    with pytest.raises(ValidationError, match="unknown entry_id: exp_missing"):
        UserProfile.model_validate(sample_data)


@pytest.mark.parametrize("reference", ["acc_missing", "acc_queue_pending"])
def test_verified_bullet_needs_existing_verified_evidence(
    sample_data: dict[str, Any], reference: str
) -> None:
    sample_data["verified_bullets"][0]["accomplishment_ids"] = [reference]
    with pytest.raises(ValidationError, match=r"unknown accomplishment|unverified accomplishment"):
        UserProfile.model_validate(sample_data)


@pytest.mark.parametrize("references", [[], ["acc_api", "acc_api"]])
def test_bullet_references_are_nonempty_and_distinct(references: list[str]) -> None:
    with pytest.raises(ValidationError):
        VerifiedBullet(id="bullet_demo", text="Example", accomplishment_ids=references)


def test_verification_is_opt_in_and_metrics_are_not_required() -> None:
    item = Accomplishment(id="acc_demo", entry_id="exp_demo", statement="Built a test utility.")
    assert item.verified is False
    assert item.metrics == []
    with pytest.raises(ValidationError):
        Accomplishment.model_validate({**item.model_dump(), "verified": "true"})


def test_wrong_collection_and_blank_evidence_rejected(sample_data: dict[str, Any]) -> None:
    sample_data["skills"]["languages"] = "Python"
    sample_data["accomplishments"][0]["statement"] = "\n  "
    with pytest.raises(ValidationError) as error:
        UserProfile.model_validate(sample_data)
    assert error.value.error_count() == 2
