"""Local-only Ollama HTTP adapter; never downloads models or falls back to cloud."""

import json
import math
import re
from dataclasses import dataclass, field
from time import monotonic
from typing import NoReturn

import httpx
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from resumeforge.inputs import MAX_INPUT_BYTES
from resumeforge.providers.base import ProviderError, StructuredRequest

DEFAULT_MODEL = "qwen3:4b"
DEFAULT_PORT = 11434
DEFAULT_TIMEOUT = 180.0
DEFAULT_OUTPUT_TOKENS = 4096
CONTEXT_TOKENS = 16384


class _Envelope(BaseModel):
    model_config = ConfigDict(strict=True, extra="ignore", hide_input_in_errors=True)


class _Cloud(_Envelope):
    disabled: bool


class _Status(_Envelope):
    cloud: _Cloud


class _Details(_Envelope):
    format: str


class _Model(_Envelope):
    details: _Details
    capabilities: list[str]
    remote_model: str | None = None
    remote_host: str | None = None


class _Message(_Envelope):
    role: str
    content: str
    tool_calls: list[object] = Field(default_factory=list)


class _Chat(_Envelope):
    model: str
    message: _Message
    done: bool
    done_reason: str


def _validate_envelope[EnvelopeType: _Envelope](
    kind: type[EnvelopeType], data: object
) -> EnvelopeType:
    try:
        return kind.model_validate(data)
    except ValidationError:
        raise ProviderError(
            "Ollama returned an invalid API envelope; check the server version."
        ) from None


def _unique_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ProviderError("Ollama returned duplicate JSON keys.")
        result[key] = value
    return result


def _reject_constant(value: str) -> NoReturn:
    raise ProviderError("Ollama returned nonstandard JSON constants.")


def _remaining(deadline: float) -> float:
    remaining = deadline - monotonic()
    if remaining <= 0:
        raise ProviderError("Local Ollama request exceeded its deadline; reduce the input.")
    return remaining


