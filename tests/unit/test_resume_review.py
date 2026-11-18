"""Draft bindings and literal change observations are never semantic approval."""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from resumeforge.inputs import InputError
from resumeforge.jobs import JobDocument, JobRequirements
from resumeforge.planning import PlanSelection
from resumeforge.profile import UserProfile
from resumeforge.resume import (
    ResumeDocument,
    ResumeError,
    ResumeReview,
    load_resume_document,
    parse_resume_document,
    review_resume,
)


@dataclass
class ReviewInputs:
    profile: UserProfile
    job: JobDocument
    requirements: JobRequirements
    selection: PlanSelection

    def review(self, draft: ResumeDocument | None = None) -> ResumeReview:
        return review_resume(
            self.profile,
            self.job,
            self.requirements,
            self.selection,
            draft,
            requirements_reviewed=True,
            selection_reviewed=True,
        )


@pytest.fixture
def inputs(sample_data: dict[str, Any], job_text: str, job_payload: dict[str, Any]) -> ReviewInputs:
    sample_data["resume_preferences"]["min_bullets_per_entry"] = 0
    return ReviewInputs(
        UserProfile.model_validate(sample_data),
        JobDocument(job_text),
        JobRequirements.model_validate(job_payload),
        PlanSelection.model_validate(
            {
                "schema_version": 1,
                "entries": [
                    {"entry_id": "edu_example", "accomplishment_ids": []},
                    {"entry_id": "exp_example", "accomplishment_ids": ["acc_api"]},
                    {"entry_id": "proj_queue", "accomplishment_ids": ["acc_queue"]},
                ],
                "max_total_bullets": 4,
            }
        ),
    )


def first_bullet(data: dict[str, Any]) -> dict[str, Any]:
    bullet: dict[str, Any] = data["sections"][1]["entries"][0]["bullets"][0]
    return bullet


def test_seed_copies_whole_source_statements_with_no_profile_mutation_or_network(
    inputs: ReviewInputs,
) -> None:
    before = inputs.profile.model_dump_json()
    with patch("socket.socket", side_effect=AssertionError("Offline")):
        review = inputs.review()
    assert review.mode == "source_seed" and review.status == "needs_review"
    assert review.review_version == "resume-draft-review-v1"
    assert review.document.status == "needs_review"
    assert review.document.sections[0].entries[0].bullets == ()
    assert (
        review.document.sections[1].entries[0].bullets[0].text
        == inputs.profile.accomplishments[0].statement
    )
    assert review.document.sections[1].entries[0].bullets[0].id == "bullet_draft_api"
    assert all(
        b.wording_status == "verbatim_source" and b.review_status == "pending_review"
        for b in review.bullets
    )
    assert review.bullets[1].caveats == ("parent_entry_in_progress",)
    assert len(review.document.plan_sha256) == len(review.document_sha256) == 64
    assert review.plan.job_items and review.plan.sections[0].required
    assert inputs.profile.model_dump_json() == before
    assert review == inputs.review()
    text = review.model_dump_json()
    assert "alex@example.com" not in text and "Résumé wording idea" not in text
    assert "acc_queue_pending" not in text


def test_submitted_roundtrip_keeps_all_wording_pending_and_has_same_document_identity(
    inputs: ReviewInputs,
) -> None:
    seed = inputs.review()
    document = parse_resume_document("\ufeff" + seed.document.model_dump_json())
    submitted = inputs.review(document)
    assert submitted.mode == "submitted_draft"
    assert submitted.document == seed.document and submitted.document_sha256 == seed.document_sha256
    assert all(b.review_status == "pending_review" for b in submitted.bullets)


@pytest.mark.parametrize(
    "wording",
    [
        "Owned the entire service and managed the engineering team.",
        "Improved throughput by 93% using Kubernetes.",
        "Added tests for exactly 120 endpoints without supervision.",
        "Implemented automated tests for 12 existing internal API endpoints.",
        "Implemented automated tests for at least 12 endpoints under mentor review.",
    ],
)
def test_all_edits_need_review_including_invented_claims_and_lost_qualifiers(
    inputs: ReviewInputs, wording: str
) -> None:
    seed = inputs.review()
    data = seed.document.model_dump(mode="json")
    first_bullet(data)["text"] = wording
    review = inputs.review(parse_resume_document(json.dumps(data)))
    assert review.bullets[0].wording_status == "edited_requires_review"
    assert review.bullets[0].review_status == "pending_review"
    assert review.bullets[0].source_statement == inputs.profile.accomplishments[0].statement
    assert review.document_sha256 != seed.document_sha256
    assert "no semantic support check" in review.warnings[1]
    assert (
        review.status == "needs_review"
    )  # No claim that changed wording is supported or approved.


