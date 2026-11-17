"""Conservative exact-text comparison against a source-grounded, human-authored reference."""

from dataclasses import dataclass

from resumeforge.jobs.models import JobAnalysis, JobRequirements
from resumeforge.jobs.source import JobDocument

EVALUATION_VERSION = "job-evaluation-v1"


class EvaluationError(ValueError):
    """A safe error for mismatched sources or ungrounded evaluation inputs."""


@dataclass(frozen=True)
class SectionScore:
    section: str
    matched: tuple[str, ...]
    missing: tuple[str, ...]
    unexpected: tuple[str, ...]
    precision: float | None
    recall: float | None


@dataclass(frozen=True)
class MetadataScore:
    field: str
    expected: str | None
    actual: str | None
    matches: bool


@dataclass(frozen=True)
class EvaluationReport:
    evaluation_version: str
    source_sha256: str
    provider: str
    model: str
    prompt_version: str
    sections: tuple[SectionScore, ...]
    metadata: tuple[MetadataScore, ...]
    matched_items: int
    expected_items: int
    actual_items: int
    precision: float | None
    recall: float | None
    exact_match: bool


def _ratio(numerator: int, denominator: int) -> float | None:
    return numerator / denominator if denominator else None


def evaluate_analysis(
    document: JobDocument, expected: JobRequirements, actual: JobAnalysis
) -> EvaluationReport:
    """Compare exact texts by section; ignore IDs/quote length, never infer semantic equivalence.

    Callers must validate schemas first. Ground both sides in this source again, so a valid but
    stale reference/result cannot be scored against a different job. A mismatch is a review
    finding, not proof the model is wrong: equivalent wording can use different literal spans.
    """
    if actual.source_sha256 != document.sha256:
        raise EvaluationError("Analysis source hash does not match the evaluation job.")
    for requirements in (expected, actual.requirements):
        if any(fact.source_quote not in document.text for fact in requirements.facts()):
            raise EvaluationError("Evaluation reference or result contains an ungrounded quote.")

    sections = []
    for name in JobRequirements.ITEM_FIELDS:
        expected_texts = {item.text for item in getattr(expected, name)}
        actual_texts = {item.text for item in getattr(actual.requirements, name)}
        matched = tuple(sorted(expected_texts & actual_texts))
        sections.append(
            SectionScore(
                section=name,
                matched=matched,
                missing=tuple(sorted(expected_texts - actual_texts)),
                unexpected=tuple(sorted(actual_texts - expected_texts)),
                precision=_ratio(len(matched), len(actual_texts)),
                recall=_ratio(len(matched), len(expected_texts)),
            )
        )
    metadata = []
    for name in ("company", "job_title"):
        expected_fact = getattr(expected, name)
        actual_fact = getattr(actual.requirements, name)
        expected_text = expected_fact.text if expected_fact is not None else None
        actual_text = actual_fact.text if actual_fact is not None else None
        metadata.append(
            MetadataScore(name, expected_text, actual_text, expected_text == actual_text)
        )

    matched_count = sum(len(section.matched) for section in sections)
    expected_count = matched_count + sum(len(section.missing) for section in sections)
    actual_count = matched_count + sum(len(section.unexpected) for section in sections)
    return EvaluationReport(
        evaluation_version=EVALUATION_VERSION,
        source_sha256=document.sha256,
        provider=actual.provider,
        model=actual.model,
        prompt_version=actual.prompt_version,
        sections=tuple(sections),
        metadata=tuple(metadata),
        matched_items=matched_count,
        expected_items=expected_count,
        actual_items=actual_count,
        precision=_ratio(matched_count, actual_count),
        recall=_ratio(matched_count, expected_count),
        exact_match=all(not section.missing and not section.unexpected for section in sections)
        and all(field.matches for field in metadata),
    )
