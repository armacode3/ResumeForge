"""Mocked HTTP tests for local-only guards, response limits and structured requests."""

import json
from typing import Any
from unittest.mock import patch

import httpx
import pytest

from resumeforge.inputs import MAX_INPUT_BYTES
from resumeforge.jobs import JobAnalysisError, JobDocument, analyze_job
from resumeforge.providers import OllamaProvider, ProviderError, StructuredRequest
from resumeforge.providers.ollama import CONTEXT_TOKENS


@pytest.fixture
def api_payloads(job_payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "/api/status": {"cloud": {"disabled": True, "source": "env"}},
        "/api/show": {"details": {"format": "gguf"}, "capabilities": ["completion", "thinking"]},
        "/api/chat": {
            "model": "qwen3:4b",
            "done": True,
            "done_reason": "stop",
            "message": {"role": "assistant", "content": json.dumps(job_payload)},
        },
    }


@pytest.fixture
def requests() -> list[httpx.Request]:
    return []


@pytest.fixture
def transport(api_payloads: dict[str, Any], requests: list[httpx.Request]) -> httpx.MockTransport:
    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json=api_payloads[request.url.path])

    return httpx.MockTransport(handler)


def test_success_keeps_schema_instructions_data_and_provenance_separate(
    job_text: str,
    transport: httpx.MockTransport,
    requests: list[httpx.Request],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("HTTP_PROXY", "http://example.invalid:9999")
    monkeypatch.setenv("OLLAMA_HOST", "https://example.invalid")
    result = analyze_job(JobDocument(job_text), OllamaProvider(port=11435, transport=transport))

    assert result.provider == "ollama"
    assert result.model == "qwen3:4b"
    assert [request.url.path for request in requests] == ["/api/status", "/api/show", "/api/chat"]
    assert all(
        request.url.host == "127.0.0.1" and request.url.port == 11435 for request in requests
    )
    assert requests[0].method == "GET"
    assert requests[0].content == b""
    assert json.loads(requests[1].content) == {"model": "qwen3:4b"}
    payload = json.loads(requests[2].content)
    assert payload["messages"][1] == {"role": "user", "content": job_text}
    assert "Output JSON schema:" in payload["messages"][0]["content"]
    assert payload["format"]["type"] == "object"
    assert payload["stream"] is False
    assert payload["think"] is False
    assert payload["keep_alive"] == 0
    assert payload["options"] == {
        "temperature": 0,
        "seed": 0,
        "num_ctx": CONTEXT_TOKENS,
        "num_predict": 4096,
    }
    assert "tools" not in payload
    assert requests[2].extensions["timeout"]["connect"] <= 5
    assert requests[2].headers["accept-encoding"] == "identity"


@pytest.mark.parametrize("disabled", [False, 1, "true", None])
def test_cloud_guard_fails_before_model_lookup_or_job_transmission(
    disabled: object,
    api_payloads: dict[str, Any],
    transport: httpx.MockTransport,
    requests: list[httpx.Request],
) -> None:
    api_payloads["/api/status"]["cloud"]["disabled"] = disabled
    with pytest.raises(ProviderError):
        OllamaProvider(transport=transport).complete(StructuredRequest("Rules", "Private job", {}))
    assert len(requests) == 1
    assert requests[0].content == b""


@pytest.mark.parametrize(
    ("field", "value"),
    [("remote_host", "https://example.invalid"), ("remote_model", "remote-alias")],
)
def test_cloud_alias_metadata_fails_before_job_transmission(
    field: str,
    value: str,
    api_payloads: dict[str, Any],
    transport: httpx.MockTransport,
    requests: list[httpx.Request],
) -> None:
    api_payloads["/api/show"][field] = value
    with pytest.raises(ProviderError, match="local GGUF"):
        OllamaProvider(transport=transport).complete(StructuredRequest("Rules", "Private job", {}))
    assert len(requests) == 2
    assert all(b"Private job" not in request.content for request in requests)


@pytest.mark.parametrize(
    "model", ["", "../model", "https://host/model", "a b", "a" * 129, "x:cloud", "x:4b-cloud"]
)
def test_invalid_or_cloud_model_names_fail_before_http(model: str) -> None:
    with pytest.raises(ProviderError):
        OllamaProvider(model=model)


@pytest.mark.parametrize("port", [0, -1, 65536, True])
def test_invalid_ports(port: int) -> None:
    with pytest.raises(ProviderError, match="port"):
        OllamaProvider(port=port)


@pytest.mark.parametrize("timeout", [0.0, 601.0, float("nan"), float("inf"), True])
def test_invalid_timeouts(timeout: float) -> None:
    with pytest.raises(ProviderError, match="timeout"):
        OllamaProvider(timeout=timeout)


@pytest.mark.parametrize("tokens", [0, 127, 8193, True])
def test_invalid_output_limits(tokens: int) -> None:
    with pytest.raises(ProviderError, match="output limit"):
        OllamaProvider(max_output_tokens=tokens)


@pytest.mark.parametrize("change", ["format", "capabilities", "missing"])
def test_unsupported_model_metadata_fails_closed(
    change: str,
    api_payloads: dict[str, Any],
    transport: httpx.MockTransport,
    requests: list[httpx.Request],
) -> None:
    if change == "missing":
        api_payloads["/api/show"] = {}
    elif change == "format":
        api_payloads["/api/show"]["details"]["format"] = "remote"
    else:
        api_payloads["/api/show"]["capabilities"] = []
    with pytest.raises(ProviderError):
        OllamaProvider(transport=transport).complete(StructuredRequest("Rules", "Private job", {}))
    assert len(requests) == 2


@pytest.mark.parametrize(
    ("status", "path", "message"),
    [
        (404, "/api/status", "upgrade"),
        (404, "/api/show", "pull"),
        (500, "/api/chat", "HTTP 500"),
        (302, "/api/status", "HTTP 302"),
    ],
)
def test_http_errors_are_sanitized_and_redirects_are_not_followed(
    status: int,
    path: str,
    message: str,
    api_payloads: dict[str, Any],
) -> None:
    seen: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request.url.path)
        if request.url.path == path:
            return httpx.Response(
                status,
                text="fictional-private-error",
                headers={"Location": "https://example.invalid"},
            )
        return httpx.Response(200, json=api_payloads[request.url.path])

    with pytest.raises(ProviderError, match=message) as error:
        OllamaProvider(transport=httpx.MockTransport(handler)).complete(
            StructuredRequest("Rules", "Job", {})
        )
    assert "fictional-private-error" not in str(error.value)
    assert seen[-1] == path
    assert len(seen) == ["/api/status", "/api/show", "/api/chat"].index(path) + 1


