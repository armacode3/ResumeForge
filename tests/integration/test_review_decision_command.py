"""Decision mode needs explicit human confirmation and never authorizes rendering."""

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
def decision_args(
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
    review = json.loads(seed.stdout)
    draft = tmp_path / "draft.json"
    draft.write_text(json.dumps(review["document"]))
    decisions = tmp_path / "decisions.json"
    decisions.write_text(
        json.dumps(
            {
                "schema_version": 2,
                "review_version": review["review_version"],
                "plan_sha256": review["document"]["plan_sha256"],
                "document_sha256": review["document_sha256"],
                "findings_sha256": review["findings_sha256"],
                "bullets": [
                    {
                        "bullet_id": b["bullet_id"],
                        "decision": "approve",
                        "reason": "Fictional user reviewed source scope and wording.",
                        "acknowledged_finding_ids": [],
                    }
                    for b in review["bullets"]
                ],
            }
        )
    )
    return [*args, "--draft", str(draft), "--decisions", str(decisions), "--confirm-decisions"]


def test_installed_decision_mode_is_narrow_offline_and_read_only(
    decision_args: list[str], tmp_path: Path
) -> None:
    before = {path: path.read_bytes() for path in tmp_path.iterdir()}
    result = subprocess.run(
        [sys.executable, "-m", "resumeforge", *decision_args],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
        timeout=10,
    )
    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report["status"] == "bullet_wording_approved_by_user"
    assert report["scope"] == "bullet_wording_only" and not report["rendering_authorized"]
    assert report["review"]["document"]["status"] == "needs_review"
    assert all(b["review_status"] == "approved_by_user" for b in report["bullets"])
    assert "alex@example.com" not in result.stdout
    assert "no inference" in result.stderr
    assert before == {path: path.read_bytes() for path in tmp_path.iterdir()}


@pytest.mark.parametrize("mode", ["partial", "rejected"])
def test_incomplete_and_rejected_decisions_exit_three_with_a_complete_report(
    decision_args: list[str], mode: str
) -> None:
    path = Path(decision_args[decision_args.index("--decisions") + 1])
    data = json.loads(path.read_text())
    if mode == "partial":
        data["bullets"] = data["bullets"][:1]
    else:
        data["bullets"][0]["decision"] = "reject"
    path.write_text(json.dumps(data))
    with (
        patch("socket.socket", side_effect=AssertionError("No network")),
        patch("resumeforge.cli.OllamaProvider", side_effect=AssertionError("No live provider")),
    ):
        result = runner.invoke(app, decision_args)
    assert result.exit_code == 3, result.output
    report = json.loads(result.stdout)
    assert report["status"] == ("needs_review" if mode == "partial" else "has_rejections")
    assert (
        len(report["bullets"]) == 2 and report["review"]["plan"]["budget"]["bullet_slot_count"] == 2
    )


@pytest.mark.parametrize(
    "mode", ["no_decision_ack", "no_source_ack", "no_draft", "ack_without_decisions"]
)
def test_incomplete_decision_usage_fails_before_any_input_io(mode: str) -> None:
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
        "--decisions",
        "unused",
        "--confirm-review",
        "--confirm-decisions",
    ]
    if mode == "no_decision_ack":
        args.remove("--confirm-decisions")
    elif mode == "no_source_ack":
        args.remove("--confirm-review")
    else:
        index = args.index("--draft" if mode == "no_draft" else "--decisions")
        del args[index : index + 2]
    with (
        patch("resumeforge.cli.load_job", side_effect=AssertionError("No job IO")),
        patch("resumeforge.cli.load_profile", side_effect=AssertionError("No profile IO")),
        patch(
            "resumeforge.cli.load_review_decisions", side_effect=AssertionError("No decision IO")
        ),
    ):
        result = runner.invoke(app, args)
    assert result.exit_code == 2 and result.stdout == ""
    assert "requires" in result.stderr or "--confirm-review" in Text.from_ansi(result.stderr).plain


