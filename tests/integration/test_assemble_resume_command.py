"""Installed assembly is offline, explicit, bounded and never a publication authorization."""

import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from resumeforge.cli import app

pytestmark = pytest.mark.integration
runner = CliRunner()


@pytest.fixture
def assembly_args(
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
    seeded = runner.invoke(app, ["review-resume", *common])
    assert seeded.exit_code == 0, seeded.output
    draft = tmp_path / "draft.json"
    draft.write_text(json.dumps(json.loads(seeded.stdout)["document"]))
    fields = tmp_path / "fields.json"
    fields.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "person_fields": ["name"],
                "entries": [
                    {"entry_id": entry, "fields": ["title"]}
                    for entry in ("edu_example", "exp_example", "proj_queue")
                ],
            }
        )
    )
    args = ["assemble-resume", *common, "--draft", str(draft), "--metadata-selection", str(fields)]
    result = runner.invoke(app, args)
    assert result.exit_code == 3, result.output
    review = json.loads(result.stdout)["review"]
    wording = review["wording_review"]
    Path(tmp_path / "bullets.json").write_text(
        json.dumps(
            {
                "schema_version": 3,
                "review_version": wording["review_version"],
                "plan_sha256": wording["document"]["plan_sha256"],
                "document_sha256": wording["document_sha256"],
                "findings_sha256": wording["findings_sha256"],
                "fragments_sha256": wording["fragments_sha256"],
                "bullets": [
                    {
                        "bullet_id": b["bullet_id"],
                        "decision": "approve",
                        "reason": "Synthetic wording gate assertion.",
                        "acknowledged_finding_ids": [],
                        "fragment_decisions": [],
                    }
                    for b in wording["bullets"]
                ],
            }
        )
    )
    doc = review["document"]
    Path(tmp_path / "metadata.json").write_text(
        json.dumps(
            {
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
                        "reason": "Synthetic metadata gate assertion.",
                    }
                    for f in doc["fields"]
                ],
            }
        )
    )
    return args


def decision_args(args: list[str], kind: str) -> list[str]:
    directory = Path(args[args.index("--profile") + 1]).parent
    return [
        "--" + kind + "-decisions",
        str(directory / ("bullets.json" if kind == "bullet" else "metadata.json")),
        "--confirm-" + kind + "-decisions",
    ]


def test_installed_assembly_combines_components_without_implicit_disclosure_or_writes(
    assembly_args: list[str], tmp_path: Path
) -> None:
    before = {p: p.read_bytes() for p in tmp_path.iterdir()}
    args = (
        assembly_args
        + decision_args(assembly_args, "bullet")
        + decision_args(assembly_args, "metadata")
    )
    process = subprocess.run(
        [sys.executable, "-m", "resumeforge", *args],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
        timeout=10,
    )
    assert process.returncode == 0, process.stderr
    result = json.loads(process.stdout)
    assert result["status"] == "components_reviewed" and result["issues"] == []
    assert result["scope"] == "structured_components_only" and not result["rendering_authorized"]
    assert result["document"]["status"] == "needs_review"
    assert result["bullet_attestations"]["scope"] == "bullet_wording_only"
    assert result["metadata_attestations"]["scope"] == "selected_metadata_only"
    assert all(
        f["review_status"] == "pending_review" for f in result["review"]["document"]["fields"]
    )
    assert "alex@example.com" not in process.stdout and "+1-202-555-0100" not in process.stdout
    assert "no inference" in process.stderr
    assert before == {p: p.read_bytes() for p in tmp_path.iterdir()}


@pytest.mark.parametrize("kind", ["none", "bullet", "metadata"])
def test_missing_decisions_are_reported_with_complete_pending_content(
    assembly_args: list[str], kind: str
) -> None:
    options = [] if kind == "none" else decision_args(assembly_args, kind)
    with (
        patch("socket.socket", side_effect=AssertionError("Offline")),
        patch("resumeforge.cli.OllamaProvider", side_effect=AssertionError("No inference")),
    ):
        result = runner.invoke(app, assembly_args + options)
    assert result.exit_code == 3, result.output
    data = json.loads(result.stdout)
    assert data["status"] == "needs_review" and data["issues"]
    assert len(data["document"]["sections"]) == 3
    assert not data["rendering_authorized"]


