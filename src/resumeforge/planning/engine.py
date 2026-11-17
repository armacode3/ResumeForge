"""Count-constrained assembly of explicitly reviewed selections; no relevance ranking."""

from hashlib import sha256
from typing import cast

from pydantic import ValidationError

from resumeforge.jobs import JobDocument, JobRequirements
from resumeforge.matching import MatchingError, match_evidence
from resumeforge.matching.models import EvidenceDecision
from resumeforge.planning.models import (
    BulletSlot,
    PlanBudget,
    PlanFinding,
    PlanJobItem,
    PlannedEntry,
    PlannedSection,
    PlanningError,
    PlanSelection,
    ResumePlan,
)
from resumeforge.profile import UserProfile
from resumeforge.profile.models import ResumeSection, Skills

PLANNING_VERSION = "reviewed-selection-plan-v1"


def _bullet_slots(
    entry_id: str,
    references: list[str],
    evidence: dict[str, EvidenceDecision],
    links: dict[str, tuple[str, ...]],
    findings: list[PlanFinding],
) -> tuple[BulletSlot, ...]:
    slots = []
    for reference in references:
        record = evidence[reference]
        if record.eligibility != "eligible_for_matching":
            findings.append(
                PlanFinding(
                    "selected_evidence_ineligible",
                    "conflict",
                    entry_id=entry_id,
                    accomplishment_id=reference,
                )
            )
            continue
        if not links[reference]:
            findings.append(
                PlanFinding(
                    "selected_evidence_without_lexical_link",
                    "review",
                    entry_id=entry_id,
                    accomplishment_id=reference,
                )
            )
        assert record.statement is not None
        caveats = (
            ("parent_entry_in_progress",) if record.entry_completion_status == "in_progress" else ()
        )
        slots.append(BulletSlot(reference, record.statement, links[reference], caveats))
    return tuple(slots)


def _check_counts(budget: PlanBudget, sections: tuple[PlannedSection, ...]) -> list[PlanFinding]:
    findings = []
    if budget.min_projects is not None and budget.project_count < budget.min_projects:
        findings.append(
            PlanFinding(
                "project_minimum_not_met",
                "conflict",
                section="projects",
                actual=budget.project_count,
                bound=budget.min_projects,
            )
        )
    if budget.max_projects is not None and budget.project_count > budget.max_projects:
        findings.append(
            PlanFinding(
                "project_maximum_exceeded",
                "conflict",
                section="projects",
                actual=budget.project_count,
                bound=budget.max_projects,
            )
        )
    for section in sections:
        for entry in section.entries:
            count = len(entry.bullet_slots)
            if budget.min_bullets_per_entry is not None and count < budget.min_bullets_per_entry:
                findings.append(
                    PlanFinding(
                        "entry_bullet_minimum_not_met",
                        "conflict",
                        section.section,
                        entry.entry_id,
                        actual=count,
                        bound=budget.min_bullets_per_entry,
                    )
                )
            if budget.max_bullets_per_entry is not None and count > budget.max_bullets_per_entry:
                findings.append(
                    PlanFinding(
                        "entry_bullet_maximum_exceeded",
                        "conflict",
                        section.section,
                        entry.entry_id,
                        actual=count,
                        bound=budget.max_bullets_per_entry,
                    )
                )
    if budget.max_total_bullets is not None and budget.bullet_slot_count > budget.max_total_bullets:
        findings.append(
            PlanFinding(
                "total_bullet_budget_exceeded",
                "conflict",
                actual=budget.bullet_slot_count,
                bound=budget.max_total_bullets,
            )
        )
    return findings


