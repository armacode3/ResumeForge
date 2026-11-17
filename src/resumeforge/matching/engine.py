"""Offline evidence eligibility and conservative literal candidate retrieval; no ranking."""

import re
from hashlib import sha256

from pydantic import ValidationError

from resumeforge.jobs import JobDocument, JobRequirements
from resumeforge.matching.models import (
    ConstraintFinding,
    Eligibility,
    EvidenceCandidate,
    EvidenceDecision,
    ItemMatches,
    LexicalOverlap,
    MatchingReport,
    Reason,
)
from resumeforge.profile import UserProfile
from resumeforge.profile.models import Accomplishment, ProfileEntry

MATCHING_VERSION = "evidence-matching-v1"
MAX_MATCH_PAIRS = 20_000


class MatchingError(ValueError):
    """A static, user-safe failure of matching input review, validity or limits."""


def _assess_evidence(
    item: Accomplishment, entry: ProfileEntry, excluded: set[str], required: set[str]
) -> EvidenceDecision:
    reasons: list[Reason] = []
    if entry.id in excluded:
        reasons.append("excluded_entry")
    if not item.verified:
        reasons.append("unverified_accomplishment")
    if item.completion_status == "unknown":
        reasons.append("unknown_completion")
    elif item.completion_status != "completed":
        reasons.append("unfinished_accomplishment")
    if entry.completion_status == "unknown":
        reasons.append("unknown_entry_status")
    elif entry.completion_status not in ("completed", "in_progress"):
        reasons.append("entry_status_requires_review")
    eligibility: Eligibility
    if "excluded_entry" in reasons:
        eligibility = "excluded"
    elif "unverified_accomplishment" in reasons:
        eligibility = "unverified"
    elif reasons:
        eligibility = "status_review_required"
    else:
        eligibility = "eligible_for_matching"
    return EvidenceDecision(
        accomplishment_id=item.id,
        entry_id=entry.id,
        eligibility=eligibility,
        reasons=tuple(reasons),
        completion_status=item.completion_status,
        entry_completion_status=entry.completion_status,
        required_entry=entry.id in required,
        statement=item.statement if not reasons else None,
        technologies=tuple(item.technologies) if not reasons else (),
    )


def _literal_span(needle: str, haystack: str) -> str | None:
    # Keep +/# attached to technology names: C is not C++/C#, Java is not JavaScript.
    if len(needle) > len(haystack):
        return None
    found = re.search(r"(?<![\w+#])" + re.escape(needle) + r"(?![\w+#])", haystack, re.IGNORECASE)
    return found.group() if found else None


def _overlaps(evidence: EvidenceDecision, job_text: str) -> tuple[LexicalOverlap, ...]:
    matches = []
    seen: set[str] = set()
    for technology in evidence.technologies:
        if technology.casefold() in seen:
            continue
        seen.add(technology.casefold())
        span = _literal_span(technology, job_text)
        if span is not None:
            matches.append(LexicalOverlap("technology_mention", technology, span))
    assert evidence.statement is not None
    span = _literal_span(job_text, evidence.statement)
    if span is not None:
        matches.append(LexicalOverlap("job_phrase_in_statement", span, job_text))
    return tuple(matches)


def _constraint_findings(
    profile: UserProfile, eligible: list[EvidenceDecision]
) -> tuple[ConstraintFinding, ...]:
    preferences = profile.resume_preferences
    eligible_entries = {item.entry_id for item in eligible}
    findings = []
    for entry_id in preferences.required_entry_ids:
        if entry_id not in eligible_entries:
            findings.append(ConstraintFinding("required_entry_without_eligible_evidence", entry_id))
    for section in preferences.required_sections:
        if section in ("skills", "coursework"):
            findings.append(
                ConstraintFinding("section_requires_separate_evidence_review", section=section)
            )
        elif not any(entry.id in eligible_entries for entry in getattr(profile, section)):
            findings.append(
                ConstraintFinding("required_section_without_eligible_evidence", section=section)
            )
    available_projects = sum(entry.id in eligible_entries for entry in profile.projects)
    if preferences.min_projects is not None and preferences.min_projects > available_projects:
        findings.append(ConstraintFinding("project_minimum_needs_review", section="projects"))
    return tuple(findings)


def match_evidence(
    profile: UserProfile,
    document: JobDocument,
    requirements: JobRequirements,
    *,
    requirements_reviewed: bool = False,
) -> MatchingReport:
    """Return lexical candidates only after explicit review acknowledgement and revalidation.

    Review acknowledgement is the caller's assertion, not semantic proof. Unmatched items do
    not establish missing candidate qualifications. No providers, files or notes are accessed.
    """
    if requirements_reviewed is not True:
        raise MatchingError(
            "Review the full job requirements and explicitly confirm review before matching."
        )
    try:
        profile = UserProfile.model_validate(profile.model_dump(warnings=False))
        requirements = JobRequirements.model_validate(requirements.model_dump(warnings=False))
    except ValidationError:
        raise MatchingError(
            "Invalid matching inputs; revalidate the profile and requirements."
        ) from None
    if any(fact.source_quote not in document.text for fact in requirements.facts()):
        raise MatchingError(
            "Requirements contain a quote absent from this job; review the selected inputs."
        )
    entries = {entry.id: entry for entry in profile.entries()}
    excluded = set(profile.resume_preferences.excluded_entry_ids)
    required = set(profile.resume_preferences.required_entry_ids)
    evidence = tuple(
        _assess_evidence(item, entries[item.entry_id], excluded, required)
        for item in sorted(profile.accomplishments, key=lambda item: item.id)
    )
    eligible = [item for item in evidence if item.eligibility == "eligible_for_matching"]
    if len(eligible) * len(requirements.items()) > MAX_MATCH_PAIRS:
        raise MatchingError("Matching comparison budget exceeded; reduce job items or evidence.")
    items = []
    for section in requirements.ITEM_FIELDS:
        for item in getattr(requirements, section):
            candidates = []
            for record in eligible:
                overlaps = _overlaps(record, item.text)
                if overlaps:
                    caveats = (
                        ("parent_entry_in_progress",)
                        if record.entry_completion_status == "in_progress"
                        else ()
                    )
                    candidates.append(
                        EvidenceCandidate(
                            record.accomplishment_id, record.entry_id, overlaps, caveats
                        )
                    )
            items.append(
                ItemMatches(
                    item.id,
                    section,
                    item.text,
                    item.source_quote,
                    "lexical_candidates" if candidates else "no_lexical_candidates",
                    tuple(candidates),
                )
            )
    return MatchingReport(
        matching_version=MATCHING_VERSION,
        profile_model_sha256=sha256(profile.model_dump_json().encode("utf-8")).hexdigest(),
        job_source_sha256=document.sha256,
        requirements_model_sha256=sha256(
            requirements.model_dump_json().encode("utf-8")
        ).hexdigest(),
        requirements_reviewed=True,
        evidence=evidence,
        items=tuple(items),
        findings=_constraint_findings(profile, eligible),
        warnings=(
            "Lexical candidates are not proof of qualification, entailment or factual truth; "
            "review each in context.",
            "No lexical candidate does not mean missing experience "
            "or absence from the original job.",
            "No ranking, content selection, bullet-budget allocation "
            "or layout feasibility check was performed.",
        ),
    )
