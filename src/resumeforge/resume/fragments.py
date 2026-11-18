"""Source sentence/clause literal absence, not inferred semantic omission or support."""

import json
import re
from hashlib import sha256

from resumeforge.resume.models import BulletReview, ResumeError, ReviewSpan, SourceFragment

FRAGMENTS_VERSION = "literal-source-fragments-v1"
MAX_BULLET_FRAGMENTS = 1024
# Keep terminal punctuation; split only before whitespace/end, or at line boundaries.
# This is deliberately not a linguistic sentence/clause parser (e.g. abbreviations split).
_BOUNDARY = re.compile(r"[.!?;](?=\s|$)|[\r\n]+")


def _digest(value: object) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return sha256(encoded.encode("utf-8")).hexdigest()


def inspect_source_fragments(
    bullet_id: str, accomplishment_id: str, source: str, draft: str
) -> tuple[SourceFragment, ...]:
    """Return trimmed source segments absent as exact substrings anywhere in this draft.

    Case/spacing/punctuation matter. Repetition counts, order, scope and meaning are not tested.
    A paraphrase can flag; text copied into a false new context can escape. Only selected source
    statements are compared. Observations require human review, not an automatic omission verdict.
    """
    spans = []
    start = 0
    for end in [match.end() for match in _BOUNDARY.finditer(source)] + [len(source)]:
        text = source[start:end]
        left = start + len(text) - len(text.lstrip())
        right = end - (len(text) - len(text.rstrip()))
        start = end
        if left < right and source[left:right] not in draft:
            spans.append(ReviewSpan(start=left, end=right, text=source[left:right]))
            if len(spans) > MAX_BULLET_FRAGMENTS:
                raise ResumeError(
                    "Bullet exceeds the source fragment limit; shorten and review again."
                )
    return tuple(
        SourceFragment(
            id=_digest(
                {
                    "version": FRAGMENTS_VERSION,
                    "bullet_id": bullet_id,
                    "accomplishment_id": accomplishment_id,
                    "source": source,
                    "draft": draft,
                    "source_span": span.model_dump(),
                }
            ),
            source_span=span,
        )
        for span in spans
    )


def fragments_digest(
    plan_sha256: str, document_sha256: str, bullets: tuple[BulletReview, ...]
) -> str:
    return _digest(
        {
            "version": FRAGMENTS_VERSION,
            "plan_sha256": plan_sha256,
            "document_sha256": document_sha256,
            "bullets": [
                {
                    "bullet_id": bullet.bullet_id,
                    "source_fragments": [f.model_dump() for f in bullet.source_fragments],
                }
                for bullet in bullets
            ],
        }
    )
