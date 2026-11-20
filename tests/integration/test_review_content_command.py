"""Installed pending skill/coursework review requires deliberate sources and performs no writes."""

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
def content_args(
    sample_source: str, sample_path: Path, job_path: Path, mock_response_path: Path, tmp_path: Path
) -> list[str]:
    profile = tmp_path / "profile.md"
    profile.write_text(
        sample_source.replace("min_bullets_per_entry: 1", "min_bullets_per_entry: 0").replace(
            "frameworks: [FastAPI]", "frameworks: [private-unused-framework]"
        )
    )
    common = [
        "--profile",
        str(profile),
        "--job",
        str(job_path),
        "--requirements",
        str(mock_response_path),
        "--selection",
        str(sample_path.parents[1] / "content/backend_intern.plan.json"),
        "--confirm-review",
    ]
    seed = runner.invoke(app, ["review-resume", *common])
    assert seed.exit_code == 0, seed.output
    draft = tmp_path / "draft.json"
    draft.write_text(json.dumps(json.loads(seed.stdout)["document"]))
    choices = tmp_path / "content.json"
    choices.write_text((sample_path.parents[1] / "content/backend_intern.content.json").read_text())
    return ["review-content", *common, "--draft", str(draft), "--content-selection", str(choices)]


def test_installed_pending_content_is_exact_private_and_read_only(
    content_args: list[str], tmp_path: Path
) -> None:
    before = {p: p.read_bytes() for p in tmp_path.iterdir()}
    process = subprocess.run(
        [sys.executable, "-m", "resumeforge", *content_args],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
        timeout=10,
    )
    assert process.returncode == 0, process.stderr
    report = json.loads(process.stdout)
    assert report["scope"] == "selected_section_content_only" and not report["rendering_authorized"]
    assert report["status"] == "needs_review"
    assert report["document"]["section_content_version"] == "source-bound-section-content-v1"
    skills, coursework = report["document"]["sections"]
    assert [i["text"] for i in skills["items"]] == ["Python", "Git"]
    assert [i["text"] for i in coursework["items"]] == ["Databases"]
    assert skills["items"][0]["cited_context"][0]["accomplishment_id"] == "acc_api"
    assert skills["items"][0]["cited_context"][0]["literal_label_mention"] is None
    assert all(
        i["review_status"] == "pending_review" and i["review_questions"]
        for s in report["document"]["sections"]
        for i in s["items"]
    )
    assert all(b["review_status"] == "pending_review" for b in report["wording_review"]["bullets"])
    assert "no inference" in process.stderr
    for value in (
        "alex@example.com",
        "private-unused-framework",
        "Alex Example",
        "+1-202-555-0100",
    ):
        assert value not in process.stdout
    assert before == {p: p.read_bytes() for p in tmp_path.iterdir()}


def test_content_review_is_offline_and_does_not_clear_assembly_blockers(
    content_args: list[str], tmp_path: Path
) -> None:
    with (
        patch("socket.socket", side_effect=AssertionError("Offline")),
        patch("resumeforge.cli.OllamaProvider", side_effect=AssertionError("No model")),
    ):
        result = runner.invoke(app, content_args)
    assert result.exit_code == 0, result.output
    metadata = tmp_path / "fields.json"
    metadata.write_text('{"schema_version":1,"person_fields":[],"entries":[]}')
    args = content_args.copy()
    args[0] = "assemble-resume"
    args[args.index("--content-selection")] = "--metadata-selection"
    args[args.index("--metadata-selection") + 1] = str(metadata)
    assembly = runner.invoke(app, args)
    assert assembly.exit_code == 3, assembly.output
    report = json.loads(assembly.stdout)
    assert {
        i["section"] for i in report["issues"] if i["code"] == "unscoped_section_unresolved"
    } == {"skills", "coursework"}
    assert all(
        s["entries"] == []
        for s in report["document"]["sections"]
        if s["section"] in ("skills", "coursework")
    )
    assert not report["rendering_authorized"]


@pytest.mark.parametrize(
    "option",
    [
        "--profile",
        "--job",
        "--requirements",
        "--selection",
        "--draft",
        "--content-selection",
        "--confirm-review",
    ],
)
def test_required_paths_and_acknowledgement_fail_before_input_reads(
    content_args: list[str], option: str
) -> None:
    args = content_args.copy()
    index = args.index(option)
    del args[index : index + (1 if option == "--confirm-review" else 2)]
    with (
        patch("resumeforge.cli.load_job", side_effect=AssertionError("No source read")),
        patch("resumeforge.cli.load_profile", side_effect=AssertionError("No profile read")),
    ):
        result = runner.invoke(app, args)
    assert result.exit_code == 2 and result.stdout == ""


