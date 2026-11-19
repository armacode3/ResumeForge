"""Partial selections and component attestations cannot authorize publication."""

import json
from dataclasses import dataclass
from hashlib import sha256
from typing import Any
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from resumeforge.jobs import JobDocument, JobRequirements
from resumeforge.planning import PlanSelection
from resumeforge.profile import UserProfile
from resumeforge.resume import (
    AssemblyResult,
    MetadataDecisions,
    MetadataReview,
    MetadataSelection,
    ResumeDocument,
    ResumeError,
    ReviewDecisions,
    assemble_resume,
    parse_metadata_decisions,
    parse_resume_document,
    parse_review_decisions,
    review_metadata,
    review_resume,
)


def bullet_choices(review: MetadataReview) -> ReviewDecisions:
    wording = review.wording_review
    return parse_review_decisions(
        json.dumps(
            {
                "schema_version": 3,
                "review_version": wording.review_version,
                "plan_sha256": wording.document.plan_sha256,
                "document_sha256": wording.document_sha256,
                "findings_sha256": wording.findings_sha256,
                "fragments_sha256": wording.fragments_sha256,
                "bullets": [
                    {
                        "bullet_id": b.bullet_id,
                        "decision": "approve",
                        "reason": "Synthetic reviewed wording, not factual proof.",
                        "acknowledged_finding_ids": [f.id for f in b.findings],
                        "fragment_decisions": [
                            {
                                "fragment_id": f.id,
                                "disposition": "omission_accepted",
                                "reason": "Synthetic gate assertion only.",
                                "draft_span": None,
                            }
                            for f in b.source_fragments
                        ],
                    }
                    for b in wording.bullets
                ],
            }
        )
    )


def metadata_choices(review: MetadataReview) -> MetadataDecisions:
    document = review.document
    return parse_metadata_decisions(
        json.dumps(
            {
                "schema_version": 1,
                "decision_version": "metadata-field-decisions-v1",
                "metadata_version": document.metadata_version,
                "plan_sha256": document.plan_sha256,
                "wording_document_sha256": document.wording_document_sha256,
                "metadata_selection_sha256": document.metadata_selection_sha256,
                "metadata_document_sha256": review.document_sha256,
                "fields": [
                    {
                        "source_ref": f.source_ref,
                        "decision": "approve",
                        "reason": "Synthetic reviewed value, not identity proof.",
                    }
                    for f in document.fields
                ],
            }
        )
    )


@dataclass
class AssemblyInputs:
    profile: UserProfile
    job: JobDocument
    requirements: JobRequirements
    selection: PlanSelection
    draft: ResumeDocument
    fields: MetadataSelection

    def reseed(self) -> None:
        self.draft = review_resume(
            self.profile,
            self.job,
            self.requirements,
            self.selection,
            requirements_reviewed=True,
            selection_reviewed=True,
        ).document

    def inspect(self) -> MetadataReview:
        return review_metadata(
            self.profile,
            self.job,
            self.requirements,
            self.selection,
            self.draft,
            self.fields,
            requirements_reviewed=True,
            selection_reviewed=True,
            metadata_selection_reviewed=True,
        )

    def assemble(self, **kwargs: Any) -> AssemblyResult:
        flags = {
            "requirements_reviewed": True,
            "selection_reviewed": True,
            "metadata_selection_reviewed": True,
            **kwargs,
        }
        return assemble_resume(
            self.profile,
            self.job,
            self.requirements,
            self.selection,
            self.draft,
            self.fields,
            **flags,
        )

    def approved(self, **kwargs: Any) -> AssemblyResult:
        review = self.inspect()
        flags = {
            "bullet_decisions": bullet_choices(review),
            "metadata_decisions": metadata_choices(review),
            "bullet_decisions_confirmed": True,
            "metadata_decisions_confirmed": True,
            **kwargs,
        }
        return self.assemble(**flags)


@pytest.fixture
def assembly_inputs(
    sample_data: dict[str, Any], job_text: str, job_payload: dict[str, Any]
) -> AssemblyInputs:
    sample_data["resume_preferences"]["min_bullets_per_entry"] = 0
    profile = UserProfile.model_validate(sample_data)
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
    job = JobDocument(job_text)
    requirements = JobRequirements.model_validate(job_payload)
    draft = review_resume(
        profile, job, requirements, selection, requirements_reviewed=True, selection_reviewed=True
    ).document
    fields = MetadataSelection.model_validate(
        {
            "schema_version": 1,
            "person_fields": ("name",),
            "entries": tuple(
                {"entry_id": e.entry_id, "fields": ("title",)} for e in selection.entries
            ),
        }
    )
    return AssemblyInputs(profile, job, requirements, selection, draft, fields)


