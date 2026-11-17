"""Conservative retrieval: traceable overlaps never become qualification or completion proof."""

import json
from dataclasses import asdict
from typing import Any
from unittest.mock import patch

import pytest

from resumeforge.jobs import JobDocument, JobRequirements
from resumeforge.matching import MatchingError, match_evidence
from resumeforge.profile import UserProfile


@pytest.fixture
def matching_profile() -> UserProfile:
    return UserProfile.model_validate(
        {
            "schema_version": 1,
            "person": {"name": "Fictional private name"},
            "projects": [{"id": "proj_demo", "title": "Demo", "completion_status": "in_progress"}],
            "accomplishments": [
                {
                    "id": "acc_demo",
                    "entry_id": "proj_demo",
                    "statement": "Implemented automated tests using Python.",
                    "technologies": ["Python"],
                    "verified": True,
                    "completion_status": "completed",
                }
            ],
        }
    )


def requirements_for(text: str, empty_job_payload: dict[str, Any]) -> JobRequirements:
    empty_job_payload["required_qualifications"] = [
        {"id": "job_req", "text": text, "source_quote": text}
    ]
    return JobRequirements.model_validate(empty_job_payload)


@pytest.mark.parametrize("reviewed", [False, None, 1, "true"])
def test_review_is_explicit_not_truthy(
    matching_profile: UserProfile, empty_job_payload: dict[str, Any], reviewed: Any
) -> None:
    requirements = requirements_for("Python experience.", empty_job_payload)
    with pytest.raises(MatchingError, match="confirm review"):
        match_evidence(
            matching_profile,
            JobDocument("Python experience."),
            requirements,
            requirements_reviewed=reviewed,
        )


def test_default_review_is_not_granted(
    matching_profile: UserProfile, empty_job_payload: dict[str, Any]
) -> None:
    with pytest.raises(MatchingError, match="confirm review"):
        match_evidence(
            matching_profile, JobDocument("Python"), requirements_for("Python", empty_job_payload)
        )


def test_eligible_scoped_subtask_preserves_context_and_does_not_read_notes_or_network(
    matching_profile: UserProfile, empty_job_payload: dict[str, Any]
) -> None:
    requirements = requirements_for("Python experience.", empty_job_payload)
    before = matching_profile.model_dump_json()
    with patch("socket.socket", side_effect=AssertionError("No network")):
        report = match_evidence(
            matching_profile,
            JobDocument("Python experience."),
            requirements,
            requirements_reviewed=True,
        )
    assert report.requirements_reviewed
    assert report.matching_version == "evidence-matching-v1"
    assert (
        report.profile_model_sha256
        and report.requirements_model_sha256
        and report.job_source_sha256
    )
    assert report.evidence[0].statement == "Implemented automated tests using Python."
    assert report.evidence[0].completion_status == "completed"
    assert report.evidence[0].entry_completion_status == "in_progress"
    item = report.items[0]
    assert (item.job_item_id, item.section, item.text, item.source_quote) == (
        "job_req",
        "required_qualifications",
        "Python experience.",
        "Python experience.",
    )
    assert item.status == "lexical_candidates"
    assert item.candidates[0].accomplishment_id == "acc_demo"
    assert item.candidates[0].caveats == ("parent_entry_in_progress",)
    assert item.candidates[0].overlaps[0].basis == "technology_mention"
    assert matching_profile.model_dump_json() == before
    assert len(report.warnings) == 3
    assert "Fictional private name" not in json.dumps(asdict(report))


