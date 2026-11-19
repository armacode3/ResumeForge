"""Metadata attestations cannot approve missing values, wording, or a complete resume."""

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
    MetadataDecisionResult,
    MetadataDecisions,
    MetadataReview,
    MetadataSelection,
    ResumeDocument,
    ResumeError,
    apply_metadata_decisions,
    load_metadata_decisions,
    parse_metadata_decisions,
    parse_metadata_selection,
    parse_resume_document,
    review_metadata,
    review_resume,
)


def decisions_for(review: MetadataReview) -> MetadataDecisions:
    return parse_metadata_decisions(
        json.dumps(
            {
                "schema_version": 1,
                "decision_version": "metadata-field-decisions-v1",
                "metadata_version": review.document.metadata_version,
                "plan_sha256": review.document.plan_sha256,
                "wording_document_sha256": review.document.wording_document_sha256,
                "metadata_selection_sha256": review.document.metadata_selection_sha256,
                "metadata_document_sha256": review.document_sha256,
                "fields": [
                    {
                        "source_ref": f.source_ref,
                        "decision": "approve",
                        "reason": "Fictional user reviewed this source value and its context.",
                    }
                    for f in review.document.fields
                ],
            }
        )
    )


@dataclass
class MetadataDecisionInputs:
    profile: UserProfile
    job: JobDocument
    requirements: JobRequirements
    selection: PlanSelection
    draft: ResumeDocument
    metadata_selection: MetadataSelection
    decisions: MetadataDecisions

    def inspect(self) -> MetadataReview:
        return review_metadata(
            self.profile,
            self.job,
            self.requirements,
            self.selection,
            self.draft,
            self.metadata_selection,
            requirements_reviewed=True,
            selection_reviewed=True,
            metadata_selection_reviewed=True,
        )

    def reseed(self) -> None:
        self.draft = review_resume(
            self.profile,
            self.job,
            self.requirements,
            self.selection,
            requirements_reviewed=True,
            selection_reviewed=True,
        ).document
        self.decisions = decisions_for(self.inspect())

    def apply(self) -> MetadataDecisionResult:
        return apply_metadata_decisions(
            self.profile,
            self.job,
            self.requirements,
            self.selection,
            self.draft,
            self.metadata_selection,
            self.decisions,
            requirements_reviewed=True,
            selection_reviewed=True,
            metadata_selection_reviewed=True,
            decisions_confirmed=True,
        )


@pytest.fixture
def metadata_decision_inputs(
    sample_data: dict[str, Any], job_text: str, job_payload: dict[str, Any]
) -> MetadataDecisionInputs:
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
    fields = parse_metadata_selection(
        json.dumps(
            {
                "schema_version": 1,
                "person_fields": ["name", "links"],
                "entries": [
                    {"entry_id": "edu_example", "fields": ["title", "end_date"]},
                    {"entry_id": "proj_queue", "fields": ["end_date"]},
                ],
            }
        )
    )
    review = review_metadata(
        profile,
        job,
        requirements,
        selection,
        draft,
        fields,
        requirements_reviewed=True,
        selection_reviewed=True,
        metadata_selection_reviewed=True,
    )
    return MetadataDecisionInputs(
        profile, job, requirements, selection, draft, fields, decisions_for(review)
    )


