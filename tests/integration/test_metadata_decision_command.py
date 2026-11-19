"""Metadata decision CLI keeps narrow user attestations separate from sources and wording."""

import json
import subprocess
import sys
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest
from rich.text import Text
from typer.testing import CliRunner

from resumeforge.cli import app

pytestmark = pytest.mark.integration
runner = CliRunner()


def choice_data(review: dict[str, Any]) -> dict[str, Any]:
    doc = review["document"]
    return {
        "schema_version": 1,
        "decision_version": "metadata-field-decisions-v1",
        "metadata_version": doc["metadata_version"],
        "plan_sha256": doc["plan_sha256"],
        "wording_document_sha256": doc["wording_document_sha256"],
        "metadata_selection_sha256": doc["metadata_selection_sha256"],
        "metadata_document_sha256": review["document_sha256"],
        "fields": [
            {
                "source_ref": f["source_ref"],
                "decision": "approve",
                "reason": "Fictional user reviewed this exact metadata snapshot.",
            }
            for f in doc["fields"]
        ],
    }


@pytest.fixture
def metadata_decision_args(
    sample_source: str, sample_path: Path, job_path: Path, mock_response_path: Path, tmp_path: Path
) -> list[str]:
    profile = tmp_path / "profile.md"
    profile.write_text(
        sample_source.replace("min_bullets_per_entry: 1", "min_bullets_per_entry: 0")
    )
    common = [
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
    seed = runner.invoke(app, ["review-resume", *common])
    assert seed.exit_code == 0, seed.output
    draft = tmp_path / "draft.json"
    draft.write_text(json.dumps(json.loads(seed.stdout)["document"]))
    fields = tmp_path / "metadata-fields.json"
    fields.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "person_fields": ["name", "links"],
                "entries": [{"entry_id": "proj_queue", "fields": ["end_date"]}],
            }
        )
    )
    args = ["review-metadata", *common, "--draft", str(draft), "--metadata-selection", str(fields)]
    inspected = runner.invoke(app, args)
    assert inspected.exit_code == 0, inspected.output
    choices = tmp_path / "decisions.json"
    choices.write_text(json.dumps(choice_data(json.loads(inspected.stdout))))
    return [*args, "--decisions", str(choices), "--confirm-decisions"]


def test_installed_metadata_attestations_are_read_only_and_not_wording_approval(
    metadata_decision_args: list[str],
    tmp_path: Path,
) -> None:
    before = {p: p.read_bytes() for p in tmp_path.iterdir()}
    result = subprocess.run(
        [sys.executable, "-m", "resumeforge", *metadata_decision_args],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
        timeout=10,
    )
    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report["decision_version"] == "metadata-field-decisions-v1"
    assert report["status"] == "metadata_fields_approved_by_user"
    assert report["scope"] == "selected_metadata_only" and not report["rendering_authorized"]
    assert all(f["review_status"] == "approved_by_user" for f in report["fields"])
    assert all(
        f["review_status"] == "pending_review" for f in report["review"]["document"]["fields"]
    )
    assert all(
        b["review_status"] == "pending_review"
        for b in report["review"]["wording_review"]["bullets"]
    )
    assert "alex@example.com" not in result.stdout
    assert "no inference" in result.stderr
    assert before == {p: p.read_bytes() for p in tmp_path.iterdir()}


@pytest.mark.parametrize(
    "mode", ["partial", "reject", "missing_links", "missing_date", "plan_conflict", "empty"]
)
def test_pending_rejected_unset_and_conflicted_metadata_keep_complete_reports(
    metadata_decision_args: list[str],
    mode: str,
) -> None:
    args = metadata_decision_args
    inspect_args = args[: args.index("--decisions")]
    profile = Path(args[args.index("--profile") + 1])
    if mode in ("missing_links", "missing_date", "plan_conflict"):
        text = profile.read_text()
        text = (
            text.replace("  links:\n    - https://example.com/alex", "  links: []")
            if mode == "missing_links"
            else text.replace("    end_date: present\n", "")
            if mode == "missing_date"
            else text.replace("min_bullets_per_entry: 0", "min_bullets_per_entry: 1")
        )
        profile.write_text(text)
        common = args[1 : args.index("--draft")]
        seed = runner.invoke(app, ["review-resume", *common])
        assert seed.exit_code == (3 if mode == "plan_conflict" else 0), seed.output
        Path(args[args.index("--draft") + 1]).write_text(
            json.dumps(json.loads(seed.stdout)["document"])
        )
    elif mode == "empty":
        Path(args[args.index("--metadata-selection") + 1]).write_text(
            '{"schema_version":1,"person_fields":[],"entries":[]}'
        )
    inspected = runner.invoke(app, inspect_args)
    assert inspected.exit_code == (3 if mode == "plan_conflict" else 0), inspected.output
    review = json.loads(inspected.stdout)
    choices = choice_data(review)
    if mode == "partial":
        choices["fields"] = choices["fields"][:1]
    elif mode == "reject":
        choices["fields"][0]["decision"] = "reject"
    Path(args[args.index("--decisions") + 1]).write_text(json.dumps(choices))
    with (
        patch("socket.socket", side_effect=AssertionError("Offline")),
        patch("resumeforge.cli.OllamaProvider", side_effect=AssertionError("No model")),
    ):
        result = runner.invoke(app, args)
    assert result.exit_code == 3, result.output
    report = json.loads(result.stdout)
    assert report["status"] == {"reject": "has_rejections", "plan_conflict": "blocked_by_plan"}.get(
        mode, "needs_review"
    )
    assert report["review"]["document"] == review["document"]
    assert not report["rendering_authorized"]
    if mode in ("missing_links", "missing_date"):
        assert any(
            f["source_value_missing"] and f["review_status"] == "pending_review"
            for f in report["fields"]
        )
        assert report["review"]["findings"]


