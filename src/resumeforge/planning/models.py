"""Reviewed selection inputs and immutable, unapproved content-plan snapshots."""

from dataclasses import dataclass
from typing import Annotated, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from resumeforge.profile.models import (
    AccomplishmentId,
    CompletionStatus,
    ContentCount,
    EntryId,
    ResumeSection,
)


class PlanningError(ValueError):
    """A static, safe input or provenance failure; never a raw validation dump."""


class SelectionModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, hide_input_in_errors=True)


class EntrySelection(SelectionModel):
    entry_id: EntryId
    accomplishment_ids: list[AccomplishmentId]

    @model_validator(mode="after")
    def distinct_evidence(self) -> Self:
        if len(set(self.accomplishment_ids)) != len(self.accomplishment_ids):
            raise ValueError("Each evidence reference must be distinct.")
        return self


class PlanSelection(SelectionModel):
    schema_version: Annotated[int, Field(ge=1, le=1)]
    entries: list[EntrySelection]
    include_sections: list[Literal["skills", "coursework"]] = Field(default_factory=list)
    max_total_bullets: ContentCount | None = None

    @model_validator(mode="after")
    def distinct_content(self) -> Self:
        if len({entry.entry_id for entry in self.entries}) != len(self.entries):
            raise ValueError("Each selected entry must be distinct.")
        if len(set(self.include_sections)) != len(self.include_sections):
            raise ValueError("Each selected section must be distinct.")
        return self


@dataclass(frozen=True)
class BulletSlot:
    accomplishment_id: str
    statement: str
    job_item_ids: tuple[str, ...]
    caveats: tuple[str, ...]


@dataclass(frozen=True)
class PlannedEntry:
    entry_id: str
    required: bool
    selection_reason: Literal["user_selected", "required_by_preferences"]
    completion_status: CompletionStatus
    bullet_slots: tuple[BulletSlot, ...]


@dataclass(frozen=True)
class PlannedSection:
    section: ResumeSection
    required: bool
    entries: tuple[PlannedEntry, ...]


@dataclass(frozen=True)
class PlanFinding:
    code: Literal[
        "excluded_entry_selected",
        "selected_evidence_ineligible",
        "selected_evidence_without_lexical_link",
        "required_entry_added",
        "required_section_needs_entry_selection",
        "section_requires_separate_evidence_review",
        "selected_section_without_content",
        "metadata_only_entry",
        "entry_status_requires_review",
        "project_minimum_not_met",
        "project_maximum_exceeded",
        "entry_bullet_minimum_not_met",
        "entry_bullet_maximum_exceeded",
        "total_bullet_budget_exceeded",
    ]
    severity: Literal["conflict", "review"]
    section: ResumeSection | None = None
    entry_id: str | None = None
    accomplishment_id: str | None = None
    actual: int | None = None
    bound: int | None = None


@dataclass(frozen=True)
class PlanJobItem:
    job_item_id: str
    section: str
    text: str
    source_quote: str
    selected_accomplishment_ids: tuple[str, ...]


@dataclass(frozen=True)
class PlanBudget:
    project_count: int
    bullet_slot_count: int
    min_projects: int | None
    max_projects: int | None
    min_bullets_per_entry: int | None
    max_bullets_per_entry: int | None
    max_total_bullets: int | None


@dataclass(frozen=True)
class ResumePlan:
    planning_version: str
    matching_version: str
    signals_version: str
    profile_model_sha256: str
    job_source_sha256: str
    requirements_model_sha256: str
    selection_model_sha256: str
    requirements_reviewed: bool
    selection_reviewed: bool
    status: Literal["needs_review"]
    constraint_status: Literal["conflicts", "within_count_constraints"]
    sections: tuple[PlannedSection, ...]
    job_items: tuple[PlanJobItem, ...]
    budget: PlanBudget
    findings: tuple[PlanFinding, ...]
    warnings: tuple[str, ...]
