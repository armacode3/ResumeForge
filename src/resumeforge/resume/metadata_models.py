"""Explicit metadata exposure and pending source copies, not approved resume content."""

from typing import Annotated, Literal, Self

from pydantic import Field, model_validator

from resumeforge.profile.models import CompletionStatus, EntryId, ResumeSection, Text
from resumeforge.resume.models import Digest, DraftText, ResumeModel, ResumeReview

PersonMetadataField = Literal["name", "email", "phone", "location", "links"]
EntryMetadataField = Literal["title", "organization", "location", "start_date", "end_date"]


class EntryMetadataSelection(ResumeModel):
    entry_id: EntryId
    fields: Annotated[tuple[EntryMetadataField, ...], Field(min_length=1)]

    @model_validator(mode="after")
    def distinct_fields(self) -> Self:
        if len(set(self.fields)) != len(self.fields):
            raise ValueError("Metadata entry fields must be distinct.")
        return self


class MetadataSelection(ResumeModel):
    schema_version: Annotated[int, Field(ge=1, le=1)]
    person_fields: tuple[PersonMetadataField, ...]
    entries: tuple[EntryMetadataSelection, ...]

    @model_validator(mode="after")
    def distinct_selections(self) -> Self:
        if len(set(self.person_fields)) != len(self.person_fields):
            raise ValueError("Person metadata fields must be distinct.")
        if len({entry.entry_id for entry in self.entries}) != len(self.entries):
            raise ValueError("Metadata entries must be distinct.")
        return self


class MetadataField(ResumeModel):
    # Logical model reference, not a raw-Markdown offset or an executable path expression.
    source_ref: str
    value: DraftText | tuple[DraftText, ...] | None
    review_status: Literal["pending_review"] = "pending_review"


class MetadataEntryContext(ResumeModel):
    entry_id: EntryId
    section: ResumeSection
    completion_status: CompletionStatus


class MetadataDocument(ResumeModel):
    schema_version: Annotated[int, Field(ge=1, le=1)]
    metadata_version: Literal["source-bound-metadata-v1"] = "source-bound-metadata-v1"
    plan_sha256: Digest
    wording_document_sha256: Digest
    metadata_selection_sha256: Digest
    fields: tuple[MetadataField, ...]
    entry_contexts: tuple[MetadataEntryContext, ...]


class MetadataFinding(ResumeModel):
    code: Literal["missing_source_value"] = "missing_source_value"
    source_ref: str


class MetadataReview(ResumeModel):
    scope: Literal["selected_metadata_only"] = "selected_metadata_only"
    rendering_authorized: Literal[False] = False
    status: Literal["needs_review", "blocked_by_plan"]
    document_sha256: Digest
    document: MetadataDocument
    findings: tuple[MetadataFinding, ...]
    wording_review: ResumeReview
    warnings: tuple[str, ...]


class MetadataFieldDecision(ResumeModel):
    source_ref: Text
    decision: Literal["approve", "reject"]
    reason: DraftText


class MetadataDecisions(ResumeModel):
    """Unsigned user attestations for selected source copies, not metadata edits."""

    schema_version: Annotated[int, Field(ge=1, le=1)]
    decision_version: Literal["metadata-field-decisions-v1"]
    metadata_version: Literal["source-bound-metadata-v1"]
    plan_sha256: Digest
    wording_document_sha256: Digest
    metadata_selection_sha256: Digest
    metadata_document_sha256: Digest
    fields: Annotated[tuple[MetadataFieldDecision, ...], Field(max_length=512)]

    @model_validator(mode="after")
    def distinct_fields(self) -> Self:
        if len({field.source_ref for field in self.fields}) != len(self.fields):
            raise ValueError("Each metadata field may have only one decision.")
        return self


class AppliedMetadataDecision(ResumeModel):
    source_ref: str
    decision: Literal["approve", "reject"] | None
    reason: str | None
    source_value_missing: bool
    review_status: Literal[
        "pending_review", "approved_by_user", "rejected_by_user", "blocked_by_plan"
    ]


class MetadataDecisionResult(ResumeModel):
    decision_version: str
    scope: Literal["selected_metadata_only"] = "selected_metadata_only"
    rendering_authorized: Literal[False] = False
    status: Literal[
        "needs_review", "blocked_by_plan", "has_rejections", "metadata_fields_approved_by_user"
    ]
    decisions_model_sha256: Digest
    review: MetadataReview
    fields: tuple[AppliedMetadataDecision, ...]
    warnings: tuple[str, ...]
