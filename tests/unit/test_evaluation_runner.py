"""The developer benchmark defaults to replay and keeps validation failures visible."""

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from resumeforge.jobs import JobAnalysisError
from resumeforge.jobs.benchmark import CASES, main, run_case
from resumeforge.providers import StructuredRequest

CORPUS_ROOT = Path(__file__).resolve().parents[2] / "examples/jobs"


@pytest.mark.parametrize("case_id", CASES)
def test_all_hand_authored_references_are_grounded_and_replay_without_network(case_id: str) -> None:
    with patch("socket.socket", side_effect=AssertionError("Network forbidden")):
        result = run_case(case_id, CORPUS_ROOT)
    assert result.status == "exact_match", result.error
    assert result.report is not None
    assert result.report.provider == "fake"


def test_default_run_truthfully_labels_reference_replay(capsys: pytest.CaptureFixture[str]) -> None:
    with patch(
        "resumeforge.jobs.benchmark.OllamaProvider", side_effect=AssertionError("No implicit model")
    ):
        assert main([], corpus_root=CORPUS_ROOT) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["mode"] == "reference_replay"
    assert report["total_cases"] == report["validated_cases"] == report["exact_match_cases"] == 6
    assert len(report["limitations"]) == 3


def test_omitted_tag_is_a_mismatch_not_a_schema_failure(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    reference = json.loads((CORPUS_ROOT / "missing_metadata.response.json").read_text())
    reference["programming_languages"] = reference["programming_languages"][:1]
    (tmp_path / "missing_metadata.response.json").write_text(json.dumps(reference))
    assert (
        main(
            ["--case", "missing_metadata", "--responses-dir", str(tmp_path)],
            corpus_root=CORPUS_ROOT,
        )
        == 1
    )
    report = json.loads(capsys.readouterr().out)
    assert report["mode"] == "response_replay"
    assert report["validated_cases"] == 1
    assert report["exact_match_cases"] == 0
    assert report["cases"][0]["status"] == "mismatch"
    languages = report["cases"][0]["report"]["sections"][3]
    assert languages["missing"] == ["SQL"]


@pytest.mark.parametrize(
    "body", [None, "{}", "not JSON", '{"schema_version":1,"schema_version":1}']
)
def test_missing_or_invalid_results_count_as_failures_without_stopping_other_cases(
    body: str | None, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    if body is not None:
        (tmp_path / "backend_intern.response.json").write_text(body)
    (tmp_path / "missing_metadata.response.json").write_bytes(
        (CORPUS_ROOT / "missing_metadata.response.json").read_bytes()
    )
    assert (
        main(
            [
                "--case",
                "backend_intern",
                "--case",
                "missing_metadata",
                "--responses-dir",
                str(tmp_path),
            ],
            corpus_root=CORPUS_ROOT,
        )
        == 1
    )
    report = json.loads(capsys.readouterr().out)
    assert report["total_cases"] == 2
    assert report["validated_cases"] == report["exact_match_cases"] == 1
    assert report["cases"][0]["status"] == "validation_failed"
    assert report["cases"][0]["report"] is None
    assert report["cases"][1]["status"] == "exact_match"


@pytest.mark.parametrize(
    "arguments",
    [
        ["--provider", "ollama", "--responses-dir", "unused"],
        ["--model", "different-model"],
        ["--provider", "ollama", "--model", "x:cloud"],
        ["--case", "unknown"],
    ],
)
def test_bad_options_fail_before_any_inference(arguments: list[str]) -> None:
    with (
        patch(
            "resumeforge.jobs.benchmark.run_case", side_effect=AssertionError("No case should run")
        ),
        pytest.raises(SystemExit) as error,
    ):
        main(arguments, corpus_root=CORPUS_ROOT)
    assert error.value.code == 2


def test_explicit_local_mode_is_mocked_and_deduplicates_selected_cases(
    capsys: pytest.CaptureFixture[str],
) -> None:
    class Stub:
        name = "ollama"
        model = "synthetic-stub"
        calls = 0

        def complete(self, request: StructuredRequest) -> str:
            self.calls += 1
            assert "Build Python services." in request.input_text
            return (CORPUS_ROOT / "missing_metadata.response.json").read_text()

    provider = Stub()
    with patch("resumeforge.jobs.benchmark.OllamaProvider", return_value=provider):
        assert (
            main(
                [
                    "--provider",
                    "ollama",
                    "--case",
                    "missing_metadata",
                    "--case",
                    "missing_metadata",
                ],
                corpus_root=CORPUS_ROOT,
            )
            == 0
        )
    report = json.loads(capsys.readouterr().out)
    assert report["mode"] == "live_local"
    assert provider.calls == report["total_cases"] == 1
    assert report["cases"][0]["report"]["model"] == "synthetic-stub"


def test_provider_failure_is_reported_without_retry() -> None:
    class FailingProvider:
        name = "synthetic"
        model = "stub"
        calls = 0

        def complete(self, request: StructuredRequest) -> str:
            self.calls += 1
            raise JobAnalysisError("fictional-private-error")

    provider = FailingProvider()
    result = run_case("backend_intern", CORPUS_ROOT, provider)
    assert result.status == "validation_failed"
    assert result.error is not None and "fictional-private-error" not in result.error
    assert provider.calls == 1
