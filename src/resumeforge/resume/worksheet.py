"""Fresh offline review with unfilled decision fields, never a source of attestations."""

from resumeforge.inputs import MAX_INPUT_BYTES
from resumeforge.jobs import JobDocument, JobRequirements
from resumeforge.planning import PlanSelection
from resumeforge.profile import UserProfile
from resumeforge.resume.engine import review_resume
from resumeforge.resume.models import (
    PendingBulletDecision,
    PendingFragmentDecision,
    PendingReviewDecisions,
    ResumeDocument,
    ResumeError,
    ReviewWorksheet,
)


def build_review_worksheet(
    profile: UserProfile,
    job: JobDocument,
    requirements: JobRequirements,
    selection: PlanSelection,
    draft: ResumeDocument,
    *,
    requirements_reviewed: bool = False,
    selection_reviewed: bool = False,
) -> ReviewWorksheet:
    """Copy bindings/IDs, never infer choices, reasons, acknowledgements or draft links.

    An explicit draft and freshly revalidated original sources are required. No prior review,
    worksheet or decision receipt is accepted as authority. All generated choices remain null.
    """
    if requirements_reviewed is not True or selection_reviewed is not True:
        raise ResumeError(
            "Explicitly confirm requirements and selection before building a worksheet."
        )
    if draft is None:
        raise ResumeError(
            "A review worksheet requires an explicit draft, not an implicit source seed."
        )
    review = review_resume(
        profile,
        job,
        requirements,
        selection,
        draft,
        requirements_reviewed=requirements_reviewed,
        selection_reviewed=selection_reviewed,
    )
    try:
        template = PendingReviewDecisions.model_validate(
            {
                "review_version": review.review_version,
                "plan_sha256": review.document.plan_sha256,
                "document_sha256": review.document_sha256,
                "findings_sha256": review.findings_sha256,
                "fragments_sha256": review.fragments_sha256,
                "bullets": tuple(
                    PendingBulletDecision(
                        bullet_id=bullet.bullet_id,
                        fragment_decisions=tuple(
                            PendingFragmentDecision(fragment_id=fragment.id)
                            for fragment in bullet.source_fragments
                        ),
                    )
                    for bullet in review.bullets
                ),
            }
        )
        worksheet = ReviewWorksheet(
            status=review.status,
            review=review,
            decision_template=template,
            warnings=(
                "Every worksheet choice is unfilled; no finding is acknowledged "
                "or fragment reviewed.",
                "Extract decision_template privately, deliberately fill choices/reasons and "
                "reviewed fragment dispositions, or remove unreviewed bullet records "
                "before applying decisions.",
                "Null placeholders are not valid decisions. Empty documents or omitted decisions "
                "remain pending; changed sources/wording/policies require fresh review.",
                "The worksheet is not decision input, factual/semantic proof or rendering "
                "authorization. Literal findings and fragments have documented blind spots.",
            ),
        )
        encoded = worksheet.model_dump_json(indent=2).encode("utf-8", errors="strict")
    except ValueError:
        raise ResumeError(
            "Invalid worksheet fields or inspection policy; inspect the current draft."
        ) from None
    if len(encoded) > MAX_INPUT_BYTES:
        raise ResumeError(
            "Review worksheet exceeds the byte limit; shorten the selection and review again."
        )
    return worksheet
