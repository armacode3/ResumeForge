"""Apply narrow user metadata attestations to freshly reconstructed source snapshots."""

from hashlib import sha256
from pathlib import Path
from typing import Literal

from resumeforge.inputs import MAX_INPUT_BYTES, read_utf8_file
from resumeforge.jobs import JobDocument, JobRequirements
from resumeforge.planning import PlanSelection
from resumeforge.profile import UserProfile
from resumeforge.resume.documents import _parse_resume_model
from resumeforge.resume.metadata import review_metadata
from resumeforge.resume.metadata_models import (
    AppliedMetadataDecision,
    MetadataDecisionResult,
    MetadataDecisions,
    MetadataSelection,
)
from resumeforge.resume.models import ResumeDocument, ResumeError

METADATA_DECISION_VERSION = "metadata-field-decisions-v1"


def parse_metadata_decisions(text: str) -> MetadataDecisions:
    return _parse_resume_model(text, MetadataDecisions, label="Metadata decisions")


def load_metadata_decisions(path: Path) -> MetadataDecisions:
    return parse_metadata_decisions(read_utf8_file(path, label="Metadata decisions"))


def apply_metadata_decisions(
    profile: UserProfile,
    job: JobDocument,
    requirements: JobRequirements,
    selection: PlanSelection,
    draft: ResumeDocument,
    metadata_selection: MetadataSelection,
    decisions: MetadataDecisions,
    *,
    requirements_reviewed: bool = False,
    selection_reviewed: bool = False,
    metadata_selection_reviewed: bool = False,
    decisions_confirmed: bool = False,
) -> MetadataDecisionResult:
    """Require original inputs, fresh metadata and separate exact user confirmation.

    No input report or approved metadata value is trusted. Rejection retains source content;
    missing decisions and null/empty source values stay pending. Plan conflicts block approvals.
    """
    if (
        requirements_reviewed is not True
        or selection_reviewed is not True
        or metadata_selection_reviewed is not True
        or decisions_confirmed is not True
    ):
        raise ResumeError(
            "Explicitly confirm requirements, both selections and metadata decisions."
        )
    if draft is None:
        raise ResumeError("Metadata decisions require an explicit wording draft.")
    try:
        decisions = MetadataDecisions.model_validate(decisions.model_dump(warnings=False))
        encoded = decisions.model_dump_json().encode("utf-8", errors="strict")
    except ValueError:
        raise ResumeError("Invalid metadata decisions; revalidate the versioned fields.") from None
    if len(encoded) > MAX_INPUT_BYTES:
        raise ResumeError("Metadata decisions exceed the input byte limit.")
    if decisions.decision_version != METADATA_DECISION_VERSION:
        raise ResumeError("Decisions belong to a different metadata decision policy; review again.")
    review = review_metadata(
        profile,
        job,
        requirements,
        selection,
        draft,
        metadata_selection,
        requirements_reviewed=requirements_reviewed,
        selection_reviewed=selection_reviewed,
        metadata_selection_reviewed=metadata_selection_reviewed,
    )
    if decisions.metadata_version != review.document.metadata_version:
        raise ResumeError(
            "Decisions belong to a different metadata inspection policy; review again."
        )
    if (
        decisions.plan_sha256 != review.document.plan_sha256
        or decisions.wording_document_sha256 != review.document.wording_document_sha256
        or decisions.metadata_selection_sha256 != review.document.metadata_selection_sha256
        or decisions.metadata_document_sha256 != review.document_sha256
    ):
        raise ResumeError(
            "Decisions belong to a different metadata snapshot; inspect and review again."
        )
    choices = {choice.source_ref: choice for choice in decisions.fields}
    if not choices.keys() <= {field.source_ref for field in review.document.fields}:
        raise ResumeError(
            "Decisions reference an unselected metadata field; review current fields."
        )
    resolved = []
    for field in review.document.fields:
        choice = choices.get(field.source_ref)
        missing = field.value is None or field.value == ()
        state: Literal["pending_review", "approved_by_user", "rejected_by_user", "blocked_by_plan"]
        if choice is None:
            state = "pending_review"
        elif choice.decision == "reject":
            state = "rejected_by_user"
        elif review.status == "blocked_by_plan":
            state = "blocked_by_plan"
        elif missing:
            state = "pending_review"
        else:
            state = "approved_by_user"
        resolved.append(
            AppliedMetadataDecision(
                source_ref=field.source_ref,
                decision=choice.decision if choice else None,
                reason=choice.reason if choice else None,
                source_value_missing=missing,
                review_status=state,
            )
        )
    status: Literal[
        "needs_review", "blocked_by_plan", "has_rejections", "metadata_fields_approved_by_user"
    ]
    if review.status == "blocked_by_plan":
        status = "blocked_by_plan"
    elif any(field.review_status == "rejected_by_user" for field in resolved):
        status = "has_rejections"
    elif not resolved or any(field.review_status == "pending_review" for field in resolved):
        status = "needs_review"
    else:
        status = "metadata_fields_approved_by_user"
    result = MetadataDecisionResult(
        decision_version=METADATA_DECISION_VERSION,
        status=status,
        decisions_model_sha256=sha256(encoded).hexdigest(),
        review=review,
        fields=tuple(resolved),
        warnings=(
            "Metadata decisions are local user attestations, not authenticated identity "
            "or proof of factual truth, dates, contact accuracy or semantic support.",
            "Scope is selected metadata only; no bullet decisions, unselected fields, "
            "skills/coursework or full-resume publication approval is implied.",
            "Missing source values remain unknown; reasons cannot fill or waive them. "
            "Source copies, missing findings, completion context and conflicts remain visible.",
            "Underlying metadata and wording inspection records stay pending. "
            "No source facts were promoted, links fetched, model called or rendering authorized.",
        ),
    )
    if len(result.model_dump_json(indent=2).encode("utf-8")) > MAX_INPUT_BYTES:
        raise ResumeError("Metadata decision result exceeds the output byte limit.")
    return result
