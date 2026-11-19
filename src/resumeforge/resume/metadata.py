"""Offline selected metadata snapshots; no editing, factual approval or rendering."""

from hashlib import sha256
from pathlib import Path

from resumeforge.inputs import MAX_INPUT_BYTES, read_utf8_file
from resumeforge.jobs import JobDocument, JobRequirements
from resumeforge.planning import PlanSelection
from resumeforge.profile import UserProfile
from resumeforge.resume.documents import _parse_resume_model
from resumeforge.resume.engine import review_resume
from resumeforge.resume.metadata_models import (
    MetadataDocument,
    MetadataEntryContext,
    MetadataField,
    MetadataFinding,
    MetadataReview,
    MetadataSelection,
)
from resumeforge.resume.models import ResumeDocument, ResumeError

MAX_METADATA_FIELDS = 512


def parse_metadata_selection(text: str) -> MetadataSelection:
    return _parse_resume_model(text, MetadataSelection, label="Metadata selection")


def load_metadata_selection(path: Path) -> MetadataSelection:
    return parse_metadata_selection(read_utf8_file(path, label="Metadata selection"))


def review_metadata(
    profile: UserProfile,
    job: JobDocument,
    requirements: JobRequirements,
    selection: PlanSelection,
    draft: ResumeDocument,
    metadata_selection: MetadataSelection,
    *,
    requirements_reviewed: bool = False,
    selection_reviewed: bool = False,
    metadata_selection_reviewed: bool = False,
) -> MetadataReview:
    """Expose only explicitly chosen fields from fresh source snapshots; all remain pending.

    Entry choices must already be present in the current plan (including required placeholders).
    Completion context is independent of dates; missing values stay unset. An output metadata
    document or previous approval is never accepted as evidence, and no provider receives metadata.
    """
    if (
        requirements_reviewed is not True
        or selection_reviewed is not True
        or metadata_selection_reviewed is not True
    ):
        raise ResumeError(
            "Explicitly confirm requirements, content and metadata selections before review."
        )
    if draft is None:
        raise ResumeError("Metadata review requires an explicit wording draft.")
    try:
        # Keep the values used below on the same private model snapshot passed to inspection.
        profile = UserProfile.model_validate(profile.model_dump(warnings=False))
        metadata_selection = MetadataSelection.model_validate(
            metadata_selection.model_dump(warnings=False)
        )
        selection_bytes = metadata_selection.model_dump_json().encode("utf-8", errors="strict")
    except ValueError:
        raise ResumeError(
            "Invalid metadata inputs; revalidate the profile and field selection."
        ) from None
    if len(selection_bytes) > MAX_INPUT_BYTES:
        raise ResumeError("Metadata selection exceeds the input byte limit.")
    count = len(metadata_selection.person_fields) + sum(
        len(e.fields) for e in metadata_selection.entries
    )
    if count > MAX_METADATA_FIELDS:
        raise ResumeError("Metadata selection exceeds the field limit; select fewer fields.")
    review = review_resume(
        profile,
        job,
        requirements,
        selection,
        draft,
        requirements_reviewed=requirements_reviewed,
        selection_reviewed=selection_reviewed,
    )
    planned = {e.entry_id: (s.section, e) for s in review.plan.sections for e in s.entries}
    sources = {entry.id: entry for entry in profile.entries()}
    if not {e.entry_id for e in metadata_selection.entries} <= planned.keys():
        raise ResumeError("Metadata entries must belong to the current non-excluded plan.")
    try:
        fields = []
        for field in metadata_selection.person_fields:
            value = (
                tuple(str(link) for link in profile.person.links)
                if field == "links"
                else getattr(profile.person, field)
            )
            fields.append(MetadataField(source_ref=f"person.{field}", value=value))
        contexts = []
        for choice in metadata_selection.entries:
            section, entry = planned[choice.entry_id]
            contexts.append(
                MetadataEntryContext(
                    entry_id=choice.entry_id,
                    section=section,
                    completion_status=entry.completion_status,
                )
            )
            fields.extend(
                MetadataField(
                    source_ref=f"{section}.{choice.entry_id}.{field}",
                    value=getattr(sources[choice.entry_id], field),
                )
                for field in choice.fields
            )
        document = MetadataDocument(
            schema_version=1,
            plan_sha256=review.document.plan_sha256,
            wording_document_sha256=review.document_sha256,
            metadata_selection_sha256=sha256(selection_bytes).hexdigest(),
            fields=tuple(fields),
            entry_contexts=tuple(contexts),
        )
        result = MetadataReview(
            status=review.status,
            document=document,
            document_sha256=sha256(document.model_dump_json().encode("utf-8")).hexdigest(),
            findings=tuple(
                MetadataFinding(source_ref=field.source_ref)
                for field in fields
                if field.value is None or field.value == ()
            ),
            wording_review=review,
            warnings=(
                "All selected metadata remains pending; profile structure and source copying "
                "do not verify facts, dates, identity or contact accuracy.",
                "Dates and completion states are independent; missing values stay unknown, "
                "and present is copied only when explicitly recorded.",
                "This private output includes only explicitly selected metadata values; "
                "links are model-normalized strings and are never fetched.",
                "Metadata inspection itself applies no decisions, transfers no bullet approval, "
                "assembles no full resume, calls no model and authorizes no rendering.",
            ),
        )
        encoded = result.model_dump_json(indent=2).encode("utf-8", errors="strict")
    except ValueError:
        raise ResumeError(
            "Invalid metadata source values; check the versioned field limits."
        ) from None
    if len(encoded) > MAX_INPUT_BYTES:
        raise ResumeError(
            "Metadata review exceeds the output byte limit; reduce the explicit selection."
        )
    return result
