"""Finite literal observations over selected statements only, never claim-support verdicts."""

import json
import re
from hashlib import sha256

from resumeforge.resume.models import BulletReview, ClaimFinding, ResumeError, ReviewSpan

FINDINGS_VERSION = "literal-claim-findings-v1"
MAX_BULLET_FINDINGS = 1024

# ASCII digits, punctuation inside a numeric run, optional percent/magnitude suffix.
# Deliberately no arithmetic, unit, polarity, context, or semantic equivalence analysis.
_NUMERIC = re.compile(r"[0-9]+(?:[.,][0-9]+)*(?:%|[kKmMbB](?!\w))?")
CAVEAT_CUES = (
    "not",
    "never",
    "only",
    "assisted",
    "supported",
    "contributed",
    "under supervision",
    "under mentor review",
    "under a mentor's review",
    "prototype",
    "experimental",
    "approximately",
    "up to",
    "in progress",
)
_CUES = tuple(
    (cue, re.compile(r"\b" + r"\s+".join(cue.split()) + r"\b", re.IGNORECASE))
    for cue in CAVEAT_CUES
)


def _digest(value: object) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return sha256(encoded.encode("utf-8")).hexdigest()


def _span(match: re.Match[str]) -> ReviewSpan:
    return ReviewSpan(start=match.start(), end=match.end(), text=match.group())


def inspect_claims(
    bullet_id: str, accomplishment_id: str, source: str, draft: str
) -> tuple[ClaimFinding, ...]:
    """Return numeric occurrences, then missing cue occurrences in source-offset order.

    Token membership ignores occurrence counts and location. A retained cue anywhere in the
    draft suppresses that cue's findings, even in negated or unrelated context. No other profile
    fields, metrics, parent skills, historical wording or job requirements supply claim evidence.
    """
    observations: list[tuple[str, str | None, ReviewSpan | None, ReviewSpan | None]] = []
    source_numbers = {match.group() for match in _NUMERIC.finditer(source)}
    observations.extend(
        ("numeric_token_absent_from_source", None, None, _span(match))
        for match in _NUMERIC.finditer(draft)
        if match.group() not in source_numbers
    )
    missing_cues = sorted(
        (
            (match.start(), cue, _span(match))
            for cue, pattern in _CUES
            if pattern.search(draft) is None
            for match in pattern.finditer(source)
        ),
        key=lambda item: (item[0], item[1]),
    )
    observations.extend(
        ("source_caveat_cue_not_retained", cue, span, None) for _, cue, span in missing_cues
    )
    if len(observations) > MAX_BULLET_FINDINGS:
        raise ResumeError(
            "Bullet exceeds the literal finding limit; shorten wording and review again."
        )
    findings = []
    for code, cue, source_span, draft_span in observations:
        payload = {
            "version": FINDINGS_VERSION,
            "bullet_id": bullet_id,
            "accomplishment_id": accomplishment_id,
            "source": source,
            "draft": draft,
            "code": code,
            "cue": cue,
            "source_span": source_span.model_dump() if source_span else None,
            "draft_span": draft_span.model_dump() if draft_span else None,
        }
        findings.append(
            ClaimFinding.model_validate(
                {
                    "id": _digest(payload),
                    "code": code,
                    "cue": cue,
                    "source_span": source_span,
                    "draft_span": draft_span,
                }
            )
        )
    return tuple(findings)


def findings_digest(
    plan_sha256: str, document_sha256: str, bullets: tuple[BulletReview, ...]
) -> str:
    return _digest(
        {
            "version": FINDINGS_VERSION,
            "plan_sha256": plan_sha256,
            "document_sha256": document_sha256,
            "bullets": [
                {
                    "bullet_id": bullet.bullet_id,
                    "findings": [finding.model_dump() for finding in bullet.findings],
                }
                for bullet in bullets
            ],
        }
    )
