"""Small structured-output boundary; no SDK, credentials, tools or network configuration."""

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class StructuredRequest:
    instructions: str
    input_text: str
    response_schema: dict[str, object]


class StructuredOutputProvider(Protocol):
    """Adapters receive instructions separately from untrusted input and return raw JSON."""

    @property
    def name(self) -> str: ...

    @property
    def model(self) -> str: ...

    def complete(self, request: StructuredRequest) -> str: ...