@pytest.mark.parametrize(
    "mode",
    [
        "no_review",
        "bullet_unconfirmed",
        "metadata_unconfirmed",
        "bullet_flag_only",
        "metadata_flag_only",
    ],
)
def test_usage_errors_precede_all_source_io(assembly_args: list[str], mode: str) -> None:
    args = assembly_args.copy()
    if mode == "no_review":
        args.remove("--confirm-review")
    else:
        kind = mode.split("_")[0]
        options = decision_args(args, kind)
        args += options[:2] if "unconfirmed" in mode else options[2:]
    with (
        patch("resumeforge.cli.load_job", side_effect=AssertionError("No reads")),
        patch("resumeforge.cli.load_profile", side_effect=AssertionError("No reads")),
    ):
        result = runner.invoke(app, args)
    assert result.exit_code == 2 and result.stdout == ""


@pytest.mark.parametrize("kind", ["bullet", "metadata"])
@pytest.mark.parametrize("bad", ["malformed", "wrong_format", "stale", "unknown", "missing_file"])
def test_invalid_decisions_fail_without_partial_json_or_private_error_values(
    assembly_args: list[str], kind: str, bad: str
) -> None:
    options = decision_args(assembly_args, kind)
    path = Path(options[1])
    data = json.loads(path.read_text())
    if bad == "malformed":
        data = {"private-field": "private-value"}
    elif bad == "wrong_format":
        other = "metadata" if kind == "bullet" else "bullet"
        data = json.loads(Path(decision_args(assembly_args, other)[1]).read_text())
    elif bad == "stale":
        data["plan_sha256"] = "0" * 64
    elif bad == "unknown":
        data["bullets" if kind == "bullet" else "fields"][0][
            "bullet_id" if kind == "bullet" else "source_ref"
        ] = "bullet_private_unknown" if kind == "bullet" else "person.private_unknown"
    else:
        options[1] = str(path.with_name("absent.json"))
    path.write_text(json.dumps(data))
    result = runner.invoke(app, assembly_args + options)
    assert result.exit_code == 1 and result.stdout == ""
    assert "private-" not in result.output and "private_unknown" not in result.output
    assert "Traceback" not in result.output


@pytest.mark.parametrize("kind", ["bullet", "metadata"])
def test_bad_decision_format_is_rejected_before_profile_read(
    assembly_args: list[str], kind: str
) -> None:
    options = decision_args(assembly_args, kind)
    Path(options[1]).write_text('{"private":"invalid"}')
    with patch("resumeforge.cli.load_profile", side_effect=AssertionError("No profile read")):
        result = runner.invoke(app, assembly_args + options)
    assert result.exit_code == 1 and result.stdout == ""


def test_conflicted_assembly_retains_sources_and_required_content(assembly_args: list[str]) -> None:
    args = assembly_args
    profile = Path(args[args.index("--profile") + 1])
    profile.write_text(
        profile.read_text().replace("min_bullets_per_entry: 0", "min_bullets_per_entry: 1")
    )
    common = args[1 : args.index("--draft")]
    seeded = runner.invoke(app, ["review-resume", *common])
    assert seeded.exit_code == 3
    Path(args[args.index("--draft") + 1]).write_text(
        json.dumps(json.loads(seeded.stdout)["document"])
    )
    result = runner.invoke(app, args)
    assert result.exit_code == 3, result.output
    report = json.loads(result.stdout)
    assert report["status"] == "blocked_by_plan"
    assert any(i["code"] == "plan_conflict" for i in report["issues"])
    assert report["document"]["sections"][0]["entries"][0]["bullets"] == []


def test_assembly_output_limit_and_stale_sources_fail_without_partial_json(
    assembly_args: list[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("resumeforge.resume.assembly.MAX_INPUT_BYTES", 1)
    result = runner.invoke(app, assembly_args)
    assert result.exit_code == 1 and result.stdout == ""
    assert "output byte limit" in result.output
    profile = Path(assembly_args[assembly_args.index("--profile") + 1])
    profile.write_text(profile.read_text().replace("Alex Example", "private-name"))
    result = runner.invoke(app, assembly_args)
    assert result.exit_code == 1 and result.stdout == "" and "private-name" not in result.output


@pytest.mark.parametrize("option", ["--provider", "--model", "--decisions", "--confirm-decisions"])
def test_no_implicit_inference_or_combined_approval_option(
    assembly_args: list[str], option: str
) -> None:
    result = runner.invoke(app, [*assembly_args, option])
    assert result.exit_code == 2


def test_assembly_output_is_not_valid_draft_input(assembly_args: list[str]) -> None:
    result = runner.invoke(app, assembly_args)
    report = json.loads(result.stdout)
    draft = Path(assembly_args[assembly_args.index("--draft") + 1])
    draft.write_text(json.dumps(report["document"]))
    result = runner.invoke(app, assembly_args)
    assert result.exit_code == 1 and result.stdout == ""