@pytest.mark.parametrize(
    ("verified", "status", "parent", "excluded", "eligibility", "reason"),
    [
        (True, "completed", "completed", True, "excluded", "excluded_entry"),
        (False, "completed", "completed", False, "unverified", "unverified_accomplishment"),
        (True, "unknown", "completed", False, "status_review_required", "unknown_completion"),
        (
            True,
            "planned",
            "completed",
            False,
            "status_review_required",
            "unfinished_accomplishment",
        ),
        (
            True,
            "in_progress",
            "completed",
            False,
            "status_review_required",
            "unfinished_accomplishment",
        ),
        (
            True,
            "on_hold",
            "completed",
            False,
            "status_review_required",
            "unfinished_accomplishment",
        ),
        (
            True,
            "cancelled",
            "completed",
            False,
            "status_review_required",
            "unfinished_accomplishment",
        ),
        (True, "completed", "unknown", False, "status_review_required", "unknown_entry_status"),
        (
            True,
            "completed",
            "planned",
            False,
            "status_review_required",
            "entry_status_requires_review",
        ),
        (
            True,
            "completed",
            "on_hold",
            False,
            "status_review_required",
            "entry_status_requires_review",
        ),
        (
            True,
            "completed",
            "cancelled",
            False,
            "status_review_required",
            "entry_status_requires_review",
        ),
    ],
)
def test_ineligible_evidence_is_never_a_candidate(
    matching_profile: UserProfile,
    empty_job_payload: dict[str, Any],
    verified: bool,
    status: str,
    parent: str,
    excluded: bool,
    eligibility: str,
    reason: str,
) -> None:
    data = matching_profile.model_dump()
    data["accomplishments"][0].update(verified=verified, completion_status=status)
    data["projects"][0]["completion_status"] = parent
    if excluded:
        data["resume_preferences"]["excluded_entry_ids"] = ["proj_demo"]
    profile = UserProfile.model_validate(data)
    report = match_evidence(
        profile,
        JobDocument("Python"),
        requirements_for("Python", empty_job_payload),
        requirements_reviewed=True,
    )
    decision = report.evidence[0]
    assert decision.eligibility == eligibility
    assert reason in decision.reasons
    assert decision.statement is None and decision.technologies == ()
    assert report.items[0].candidates == ()
    assert report.items[0].status == "no_lexical_candidates"


@pytest.mark.parametrize(
    ("term", "text", "matches"),
    [
        ("Python", "python", True),
        ("Python", "Pythonic", False),
        ("SQL", "PostgreSQL", False),
        ("Java", "JavaScript", False),
        ("C", "C++", False),
        ("C", "C#", False),
        ("C++", "Use C++.", True),
        ("C#", "Use C#.", True),
        (".NET", "Use .NET.", True),
        (".NET", "ASP.NET", False),
        ("Node.js", "Node.js", True),
        ("Py(th)on", "Py(th)on", True),
        ("Python", "Pyton", False),
        ("Python", "Python experience", True),
    ],
)
def test_literal_matching_is_case_insensitive_bounded_and_not_fuzzy(
    matching_profile: UserProfile,
    empty_job_payload: dict[str, Any],
    term: str,
    text: str,
    matches: bool,
) -> None:
    matching_profile.accomplishments[0].technologies = [term]
    matching_profile.accomplishments[0].statement = "A different scoped assertion."
    report = match_evidence(
        matching_profile,
        JobDocument(text),
        requirements_for(text, empty_job_payload),
        requirements_reviewed=True,
    )
    assert bool(report.items[0].candidates) is matches
    if matches:
        overlap = report.items[0].candidates[0].overlaps[0]
        assert overlap.evidence_text == term
        assert overlap.job_text in text


def test_exact_job_phrase_in_verified_statement_can_retrieve_non_technology_evidence(
    matching_profile: UserProfile, empty_job_payload: dict[str, Any]
) -> None:
    matching_profile.accomplishments[0].technologies = []
    report = match_evidence(
        matching_profile,
        JobDocument("automated tests"),
        requirements_for("automated tests", empty_job_payload),
        requirements_reviewed=True,
    )
    overlap = report.items[0].candidates[0].overlaps[0]
    assert overlap.basis == "job_phrase_in_statement"
    assert overlap.evidence_text == overlap.job_text == "automated tests"


