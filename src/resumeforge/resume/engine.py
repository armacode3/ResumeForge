"""Seed source wording or review submitted wording against a freshly recomputed plan."""

import json
from dataclasses import asdict
from hashlib import sha256

from resumeforge.inputs import MAX_INPUT_BYTES
from resumeforge.jobs import JobDocument, JobRequirements
from resumeforge.planning import PlanningError, PlanSelection, ResumePlan, plan_resume
from resumeforge.profile import UserProfile
from resumeforge.resume.models import (
    BulletReview,
    ResumeBullet,
    ResumeDocument,
    ResumeEntry,
    ResumeError,
    ResumeReview,
    ResumeSectionDraft,
)

REVIEW_VERSION = "resume-draft-review-v1"


def _plan_digest(plan: ResumePlan) -> str:
    encoded = json.dumps(asdict(plan), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return sha256(encoded.encode("utf-8")).hexdigest()


def _seed_document(plan: ResumePlan, digest: str) -> ResumeDocument:
    return ResumeDocument(
        schema_version=1,
        plan_sha256=digest,
        sections=tuple(
            ResumeSectionDraft(
                section=section.section,
                entries=tuple(
                    ResumeEntry(
                        entry_id=entry.entry_id,
                        bullets=tuple(
                            ResumeBullet(
                                id="bullet_draft_" + slot.accomplishment_id.removeprefix("acc_"),
                                accomplishment_id=slot.accomplishment_id,
                                text=slot.statement,
                            )
                            for slot in entry.bullet_slots
                        ),
                    )
                    for entry in section.entries
                ),
            )
            for section in plan.sections
        ),
    )


def _check_alignment(document: ResumeDocument, plan: ResumePlan) -> None:
    if tuple(section.section for section in document.sections) != tuple(
        section.section for section in plan.sections
    ):
        raise ResumeError("Draft sections must exactly preserve the current plan and its order.")
    for proposed, planned in zip(document.sections, plan.sections, strict=True):
        if tuple(entry.entry_id for entry in proposed.entries) != tuple(
            entry.entry_id for entry in planned.entries
        ):
            raise ResumeError("Draft entries must exactly preserve the current plan and its order.")
        for entry, planned_entry in zip(proposed.entries, planned.entries, strict=True):
            if tuple(bullet.accomplishment_id for bullet in entry.bullets) != tuple(
                slot.accomplishment_id for slot in planned_entry.bullet_slots
            ):
                raise ResumeError(
                    "Draft evidence must exactly preserve selected slots and their order."
                )


def review_resume(
    profile: UserProfile,
    job: JobDocument,
    requirements: JobRequirements,
    selection: PlanSelection,
    draft: ResumeDocument | None = None,
    *,
    requirements_reviewed: bool = False,
    selection_reviewed: bool = False,
) -> ResumeReview:
    """Never approve wording, infer claim support, or trust a supplied plan/review result.

    When draft is omitted, copy complete source statements into pending bullet records. With
    a submitted draft, validate its exact plan binding/structure and flag all changed wording.
    Even verbatim wording remains pending factual/context review. No model is called.
    """
    try:
        plan = plan_resume(
            profile,
            job,
            requirements,
            selection,
            requirements_reviewed=requirements_reviewed,
            selection_reviewed=selection_reviewed,
        )
    except PlanningError as error:
        raise ResumeError(str(error)) from None
    digest = _plan_digest(plan)
    try:
        if draft is None:
            document = _seed_document(plan, digest)
        else:
            document = ResumeDocument.model_validate(draft.model_dump(warnings=False))
        encoded = document.model_dump_json().encode("utf-8", errors="strict")
    except ValueError:
        raise ResumeError(
            "Invalid draft fields or source statements; check the versioned draft limits."
        ) from None
    if len(encoded) > MAX_INPUT_BYTES:
        raise ResumeError("Draft exceeds the input byte limit; shorten the selection or wording.")
    if draft is not None:
        if document.plan_sha256 != digest:
            raise ResumeError(
                "Draft belongs to a different plan snapshot; seed/review a current draft."
            )
        _check_alignment(document, plan)
    reviews = tuple(
        BulletReview(
            bullet_id=bullet.id,
            entry_id=entry.entry_id,
            accomplishment_id=bullet.accomplishment_id,
            source_statement=slot.statement,
            wording_status="verbatim_source"
            if bullet.text == slot.statement
            else "edited_requires_review",
            caveats=slot.caveats,
        )
        for section, planned_section in zip(document.sections, plan.sections, strict=True)
        for entry, planned_entry in zip(section.entries, planned_section.entries, strict=True)
        for bullet, slot in zip(entry.bullets, planned_entry.bullet_slots, strict=True)
    )
    return ResumeReview(
        review_version=REVIEW_VERSION,
        mode="source_seed" if draft is None else "submitted_draft",
        status="blocked_by_plan" if plan.constraint_status == "conflicts" else "needs_review",
        document_sha256=sha256(encoded).hexdigest(),
        document=document,
        plan=plan,
        bullets=reviews,
        warnings=(
            "Every bullet remains pending review, including verbatim source statements.",
            "Changed wording needs factual/context review; "
            "no semantic support check was performed.",
            "No detection guarantee for invented metrics, technology use, "
            "ownership or lost qualifiers.",
            "No approval, model inference, rendering or page/readability validation was performed.",
        ),
    )