@pytest.mark.parametrize(
    "mode",
    [
        "stale",
        "malformed",
        "missing_file",
        "unknown_bullet",
        "stale_findings",
        "old_format",
        "invalid_ack",
    ],
)
def test_bad_decisions_never_emit_a_partial_approval_or_raw_input(
    decision_args: list[str], mode: str
) -> None:
    path = Path(decision_args[decision_args.index("--decisions") + 1])
    data = json.loads(path.read_text())
    if mode == "stale":
        data["document_sha256"] = "0" * 64
    elif mode == "malformed":
        data = {"fictional-private-field": "fictional-private-value"}
    elif mode == "unknown_bullet":
        data["bullets"][0]["bullet_id"] = "bullet_private_unknown"
    elif mode == "stale_findings":
        data["findings_sha256"] = "0" * 64
    elif mode == "old_format":
        data["schema_version"] = 1
    elif mode == "invalid_ack":
        data["bullets"][0]["acknowledged_finding_ids"] = ["0" * 64]
    else:
        decision_args[decision_args.index("--decisions") + 1] = str(path.with_name("missing.json"))
    path.write_text(json.dumps(data))
    result = runner.invoke(app, decision_args)
    assert result.exit_code == 1 and result.stdout == ""
    assert "fictional-private" not in result.output and "private_unknown" not in result.output
    assert "Traceback" not in result.output


def test_invalid_decision_fields_are_rejected_before_profile_access(
    decision_args: list[str],
) -> None:
    path = Path(decision_args[decision_args.index("--decisions") + 1])
    path.write_text('{"fictional-private-field":"fictional-private-value"}')
    with patch("resumeforge.cli.load_profile", side_effect=AssertionError("No profile IO")):
        result = runner.invoke(app, decision_args)
    assert result.exit_code == 1 and result.stdout == ""
    assert "fictional-private" not in result.output


def test_plan_conflicts_cannot_be_approved_through_the_cli(decision_args: list[str]) -> None:
    profile = Path(decision_args[decision_args.index("--profile") + 1])
    profile.write_text(
        profile.read_text().replace("min_bullets_per_entry: 0", "min_bullets_per_entry: 1")
    )
    # Seed a fresh, blocked snapshot so the test is not merely an old-hash rejection.
    base_args = decision_args[: decision_args.index("--draft")]
    seed = runner.invoke(app, base_args)
    assert seed.exit_code == 3
    review = json.loads(seed.stdout)
    Path(decision_args[decision_args.index("--draft") + 1]).write_text(
        json.dumps(review["document"])
    )
    path = Path(decision_args[decision_args.index("--decisions") + 1])
    data = json.loads(path.read_text())
    data.update(
        plan_sha256=review["document"]["plan_sha256"],
        document_sha256=review["document_sha256"],
        findings_sha256=review["findings_sha256"],
    )
    path.write_text(json.dumps(data))
    result = runner.invoke(app, decision_args)
    assert result.exit_code == 3, result.output
    report = json.loads(result.stdout)
    assert report["status"] == "blocked_by_plan"
    assert all(b["review_status"] == "blocked_by_plan" for b in report["bullets"])


def test_help_explains_explicit_decision_options() -> None:
    result = runner.invoke(app, ["review-resume", "--help"])
    assert result.exit_code == 0
    text = Text.from_ansi(result.stdout).plain
    assert "--decisions" in text and "--confirm-decisions" in text
    assert "--provider" not in text


def test_installed_findings_gate_preserves_wording_until_acknowledged(
    decision_args: list[str], tmp_path: Path
) -> None:
    draft_path = Path(decision_args[decision_args.index("--draft") + 1])
    draft = json.loads(draft_path.read_text())
    draft["sections"][1]["entries"][0]["bullets"][0]["text"] = "Owned 99 endpoints."
    draft_path.write_text(json.dumps(draft))
    inspect_args = decision_args[: decision_args.index("--decisions")]
    inspected = runner.invoke(app, inspect_args)
    assert inspected.exit_code == 0, inspected.output
    review = json.loads(inspected.stdout)
    assert len(review["bullets"][0]["findings"]) == 2
    path = Path(decision_args[decision_args.index("--decisions") + 1])
    choices = json.loads(path.read_text())
    choices.update(
        document_sha256=review["document_sha256"], findings_sha256=review["findings_sha256"]
    )
    path.write_text(json.dumps(choices))
    for acknowledge in (False, True):
        if acknowledge:
            choices["bullets"][0]["acknowledged_finding_ids"] = [
                finding["id"] for finding in review["bullets"][0]["findings"]
            ]
            path.write_text(json.dumps(choices))
        result = subprocess.run(
            [sys.executable, "-m", "resumeforge", *decision_args],
            cwd=tmp_path,
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
        )
        assert result.returncode == (0 if acknowledge else 3), result.stderr
        report = json.loads(result.stdout)
        assert report["status"] == (
            "bullet_wording_approved_by_user" if acknowledge else "needs_review"
        )
        assert report["review"]["document"] == draft
        assert report["rendering_authorized"] is False
        assert report["review"]["bullets"][0]["findings"] == review["bullets"][0]["findings"]