def plan_resume(
    profile: UserProfile,
    document: JobDocument,
    requirements: JobRequirements,
    selection: PlanSelection,
    *,
    requirements_reviewed: bool = False,
    selection_reviewed: bool = False,
) -> ResumePlan:
    """Recompute retrieval from source snapshots; never accept a caller-forged matching report.

    One explicitly selected eligible accomplishment reserves one bullet slot, not approved
    wording. Required entries/sections are preserved as placeholders when necessary. Conflicts
    remain visible instead of trimming content, inventing evidence or guessing relevance.
    """
    if requirements_reviewed is not True or selection_reviewed is not True:
        raise PlanningError(
            "Review the full job requirements and content selection before planning."
        )
    try:
        profile = UserProfile.model_validate(profile.model_dump(warnings=False))
        selection = PlanSelection.model_validate(selection.model_dump(warnings=False))
    except ValidationError:
        raise PlanningError(
            "Invalid planning inputs; revalidate the profile and selection."
        ) from None
    try:
        report = match_evidence(profile, document, requirements, requirements_reviewed=True)
    except MatchingError as error:
        raise PlanningError(str(error)) from None
    entries = {entry.id: entry for entry in profile.entries()}
    evidence = {item.accomplishment_id: item for item in report.evidence}
    for choice in selection.entries:
        if choice.entry_id not in entries:
            raise PlanningError("Selection references an unknown profile entry; review the IDs.")
        for reference in choice.accomplishment_ids:
            if reference not in evidence or evidence[reference].entry_id != choice.entry_id:
                raise PlanningError(
                    "Selected evidence must exist and belong to its selected entry."
                )
    selected = {choice.entry_id: choice.accomplishment_ids for choice in selection.entries}
    explicitly_selected = set(selected)
    preferences = profile.resume_preferences
    excluded = set(preferences.excluded_entry_ids)
    required_entries = set(preferences.required_entry_ids)
    findings: list[PlanFinding] = []
    for entry_id in preferences.required_entry_ids:
        if entry_id not in selected:
            selected[entry_id] = []
            findings.append(PlanFinding("required_entry_added", "review", entry_id=entry_id))
    link_lists: dict[str, list[str]] = {reference: [] for reference in evidence}
    for item in report.items:
        for candidate in item.candidates:
            link_lists[candidate.accomplishment_id].append(item.job_item_id)
    links = {reference: tuple(items) for reference, items in link_lists.items()}
    background_sections = tuple(cast(ResumeSection, name) for name in UserProfile.SECTION_PREFIXES)
    section_entries: dict[ResumeSection, list[PlannedEntry]] = {}
    entry_sections: dict[str, ResumeSection] = {
        entry.id: section for section in background_sections for entry in getattr(profile, section)
    }
    for entry_id, references in selected.items():
        section = entry_sections[entry_id]
        if entry_id in excluded:
            findings.append(PlanFinding("excluded_entry_selected", "conflict", section, entry_id))
            continue
        entry = entries[entry_id]
        slots = _bullet_slots(entry_id, references, evidence, links, findings)
        if not slots:
            findings.append(PlanFinding("metadata_only_entry", "review", section, entry_id))
        if entry.completion_status not in ("completed", "in_progress"):
            findings.append(
                PlanFinding("entry_status_requires_review", "review", section, entry_id)
            )
        section_entries.setdefault(section, []).append(
            PlannedEntry(
                entry_id,
                entry_id in required_entries,
                "user_selected" if entry_id in explicitly_selected else "required_by_preferences",
                entry.completion_status,
                slots,
            )
        )
    included_sections = (
        set(section_entries) | set(preferences.required_sections) | set(selection.include_sections)
    )
    sections = []
    all_sections: tuple[ResumeSection, ...] = (*background_sections, "skills", "coursework")
    for section in all_sections:
        if section not in included_sections:
            continue
        planned_entries = tuple(section_entries.get(section, []))
        required = section in preferences.required_sections
        if section in ("skills", "coursework"):
            findings.append(
                PlanFinding("section_requires_separate_evidence_review", "review", section)
            )
            has_content = (
                any(getattr(profile.skills, name) for name in Skills.model_fields)
                if section == "skills"
                else bool(profile.coursework)
            )
            if not has_content:
                findings.append(
                    PlanFinding("selected_section_without_content", "conflict", section)
                )
        elif required and not planned_entries:
            findings.append(
                PlanFinding("required_section_needs_entry_selection", "conflict", section)
            )
        sections.append(PlannedSection(section, required, planned_entries))
    selected_evidence = {
        slot.accomplishment_id
        for section in sections
        for entry in section.entries
        for slot in entry.bullet_slots
    }
    budget = PlanBudget(
        project_count=len(section_entries.get("projects", [])),
        bullet_slot_count=len(selected_evidence),
        min_projects=preferences.min_projects,
        max_projects=preferences.max_projects,
        min_bullets_per_entry=preferences.min_bullets_per_entry,
        max_bullets_per_entry=preferences.max_bullets_per_entry,
        max_total_bullets=selection.max_total_bullets,
    )
    findings.extend(_check_counts(budget, tuple(sections)))
    return ResumePlan(
        planning_version=PLANNING_VERSION,
        matching_version=report.matching_version,
        signals_version=report.signals_version,
        profile_model_sha256=report.profile_model_sha256,
        job_source_sha256=report.job_source_sha256,
        requirements_model_sha256=report.requirements_model_sha256,
        selection_model_sha256=sha256(selection.model_dump_json().encode("utf-8")).hexdigest(),
        requirements_reviewed=True,
        selection_reviewed=True,
        status="needs_review",
        constraint_status="conflicts"
        if any(f.severity == "conflict" for f in findings)
        else "within_count_constraints",
        sections=tuple(sections),
        job_items=tuple(
            PlanJobItem(
                item.job_item_id,
                item.section,
                item.text,
                item.source_quote,
                tuple(
                    candidate.accomplishment_id
                    for candidate in item.candidates
                    if candidate.accomplishment_id in selected_evidence
                ),
            )
            for item in report.items
        ),
        budget=budget,
        findings=tuple(findings),
        warnings=(
            "Explicit selection, not relevance ranking; "
            "lexical links do not satisfy job requirements.",
            "No lexical link does not prove missing experience or absence from the original job.",
            "All entry metadata and selected evidence need factual/context review; "
            "no wording is approved.",
            "Count budgets are not page/line budgets; "
            "readable one-page feasibility was not checked.",
        ),
    )