def test_unscoped_skills_entry_technologies_and_verified_bullets_are_not_evidence(
    matching_profile: UserProfile, empty_job_payload: dict[str, Any]
) -> None:
    matching_profile.skills.languages = ["Rust"]
    matching_profile.projects[0].technologies = ["Rust"]
    matching_profile.projects[0].details = ["Planned Rust work, not a scoped verified result."]
    data = matching_profile.model_dump()
    data["verified_bullets"] = [
        {"id": "bullet_demo", "text": "Rust expertise", "accomplishment_ids": ["acc_demo"]}
    ]
    profile = UserProfile.model_validate(data)
    report = match_evidence(
        profile,
        JobDocument("Rust"),
        requirements_for("Rust", empty_job_payload),
        requirements_reviewed=True,
    )
    assert report.items[0].candidates == ()


def test_excluded_evidence_cannot_reenter_through_a_verified_bullet(
    matching_profile: UserProfile, empty_job_payload: dict[str, Any]
) -> None:
    data = matching_profile.model_dump()
    data["resume_preferences"]["excluded_entry_ids"] = ["proj_demo"]
    data["verified_bullets"] = [
        {
            "id": "bullet_demo",
            "text": "Implemented Python tests.",
            "accomplishment_ids": ["acc_demo"],
        }
    ]
    profile = UserProfile.model_validate(data)
    report = match_evidence(
        profile,
        JobDocument("Python"),
        requirements_for("Python", empty_job_payload),
        requirements_reviewed=True,
    )
    assert report.evidence[0].eligibility == "excluded"
    assert report.items[0].candidates == ()
    assert profile.verified_bullets[0].accomplishment_ids == ["acc_demo"]


def test_required_eligible_entry_is_not_discarded_for_lack_of_lexical_overlap(
    matching_profile: UserProfile, empty_job_payload: dict[str, Any]
) -> None:
    data = matching_profile.model_dump()
    data["resume_preferences"]["required_entry_ids"] = ["proj_demo"]
    report = match_evidence(
        UserProfile.model_validate(data),
        JobDocument("Rust"),
        requirements_for("Rust", empty_job_payload),
        requirements_reviewed=True,
    )
    assert report.evidence[0].required_entry
    assert report.evidence[0].eligibility == "eligible_for_matching"
    assert report.items[0].candidates == ()
    assert report.findings == ()


def test_profile_without_accomplishments_reports_no_candidates_not_missing_qualifications(
    empty_job_payload: dict[str, Any],
) -> None:
    profile = UserProfile.model_validate({"schema_version": 1, "person": {"name": "Example"}})
    report = match_evidence(
        profile,
        JobDocument("Python"),
        requirements_for("Python", empty_job_payload),
        requirements_reviewed=True,
    )
    assert report.evidence == ()
    assert report.items[0].status == "no_lexical_candidates"
    assert report.items[0].candidates == ()
    assert "does not mean missing experience" in report.warnings[1]


@pytest.mark.parametrize(
    "text", ["Python or Java; either is sufficient.", "Python is not required."]
)
def test_overlap_never_splits_or_satisfies_qualified_job_text(
    matching_profile: UserProfile, empty_job_payload: dict[str, Any], text: str
) -> None:
    report = match_evidence(
        matching_profile,
        JobDocument(text),
        requirements_for(text, empty_job_payload),
        requirements_reviewed=True,
    )
    assert report.items[0].text == report.items[0].source_quote == text
    assert report.items[0].candidates
    assert "not proof of qualification" in report.warnings[0]


def test_omitted_taxonomy_tag_does_not_hide_preferred_clause(
    matching_profile: UserProfile, empty_job_payload: dict[str, Any]
) -> None:
    empty_job_payload["preferred_qualifications"] = [
        {"id": "job_pref", "text": "Python preferred.", "source_quote": "Python preferred."}
    ]
    requirements = JobRequirements.model_validate(empty_job_payload)
    report = match_evidence(
        matching_profile, JobDocument("Python preferred."), requirements, requirements_reviewed=True
    )
    assert len(report.items) == 1
    assert report.items[0].section == "preferred_qualifications"
    assert report.items[0].candidates


def test_empty_results_are_explicit_not_qualification_failures(
    matching_profile: UserProfile, empty_job_payload: dict[str, Any]
) -> None:
    report = match_evidence(
        matching_profile,
        JobDocument("Unstructured source"),
        JobRequirements.model_validate(empty_job_payload),
        requirements_reviewed=True,
    )
    assert report.items == ()
    assert "absence from the original job" in report.warnings[1]


