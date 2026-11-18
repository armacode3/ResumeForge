"""Installed review command keeps source seeds and submitted drafts private and unapproved."""

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


def arguments(profile: Path, job: Path, requirements: Path, selection: Path) -> list[str]:
    return [
        "review-resume",
        "--profile",
        str(profile),
        "--job",
        str(job),
        "--requirements",
        str(requirements),
        "--selection",
        str(selection),
    ]


@pytest.fixture
def review_arguments(sample_path: Path, job_path: Path, mock_response_path: Path) -> list[str]:
    return arguments(
        sample_path,
        job_path,
        mock_response_path,
        sample_path.parents[1] / "plans/backend_intern.selection.json",
    )


def test_installed_source_seed_keeps_plan_conflicts_and_pending_bullets(
    review_arguments: list[str], tmp_path: Path
) -> None:
    result = subprocess.run(
        [sys.executable, "-m", "resumeforge", *review_arguments, "--confirm-review"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    assert result.returncode == 3, result.stderr
    report = json.loads(result.stdout)
    assert report["mode"] == "source_seed" and report["status"] == "blocked_by_plan"
    assert len(report["bullets"]) == 2
    assert all(
        b["wording_status"] == "verbatim_source" and b["review_status"] == "pending_review"
        for b in report["bullets"]
    )
    assert report["document"]["status"] == "needs_review"
    assert report["document"]["sections"][0]["entries"][0]["bullets"] == []
    assert "alex@example.com" not in result.stdout
    assert "Résumé wording idea" not in result.stdout
    assert "acc_queue_pending" not in result.stdout
    assert "no inference" in result.stderr
    assert list(tmp_path.iterdir()) == []


def test_review_edited_wording_is_offline_and_never_an_approval(
    sample_source: str, review_arguments: list[str], tmp_path: Path
) -> None:
    profile = tmp_path / "profile.md"
    profile.write_text(
        sample_source.replace("min_bullets_per_entry: 1", "min_bullets_per_entry: 0")
    )
    review_arguments[review_arguments.index("--profile") + 1] = str(profile)
    seed = runner.invoke(app, [*review_arguments, "--confirm-review"])
    assert seed.exit_code == 0, seed.output
    document = json.loads(seed.stdout)["document"]
    document["sections"][1]["entries"][0]["bullets"][0]["text"] = (
        "Owned the entire service using Kubernetes."
    )
    draft = tmp_path / "edited.json"
    draft.write_text(json.dumps(document))
    before = {path: path.read_bytes() for path in (profile, draft)}
    with (
        patch("socket.socket", side_effect=AssertionError("No network")),
        patch("resumeforge.cli.OllamaProvider", side_effect=AssertionError("No live provider")),
    ):
        result = runner.invoke(app, [*review_arguments, "--draft", str(draft), "--confirm-review"])
    assert result.exit_code == 0, result.output
    report = json.loads(result.stdout)
    assert report["mode"] == "submitted_draft" and report["status"] == "needs_review"
    assert report["bullets"][0]["wording_status"] == "edited_requires_review"
    assert report["bullets"][0]["review_status"] == "pending_review"
    assert "mentor" in report["bullets"][0]["source_statement"]
    assert before == {path: path.read_bytes() for path in (profile, draft)}
    assert set(tmp_path.iterdir()) == set(before)


def test_confirmation_precedes_all_input_access(review_arguments: list[str]) -> None:
    with (
        patch("resumeforge.cli.load_job", side_effect=AssertionError("No job IO")),
        patch("resumeforge.cli.load_profile", side_effect=AssertionError("No profile IO")),
        patch("resumeforge.cli.load_selection", side_effect=AssertionError("No selection IO")),
        patch("resumeforge.cli.load_resume_document", side_effect=AssertionError("No draft IO")),
    ):
        result = runner.invoke(app, [*review_arguments, "--draft", "unused"])
    assert result.exit_code == 2 and result.stdout == ""
    assert "--confirm-review" in Text.from_ansi(result.stderr).plain


@pytest.mark.parametrize(
    "payload",
    [
        '{"fictional-private-key":"fictional-private-value"}',
        '{"status":"approved","sections":[]}',
    ],
)
def test_invalid_or_self_approved_input_fails_before_profile_access(
    review_arguments: list[str], tmp_path: Path, payload: str
) -> None:
    path = tmp_path / "invalid.json"
    path.write_text(payload)
    with patch("resumeforge.cli.load_profile", side_effect=AssertionError("No profile IO")):
        result = runner.invoke(app, [*review_arguments, "--draft", str(path), "--confirm-review"])
    assert result.exit_code == 1 and result.stdout == ""
    assert "Resume draft review failed" in result.stderr
    assert "fictional-private" not in result.output and "Traceback" not in result.output


def test_changed_sources_reject_old_draft_without_partial_report(
    review_arguments: list[str], tmp_path: Path
) -> None:
    seed = runner.invoke(app, [*review_arguments, "--confirm-review"])
    document = json.loads(seed.stdout)["document"]
    document["plan_sha256"] = "0" * 64
    path = tmp_path / "stale.json"
    path.write_text(json.dumps(document))
    result = runner.invoke(app, [*review_arguments, "--draft", str(path), "--confirm-review"])
    assert result.exit_code == 1 and result.stdout == ""
    assert "different plan snapshot" in result.stderr


@pytest.mark.parametrize(
    "option", ["--draft", "--profile", "--selection", "--requirements", "--job"]
)
def test_missing_files_fail_safely(review_arguments: list[str], option: str) -> None:
    if option == "--draft":
        review_arguments.extend([option, "missing-private-file.json"])
    else:
        review_arguments[review_arguments.index(option) + 1] = "missing-private-file"
    result = runner.invoke(app, [*review_arguments, "--confirm-review"])
    assert result.exit_code == 1 and result.stdout == ""
    assert "Resume draft review failed" in result.stderr
    assert "Traceback" not in result.output


def test_review_help_explains_seed_mode_and_has_no_provider_or_approval_option() -> None:
    result = runner.invoke(app, ["review-resume", "--help"])
    assert result.exit_code == 0
    text = Text.from_ansi(result.stdout).plain
    for option in (
        "--profile",
        "--job",
        "--requirements",
        "--selection",
        "--draft",
        "--confirm-review",
    ):
        assert option in text
    assert "pending review" in text and "verbatim" in text
    assert "--provider" not in text and "--approve" not in text
