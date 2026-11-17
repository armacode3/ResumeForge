"""Local job text with exact-source identity, independent of profile information."""

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path

from resumeforge.inputs import MAX_INPUT_BYTES, InputError, read_utf8_file


@dataclass(frozen=True)
class JobDocument:
    text: str

    def __post_init__(self) -> None:
        try:
            size = len(self.text.encode("utf-8"))
        except UnicodeEncodeError:
            raise InputError("Job description must contain valid UTF-8 text.") from None
        if size > MAX_INPUT_BYTES:
            raise InputError(f"Job description exceeds {MAX_INPUT_BYTES} bytes.")
        if not self.text.removeprefix("\ufeff").strip():
            raise InputError("Job description is empty; supply nonblank text or Markdown.")
        if "\x00" in self.text:
            raise InputError("Job description contains NUL bytes; supply text, not a binary file.")

    @property
    def sha256(self) -> str:
        return sha256(self.text.encode("utf-8")).hexdigest()


def load_job(path: Path) -> JobDocument:
    return JobDocument(read_utf8_file(path, label="Job description"))
