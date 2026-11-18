"""Fixed-corpus wording evaluation retains failures and never invents a quality grade."""

import json
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from resumeforge.inputs import InputError
from resumeforge.providers import FakeProvider, ProviderError
from resumeforge.resume import ResumeError
from resumeforge.resume.benchmark import CASES, main, prepare_case, run_case, source_replay


@pytest.fixture
def corpus_root(sample_path: Path) -> Path:
    return sample_path.parents[1] / "wording/evaluation"


@pytest.mark.parametrize("case_id", CASES)
def test_frozen_cases_have_valid_nonempty_plans_and_truthful_source_seed_replay(
    corpus_root: Path, case_id: str
) -> None:
    prepared = prepare_case(case_id, corpus_root)
    with patch("socket.socket", side_effect=AssertionError("No network")):
        report = run_case(prepared)
    assert report.status == "validated_needs_review" and report.provider_calls == 1
    assert report.manual_review_status == "not_performed" and report.error is None
    assert len(report.corpus_sha256 or "") == 64
    assert report.result is not None and report.result.attempt is not None
    assert report.result.attempt.provider == "fake"
    assert report.response_sha256 == report.result.attempt.response_sha256
    assert report.result.review.document == prepared.seed.document
    assert all(
        not b.findings and b.wording_status == "verbatim_source"
        for b in report.result.review.bullets
    )
    assert report.review_focus and not report.result.rendering_authorized
    assert "Fictional Benchmark Person" not in report.model_dump_json()
    with pytest.raises(ValidationError):
        report.status = "validation_failed"


