"""Bounded local text input shared by job files and offline response fixtures."""

from pathlib import Path

MAX_INPUT_BYTES = 1_048_576


class InputError(ValueError):
    """An input error that does not disclose file contents or system exception details."""


def read_utf8_file(path: Path, *, label: str) -> str:
    """Read a regular UTF-8 file without newline normalization or remote access."""
    try:
        if not path.is_file():
            raise InputError(f"{label} must point to an existing regular file.")
        with path.open("rb") as handle:
            data = handle.read(MAX_INPUT_BYTES + 1)
    except OSError:
        raise InputError(f"Unable to read {label}; check permissions and availability.") from None
    if len(data) > MAX_INPUT_BYTES:
        raise InputError(f"{label} exceeds {MAX_INPUT_BYTES} bytes; shorten the input.")
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        raise InputError(f"{label} must be a UTF-8 encoded text file.") from None
