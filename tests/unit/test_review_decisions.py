"""Human wording decisions bind snapshots, not biography, layout or plan-conflict approval."""

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
from resumeforge.profile.models import ResumePreferences
from resumeforge.resume import (
    ResumeDocument,
    ResumeError,
    ResumeReview,
    ReviewDecisionResult,
    ReviewDecisions,
    apply_review_decisions,
    load_review_decisions,
    parse_resume_document,
    parse_review_decisions,
    review_resume,
)


def decisions_for(review: ResumeReview) -> ReviewDecisions:
    return parse_review_decisions(
        json.dumps(
            {
                "schema_version": 1,
                "review_version": review.review_version,
                "plan_sha256": review.document.plan_sha256,
                "document_sha256": review.document_sha256,
                "bullets": [
                    {
                        "bullet_id": bullet.bullet_id,
                        "decision": "approve",
                        "reason": "Fictional reviewer checked wording and evidence in context.",
                    }
                    for bullet in review.bullets
                ],
            }
        )
    )


@dataclass
class DecisionInputs:
    profile: UserProfile
    job: JobDocument
    requirements: JobRequirements
    selection: PlanSelection
    draft: ResumeDocument
    decisions: ReviewDecisions

    def reseed(self) -> None:
        review = review_resume(
            self.profile,
            self.job,
            self.requirements,
            self.selection,
            requirements_reviewed=True,
            selection_reviewed=True,
        )
        self.draft = review.document
        self.decisions = decisions_for(review)

    def apply(self) -> ReviewDecisionResult:
        return apply_review_decisions(
            self.profile,
            self.job,
            self.requirements,
            self.selection,
            self.draft,
            self.decisions,
            requirements_reviewed=True,
            selection_reviewed=True,
            decisions_confirmed=True,
        )


@pytest.fixture
def decision_inputs(
    sample_data: dict[str, Any], job_text: str, job_payload: dict[str, Any]
) -> DecisionInputs:
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
    review = review_resume(
        profile, job, requirements, selection, requirements_reviewed=True, selection_reviewed=True
    )
    return DecisionInputs(
        profile, job, requirements, selection, review.document, decisions_for(review)
    )


def test_all_explicit_decisions_are_narrow_immutable_attestations_not_full_approval(
    decision_inputs: DecisionInputs,
) -> None:
    before = decision_inputs.profile.model_dump_json()
    with patch("socket.socket", side_effect=AssertionError("Offline")):
        result = decision_inputs.apply()
    assert result.decision_version == "snapshot-bound-decisions-v1"
    assert result.status == "bullet_wording_approved_by_user"
    assert result.scope == "bullet_wording_only" and result.rendering_authorized is False
    assert len(result.decisions_model_sha256) == 64
    assert all(b.review_status == "approved_by_user" for b in result.bullets)
    assert all(b.review_status == "pending_review" for b in result.review.bullets)
    assert result.review.document.status == "needs_review"
    assert result.review.document == decision_inputs.draft
    assert result.review.plan.sections[0].entries[0].bullet_slots == ()
    assert "mentor" in result.review.bullets[0].source_statement
    assert result.review.bullets[1].caveats == ("parent_entry_in_progress",)
    assert before == decision_inputs.profile.model_dump_json()
    assert result == decision_inputs.apply()
    assert "alex@example.com" not in result.model_dump_json()
    with pytest.raises(ValidationError):
        result.rendering_authorized = False


@pytest.mark.parametrize("count", [0, 1])
def test_missing_decisions_stay_pending_even_for_verbatim_wording(
    decision_inputs: DecisionInputs, count: int
) -> None:
    decision_inputs.decisions = decision_inputs.decisions.model_copy(
        update={"bullets": decision_inputs.decisions.bullets[:count]}
    )
    result = decision_inputs.apply()
    assert result.status == "needs_review"
    assert result.bullets[-1].review_status == "pending_review"
    assert result.bullets[-1].decision is None and result.bullets[-1].reason is None
    assert all(b.wording_status == "verbatim_source" for b in result.review.bullets)