def test_no_decisions_means_exact_pending_content_not_an_approval(
    assembly_inputs: AssemblyInputs,
) -> None:
    inputs = assembly_inputs
    original = inputs.profile.model_dump_json(), inputs.draft.model_dump_json()
    with patch("socket.socket", side_effect=AssertionError("Offline")):
        result = inputs.assemble()
    assert result.status == "needs_review"
    assert result.bullet_attestations is None
    assert result.metadata_attestations is None
    assert [f.value for f in result.document.header] == ["Alex Example"]
    assert [s.section for s in result.document.sections] == [
        s.section for s in inputs.draft.sections
    ]
    for actual, expected in zip(result.document.sections, inputs.draft.sections, strict=True):
        assert [e.entry_id for e in actual.entries] == [e.entry_id for e in expected.entries]
        assert [e.bullets for e in actual.entries] == [e.bullets for e in expected.entries]
    assert {issue.code for issue in result.issues} == {
        "bullet_decision_pending",
        "metadata_decision_pending",
    }
    assert result.scope == "structured_components_only" and not result.rendering_authorized
    assert "alex@example.com" not in result.model_dump_json()
    assert "+1-202-555-0100" not in result.model_dump_json()
    assert original == (inputs.profile.model_dump_json(), inputs.draft.model_dump_json())
    assert result == inputs.assemble()
    assert result.document_sha256 == sha256(result.document.model_dump_json().encode()).hexdigest()


def test_complete_attestations_are_separate_and_never_rendering_authority(
    assembly_inputs: AssemblyInputs,
) -> None:
    result = assembly_inputs.approved()
    assert result.status == "components_reviewed" and result.issues == ()
    assert result.document.status == "needs_review" and not result.rendering_authorized
    assert result.bullet_attestations is not None and result.metadata_attestations is not None
    assert result.bullet_attestations.scope == "bullet_wording_only"
    assert result.metadata_attestations.scope == "selected_metadata_only"
    assert all(
        b.review_status == "pending_review"
        for s in result.document.sections
        for e in s.entries
        for b in e.bullets
    )
    assert all(f.review_status == "pending_review" for f in result.review.document.fields)
    assert result.document.sections[-1].entries[0].completion_status == "in_progress"
    assert result.review.wording_review.bullets[-1].caveats == ("parent_entry_in_progress",)
    with pytest.raises(ValidationError):
        result.status = "components_reviewed"
    with pytest.raises(ResumeError):
        parse_resume_document(result.document.model_dump_json())
    with pytest.raises(ResumeError):
        parse_resume_document(result.model_dump_json())


@pytest.mark.parametrize("kind", ["bullet", "metadata"])
@pytest.mark.parametrize("choice", ["partial", "reject", "empty"])
def test_partial_or_rejected_attestations_keep_all_content(
    assembly_inputs: AssemblyInputs, kind: str, choice: str
) -> None:
    inputs = assembly_inputs
    review = inputs.inspect()
    kwargs: dict[str, Any] = {}
    if kind == "bullet":
        data = bullet_choices(review).model_dump(mode="json")
        key = "bullets"
    else:
        data = metadata_choices(review).model_dump(mode="json")
        key = "fields"
    if choice == "reject":
        data[key][0]["decision"] = "reject"
    else:
        data[key] = data[key][:1] if choice == "partial" else []
    kwargs[kind + "_decisions"] = (
        parse_review_decisions(json.dumps(data))
        if kind == "bullet"
        else parse_metadata_decisions(json.dumps(data))
    )
    result = inputs.approved(**kwargs)
    assert result.status == "needs_review"
    assert result.document == inputs.approved().document
    assert result.document_sha256 == inputs.approved().document_sha256
    assert any(
        i.code == kind + "_decision_" + ("rejected" if choice == "reject" else "pending")
        for i in result.issues
    )


@pytest.mark.parametrize("kind", ["bullet", "metadata"])
def test_one_scope_cannot_approve_the_other(assembly_inputs: AssemblyInputs, kind: str) -> None:
    review = assembly_inputs.inspect()
    kwargs: dict[str, Any] = {
        kind + "_decisions": bullet_choices(review)
        if kind == "bullet"
        else metadata_choices(review),
        kind + "_decisions_confirmed": True,
    }
    result = assembly_inputs.assemble(**kwargs)
    assert result.status == "needs_review"
    other = "metadata" if kind == "bullet" else "bullet"
    assert all(issue.code == other + "_decision_pending" for issue in result.issues)