def test_complete_attestations_are_narrow_and_preserve_pending_source_records(
    metadata_decision_inputs: MetadataDecisionInputs,
) -> None:
    inputs = metadata_decision_inputs
    before = inputs.profile.model_dump_json(), inputs.draft.model_dump_json()
    with patch("socket.socket", side_effect=AssertionError("Offline")):
        result = inputs.apply()
    assert result.decision_version == "metadata-field-decisions-v1"
    assert result.scope == "selected_metadata_only" and not result.rendering_authorized
    assert result.status == "metadata_fields_approved_by_user"
    assert all(f.review_status == "approved_by_user" for f in result.fields)
    assert all(not f.source_value_missing for f in result.fields)
    assert all(f.review_status == "pending_review" for f in result.review.document.fields)
    assert all(b.review_status == "pending_review" for b in result.review.wording_review.bullets)
    assert result.review.wording_review.document == inputs.draft
    assert result.review.document.fields[-1].value == "present"
    assert result.review.document.entry_contexts[-1].completion_status == "in_progress"
    assert before == (inputs.profile.model_dump_json(), inputs.draft.model_dump_json())
    assert len(result.decisions_model_sha256) == 64
    assert result == inputs.apply()
    with pytest.raises(ValidationError):
        result.rendering_authorized = False
    with pytest.raises(ResumeError):
        parse_metadata_decisions(result.model_dump_json())


@pytest.mark.parametrize("mode", ["none", "partial", "reject", "plan_conflict", "empty"])
def test_missing_rejected_conflicted_and_empty_metadata_never_pass_collectively(
    metadata_decision_inputs: MetadataDecisionInputs,
    mode: str,
) -> None:
    inputs = metadata_decision_inputs
    if mode == "plan_conflict":
        inputs.profile.resume_preferences.min_bullets_per_entry = 1
        inputs.reseed()
    if mode == "empty":
        inputs.metadata_selection = parse_metadata_selection(
            '{"schema_version":1,"person_fields":[],"entries":[]}'
        )
        inputs.decisions = decisions_for(inputs.inspect())
    data = inputs.decisions.model_dump(mode="json")
    if mode == "none":
        data["fields"] = []
    elif mode == "partial":
        data["fields"] = data["fields"][:1]
    elif mode == "reject":
        data["fields"][0]["decision"] = "reject"
    inputs.decisions = parse_metadata_decisions(json.dumps(data))
    result = inputs.apply()
    assert result.status == {"reject": "has_rejections", "plan_conflict": "blocked_by_plan"}.get(
        mode, "needs_review"
    )
    assert not result.rendering_authorized
    if mode in ("none", "partial"):
        assert result.fields[-1].decision is result.fields[-1].reason is None
        assert result.fields[-1].review_status == "pending_review"
    elif mode == "reject":
        assert result.fields[0].review_status == "rejected_by_user"
        assert result.review.document.fields[0].value == inputs.profile.person.name
    elif mode == "plan_conflict":
        assert all(f.review_status == "blocked_by_plan" for f in result.fields)
    else:
        assert result.fields == ()


@pytest.mark.parametrize("choice", ["approve", "reject", "missing", "plan_conflict"])
def test_unset_scalar_and_empty_links_are_never_approved_or_filled(
    metadata_decision_inputs: MetadataDecisionInputs,
    choice: str,
) -> None:
    inputs = metadata_decision_inputs
    inputs.profile.person.links = []
    inputs.profile.projects[0].end_date = None
    if choice == "plan_conflict":
        inputs.profile.resume_preferences.min_bullets_per_entry = 1
    inputs.reseed()
    data = inputs.decisions.model_dump(mode="json")
    if choice == "reject":
        for field in data["fields"]:
            field["decision"] = "reject"
    elif choice == "missing":
        data["fields"] = []
    inputs.decisions = parse_metadata_decisions(json.dumps(data))
    result = inputs.apply()
    unset = [f for f in result.fields if f.source_value_missing]
    assert len(unset) == 2
    assert all(
        f.review_status
        == {"reject": "rejected_by_user", "plan_conflict": "blocked_by_plan"}.get(
            choice, "pending_review"
        )
        for f in unset
    )
    assert result.review.document.fields[1].value == ()
    assert result.review.document.fields[-1].value is None
    assert result.review.document.entry_contexts[-1].completion_status == "in_progress"
    assert len(result.review.findings) == 2 and not result.rendering_authorized


