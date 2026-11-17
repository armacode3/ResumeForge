"""Deterministic evidence retrieval, independent of presentation and provider interfaces."""

from resumeforge.matching.engine import MatchingError, match_evidence
from resumeforge.matching.models import MatchingReport

__all__ = ["MatchingError", "MatchingReport", "match_evidence"]
