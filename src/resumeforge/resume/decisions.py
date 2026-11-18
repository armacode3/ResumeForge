"""Apply explicit user decisions to exact current snapshots, never to self-approved drafts."""

from hashlib import sha256
from typing import Literal

from resumeforge.inputs import MAX_INPUT_BYTES
from resumeforge.jobs import JobDocument, JobRequirements
from resumeforge.planning import PlanSelection
from resumeforge.profile import UserProfile
from resumeforge.resume.engine import review_resume
from resumeforge.resume.models import (
    AppliedBulletDecision,
    ResumeDocument,
    ResumeError,
    ReviewDecisionResult,
    ReviewDecisions,
)

DECISION_VERSION = "snapshot-bound-decisions-v3"


def apply_review_decisions(
    profile: UserProfile,
    job: JobDocument,
    requirements: JobRequirements,
    selection: PlanSelection,
    draft: ResumeDocument,
    decisions: ReviewDecisions,
    *,
    requirements_reviewed: bool = False,
    selection_reviewed: bool = False,
    decisions_confirmed: bool = False,
) -> ReviewDecisionResult:
    """Record narrow human attestations; do not approve metadata, truth, job fit or rendering.

    Missing decisions stay pending. Rejected content remains visible rather than being trimmed.
    Plan conflicts block approvals, even when every requested decision says approve. Callers
    must supply sources and a draft, not a prior result claiming to have been approved.
    """
    if (
        requirements_reviewed is not True
        or selection_reviewed is not True
        or decisions_confirmed is not True
    ):
        raise ResumeError(
            "Explicitly confirm requirements, selection and human decisions "
            "before applying decisions."
        )
    if draft is None:
        raise ResumeError(
            "Review decisions require an explicit draft, not an implicit source seed."
        )
    try:
        decisions = ReviewDecisions.model_validate(decisions.model_dump(warnings=False))
        encoded = decisions.model_dump_json().encode("utf-8", errors="strict")
    except ValueError:
        raise ResumeError(
            "Invalid review decisions; revalidate the versioned decision fields."
        ) from None
    if len(encoded) > MAX_INPUT_BYTES:
        raise ResumeError("Review decisions exceed the input byte limit; shorten the input.")
    review = review_resume(
        profile,
        job,
        requirements,
        selection,
        draft,
        requirements_reviewed=requirements_reviewed,
        selection_reviewed=selection_reviewed,
    )
    if decisions.review_version != review.review_version:
        raise ResumeError("Review decisions belong to a different inspection policy; review again.")
    if (
        decisions.plan_sha256 != review.document.plan_sha256
        or decisions.document_sha256 != review.document_sha256
    ):
        raise ResumeError(
            "Review decisions belong to a different draft snapshot; "
            "review current wording and evidence."
        )
    choices = {choice.bullet_id: choice for choice in decisions.bullets}
    if decisions.findings_sha256 != review.findings_sha256:
        raise ResumeError(
            "Review decisions belong to different findings; inspect and review again."
        )
    if decisions.fragments_sha256 != review.fragments_sha256:
        raise ResumeError(
            "Review decisions belong to different source fragments; inspect and review again."
        )
    if not choices.keys() <= {bullet.bullet_id for bullet in review.bullets}:
        raise ResumeError("Review decisions reference a bullet absent from the current draft.")
    resolved = []
    draft_texts = {
        bullet.id: bullet.text
        for section in review.document.sections
        for entry in section.entries
        for bullet in entry.bullets
    }
    for bullet in review.bullets:
        choice = choices.get(bullet.bullet_id)
        finding_ids = tuple(finding.id for finding in bullet.findings)
        acknowledged = choice.acknowledged_finding_ids if choice else ()
        if not set(acknowledged) <= set(finding_ids):
            raise ResumeError(
                "Finding acknowledgements must reference current findings on that bullet."
            )
        unacknowledged = tuple(
            identifier for identifier in finding_ids if identifier not in acknowledged
        )
        fragment_ids = tuple(fragment.id for fragment in bullet.source_fragments)
        fragment_choices = choice.fragment_decisions if choice else ()
        by_fragment = {record.fragment_id: record for record in fragment_choices}
        if not by_fragment.keys() <= set(fragment_ids):
            raise ResumeError("Fragment decisions must reference current fragments on that bullet.")
        for record in fragment_choices:
            span = record.draft_span
            text = draft_texts[bullet.bullet_id]
            if span is not None and (
                span.end > len(text) or text[span.start : span.end] != span.text
            ):
                raise ResumeError(
                    "Fragment draft passages must exactly match that bullet's wording."
                )
        # Preserve source order in applied records, irrespective of decision input order.
        ordered_fragments = tuple(by_fragment[f] for f in fragment_ids if f in by_fragment)
        unreviewed = tuple(f for f in fragment_ids if f not in by_fragment)
        revisions = tuple(
            f.fragment_id for f in ordered_fragments if f.disposition == "needs_revision"
        )
        state: Literal["pending_review", "approved_by_user", "rejected_by_user", "blocked_by_plan"]
        if choice is None:
            state = "pending_review"
        elif choice.decision == "reject":
            state = "rejected_by_user"
        elif review.status == "blocked_by_plan":
            state = "blocked_by_plan"
        elif unacknowledged or unreviewed or revisions:
            state = "pending_review"
        else:
            state = "approved_by_user"
        resolved.append(
            AppliedBulletDecision(
                bullet_id=bullet.bullet_id,
                accomplishment_id=bullet.accomplishment_id,
                decision=choice.decision if choice else None,
                reason=choice.reason if choice else None,
                acknowledged_finding_ids=acknowledged,
                unacknowledged_finding_ids=unacknowledged,
                fragment_decisions=ordered_fragments,
                unreviewed_fragment_ids=unreviewed,
                revision_fragment_ids=revisions,
                review_status=state,
            )
        )
    status: Literal[
        "blocked_by_plan", "has_rejections", "needs_review", "bullet_wording_approved_by_user"
    ]
    if review.status == "blocked_by_plan":
        status = "blocked_by_plan"
    elif any(bullet.review_status == "rejected_by_user" for bullet in resolved):
        status = "has_rejections"
    elif not resolved or any(bullet.review_status == "pending_review" for bullet in resolved):
        status = "needs_review"
    else:
        status = "bullet_wording_approved_by_user"
    return ReviewDecisionResult(
        decision_version=DECISION_VERSION,
        status=status,
        decisions_model_sha256=sha256(encoded).hexdigest(),
        review=review,
        bullets=tuple(resolved),
        warnings=(
            "Decisions are local user attestations, not authenticated identity or semantic proof.",
            "Acknowledging literal findings is not evidence of claim support or issue resolution.",
            "Fragment representations and accepted omissions are user attestations, "
            "not semantic equivalence, qualifier safety or proof of source coverage.",
            "Scope is bullet wording only; metadata, unscoped sections, "
            "job fit and layout remain unapproved.",
            "Underlying draft/inspection states stay pending; "
            "applied decisions are separate snapshot records.",
            "No rendering, model inference, profile fact promotion "
            "or history persistence was performed.",
        ),
    )
