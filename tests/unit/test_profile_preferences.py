"""Completion is not verification; explicit preferences are validated, never inferred from notes."""

from copy import deepcopy
from typing import Any

import pytest
from pydantic import ValidationError

from resumeforge.profile import ResumePreferences, UserProfile, find_profile_gaps, parse_profile
from resumeforge.profile.models import Accomplishment, ProfileEntry

STATUSES = ["unknown", "planned", "in_progress", "completed", "on_hold", "cancelled"]


@pytest.mark.parametrize("status", STATUSES)
@pytest.mark.parametrize("verified", [False, True])
def test_completion_state_is_explicit_and_separate_from_verification(
    status: str, verified: bool
) -> None:
    entry = ProfileEntry.model_validate(
        {"id": "proj_demo", "title": "Demo", "completion_status": status}
    )
    claim = Accomplishment.model_validate(
        {
            "id": "acc_demo",
            "entry_id": entry.id,
            "statement": "A scoped assertion.",
            "completion_status": status,
            "verified": verified,
        }
    )
    assert entry.completion_status == claim.completion_status == status
    assert claim.verified is verified


@pytest.mark.parametrize("end_date", [None, "present", "2025-01"])
def test_dates_never_imply_completion_state(end_date: str | None) -> None:
    entry = ProfileEntry(id="proj_demo", title="Demo", end_date=end_date)
    assert entry.completion_status == "unknown"


@pytest.mark.parametrize("value", ["Complete", "finished", "", " completed", None, True, 1, []])
@pytest.mark.parametrize("record", ["entry", "accomplishment"])
def test_invalid_states_are_not_normalized(value: object, record: str) -> None:
    data = {"id": "proj_demo", "title": "Demo", "completion_status": value}
    if record == "accomplishment":
        data = {
            "id": "acc_demo",
            "entry_id": "proj_demo",
            "statement": "Demo",
            "completion_status": value,
        }
    model = ProfileEntry if record == "entry" else Accomplishment
    with pytest.raises(ValidationError):
        model.model_validate(data)


def test_legacy_v1_dates_and_notes_never_supply_new_defaults() -> None:
    source = """---
schema_version: 1
person: {name: Example}
projects:
  - id: proj_demo
    title: Demo
    end_date: "2025-01"
    details: [Completed according to an unreviewed draft.]
accomplishments:
  - id: acc_demo
    entry_id: proj_demo
    statement: Built a scoped component.
    verified: true
---
completion_status: completed
resume_preferences: {required_entry_ids: [proj_demo], max_projects: 1}
"""
    document = parse_profile(source)
    profile = document.profile
    assert profile.projects[0].completion_status == "unknown"
    assert profile.accomplishments[0].completion_status == "unknown"
    assert profile.resume_preferences == ResumePreferences()
    assert profile.accomplishments[0].verified
    assert document.source_text == source
    assert "required_entry_ids" in document.markdown_notes
    assert (
        sum("completion_status unknown" in warning for warning in find_profile_gaps(profile)) == 2
    )


def test_completed_subtask_does_not_complete_parent_and_status_does_not_change_dates() -> None:
    profile = UserProfile.model_validate(
        {
            "schema_version": 1,
            "person": {"name": "Example"},
            "projects": [{"id": "proj_demo", "title": "Demo", "completion_status": "in_progress"}],
            "accomplishments": [
                {
                    "id": "acc_demo",
                    "entry_id": "proj_demo",
                    "statement": "Completed a scoped subtask.",
                    "completion_status": "completed",
                    "verified": True,
                }
            ],
        }
    )
    assert profile.projects[0].completion_status == "in_progress"
    assert profile.projects[0].end_date is None
    assert profile.accomplishments[0].completion_status == "completed"


def test_preferences_have_no_implicit_content_or_layout_policy() -> None:
    preferences = ResumePreferences()
    assert (
        preferences.required_sections
        == preferences.required_entry_ids
        == preferences.excluded_entry_ids
        == []
    )
    assert preferences.min_projects is preferences.max_projects is None
    assert preferences.min_bullets_per_entry is preferences.max_bullets_per_entry is None
    preferences.required_entry_ids.append("proj_demo")
    assert ResumePreferences().required_entry_ids == []


@pytest.mark.parametrize(
    "field", ["min_projects", "max_projects", "min_bullets_per_entry", "max_bullets_per_entry"]
)
@pytest.mark.parametrize("value", [-1, 21, True, 1.0, "2"])
def test_counts_are_bounded_strict_integers(field: str, value: object) -> None:
    with pytest.raises(ValidationError):
        ResumePreferences.model_validate({field: value})