def test_plan_conflicts_block_even_verbatim_wording_without_filling_missing_education(
    inputs: ReviewInputs,
) -> None:
    inputs.profile.resume_preferences.min_bullets_per_entry = 1
    review = inputs.review()
    assert review.status == "blocked_by_plan"
    assert review.document.sections[0].entries[0].bullets == ()
    assert review.plan.constraint_status == "conflicts"
    assert all(b.wording_status == "verbatim_source" for b in review.bullets)
    assert any(f.code == "entry_bullet_minimum_not_met" for f in review.plan.findings)


@pytest.mark.parametrize("change", ["profile", "preferences", "job", "requirements", "selection"])
def test_source_changes_invalidate_prior_draft_binding(inputs: ReviewInputs, change: str) -> None:
    draft = inputs.review().document
    if change == "profile":
        inputs.profile.accomplishments[0].statement += " under further review"
    elif change == "preferences":
        inputs.profile.resume_preferences.max_bullets_per_entry = 2
    elif change == "job":
        inputs.job = JobDocument(inputs.job.text + "\nAdditional context.")
    elif change == "requirements":
        inputs.requirements.company = None
    else:
        inputs.selection.max_total_bullets = 5
    with pytest.raises(ResumeError, match="different plan snapshot"):
        inputs.review(draft)


@pytest.mark.parametrize(
    "change",
    [
        "section_missing",
        "section_order",
        "entry_missing",
        "entry_order",
        "evidence_missing",
        "evidence_unknown",
        "wrong_parent",
        "evidence_unselected",
    ],
)
def test_current_hash_cannot_bypass_exact_plan_structure(inputs: ReviewInputs, change: str) -> None:
    data = inputs.review().document.model_dump(mode="json")
    if change == "section_missing":
        data["sections"].pop(0)
    elif change == "section_order":
        data["sections"].reverse()
    elif change == "entry_missing":
        data["sections"][0]["entries"] = []
    elif change == "entry_order":
        data["sections"][0]["entries"][0]["entry_id"] = "edu_unknown"
    elif change == "evidence_missing":
        data["sections"][1]["entries"][0]["bullets"] = []
    else:
        first_bullet(data)["accomplishment_id"] = {
            "evidence_unknown": "acc_private_unknown",
            "wrong_parent": "acc_other_parent",
            "evidence_unselected": "acc_queue_pending",
        }[change]
    with pytest.raises(ResumeError) as error:
        inputs.review(parse_resume_document(json.dumps(data)))
    assert "private_unknown" not in str(error.value)


@pytest.mark.parametrize("blocker", ["excluded", "unverified", "unfinished", "unknown_parent"])
def test_ineligible_or_excluded_source_text_is_not_seeded_or_reintroduced(
    inputs: ReviewInputs, blocker: str
) -> None:
    inputs.profile.accomplishments[0].statement = "fictional-private-blocked-statement"
    if blocker == "excluded":
        inputs.profile.resume_preferences.required_entry_ids = []
        inputs.profile.resume_preferences.excluded_entry_ids.append("exp_example")
        inputs.profile.resume_preferences.required_sections.remove("experiences")
    elif blocker == "unverified":
        inputs.profile.verified_bullets = []
        inputs.profile.accomplishments[0].verified = False
    elif blocker == "unfinished":
        inputs.profile.accomplishments[0].completion_status = "in_progress"
    else:
        inputs.profile.experiences[0].completion_status = "unknown"
    review = inputs.review()
    assert review.status == "blocked_by_plan"
    assert "fictional-private-blocked-statement" not in review.model_dump_json()
    data = review.document.model_dump(mode="json")
    target = next(section for section in data["sections"] if section["section"] == "projects")
    target["entries"][0]["bullets"][0]["accomplishment_id"] = "acc_api"
    with pytest.raises(ResumeError, match="evidence"):
        inputs.review(parse_resume_document(json.dumps(data)))


@pytest.mark.parametrize("field", ["requirements_reviewed", "selection_reviewed"])
@pytest.mark.parametrize("value", [False, None, 1, "true"])
def test_review_acknowledgements_are_not_approval_and_must_be_exact_booleans(
    inputs: ReviewInputs, field: str, value: Any
) -> None:
    flags = {"requirements_reviewed": True, "selection_reviewed": True, field: value}
    with (
        patch(
            "resumeforge.planning.engine.match_evidence", side_effect=AssertionError("No matching")
        ),
        pytest.raises(ResumeError, match="Review"),
    ):
        review_resume(inputs.profile, inputs.job, inputs.requirements, inputs.selection, **flags)


def test_default_gates_are_closed(inputs: ReviewInputs) -> None:
    with pytest.raises(ResumeError, match="Review"):
        review_resume(inputs.profile, inputs.job, inputs.requirements, inputs.selection)


