"""Recorded labels and explicit source contexts cannot establish skill proficiency or attendance."""

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
from resumeforge.resume import (
    ResumeDocument,
    ResumeError,
    SectionContentReview,
    SectionContentSelection,
    load_section_content_selection,
    parse_resume_document,
    parse_section_content_selection,
    review_resume,
    review_section_content,
)


@dataclass
class ContentInputs:
    profile: UserProfile
    job: JobDocument
    requirements: JobRequirements
    selection: PlanSelection
    draft: ResumeDocument
    content: SectionContentSelection

    def reseed(self) -> None:
        self.draft = review_resume(
            self.profile,
            self.job,
            self.requirements,
            self.selection,
            requirements_reviewed=True,
            selection_reviewed=True,
        ).document

    def review(self, **kwargs: Any) -> SectionContentReview:
        flags = {
            "requirements_reviewed": True,
            "selection_reviewed": True,
            "content_selection_reviewed": True,
            **kwargs,
        }
        return review_section_content(
            self.profile,
            self.job,
            self.requirements,
            self.selection,
            self.draft,
            self.content,
            **flags,
        )


@pytest.fixture
def content_inputs(
    sample_data: dict[str, Any], job_text: str, job_payload: dict[str, Any]
) -> ContentInputs:
    sample_data["resume_preferences"]["min_bullets_per_entry"] = 0
    sample_data["skills"]["frameworks"] = ["private-unselected-framework"]
    profile = UserProfile.model_validate(sample_data)
    selection = PlanSelection.model_validate(
        {
            "schema_version": 1,
            "entries": [
                {"entry_id": "edu_example", "accomplishment_ids": []},
                {"entry_id": "exp_example", "accomplishment_ids": ["acc_api"]},
                {"entry_id": "proj_queue", "accomplishment_ids": ["acc_queue"]},
            ],
            "include_sections": ["skills", "coursework"],
        }
    )
    job = JobDocument(job_text)
    requirements = JobRequirements.model_validate(job_payload)
    draft = review_resume(
        profile, job, requirements, selection, requirements_reviewed=True, selection_reviewed=True
    ).document
    content = parse_section_content_selection(
        json.dumps(
            {
                "schema_version": 1,
                "skills": [
                    {
                        "category": "languages",
                        "source_index": 0,
                        "expected_text": "Python",
                        "accomplishment_ids": ["acc_api"],
                    },
                    {
                        "category": "tools",
                        "source_index": 0,
                        "expected_text": "Git",
                        "accomplishment_ids": [],
                    },
                ],
                "coursework": [
                    {
                        "source_index": 1,
                        "expected_text": "Databases",
                        "accomplishment_ids": ["acc_queue"],
                    }
                ],
            }
        )
    )
    return ContentInputs(profile, job, requirements, selection, draft, content)


def test_exact_selected_labels_and_contexts_remain_pending_private_and_immutable(
    content_inputs: ContentInputs,
) -> None:
    inputs = content_inputs
    before = inputs.profile.model_dump_json(), inputs.draft.model_dump_json()
    with patch("socket.socket", side_effect=AssertionError("Offline")):
        result = inputs.review()
    assert result.status == "needs_review"
    assert result.scope == "selected_section_content_only" and not result.rendering_authorized
    assert result.document.section_content_version == "source-bound-section-content-v1"
    skills, coursework = result.document.sections
    assert skills.section == "skills" and coursework.section == "coursework"
    assert [item.text for item in skills.items] == ["Python", "Git"]
    assert [item.source_ref for item in skills.items] == ["skills.languages.0", "skills.tools.0"]
    assert (
        coursework.items[0].source_ref == "coursework.1" and coursework.items[0].text == "Databases"
    )
    context = skills.items[0].cited_context[0]
    assert context.source_statement == inputs.profile.accomplishments[0].statement
    assert context.entry_id == "exp_example" and context.section == "experiences"
    assert context.entry_completion_status == "completed" and context.literal_label_mention is None
    assert coursework.items[0].cited_context[0].caveats == ("parent_entry_in_progress",)
    assert coursework.items[0].cited_context[0].entry_completion_status == "in_progress"
    assert skills.items[1].cited_context == ()
    assert all(
        item.review_status == "pending_review" and len(item.review_questions) == 2
        for section in result.document.sections
        for item in section.items
    )
    assert "have not used it" in skills.items[0].review_questions[0]
    assert "completed, current, planned or uncertain" in coursework.items[0].review_questions[0]
    assert result.wording_review.document == inputs.draft
    assert before == (inputs.profile.model_dump_json(), inputs.draft.model_dump_json())
    assert result == inputs.review()
    assert result.document_sha256 == sha256(result.document.model_dump_json().encode()).hexdigest()
    assert (
        result.document.content_selection_sha256
        == sha256(inputs.content.model_dump_json().encode()).hexdigest()
    )
    serialized = result.model_dump_json()
    for private in (
        "alex@example.com",
        "Alex Example",
        "Technical writing",
        "Data Structures",
        "private-unselected-framework",
        "+1-202-555-0100",
        "Rough notes:",
    ):
        assert private not in serialized
    with pytest.raises(ValidationError):
        skills.items[0].review_status = "pending_review"
    with pytest.raises(ResumeError):
        parse_section_content_selection(serialized)
    with pytest.raises(ResumeError):
        parse_resume_document(result.document.model_dump_json())


