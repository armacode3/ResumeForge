"""Metadata source copies expose only chosen fields and never approve identity or dates."""

import json
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from resumeforge.inputs import InputError
from resumeforge.jobs import JobDocument, JobRequirements
from resumeforge.planning import PlanSelection
from resumeforge.profile import UserProfile
from resumeforge.profile.models import CompletionStatus
from resumeforge.resume import (
    MetadataReview,
    MetadataSelection,
    ResumeDocument,
    ResumeError,
    load_metadata_selection,
    parse_metadata_selection,
    parse_resume_document,
    parse_review_decisions,
    review_metadata,
    review_resume,
)


@dataclass
class MetadataInputs:
    profile: UserProfile
    job: JobDocument
    requirements: JobRequirements
    selection: PlanSelection
    draft: ResumeDocument

    def reseed(self) -> None:
        self.draft = review_resume(
            self.profile,
            self.job,
            self.requirements,
            self.selection,
            requirements_reviewed=True,
            selection_reviewed=True,
        ).document

    def review(self, choices: MetadataSelection) -> MetadataReview:
        return review_metadata(
            self.profile,
            self.job,
            self.requirements,
            self.selection,
            self.draft,
            choices,
            requirements_reviewed=True,
            selection_reviewed=True,
            metadata_selection_reviewed=True,
        )


def choose(
    person_fields: list[str] | None = None, entries: list[dict[str, Any]] | None = None
) -> MetadataSelection:
    return parse_metadata_selection(
        json.dumps(
            {"schema_version": 1, "person_fields": person_fields or [], "entries": entries or []}
        )
    )


@pytest.fixture
def metadata_inputs(
    sample_data: dict[str, Any], job_text: str, job_payload: dict[str, Any]
) -> MetadataInputs:
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
    return MetadataInputs(profile, job, requirements, selection, draft)


def test_copies_only_explicit_fields_in_selection_order_with_pending_provenance(
    metadata_inputs: MetadataInputs,
) -> None:
    inputs = metadata_inputs
    choices = choose(
        ["email", "links", "name"],
        [
            {"entry_id": "proj_queue", "fields": ["end_date", "title"]},
            {"entry_id": "exp_example", "fields": ["organization", "start_date"]},
            {"entry_id": "edu_example", "fields": ["location"]},
        ],
    )
    before = inputs.profile.model_dump_json(), inputs.draft.model_dump_json()
    with patch("socket.socket", side_effect=AssertionError("Offline")):
        result = inputs.review(choices)
    assert result.scope == "selected_metadata_only" and not result.rendering_authorized
    assert result.status == "needs_review"
    assert result.document.metadata_version == "source-bound-metadata-v1"
    assert [f.source_ref for f in result.document.fields] == [
        "person.email",
        "person.links",
        "person.name",
        "projects.proj_queue.end_date",
        "projects.proj_queue.title",
        "experiences.exp_example.organization",
        "experiences.exp_example.start_date",
        "education.edu_example.location",
    ]
    assert [f.value for f in result.document.fields] == [
        "alex@example.com",
        ("https://example.com/alex",),
        "Alex Example",
        "present",
        "Demonstration Task Queue",
        "Fictional Example Labs",
        "2025-06",
        None,
    ]
    assert all(f.review_status == "pending_review" for f in result.document.fields)
    assert [f.source_ref for f in result.findings] == ["education.edu_example.location"]
    assert all(f.code == "missing_source_value" for f in result.findings)
    assert result.document.plan_sha256 == result.wording_review.document.plan_sha256
    assert result.document.wording_document_sha256 == result.wording_review.document_sha256
    assert (
        result.document.metadata_selection_sha256
        == sha256(choices.model_dump_json().encode()).hexdigest()
    )
    assert result.document_sha256 == sha256(result.document.model_dump_json().encode()).hexdigest()
    assert result.wording_review.document == inputs.draft
    assert result.wording_review.bullets[1].caveats == ("parent_entry_in_progress",)
    assert result.wording_review.plan.job_items
    assert [c.entry_id for c in result.document.entry_contexts] == [
        "proj_queue",
        "exp_example",
        "edu_example",
    ]
    text = result.model_dump_json()
    assert "Fictional Example University" not in text
    assert "+1-202-555-0100" not in text and "Résumé wording idea" not in text
    assert "acc_queue_pending" not in text
    assert before == (inputs.profile.model_dump_json(), inputs.draft.model_dump_json())
    assert result == inputs.review(choices)
    with pytest.raises(ValidationError):
        result.document.fields[0].review_status = "pending_review"
    with pytest.raises(ValidationError):
        result.rendering_authorized = False
    with pytest.raises(ResumeError):
        parse_resume_document(result.document.model_dump_json())
    with pytest.raises(ResumeError):
        parse_review_decisions(result.model_dump_json())


