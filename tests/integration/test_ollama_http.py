"""Real loopback HTTP against a synthetic stub, never a live language model."""

import json
import subprocess
import sys
from collections.abc import Iterator
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from typing import Any

import pytest

from resumeforge.jobs import JobAnalysis

pytestmark = pytest.mark.integration


@pytest.fixture
def local_api(job_payload: dict[str, Any]) -> Iterator[tuple[int, list[tuple[str, object]]]]:
    calls: list[tuple[str, object]] = []

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, format: str, *args: object) -> None:
            pass

        def reply(self, body: object) -> None:
            data = json.dumps(body).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self) -> None:
            calls.append((self.path, None))
            self.reply({"cloud": {"disabled": True}})

        def do_POST(self) -> None:
            payload = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            calls.append((self.path, payload))
            if self.path == "/api/show":
                self.reply({"details": {"format": "gguf"}, "capabilities": ["completion"]})
            else:
                self.reply(
                    {
                        "model": "qwen3:4b",
                        "done": True,
                        "done_reason": "stop",
                        "message": {"role": "assistant", "content": json.dumps(job_payload)},
                    }
                )

    with ThreadingHTTPServer(("127.0.0.1", 0), Handler) as server:
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            yield server.server_port, calls
        finally:
            server.shutdown()
            thread.join(timeout=5)


def test_installed_cli_uses_local_http_not_a_model_or_profile(
    local_api: tuple[int, list[tuple[str, object]]],
    job_path: Path,
    tmp_path: Path,
) -> None:
    port, calls = local_api
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "resumeforge",
            "analyze-job",
            "--job",
            str(job_path),
            "--provider",
            "ollama",
            "--ollama-port",
            str(port),
            "--timeout",
            "10",
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    analysis = JobAnalysis.model_validate_json(result.stdout)
    assert analysis.provider == "ollama"
    assert "loopback-only" in result.stderr
    assert [path for path, payload in calls] == ["/api/status", "/api/show", "/api/chat"]
    assert list(tmp_path.iterdir()) == []