@pytest.mark.parametrize(
    "category", ["languages", "frameworks", "libraries", "tools", "platforms", "other"]
)
def test_all_categories_use_only_their_exact_recorded_source_list(
    content_inputs: ContentInputs, category: str
) -> None:
    inputs = content_inputs
    value = getattr(inputs.profile.skills, category)[0]
    inputs.content = parse_section_content_selection(
        json.dumps(
            {
                "schema_version": 1,
                "skills": [
                    {
                        "category": category,
                        "source_index": 0,
                        "expected_text": value,
                        "accomplishment_ids": [],
                    }
                ],
                "coursework": [],
            }
        )
    )
    result = inputs.review()
    assert result.document.sections[0].items[0].text == value
    assert result.document.sections[0].items[0].source_ref == f"skills.{category}.0"
    assert any(f.code == "no_cited_accomplishments" for f in result.findings)


@pytest.mark.parametrize(
    "statement, mention",
    [
        ("Used PYTHON under a mentor's review.", "PYTHON"),
        ("Did not use Python for this prototype.", "Python"),
        ("Only discussed Python; did not implement the service.", "Python"),
        ("Used CPython for a test.", None),
    ],
)
def test_mentions_are_literal_observations_not_positive_support(
    content_inputs: ContentInputs, statement: str, mention: str | None
) -> None:
    inputs = content_inputs
    inputs.profile.accomplishments[0].statement = statement
    inputs.reseed()
    result = inputs.review()
    item = result.document.sections[0].items[0]
    assert item.cited_context[0].literal_label_mention == mention
    assert item.review_status == "pending_review"
    assert any(
        f.code == "skill_usage_requires_user_review" and f.source_ref == item.source_ref
        for f in result.findings
    )
    absent = [
        f
        for f in result.findings
        if f.code == "label_not_literal_in_cited_statement" and f.source_ref == item.source_ref
    ]
    assert bool(absent) == (mention is None)


def test_selection_and_context_order_are_explicit_without_reordering_the_plan(
    content_inputs: ContentInputs,
) -> None:
    inputs = content_inputs
    data = inputs.content.model_dump(mode="json")
    data["skills"].reverse()
    data["skills"][1]["accomplishment_ids"] = ["acc_queue", "acc_api"]
    inputs.content = parse_section_content_selection(json.dumps(data))
    result = inputs.review()
    assert [item.text for item in result.document.sections[0].items] == ["Git", "Python"]
    assert [
        context.accomplishment_id for context in result.document.sections[0].items[1].cited_context
    ] == ["acc_queue", "acc_api"]
    assert result.wording_review.document == inputs.draft


@pytest.mark.parametrize("mode", ["no_sections", "empty", "required", "conflict"])
def test_empty_and_required_sections_keep_unknown_content_and_conflicts(
    content_inputs: ContentInputs, mode: str
) -> None:
    inputs = content_inputs
    inputs.content = parse_section_content_selection(
        '{"schema_version":1,"skills":[],"coursework":[]}'
    )
    if mode == "no_sections":
        inputs.selection.include_sections = []
    elif mode == "required":
        inputs.profile.resume_preferences.required_sections += ["skills", "coursework"]
        inputs.selection.include_sections = []
    elif mode == "conflict":
        inputs.profile.resume_preferences.min_bullets_per_entry = 1
    inputs.reseed()
    result = inputs.review()
    assert result.status == ("blocked_by_plan" if mode == "conflict" else "needs_review")
    assert any(f.code == "no_selected_items" for f in result.findings)
    assert all(s.items == () for s in result.document.sections)
    assert len(result.document.sections) == (0 if mode == "no_sections" else 2)
    if mode == "required":
        assert all(s.required for s in result.document.sections)
    elif mode == "conflict":
        assert result.wording_review.plan.constraint_status == "conflicts"


