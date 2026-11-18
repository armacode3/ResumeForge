"""Installed wording assistance remains explicit, read-only, source-bound and pending."""

import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from resumeforge.cli import app
from resumeforge.providers import FakeProvider

pytestmark = pytest.mark.integration
runner = CliRunner()


@pytest.fixture
def wording_args(
    sample_source: str, sample_path: Path, job_path: Path, mock_response_path: Path, tmp_path: Path
) -> list[str]:
    profile = tmp_path / "profile.md"
    profile.write_text(
        sample_source.replace("min_bullets_per_entry: 1", "min_bullets_per_entry: 0")
    )
    sources = [
        "--profile",
        str(profile),
        "--job",
        str(job_path),
        "--requirements",
        str(mock_response_path),
        "--selection",
        str(sample_path.parents[1] / "plans/backend_intern.selection.json"),
        "--confirm-review",
    ]
    seed_process = runner.invoke(app, ["review-resume", *sources])
    assert seed_process.exit_code == 0, seed_process.output
    seed = json.loads(seed_process.stdout)
    response = tmp_path / "wording.json"
    response.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "plan_sha256": seed["document"]["plan_sha256"],
                "seed_document_sha256": seed["document_sha256"],
                "bullets": [
                    {
                        "bullet_id": b["bullet_id"],
                        "accomplishment_id": b["accomplishment_id"],
                        "text": b["source_statement"],
                    }
                    for b in seed["bullets"]
                ],
            }
        )
    )
    return ["suggest-wording", *sources, "--mock-response", str(response)]


def test_installed_fake_wording_is_read_only_pending_and_has_an_inner_draft(
    wording_args: list[str], tmp_path: Path
) -> None:
    before = {p: p.read_bytes() for p in tmp_path.iterdir()}
    result = subprocess.run(
        [sys.executable, "-m", "resumeforge", *wording_args],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
        timeout=10,
    )
    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report["attempt"]["provider"] == "fake"
    assert "Offline wording response replay" in result.stderr
    assert report["review"]["document"]["status"] == "needs_review"
    assert all(b["review_status"] == "pending_review" for b in report["review"]["bullets"])
    assert report["rendering_authorized"] is False
    assert "alex@example.com" not in result.stdout
    assert before == {p: p.read_bytes() for p in tmp_path.iterdir()}
    # Output's inner document is usable by existing inspection, not by self-approval.
    draft = tmp_path / "draft.json"
    draft.write_text(json.dumps(report["review"]["document"]))
    sources = wording_args[1 : wording_args.index("--mock-response")]
    inspected = runner.invoke(app, ["review-resume", *sources, "--draft", str(draft)])
    assert inspected.exit_code == 0
    assert json.loads(inspected.stdout) == report["review"]


@pytest.mark.parametrize(
    "mode",
    [
        "missing_review",
        "missing_fixture",
        "unconfirmed_local",
        "local_with_fixture",
        "fake_with_local_flag",
        "fake_with_model",
        "fake_with_port",
        "fake_with_timeout",
        "fake_with_tokens",
        "cloud_choice",
    ],
)
def test_invalid_activation_fails_before_all_input_io(mode: str) -> None:
    args = [
        "suggest-wording",
        "--profile",
        "unused",
        "--job",
        "unused",
        "--requirements",
        "unused",
        "--selection",
        "unused",
        "--mock-response",
        "unused",
        "--confirm-review",
    ]
    if mode == "missing_review":
        args.remove("--confirm-review")
    elif mode in ("missing_fixture", "unconfirmed_local"):
        index = args.index("--mock-response")
        del args[index : index + 2]
        if mode == "unconfirmed_local":
            args.extend(["--provider", "ollama"])
    elif mode == "local_with_fixture":
        args.extend(["--provider", "ollama", "--confirm-local-data"])
    else:
        args.extend(
            {
                "fake_with_local_flag": ["--confirm-local-data"],
                "fake_with_model": ["--model", "other:4b"],
                "fake_with_port": ["--ollama-port", "11435"],
                "fake_with_timeout": ["--timeout", "10"],
                "fake_with_tokens": ["--max-output-tokens", "512"],
                "cloud_choice": ["--provider", "cloud"],
            }[mode]
        )
    with (
        patch("resumeforge.cli.load_job", side_effect=AssertionError("No IO")),
        patch("resumeforge.cli.load_profile", side_effect=AssertionError("No IO")),
        patch("resumeforge.cli.OllamaProvider", side_effect=AssertionError("No provider")),
    ):
        result = runner.invoke(app, args)
    assert result.exit_code == 2 and result.stdout == ""


