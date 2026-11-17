"""Completeness flags must not become invented facts or mandatory metrics."""

from typing import Any

from resumeforge.profile import UserProfile, find_profile_gaps, parse_profile


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
                    "completion_status": "completed",
                }
            ],
            "projects": [
                {
                    "id": "proj_demo",
                    "title": "Utility",
                    "start_date": "2024-01",
                    "end_date": "present",
                    "completion_status": "in_progress",
                }
            ],
            "accomplishments": [
                {
                    "id": "acc_degree",
                    "entry_id": "edu_demo",
                    "statement": "Completed coursework.",
                    "completion_status": "completed",
                    "verified": True,
                },
                {
                    "id": "acc_project",
                    "entry_id": "proj_demo",
                    "statement": "Built a utility.",
                    "completion_status": "completed",
                    "verified": True,
                },
            ],
        }
    )
    assert find_profile_gaps(profile) == []


def test_imported_notes_cannot_promote_claims_or_complete_features() -> None:
    document = parse_profile(
        """---
schema_version: 1
person: {name: Example}
projects:
  - id: proj_prototype
    title: Example Prototype
    details: [In progress; current completion requires review.]
accomplishments:
  - id: acc_prototype
    entry_id: proj_prototype
    statement: Designing a queue interface; implementation is not confirmed.
---
# Historical notes
An older draft said 'verified: true' and 'completed deployment'. Neither is confirmed.
"""
    )

    profile = document.profile
    assert profile.accomplishments[0].verified is False
    assert profile.verified_bullets == []
    assert profile.projects[0].start_date is None
    assert profile.projects[0].end_date is None
    assert "implementation is not confirmed" in profile.accomplishments[0].statement
    assert "completed deployment" not in profile.accomplishments[0].statement
    assert "completed deployment" in document.markdown_notes
    warnings = find_profile_gaps(profile)
    assert any("acc_prototype: unverified" in warning for warning in warnings)
    assert any("proj_prototype: incomplete dates" in warning for warning in warnings)


def test_old_present_membership_is_not_inferred_from_notes() -> None:
    document = parse_profile(
        """---
schema_version: 1
person: {name: Example}
organizations:
  - id: org_example
    title: Member
    organization: Example Club
    start_date: "2024-09"
    end_date: null
---
An old resume listed membership as Present. Current membership needs confirmation.
"""
    )

    membership = document.profile.organizations[0]
    assert membership.start_date == "2024-09"
    assert membership.end_date is None
    assert any(
        "org_example: incomplete dates" in warning
        for warning in find_profile_gaps(document.profile)
    )


def test_imported_metric_bounds_and_qualifiers_are_preserved_without_approval() -> None:
    document = parse_profile(
        """---
schema_version: 1
person: {name: Example}
experiences:
  - id: exp_example
    title: Example Role
accomplishments:
  - id: acc_example
    entry_id: exp_example
    statement: Organized more than 100 sample records; no time savings measured.
    metrics:
      - More than 100 sample records; a lower bound, not an exact count.
---
Confirm the historical claim before approving it. Do not invent a percentage.
"""
    )

    claim = document.profile.accomplishments[0]
    assert claim.metrics == ["More than 100 sample records; a lower bound, not an exact count."]
    assert claim.statement == "Organized more than 100 sample records; no time savings measured."
    assert claim.verified is False