@pytest.mark.parametrize("section", ["skills", "coursework"])
def test_selected_content_cannot_create_a_section_not_in_the_plan(
    content_inputs: ContentInputs, section: str
) -> None:
    inputs = content_inputs
    inputs.selection.include_sections = ["coursework"] if section == "skills" else ["skills"]
    inputs.reseed()
    with pytest.raises(ResumeError, match="already belong to the current plan"):
        inputs.review()


@pytest.mark.parametrize(
    "change",
    ["index", "label", "category", "case", "course_index", "course_label", "reordered_source"],
)
def test_positions_and_exact_labels_must_match_current_sources(
    content_inputs: ContentInputs, change: str
) -> None:
    inputs = content_inputs
    data = inputs.content.model_dump(mode="json")
    if change == "index":
        data["skills"][0]["source_index"] = 100
    elif change == "label":
        data["skills"][0]["expected_text"] = "private-false-skill"
    elif change == "category":
        data["skills"][0]["category"] = "frameworks"
    elif change == "case":
        data["skills"][0]["expected_text"] = "python"
    elif change == "course_index":
        data["coursework"][0]["source_index"] = 100
    elif change == "course_label":
        data["coursework"][0]["expected_text"] = "private-false-course"
    else:
        inputs.profile.skills.languages.reverse()
        inputs.reseed()
    inputs.content = parse_section_content_selection(json.dumps(data))
    with pytest.raises(ResumeError, match="current source positions and text") as error:
        inputs.review()
    assert "private-" not in str(error.value)


@pytest.mark.parametrize(
    "reference", ["acc_queue_pending", "acc_private_unknown", "acc_unselected", "acc_excluded"]
)
def test_only_eligible_currently_selected_accomplishments_can_be_cited(
    content_inputs: ContentInputs, reference: str
) -> None:
    inputs = content_inputs
    if reference in ("acc_unselected", "acc_excluded"):
        record = inputs.profile.accomplishments[0].model_copy(
            update={
                "id": reference,
                "entry_id": "other_tutor" if reference == "acc_excluded" else "exp_example",
            }
        )
        inputs.profile.accomplishments.append(record)
        inputs.reseed()
    data = inputs.content.model_dump(mode="json")
    data["skills"][0]["accomplishment_ids"] = [reference]
    inputs.content = parse_section_content_selection(json.dumps(data))
    with pytest.raises(ResumeError, match="eligible accomplishments selected") as error:
        inputs.review()
    assert reference not in str(error.value)


@pytest.mark.parametrize(
    "change", ["profile", "job", "requirements", "selection", "wording_structure"]
)
def test_stale_or_detached_drafts_fail_before_exposure(
    content_inputs: ContentInputs, change: str
) -> None:
    inputs = content_inputs
    if change == "profile":
        inputs.profile.person.name = "private-new-name"
    elif change == "job":
        inputs.job = JobDocument(inputs.job.text + "\nMore context.")
    elif change == "requirements":
        inputs.requirements.company = None
    elif change == "selection":
        inputs.selection.max_total_bullets = 3
    else:
        inputs.draft = inputs.draft.model_copy(update={"sections": ()})
    with pytest.raises(ResumeError, match=r"snapshot|sections") as error:
        inputs.review()
    assert "private-new-name" not in str(error.value)


@pytest.mark.parametrize(
    "gate", ["requirements_reviewed", "selection_reviewed", "content_selection_reviewed"]
)
@pytest.mark.parametrize("value", [False, None, 1, "true"])
def test_exact_review_gates_precede_inspection(
    content_inputs: ContentInputs, gate: str, value: Any
) -> None:
    with (
        patch(
            "resumeforge.resume.section_content.review_resume",
            side_effect=AssertionError("No inspection"),
        ),
        pytest.raises(ResumeError, match="Explicitly confirm"),
    ):
        content_inputs.review(**{gate: value})


def test_no_default_confirmation_or_implicit_draft(content_inputs: ContentInputs) -> None:
    inputs = content_inputs
    with pytest.raises(ResumeError, match="Explicitly confirm"):
        review_section_content(
            inputs.profile,
            inputs.job,
            inputs.requirements,
            inputs.selection,
            inputs.draft,
            inputs.content,
        )
    inputs.draft = None  # type: ignore[assignment]
    with pytest.raises(ResumeError, match="explicit wording draft"):
        inputs.review()


