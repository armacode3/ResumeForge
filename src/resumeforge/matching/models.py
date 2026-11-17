"""Deterministic retrieval findings, not semantic qualification or resume approval."""

from dataclasses import dataclass
from typing import Literal

from resumeforge.profile.models import CompletionStatus

Eligibility = Literal["eligible_for_matching", "excluded", "unverified", "status_review_required"]
Reason = Literal[
    "excluded_entry",
    "unverified_accomplishment",
    "unknown_completion",
    "unfinished_accomplishment",
    "unknown_entry_status",
    "entry_status_requires_review",
]


@dataclass(frozen=True)
class EvidenceDecision:
    accomplishment_id: str
    entry_id: str
    eligibility: Eligibility
    reasons: tuple[Reason, ...]
    completion_status: CompletionStatus
    entry_completion_status: CompletionStatus
    required_entry: bool
    statement: str | None
    technologies: tuple[str, ...]


@dataclass(frozen=True)
class LexicalOverlap:
    basis: Literal["technology_mention", "job_phrase_in_statement"]
    evidence_text: str
    job_text: str


@dataclass(frozen=True)
class TechnologySignal:
    """A retrieved technology's literal spans, not proof that it was used."""

    technology: str
    job_span: str
    statement_span: str | None


@dataclass(frozen=True)
class MetricSignal:
    """An explicitly recorded scoped metric; no numeric extraction or job alignment."""

    text: str
    statement_span: str | None


@dataclass(frozen=True)
class RelevanceSignals:
    """Unweighted review observations; absence means unknown, not weaker experience."""

    job_phrase_in_statement: bool
    technologies: tuple[TechnologySignal, ...]
    metrics: tuple[MetricSignal, ...]


@dataclass(frozen=True)
class EvidenceCandidate:
    accomplishment_id: str
    entry_id: str
    overlaps: tuple[LexicalOverlap, ...]
    caveats: tuple[str, ...]
    signals: RelevanceSignals


@dataclass(frozen=True)
class ItemMatches:
    job_item_id: str
    section: str
    text: str
    source_quote: str
    status: Literal["lexical_candidates", "no_lexical_candidates"]
    candidates: tuple[EvidenceCandidate, ...]


@dataclass(frozen=True)
class ConstraintFinding:
    code: Literal[
        "required_entry_without_eligible_evidence",
        "required_section_without_eligible_evidence",
        "section_requires_separate_evidence_review",
        "project_minimum_needs_review",
    ]
    entry_id: str | None = None
    section: str | None = None


@dataclass(frozen=True)
class MatchingReport:
    matching_version: str
    signals_version: str
    profile_model_sha256: str
    job_source_sha256: str
    requirements_model_sha256: str
    requirements_reviewed: bool
    evidence: tuple[EvidenceDecision, ...]
    items: tuple[ItemMatches, ...]
    findings: tuple[ConstraintFinding, ...]
    warnings: tuple[str, ...]
