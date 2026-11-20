"""Offline pending skill/coursework copies and explicit context, never inferred qualifications."""

from hashlib import sha256
from pathlib import Path

from resumeforge.inputs import MAX_INPUT_BYTES, read_utf8_file
from resumeforge.jobs import JobDocument, JobRequirements
from resumeforge.matching.literals import literal_span
from resumeforge.planning import PlanSelection
from resumeforge.planning.models import BulletSlot, PlannedEntry
from resumeforge.profile import UserProfile
from resumeforge.profile.models import ResumeSection
from resumeforge.resume.documents import _parse_resume_model
from resumeforge.resume.engine import review_resume
from resumeforge.resume.models import ResumeDocument, ResumeError
from resumeforge.resume.section_content_models import (
    CitedContentContext,
    ContentSection,
    SectionContentDocument,
    SectionContentFinding,
    SectionContentItem,
    SectionContentReview,
    SectionContentSection,
    SectionContentSelection,
    SourceItemSelection,
)


def parse_section_content_selection(text: str) -> SectionContentSelection:
    return _parse_resume_model(text, SectionContentSelection, label="Section content selection")


def load_section_content_selection(path: Path) -> SectionContentSelection:
    return parse_section_content_selection(read_utf8_file(path, label="Section content selection"))


def _pending_item(
    section: ContentSection,
    source_ref: str,
    source_values: list[str],
    choice: SourceItemSelection,
    selected: dict[str, tuple[ResumeSection, PlannedEntry, BulletSlot]],
    findings: list[SectionContentFinding],
) -> SectionContentItem:
    if (
        choice.source_index >= len(source_values)
        or source_values[choice.source_index] != choice.expected_text
    ):
        raise ResumeError(
            "Content selection does not match current source positions and text; review again."
        )
    if not set(choice.accomplishment_ids) <= selected.keys():
        raise ResumeError(
            "Content context must cite eligible accomplishments selected in the current plan."
        )
    findings.append(
        SectionContentFinding(
            code="skill_usage_requires_user_review"
            if section == "skills"
            else "coursework_context_requires_user_review",
            section=section,
            source_ref=source_ref,
        )
    )
    if not choice.accomplishment_ids:
        findings.append(
            SectionContentFinding(
                code="no_cited_accomplishments", section=section, source_ref=source_ref
            )
        )
    contexts = []
    text = source_values[choice.source_index]
    for reference in choice.accomplishment_ids:
        parent_section, entry, slot = selected[reference]
        mention = literal_span(text, slot.statement)
        contexts.append(
            CitedContentContext(
                accomplishment_id=reference,
                entry_id=entry.entry_id,
                section=parent_section,
                source_statement=slot.statement,
                entry_completion_status=entry.completion_status,
                caveats=slot.caveats,
                literal_label_mention=mention,
            )
        )
        if mention is None:
            findings.append(
                SectionContentFinding(
                    code="label_not_literal_in_cited_statement",
                    section=section,
                    source_ref=source_ref,
                    accomplishment_id=reference,
                )
            )
    questions = (
        (
            "Where and how did you personally use this skill: "
            "class, project, job, research or elsewhere? "
            "If you have not used it or are unsure, say so; the recorded label is not proof.",
            "What was your own contribution and what supervision or limitations applied? "
            "Inspect each cited statement; do not infer professional experience or proficiency.",
        )
        if section == "skills"
        else (
            "What does this course record mean: completed, current, planned or uncertain? "
            "The recorded name alone establishes no enrollment, completion, grade or institution.",
            "Which original source supports that context? Cited project/work statements do not "
            "by themselves prove course attendance or skill proficiency.",
        )
    )
    return SectionContentItem(
        source_ref=source_ref, text=text, cited_context=tuple(contexts), review_questions=questions
    )