@pytest.mark.parametrize(
    "field", ["min_projects", "max_projects", "min_bullets_per_entry", "max_bullets_per_entry"]
)
@pytest.mark.parametrize("value", [0, 20, None])
def test_count_boundaries_and_explicit_unspecified(field: str, value: int | None) -> None:
    assert getattr(ResumePreferences.model_validate({field: value}), field) == value


@pytest.mark.parametrize("field", ["required_sections", "required_entry_ids", "excluded_entry_ids"])
def test_preferences_reject_duplicate_lists(field: str) -> None:
    value = "projects" if field == "required_sections" else "proj_demo"
    with pytest.raises(ValidationError, match="duplicates"):
        ResumePreferences.model_validate({field: [value, value]})


@pytest.mark.parametrize(
    "data",
    [
        {"required_sections": ["person"]},
        {"required_sections": ["projects "]},
        {"required_sections": "projects"},
        {"required_entry_ids": ["acc_demo"]},
        {"excluded_entry_ids": None},
        {"min_projects": 2, "max_projects": 1},
        {"min_bullets_per_entry": 3, "max_bullets_per_entry": 2},
        {"required_entry_ids": ["proj_demo"], "excluded_entry_ids": ["proj_demo"]},
        {"unknown_setting": "fictional-private-value"},
    ],
)
def test_invalid_preference_shapes_and_conflicts(data: dict[str, Any]) -> None:
    with pytest.raises(ValidationError) as error:
        ResumePreferences.model_validate(data)
    assert "fictional-private-value" not in str(error.value)


@pytest.mark.parametrize("field", ["required_entry_ids", "excluded_entry_ids"])
def test_entry_preferences_must_resolve_in_the_profile(
    sample_data: dict[str, Any], field: str
) -> None:
    sample_data["resume_preferences"] = {field: ["proj_fictional_private_unknown"]}
    with pytest.raises(ValidationError, match="existing profile entries") as error:
        UserProfile.model_validate(sample_data)
    assert "proj_fictional_private_unknown" not in str(error.value)


@pytest.mark.parametrize(
    "preferences",
    [
        {"required_sections": ["projects"], "excluded_entry_ids": ["proj_queue"]},
        {"min_projects": 1, "excluded_entry_ids": ["proj_queue"]},
        {"min_projects": 2},
        {"required_sections": ["projects"], "max_projects": 0},
        {"required_entry_ids": ["proj_queue"], "max_projects": 0},
    ],
)
def test_project_budgets_cannot_override_required_or_excluded_content(
    sample_data: dict[str, Any], preferences: dict[str, Any]
) -> None:
    sample_data["resume_preferences"] = preferences
    with pytest.raises(ValidationError, match="resume_preferences"):
        UserProfile.model_validate(sample_data)


@pytest.mark.parametrize("section", [*UserProfile.SECTION_PREFIXES, "skills", "coursework"])
def test_required_sections_must_have_available_content(section: str) -> None:
    with pytest.raises(ValidationError, match="non-excluded content"):
        UserProfile.model_validate(
            {
                "schema_version": 1,
                "person": {"name": "Example"},
                "resume_preferences": {"required_sections": [section]},
            }
        )


def test_valid_preferences_round_trip_without_removing_excluded_evidence(
    sample_data: dict[str, Any],
) -> None:
    original = deepcopy(sample_data)
    sample_data["resume_preferences"] = {
        "required_sections": [*UserProfile.SECTION_PREFIXES, "skills", "coursework"],
        "required_entry_ids": ["exp_example", "proj_queue"],
        "min_projects": 1,
        "max_projects": 2,
        "min_bullets_per_entry": 1,
        "max_bullets_per_entry": 3,
    }
    profile = UserProfile.model_validate(sample_data)
    assert UserProfile.model_validate_json(profile.model_dump_json()) == profile
    assert len(profile.entries()) == 8
    assert profile.accomplishments[2].verified == original["accomplishments"][2]["verified"]
    sample_data["resume_preferences"] = {"excluded_entry_ids": ["proj_queue"], "max_projects": 0}
    excluded = UserProfile.model_validate(sample_data)
    assert excluded.projects and excluded.accomplishments and excluded.verified_bullets


def test_required_unverified_work_is_not_approved_by_preferences(
    sample_data: dict[str, Any],
) -> None:
    sample_data["resume_preferences"] = {"required_entry_ids": ["proj_queue"]}
    profile = UserProfile.model_validate(sample_data)
    assert profile.accomplishments[2].verified is False
    assert any("acc_queue_pending: unverified" in warning for warning in find_profile_gaps(profile))