def test_mutated_models_cannot_skip_schema_validation(inputs: ReviewInputs) -> None:
    draft = inputs.review().document.model_copy(update={"sections": "fictional-private-invalid"})
    with pytest.raises(ResumeError, match="Invalid draft") as error:
        inputs.review(draft)
    assert "fictional-private" not in str(error.value)


def test_drafts_reviews_and_nested_records_are_immutable_snapshots(inputs: ReviewInputs) -> None:
    review = inputs.review()
    statement = review.bullets[0].source_statement
    inputs.profile.accomplishments[0].statement = "Later edit"
    assert review.bullets[0].source_statement == statement
    with pytest.raises(ValidationError):
        review.document.status = "needs_review"
    with pytest.raises(ValidationError):
        review.document.sections[1].entries[0].bullets[0].text = "Later edit"


@pytest.mark.parametrize(
    "change",
    [
        "approved_document",
        "approved_bullet",
        "extra_field",
        "duplicate_section",
        "duplicate_entry",
        "duplicate_bullet",
        "duplicate_evidence",
        "blank_wording",
        "long_wording",
        "version_bool",
        "version_unknown",
        "number_wording",
        "bad_hash",
        "surrogate",
    ],
)
def test_invalid_or_self_approved_draft_fields_are_rejected_safely(
    inputs: ReviewInputs, change: str
) -> None:
    data = inputs.review().document.model_dump(mode="json")
    if change == "approved_document":
        data["status"] = "approved"
    elif change == "approved_bullet":
        first_bullet(data)["review_status"] = "approved"
    elif change == "extra_field":
        data["fictional-private-field"] = "fictional-private-value"
    elif change == "duplicate_section":
        data["sections"].append(data["sections"][0])
    elif change == "duplicate_entry":
        data["sections"][0]["entries"] *= 2
    elif change in ("duplicate_bullet", "duplicate_evidence"):
        copy = dict(first_bullet(data))
        if change == "duplicate_evidence":
            copy["id"] = "bullet_another"
        data["sections"][1]["entries"][0]["bullets"].append(copy)
    elif change in ("blank_wording", "long_wording", "number_wording", "surrogate"):
        first_bullet(data)["text"] = {
            "blank_wording": " ",
            "long_wording": "x" * 8193,
            "number_wording": 123,
            "surrogate": "\ud800",
        }[change]
    elif change == "bad_hash":
        data["plan_sha256"] = "not-a-hash"
    else:
        data["schema_version"] = True if change == "version_bool" else 2
    with pytest.raises(ResumeError) as error:
        parse_resume_document(json.dumps(data))
    assert "fictional-private" not in str(error.value)


@pytest.mark.parametrize(
    "text",
    [
        "fictional-private-not-json",
        '{"sections":[],"sections":[]}',
        '{"schema_version":NaN}',
        "[" * 40 + "0" + "]" * 40,
        "[" * 2000 + "0" + "]" * 2000,
        "1" * 5000,
        "\ud800",
        "x" * 1_048_577,
    ],
)
def test_malformed_oversized_or_deep_draft_json_never_leaks_values(text: str) -> None:
    with pytest.raises(ResumeError) as error:
        parse_resume_document(text)
    assert "fictional-private" not in str(error.value)


def test_source_seed_limit_failure_is_safe_and_does_not_truncate_facts(
    inputs: ReviewInputs,
) -> None:
    inputs.profile.accomplishments[0].statement = "x" * 8193
    with pytest.raises(ResumeError, match="versioned draft limits"):
        inputs.review()


def test_unserializable_source_text_fails_safely_before_draft_construction(
    inputs: ReviewInputs,
) -> None:
    inputs.profile.accomplishments[0].statement = "fictional-private-\ud800"
    with pytest.raises(ResumeError, match="Invalid planning inputs") as error:
        inputs.review()
    assert "fictional-private" not in str(error.value)


def test_generated_document_size_is_bounded(
    inputs: ReviewInputs, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("resumeforge.resume.engine.MAX_INPUT_BYTES", 1)
    with pytest.raises(ResumeError, match="byte limit"):
        inputs.review()


def test_loader_handles_missing_and_valid_local_files(inputs: ReviewInputs, tmp_path: Path) -> None:
    path = tmp_path / "draft.json"
    with pytest.raises(InputError):
        load_resume_document(path)
    document = inputs.review().document
    path.write_text(document.model_dump_json())
    assert load_resume_document(path) == document


def test_outer_review_envelope_is_not_a_draft_input(inputs: ReviewInputs) -> None:
    with pytest.raises(ResumeError, match="draft fields"):
        parse_resume_document(inputs.review().model_dump_json())