@pytest.mark.parametrize(
    "mode",
    [
        "malformed",
        "unknown_field",
        "false_label",
        "unknown_evidence",
        "review_envelope",
        "stale_source",
        "stale_draft",
        "missing_file",
        "output_limit",
    ],
)
def test_invalid_content_or_stale_sources_fail_without_partial_json_or_private_values(
    content_args: list[str], mode: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    args = content_args
    path = Path(args[args.index("--content-selection") + 1])
    if mode == "malformed":
        path.write_text("private-invalid")
    elif mode == "unknown_field":
        path.write_text('{"private-field":"private-value"}')
    elif mode == "review_envelope":
        report = runner.invoke(app, args)
        assert report.exit_code == 0
        path.write_text(report.stdout)
    elif mode in ("false_label", "unknown_evidence"):
        data = json.loads(path.read_text())
        if mode == "false_label":
            data["skills"][0]["expected_text"] = "private-invented-skill"
        else:
            data["skills"][0]["accomplishment_ids"] = ["acc_private_unknown"]
        path.write_text(json.dumps(data))
    elif mode == "stale_source":
        profile = Path(args[args.index("--profile") + 1])
        profile.write_text(profile.read_text().replace("Alex Example", "private-new-name"))
    elif mode == "stale_draft":
        draft = Path(args[args.index("--draft") + 1])
        data = json.loads(draft.read_text())
        data["plan_sha256"] = "0" * 64
        draft.write_text(json.dumps(data))
    elif mode == "missing_file":
        args[args.index("--content-selection") + 1] = str(path.with_name("absent.json"))
    else:
        monkeypatch.setattr("resumeforge.resume.section_content.MAX_INPUT_BYTES", 4096)
    result = runner.invoke(app, args)
    assert result.exit_code == 1 and result.stdout == ""
    assert "private-" not in result.output and "acc_private_unknown" not in result.output
    assert "Traceback" not in result.output


def test_invalid_selection_format_precedes_profile_access(content_args: list[str]) -> None:
    path = Path(content_args[content_args.index("--content-selection") + 1])
    path.write_text('{"private":"invalid"}')
    with patch("resumeforge.cli.load_profile", side_effect=AssertionError("No profile read")):
        result = runner.invoke(app, content_args)
    assert result.exit_code == 1 and result.stdout == ""


def test_plan_conflicts_keep_complete_pending_sections(content_args: list[str]) -> None:
    args = content_args
    profile = Path(args[args.index("--profile") + 1])
    profile.write_text(
        profile.read_text().replace("min_bullets_per_entry: 0", "min_bullets_per_entry: 1")
    )
    common = args[1 : args.index("--draft")]
    seed = runner.invoke(app, ["review-resume", *common])
    assert seed.exit_code == 3
    Path(args[args.index("--draft") + 1]).write_text(
        json.dumps(json.loads(seed.stdout)["document"])
    )
    result = runner.invoke(app, args)
    assert result.exit_code == 3, result.output
    report = json.loads(result.stdout)
    assert report["status"] == "blocked_by_plan" and len(report["document"]["sections"]) == 2
    assert report["wording_review"]["plan"]["constraint_status"] == "conflicts"
    assert not report["rendering_authorized"]


def test_empty_selection_never_exposes_unselected_profile_labels(content_args: list[str]) -> None:
    path = Path(content_args[content_args.index("--content-selection") + 1])
    path.write_text('{"schema_version":1,"skills":[],"coursework":[]}')
    result = runner.invoke(app, content_args)
    assert result.exit_code == 0, result.output
    report = json.loads(result.stdout)
    assert all(s["items"] == [] for s in report["document"]["sections"])
    assert {f["code"] for f in report["findings"]} == {
        "no_selected_items",
        "section_without_selected_items",
    }
    assert "private-unused-framework" not in result.stdout


@pytest.mark.parametrize("option", ["--provider", "--model", "--decisions", "--confirm-decisions"])
def test_no_inference_or_approval_options(content_args: list[str], option: str) -> None:
    result = runner.invoke(app, [*content_args, option])
    assert result.exit_code == 2