@pytest.mark.parametrize("approve_first", [True, False])
def test_rejection_prevents_collective_approval_without_trimming_required_content(
    decision_inputs: DecisionInputs, approve_first: bool
) -> None:
    data = decision_inputs.decisions.model_dump(mode="json")
    data["bullets"][-1].update(decision="reject", reason="Needs correction before use.")
    if not approve_first:
        data["bullets"] = data["bullets"][-1:]
    decision_inputs.decisions = parse_review_decisions(json.dumps(data))
    result = decision_inputs.apply()
    assert result.status == "has_rejections"
    assert result.bullets[-1].review_status == "rejected_by_user"
    assert result.review.document == decision_inputs.draft
    assert result.review.plan.budget.bullet_slot_count == 2


def test_plan_conflicts_block_every_approval_and_keep_reasons_visible(
    decision_inputs: DecisionInputs,
) -> None:
    decision_inputs.profile.resume_preferences.min_bullets_per_entry = 1
    decision_inputs.reseed()
    result = decision_inputs.apply()
    assert result.status == "blocked_by_plan"
    assert all(b.review_status == "blocked_by_plan" for b in result.bullets)
    assert all(b.decision == "approve" and b.reason for b in result.bullets)
    assert result.rendering_authorized is False
    data = decision_inputs.decisions.model_dump(mode="json")
    data["bullets"][0]["decision"] = "reject"
    decision_inputs.decisions = parse_review_decisions(json.dumps(data))
    result = decision_inputs.apply()
    assert result.status == "blocked_by_plan"
    assert result.bullets[0].review_status == "rejected_by_user"


def test_no_bullets_is_not_vacuous_approval(decision_inputs: DecisionInputs) -> None:
    decision_inputs.profile.resume_preferences = ResumePreferences()
    decision_inputs.selection.entries = []
    decision_inputs.reseed()
    result = decision_inputs.apply()
    assert result.review.plan.constraint_status == "within_count_constraints"
    assert result.bullets == () and result.status == "needs_review"


@pytest.mark.parametrize(
    "change", ["wording", "bullet_id", "profile", "job", "requirements", "selection", "preferences"]
)
def test_old_decisions_cannot_transfer_to_changed_inputs(
    decision_inputs: DecisionInputs, change: str
) -> None:
    if change in ("wording", "bullet_id"):
        data = decision_inputs.draft.model_dump(mode="json")
        bullet = data["sections"][1]["entries"][0]["bullets"][0]
        bullet["text" if change == "wording" else "id"] = (
            "Changed wording." if change == "wording" else "bullet_changed"
        )
        decision_inputs.draft = parse_resume_document(json.dumps(data))
    elif change == "profile":
        decision_inputs.profile.accomplishments[0].statement += " More context."
    elif change == "job":
        decision_inputs.job = JobDocument(decision_inputs.job.text + "\nAdditional context.")
    elif change == "requirements":
        decision_inputs.requirements.company = None
    elif change == "selection":
        decision_inputs.selection.max_total_bullets = 4
    else:
        decision_inputs.profile.resume_preferences.max_bullets_per_entry = 2
    with pytest.raises(ResumeError, match=r"different (draft|plan) snapshot"):
        decision_inputs.apply()


@pytest.mark.parametrize("field", ["document_sha256", "plan_sha256"])
def test_each_explicit_binding_is_checked(decision_inputs: DecisionInputs, field: str) -> None:
    decision_inputs.decisions = decision_inputs.decisions.model_copy(update={field: "0" * 64})
    with pytest.raises(ResumeError, match="different draft snapshot"):
        decision_inputs.apply()


