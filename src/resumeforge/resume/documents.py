"""Bounded draft JSON with duplicate-key, depth and strict-schema checks."""

import json
from pathlib import Path
from typing import NoReturn

from resumeforge.inputs import MAX_INPUT_BYTES, read_utf8_file
from resumeforge.resume.models import ResumeDocument, ResumeError


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ResumeError("Draft contains duplicate JSON keys; use unique keys.")
        result[key] = value
    return result


def _reject_constant(value: str) -> NoReturn:
    raise ResumeError("Draft contains a nonstandard JSON numeric constant.")


def parse_resume_document(text: str) -> ResumeDocument:
    try:
        size = len(text.encode("utf-8"))
    except UnicodeEncodeError:
        raise ResumeError("Draft must contain valid UTF-8 text.") from None
    if size > MAX_INPUT_BYTES:
        raise ResumeError("Draft exceeds the input byte limit; shorten the input.")
    try:
        data = json.loads(
            text.removeprefix("\ufeff"),
            object_pairs_hook=_unique_object,
            parse_constant=_reject_constant,
        )
    except ResumeError:
        raise
    except (ValueError, RecursionError):
        raise ResumeError("Invalid draft JSON; supply one bounded JSON object.") from None
    pending: list[tuple[object, int]] = [(data, 1)]
    while pending:
        value, depth = pending.pop()
        if isinstance(value, (dict, list)):
            if depth > 32:
                raise ResumeError("Draft JSON nesting is excessive; simplify the input.")
            children = value.values() if isinstance(value, dict) else value
            pending.extend((child, depth + 1) for child in children)
    try:
        # JSON mode accepts JSON arrays as immutable tuples while keeping scalar types strict.
        document = ResumeDocument.model_validate_json(json.dumps(data))
        document.model_dump_json().encode("utf-8", errors="strict")
        return document
    except ValueError:
        raise ResumeError("Invalid draft fields; check the versioned draft format.") from None


def load_resume_document(path: Path) -> ResumeDocument:
    return parse_resume_document(read_utf8_file(path, label="Resume draft"))
