"""Bounded draft, decision and wording JSON with strict schema and nesting checks."""

import json
from pathlib import Path
from typing import NoReturn

from resumeforge.inputs import MAX_INPUT_BYTES, read_utf8_file
from resumeforge.resume.models import (
    ResumeDocument,
    ResumeError,
    ResumeModel,
    ReviewDecisions,
    WordingResponse,
)


def _unique_object(pairs: list[tuple[str, object]], label: str) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ResumeError(f"{label} contains duplicate JSON keys; use unique keys.")
        result[key] = value
    return result


def _reject_constant(value: str, label: str) -> NoReturn:
    raise ResumeError(f"{label} contains a nonstandard JSON numeric constant.")


def _parse_resume_model[Model: ResumeModel](text: str, model: type[Model], *, label: str) -> Model:
    try:
        size = len(text.encode("utf-8"))
    except UnicodeEncodeError:
        raise ResumeError(f"{label} must contain valid UTF-8 text.") from None
    if size > MAX_INPUT_BYTES:
        raise ResumeError(f"{label} exceeds the input byte limit; shorten the input.")
    try:
        data = json.loads(
            text.removeprefix("\ufeff"),
            object_pairs_hook=lambda pairs: _unique_object(pairs, label),
            parse_constant=lambda value: _reject_constant(value, label),
        )
    except ResumeError:
        raise
    except (ValueError, RecursionError):
        raise ResumeError(
            f"Invalid {label.lower()} JSON; supply one bounded JSON object."
        ) from None
    pending: list[tuple[object, int]] = [(data, 1)]
    while pending:
        value, depth = pending.pop()
        if isinstance(value, (dict, list)):
            if depth > 32:
                raise ResumeError(f"{label} JSON nesting is excessive; simplify the input.")
            children = value.values() if isinstance(value, dict) else value
            pending.extend((child, depth + 1) for child in children)
    try:
        # JSON mode accepts JSON arrays as immutable tuples while keeping scalar types strict.
        document = model.model_validate_json(json.dumps(data))
        document.model_dump_json().encode("utf-8", errors="strict")
        return document
    except ValueError:
        raise ResumeError(f"Invalid {label.lower()} fields; check the versioned format.") from None


def parse_resume_document(text: str) -> ResumeDocument:
    return _parse_resume_model(text, ResumeDocument, label="Draft")


def load_resume_document(path: Path) -> ResumeDocument:
    return parse_resume_document(read_utf8_file(path, label="Resume draft"))


def parse_review_decisions(text: str) -> ReviewDecisions:
    return _parse_resume_model(text, ReviewDecisions, label="Review decisions")


def load_review_decisions(path: Path) -> ReviewDecisions:
    return parse_review_decisions(read_utf8_file(path, label="Review decisions"))


def parse_wording_response(text: str) -> WordingResponse:
    if not isinstance(text, str):
        raise ResumeError("Wording provider must return a JSON string.")
    return _parse_resume_model(text, WordingResponse, label="Wording response")