@pytest.mark.parametrize(
    "binding",
    [
        "plan_sha256",
        "wording_document_sha256",
        "metadata_selection_sha256",
        "metadata_document_sha256",
    ],
)
def test_every_explicit_binding_is_checked(
    metadata_decision_inputs: MetadataDecisionInputs, binding: str
) -> None:
    inputs = metadata_decision_inputs
    inputs.decisions = inputs.decisions.model_copy(update={binding: "0" * 64})
    with pytest.raises(ResumeError, match="different metadata snapshot"):
        inputs.apply()


@pytest.mark.parametrize(
    "change",
    [
        "contact",
        "entry",
        "status",
        "job",
        "requirements",
        "preferences",
        "content_selection",
        "metadata_selection",
        "wording",
    ],
)
def test_attestations_do_not_transfer_to_changed_snapshots(
    metadata_decision_inputs: MetadataDecisionInputs,
    change: str,
) -> None:
    inputs = metadata_decision_inputs
    old = inputs.decisions
    if change == "contact":
        inputs.profile.person.name += " Changed"
    elif change == "entry":
        inputs.profile.education[0].title += " Changed"
    elif change == "status":
        inputs.profile.projects[0].completion_status = "completed"
    elif change == "job":
        inputs.job = JobDocument(inputs.job.text + "\nMore context.")
    elif change == "requirements":
        inputs.requirements.company = None
    elif change == "preferences":
        inputs.profile.resume_preferences.max_bullets_per_entry = 4
    elif change == "content_selection":
        inputs.selection.max_total_bullets = 4
    elif change == "metadata_selection":
        data = inputs.metadata_selection.model_dump(mode="json")
        data["person_fields"].reverse()
        inputs.metadata_selection = parse_metadata_selection(json.dumps(data))
    else:
        data = inputs.draft.model_dump(mode="json")
        data["sections"][1]["entries"][0]["bullets"][0]["text"] = "Owned 99 endpoints."
        inputs.draft = parse_resume_document(json.dumps(data))
    if change not in ("metadata_selection", "wording"):
        inputs.reseed()
    inputs.decisions = old
    with pytest.raises(ResumeError, match="different metadata snapshot"):
        inputs.apply()


def test_decision_order_does_not_reorder_source_records(
    metadata_decision_inputs: MetadataDecisionInputs,
) -> None:
    inputs = metadata_decision_inputs
    original = inputs.apply()
    inputs.decisions = inputs.decisions.model_copy(
        update={"fields": tuple(reversed(inputs.decisions.fields))}
    )
    reordered = inputs.apply()
    assert original.fields == reordered.fields and original.review == reordered.review
    assert original.decisions_model_sha256 != reordered.decisions_model_sha256


@pytest.mark.parametrize(
    "ref", ["person.email", "experiences.exp_private_unknown.title", "person.__class__"]
)
def test_unknown_unselected_and_unscoped_refs_fail_without_disclosure(
    metadata_decision_inputs: MetadataDecisionInputs,
    ref: str,
) -> None:
    inputs = metadata_decision_inputs
    data = inputs.decisions.model_dump(mode="json")
    data["fields"][0]["source_ref"] = ref
    inputs.decisions = parse_metadata_decisions(json.dumps(data))
    with pytest.raises(ResumeError, match="unselected metadata field") as error:
        inputs.apply()
    assert ref not in str(error.value)


@pytest.mark.parametrize(
    "gate",
    [
        "requirements_reviewed",
        "selection_reviewed",
        "metadata_selection_reviewed",
        "decisions_confirmed",
    ],
)
@pytest.mark.parametrize("value", [False, None, 1, "true"])
def test_exact_confirmation_precedes_inspection(
    metadata_decision_inputs: MetadataDecisionInputs,
    gate: str,
    value: Any,
) -> None:
    inputs = metadata_decision_inputs
    flags = {
        "requirements_reviewed": True,
        "selection_reviewed": True,
        "metadata_selection_reviewed": True,
        "decisions_confirmed": True,
        gate: value,
    }
    with (
        patch(
            "resumeforge.resume.metadata_decisions.review_metadata",
            side_effect=AssertionError("No inspection"),
        ),
        pytest.raises(ResumeError, match="Explicitly confirm"),
    ):
        apply_metadata_decisions(
            inputs.profile,
            inputs.job,
            inputs.requirements,
            inputs.selection,
            inputs.draft,
            inputs.metadata_selection,
            inputs.decisions,
            **flags,
        )


