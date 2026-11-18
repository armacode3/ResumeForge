"""Fixed fictional wording evaluation: structural observations, never automatic quality scores."""

import argparse
import json
import sys
from dataclasses import dataclass, field
from hashlib import sha256
from pathlib import Path
from typing import Annotated, Literal

from pydantic import Field

from resumeforge.inputs import MAX_INPUT_BYTES, InputError, read_utf8_file
from resumeforge.jobs import JobDocument, JobRequirements
from resumeforge.planning import PlanSelection
from resumeforge.profile import UserProfile
from resumeforge.providers import (
    FakeProvider,
    OllamaProvider,
    ProviderError,
    StructuredOutputProvider,
)
from resumeforge.providers.base import StructuredRequest
from resumeforge.providers.ollama import (
    DEFAULT_MODEL,
    DEFAULT_OUTPUT_TOKENS,
    DEFAULT_PORT,
    DEFAULT_TIMEOUT,
)
from resumeforge.resume.documents import _parse_resume_model
from resumeforge.resume.engine import review_resume
from resumeforge.resume.models import (
    DraftText,
    ResumeError,
    ResumeModel,
    ResumeReview,
    WordingObjective,
    WordingResult,
)
from resumeforge.resume.wording import suggest_wording, wording_policy

BENCHMARK_VERSION = "synthetic-wording-v1"
CASES = (
    "supervised_bounds",
    "negated_prototype",
    "ongoing_parent",
    "cross_evidence",
    "unicode_qualitative",
    "untrusted_job",
)
DEVELOPMENT_CASES = ("dev_supervision", "dev_prototype", "dev_team")
HOLDOUT_CASES = ("eval_bound_tests", "eval_components", "eval_survey")
SUITE_CASES = {
    "baseline": CASES,
    "rewrite_development": DEVELOPMENT_CASES,
    "rewrite_holdout": HOLDOUT_CASES,
}
SUITE_VERSIONS = {
    "baseline": BENCHMARK_VERSION,
    "rewrite_development": "synthetic-wording-rewrite-development-v1",
    "rewrite_holdout": "synthetic-wording-rewrite-holdout-v1",
}


class WordingCase(ResumeModel):
    schema_version: Annotated[int, Field(ge=1, le=1)]
    case_id: str
    profile: UserProfile
    job_text: DraftText
    requirements: JobRequirements
    selection: PlanSelection
    review_focus: tuple[DraftText, ...]


class CaseReport(ResumeModel):
    case_id: str
    corpus_sha256: str | None
    status: Literal["validated_needs_review", "validation_failed", "case_input_failed", "not_run"]
    provider_calls: int = 0
    response_sha256: str | None = None
    review_focus: tuple[str, ...] = ()
    manual_review_status: Literal["not_performed"] = "not_performed"
    result: WordingResult | None = None
    error: str | None = None


@dataclass(frozen=True)
class PreparedCase:
    case: WordingCase
    job: JobDocument
    seed: ResumeReview
    corpus_sha256: str


@dataclass
class ObservedProvider:
    """Capture only assistant text in memory; no prompt logs, retries or provider substitution."""

    adapter: StructuredOutputProvider
    calls: int = 0
    response: str | None = field(default=None, repr=False)

    @property
    def name(self) -> str:
        return self.adapter.name

    @property
    def model(self) -> str:
        return self.adapter.model

    def complete(self, request: StructuredRequest) -> str:
        self.calls += 1
        self.response = self.adapter.complete(request)
        return self.response


def prepare_case(case_id: str, corpus_root: Path, *, suite: str = "baseline") -> PreparedCase:
    if case_id not in SUITE_CASES.get(suite, ()):
        raise ResumeError("Unknown fixed wording evaluation case.")
    text = read_utf8_file(corpus_root / f"{case_id}.json", label="Synthetic wording case")
    case = _parse_resume_model(text, WordingCase, label="Synthetic wording case")
    if case.case_id != case_id or not case.review_focus:
        raise ResumeError("Synthetic case identity or review focus is invalid.")
    job = JobDocument(case.job_text)
    seed = review_resume(
        case.profile,
        job,
        case.requirements,
        case.selection,
        requirements_reviewed=True,
        selection_reviewed=True,
    )
    if seed.status == "blocked_by_plan" or not seed.bullets:
        raise ResumeError("Synthetic evaluation cases require nonempty conflict-free plans.")
    return PreparedCase(case, job, seed, sha256(text.encode("utf-8")).hexdigest())


