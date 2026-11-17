"""Evaluate only the fixed fictional corpus; default to offline reference replay."""

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Literal

from resumeforge.inputs import InputError
from resumeforge.jobs import JobAnalysisError, analyze_job, load_job
from resumeforge.jobs.evaluation import EvaluationError, EvaluationReport, evaluate_analysis
from resumeforge.providers import (
    FakeProvider,
    OllamaProvider,
    ProviderError,
    StructuredOutputProvider,
)
from resumeforge.providers.ollama import (
    DEFAULT_MODEL,
    DEFAULT_OUTPUT_TOKENS,
    DEFAULT_PORT,
    DEFAULT_TIMEOUT,
)

CASES = {
    "backend_intern": "backend_intern.md",
    "missing_metadata": "missing_metadata.txt",
    "mixed_priority": "evaluation/mixed_priority.md",
    "negated_requirement": "evaluation/negated_requirement.txt",
    "untrusted_instructions": "evaluation/untrusted_instructions.md",
    "regulated_unicode": "evaluation/regulated_unicode.txt",
}


@dataclass(frozen=True)
class CaseResult:
    case_id: str
    status: Literal["exact_match", "mismatch", "validation_failed"]
    report: EvaluationReport | None
    error: str | None


def run_case(
    case_id: str,
    corpus_root: Path,
    provider: StructuredOutputProvider | None = None,
    responses_dir: Path | None = None,
) -> CaseResult:
    """One validated result or one explicit failure; never drop a failing case from totals."""
    source = corpus_root / CASES[case_id]
    reference = source.with_suffix(".response.json")
    try:
        document = load_job(source)
        expected = analyze_job(document, FakeProvider.from_file(reference)).requirements
        if provider is None:
            response = responses_dir / f"{case_id}.response.json" if responses_dir else reference
            provider = FakeProvider.from_file(response)
        actual = analyze_job(document, provider)
        report = evaluate_analysis(document, expected, actual)
    except (InputError, JobAnalysisError, EvaluationError) as error:
        return CaseResult(case_id, "validation_failed", None, str(error))
    return CaseResult(case_id, "exact_match" if report.exact_match else "mismatch", report, None)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--case", action="append", choices=CASES, help="Select cases; default: all."
    )
    parser.add_argument(
        "--responses-dir", type=Path, help="Replay <case>.response.json files offline."
    )
    parser.add_argument("--provider", choices=("fake", "ollama"), default="fake")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--ollama-port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT)
    parser.add_argument("--max-output-tokens", type=int, default=DEFAULT_OUTPUT_TOKENS)
    return parser


def main(argv: list[str] | None = None, *, corpus_root: Path) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    provider: StructuredOutputProvider | None = None
    if args.provider == "ollama":
        if args.responses_dir is not None:
            parser.error("--responses-dir cannot be combined with --provider ollama")
        try:
            provider = OllamaProvider(
                args.model, args.ollama_port, args.timeout, args.max_output_tokens
            )
        except ProviderError as error:
            parser.error(str(error))
        mode = "live_local"
    else:
        if (
            args.model != DEFAULT_MODEL
            or args.ollama_port != DEFAULT_PORT
            or args.timeout != DEFAULT_TIMEOUT
            or args.max_output_tokens != DEFAULT_OUTPUT_TOKENS
        ):
            parser.error("Ollama options require --provider ollama")
        mode = "response_replay" if args.responses_dir is not None else "reference_replay"
    selected = list(dict.fromkeys(args.case or CASES))
    results = [run_case(case_id, corpus_root, provider, args.responses_dir) for case_id in selected]
    exact_matches = sum(case.status == "exact_match" for case in results)
    print(
        json.dumps(
            {
                "benchmark_version": "synthetic-jobs-v1",
                "mode": mode,
                "total_cases": len(results),
                "validated_cases": sum(case.status != "validation_failed" for case in results),
                "exact_match_cases": exact_matches,
                "cases": [asdict(case) for case in results],
                "limitations": [
                    "Exact-text comparison is not semantic proof or a general accuracy benchmark.",
                    "Reference replay tests the harness, not extraction by a language model.",
                    "Unexpected texts may be valid alternate spans and require human review.",
                ],
            },
            ensure_ascii=False,
            allow_nan=False,
            indent=2,
        )
    )
    return 0 if exact_matches == len(results) else 1