def review_section_content(
    profile: UserProfile,
    job: JobDocument,
    requirements: JobRequirements,
    selection: PlanSelection,
    draft: ResumeDocument,
    content_selection: SectionContentSelection,
    *,
    requirements_reviewed: bool = False,
    selection_reviewed: bool = False,
    content_selection_reviewed: bool = False,
) -> SectionContentReview:
    """Only expose deliberately chosen recorded labels; all items/questions remain unapproved."""
    if (
        requirements_reviewed is not True
        or selection_reviewed is not True
        or content_selection_reviewed is not True
    ):
        raise ResumeError("Explicitly confirm requirements, plan and section content selections.")
    if draft is None:
        raise ResumeError("Section content review requires an explicit wording draft.")
    try:
        profile = UserProfile.model_validate(profile.model_dump(warnings=False))
        content_selection = SectionContentSelection.model_validate(
            content_selection.model_dump(warnings=False)
        )
        encoded_selection = content_selection.model_dump_json().encode("utf-8", errors="strict")
    except ValueError:
        raise ResumeError(
            "Invalid section content inputs; revalidate profile and selection."
        ) from None
    if len(encoded_selection) > MAX_INPUT_BYTES:
        raise ResumeError("Section content selection exceeds the input byte limit.")
    review = review_resume(
        profile,
        job,
        requirements,
        selection,
        draft,
        requirements_reviewed=True,
        selection_reviewed=True,
    )
    sections = {s.section for s in review.plan.sections}
    if (content_selection.skills and "skills" not in sections) or (
        content_selection.coursework and "coursework" not in sections
    ):
        raise ResumeError("Selected content sections must already belong to the current plan.")
    selected = {
        slot.accomplishment_id: (section.section, entry, slot)
        for section in review.plan.sections
        for entry in section.entries
        for slot in entry.bullet_slots
    }
    findings: list[SectionContentFinding] = []
    try:
        skills = tuple(
            _pending_item(
                "skills",
                f"skills.{item.category}.{item.source_index}",
                getattr(profile.skills, item.category),
                item,
                selected,
                findings,
            )
            for item in content_selection.skills
        )
        courses = tuple(
            _pending_item(
                "coursework",
                f"coursework.{item.source_index}",
                profile.coursework,
                item,
                selected,
                findings,
            )
            for item in content_selection.coursework
        )
        content_sections = []
        for planned in review.plan.sections:
            if planned.section not in ("skills", "coursework"):
                continue
            items = skills if planned.section == "skills" else courses
            content_sections.append(
                SectionContentSection(
                    section=planned.section, required=planned.required, items=items
                )
            )
            if not items:
                findings.append(
                    SectionContentFinding(
                        code="section_without_selected_items", section=planned.section
                    )
                )
        if not skills and not courses:
            findings.append(SectionContentFinding(code="no_selected_items"))
        document = SectionContentDocument(
            plan_sha256=review.document.plan_sha256,
            wording_document_sha256=review.document_sha256,
            content_selection_sha256=sha256(encoded_selection).hexdigest(),
            sections=tuple(content_sections),
        )
        result = SectionContentReview(
            status=review.status,
            document=document,
            document_sha256=sha256(document.model_dump_json().encode("utf-8")).hexdigest(),
            findings=tuple(findings),
            wording_review=review,
            warnings=(
                "Recorded skill/course names and user-cited contexts remain pending, not verified "
                "skills, demonstrated proficiency, professional experience or job qualification.",
                "A literal label mention can be negated/incidental; an absent mention is unknown, "
                "not proof of missing experience or unsupported claims. Review full sources.",
                "Questions have no prefilled answers or confirmations. New answers require a "
                "separate source-review workflow; this command saves or promotes no facts.",
                "No enrollment, completion, dates or contribution is inferred. "
                "Course lists, job text, parent technologies and old wording "
                "are not skill evidence.",
                "Only selected labels and current plan context are exposed; no contact or notes "
                "are copied. Output is private, not anonymized; inspect original sources too.",
                "No approval transfer, inference, research, link fetching or assembly integration. "
                "Rendering stays unauthorized; skills/coursework readiness blockers are unchanged.",
            ),
        )
        encoded = result.model_dump_json(indent=2).encode("utf-8", errors="strict")
    except ResumeError:
        raise
    except ValueError:
        raise ResumeError(
            "Invalid section content source values; check the versioned limits."
        ) from None
    if len(encoded) > MAX_INPUT_BYTES:
        raise ResumeError(
            "Section content review exceeds the output byte limit; reduce explicit inputs."
        )
    return result
