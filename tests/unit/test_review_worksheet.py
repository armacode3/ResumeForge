"""Pending worksheets reduce copying, never select or carry forward user attestations."""

import json
from dataclasses import dataclass
from typing import Any
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from resumeforge.jobs import JobDocument, JobRequirements
from resumeforge.planning import PlanSelection
from resumeforge.profile import UserProfile
from resumeforge.profile.models import ResumePreferences
from resumeforge.resume import (
    ResumeDocument,
    ResumeError,
    ReviewWorksheet,
    apply_review_decisions,
    build_review_worksheet,
    parse_resume_document,
    parse_review_decisions,
    review_resume,
)


@dataclass
class WorksheetInputs:
    profile: UserProfile
    job: JobDocument
    requirements: JobRequirements
    selection: PlanSelection
    draft: ResumeDocument

    def build(self) -> ReviewWorksheet:
        return build_review_worksheet(
            self.profile,
            self.job,
            self.requirements,
            self.selection,
            self.draft,
            requirements_reviewed=True,
            selection_reviewed=True,
        )


@pytest.fixture
def worksheet_inputs(
    sample_data: dict[str, Any], job_text: str, job_payload: dict[str, Any]
) -> WorksheetInputs:
    sample_data["resume_preferences"]["min_bullets_per_entry"] = 0
    profile = UserProfile.model_validate(sample_data)
    job = JobDocument(job_text)
    requirements = JobRequirements.model_validate(job_payload)
    selection = PlanSelection.model_validate(
        {
            "schema_version": 1,
            "entries": [
                {"entry_id": "edu_example", "accomplishment_ids": []},
                {"entry_id": "exp_example", "accomplishment_ids": ["acc_api"]},
                {"entry_id": "proj_queue", "accomplishment_ids": ["acc_queue"]},
            ],
        }
    )
    draft = review_resume(
        profile, job, requirements, selection, requirements_reviewed=True, selection_reviewed=True
    ).document
    return WorksheetInputs(profile, job, requirements, selection, draft)


def edit_first(inputs: WorksheetInputs) -> None:
    data = inputs.draft.model_dump(mode="json")
    data["sections"][1]["entries"][0]["bullets"][0]["text"] = "Owned 99 endpoints."
    inputs.draft = parse_resume_document(json.dumps(data))


@pytest.mark.parametrize("edited", [False, True])
def test_worksheet_keeps_fresh_context_and_all_choices_pending(
    worksheet_inputs: WorksheetInputs,
    edited: bool,
) -> None:
    inputs = worksheet_inputs
    if edited:
        edit_first(inputs)
    before = inputs.profile.model_dump_json(), inputs.draft.model_dump_json()
    with patch("socket.socket", side_effect=AssertionError("Offline")):
        worksheet = inputs.build()
    assert worksheet.worksheet_version == "pending-review-worksheet-v1"
    assert worksheet.status == "needs_review" and not worksheet.rendering_authorized
    assert worksheet.scope == "bullet_wording_only"
    assert worksheet.review.document == inputs.draft
    assert worksheet.review.mode == "submitted_draft"
    assert worksheet.review.plan.job_items
    assert worksheet.review.bullets[1].caveats == ("parent_entry_in_progress",)
    assert before == (inputs.profile.model_dump_json(), inputs.draft.model_dump_json())
    template = worksheet.decision_template
    assert (
        template.schema_version == 3 and template.review_version == worksheet.review.review_version
    )
    assert template.plan_sha256 == worksheet.review.document.plan_sha256
    assert template.document_sha256 == worksheet.review.document_sha256
    assert template.findings_sha256 == worksheet.review.findings_sha256
    assert template.fragments_sha256 == worksheet.review.fragments_sha256
    for pending, reviewed in zip(template.bullets, worksheet.review.bullets, strict=True):
        assert pending.bullet_id == reviewed.bullet_id
        assert pending.decision is pending.reason is None
        assert pending.acknowledged_finding_ids == ()
        assert [f.fragment_id for f in pending.fragment_decisions] == [
            f.id for f in reviewed.source_fragments
        ]
        assert all(
            f.disposition is f.reason is f.draft_span is None for f in pending.fragment_decisions
        )
        assert reviewed.review_status == "pending_review"
    text = worksheet.model_dump_json()
    assert "alex@example.com" not in text and "Résumé wording idea" not in text
    assert "acc_queue_pending" not in text
    assert worksheet == inputs.build()
    with pytest.raises(ResumeError, match="fields"):
        parse_review_decisions(text)
    with pytest.raises(ResumeError, match="fields"):
        parse_resume_document(text)
    with pytest.raises(ResumeError, match="fields"):
        parse_review_decisions(template.model_dump_json())
    with pytest.raises(ValidationError):
        template.bullets[0].decision = None
    with pytest.raises(ValidationError):
        worksheet.rendering_authorized = False