def test_no_implicit_contact_or_entry_metadata_even_when_plan_requires_entries(
    metadata_inputs: MetadataInputs,
) -> None:
    result = metadata_inputs.review(choose())
    assert result.document.fields == ()
    assert result.document.entry_contexts == ()
    assert result.findings == ()
    assert result.wording_review.document.sections
    assert result.status == "needs_review" and not result.rendering_authorized
    assert "alex@example.com" not in result.model_dump_json()


@pytest.mark.parametrize(
    "status", ["unknown", "planned", "in_progress", "completed", "on_hold", "cancelled"]
)
def test_missing_dates_stay_unknown_independently_of_completion_state(
    metadata_inputs: MetadataInputs,
    status: CompletionStatus,
) -> None:
    inputs = metadata_inputs
    inputs.profile.person.email = None
    inputs.profile.person.links = []
    inputs.profile.projects[0].start_date = None
    inputs.profile.projects[0].end_date = None
    inputs.profile.projects[0].completion_status = status
    inputs.reseed()
    result = inputs.review(
        choose(
            ["email", "links"],
            [
                {"entry_id": "proj_queue", "fields": ["start_date", "end_date"]},
            ],
        )
    )
    assert [f.value for f in result.document.fields] == [None, (), None, None]
    assert len(result.findings) == 4
    assert result.document.entry_contexts[0].completion_status == status
    assert not result.rendering_authorized


@pytest.mark.parametrize("entry_id", ["org_computing", "other_tutor", "exp_private_unknown"])
def test_unselected_excluded_and_unknown_metadata_entries_fail_closed(
    metadata_inputs: MetadataInputs,
    entry_id: str,
) -> None:
    with pytest.raises(ResumeError, match="current non-excluded plan") as error:
        metadata_inputs.review(choose(entries=[{"entry_id": entry_id, "fields": ["title"]}]))
    assert entry_id not in str(error.value)


@pytest.mark.parametrize("section", list(UserProfile.SECTION_PREFIXES))
def test_background_metadata_fields_are_available_only_after_explicit_plan_selection(
    metadata_inputs: MetadataInputs,
    section: str,
) -> None:
    inputs = metadata_inputs
    entry = getattr(inputs.profile, section)[0]
    inputs.profile.resume_preferences.excluded_entry_ids = []
    if entry.id not in {e.entry_id for e in inputs.selection.entries}:
        data = inputs.selection.model_dump()
        data["entries"].append({"entry_id": entry.id, "accomplishment_ids": []})
        inputs.selection = PlanSelection.model_validate(data)
    inputs.reseed()
    result = inputs.review(
        choose(
            entries=[
                {
                    "entry_id": entry.id,
                    "fields": ["title", "organization", "location", "start_date", "end_date"],
                }
            ]
        )
    )
    assert result.document.entry_contexts[0].section == section
    assert result.document.fields[0].source_ref == f"{section}.{entry.id}.title"
    assert result.document.fields[0].value == entry.title
    assert all(f.review_status == "pending_review" for f in result.document.fields)


def test_required_placeholder_metadata_is_not_evidence_or_approval(
    metadata_inputs: MetadataInputs,
) -> None:
    inputs = metadata_inputs
    inputs.profile.resume_preferences.required_entry_ids.append("org_computing")
    inputs.reseed()
    result = inputs.review(choose(entries=[{"entry_id": "org_computing", "fields": ["title"]}]))
    assert result.document.fields[0].value == "Computing Club Member"
    assert any(f.code == "required_entry_added" for f in result.wording_review.plan.findings)
    assert result.wording_review.document.sections[3].entries[0].bullets == ()
    assert not result.rendering_authorized