@pytest.mark.parametrize("failure", [httpx.ReadTimeout, httpx.ConnectError])
def test_transport_errors_are_sanitized_without_retry(failure: type[httpx.HTTPError]) -> None:
    seen = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        raise failure("fictional-private-transport-details")

    with pytest.raises(ProviderError) as error:
        OllamaProvider(transport=httpx.MockTransport(handler)).complete(
            StructuredRequest("Rules", "Job", {})
        )
    assert "fictional-private" not in str(error.value)
    assert len(seen) == 1


@pytest.mark.parametrize(
    "body",
    [
        b"not JSON",
        b"\xff",
        b'{"cloud":{"disabled":false,"disabled":true}}',
        b'{"cloud":{"disabled":NaN}}',
        b"[" * 5000 + b"0" + b"]" * 5000,
    ],
)
def test_invalid_outer_json_is_rejected(body: bytes) -> None:
    transport = httpx.MockTransport(lambda request: httpx.Response(200, content=body))
    with pytest.raises(ProviderError):
        OllamaProvider(transport=transport).complete(StructuredRequest("Rules", "Job", {}))


def test_oversized_outer_response_is_rejected() -> None:
    transport = httpx.MockTransport(
        lambda request: httpx.Response(200, content=b"x" * (MAX_INPUT_BYTES + 1))
    )
    with pytest.raises(ProviderError, match="1 MiB"):
        OllamaProvider(transport=transport).complete(StructuredRequest("Rules", "Job", {}))