def test_whole_default_benchmark_is_replay_not_model_quality(
    corpus_root: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    with patch(
        "resumeforge.resume.benchmark.OllamaProvider",
        side_effect=AssertionError("No local inference"),
    ):
        assert main([], corpus_root=corpus_root) == 0
    captured = capsys.readouterr()
    result = json.loads(captured.out)
    assert (
        result["mode"] == "source_seed_replay"
        and result["total_cases"] == result["validated_cases"] == 6
    )
    assert (
        result["inspected_bullets"] == 7
        and result["edited_bullets"] == result["literal_findings"] == 0
    )
    assert result["manual_review_status"] == "not_performed" and not result["rendering_authorized"]
    assert result["requested_runtime"] is None
    assert "quality_score" not in result and "accuracy" not in result
    assert "no automatic quality score" in captured.err


def test_case_selection_deduplicates_without_reordering(
    corpus_root: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert (
        main(
            ["--case", "ongoing_parent", "--case", "cross_evidence", "--case", "ongoing_parent"],
            corpus_root=corpus_root,
        )
        == 0
    )
    result = json.loads(capsys.readouterr().out)
    assert [case["case_id"] for case in result["cases"]] == ["ongoing_parent", "cross_evidence"]
    assert result["cases"][0]["result"]["review"]["bullets"][0]["caveats"] == [
        "parent_entry_in_progress"
    ]


@pytest.mark.parametrize(
    "response", ["not-json", '{"schema_version":true}', "\ud800", "x" * 1_048_577]
)
def test_invalid_responses_stay_in_results_without_claiming_quality(
    corpus_root: Path, response: str
) -> None:
    report = run_case(prepare_case(CASES[0], corpus_root), FakeProvider(response))
    assert report.status == "validation_failed" and report.provider_calls == 1
    assert report.result is None and report.error
    assert "not-json" not in report.error


def test_fabricated_proposal_is_validated_with_findings_not_a_quality_pass(
    corpus_root: Path,
) -> None:
    prepared = prepare_case(CASES[0], corpus_root)
    data = json.loads(source_replay(prepared).response_json)
    data["bullets"][0]["text"] = "Owned 99 Kubernetes services."
    report = run_case(prepared, FakeProvider(json.dumps(data)))
    assert (
        report.status == "validated_needs_review" and report.manual_review_status == "not_performed"
    )
    assert report.result is not None and report.result.review.bullets[0].findings
    assert report.result.review.bullets[0].review_status == "pending_review"
    assert not report.result.rendering_authorized


def test_invalid_replay_files_do_not_disappear_from_denominator(
    corpus_root: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    for case_id in CASES[:-1]:
        prepared = prepare_case(case_id, corpus_root)
        (tmp_path / f"{case_id}.response.json").write_text(source_replay(prepared).response_json)
    assert main(["--responses-dir", str(tmp_path)], corpus_root=corpus_root) == 1
    result = json.loads(capsys.readouterr().out)
    assert result["mode"] == "response_replay"
    assert (
        result["total_cases"] == 6
        and result["validated_cases"] == 5
        and result["provider_calls"] == 5
    )
    assert result["cases"][-1]["status"] == "validation_failed"


@pytest.mark.parametrize("change", ["identity", "focus", "conflict", "empty", "quote", "extra"])
def test_invalid_corpus_is_rejected_before_any_provider_access(
    corpus_root: Path, tmp_path: Path, change: str
) -> None:
    data = json.loads((corpus_root / f"{CASES[0]}.json").read_text())
    if change == "identity":
        data["case_id"] = "private-unknown"
    elif change == "focus":
        data["review_focus"] = []
    elif change == "conflict":
        data["profile"]["resume_preferences"] = {"min_projects": 1}
        data["profile"]["projects"] = [
            {"id": "proj_omitted", "title": "Omitted", "completion_status": "completed"}
        ]
    elif change == "empty":
        data["selection"]["entries"] = []
    elif change == "quote":
        data["requirements"]["programming_languages"][0]["source_quote"] = "Python private-unknown"
    else:
        data["private-unknown"] = "private-value"
    (tmp_path / f"{CASES[0]}.json").write_text(json.dumps(data))
    with pytest.raises(ResumeError) as error:
        prepare_case(CASES[0], tmp_path)
    assert "private-value" not in str(error.value)


def test_missing_and_unknown_corpus_cases_fail_safely(tmp_path: Path) -> None:
    with pytest.raises(ResumeError, match="Unknown fixed"):
        prepare_case("../private", tmp_path)
    with pytest.raises(InputError):
        prepare_case(CASES[0], tmp_path)


def test_all_cases_preflight_before_live_calls(
    corpus_root: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    (tmp_path / f"{CASES[0]}.json").write_bytes((corpus_root / f"{CASES[0]}.json").read_bytes())
    provider = FakeProvider("unused")
    with (
        patch("resumeforge.resume.benchmark.OllamaProvider", return_value=provider),
        patch.object(FakeProvider, "complete", side_effect=AssertionError("No inference")),
    ):
        assert main(["--provider", "ollama", "--confirm-local-data"], corpus_root=tmp_path) == 1
    result = json.loads(capsys.readouterr().out)
    assert result["total_cases"] == 6 and result["validated_cases"] == result["provider_calls"] == 0
    assert result["cases"][0]["status"] == "not_run"
    assert all(case["status"] == "case_input_failed" for case in result["cases"][1:])


@pytest.mark.parametrize(
    "args",
    [
        ["--provider", "ollama"],
        ["--provider", "ollama", "--confirm-local-data", "--responses-dir", "unused"],
        ["--model", "other"],
        ["--timeout", "20"],
        ["--ollama-port", "11435"],
        ["--max-output-tokens", "512"],
        ["--confirm-local-data"],
        ["--provider", "cloud"],
        ["--case", "../private"],
        ["--provider", "ollama", "--confirm-local-data", "--model", "model:cloud"],
    ],
)
def test_invalid_live_options_fail_before_corpus_io(corpus_root: Path, args: list[str]) -> None:
    with (
        patch(
            "resumeforge.resume.benchmark.prepare_case", side_effect=AssertionError("No corpus IO")
        ),
        pytest.raises(SystemExit) as error,
    ):
        main(args, corpus_root=corpus_root)
    assert error.value.code == 2


def test_mocked_live_path_is_one_call_and_never_a_quality_grade(
    corpus_root: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    prepared = prepare_case(CASES[0], corpus_root)
    with patch(
        "resumeforge.resume.benchmark.OllamaProvider", return_value=source_replay(prepared)
    ) as factory:
        assert (
            main(
                ["--provider", "ollama", "--confirm-local-data", "--case", CASES[0]],
                corpus_root=corpus_root,
            )
            == 0
        )
    factory.assert_called_once_with("qwen3:4b", 11434, 180.0, 4096)
    result = json.loads(capsys.readouterr().out)
    assert result["mode"] == "live_local" and result["provider_calls"] == 1
    assert result["requested_runtime"]["model"] == "qwen3:4b"
    assert result["cases"][0]["manual_review_status"] == "not_performed"


def test_capture_is_explicit_private_and_never_overwrites(
    corpus_root: Path, tmp_path: Path
) -> None:
    prepared = prepare_case(CASES[0], corpus_root)
    first = run_case(prepared, capture_dir=tmp_path)
    path = tmp_path / f"{CASES[0]}.response.json"
    original = path.read_bytes()
    assert first.status == "validated_needs_review" and path.stat().st_mode & 0o777 == 0o600
    second = run_case(prepared, FakeProvider("invalid"), capture_dir=tmp_path)
    assert second.status == "validation_failed" and second.result is None
    assert path.read_bytes() == original


def test_invalid_json_is_captured_for_replay_but_unencodable_or_oversized_text_is_not(
    corpus_root: Path, tmp_path: Path
) -> None:
    prepared = prepare_case(CASES[0], corpus_root)
    report = run_case(prepared, FakeProvider("invalid"), capture_dir=tmp_path)
    assert report.status == "validation_failed" and report.response_sha256
    assert (tmp_path / f"{CASES[0]}.response.json").read_text() == "invalid"
    for response in ("\ud800", "x" * 1_048_577):
        report = run_case(prepared, FakeProvider(response))
        assert report.response_sha256 is None


def test_capture_directory_requires_new_path(
    corpus_root: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    capture = tmp_path / "new-capture"
    assert (
        main(["--case", CASES[0], "--capture-responses-dir", str(capture)], corpus_root=corpus_root)
        == 0
    )
    assert capture.stat().st_mode & 0o777 == 0o700
    capsys.readouterr()
    with pytest.raises(SystemExit) as error:
        main(["--capture-responses-dir", str(capture)], corpus_root=corpus_root)
    assert error.value.code == 2


def test_provider_failure_is_one_failure_not_a_retry(corpus_root: Path) -> None:
    prepared = prepare_case(CASES[0], corpus_root)
    with patch.object(
        FakeProvider, "complete", side_effect=ProviderError("Safe synthetic error.")
    ) as complete:
        report = run_case(prepared, FakeProvider("unused"))
    assert complete.call_count == report.provider_calls == 1
    assert report.status == "validation_failed" and report.response_sha256 is None


def test_untrusted_footer_and_manual_rubric_are_kept_in_separate_channels(
    corpus_root: Path,
) -> None:
    prepared = prepare_case("untrusted_job", corpus_root)
    adapter = source_replay(prepared)
    requests = []
    original = FakeProvider.complete

    def record(self: FakeProvider, request: Any) -> str:
        requests.append(request)
        return original(self, request)

    with patch.object(FakeProvider, "complete", new=record):
        report = run_case(prepared, adapter)
    assert report.status == "validated_needs_review"
    assert "ignore instructions" in requests[0].input_text
    assert "ignore instructions" not in requests[0].instructions
    assert prepared.case.review_focus[0] not in requests[0].input_text