def test_constraints_report_review_gaps_without_approving_or_selecting_evidence(
    matching_profile: UserProfile, empty_job_payload: dict[str, Any]
) -> None:
    data = matching_profile.model_dump()
    data["accomplishments"][0]["verified"] = False
    data["skills"]["languages"] = ["Python"]
    data["coursework"] = ["Databases"]
    data["resume_preferences"] = {
        "required_entry_ids": ["proj_demo"],
        "required_sections": ["projects", "skills", "coursework"],
        "min_projects": 1,
        "max_bullets_per_entry": 0,
    }
    report = match_evidence(
        UserProfile.model_validate(data),
        JobDocument("Python"),
        requirements_for("Python", empty_job_payload),
        requirements_reviewed=True,
    )
    assert report.evidence[0].required_entry
    assert report.items[0].candidates == ()
    assert [finding.code for finding in report.findings] == [
        "required_entry_without_eligible_evidence",
        "required_section_without_eligible_evidence",
        "section_requires_separate_evidence_review",
        "section_requires_separate_evidence_review",
        "project_minimum_needs_review",
    ]


def test_input_revalidation_and_grounding_errors_are_safe(
    matching_profile: UserProfile, empty_job_payload: dict[str, Any]
) -> None:
    requirements = requirements_for("Fictional private source text", empty_job_payload)
    with pytest.raises(MatchingError, match="quote absent") as error:
        match_evidence(
            matching_profile, JobDocument("Other source"), requirements, requirements_reviewed=True
        )
    assert "Fictional private source text" not in str(error.value)
    matching_profile.accomplishments[0].entry_id = "proj_missing"
    with pytest.raises(MatchingError, match="Invalid matching inputs") as error:
        match_evidence(
            matching_profile,
            JobDocument("Fictional private source text"),
            requirements,
            requirements_reviewed=True,
        )
    assert "proj_missing" not in str(error.value)


def test_unchecked_model_copy_cannot_bypass_strict_schema_or_emit_serialization_values(
    matching_profile: UserProfile, empty_job_payload: dict[str, Any]
) -> None:
    requirements = requirements_for("Python", empty_job_payload)
    invalid = requirements.model_copy(
        update={"required_qualifications": "fictional-private-serialized-value"}
    )
    with pytest.raises(MatchingError, match="Invalid matching inputs") as error:
        match_evidence(matching_profile, JobDocument("Python"), invalid, requirements_reviewed=True)
    assert "fictional-private" not in str(error.value)


def test_comparison_budget_fails_before_retrieval(
    matching_profile: UserProfile,
    empty_job_payload: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("resumeforge.matching.engine.MAX_MATCH_PAIRS", 0)
    with pytest.raises(MatchingError, match="comparison budget"):
        match_evidence(
            matching_profile,
            JobDocument("Python"),
            requirements_for("Python", empty_job_payload),
            requirements_reviewed=True,
        )


def test_ordering_and_duplicate_technology_labels_are_deterministic(
    matching_profile: UserProfile, empty_job_payload: dict[str, Any]
) -> None:
    data = matching_profile.model_dump()
    second = {**data["accomplishments"][0], "id": "acc_another"}
    data["accomplishments"].append(second)
    data["accomplishments"][0]["technologies"] = ["Python", "PYTHON"]
    profile = UserProfile.model_validate(data)
    requirements = requirements_for("Python", empty_job_payload)
    report = match_evidence(
        profile, JobDocument("Python"), requirements, requirements_reviewed=True
    )
    assert [record.accomplishment_id for record in report.evidence] == ["acc_another", "acc_demo"]
    assert [candidate.accomplishment_id for candidate in report.items[0].candidates] == [
        "acc_another",
        "acc_demo",
    ]
    assert (
        sum(
            overlap.basis == "technology_mention"
            for overlap in report.items[0].candidates[1].overlaps
        )
        == 1
    )
    assert report == match_evidence(
        profile, JobDocument("Python"), requirements, requirements_reviewed=True
    )
