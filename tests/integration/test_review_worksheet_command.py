"""Installed worksheets are private read-only scaffolds, never prefilled decisions."""

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
def worksheet_args(
    sample_source: str, sample_path: Path, job_path: Path, mock_response_path: Path, tmp_path: Path
) -> list[str]:
    profile = tmp_path / "profile.md"
    profile.write_text(
        sample_source.replace("min_bullets_per_entry: 1", "min_bullets_per_entry: 0")
    )
    args = [
        "review-resume",
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
    seed = runner.invoke(app, args)
    assert seed.exit_code == 0, seed.output
    draft = tmp_path / "draft.json"
    draft.write_text(json.dumps(json.loads(seed.stdout)["document"]))
    return [*args, "--draft", str(draft), "--worksheet"]


@pytest.mark.parametrize("edited", [False, True])
def test_installed_worksheet_retains_current_context_and_null_choices_without_writing(
    worksheet_args: list[str],
    tmp_path: Path,
    edited: bool,
) -> None:
    draft_path = Path(worksheet_args[worksheet_args.index("--draft") + 1])
    draft = json.loads(draft_path.read_text())
    if edited:
        draft["sections"][1]["entries"][0]["bullets"][0]["text"] = "Owned 99 endpoints."
        draft_path.write_text(json.dumps(draft))
    before = {p: p.read_bytes() for p in tmp_path.iterdir()}
    result = subprocess.run(
        [sys.executable, "-m", "resumeforge", *worksheet_args],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
        timeout=10,
    )
    assert result.returncode == 0, result.stderr
    worksheet = json.loads(result.stdout)
    assert worksheet["worksheet_version"] == "pending-review-worksheet-v1"
    assert worksheet["review"]["document"] == draft
    assert worksheet["status"] == "needs_review" and not worksheet["rendering_authorized"]
    for pending, bullet in zip(
        worksheet["decision_template"]["bullets"], worksheet["review"]["bullets"], strict=True
    ):
        assert pending["decision"] is pending["reason"] is None
        assert pending["acknowledged_finding_ids"] == []
        assert [f["fragment_id"] for f in pending["fragment_decisions"]] == [
            f["id"] for f in bullet["source_fragments"]
        ]
        assert all(
            f["disposition"] is f["reason"] is f["draft_span"] is None
            for f in pending["fragment_decisions"]
        )
    assert "alex@example.com" not in result.stdout
    assert "no inference" in result.stderr
    assert before == {p: p.read_bytes() for p in tmp_path.iterdir()}


@pytest.mark.parametrize(
    "mode", ["no_draft", "decisions", "confirmation", "no_review", "all_decision_options"]
)
def test_invalid_worksheet_options_fail_before_all_source_io(mode: str) -> None:
    args = [
        "review-resume",
        "--profile",
        "unused",
        "--job",
        "unused",
        "--requirements",
        "unused",
        "--selection",
        "unused",
        "--draft",
        "unused",
        "--worksheet",
        "--confirm-review",
    ]
    if mode == "no_draft":
        index = args.index("--draft")
        del args[index : index + 2]
    elif mode == "no_review":
        args.remove("--confirm-review")
    elif mode == "decisions":
        args.extend(["--decisions", "unused"])
    elif mode == "confirmation":
        args.append("--confirm-decisions")
    else:
        args.extend(["--decisions", "unused", "--confirm-decisions"])
    with (
        patch("resumeforge.cli.load_job", side_effect=AssertionError("No job read")),
        patch("resumeforge.cli.load_profile", side_effect=AssertionError("No profile read")),
        patch("resumeforge.cli.load_resume_document", side_effect=AssertionError("No draft read")),
    ):
        result = runner.invoke(app, args)
    assert result.exit_code == 2 and result.stdout == ""


def test_worksheet_blocked_plan_is_complete_and_still_exits_three(
    worksheet_args: list[str],
) -> None:
    profile = Path(worksheet_args[worksheet_args.index("--profile") + 1])
    profile.write_text(
        profile.read_text().replace("min_bullets_per_entry: 0", "min_bullets_per_entry: 1")
    )
    base = worksheet_args[: worksheet_args.index("--draft")]
    seed = runner.invoke(app, base)
    assert seed.exit_code == 3, seed.output
    draft = json.loads(seed.stdout)["document"]
    Path(worksheet_args[worksheet_args.index("--draft") + 1]).write_text(json.dumps(draft))
    with (
        patch("socket.socket", side_effect=AssertionError("No network")),
        patch("resumeforge.cli.OllamaProvider", side_effect=AssertionError("No provider")),
    ):
        result = runner.invoke(app, worksheet_args)
    assert result.exit_code == 3, result.output
    worksheet = json.loads(result.stdout)
    assert worksheet["status"] == worksheet["review"]["status"] == "blocked_by_plan"
    assert worksheet["review"]["document"] == draft
    assert worksheet["review"]["plan"]["constraint_status"] == "conflicts"
    assert all(b["decision"] is None for b in worksheet["decision_template"]["bullets"])


@pytest.mark.parametrize("mode", ["envelope", "untouched_template", "stale_draft"])
def test_worksheet_and_placeholder_inputs_cannot_be_used_as_decisions(
    worksheet_args: list[str],
    tmp_path: Path,
    mode: str,
) -> None:
    result = runner.invoke(app, worksheet_args)
    assert result.exit_code == 0, result.output
    worksheet = json.loads(result.stdout)
    if mode == "stale_draft":
        profile = Path(worksheet_args[worksheet_args.index("--profile") + 1])
        profile.write_text(profile.read_text().replace("12 existing", "13 existing"))
        result = runner.invoke(app, worksheet_args)
    else:
        path = tmp_path / "choices.json"
        path.write_text(
            json.dumps(worksheet if mode == "envelope" else worksheet["decision_template"])
        )
        result = runner.invoke(
            app, [*worksheet_args[:-1], "--decisions", str(path), "--confirm-decisions"]
        )
    assert result.exit_code == 1 and result.stdout == ""
    assert "Traceback" not in result.output


def test_deliberate_template_completion_still_requires_separate_confirmation(
    worksheet_args: list[str],
    tmp_path: Path,
) -> None:
    worksheet = json.loads(runner.invoke(app, worksheet_args).stdout)
    choices = worksheet["decision_template"]
    for choice in choices["bullets"]:
        choice.update(
            decision="approve", reason="Fictional user reviewed this exact unchanged wording."
        )
    path = tmp_path / "choices.json"
    path.write_text(json.dumps(choices))
    args = [*worksheet_args[:-1], "--decisions", str(path)]
    result = runner.invoke(app, args)
    assert result.exit_code == 2 and result.stdout == ""
    result = runner.invoke(app, [*args, "--confirm-decisions"])
    assert result.exit_code == 0, result.output
    report = json.loads(result.stdout)
    assert report["status"] == "bullet_wording_approved_by_user"
    assert not report["rendering_authorized"]
    assert all(b["review_status"] == "pending_review" for b in report["review"]["bullets"])


def test_worksheet_help_has_no_provider_activation() -> None:
    result = runner.invoke(app, ["review-resume", "--help"])
    assert result.exit_code == 0
    text = Text.from_ansi(result.stdout).plain
    assert "--worksheet" in text and "--draft" in text
    assert "--provider" not in text


def test_oversized_worksheet_never_emits_partial_json(
    worksheet_args: list[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("resumeforge.resume.worksheet.MAX_INPUT_BYTES", 1)
    result = runner.invoke(app, worksheet_args)
    assert result.exit_code == 1 and result.stdout == ""
    assert "byte limit" in result.stderr and "Traceback" not in result.output