def complete_template(worksheet: ReviewWorksheet) -> dict[str, Any]:
    """Fictional review, never production bulk-approval guidance."""
    data = worksheet.decision_template.model_dump(mode="json")
    for choice, bullet in zip(data["bullets"], worksheet.review.bullets, strict=True):
        choice.update(decision="approve", reason="Fictional user reviewed this exact snapshot.")
        choice["acknowledged_finding_ids"] = [f.id for f in bullet.findings]
        for fragment in choice["fragment_decisions"]:
            fragment.update(disposition="needs_revision", reason="Correct wording before use.")
    return data


def test_completed_template_uses_existing_independent_fragment_and_confirmation_gates(
    worksheet_inputs: WorksheetInputs,
) -> None:
    inputs = worksheet_inputs
    edit_first(inputs)
    worksheet = inputs.build()
    data = complete_template(worksheet)
    choices = parse_review_decisions(json.dumps(data))
    with pytest.raises(ResumeError, match="Explicitly confirm"):
        apply_review_decisions(
            inputs.profile,
            inputs.job,
            inputs.requirements,
            inputs.selection,
            inputs.draft,
            choices,
            requirements_reviewed=True,
            selection_reviewed=True,
        )
    result = apply_review_decisions(
        inputs.profile,
        inputs.job,
        inputs.requirements,
        inputs.selection,
        inputs.draft,
        choices,
        requirements_reviewed=True,
        selection_reviewed=True,
        decisions_confirmed=True,
    )
    assert result.status == "needs_review" and result.bullets[0].revision_fragment_ids
    assert result.review.document == inputs.draft and not result.rendering_authorized
    # Dropping an unresolved fragment record is not approval: it becomes unreviewed.
    data["bullets"][0]["fragment_decisions"] = []
    result = apply_review_decisions(
        inputs.profile,
        inputs.job,
        inputs.requirements,
        inputs.selection,
        inputs.draft,
        parse_review_decisions(json.dumps(data)),
        requirements_reviewed=True,
        selection_reviewed=True,
        decisions_confirmed=True,
    )
    assert result.status == "needs_review" and result.bullets[0].unreviewed_fragment_ids


@pytest.mark.parametrize("gate", ["requirements_reviewed", "selection_reviewed"])
@pytest.mark.parametrize("value", [False, None, 1, "true"])
def test_worksheet_requires_exact_review_flags_before_inspection(
    worksheet_inputs: WorksheetInputs,
    gate: str,
    value: Any,
) -> None:
    inputs = worksheet_inputs
    flags = {"requirements_reviewed": True, "selection_reviewed": True, gate: value}
    with (
        patch(
            "resumeforge.resume.worksheet.review_resume",
            side_effect=AssertionError("No inspection"),
        ),
        pytest.raises(ResumeError, match="Explicitly confirm"),
    ):
        build_review_worksheet(
            inputs.profile, inputs.job, inputs.requirements, inputs.selection, inputs.draft, **flags
        )


def test_worksheet_requires_explicit_draft_and_no_default_confirmation(
    worksheet_inputs: WorksheetInputs,
) -> None:
    inputs = worksheet_inputs
    with pytest.raises(ResumeError, match="Explicitly confirm"):
        build_review_worksheet(
            inputs.profile, inputs.job, inputs.requirements, inputs.selection, inputs.draft
        )
    missing: Any = None
    with (
        patch(
            "resumeforge.resume.worksheet.review_resume",
            side_effect=AssertionError("No inspection"),
        ),
        pytest.raises(ResumeError, match="explicit draft"),
    ):
        build_review_worksheet(
            inputs.profile,
            inputs.job,
            inputs.requirements,
            inputs.selection,
            missing,
            requirements_reviewed=True,
            selection_reviewed=True,
        )


@pytest.mark.parametrize("mode", ["stale", "malformed", "reordered"])
def test_worksheet_revalidates_original_sources_and_draft(
    worksheet_inputs: WorksheetInputs, mode: str
) -> None:
    inputs = worksheet_inputs
    if mode == "stale":
        inputs.profile.accomplishments[0].statement += " More source context."
    elif mode == "malformed":
        inputs.draft = inputs.draft.model_copy(update={"status": "private-value"})
    else:
        inputs.draft = inputs.draft.model_copy(
            update={"sections": tuple(reversed(inputs.draft.sections))}
        )
    with pytest.raises(ResumeError) as error:
        inputs.build()
    assert "private-value" not in str(error.value)


