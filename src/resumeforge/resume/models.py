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


class ReviewSpan(ResumeModel):
    """Zero-based, end-exclusive Python string offsets in an unchanged text."""

    start: Annotated[int, Field(ge=0)]
    end: Annotated[int, Field(gt=0)]
    text: str


class ClaimFinding(ResumeModel):
    id: Digest
    code: Literal["numeric_token_absent_from_source", "source_caveat_cue_not_retained"]
    cue: str | None
    source_span: ReviewSpan | None
    draft_span: ReviewSpan | None


class BulletReview(ResumeModel):
    bullet_id: str
    entry_id: str
    accomplishment_id: str
    source_statement: str
    wording_status: Literal["verbatim_source", "edited_requires_review"]
    review_status: Literal["pending_review"] = "pending_review"
    caveats: tuple[str, ...]
    findings: tuple[ClaimFinding, ...]


class ResumeReview(ResumeModel):
    review_version: str
    findings_version: str
    findings_sha256: Digest
    mode: Literal["source_seed", "submitted_draft"]
    status: Literal["needs_review", "blocked_by_plan"]
    document_sha256: Digest
    document: ResumeDocument
    # The plan keeps complete job context, required placeholders, statuses and conflicts.
    plan: ResumePlan
    bullets: tuple[BulletReview, ...]
    warnings: tuple[str, ...]


class BulletDecision(ResumeModel):
    bullet_id: BulletId
    decision: Literal["approve", "reject"]
    reason: DraftText
    acknowledged_finding_ids: tuple[Digest, ...]

    @model_validator(mode="after")
    def distinct_acknowledgements(self) -> Self:
        if len(set(self.acknowledged_finding_ids)) != len(self.acknowledged_finding_ids):
            raise ValueError("Finding acknowledgements must be distinct.")
        return self


class ReviewDecisions(ResumeModel):
    """Local user attestations, not signed proof of identity, truth or semantic support."""

    schema_version: Annotated[int, Field(ge=2, le=2)]
    review_version: Literal["resume-draft-review-v2"]
    plan_sha256: Digest
    document_sha256: Digest
    findings_sha256: Digest
    bullets: tuple[BulletDecision, ...]

    @model_validator(mode="after")
    def distinct_bullets(self) -> Self:
        if len({bullet.bullet_id for bullet in self.bullets}) != len(self.bullets):
            raise ValueError("Each bullet may have only one review decision.")
        return self


class AppliedBulletDecision(ResumeModel):
    bullet_id: str
    accomplishment_id: str
    decision: Literal["approve", "reject"] | None
    reason: str | None
    acknowledged_finding_ids: tuple[Digest, ...]
    unacknowledged_finding_ids: tuple[Digest, ...]
    review_status: Literal[
        "pending_review", "approved_by_user", "rejected_by_user", "blocked_by_plan"
    ]


class ReviewDecisionResult(ResumeModel):
    decision_version: str
    scope: Literal["bullet_wording_only"] = "bullet_wording_only"
    rendering_authorized: Literal[False] = False
    status: Literal[
        "blocked_by_plan", "has_rejections", "needs_review", "bullet_wording_approved_by_user"
    ]
    decisions_model_sha256: Digest
    review: ResumeReview
    bullets: tuple[AppliedBulletDecision, ...]
    warnings: tuple[str, ...]
