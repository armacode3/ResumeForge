"""Strict evidence-linked wording drafts; no input can declare itself approved."""

from typing import Annotated, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

from resumeforge.planning.models import ResumePlan
from resumeforge.profile.models import AccomplishmentId, BulletId, EntryId, ResumeSection

Digest = Annotated[str, StringConstraints(pattern=r"^[a-f0-9]{64}$")]
DraftText = Annotated[str, StringConstraints(min_length=1, max_length=8192, pattern=r"\S")]


class ResumeError(ValueError):
    """Static, safe failure of draft structure, source identity or plan alignment."""


class ResumeModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        strict=True,
        frozen=True,
        hide_input_in_errors=True,
        revalidate_instances="always",
    )


class ResumeBullet(ResumeModel):
    id: BulletId
    accomplishment_id: AccomplishmentId
    text: DraftText
    review_status: Literal["pending_review"] = "pending_review"


class ResumeEntry(ResumeModel):
    entry_id: EntryId
    bullets: tuple[ResumeBullet, ...]


class ResumeSectionDraft(ResumeModel):
    section: ResumeSection
    entries: tuple[ResumeEntry, ...]


class ResumeDocument(ResumeModel):
    schema_version: Annotated[int, Field(ge=1, le=1)]
    plan_sha256: Digest
    status: Literal["needs_review"] = "needs_review"
    sections: tuple[ResumeSectionDraft, ...]

    @model_validator(mode="after")
    def distinct_references(self) -> Self:
        sections = [section.section for section in self.sections]
        entries = [entry.entry_id for section in self.sections for entry in section.entries]
        bullets = [
            bullet
            for section in self.sections
            for entry in section.entries
            for bullet in entry.bullets
        ]
        identifiers = [bullet.id for bullet in bullets]
        references = [bullet.accomplishment_id for bullet in bullets]
        if any(
            len(values) != len(set(values))
            for values in (sections, entries, identifiers, references)
        ):
            raise ValueError(
                "Draft sections, entries, bullet IDs and evidence references must be distinct."
            )
        return self


class BulletReview(ResumeModel):
    bullet_id: str
    entry_id: str
    accomplishment_id: str
    source_statement: str
    wording_status: Literal["verbatim_source", "edited_requires_review"]
    review_status: Literal["pending_review"] = "pending_review"
    caveats: tuple[str, ...]


class ResumeReview(ResumeModel):
    review_version: str
    mode: Literal["source_seed", "submitted_draft"]
    status: Literal["needs_review", "blocked_by_plan"]
    document_sha256: Digest
    document: ResumeDocument
    # The plan keeps complete job context, required placeholders, statuses and conflicts.
    plan: ResumePlan
    bullets: tuple[BulletReview, ...]
    warnings: tuple[str, ...]