@pytest.mark.parametrize("missing", ["name", "title", "scalar", "links"])
def test_unselected_required_and_missing_selected_fields_are_explicit_without_inference(
    assembly_inputs: AssemblyInputs, missing: str
) -> None:
    inputs = assembly_inputs
    data = inputs.fields.model_dump()
    if missing == "name":
        data["person_fields"] = ()
    elif missing == "title":
        data["entries"] = data["entries"][1:]
    elif missing == "scalar":
        inputs.profile.projects[0].end_date = None
        data["entries"][-1]["fields"] = ("title", "end_date")
        inputs.reseed()
    else:
        inputs.profile.person.links = []
        data["person_fields"] = ("name", "links")
        inputs.reseed()
    inputs.fields = MetadataSelection.model_validate(data)
    result = inputs.approved()
    assert result.status == "needs_review"
    issue = (
        "required_field_unselected" if missing in ("name", "title") else "selected_field_missing"
    )
    assert any(i.code == issue for i in result.issues)
    if missing == "name":
        assert result.document.header == ()
        assert "Alex Example" not in result.model_dump_json()
    elif missing == "title":
        assert result.document.sections[0].entries[0].metadata == ()
        assert inputs.profile.education[0].title not in result.model_dump_json()
    else:
        assert result.review.findings


@pytest.mark.parametrize("section", ["skills", "coursework"])
@pytest.mark.parametrize("required", [False, True])
def test_unscoped_sections_remain_placeholders_even_with_approved_components(
    assembly_inputs: AssemblyInputs, section: str, required: bool
) -> None:
    inputs = assembly_inputs
    if required:
        data = inputs.profile.model_dump()
        data["resume_preferences"]["required_sections"].append(section)
        inputs.profile = UserProfile.model_validate(data)
    else:
        inputs.selection = inputs.selection.model_copy(update={"include_sections": [section]})
    inputs.reseed()
    result = inputs.approved()
    assert result.status == "needs_review"
    assert result.document.sections[-1].section == section
    assert result.document.sections[-1].entries == ()
    assert any(
        i.code == "unscoped_section_unresolved" and i.section == section for i in result.issues
    )
    assert (
        "Technical writing" not in result.model_dump_json()
        and "Data Structures" not in result.model_dump_json()
    )


def test_conflicts_dominate_and_approvals_do_not_hide_required_placeholders(
    assembly_inputs: AssemblyInputs,
) -> None:
    inputs = assembly_inputs
    inputs.profile.resume_preferences.min_bullets_per_entry = 1
    inputs.reseed()
    result = inputs.approved()
    assert result.status == "blocked_by_plan"
    assert any(
        i.code == "plan_conflict" and i.plan_finding_code == "entry_bullet_minimum_not_met"
        for i in result.issues
    )
    assert any(i.code == "bullet_decision_blocked" for i in result.issues)
    assert any(i.code == "metadata_decision_blocked" for i in result.issues)
    assert result.document.sections[0].entries[0].entry_id == "edu_example"
    assert result.document.sections[0].entries[0].bullets == ()


def test_required_entry_added_is_not_an_explicit_selection(assembly_inputs: AssemblyInputs) -> None:
    inputs = assembly_inputs
    inputs.selection.entries = [e for e in inputs.selection.entries if e.entry_id != "exp_example"]
    inputs.reseed()
    result = inputs.approved()
    assert any(
        i.code == "required_entry_not_explicitly_selected" and i.entry_id == "exp_example"
        for i in result.issues
    )
    assert result.status == "needs_review"


@pytest.mark.parametrize("status", ["unknown", "planned", "on_hold", "cancelled"])
def test_unresolved_metadata_only_entry_states_are_not_inferred_from_dates(
    assembly_inputs: AssemblyInputs, status: str
) -> None:
    inputs = assembly_inputs
    inputs.profile.education[0] = inputs.profile.education[0].model_copy(
        update={"completion_status": status}
    )
    inputs.reseed()
    result = inputs.approved()
    assert any(
        i.code == "entry_status_unresolved" and i.entry_id == "edu_example" for i in result.issues
    )
    assert result.document.sections[0].entries[0].completion_status == status