def test_no_default_confirmation_or_implicit_draft(
    metadata_decision_inputs: MetadataDecisionInputs,
) -> None:
    inputs = metadata_decision_inputs
    with pytest.raises(ResumeError, match="Explicitly confirm"):
        apply_metadata_decisions(
            inputs.profile,
            inputs.job,
            inputs.requirements,
            inputs.selection,
            inputs.draft,
            inputs.metadata_selection,
            inputs.decisions,
        )
    missing: Any = None
    with pytest.raises(ResumeError, match="explicit wording draft"):
        apply_metadata_decisions(
            inputs.profile,
            inputs.job,
            inputs.requirements,
            inputs.selection,
            missing,
            inputs.metadata_selection,
            inputs.decisions,
            requirements_reviewed=True,
            selection_reviewed=True,
            metadata_selection_reviewed=True,
            decisions_confirmed=True,
        )


@pytest.mark.parametrize(
    "mode",
    [
        "duplicate",
        "blank_reason",
        "missing_reason",
        "long_reason",
        "wrong_choice",
        "bool_version",
        "wrong_policy",
        "bad_metadata_version",
        "extra_value",
        "bad_hash",
        "missing_binding",
    ],
)
def test_invalid_metadata_decisions_are_safe(
    metadata_decision_inputs: MetadataDecisionInputs, mode: str
) -> None:
    data = metadata_decision_inputs.decisions.model_dump(mode="json")
    if mode == "duplicate":
        data["fields"].append(data["fields"][0])
    elif mode == "blank_reason":
        data["fields"][0]["reason"] = " \t"
    elif mode == "missing_reason":
        data["fields"][0].pop("reason")
    elif mode == "long_reason":
        data["fields"][0]["reason"] = "x" * 8193
    elif mode == "wrong_choice":
        data["fields"][0]["decision"] = "approve_all"
    elif mode == "bool_version":
        data["schema_version"] = True
    elif mode == "wrong_policy":
        data["decision_version"] = "private-policy"
    elif mode == "bad_metadata_version":
        data["metadata_version"] = "private-policy"
    elif mode == "extra_value":
        data["fields"][0]["value"] = "private-value"
    elif mode == "missing_binding":
        data.pop("metadata_document_sha256")
    else:
        data["metadata_document_sha256"] = "private-hash"
    with pytest.raises(ResumeError) as error:
        parse_metadata_decisions(json.dumps(data))
    assert "private-" not in str(error.value)


