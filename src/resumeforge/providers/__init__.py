"""Provider contracts, offline replay, and guarded local inference."""

from resumeforge.providers.base import ProviderError, StructuredOutputProvider, StructuredRequest
from resumeforge.providers.fake import FakeProvider
from resumeforge.providers.ollama import OllamaProvider

__all__ = [
    "FakeProvider",
    "OllamaProvider",
    "ProviderError",
    "StructuredOutputProvider",
    "StructuredRequest",
]
