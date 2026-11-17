"""Provider contracts and deterministic offline testing adapter."""

from resumeforge.providers.base import StructuredOutputProvider, StructuredRequest
from resumeforge.providers.fake import FakeProvider

__all__ = ["FakeProvider", "StructuredOutputProvider", "StructuredRequest"]
