"""Assemble exact selected components with fresh, separate attestations and finite readiness."""

from hashlib import sha256

from resumeforge.inputs import MAX_INPUT_BYTES
from resumeforge.jobs import JobDocument, JobRequirements
from resumeforge.planning import PlanSelection
from resumeforge.profile import UserProfile
from resumeforge.resume.assembly_models import (
    AssemblyIssue,
    AssemblyResult,
    BulletAttestations,
    IssueCode,
    MetadataAttestations,
    StructuredEntry,
    StructuredResume,
    StructuredSection,
)
from resumeforge.resume.decisions import apply_review_decisions
from resumeforge.resume.metadata import review_metadata
from resumeforge.resume.metadata_decisions import apply_metadata_decisions
from resumeforge.resume.metadata_models import MetadataDecisions, MetadataReview, MetadataSelection
from resumeforge.resume.models import ResumeDocument, ResumeError, ReviewDecisions


def assemble_resume(
    profile: UserProfile,
    job: JobDocument,
    requirements: JobRequirements,
    selection: PlanSelection,
    draft: ResumeDocument,
    metadata_selection: MetadataSelection,
    *,
    bullet_decisions: ReviewDecisions | None = None,
    metadata_decisions: MetadataDecisions | None = None,
    requirements_reviewed: bool = False,
    selection_reviewed: bool = False,
    metadata_selection_reviewed: bool = False,
    bullet_decisions_confirmed: bool = False,
    metadata_decisions_confirmed: bool = False,
) -> AssemblyResult:
    """Never accept prior receipts, infer fields, filter rejections or approve the whole resume."""
    if (
        requirements_reviewed is not True
        or selection_reviewed is not True
        or metadata_selection_reviewed is not True
    ):
        raise ResumeError("Explicitly confirm requirements and both selections before assembly.")
    for decisions, confirmed in (
        (bullet_decisions, bullet_decisions_confirmed),
        (metadata_decisions, metadata_decisions_confirmed),
    ):
        if (decisions is not None and confirmed is not True) or (
            decisions is None and confirmed is not False
        ):
            raise ResumeError("Each supplied decision file requires its own exact confirmation.")
    review = review_metadata(
        profile,
        job,
        requirements,
        selection,
        draft,
        metadata_selection,
        requirements_reviewed=True,
        selection_reviewed=True,
        metadata_selection_reviewed=True,
    )
    bullet_attestations = None
    metadata_attestations = None
    if bullet_decisions is not None:
        applied = apply_review_decisions(
            profile,
            job,
            requirements,
            selection,
            draft,
            bullet_decisions,
            requirements_reviewed=True,
            selection_reviewed=True,
            decisions_confirmed=True,
        )
        if applied.review != review.wording_review:
            raise ResumeError("Assembly inputs changed during review; inspect the sources again.")
        bullet_attestations = BulletAttestations(
            decision_version=applied.decision_version,
            status=applied.status,
            decisions_model_sha256=applied.decisions_model_sha256,
            bullets=applied.bullets,
            warnings=applied.warnings,
        )
    if metadata_decisions is not None:
        metadata_applied = apply_metadata_decisions(
            profile,
            job,
            requirements,
            selection,
            draft,
            metadata_selection,
            metadata_decisions,
            requirements_reviewed=True,
            selection_reviewed=True,
            metadata_selection_reviewed=True,
            decisions_confirmed=True,
        )
        if metadata_applied.review != review:
            raise ResumeError("Assembly inputs changed during review; inspect the sources again.")
        metadata_attestations = MetadataAttestations(
            decision_version=metadata_applied.decision_version,
            status=metadata_applied.status,
            decisions_model_sha256=metadata_applied.decisions_model_sha256,
            fields=metadata_applied.fields,
            warnings=metadata_applied.warnings,
        )
    document, issues = _components(review, bullet_attestations, metadata_attestations)
    result = AssemblyResult(
        status="blocked_by_plan"
        if review.status == "blocked_by_plan"
        else "needs_review"
        if issues
        else "components_reviewed",
        document_sha256=sha256(document.model_dump_json().encode("utf-8")).hexdigest(),
        document=document,
        review=review,
        bullet_attestations=bullet_attestations,
        metadata_attestations=metadata_attestations,
        issues=tuple(issues),
        warnings=(
            "Finite component readiness is not full-resume approval, factual/semantic proof, "
            "job qualification, safe publication or layout feasibility. "
            "Rendering remains unauthorized.",
            "Minimum fields are selected person.name and each planned entry title; no contact "
            "method, organization or date is inferred or required by this limited policy.",
            "Selected skills/coursework remain unresolved placeholders; no unscoped content is "
            "copied or approved. All source copies and wording records remain pending.",
            "User attestations retain separate scopes and snapshot bindings; findings, source "
            "caveats, completion context and rejected content remain visible, not resolved.",
            "Private read-only output; no provider, link fetching, history, rendering or writes.",
        ),
    )
    if len(result.model_dump_json(indent=2).encode("utf-8")) > MAX_INPUT_BYTES:
        raise ResumeError(
            "Structured assembly exceeds the output byte limit; reduce explicit inputs."
        )
    return result