def test_compressed_responses_fail_without_decompression() -> None:
    transport = httpx.MockTransport(
        lambda request: httpx.Response(
            200, headers={"Content-Encoding": "gzip"}, stream=httpx.ByteStream(b"not-a-gzip-body")
        )
    )
    with pytest.raises(ProviderError, match="Compressed"):
        OllamaProvider(transport=transport).complete(StructuredRequest("Rules", "Job", {}))


@pytest.mark.parametrize("text", ["x" * CONTEXT_TOKENS, "\ud800"])
def test_context_and_encoding_guards_run_before_http(text: str) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise AssertionError("Input guard must run before contacting Ollama")

    with pytest.raises(ProviderError):
        OllamaProvider(transport=httpx.MockTransport(handler)).complete(
            StructuredRequest("Rules", text, {})
        )


def test_shared_deadline_stops_between_calls(monkeypatch: pytest.MonkeyPatch) -> None:
    clock = [0.0]
    monkeypatch.setattr("resumeforge.providers.ollama.monotonic", lambda: clock[0])

    def handler(request: httpx.Request) -> httpx.Response:
        clock[0] = 181.0
        return httpx.Response(200, json={"cloud": {"disabled": True}})

    with pytest.raises(ProviderError, match="deadline"):
        OllamaProvider(transport=httpx.MockTransport(handler)).complete(
            StructuredRequest("Rules", "Job", {})
        )


@pytest.mark.parametrize("change", ["done", "length", "model", "role", "tools", "empty"])
def test_truncated_tool_or_unexpected_responses_fail_closed(
    change: str,
    api_payloads: dict[str, Any],
    transport: httpx.MockTransport,
) -> None:
    chat = api_payloads["/api/chat"]
    if change == "done":
        chat["done"] = False
    elif change == "length":
        chat["done_reason"] = "length"
    elif change == "model":
        chat["model"] = "different-model"
    elif change == "role":
        chat["message"]["role"] = "tool"
    elif change == "tools":
        chat["message"]["tool_calls"] = [{"function": {"name": "read_private_file"}}]
    else:
        chat["message"]["content"] = "  "
    with pytest.raises(ProviderError):
        OllamaProvider(transport=transport).complete(StructuredRequest("Rules", "Job", {}))


def test_model_thinking_is_not_returned(
    api_payloads: dict[str, Any],
    transport: httpx.MockTransport,
) -> None:
    api_payloads["/api/chat"]["message"]["thinking"] = "fictional-private-thinking"
    result = OllamaProvider(transport=transport).complete(StructuredRequest("Rules", "Job", {}))
    assert "fictional-private-thinking" not in result


def test_http_client_cannot_use_environment_proxies_or_redirects(
    transport: httpx.MockTransport,
) -> None:
    with patch("resumeforge.providers.ollama.httpx.Client", wraps=httpx.Client) as client_factory:
        OllamaProvider(transport=transport).complete(StructuredRequest("Rules", "Job", {}))
    assert client_factory.call_args.kwargs["trust_env"] is False
    assert client_factory.call_args.kwargs["follow_redirects"] is False


def test_inner_job_output_still_uses_existing_validator(
    job_text: str,
    api_payloads: dict[str, Any],
    transport: httpx.MockTransport,
) -> None:
    api_payloads["/api/chat"]["message"]["content"] = "{}"
    with pytest.raises(JobAnalysisError, match="Invalid job requirements"):
        analyze_job(JobDocument(job_text), OllamaProvider(transport=transport))