@pytest.mark.parametrize(
    "mode", ["malformed", "stale", "unknown_bullet", "self_approval", "missing_file"]
)
def test_invalid_response_emits_no_partial_json_or_input_dump(
    wording_args: list[str], mode: str
) -> None:
    path = Path(wording_args[-1])
    data = json.loads(path.read_text())
    if mode == "malformed":
        data = {"private-field": "private-value"}
    elif mode == "stale":
        data["seed_document_sha256"] = "0" * 64
    elif mode == "unknown_bullet":
        data["bullets"][0]["bullet_id"] = "bullet_private_unknown"
    elif mode == "self_approval":
        data["bullets"][0]["review_status"] = "approved"
    else:
        wording_args[-1] = str(path.with_name("missing.json"))
    path.write_text(json.dumps(data))
    with patch("socket.socket", side_effect=AssertionError("Offline")):
        result = runner.invoke(app, wording_args)
    assert result.exit_code == 1 and result.stdout == ""
    assert "private-value" not in result.output and "private_unknown" not in result.output
    assert "Traceback" not in result.output


def test_fabricated_proposal_enters_findings_not_approval(wording_args: list[str]) -> None:
    path = Path(wording_args[-1])
    data = json.loads(path.read_text())
    data["bullets"][0]["text"] = "Owned 99 Kubernetes services."
    path.write_text(json.dumps(data))
    result = runner.invoke(app, wording_args)
    assert result.exit_code == 0, result.output
    report = json.loads(result.stdout)
    assert len(report["review"]["bullets"][0]["findings"]) == 2
    assert report["review"]["bullets"][0]["review_status"] == "pending_review"
    assert report["rendering_authorized"] is False


def test_conflicted_plan_returns_review_without_a_wording_attempt(wording_args: list[str]) -> None:
    profile = Path(wording_args[wording_args.index("--profile") + 1])
    profile.write_text(
        profile.read_text().replace("min_bullets_per_entry: 0", "min_bullets_per_entry: 1")
    )
    result = runner.invoke(app, wording_args)
    assert result.exit_code == 3, result.output
    report = json.loads(result.stdout)
    assert report["status"] == "blocked_by_plan" and report["attempt"] is None
    assert report["review"]["plan"]["findings"]
    assert "No wording provider called" in result.stderr


def test_local_mode_uses_separate_consent_and_guarded_adapter_with_mocked_completion(
    wording_args: list[str],
) -> None:
    response = Path(wording_args[-1]).read_text()
    args = [
        *wording_args[:-2],
        "--provider",
        "ollama",
        "--confirm-local-data",
        "--ollama-port",
        "11435",
    ]
    with (
        patch("resumeforge.cli.OllamaProvider", return_value=FakeProvider(response)) as factory,
        patch("socket.socket", side_effect=AssertionError("Mocked adapter only")),
    ):
        result = runner.invoke(app, args)
    assert result.exit_code == 0, result.output
    factory.assert_called_once_with("qwen3:4b", 11435, 180.0, 4096)
    assert "Local Ollama wording proposals" in result.stderr
    assert json.loads(result.stdout)["review"]["document"]["status"] == "needs_review"


def test_invalid_selection_is_a_safe_cli_error_before_profile_access(
    wording_args: list[str], tmp_path: Path
) -> None:
    selection = tmp_path / "invalid-selection.json"
    selection.write_text('{"private-key": "private-value"}')
    wording_args[wording_args.index("--selection") + 1] = str(selection)
    with patch("resumeforge.cli.load_profile", side_effect=AssertionError("No profile IO")):
        result = runner.invoke(app, wording_args)
    assert result.exit_code == 1 and result.stdout == ""
    assert "private-value" not in result.output and "Traceback" not in result.output