def test_api_and_output_limits_fail_without_partial_attestations(
    metadata_decision_inputs: MetadataDecisionInputs,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    inputs = metadata_decision_inputs
    original = inputs.decisions
    inputs.decisions = original.model_copy(update={"fields": "private-invalid"})
    with pytest.raises(ResumeError, match="Invalid metadata decisions"):
        inputs.apply()
    inputs.decisions = original
    monkeypatch.setattr("resumeforge.resume.metadata_decisions.MAX_INPUT_BYTES", 1)
    with pytest.raises(ResumeError, match="input byte limit"):
        inputs.apply()
    monkeypatch.setattr(
        "resumeforge.resume.metadata_decisions.MAX_INPUT_BYTES",
        len(original.model_dump_json().encode()),
    )
    with pytest.raises(ResumeError, match="output byte limit"):
        inputs.apply()


def test_future_decision_or_metadata_policy_invalidates_old_attestations(
    metadata_decision_inputs: MetadataDecisionInputs,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "resumeforge.resume.metadata_decisions.METADATA_DECISION_VERSION", "future-policy"
    )
    with pytest.raises(ResumeError, match="different metadata decision policy"):
        metadata_decision_inputs.apply()


def test_changed_metadata_policy_also_fails_even_with_copied_document_bindings(
    metadata_decision_inputs: MetadataDecisionInputs,
) -> None:
    inputs = metadata_decision_inputs
    review = inputs.inspect()
    future = review.model_copy(
        update={
            "document": review.document.model_copy(
                update={"metadata_version": "future-metadata-policy"}
            )
        }
    )
    with (
        patch("resumeforge.resume.metadata_decisions.review_metadata", return_value=future),
        pytest.raises(ResumeError, match="different metadata inspection policy"),
    ):
        inputs.apply()


def test_unknown_refs_still_fail_after_copying_current_bindings(
    metadata_decision_inputs: MetadataDecisionInputs,
) -> None:
    inputs = metadata_decision_inputs
    data = inputs.decisions.model_dump(mode="json")
    inputs.metadata_selection = parse_metadata_selection(
        '{"schema_version":1,"person_fields":["email"],"entries":[]}'
    )
    current = inputs.inspect()
    for binding, value in (
        ("plan_sha256", current.document.plan_sha256),
        ("wording_document_sha256", current.document.wording_document_sha256),
        ("metadata_selection_sha256", current.document.metadata_selection_sha256),
        ("metadata_document_sha256", current.document_sha256),
    ):
        data[binding] = value
    inputs.decisions = parse_metadata_decisions(json.dumps(data))
    with pytest.raises(ResumeError, match="unselected metadata field"):
        inputs.apply()


def test_rejection_is_preserved_but_plan_conflicts_dominate_collective_status(
    metadata_decision_inputs: MetadataDecisionInputs,
) -> None:
    inputs = metadata_decision_inputs
    inputs.profile.resume_preferences.min_bullets_per_entry = 1
    inputs.reseed()
    data = inputs.decisions.model_dump(mode="json")
    data["fields"][0]["decision"] = "reject"
    inputs.decisions = parse_metadata_decisions(json.dumps(data))
    result = inputs.apply()
    assert result.status == "blocked_by_plan"
    assert result.fields[0].review_status == "rejected_by_user"
    assert all(f.review_status == "blocked_by_plan" for f in result.fields[1:])


def test_excessive_decision_records_fail_before_source_inspection(
    metadata_decision_inputs: MetadataDecisionInputs,
) -> None:
    data = metadata_decision_inputs.decisions.model_dump(mode="json")
    data["fields"] = [
        {"source_ref": f"private-ref-{i}", "decision": "approve", "reason": "Fictional assertion."}
        for i in range(513)
    ]
    with pytest.raises(ResumeError) as error:
        parse_metadata_decisions(json.dumps(data))
    assert "private-ref" not in str(error.value)


@pytest.mark.parametrize(
    "text",
    [
        "private-invalid",
        '{"fields":[],"fields":[]}',
        '{"schema_version":NaN}',
        "[" * 40 + "0" + "]" * 40,
        "\ud800",
        "x" * 1_048_577,
    ],
)
def test_malformed_json_is_bounded_and_safe(text: str) -> None:
    with pytest.raises(ResumeError) as error:
        parse_metadata_decisions(text)
    assert "private-" not in str(error.value)


def test_decision_loader_and_wrong_envelopes_are_rejected(
    metadata_decision_inputs: MetadataDecisionInputs,
    tmp_path: Path,
) -> None:
    path = tmp_path / "decisions.json"
    with pytest.raises(InputError):
        load_metadata_decisions(path)
    choices = metadata_decision_inputs.decisions
    path.write_text("\ufeff" + choices.model_dump_json())
    assert load_metadata_decisions(path) == choices
    with pytest.raises(ResumeError):
        parse_metadata_decisions(metadata_decision_inputs.inspect().model_dump_json())