@pytest.mark.parametrize(
    "mode",
    [
        "bool_schema",
        "bool_index",
        "negative",
        "extra",
        "blank_label",
        "long_label",
        "duplicate_item",
        "duplicate_course",
        "duplicate_evidence",
        "too_many_links",
        "bad_category",
        "bad_reference",
        "self_verified",
        "replacement_context",
    ],
)
def test_strict_selection_rejects_invalid_or_self_approving_fields(
    content_inputs: ContentInputs, mode: str
) -> None:
    data = content_inputs.content.model_dump(mode="json")
    item = data["skills"][0]
    if mode == "bool_schema":
        data["schema_version"] = True
    elif mode == "bool_index":
        item["source_index"] = False
    elif mode == "negative":
        item["source_index"] = -1
    elif mode == "extra":
        data["private-unknown"] = "private-value"
    elif mode == "blank_label":
        item["expected_text"] = " \t"
    elif mode == "long_label":
        item["expected_text"] = "x" * 8193
    elif mode == "duplicate_item":
        data["skills"].append(item)
    elif mode == "duplicate_course":
        data["coursework"] *= 2
    elif mode == "duplicate_evidence":
        item["accomplishment_ids"] *= 2
    elif mode == "too_many_links":
        item["accomplishment_ids"] = [f"acc_{i}" for i in range(33)]
    elif mode == "bad_category":
        item["category"] = "__class__"
    elif mode == "bad_reference":
        item["accomplishment_ids"] = ["private-path"]
    elif mode == "self_verified":
        item["verified"] = True
    else:
        item["source_statement"] = "private-invented"
    with pytest.raises(ResumeError) as error:
        parse_section_content_selection(json.dumps(data))
    assert "private-" not in str(error.value)


@pytest.mark.parametrize("mode", ["items", "links", "array_length"])
def test_combined_item_and_link_limits_are_independent(
    content_inputs: ContentInputs, mode: str
) -> None:
    data = content_inputs.content.model_dump(mode="json")
    if mode == "items":
        data["skills"] = [
            {
                "category": "languages",
                "source_index": i,
                "expected_text": "Python",
                "accomplishment_ids": [],
            }
            for i in range(512)
        ]
        data["coursework"] = [
            {"source_index": 0, "expected_text": "Course", "accomplishment_ids": []}
        ]
    elif mode == "links":
        data["skills"] = [
            {
                "category": "languages",
                "source_index": i,
                "expected_text": "Python",
                "accomplishment_ids": [f"acc_{j}" for j in range(32)],
            }
            for i in range(17)
        ]
        data["coursework"] = []
    else:
        data["skills"] = [
            {
                "category": "languages",
                "source_index": i,
                "expected_text": "Python",
                "accomplishment_ids": [],
            }
            for i in range(513)
        ]
    with pytest.raises(ResumeError):
        parse_section_content_selection(json.dumps(data))


def test_api_revalidation_and_size_limits_fail_without_partial_output(
    content_inputs: ContentInputs, monkeypatch: pytest.MonkeyPatch
) -> None:
    inputs = content_inputs
    original = inputs.content
    inputs.content = original.model_copy(update={"skills": "private-invalid"})
    with pytest.raises(ResumeError, match="Invalid section content inputs"):
        inputs.review()
    inputs.content = original
    monkeypatch.setattr("resumeforge.resume.section_content.MAX_INPUT_BYTES", 1)
    with pytest.raises(ResumeError, match="input byte limit"):
        inputs.review()
    monkeypatch.setattr(
        "resumeforge.resume.section_content.MAX_INPUT_BYTES",
        len(original.model_dump_json().encode()),
    )
    with pytest.raises(ResumeError, match="output byte limit"):
        inputs.review()


def test_invalid_output_source_values_fail_safely(content_inputs: ContentInputs) -> None:
    with (
        patch(
            "resumeforge.resume.section_content.SectionContentItem",
            side_effect=ValueError("private-value"),
        ),
        pytest.raises(ResumeError, match="source values") as error,
    ):
        content_inputs.review()
    assert "private-value" not in str(error.value)


@pytest.mark.parametrize(
    "text",
    [
        "private-invalid",
        '{"skills":[],"skills":[]}',
        '{"schema_version":NaN}',
        "[" * 40 + "0" + "]" * 40,
        "\ud800",
        "x" * 1_048_577,
    ],
)
def test_malformed_selection_is_bounded_and_safe(text: str) -> None:
    with pytest.raises(ResumeError) as error:
        parse_section_content_selection(text)
    assert "private-" not in str(error.value)


def test_selection_loader_accepts_bom_and_no_implicit_file(
    content_inputs: ContentInputs, tmp_path: Path
) -> None:
    path = tmp_path / "content.json"
    with pytest.raises(InputError):
        load_section_content_selection(path)
    path.write_text("\ufeff" + content_inputs.content.model_dump_json())
    assert load_section_content_selection(path) == content_inputs.content
