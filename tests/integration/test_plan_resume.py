"""Installed planning emits private drafts and distinguishes count conflicts from input errors."""

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


@pytest.fixture
def selection_path(sample_path: Path) -> Path:
    return sample_path.parents[1] / "plans" / "backend_intern.selection.json"


def arguments(profile: Path, job: Path, requirements: Path, selection: Path) -> list[str]:
    return [
        "plan-resume",
        "--profile",
        str(profile),
        "--job",
        str(job),
        "--requirements",
        str(requirements),
        "--selection",
        str(selection),
    ]


def test_installed_sample_surfaces_education_bullet_conflict_without_inventing_evidence(
    sample_path: Path,
    job_path: Path,
    mock_response_path: Path,
    selection_path: Path,
    tmp_path: Path,
) -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "resumeforge",
            *arguments(sample_path, job_path, mock_response_path, selection_path),
            "--confirm-review",
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    assert result.returncode == 3, result.stderr
    plan = json.loads(result.stdout)
    assert plan["planning_version"] == "reviewed-selection-plan-v1"
    assert plan["status"] == "needs_review" and plan["constraint_status"] == "conflicts"
    assert plan["budget"]["bullet_slot_count"] == 2
    assert plan["sections"][0]["section"] == "education"
    assert plan["sections"][0]["entries"][0]["bullet_slots"] == []
    assert any(
        finding["code"] == "entry_bullet_minimum_not_met" and finding["entry_id"] == "edu_example"
        for finding in plan["findings"]
    )
    assert "alex@example.com" not in result.stdout
    assert "Résumé wording idea" not in result.stdout
    assert "acc_queue_pending" not in result.stdout
    assert "no inference" in result.stderr
    assert list(tmp_path.iterdir()) == []


def test_plan_with_metadata_permitted_by_counts_is_still_unapproved_and_offline(
    sample_source: str,
    job_path: Path,
    mock_response_path: Path,
    selection_path: Path,
    tmp_path: Path,
) -> None:
    profile = tmp_path / "synthetic.md"
    profile.write_text(
        sample_source.replace("min_bullets_per_entry: 1", "min_bullets_per_entry: 0")
    )
    before = profile.read_bytes()
    with (
        patch("socket.socket", side_effect=AssertionError("No network")),
        patch("resumeforge.cli.OllamaProvider", side_effect=AssertionError("No live provider")),
    ):
        result = runner.invoke(
            app,
            [*arguments(profile, job_path, mock_response_path, selection_path), "--confirm-review"],
        )
    assert result.exit_code == 0, result.output
    plan = json.loads(result.stdout)
    assert plan["status"] == "needs_review"
    assert plan["constraint_status"] == "within_count_constraints"
    assert plan["sections"][2]["entries"][0]["bullet_slots"][0]["caveats"] == [
        "parent_entry_in_progress"
    ]
    assert profile.read_bytes() == before
    assert set(tmp_path.iterdir()) == {profile}


def test_review_acknowledgement_precedes_all_input_io() -> None:
    with (
        patch("resumeforge.cli.load_job", side_effect=AssertionError("No job IO")),
        patch("resumeforge.cli.load_profile", side_effect=AssertionError("No profile IO")),
        patch("resumeforge.cli.load_selection", side_effect=AssertionError("No selection IO")),
    ):
        result = runner.invoke(app, arguments(*(Path("unused") for _ in range(4))))
    assert result.exit_code == 2
    assert result.stdout == ""
    assert "--confirm-review" in Text.from_ansi(result.stderr).plain


def test_invalid_selection_is_rejected_before_profile_access(
    job_path: Path, mock_response_path: Path, tmp_path: Path
) -> None:
    selection = tmp_path / "invalid.json"
    selection.write_text('{"fictional-private-field":"fictional-private-value"}')
    with patch("resumeforge.cli.load_profile", side_effect=AssertionError("No profile access")):
        result = runner.invoke(
            app,
            [
                *arguments(Path("unused"), job_path, mock_response_path, selection),
                "--confirm-review",
            ],
        )
    assert result.exit_code == 1 and result.stdout == ""
    assert "Resume planning failed" in result.stderr
    assert "fictional-private" not in result.output


@pytest.mark.parametrize(
    "mode", ["missing_profile", "missing_selection", "source_mismatch", "bad_reference"]
)
def test_input_failures_emit_no_partial_plan_or_raw_source(
    sample_path: Path,
    job_path: Path,
    mock_response_path: Path,
    selection_path: Path,
    tmp_path: Path,
    mode: str,
) -> None:
    if mode == "missing_profile":
        sample_path = tmp_path / "missing.md"
    elif mode == "missing_selection":
        selection_path = tmp_path / "missing.json"
    elif mode == "source_mismatch":
        job_path = tmp_path / "different.md"
        job_path.write_text("fictional-private-other-source")
    else:
        selection_path = tmp_path / "bad-reference.json"
        selection_path.write_text(
            '{"schema_version":1,"entries":[{"entry_id":"proj_private_unknown","accomplishment_ids":[]}]}'
        )
    result = runner.invoke(
        app,
        [*arguments(sample_path, job_path, mock_response_path, selection_path), "--confirm-review"],
    )
    assert result.exit_code == 1 and result.stdout == ""
    assert "Resume planning failed" in result.stderr
    assert "fictional-private" not in result.output and "proj_private_unknown" not in result.output
    assert "Traceback" not in result.output


def test_plan_help_has_explicit_paths_and_no_generation_provider_or_approval_option() -> None:
    result = runner.invoke(app, ["plan-resume", "--help"])
    assert result.exit_code == 0
    help_text = Text.from_ansi(result.stdout).plain
    for option in ["--profile", "--job", "--requirements", "--selection", "--confirm-review"]:
        assert option in help_text
    assert "draft" in help_text.lower()
    assert "--provider" not in help_text and "--approve" not in help_text
