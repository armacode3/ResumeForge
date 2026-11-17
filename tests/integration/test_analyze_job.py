"""Installed CLI offline flow: JSON stdout, truthful stderr, no private-profile access."""

import json
import subprocess
import sys
from pathlib import Path

import pytest
from typer.testing import CliRunner

from resumeforge.cli import app
from resumeforge.jobs import JobAnalysis, load_job

pytestmark = pytest.mark.integration
runner = CliRunner()


def test_installed_job_analysis_is_read_only_and_explicitly_mocked(
    job_path: Path, mock_response_path: Path, tmp_path: Path
) -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "resumeforge",
            "analyze-job",
            "--job",
            str(job_path),
            "--mock-response",
            str(mock_response_path),
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    analysis = JobAnalysis.model_validate_json(result.stdout)
    assert analysis.provider == "fake"
    assert analysis.model == "fixture-v1"
    assert analysis.source_sha256 == load_job(job_path).sha256
    assert "no live AI extraction" in result.stderr
    assert list(tmp_path.iterdir()) == []


def test_analysis_does_not_load_or_change_private_profile(
    job_path: Path,
    mock_response_path: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    private = tmp_path / "data/profile/user_information.md"
    private.parent.mkdir(parents=True)
    private.write_text("fictional-private-profile-sentinel", encoding="utf-8")

    def forbid_profile(*args: object, **kwargs: object) -> None:
        raise AssertionError("Job analysis must not access a candidate profile")

    monkeypatch.setattr("resumeforge.cli.load_profile", forbid_profile)
    result = runner.invoke(
        app, ["analyze-job", "--job", str(job_path), "--mock-response", str(mock_response_path)]
    )

    assert result.exit_code == 0
    assert "fictional-private-profile-sentinel" not in result.output
    assert private.read_text(encoding="utf-8") == "fictional-private-profile-sentinel"
    assert json.loads(result.stdout)["provider"] == "fake"


@pytest.mark.parametrize("missing", ["job", "response"])
def test_missing_files_fail_cleanly(
    job_path: Path, mock_response_path: Path, tmp_path: Path, missing: str
) -> None:
    job = tmp_path / "missing.md" if missing == "job" else job_path
    response = tmp_path / "missing.json" if missing == "response" else mock_response_path
    result = runner.invoke(
        app, ["analyze-job", "--job", str(job), "--mock-response", str(response)]
    )

    assert result.exit_code == 1
    assert "existing regular file" in result.stderr
    assert result.stdout == ""
    assert "Traceback" not in result.output


def test_invalid_response_does_not_emit_partial_json(job_path: Path, tmp_path: Path) -> None:
    response = tmp_path / "invalid.json"
    response.write_text('{"private-value":', encoding="utf-8")
    result = runner.invoke(
        app, ["analyze-job", "--job", str(job_path), "--mock-response", str(response)]
    )

    assert result.exit_code == 1
    assert result.stdout == ""
    assert "Invalid provider JSON" in result.stderr
    assert "private-value" not in result.output


def test_fake_fixture_is_mandatory_and_live_provider_is_not_available(job_path: Path) -> None:
    for arguments in [
        ["analyze-job", "--job", str(job_path)],
        ["analyze-job", "--job", str(job_path), "--provider", "openai"],
    ]:
        result = runner.invoke(app, arguments)
        assert result.exit_code == 2


def test_analyze_help_describes_offline_mode() -> None:
    result = runner.invoke(app, ["analyze-job", "--help"])
    assert result.exit_code == 0
    assert "--mock-response" in result.stdout
    assert "offline replay" in result.stdout.lower()
