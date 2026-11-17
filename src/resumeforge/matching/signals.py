"""Annotate already-retrieved candidates without scoring, ranking or approving claims."""

from resumeforge.matching.literals import literal_span
from resumeforge.matching.models import (
    LexicalOverlap,
    MetricSignal,
    RelevanceSignals,
    TechnologySignal,
)
from resumeforge.profile.models import Accomplishment

SIGNALS_VERSION = "evidence-signals-v1"


def relevance_signals(
    accomplishment: Accomplishment, overlaps: tuple[LexicalOverlap, ...]
) -> RelevanceSignals:
    """Use only the revalidated eligible accomplishment and existing retrieval anchors.

    A statement mention may be negated/incidental. A metric is merely recorded on this
    accomplishment; it is not necessarily numeric, mentioned in the statement or job-relevant.
    Never infer technologies, metrics, responsibility, ownership or comparative quality.
    """
    return RelevanceSignals(
        job_phrase_in_statement=any(
            overlap.basis == "job_phrase_in_statement" for overlap in overlaps
        ),
        technologies=tuple(
            TechnologySignal(
                technology=overlap.evidence_text,
                job_span=overlap.job_text,
                statement_span=literal_span(overlap.evidence_text, accomplishment.statement),
            )
            for overlap in overlaps
            if overlap.basis == "technology_mention"
        ),
        metrics=tuple(
            MetricSignal(text=metric, statement_span=literal_span(metric, accomplishment.statement))
            for metric in accomplishment.metrics
        ),
    )