@dataclass(frozen=True)
class OllamaProvider:
    model: str = DEFAULT_MODEL
    port: int = DEFAULT_PORT
    timeout: float = DEFAULT_TIMEOUT
    max_output_tokens: int = DEFAULT_OUTPUT_TOKENS
    transport: httpx.BaseTransport | None = field(default=None, repr=False, compare=False)

    def __post_init__(self) -> None:
        if len(self.model) > 128 or not re.fullmatch(
            r"[A-Za-z0-9][A-Za-z0-9._-]*(/[A-Za-z0-9][A-Za-z0-9._-]*)*"
            r"(:[A-Za-z0-9][A-Za-z0-9._-]*)?",
            self.model,
        ):
            raise ProviderError("Use a local Ollama model name, not a URL or filesystem path.")
        if self.model.lower().endswith((":cloud", "-cloud")):
            raise ProviderError(
                "Cloud model names are not allowed; select a downloaded local model."
            )
        if type(self.port) is not int or not 1 <= self.port <= 65535:
            raise ProviderError("Ollama port must be an integer from 1 to 65535.")
        if (
            isinstance(self.timeout, bool)
            or not math.isfinite(self.timeout)
            or not 1 <= self.timeout <= 600
        ):
            raise ProviderError("Ollama timeout must be finite and between 1 and 600 seconds.")
        if type(self.max_output_tokens) is not int or not 128 <= self.max_output_tokens <= 8192:
            raise ProviderError("Ollama output limit must be an integer from 128 to 8192 tokens.")

    @property
    def name(self) -> str:
        return "ollama"

    def _request_json(
        self,
        client: httpx.Client,
        path: str,
        deadline: float,
        payload: dict[str, object] | None = None,
    ) -> object:
        remaining = _remaining(deadline)
        timeout = httpx.Timeout(
            remaining,
            connect=min(5.0, remaining),
            write=min(5.0, remaining),
            pool=min(5.0, remaining),
        )
        with client.stream(
            "GET" if payload is None else "POST",
            f"http://127.0.0.1:{self.port}{path}",
            json=payload,
            timeout=timeout,
        ) as response:
            if response.status_code == 404 and path == "/api/status":
                raise ProviderError("Ollama lacks the local-only status API; upgrade the server.")
            if response.status_code == 404:
                raise ProviderError(
                    "Local model not found; pull the selected model manually and retry."
                )
            if response.status_code != 200:
                raise ProviderError(
                    f"Ollama request failed (HTTP {response.status_code}); "
                    "check server/model support."
                )
            if response.headers.get("content-encoding", "identity").lower() != "identity":
                raise ProviderError("Compressed Ollama responses are not supported.")
            data = bytearray()
            for chunk in response.iter_bytes(chunk_size=16384):
                _remaining(deadline)
                if len(data) + len(chunk) > MAX_INPUT_BYTES:
                    raise ProviderError("Ollama API response exceeds the 1 MiB limit.")
                data.extend(chunk)
        _remaining(deadline)
        try:
            return json.loads(
                data.decode("utf-8"),
                object_pairs_hook=_unique_keys,
                parse_constant=_reject_constant,
            )
        except ProviderError:
            raise
        except (ValueError, RecursionError):
            raise ProviderError(
                "Ollama returned malformed JSON; check the server version."
            ) from None

    def complete(self, request: StructuredRequest) -> str:
        schema = json.dumps(request.response_schema, ensure_ascii=False, separators=(",", ":"))
        system = request.instructions + "\nOutput JSON schema:\n" + schema
        try:
            budget = len(system.encode("utf-8")) + len(request.input_text.encode("utf-8"))
        except UnicodeEncodeError:
            raise ProviderError("Ollama input must contain valid UTF-8 text.") from None
        if budget + self.max_output_tokens + 1024 > CONTEXT_TOKENS:
            raise ProviderError(
                "Input/schema exceeds the conservative local context budget; shorten the input "
                "or lower --max-output-tokens. Nothing was sent."
            )
        deadline = monotonic() + self.timeout
        try:
            with httpx.Client(
                transport=self.transport,
                trust_env=False,
                follow_redirects=False,
                headers={"Accept-Encoding": "identity", "Accept": "application/json"},
            ) as client:
                status = _validate_envelope(
                    _Status, self._request_json(client, "/api/status", deadline)
                )
                if not status.cloud.disabled:
                    raise ProviderError(
                        "Ollama cloud is not disabled. Restart the server with OLLAMA_NO_CLOUD=1."
                    )
                model = _validate_envelope(
                    _Model, self._request_json(client, "/api/show", deadline, {"model": self.model})
                )
                if model.remote_host or model.remote_model or model.details.format != "gguf":
                    raise ProviderError(
                        "Selected model is not reported as a local GGUF model; no input data sent."
                    )
                if "completion" not in model.capabilities:
                    raise ProviderError("Selected local model does not support text completion.")
                result = _validate_envelope(
                    _Chat,
                    self._request_json(
                        client,
                        "/api/chat",
                        deadline,
                        {
                            "model": self.model,
                            "messages": [
                                {"role": "system", "content": system},
                                {"role": "user", "content": request.input_text},
                            ],
                            "format": request.response_schema,
                            "stream": False,
                            "think": False,
                            "keep_alive": 0,
                            "options": {
                                "temperature": 0,
                                "seed": 0,
                                "num_ctx": CONTEXT_TOKENS,
                                "num_predict": self.max_output_tokens,
                            },
                        },
                    ),
                )
        except httpx.TimeoutException:
            raise ProviderError(
                "Local Ollama request timed out; reduce the input/output or adjust --timeout."
            ) from None
        except httpx.HTTPError:
            raise ProviderError(
                "Cannot communicate with local Ollama; "
                "start its loopback server and check the port."
            ) from None
        if not result.done or result.done_reason != "stop":
            raise ProviderError(
                "Ollama output was unfinished/truncated; reduce input or raise --max-output-tokens."
            )
        if (
            result.model != self.model
            or result.message.role != "assistant"
            or result.message.tool_calls
            or not result.message.content.strip()
        ):
            raise ProviderError("Ollama returned an unexpected model/message or requested tools.")
        return result.message.content
