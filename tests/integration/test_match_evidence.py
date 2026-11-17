"""Installed matching reads explicit local inputs and acknowledges review without writing files."""

import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest
from rich.text import Text
from typer.testing import CliRunner

from resumeforge.cli import app

pytestmark = pytest.mark.integration
runner = CliRunner()


def arguments(profile: Path, job: Path, requirements: Path) -> list[str]:
    return [
        "match-evidence",
        "--profile",
        str(profile),
        "--job",
        str(job),
        "--requirements",
        str(requirements),
    ]


def test_installed_matching_is_offline_read_only_and_not_a_qualification_verdict(
    sample_path: Path, job_path: Path, mock_response_path: Path, tmp_path: Path
) -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "resumeforge",
            *arguments(sample_path, job_path, mock_response_path),
            "--confirm-review",
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report["matching_version"] == "evidence-matching-v1"
    assert report["signals_version"] == "evidence-signals-v1"
    assert report["requirements_reviewed"] is True
    python = next(item for item in report["items"] if item["job_item_id"] == "job_python_required")
    assert [candidate["accomplishment_id"] for candidate in python["candidates"]] == [
        "acc_api",
        "acc_queue",
    ]
    # Both Python mentions are scoped metadata, not wording inherited from verified bullets.
    assert python["candidates"][0]["signals"] == {
        "job_phrase_in_statement": False,
        "technologies": [{"technology": "Python", "job_span": "Python", "statement_span": None}],
        "metrics": [
            {
                "text": "12 existing internal API endpoints covered by the added tests.",
                "statement_span": None,
            }
        ],
    }
    assert python["candidates"][1]["signals"]["metrics"] == []
    pending = next(
        record
        for record in report["evidence"]
        if record["accomplishment_id"] == "acc_queue_pending"
    )
    assert pending["eligibility"] == "unverified" and pending["statement"] is None
    assert any(finding["section"] == "education" for finding in report["findings"])
    assert "alex@example.com" not in result.stdout
    assert "Résumé wording idea" not in result.stdout
    assert "no inference" in result.stderr
    assert list(tmp_path.iterdir()) == []


def test_review_acknowledgement_is_required_before_reading_inputs() -> None:
    with (
        patch("resumeforge.cli.load_job", side_effect=AssertionError("No IO before review")),
        patch("resumeforge.cli.load_profile", side_effect=AssertionError("No profile access")),
    ):
        result = runner.invoke(app, arguments(Path("unused"), Path("unused"), Path("unused")))
    assert result.exit_code == 2
    assert result.stdout == ""
    assert "--confirm-review" in Text.from_ansi(result.stderr).plain


def test_matching_never_constructs_a_live_provider_or_opens_network(
    sample_path: Path, job_path: Path, mock_response_path: Path
) -> None:
    with (
        patch("socket.socket", side_effect=AssertionError("No network")),
        patch("resumeforge.cli.OllamaProvider", side_effect=AssertionError("No live provider")),
    ):
        result = runner.invoke(
            app, [*arguments(sample_path, job_path, mock_response_path), "--confirm-review"]
        )
    assert result.exit_code == 0, result.output


def test_invalid_response_fails_before_loading_profile(job_path: Path, tmp_path: Path) -> None:
    path = tmp_path / "invalid.json"
    path.write_text('{"fictional-private-field":"fictional-private-value"}')
    with patch("resumeforge.cli.load_profile", side_effect=AssertionError("No profile access")):
        result = runner.invoke(
            app, [*arguments(Path("unused"), job_path, path), "--confirm-review"]
        )
    assert result.exit_code == 1
    assert result.stdout == ""
    assert "Evidence matching failed" in result.stderr
    assert "fictional-private" not in result.output
    assert "Traceback" not in result.output


@pytest.mark.parametrize("mode", ["missing_profile", "invalid_profile"])
def test_profile_failures_have_no_partial_matching_output(
    mode: str, job_path: Path, mock_response_path: Path, tmp_path: Path
) -> None:
    profile = tmp_path / "invalid.md"
    if mode == "invalid_profile":
        profile.write_text(
            "---\nschema_version: 1\nperson: {name: [fictional-private-value]}\n---\n"
        )
    result = runner.invoke(
        app, [*arguments(profile, job_path, mock_response_path), "--confirm-review"]
    )
    assert result.exit_code == 1
    assert result.stdout == ""
    assert "fictional-private-value" not in result.output


def test_match_help_requires_explicit_profile_and_documents_lexical_scope() -> None:
    result = runner.invoke(app, ["match-evidence", "--help"])
    help_text = Text.from_ansi(result.stdout).plain
    assert result.exit_code == 0
    for option in ["--profile", "--job", "--requirements", "--confirm-review"]:
        assert option in help_text
    assert "lexical" in help_text.lower()
    assert "--provider" not in help_text
