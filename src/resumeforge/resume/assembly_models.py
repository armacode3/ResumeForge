"""Output-only structured content and finite readiness, never rendering authority."""

from typing import Annotated, Literal

from pydantic import Field

from resumeforge.profile.models import CompletionStatus, EntryId, ResumeSection
from resumeforge.resume.metadata_models import (
    AppliedMetadataDecision,
    MetadataField,
    MetadataReview,
)
from resumeforge.resume.models import AppliedBulletDecision, Digest, ResumeBullet, ResumeModel

IssueCode = Literal[
    "plan_conflict",
    "no_entries",
    "no_bullets",
    "empty_section",
    "unscoped_section_unresolved",
    "required_entry_not_explicitly_selected",
    "entry_status_unresolved",
    "required_field_unselected",
    "selected_field_missing",
    "bullet_decision_pending",
    "bullet_decision_rejected",
    "bullet_decision_blocked",
    "metadata_decision_pending",
    "metadata_decision_rejected",
    "metadata_decision_blocked",
]


class StructuredEntry(ResumeModel):
    entry_id: EntryId
    completion_status: CompletionStatus
    metadata: tuple[MetadataField, ...]
    bullets: tuple[ResumeBullet, ...]


class StructuredSection(ResumeModel):
    section: ResumeSection
    required: bool
    entries: tuple[StructuredEntry, ...]


class StructuredResume(ResumeModel):
    schema_version: Annotated[int, Field(ge=1, le=1)]
    assembly_version: Literal["structured-resume-assembly-v1"] = "structured-resume-assembly-v1"
    status: Literal["needs_review"] = "needs_review"
    plan_sha256: Digest
    wording_document_sha256: Digest
    metadata_selection_sha256: Digest
    metadata_document_sha256: Digest
    header: tuple[MetadataField, ...]
    sections: tuple[StructuredSection, ...]


class AssemblyIssue(ResumeModel):
    code: IssueCode
    section: ResumeSection | None = None
    entry_id: str | None = None
    bullet_id: str | None = None
    source_ref: str | None = None
    plan_finding_code: str | None = None


class BulletAttestations(ResumeModel):
    decision_version: str
    scope: Literal["bullet_wording_only"] = "bullet_wording_only"
    rendering_authorized: Literal[False] = False
    status: str
    decisions_model_sha256: Digest
    bullets: tuple[AppliedBulletDecision, ...]
    warnings: tuple[str, ...]


class MetadataAttestations(ResumeModel):
    decision_version: str
    scope: Literal["selected_metadata_only"] = "selected_metadata_only"
    rendering_authorized: Literal[False] = False
    status: str
    decisions_model_sha256: Digest
    fields: tuple[AppliedMetadataDecision, ...]
    warnings: tuple[str, ...]


class AssemblyResult(ResumeModel):
    readiness_version: Literal["structured-resume-readiness-v1"] = "structured-resume-readiness-v1"
    scope: Literal["structured_components_only"] = "structured_components_only"
    rendering_authorized: Literal[False] = False
    status: Literal["blocked_by_plan", "needs_review", "components_reviewed"]
    document_sha256: Digest
    document: StructuredResume
    review: MetadataReview
    bullet_attestations: BulletAttestations | None
    metadata_attestations: MetadataAttestations | None
    issues: tuple[AssemblyIssue, ...]
    warnings: tuple[str, ...]
