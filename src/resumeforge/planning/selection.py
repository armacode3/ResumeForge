"""Bounded, strict local selection JSON, not instructions embedded in source documents."""

import json
from pathlib import Path
from typing import NoReturn

from pydantic import ValidationError

from resumeforge.inputs import MAX_INPUT_BYTES, read_utf8_file
from resumeforge.planning.models import PlanningError, PlanSelection


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise PlanningError("Selection contains duplicate JSON keys; use unique keys.")
        result[key] = value
    return result


def _reject_constant(value: str) -> NoReturn:
    raise PlanningError("Selection contains a nonstandard JSON numeric constant.")


def parse_selection(text: str) -> PlanSelection:
    """Validate one versioned selection without disclosing private values on failure."""
    try:
        size = len(text.encode("utf-8"))
    except UnicodeEncodeError:
        raise PlanningError("Selection must contain valid UTF-8 text.") from None
    if size > MAX_INPUT_BYTES:
        raise PlanningError("Selection exceeds the input byte limit; shorten the input.")
    try:
        data = json.loads(
            text.removeprefix("\ufeff"),
            object_pairs_hook=_unique_object,
            parse_constant=_reject_constant,
        )
    except PlanningError:
        raise
    except (ValueError, RecursionError):
        raise PlanningError("Invalid selection JSON; supply one bounded JSON object.") from None
    pending: list[tuple[object, int]] = [(data, 1)]
    while pending:
        value, depth = pending.pop()
        if isinstance(value, (dict, list)):
            if depth > 32:
                raise PlanningError("Selection JSON nesting is excessive; simplify the input.")
            children = value.values() if isinstance(value, dict) else value
            pending.extend((child, depth + 1) for child in children)
    try:
        return PlanSelection.model_validate(data)
    except ValidationError:
        raise PlanningError(
            "Invalid selection fields; check the versioned selection format."
        ) from None


def load_selection(path: Path) -> PlanSelection:
    return parse_selection(read_utf8_file(path, label="Plan selection"))
