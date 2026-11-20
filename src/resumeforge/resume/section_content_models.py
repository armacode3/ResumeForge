"""Explicit source selections and pending skill/coursework review, never proficiency proof."""

from typing import Annotated, Literal, Self

from pydantic import Field, model_validator

from resumeforge.profile.models import AccomplishmentId, CompletionStatus, ResumeSection
from resumeforge.resume.models import Digest, DraftText, ResumeModel, ResumeReview

SkillCategory = Literal["languages", "frameworks", "libraries", "tools", "platforms", "other"]
ContentSection = Literal["skills", "coursework"]


class SourceItemSelection(ResumeModel):
    source_index: Annotated[int, Field(ge=0)]
    expected_text: DraftText
    accomplishment_ids: Annotated[tuple[AccomplishmentId, ...], Field(max_length=32)]

    @model_validator(mode="after")
    def distinct_references(self) -> Self:
        if len(set(self.accomplishment_ids)) != len(self.accomplishment_ids):
            raise ValueError("Cited accomplishments must be distinct within an item.")
        return self


class SkillSelection(SourceItemSelection):
    category: SkillCategory


class SectionContentSelection(ResumeModel):
    schema_version: Annotated[int, Field(ge=1, le=1)]
    skills: Annotated[tuple[SkillSelection, ...], Field(max_length=512)]
    coursework: Annotated[tuple[SourceItemSelection, ...], Field(max_length=512)]

    @model_validator(mode="after")
    def bounded_distinct_items(self) -> Self:
        if len(self.skills) + len(self.coursework) > 512:
            raise ValueError("Select at most 512 section content items.")
        skill_refs = [(item.category, item.source_index) for item in self.skills]
        course_refs = [item.source_index for item in self.coursework]
        if len(set(skill_refs)) != len(skill_refs) or len(set(course_refs)) != len(course_refs):
            raise ValueError("Each source item may be selected only once.")
        if sum(len(item.accomplishment_ids) for item in (*self.skills, *self.coursework)) > 512:
            raise ValueError("Select at most 512 total accomplishment links.")
        return self


class CitedContentContext(ResumeModel):
    accomplishment_id: str
    entry_id: str
    section: ResumeSection
    source_statement: DraftText
    entry_completion_status: CompletionStatus
    caveats: tuple[str, ...]
    literal_label_mention: str | None


class SectionContentItem(ResumeModel):
    source_ref: str
    text: DraftText
    cited_context: tuple[CitedContentContext, ...]
    review_status: Literal["pending_review"] = "pending_review"
    # Questions are prompts to inspect original sources, not fabricated answers or approvals.
    review_questions: tuple[str, ...]


class SectionContentSection(ResumeModel):
    section: ContentSection
    required: bool
    items: tuple[SectionContentItem, ...]


class SectionContentDocument(ResumeModel):
    schema_version: Literal[1] = 1
    section_content_version: Literal["source-bound-section-content-v1"] = (
        "source-bound-section-content-v1"
    )
    plan_sha256: Digest
    wording_document_sha256: Digest
    content_selection_sha256: Digest
    sections: tuple[SectionContentSection, ...]


class SectionContentFinding(ResumeModel):
    code: Literal[
        "no_selected_items",
        "section_without_selected_items",
        "no_cited_accomplishments",
        "label_not_literal_in_cited_statement",
        "skill_usage_requires_user_review",
        "coursework_context_requires_user_review",
    ]
    section: ContentSection | None = None
    source_ref: str | None = None
    accomplishment_id: str | None = None


class SectionContentReview(ResumeModel):
    scope: Literal["selected_section_content_only"] = "selected_section_content_only"
    rendering_authorized: Literal[False] = False
    status: Literal["needs_review", "blocked_by_plan"]
    document_sha256: Digest
    document: SectionContentDocument
    findings: tuple[SectionContentFinding, ...]
    wording_review: ResumeReview
    warnings: tuple[str, ...]