def _components(
    review: MetadataReview,
    bullet_attestations: BulletAttestations | None,
    metadata_attestations: MetadataAttestations | None,
) -> tuple[StructuredResume, list[AssemblyIssue]]:
    """Place source copies in plan order without discarding unresolved or rejected content."""
    plan = review.wording_review.plan
    fields = review.document.fields
    sections = []
    issues = [
        AssemblyIssue(
            code="plan_conflict",
            section=f.section,
            entry_id=f.entry_id,
            plan_finding_code=f.code,
        )
        for f in plan.findings
        if f.severity == "conflict"
    ]
    refs = {field.source_ref for field in fields}
    if "person.name" not in refs:
        issues.append(AssemblyIssue(code="required_field_unselected", source_ref="person.name"))
    for planned_section, wording_section in zip(
        plan.sections, review.wording_review.document.sections, strict=True
    ):
        section = planned_section.section
        if section in ("skills", "coursework"):
            issues.append(AssemblyIssue(code="unscoped_section_unresolved", section=section))
        elif not planned_section.entries:
            issues.append(AssemblyIssue(code="empty_section", section=section))
        entries = []
        for planned_entry, wording_entry in zip(
            planned_section.entries, wording_section.entries, strict=True
        ):
            entry_id = planned_entry.entry_id
            prefix = f"{section}.{entry_id}."
            entries.append(
                StructuredEntry(
                    entry_id=entry_id,
                    completion_status=planned_entry.completion_status,
                    metadata=tuple(
                        field for field in fields if field.source_ref.startswith(prefix)
                    ),
                    bullets=wording_entry.bullets,
                )
            )
            if prefix + "title" not in refs:
                issues.append(
                    AssemblyIssue(
                        code="required_field_unselected",
                        section=section,
                        entry_id=entry_id,
                        source_ref=prefix + "title",
                    )
                )
            if planned_entry.selection_reason != "user_selected":
                issues.append(
                    AssemblyIssue(
                        code="required_entry_not_explicitly_selected",
                        section=section,
                        entry_id=entry_id,
                    )
                )
            if planned_entry.completion_status not in ("completed", "in_progress"):
                issues.append(
                    AssemblyIssue(
                        code="entry_status_unresolved", section=section, entry_id=entry_id
                    )
                )
        sections.append(
            StructuredSection(
                section=section, required=planned_section.required, entries=tuple(entries)
            )
        )
    if not any(section.entries for section in sections):
        issues.append(AssemblyIssue(code="no_entries"))
    if not review.wording_review.bullets:
        issues.append(AssemblyIssue(code="no_bullets"))
    bullet_states = (
        {b.bullet_id: b.review_status for b in bullet_attestations.bullets}
        if bullet_attestations
        else {}
    )
    metadata_states = (
        {f.source_ref: f.review_status for f in metadata_attestations.fields}
        if metadata_attestations
        else {}
    )
    for bullet in review.wording_review.bullets:
        state = bullet_states.get(bullet.bullet_id, "pending_review")
        if state != "approved_by_user":
            code: IssueCode = (
                "bullet_decision_rejected"
                if state == "rejected_by_user"
                else "bullet_decision_blocked"
                if state == "blocked_by_plan"
                else "bullet_decision_pending"
            )
            issues.append(
                AssemblyIssue(code=code, entry_id=bullet.entry_id, bullet_id=bullet.bullet_id)
            )
    for field in fields:
        if field.value is None or field.value == ():
            issues.append(AssemblyIssue(code="selected_field_missing", source_ref=field.source_ref))
        state = metadata_states.get(field.source_ref, "pending_review")
        if state != "approved_by_user":
            code = (
                "metadata_decision_rejected"
                if state == "rejected_by_user"
                else "metadata_decision_blocked"
                if state == "blocked_by_plan"
                else "metadata_decision_pending"
            )
            issues.append(AssemblyIssue(code=code, source_ref=field.source_ref))
    document = StructuredResume(
        schema_version=1,
        plan_sha256=review.document.plan_sha256,
        wording_document_sha256=review.document.wording_document_sha256,
        metadata_selection_sha256=review.document.metadata_selection_sha256,
        metadata_document_sha256=review.document_sha256,
        header=tuple(field for field in fields if field.source_ref.startswith("person.")),
        sections=tuple(sections),
    )
    return document, issues
