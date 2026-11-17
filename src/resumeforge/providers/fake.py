"""Explicit offline replay, not a heuristic extractor or an actual language model."""

from dataclasses import dataclass
from pathlib import Path

from resumeforge.inputs import read_utf8_file
from resumeforge.providers.base import StructuredRequest


@dataclass(frozen=True)
class FakeProvider:
    response_json: str

    @property
    def name(self) -> str:
        return "fake"

    @property
    def model(self) -> str:
        return "fixture-v1"

    @classmethod
    def from_file(cls, path: Path) -> "FakeProvider":
        return cls(read_utf8_file(path, label="Mock response"))

    def complete(self, request: StructuredRequest) -> str:
        """Return the supplied fixture unchanged; do not infer, log or persist anything."""
        return self.response_json