@pytest.mark.parametrize("mode", ["no_source_ack", "no_decision_ack", "ack_without_file"])
def test_metadata_confirmation_errors_precede_source_io(
    metadata_decision_args: list[str], mode: str
) -> None:
    args = metadata_decision_args.copy()
    if mode == "no_source_ack":
        args.remove("--confirm-review")
    elif mode == "no_decision_ack":
        args.remove("--confirm-decisions")
    else:
        index = args.index("--decisions")
        del args[index : index + 2]
    with (
        patch("resumeforge.cli.load_job", side_effect=AssertionError("No job read")),
        patch("resumeforge.cli.load_profile", side_effect=AssertionError("No profile read")),
        patch(
            "resumeforge.cli.load_metadata_decisions",
            side_effect=AssertionError("No decision read"),
        ),
    ):
        result = runner.invoke(app, args)
    assert result.exit_code == 2 and result.stdout == ""


@pytest.mark.parametrize(
    "mode",
    [
        "malformed",
        "unknown_ref",
        "stale_hash",
        "stale_source",
        "wrong_policy",
        "inspection",
        "bullet_format",
        "missing_file",
        "output_limit",
    ],
)
def test_bad_metadata_decisions_fail_without_partial_json_or_input_disclosure(
    metadata_decision_args: list[str],
    mode: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    args = metadata_decision_args
    path = Path(args[args.index("--decisions") + 1])
    data = json.loads(path.read_text())
    if mode == "malformed":
        data = {"private-field": "private-value"}
    elif mode == "unknown_ref":
        data["fields"][0]["source_ref"] = "person.private_unknown"
    elif mode == "stale_hash":
        data["metadata_document_sha256"] = "0" * 64
    elif mode == "stale_source":
        profile = Path(args[args.index("--profile") + 1])
        profile.write_text(profile.read_text().replace("Alex Example", "private-name"))
    elif mode == "wrong_policy":
        data["decision_version"] = "private-policy"
    elif mode == "inspection":
        data = json.loads(runner.invoke(app, args[: args.index("--decisions")]).stdout)
    elif mode == "bullet_format":
        data = {"schema_version": 3, "review_version": "resume-draft-review-v3", "bullets": []}
    elif mode == "missing_file":
        args[args.index("--decisions") + 1] = str(path.with_name("absent.json"))
    else:
        monkeypatch.setattr("resumeforge.resume.metadata_decisions.MAX_INPUT_BYTES", 4096)
    path.write_text(json.dumps(data))
    result = runner.invoke(app, args)
    assert result.exit_code == 1 and result.stdout == ""
    assert "private-" not in result.output and "private_unknown" not in result.output
    assert "Traceback" not in result.output


def test_invalid_metadata_decision_fields_fail_before_profile_read(
    metadata_decision_args: list[str],
) -> None:
    path = Path(metadata_decision_args[metadata_decision_args.index("--decisions") + 1])
    path.write_text('{"private-field":"private-value"}')
    with patch("resumeforge.cli.load_profile", side_effect=AssertionError("No profile read")):
        result = runner.invoke(app, metadata_decision_args)
    assert result.exit_code == 1 and result.stdout == ""


def test_metadata_approval_never_clears_edited_wording_findings(
    metadata_decision_args: list[str],
) -> None:
    args = metadata_decision_args
    draft_path = Path(args[args.index("--draft") + 1])
    draft = json.loads(draft_path.read_text())
    draft["sections"][1]["entries"][0]["bullets"][0]["text"] = "Owned 99 endpoints."
    draft_path.write_text(json.dumps(draft))
    inspected = runner.invoke(app, args[: args.index("--decisions")])
    assert inspected.exit_code == 0, inspected.output
    review = json.loads(inspected.stdout)
    Path(args[args.index("--decisions") + 1]).write_text(json.dumps(choice_data(review)))
    result = runner.invoke(app, args)
    assert result.exit_code == 0, result.output
    report = json.loads(result.stdout)
    assert report["status"] == "metadata_fields_approved_by_user"
    bullet = report["review"]["wording_review"]["bullets"][0]
    assert bullet["findings"] and bullet["review_status"] == "pending_review"
    assert not report["rendering_authorized"]


def test_help_distinguishes_metadata_decisions_from_provider_activation() -> None:
    result = runner.invoke(app, ["review-metadata", "--help"])
    assert result.exit_code == 0
    text = Text.from_ansi(result.stdout).plain
    assert "--decisions" in text and "--confirm-decisions" in text
    assert "--provider" not in text