@pytest.mark.parametrize("mode", ["empty", "no_bullets", "empty_required_section"])
def test_empty_content_cannot_pass_by_vacuity(assembly_inputs: AssemblyInputs, mode: str) -> None:
    inputs = assembly_inputs
    inputs.profile.resume_preferences.required_entry_ids = []
    inputs.profile.resume_preferences.min_projects = 0
    inputs.profile.resume_preferences.required_sections = (
        ["education"] if mode == "empty_required_section" else []
    )
    inputs.selection.entries = [] if mode != "no_bullets" else inputs.selection.entries[:1]
    data = inputs.fields.model_dump()
    data["entries"] = () if mode != "no_bullets" else data["entries"][:1]
    inputs.fields = MetadataSelection.model_validate(data)
    inputs.reseed()
    result = inputs.approved()
    codes = {i.code for i in result.issues}
    assert "no_bullets" in codes and result.status != "components_reviewed"
    if mode != "no_bullets":
        assert "no_entries" in codes
    if mode == "empty_required_section":
        assert "empty_section" in codes and "plan_conflict" in codes


@pytest.mark.parametrize(
    "gate", ["requirements_reviewed", "selection_reviewed", "metadata_selection_reviewed"]
)
@pytest.mark.parametrize("value", [False, None, 1, "true"])
def test_review_gates_precede_any_inspection(
    assembly_inputs: AssemblyInputs, gate: str, value: Any
) -> None:
    with (
        patch(
            "resumeforge.resume.assembly.review_metadata",
            side_effect=AssertionError("No inspection"),
        ),
        pytest.raises(ResumeError, match="Explicitly confirm"),
    ):
        assembly_inputs.assemble(**{gate: value})


@pytest.mark.parametrize("kind", ["bullet", "metadata"])
@pytest.mark.parametrize(
    "mode",
    ["file_without_flag", "flag_without_file", "integer_true", "integer_false", "null_false"],
)
def test_decision_confirmations_are_independent_and_exact(
    assembly_inputs: AssemblyInputs, kind: str, mode: str
) -> None:
    kwargs: dict[str, Any] = {
        kind + "_decisions_confirmed": {
            "file_without_flag": False,
            "flag_without_file": True,
            "integer_true": 1,
            "integer_false": 0,
            "null_false": None,
        }[mode]
    }
    if mode in ("file_without_flag", "integer_true"):
        review = assembly_inputs.inspect()
        kwargs[kind + "_decisions"] = (
            bullet_choices(review) if kind == "bullet" else metadata_choices(review)
        )
    with (
        patch(
            "resumeforge.resume.assembly.review_metadata",
            side_effect=AssertionError("No inspection"),
        ),
        pytest.raises(ResumeError, match="own exact confirmation"),
    ):
        assembly_inputs.assemble(**kwargs)


def test_no_default_review_or_implicit_draft(assembly_inputs: AssemblyInputs) -> None:
    inputs = assembly_inputs
    with pytest.raises(ResumeError, match="Explicitly confirm"):
        assemble_resume(
            inputs.profile,
            inputs.job,
            inputs.requirements,
            inputs.selection,
            inputs.draft,
            inputs.fields,
        )
    inputs.draft = None  # type: ignore[assignment]
    with pytest.raises(ResumeError, match="explicit wording draft"):
        inputs.assemble()


@pytest.mark.parametrize("kind", ["bullet", "metadata"])
def test_stale_decisions_fail_without_partial_report(
    assembly_inputs: AssemblyInputs, kind: str
) -> None:
    review = assembly_inputs.inspect()
    choices = bullet_choices(review) if kind == "bullet" else metadata_choices(review)
    choices = choices.model_copy(update={"plan_sha256": "0" * 64})
    with pytest.raises(ResumeError, match="different"):
        assembly_inputs.approved(**{kind + "_decisions": choices})


@pytest.mark.parametrize("missing", ["findings", "fragments", "revision"])
def test_assembly_cannot_bypass_wording_review_gates(
    assembly_inputs: AssemblyInputs, missing: str
) -> None:
    inputs = assembly_inputs
    draft = inputs.draft.model_dump(mode="json")
    draft["sections"][1]["entries"][0]["bullets"][0]["text"] = "Owned 99 endpoints."
    inputs.draft = parse_resume_document(json.dumps(draft))
    choices = bullet_choices(inputs.inspect()).model_dump(mode="json")
    if missing == "findings":
        choices["bullets"][0]["acknowledged_finding_ids"] = []
    elif missing == "fragments":
        choices["bullets"][0]["fragment_decisions"] = []
    else:
        choices["bullets"][0]["fragment_decisions"][0]["disposition"] = "needs_revision"
    result = inputs.approved(bullet_decisions=parse_review_decisions(json.dumps(choices)))
    assert result.status == "needs_review"
    assert any(i.code == "bullet_decision_pending" for i in result.issues)
    assert result.review.wording_review.bullets[0].findings
    assert result.review.wording_review.bullets[0].source_fragments
    complete = inputs.approved()
    assert complete.status == "components_reviewed" and not complete.rendering_authorized
    assert (
        complete.review.wording_review.bullets[0].findings
        == result.review.wording_review.bullets[0].findings
    )


