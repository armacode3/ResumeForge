"""Completeness flags must not become invented facts or mandatory metrics."""

from typing import Any

from resumeforge.profile import UserProfile, find_profile_gaps


def test_minimal_profile_is_valid_but_incomplete() -> None:
    profile = UserProfile.model_validate({"schema_version": 1, "person": {"name": "Example"}})
    assert len(find_profile_gaps(profile)) == 4
    assert profile.accomplishments == []


def test_flags_only_real_gaps_without_inventing_metrics(sample_data: dict[str, Any]) -> None:
    profile = UserProfile.model_validate(sample_data)
    warnings = find_profile_gaps(profile)

    assert "acc_queue_pending: unverified; user review required before use as evidence." in warnings
    assert any("edu_example: no verified accomplishment" in warning for warning in warnings)
    assert not any("acc_api:" in warning or "acc_queue:" in warning for warning in warnings)
    assert not any("metric" in warning for warning in warnings)
    assert profile.accomplishments[1].metrics == []


def test_incomplete_dates_are_reported(sample_data: dict[str, Any]) -> None:
    sample_data["projects"][0]["end_date"] = None
    profile = UserProfile.model_validate(sample_data)

    assert any("proj_queue: incomplete dates" in warning for warning in find_profile_gaps(profile))


def test_missing_institution_and_employer_are_reported(sample_data: dict[str, Any]) -> None:
    sample_data["education"][0]["organization"] = None
    sample_data["experiences"][0]["organization"] = None
    warnings = find_profile_gaps(UserProfile.model_validate(sample_data))

    assert "edu_example: missing institution or employer name." in warnings
    assert "exp_example: missing institution or employer name." in warnings


def test_complete_evidence_can_have_no_warnings() -> None:
    profile = UserProfile.model_validate(
        {
            "schema_version": 1,
            "person": {"name": "Example", "phone": "555-0100"},
            "education": [
                {
                    "id": "edu_demo",
                    "title": "Degree",
                    "organization": "Fictional University",
                    "start_date": "2020-01",
                    "end_date": "2024-01",
                }
            ],
            "projects": [
                {
                    "id": "proj_demo",
                    "title": "Utility",
                    "start_date": "2024-01",
                    "end_date": "present",
                }
            ],
            "accomplishments": [
                {
                    "id": "acc_degree",
                    "entry_id": "edu_demo",
                    "statement": "Completed coursework.",
                    "verified": True,
                },
                {
                    "id": "acc_project",
                    "entry_id": "proj_demo",
                    "statement": "Built a utility.",
                    "verified": True,
                },
            ],
        }
    )
    assert find_profile_gaps(profile) == []