def source_replay(prepared: PreparedCase) -> FakeProvider:
    seed = prepared.seed
    return FakeProvider(
        json.dumps(
            {
                "schema_version": 1,
                "plan_sha256": seed.document.plan_sha256,
                "seed_document_sha256": seed.document_sha256,
                "bullets": [
                    {
                        "bullet_id": b.bullet_id,
                        "accomplishment_id": b.accomplishment_id,
                        "text": b.source_statement,
                    }
                    for b in seed.bullets
                ],
            },
            ensure_ascii=False,
        )
    )


def _response_bytes(response: str | None) -> bytes | None:
    if not isinstance(response, str):
        return None
    try:
        encoded = response.encode("utf-8")
    except UnicodeEncodeError:
        return None
    return encoded if len(encoded) <= MAX_INPUT_BYTES else None


def run_case(
    prepared: PreparedCase,
    provider: StructuredOutputProvider | None = None,
    *,
    responses_dir: Path | None = None,
    capture_dir: Path | None = None,
    objective: WordingObjective = "source_faithful",
) -> CaseReport:
    case = prepared.case
    observed: ObservedProvider | None = None
    result: WordingResult | None = None
    error: str | None = None
    try:
        adapter = (
            provider
            if provider is not None
            else (
                FakeProvider.from_file(responses_dir / f"{case.case_id}.response.json")
                if responses_dir is not None
                else source_replay(prepared)
            )
        )
        observed = ObservedProvider(adapter)
        result = suggest_wording(
            case.profile,
            prepared.job,
            case.requirements,
            case.selection,
            observed,
            requirements_reviewed=True,
            selection_reviewed=True,
            provider_data_confirmed=True,
            objective=objective,
        )
    except (InputError, ResumeError) as failure:
        error = str(failure)
    encoded = _response_bytes(observed.response if observed else None)
    if capture_dir is not None and encoded is not None:
        # Capture was separately requested; exclusive writes never replace earlier results.
        path = capture_dir / f"{case.case_id}.response.json"
        try:
            with path.open("xb") as output:
                path.chmod(0o600)
                output.write(encoded)
        except OSError:
            error = "Cannot exclusively capture the synthetic response; no file was overwritten."
            result = None
    return CaseReport(
        case_id=case.case_id,
        corpus_sha256=prepared.corpus_sha256,
        status="validated_needs_review" if result is not None else "validation_failed",
        provider_calls=observed.calls if observed else 0,
        response_sha256=sha256(encoded).hexdigest() if encoded is not None else None,
        review_focus=case.review_focus,
        result=result,
        error=error,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--suite", choices=SUITE_CASES, default="baseline")
    parser.add_argument(
        "--objective", choices=("source_faithful", "concise_rewrite"), default="source_faithful"
    )
    parser.add_argument(
        "--case",
        choices=tuple(c for cases in SUITE_CASES.values() for c in cases),
        action="append",
        help="Default: all cases in the selected suite.",
    )
    parser.add_argument("--responses-dir", type=Path, help="Replay independent responses offline.")
    parser.add_argument("--provider", choices=("fake", "ollama"), default="fake")
    parser.add_argument("--confirm-local-data", action="store_true")
    parser.add_argument(
        "--capture-responses-dir", type=Path, help="New private directory; never overwrite."
    )
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--ollama-port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT)
    parser.add_argument("--max-output-tokens", type=int, default=DEFAULT_OUTPUT_TOKENS)
    return parser