def test_conflicted_and_empty_worksheets_cannot_be_approved_by_generation(
    worksheet_inputs: WorksheetInputs,
) -> None:
    inputs = worksheet_inputs
    inputs.profile.resume_preferences.min_bullets_per_entry = 1
    seed = review_resume(
        inputs.profile,
        inputs.job,
        inputs.requirements,
        inputs.selection,
        requirements_reviewed=True,
        selection_reviewed=True,
    )
    inputs.draft = seed.document
    worksheet = inputs.build()
    assert worksheet.status == "blocked_by_plan"
    assert worksheet.review.plan.constraint_status == "conflicts"
    assert worksheet.review.document.sections[0].entries[0].bullets == ()
    assert len(worksheet.decision_template.bullets) == 2
    inputs.profile.resume_preferences = ResumePreferences()
    inputs.selection.entries = []
    inputs.draft = review_resume(
        inputs.profile,
        inputs.job,
        inputs.requirements,
        inputs.selection,
        requirements_reviewed=True,
        selection_reviewed=True,
    ).document
    worksheet = inputs.build()
    assert worksheet.status == "needs_review" and worksheet.decision_template.bullets == ()
    choices = parse_review_decisions(worksheet.decision_template.model_dump_json())
    result = apply_review_decisions(
        inputs.profile,
        inputs.job,
        inputs.requirements,
        inputs.selection,
        inputs.draft,
        choices,
        requirements_reviewed=True,
        selection_reviewed=True,
        decisions_confirmed=True,
    )
    assert result.status == "needs_review" and not result.rendering_authorized


def test_worksheet_output_is_bounded_without_truncation(
    worksheet_inputs: WorksheetInputs,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("resumeforge.resume.worksheet.MAX_INPUT_BYTES", 1)
    with pytest.raises(ResumeError, match="byte limit"):
        worksheet_inputs.build()


def test_future_inspection_policy_cannot_emit_an_old_decision_template(
    worksheet_inputs: WorksheetInputs,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("resumeforge.resume.engine.REVIEW_VERSION", "private-future-policy")
    with pytest.raises(ResumeError, match="Invalid worksheet") as error:
        worksheet_inputs.build()
    assert "private" not in str(error.value)


@pytest.mark.parametrize("prefill", ["approve", "reject", "reason", "acknowledge", "fragment"])
def test_pending_output_schema_cannot_represent_prefilled_attestations(
    worksheet_inputs: WorksheetInputs,
    prefill: str,
) -> None:
    edit_first(worksheet_inputs)
    data = worksheet_inputs.build().model_dump()
    choice = data["decision_template"]["bullets"][0]
    if prefill in ("approve", "reject"):
        choice["decision"] = prefill
    elif prefill == "reason":
        choice["reason"] = "Some asserted review."
    elif prefill == "acknowledge":
        choice["acknowledged_finding_ids"] = ("0" * 64,)
    else:
        choice["fragment_decisions"][0]["disposition"] = "omission_accepted"
    with pytest.raises(ValidationError):
        ReviewWorksheet.model_validate(data)


def test_deliberately_completed_verbatim_template_can_apply_but_never_transfer_to_new_wording(
    worksheet_inputs: WorksheetInputs,
) -> None:
    inputs = worksheet_inputs
    worksheet = inputs.build()
    data = complete_template(worksheet)
    choices = parse_review_decisions(json.dumps(data))
    result = apply_review_decisions(
        inputs.profile,
        inputs.job,
        inputs.requirements,
        inputs.selection,
        inputs.draft,
        choices,
        requirements_reviewed=True,
        selection_reviewed=True,
        decisions_confirmed=True,
    )
    assert result.status == "bullet_wording_approved_by_user" and not result.rendering_authorized
    edit_first(inputs)
    with pytest.raises(ResumeError, match="different draft snapshot"):
        apply_review_decisions(
            inputs.profile,
            inputs.job,
            inputs.requirements,
            inputs.selection,
            inputs.draft,
            choices,
            requirements_reviewed=True,
            selection_reviewed=True,
            decisions_confirmed=True,
        )
    fresh = inputs.build()
    assert all(b.decision is None for b in fresh.decision_template.bullets)
    assert fresh.decision_template.bullets[0].acknowledged_finding_ids == ()