def test_inspection_policy_version_is_checked(
    decision_inputs: DecisionInputs, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("resumeforge.resume.engine.REVIEW_VERSION", "future-inspection-policy")
    with pytest.raises(ResumeError, match="different inspection policy"):
        decision_inputs.apply()


def test_unknown_decision_bullet_fails_without_disclosing_input_values(
    decision_inputs: DecisionInputs,
) -> None:
    data = decision_inputs.decisions.model_dump(mode="json")
    data["bullets"][0]["bullet_id"] = "bullet_private_unknown"
    decision_inputs.decisions = parse_review_decisions(json.dumps(data))
    with pytest.raises(ResumeError, match="absent") as error:
        decision_inputs.apply()
    assert "private_unknown" not in str(error.value)


def test_decision_order_does_not_change_draft_order_or_approval_scope(
    decision_inputs: DecisionInputs,
) -> None:
    original = decision_inputs.apply()
    decision_inputs.decisions = decision_inputs.decisions.model_copy(
        update={"bullets": tuple(reversed(decision_inputs.decisions.bullets))}
    )
    reversed_result = decision_inputs.apply()
    assert original.bullets == reversed_result.bullets
    assert original.review == reversed_result.review
    assert original.decisions_model_sha256 != reversed_result.decisions_model_sha256


def test_edited_wording_requires_new_explicit_attestation_not_an_inferred_semantic_verdict(
    decision_inputs: DecisionInputs,
) -> None:
    data = decision_inputs.draft.model_dump(mode="json")
    data["sections"][1]["entries"][0]["bullets"][0]["text"] = "Added tests under mentor review."
    decision_inputs.draft = parse_resume_document(json.dumps(data))
    review = review_resume(
        decision_inputs.profile,
        decision_inputs.job,
        decision_inputs.requirements,
        decision_inputs.selection,
        decision_inputs.draft,
        requirements_reviewed=True,
        selection_reviewed=True,
    )
    decision_inputs.decisions = decisions_for(review)
    result = decision_inputs.apply()
    assert result.review.bullets[0].wording_status == "edited_requires_review"
    assert result.bullets[0].review_status == "approved_by_user"
    assert "semantic proof" in result.warnings[0]
    assert (
        result.review.document.sections[1].entries[0].bullets[0].review_status == "pending_review"
    )


@pytest.mark.parametrize(
    "gate", ["requirements_reviewed", "selection_reviewed", "decisions_confirmed"]
)
@pytest.mark.parametrize("value", [False, None, 1, "true"])
def test_all_three_gates_require_exact_boolean_true_before_inspection(
    decision_inputs: DecisionInputs, gate: str, value: Any
) -> None:
    flags = {
        "requirements_reviewed": True,
        "selection_reviewed": True,
        "decisions_confirmed": True,
        gate: value,
    }
    with (
        patch(
            "resumeforge.resume.decisions.review_resume",
            side_effect=AssertionError("No inspection"),
        ),
        pytest.raises(ResumeError, match="Explicitly confirm"),
    ):
        apply_review_decisions(
            decision_inputs.profile,
            decision_inputs.job,
            decision_inputs.requirements,
            decision_inputs.selection,
            decision_inputs.draft,
            decision_inputs.decisions,
            **flags,
        )


def test_no_default_confirmation_and_no_implicit_seed_for_approvals(
    decision_inputs: DecisionInputs,
) -> None:
    with pytest.raises(ResumeError, match="Explicitly confirm"):
        apply_review_decisions(
            decision_inputs.profile,
            decision_inputs.job,
            decision_inputs.requirements,
            decision_inputs.selection,
            decision_inputs.draft,
            decision_inputs.decisions,
        )
    missing: Any = None
    with pytest.raises(ResumeError, match="explicit draft"):
        apply_review_decisions(
            decision_inputs.profile,
            decision_inputs.job,
            decision_inputs.requirements,
            decision_inputs.selection,
            missing,
            decision_inputs.decisions,
            requirements_reviewed=True,
            selection_reviewed=True,
            decisions_confirmed=True,
        )


def test_api_models_revalidate_and_remain_bounded(
    decision_inputs: DecisionInputs, monkeypatch: pytest.MonkeyPatch
) -> None:
    good = decision_inputs.decisions
    decision_inputs.decisions = good.model_copy(update={"bullets": "fictional-private-invalid"})
    with pytest.raises(ResumeError, match="Invalid review decisions") as error:
        decision_inputs.apply()
    assert "fictional-private" not in str(error.value)
    decision_inputs.decisions = good
    monkeypatch.setattr("resumeforge.resume.decisions.MAX_INPUT_BYTES", 1)
    with pytest.raises(ResumeError, match="byte limit"):
        decision_inputs.apply()


@pytest.mark.parametrize(
    "change",
    [
        "duplicate",
        "missing_reason",
        "blank_reason",
        "long_reason",
        "wrong_decision",
        "number_reason",
        "version_bool",
        "version_unknown",
        "review_policy",
        "bad_hash",
        "extra",
        "surrogate",
    ],
)
def test_invalid_decisions_are_safe_and_cannot_self_authorize(
    decision_inputs: DecisionInputs, change: str
) -> None:
    data = decision_inputs.decisions.model_dump(mode="json")
    if change == "duplicate":
        data["bullets"].append(data["bullets"][0])
    elif change == "missing_reason":
        data["bullets"][0].pop("reason")
    elif change in ("blank_reason", "long_reason", "number_reason", "surrogate"):
        data["bullets"][0]["reason"] = {
            "blank_reason": " ",
            "long_reason": "x" * 8193,
            "number_reason": 3,
            "surrogate": "\ud800",
        }[change]
    elif change == "wrong_decision":
        data["bullets"][0]["decision"] = "approve_all"
    elif change == "review_policy":
        data["review_version"] = "unknown-policy"
    elif change == "bad_hash":
        data["document_sha256"] = "not-a-hash"
    elif change == "extra":
        data["fictional-private-key"] = "fictional-private-value"
    else:
        data["schema_version"] = True if change == "version_bool" else 2
    with pytest.raises(ResumeError) as error:
        parse_review_decisions(json.dumps(data))
    assert "fictional-private" not in str(error.value)


@pytest.mark.parametrize(
    "text",
    [
        "fictional-private-invalid",
        '{"bullets":[],"bullets":[]}',
        '{"schema_version":NaN}',
        "[" * 40 + "0" + "]" * 40,
        "[" * 2000 + "0" + "]" * 2000,
        "1" * 5000,
        "\ud800",
        "x" * 1_048_577,
    ],
)
def test_malformed_decision_json_is_bounded_and_does_not_leak_values(text: str) -> None:
    with pytest.raises(ResumeError) as error:
        parse_review_decisions(text)
    assert "fictional-private" not in str(error.value)


def test_decision_loader_roundtrip_and_envelopes_are_not_decision_input(
    decision_inputs: DecisionInputs, tmp_path: Path
) -> None:
    path = tmp_path / "decisions.json"
    with pytest.raises(InputError):
        load_review_decisions(path)
    path.write_text("\ufeff" + decision_inputs.decisions.model_dump_json())
    assert load_review_decisions(path) == decision_inputs.decisions
    with pytest.raises(ResumeError, match="fields"):
        parse_review_decisions(decision_inputs.apply().model_dump_json())


@pytest.mark.parametrize("blocker", ["excluded", "unverified", "unfinished", "unknown_parent"])
def test_copied_current_hashes_cannot_reintroduce_old_ineligible_approved_bullets(
    decision_inputs: DecisionInputs, blocker: str
) -> None:
    prior = decision_inputs.decisions
    if blocker == "excluded":
        decision_inputs.profile.resume_preferences.required_entry_ids = []
        decision_inputs.profile.resume_preferences.required_sections.remove("experiences")
        decision_inputs.profile.resume_preferences.excluded_entry_ids.append("exp_example")
    elif blocker == "unverified":
        decision_inputs.profile.verified_bullets = []
        decision_inputs.profile.accomplishments[0].verified = False
    elif blocker == "unfinished":
        decision_inputs.profile.accomplishments[0].completion_status = "in_progress"
    else:
        decision_inputs.profile.experiences[0].completion_status = "unknown"
    decision_inputs.reseed()
    current = decision_inputs.decisions
    decision_inputs.decisions = prior
    with pytest.raises(ResumeError, match="different draft snapshot"):
        decision_inputs.apply()
    decision_inputs.decisions = prior.model_copy(
        update={
            "plan_sha256": current.plan_sha256,
            "document_sha256": current.document_sha256,
        }
    )
    with pytest.raises(ResumeError, match="absent"):
        decision_inputs.apply()