def test_output_is_bounded_without_truncation(
    assembly_inputs: AssemblyInputs, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("resumeforge.resume.assembly.MAX_INPUT_BYTES", 1)
    with pytest.raises(ResumeError, match="output byte limit"):
        assembly_inputs.assemble()


def test_metadata_selection_order_cannot_reorder_planned_entries_or_wording(
    assembly_inputs: AssemblyInputs,
) -> None:
    inputs = assembly_inputs
    data = inputs.fields.model_dump()
    data["person_fields"] = ("links", "name")
    data["entries"] = tuple(reversed(data["entries"]))
    data["entries"][0]["fields"] = ("end_date", "title")
    inputs.fields = MetadataSelection.model_validate(data)
    result = inputs.approved()
    assert result.status == "components_reviewed"
    assert [f.source_ref for f in result.document.header] == ["person.links", "person.name"]
    assert result.document.header[0].value == ("https://example.com/alex",)
    assert [s.section for s in result.document.sections] == ["education", "experiences", "projects"]
    assert [f.source_ref for f in result.document.sections[-1].entries[0].metadata] == [
        "projects.proj_queue.end_date",
        "projects.proj_queue.title",
    ]
    assert result.document.sections[-1].entries[0].metadata[0].value == "present"
    assert result.review.wording_review.document == inputs.draft


@pytest.mark.parametrize("ref", ["other_tutor", "org_computing", "private_unknown"])
def test_unselected_excluded_or_unknown_metadata_cannot_enter_assembly(
    assembly_inputs: AssemblyInputs,
    ref: str,
) -> None:
    inputs = assembly_inputs
    prefix = "other_" if ref == "other_tutor" else "org_" if ref == "org_computing" else "exp_"
    entry_id = ref if ref in ("other_tutor", "org_computing") else prefix + ref
    data = inputs.fields.model_dump()
    data["entries"] += ({"entry_id": entry_id, "fields": ("title",)},)
    inputs.fields = MetadataSelection.model_validate(data)
    with pytest.raises(ResumeError, match="current non-excluded plan") as error:
        inputs.assemble()
    assert ref not in str(error.value)


def test_invalid_api_selection_and_draft_cannot_self_approve(
    assembly_inputs: AssemblyInputs,
) -> None:
    inputs = assembly_inputs
    inputs.fields = inputs.fields.model_copy(update={"person_fields": ("private_invalid",)})
    with pytest.raises(ResumeError, match="Invalid metadata inputs"):
        inputs.assemble()
    inputs.fields = MetadataSelection(schema_version=1, person_fields=(), entries=())
    inputs.draft = inputs.draft.model_copy(update={"status": "approved"})
    with pytest.raises(ResumeError, match="Invalid draft"):
        inputs.assemble()


@pytest.mark.parametrize("kind", ["bullet", "metadata"])
def test_inconsistent_recomputed_reviews_fail_closed(
    assembly_inputs: AssemblyInputs, kind: str
) -> None:
    from resumeforge.resume import apply_metadata_decisions, apply_review_decisions

    inputs = assembly_inputs
    review = inputs.inspect()
    if kind == "bullet":
        applied = apply_review_decisions(
            inputs.profile,
            inputs.job,
            inputs.requirements,
            inputs.selection,
            inputs.draft,
            bullet_choices(review),
            requirements_reviewed=True,
            selection_reviewed=True,
            decisions_confirmed=True,
        )
        changed: Any = applied.model_copy(
            update={"review": applied.review.model_copy(update={"warnings": ()})}
        )
    else:
        applied_metadata = apply_metadata_decisions(
            inputs.profile,
            inputs.job,
            inputs.requirements,
            inputs.selection,
            inputs.draft,
            inputs.fields,
            metadata_choices(review),
            requirements_reviewed=True,
            selection_reviewed=True,
            metadata_selection_reviewed=True,
            decisions_confirmed=True,
        )
        changed = applied_metadata.model_copy(
            update={"review": applied_metadata.review.model_copy(update={"warnings": ()})}
        )
    target = "apply_review_decisions" if kind == "bullet" else "apply_metadata_decisions"
    with (
        patch("resumeforge.resume.assembly." + target, return_value=changed),
        pytest.raises(ResumeError, match="changed during review"),
    ):
        inputs.approved()
