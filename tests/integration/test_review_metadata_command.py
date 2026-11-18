"""Metadata exposure is explicit, offline and pending; ordinary reviews keep contact private."""

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
def metadata_args(
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
    assert "alex@example.com" not in seed.stdout
    draft = tmp_path / "draft.json"
    draft.write_text(json.dumps(json.loads(seed.stdout)["document"]))
    fields = tmp_path / "fields.json"
    fields.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "person_fields": [],
                "entries": [{"entry_id": "proj_queue", "fields": ["title", "end_date"]}],
            }
        )
    )
    return ["review-metadata", *common, "--draft", str(draft), "--metadata-selection", str(fields)]


@pytest.mark.parametrize("exposure", ["none", "email", "links"])
def test_installed_metadata_command_is_selective_read_only_and_pending(
    metadata_args: list[str],
    tmp_path: Path,
    exposure: str,
) -> None:
    fields_path = Path(metadata_args[metadata_args.index("--metadata-selection") + 1])
    fields = json.loads(fields_path.read_text())
    if exposure != "none":
        fields["person_fields"] = [exposure]
        fields_path.write_text(json.dumps(fields))
    before = {p: p.read_bytes() for p in tmp_path.iterdir()}
    process = subprocess.run(
        [sys.executable, "-m", "resumeforge", *metadata_args],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
        timeout=10,
    )
    assert process.returncode == 0, process.stderr
    report = json.loads(process.stdout)
    assert report["scope"] == "selected_metadata_only" and not report["rendering_authorized"]
    assert report["status"] == "needs_review"
    assert report["document"]["metadata_version"] == "source-bound-metadata-v1"
    values = {f["source_ref"]: f["value"] for f in report["document"]["fields"]}
    assert values["projects.proj_queue.end_date"] == "present"
    assert ("alex@example.com" in process.stdout) == (exposure == "email")
    assert ("person.links" in values) == (exposure == "links")
    assert all(f["review_status"] == "pending_review" for f in report["document"]["fields"])
    assert report["wording_review"]["document"]["status"] == "needs_review"
    assert "no inference" in process.stderr and "Traceback" not in process.stderr
    assert before == {p: p.read_bytes() for p in tmp_path.iterdir()}


@pytest.mark.parametrize(
    "missing",
    [
        "--profile",
        "--job",
        "--requirements",
        "--selection",
        "--draft",
        "--metadata-selection",
        "--confirm-review",
    ],
)
def test_metadata_usage_errors_precede_all_io(metadata_args: list[str], missing: str) -> None:
    args = metadata_args.copy()
    index = args.index(missing)
    del args[index : index + (1 if missing == "--confirm-review" else 2)]
    with (
        patch("resumeforge.cli.load_job", side_effect=AssertionError("No job read")),
        patch("resumeforge.cli.load_profile", side_effect=AssertionError("No profile read")),
    ):
        result = runner.invoke(app, args)
    assert result.exit_code == 2 and result.stdout == ""


@pytest.mark.parametrize(
    "mode", ["malformed", "absent_entry", "stale", "missing_file", "self_approval", "oversized"]
)
def test_metadata_errors_never_emit_partial_json_or_private_input_values(
    metadata_args: list[str],
    mode: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fields_path = Path(metadata_args[metadata_args.index("--metadata-selection") + 1])
    if mode == "malformed":
        fields_path.write_text('{"private-key":"private-value"}')
    elif mode == "absent_entry":
        fields_path.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "person_fields": [],
                    "entries": [{"entry_id": "exp_private_unknown", "fields": ["title"]}],
                }
            )
        )
    elif mode == "stale":
        profile = Path(metadata_args[metadata_args.index("--profile") + 1])
        profile.write_text(profile.read_text().replace("Demonstration Task Queue", "private-title"))
    elif mode == "missing_file":
        metadata_args[metadata_args.index("--metadata-selection") + 1] = str(
            fields_path.with_name("absent.json")
        )
    elif mode == "self_approval":
        fields = json.loads(fields_path.read_text())
        fields["rendering_authorized"] = True
        fields_path.write_text(json.dumps(fields))
    else:
        monkeypatch.setattr("resumeforge.resume.metadata.MAX_INPUT_BYTES", 1000)
    with (
        patch("socket.socket", side_effect=AssertionError("No network")),
        patch("resumeforge.cli.OllamaProvider", side_effect=AssertionError("No live provider")),
    ):
        result = runner.invoke(app, metadata_args)
    assert result.exit_code == 1 and result.stdout == ""
    assert "private-" not in result.output and "exp_private_unknown" not in result.output
    assert "Traceback" not in result.output


def test_invalid_field_selection_is_rejected_before_profile_access(
    metadata_args: list[str],
) -> None:
    fields_path = Path(metadata_args[metadata_args.index("--metadata-selection") + 1])
    fields_path.write_text('{"private-key":"private-value"}')
    with patch("resumeforge.cli.load_profile", side_effect=AssertionError("No profile read")):
        result = runner.invoke(app, metadata_args)
    assert result.exit_code == 1 and result.stdout == ""


def test_metadata_preserves_complete_plan_conflicts_and_missing_source_values(
    metadata_args: list[str],
) -> None:
    profile = Path(metadata_args[metadata_args.index("--profile") + 1])
    profile.write_text(
        profile.read_text().replace("min_bullets_per_entry: 0", "min_bullets_per_entry: 1")
    )
    common = metadata_args[1 : metadata_args.index("--draft")]
    seed = runner.invoke(app, ["review-resume", *common])
    assert seed.exit_code == 3, seed.output
    Path(metadata_args[metadata_args.index("--draft") + 1]).write_text(
        json.dumps(json.loads(seed.stdout)["document"])
    )
    fields = Path(metadata_args[metadata_args.index("--metadata-selection") + 1])
    fields.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "person_fields": [],
                "entries": [{"entry_id": "edu_example", "fields": ["location", "end_date"]}],
            }
        )
    )
    result = runner.invoke(app, metadata_args)
    assert result.exit_code == 3, result.output
    report = json.loads(result.stdout)
    assert report["status"] == report["wording_review"]["status"] == "blocked_by_plan"
    assert report["document"]["fields"][0]["value"] is None
    assert report["findings"][0]["code"] == "missing_source_value"
    assert report["wording_review"]["plan"]["constraint_status"] == "conflicts"
    assert not report["rendering_authorized"]


@pytest.mark.parametrize("option", ["--provider", "--decisions"])
def test_metadata_command_has_no_inference_or_approval_options(
    metadata_args: list[str], option: str
) -> None:
    result = runner.invoke(app, [*metadata_args, option, "unused"])
    assert result.exit_code == 2 and result.stdout == ""
    help_result = runner.invoke(app, ["review-metadata", "--help"])
    text = Text.from_ansi(help_result.stdout).plain
    assert "--metadata-selection" in text and option not in text