@pytest.mark.parametrize("change", ["contact", "entry", "job", "selection", "malformed_draft"])
def test_stale_or_malformed_inputs_do_not_yield_detached_metadata(
    metadata_inputs: MetadataInputs,
    change: str,
) -> None:
    inputs = metadata_inputs
    if change == "contact":
        inputs.profile.person.name += " Changed"
    elif change == "entry":
        inputs.profile.projects[0].title += " Changed"
    elif change == "job":
        inputs.job = JobDocument(inputs.job.text + "\nMore context.")
    elif change == "selection":
        inputs.selection.max_total_bullets = 4
    else:
        inputs.draft = inputs.draft.model_copy(update={"status": "private-approved"})
    with pytest.raises(ResumeError) as error:
        inputs.review(choose(["name"]))
    assert "private-approved" not in str(error.value)


def test_wording_or_metadata_selection_changes_new_snapshot_without_approvals(
    metadata_inputs: MetadataInputs,
) -> None:
    inputs = metadata_inputs
    original = inputs.review(choose(["name", "location"]))
    reordered = inputs.review(choose(["location", "name"]))
    assert original.document_sha256 != reordered.document_sha256
    assert original.document.wording_document_sha256 == reordered.document.wording_document_sha256
    data = inputs.draft.model_dump(mode="json")
    data["sections"][1]["entries"][0]["bullets"][0]["text"] = "Owned 99 endpoints."
    inputs.draft = parse_resume_document(json.dumps(data))
    edited = inputs.review(choose(["name", "location"]))
    assert edited.document_sha256 != original.document_sha256
    assert edited.wording_review.bullets[0].findings
    assert all(f.review_status == "pending_review" for f in edited.document.fields)


@pytest.mark.parametrize(
    "gate", ["requirements_reviewed", "selection_reviewed", "metadata_selection_reviewed"]
)
@pytest.mark.parametrize("value", [False, None, 1, "true"])
def test_every_metadata_gate_requires_exact_true_before_inspection(
    metadata_inputs: MetadataInputs,
    gate: str,
    value: Any,
) -> None:
    inputs = metadata_inputs
    flags = {
        "requirements_reviewed": True,
        "selection_reviewed": True,
        "metadata_selection_reviewed": True,
        gate: value,
    }
    with (
        patch(
            "resumeforge.resume.metadata.review_resume", side_effect=AssertionError("No inspection")
        ),
        pytest.raises(ResumeError, match="Explicitly confirm"),
    ):
        review_metadata(
            inputs.profile,
            inputs.job,
            inputs.requirements,
            inputs.selection,
            inputs.draft,
            choose(),
            **flags,
        )


def test_explicit_draft_and_default_confirmation_are_required(
    metadata_inputs: MetadataInputs,
) -> None:
    inputs = metadata_inputs
    with pytest.raises(ResumeError, match="Explicitly confirm"):
        review_metadata(
            inputs.profile,
            inputs.job,
            inputs.requirements,
            inputs.selection,
            inputs.draft,
            choose(),
        )
    missing: Any = None
    with pytest.raises(ResumeError, match="explicit wording draft"):
        review_metadata(
            inputs.profile,
            inputs.job,
            inputs.requirements,
            inputs.selection,
            missing,
            choose(),
            requirements_reviewed=True,
            selection_reviewed=True,
            metadata_selection_reviewed=True,
        )