def main(argv: list[str] | None = None, *, corpus_root: Path) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    objective: WordingObjective = (
        "concise_rewrite" if args.objective == "concise_rewrite" else "source_faithful"
    )
    policy = wording_policy(objective)
    selected = list(dict.fromkeys(args.case or SUITE_CASES[args.suite]))
    if not set(selected) <= set(SUITE_CASES[args.suite]):
        parser.error("Selected cases must belong to the selected fixed suite.")
    selected_root = corpus_root if args.suite == "baseline" else corpus_root.parent / args.suite
    provider: StructuredOutputProvider | None = None
    if args.provider == "ollama":
        if not args.confirm_local_data or args.responses_dir is not None:
            parser.error(
                "Live synthetic wording requires --confirm-local-data and no --responses-dir."
            )
        try:
            provider = OllamaProvider(
                args.model, args.ollama_port, args.timeout, args.max_output_tokens
            )
        except ProviderError as error:
            parser.error(str(error))
        mode = "live_local"
    else:
        if (
            args.confirm_local_data
            or args.model != DEFAULT_MODEL
            or args.ollama_port != DEFAULT_PORT
            or args.timeout != DEFAULT_TIMEOUT
            or args.max_output_tokens != DEFAULT_OUTPUT_TOKENS
        ):
            parser.error("Local data/model options require --provider ollama.")
        mode = "response_replay" if args.responses_dir is not None else "source_seed_replay"
    prepared = []
    reports = []
    for case_id in selected:
        try:
            prepared.append(prepare_case(case_id, selected_root, suite=args.suite))
        except (InputError, ResumeError):
            reports.append(
                CaseReport(
                    case_id=case_id,
                    corpus_sha256=None,
                    status="case_input_failed",
                    error="Invalid synthetic corpus case.",
                )
            )
    if reports:
        failed = {report.case_id: report for report in reports}
        reports = [
            failed.get(case_id) or CaseReport(case_id=case_id, corpus_sha256=None, status="not_run")
            for case_id in selected
        ]
    else:
        if args.capture_responses_dir is not None:
            try:
                args.capture_responses_dir.mkdir(mode=0o700)
            except OSError:
                parser.error("Response capture requires a new directory under an existing parent.")
        reports = [
            run_case(
                case,
                provider,
                responses_dir=args.responses_dir,
                capture_dir=args.capture_responses_dir,
                objective=objective,
            )
            for case in prepared
        ]
    print(
        json.dumps(
            {
                "benchmark_version": SUITE_VERSIONS[args.suite],
                "suite": args.suite,
                "objective": objective,
                "mode": mode,
                "wording_version": policy.wording_version,
                "prompt_version": policy.prompt_version,
                "total_cases": len(reports),
                "validated_cases": sum(
                    report.status == "validated_needs_review" for report in reports
                ),
                "provider_calls": sum(report.provider_calls for report in reports),
                "inspected_bullets": sum(
                    len(report.result.review.bullets) for report in reports if report.result
                ),
                "edited_bullets": sum(
                    bullet.wording_status == "edited_requires_review"
                    for report in reports
                    if report.result
                    for bullet in report.result.review.bullets
                ),
                "literal_findings": sum(
                    len(bullet.findings)
                    for report in reports
                    if report.result
                    for bullet in report.result.review.bullets
                ),
                "source_characters": sum(
                    len(b.source_statement)
                    for report in reports
                    if report.result
                    for b in report.result.review.bullets
                ),
                "draft_characters": sum(
                    len(b.text)
                    for report in reports
                    if report.result
                    for s in report.result.review.document.sections
                    for e in s.entries
                    for b in e.bullets
                ),
                "requested_runtime": {
                    "model": args.model,
                    "port": args.ollama_port,
                    "timeout_seconds": args.timeout,
                    "max_output_tokens": args.max_output_tokens,
                }
                if mode == "live_local"
                else None,
                "manual_review_status": "not_performed",
                "rendering_authorized": False,
                "cases": [report.model_dump(mode="json") for report in reports],
                "limitations": [
                    "Source-seed replay validates the harness, not model wording quality.",
                    "Schema validity, absent findings and concise text are not support verdicts.",
                    "All cases, including failures, remain in totals; manual review is required.",
                    "Replay metadata does not identify the original authoring model.",
                ],
            },
            ensure_ascii=False,
            allow_nan=False,
            indent=2,
        )
    )
    print("Synthetic wording evaluation; no automatic quality score or approval.", file=sys.stderr)
    return 0 if all(report.status == "validated_needs_review" for report in reports) else 1