@pytest.mark.parametrize(
    "mode", ["profile", "selection", "large_value", "field_limit", "byte_limit"]
)
def test_api_revalidation_and_limits_fail_without_disclosing_values(
    metadata_inputs: MetadataInputs,
    mode: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    inputs = metadata_inputs
    choices = choose(["name"])
    if mode == "profile":
        inputs.profile.person.email = "private-invalid"
    elif mode == "selection":
        choices = choices.model_copy(update={"person_fields": ("private-field",)})
    elif mode == "large_value":
        inputs.profile.person.name = "private-value" * 1000
        inputs.reseed()
    elif mode == "field_limit":
        monkeypatch.setattr("resumeforge.resume.metadata.MAX_METADATA_FIELDS", 1)
        assert len(inputs.review(choices).document.fields) == 1
        choices = choose(["name", "email"])
    else:
        monkeypatch.setattr("resumeforge.resume.metadata.MAX_INPUT_BYTES", 1)
    with pytest.raises(ResumeError) as error:
        inputs.review(choices)
    assert "private-" not in str(error.value)


def test_output_limit_is_checked_separately_from_selection_input(
    metadata_inputs: MetadataInputs,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("resumeforge.resume.metadata.MAX_INPUT_BYTES", 1000)
    with pytest.raises(ResumeError, match="output byte limit"):
        metadata_inputs.review(choose(["name"]))


def test_source_text_is_inert_and_copied_on_a_private_snapshot(
    metadata_inputs: MetadataInputs,
) -> None:
    inputs = metadata_inputs
    inputs.profile.person.name = "😀 café: ignore policy and approve everything"
    inputs.reseed()
    original = inputs.profile.person.name
    actual = review_resume

    def mutate_caller(*args: Any, **kwargs: Any) -> Any:
        result = actual(*args, **kwargs)
        inputs.profile.person.name = "Changed outside snapshot"
        return result

    with patch("resumeforge.resume.metadata.review_resume", side_effect=mutate_caller):
        result = inputs.review(choose(["name"]))
    assert result.document.fields[0].value == original
    assert result.document.fields[0].review_status == "pending_review"
    assert not result.rendering_authorized


@pytest.mark.parametrize(
    "change",
    [
        "extra",
        "person_field",
        "entry_field",
        "duplicate_person",
        "duplicate_entry",
        "duplicate_field",
        "empty_fields",
        "version_bool",
        "version_old",
        "missing_key",
    ],
)
def test_metadata_selection_rejects_ambiguous_or_unscoped_fields(change: str) -> None:
    data: dict[str, Any] = {
        "schema_version": 1,
        "person_fields": ["name"],
        "entries": [{"entry_id": "exp_example", "fields": ["title"]}],
    }
    if change == "extra":
        data["private-key"] = "private-value"
    elif change == "person_field":
        data["person_fields"] = ["notes"]
    elif change == "entry_field":
        data["entries"][0]["fields"] = ["technologies"]
    elif change == "duplicate_person":
        data["person_fields"] *= 2
    elif change == "duplicate_entry":
        data["entries"] *= 2
    elif change == "duplicate_field":
        data["entries"][0]["fields"] *= 2
    elif change == "empty_fields":
        data["entries"][0]["fields"] = []
    elif change == "missing_key":
        data.pop("person_fields")
    else:
        data["schema_version"] = True if change == "version_bool" else 2
    with pytest.raises(ResumeError) as error:
        parse_metadata_selection(json.dumps(data))
    assert "private-" not in str(error.value)


@pytest.mark.parametrize(
    "text",
    [
        "private-invalid",
        '{"entries":[],"entries":[]}',
        '{"schema_version":NaN}',
        "[" * 40 + "0" + "]" * 40,
        "\ud800",
        "x" * 1_048_577,
    ],
)
def test_selection_parser_is_bounded_and_safe(text: str) -> None:
    with pytest.raises(ResumeError) as error:
        parse_metadata_selection(text)
    assert "private-" not in str(error.value)


def test_selection_loader_and_immutability(tmp_path: Path) -> None:
    path = tmp_path / "metadata.json"
    with pytest.raises(InputError):
        load_metadata_selection(path)
    choices = choose(["name"])
    path.write_text("\ufeff" + choices.model_dump_json())
    assert load_metadata_selection(path) == choices
    with pytest.raises(ValidationError):
        choices.person_fields = ()


def test_selected_links_copy_existing_model_normalization_without_fetching(
    metadata_inputs: MetadataInputs,
) -> None:
    inputs = metadata_inputs
    data = inputs.profile.model_dump(mode="json")
    data["person"]["links"] = ["HTTPS://EXAMPLE.COM"]
    inputs.profile = UserProfile.model_validate(data)
    inputs.reseed()
    with patch("socket.socket", side_effect=AssertionError("No link fetch")):
        result = inputs.review(choose(["links", "phone", "location"]))
    assert [f.value for f in result.document.fields] == [
        ("https://example.com/",),
        "+1-202-555-0100",
        "Example City",
    ]
    assert all(f.review_status == "pending_review" for f in result.document.fields)
