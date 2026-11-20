"""Command-line boundary; future domain logic belongs outside this module."""

import json
from dataclasses import asdict
from enum import StrEnum
from pathlib import Path
from typing import Annotated

import typer

from resumeforge import __version__
from resumeforge.inputs import InputError
from resumeforge.jobs import JobAnalysisError, analyze_job, load_job
from resumeforge.matching import MatchingError, match_evidence
from resumeforge.planning import PlanningError, load_selection, plan_resume
from resumeforge.profile import ProfileError, find_profile_gaps, load_profile
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
from resumeforge.resume import (
    MetadataDecisionResult,
    MetadataReview,
    ResumeError,
    ResumeReview,
    ReviewDecisionResult,
    ReviewWorksheet,
    apply_metadata_decisions,
    apply_review_decisions,
    assemble_resume,
    build_review_worksheet,
    load_metadata_decisions,
    load_metadata_selection,
    load_resume_document,
    load_review_decisions,
    load_section_content_selection,
    review_metadata,
    review_resume,
    review_section_content,
    suggest_wording,
)


class ProviderChoice(StrEnum):
    FAKE = "fake"
    OLLAMA = "ollama"


class WordingObjectiveChoice(StrEnum):
    SOURCE_FAITHFUL = "source_faithful"
    CONCISE_REWRITE = "concise_rewrite"


app = typer.Typer(
    help="ResumeForge: evidence-first resumes. Profile validation, job analysis "
    "and evidence retrieval/planning/draft review with opt-in wording assistance.",
    add_completion=False,
    invoke_without_command=True,
    pretty_exceptions_enable=False,
    context_settings={"help_option_names": ["-h", "--help"]},
)


@app.callback()
def main(
    context: typer.Context,
    version: Annotated[
        bool,
        typer.Option("--version", "-V", help="Show the installed version and exit.", is_eager=True),
    ] = False,
) -> None:
    """Display application information without reading user data or using external services."""
    if version:
        typer.echo(f"ResumeForge {__version__}")
        raise typer.Exit()
    if context.invoked_subcommand is None:
        typer.echo(context.get_help())


@app.command("validate-profile")
def validate_profile(
    profile: Annotated[
        Path,
        typer.Option("--profile", "-p", help="Path to a UTF-8 Markdown profile."),
    ] = Path("data/profile/user_information.md"),
) -> None:
    """Validate profile structure, evidence references and preferences; report gaps."""
    try:
        document = load_profile(profile)
    except ProfileError as error:
        typer.echo(f"Profile validation failed:\n{error}", err=True)
        raise typer.Exit(code=1) from None
    verified_count = sum(item.verified for item in document.profile.accomplishments)
    typer.echo(
        f"Profile structure valid: {len(document.profile.entries())} entries, "
        f"{len(document.profile.accomplishments)} accomplishments ({verified_count} verified)."
    )
    for warning in find_profile_gaps(document.profile):
        typer.echo(f"Warning: {warning}")
    typer.echo("Structure checks do not establish factual truth; review your source evidence.")


@app.command("analyze-job")
def analyze_job_command(
    job: Annotated[Path, typer.Option("--job", help="Local UTF-8 job description.")],
    mock_response: Annotated[
        Path | None,
        typer.Option("--mock-response", help="JSON fixture for fake/offline replay, not live AI."),
    ] = None,
    provider: Annotated[
        ProviderChoice, typer.Option("--provider", help="Explicit inference mode.")
    ] = ProviderChoice.FAKE,
    model: Annotated[
        str, typer.Option("--model", help="Downloaded local Ollama model.")
    ] = DEFAULT_MODEL,
    ollama_port: Annotated[int, typer.Option("--ollama-port", min=1, max=65535)] = DEFAULT_PORT,
    timeout: Annotated[float, typer.Option("--timeout", min=1, max=600)] = DEFAULT_TIMEOUT,
    max_output_tokens: Annotated[
        int, typer.Option("--max-output-tokens", min=128, max=8192)
    ] = DEFAULT_OUTPUT_TOKENS,
) -> None:
    """Analyze with loopback-only Ollama or explicit fake replay; emit JSON to stdout."""
    if provider == ProviderChoice.FAKE and mock_response is None:
        raise typer.BadParameter(
            "Fake mode requires --mock-response; select --provider ollama for local AI."
        )
    if provider == ProviderChoice.OLLAMA and mock_response is not None:
        raise typer.BadParameter("--mock-response cannot be combined with --provider ollama.")
    if provider == ProviderChoice.FAKE and (
        model != DEFAULT_MODEL
        or ollama_port != DEFAULT_PORT
        or timeout != DEFAULT_TIMEOUT
        or max_output_tokens != DEFAULT_OUTPUT_TOKENS
    ):
        raise typer.BadParameter("Ollama options require --provider ollama.")
    try:
        document = load_job(job)
        adapter: StructuredOutputProvider
        if provider == ProviderChoice.FAKE:
            assert mock_response is not None
            adapter = FakeProvider.from_file(mock_response)
        else:
            adapter = OllamaProvider(model, ollama_port, timeout, max_output_tokens)
            typer.echo(
                "Analyzing selected job with loopback-only Ollama; profile is not loaded.", err=True
            )
        analysis = analyze_job(document, adapter)
    except (InputError, JobAnalysisError, ProviderError) as error:
        typer.echo(f"Job analysis failed:\n{error}", err=True)
        raise typer.Exit(code=1) from None
    if provider == ProviderChoice.FAKE:
        typer.echo("Offline fake response replay; no live AI extraction was performed.", err=True)
    typer.echo(analysis.model_dump_json(indent=2))


@app.command("match-evidence")
def match_evidence_command(
    profile: Annotated[Path, typer.Option("--profile", help="Explicit local Markdown profile.")],
    job: Annotated[
        Path, typer.Option("--job", help="Exact local job source used for requirements.")
    ],
    requirements: Annotated[
        Path,
        typer.Option(
            "--requirements", help="Manually reviewed JobRequirements JSON; no inference."
        ),
    ],
    confirm_review: Annotated[
        bool,
        typer.Option(
            "--confirm-review", help="Acknowledge review of requirements against the full job."
        ),
    ] = False,
) -> None:
    """Find offline lexical candidates with source signals, not qualification verdicts or a plan."""
    if not confirm_review:
        raise typer.BadParameter(
            "Review requirements against the full job, then pass --confirm-review."
        )
    try:
        document = load_job(job)
        analysis = analyze_job(document, FakeProvider.from_file(requirements))
        candidate = load_profile(profile)
        report = match_evidence(
            candidate.profile, document, analysis.requirements, requirements_reviewed=True
        )
    except (ProfileError, InputError, JobAnalysisError, MatchingError) as error:
        typer.echo(f"Evidence matching failed:\n{error}", err=True)
        raise typer.Exit(code=1) from None
    typer.echo(
        "Offline lexical candidates only; no inference or qualification approval performed.",
        err=True,
    )
    typer.echo(json.dumps(asdict(report), ensure_ascii=False, indent=2))


@app.command("plan-resume")
def plan_resume_command(
    profile: Annotated[Path, typer.Option("--profile", help="Explicit local Markdown profile.")],
    job: Annotated[
        Path, typer.Option("--job", help="Exact local source for reviewed requirements.")
    ],
    requirements: Annotated[
        Path, typer.Option("--requirements", help="Reviewed JobRequirements JSON; no inference.")
    ],
    selection: Annotated[
        Path, typer.Option("--selection", help="Reviewed version-1 entry/evidence selection JSON.")
    ],
    confirm_review: Annotated[
        bool,
        typer.Option("--confirm-review", help="Acknowledge review of requirements and selection."),
    ] = False,
) -> None:
    """Assemble an offline count-constrained draft; no resume wording or page layout."""
    if not confirm_review:
        raise typer.BadParameter(
            "Review the full job requirements and selection, then pass --confirm-review."
        )
    try:
        document = load_job(job)
        analysis = analyze_job(document, FakeProvider.from_file(requirements))
        choices = load_selection(selection)
        candidate = load_profile(profile)
        plan = plan_resume(
            candidate.profile,
            document,
            analysis.requirements,
            choices,
            requirements_reviewed=True,
            selection_reviewed=True,
        )
    except (ProfileError, InputError, JobAnalysisError, PlanningError) as error:
        typer.echo(f"Resume planning failed:\n{error}", err=True)
        raise typer.Exit(code=1) from None
    typer.echo(
        "Offline draft plan; no inference, generated wording or layout validation.", err=True
    )
    typer.echo(json.dumps(asdict(plan), ensure_ascii=False, indent=2))
    if plan.constraint_status == "conflicts":
        typer.echo("Plan has constraint conflicts; review findings before proceeding.", err=True)
        raise typer.Exit(code=3)


@app.command("suggest-wording")
def suggest_wording_command(
    profile: Annotated[Path, typer.Option("--profile", help="Explicit local Markdown profile.")],
    job: Annotated[Path, typer.Option("--job", help="Exact local job source.")],
    requirements: Annotated[
        Path, typer.Option("--requirements", help="Reviewed JobRequirements JSON; no extraction.")
    ],
    selection: Annotated[
        Path, typer.Option("--selection", help="Reviewed version-1 entry/evidence selection JSON.")
    ],
    mock_response: Annotated[
        Path | None,
        typer.Option("--mock-response", help="Snapshot-bound wording JSON; fake replay only."),
    ] = None,
    provider: Annotated[
        ProviderChoice,
        typer.Option("--provider", help="Fake replay by default; local inference is opt-in."),
    ] = ProviderChoice.FAKE,
    objective: Annotated[
        WordingObjectiveChoice,
        typer.Option("--objective", help="Wording objective; concise_rewrite is experimental."),
    ] = WordingObjectiveChoice.SOURCE_FAITHFUL,
    confirm_review: Annotated[
        bool,
        typer.Option("--confirm-review", help="Acknowledge review of requirements and selection."),
    ] = False,
    confirm_local_data: Annotated[
        bool,
        typer.Option(
            "--confirm-local-data",
            help="Allow selected statements, caveats and reviewed job items to local Ollama; "
            "no contact/notes.",
        ),
    ] = False,
    model: Annotated[
        str, typer.Option("--model", help="Downloaded local Ollama model.")
    ] = DEFAULT_MODEL,
    ollama_port: Annotated[int, typer.Option("--ollama-port", min=1, max=65535)] = DEFAULT_PORT,
    timeout: Annotated[float, typer.Option("--timeout", min=1, max=600)] = DEFAULT_TIMEOUT,
    max_output_tokens: Annotated[
        int, typer.Option("--max-output-tokens", min=128, max=8192)
    ] = DEFAULT_OUTPUT_TOKENS,
) -> None:
    """Propose pending source-bound wording, never select evidence or approve a resume."""
    if not confirm_review:
        raise typer.BadParameter("Review requirements and selection, then pass --confirm-review.")
    if provider == ProviderChoice.FAKE and mock_response is None:
        raise typer.BadParameter(
            "Fake wording mode requires --mock-response; it does not generate text."
        )
    if provider == ProviderChoice.OLLAMA and (mock_response is not None or not confirm_local_data):
        raise typer.BadParameter(
            "Local wording requires --confirm-local-data and no --mock-response."
        )
    if provider == ProviderChoice.FAKE and (
        confirm_local_data
        or model != DEFAULT_MODEL
        or ollama_port != DEFAULT_PORT
        or timeout != DEFAULT_TIMEOUT
        or max_output_tokens != DEFAULT_OUTPUT_TOKENS
    ):
        raise typer.BadParameter("Local data/model options require --provider ollama.")
    try:
        document = load_job(job)
        analysis = analyze_job(document, FakeProvider.from_file(requirements))
        choices = load_selection(selection)
        adapter: StructuredOutputProvider
        if provider == ProviderChoice.FAKE:
            assert mock_response is not None
            adapter = FakeProvider.from_file(mock_response)
        else:
            adapter = OllamaProvider(model, ollama_port, timeout, max_output_tokens)
        candidate = load_profile(profile)
        result = suggest_wording(
            candidate.profile,
            document,
            analysis.requirements,
            choices,
            adapter,
            requirements_reviewed=True,
            selection_reviewed=True,
            provider_data_confirmed=provider == ProviderChoice.FAKE or confirm_local_data,
            objective="concise_rewrite"
            if objective == WordingObjectiveChoice.CONCISE_REWRITE
            else "source_faithful",
        )
    except (
        ProfileError,
        InputError,
        JobAnalysisError,
        PlanningError,
        ResumeError,
        ProviderError,
    ) as error:
        typer.echo(f"Wording assistance failed:\n{error}", err=True)
        raise typer.Exit(code=1) from None
    if result.attempt is None:
        notice = "No wording provider called: inspect the conflicted or empty plan."
    elif provider == ProviderChoice.FAKE:
        notice = "Offline wording response replay; no model inference or approval performed."
    else:
        notice = (
            "Local Ollama wording proposals; selected-source data used, "
            "no semantic proof or approval."
        )
    typer.echo(notice, err=True)
    if objective == WordingObjectiveChoice.CONCISE_REWRITE:
        typer.echo(
            "Experimental objective: shorter wording may distort claims; human review is required.",
            err=True,
        )
    typer.echo(result.model_dump_json(indent=2))
    if result.status == "blocked_by_plan":
        raise typer.Exit(code=3)


@app.command("review-resume")
def review_resume_command(
    profile: Annotated[Path, typer.Option("--profile", help="Explicit local Markdown profile.")],
    job: Annotated[Path, typer.Option("--job", help="Exact local job source.")],
    requirements: Annotated[
        Path, typer.Option("--requirements", help="Reviewed JobRequirements JSON; no inference.")
    ],
    selection: Annotated[
        Path, typer.Option("--selection", help="Reviewed version-1 entry/evidence selection JSON.")
    ],
    draft: Annotated[
        Path | None,
        typer.Option(
            "--draft", help="Edited ResumeDocument JSON; omit to seed verbatim pending wording."
        ),
    ] = None,
    worksheet: Annotated[
        bool,
        typer.Option(
            "--worksheet",
            help="Emit fresh context and an unfilled decision template; requires --draft.",
        ),
    ] = False,
    decisions: Annotated[
        Path | None,
        typer.Option(
            "--decisions", help="Version-3 human wording/fragment decisions for this draft."
        ),
    ] = None,
    confirm_decisions: Annotated[
        bool,
        typer.Option(
            "--confirm-decisions", help="Attest that you reviewed the submitted bullet decisions."
        ),
    ] = False,
    confirm_review: Annotated[
        bool,
        typer.Option(
            "--confirm-review",
            help="Acknowledge requirements/selection review, not claim approval.",
        ),
    ] = False,
) -> None:
    """Inspect pending review drafts or apply snapshot-bound user decisions."""
    if not confirm_review:
        raise typer.BadParameter(
            "Review requirements and selection, then pass --confirm-review; "
            "this does not approve wording."
        )
    if decisions is not None and (draft is None or not confirm_decisions):
        raise typer.BadParameter("--decisions requires --draft and explicit --confirm-decisions.")
    if confirm_decisions and decisions is None:
        raise typer.BadParameter("--confirm-decisions requires --decisions.")
    if worksheet and (draft is None or decisions is not None or confirm_decisions):
        raise typer.BadParameter(
            "--worksheet requires --draft and cannot be combined with decision options."
        )
    try:
        document = load_job(job)
        analysis = analyze_job(document, FakeProvider.from_file(requirements))
        choices = load_selection(selection)
        proposed = load_resume_document(draft) if draft is not None else None
        choices_review = load_review_decisions(decisions) if decisions is not None else None
        candidate = load_profile(profile)
        result: ResumeReview | ReviewDecisionResult | ReviewWorksheet
        if worksheet:
            assert proposed is not None
            result = build_review_worksheet(
                candidate.profile,
                document,
                analysis.requirements,
                choices,
                proposed,
                requirements_reviewed=True,
                selection_reviewed=True,
            )
            blocked = result.status == "blocked_by_plan"
        elif choices_review is not None:
            assert proposed is not None
            result = apply_review_decisions(
                candidate.profile,
                document,
                analysis.requirements,
                choices,
                proposed,
                choices_review,
                requirements_reviewed=True,
                selection_reviewed=True,
                decisions_confirmed=confirm_decisions,
            )
            blocked = result.status != "bullet_wording_approved_by_user"
        else:
            result = review_resume(
                candidate.profile,
                document,
                analysis.requirements,
                choices,
                proposed,
                requirements_reviewed=True,
                selection_reviewed=True,
            )
            blocked = result.status == "blocked_by_plan"
    except (ProfileError, InputError, JobAnalysisError, PlanningError, ResumeError) as error:
        typer.echo(f"Resume draft review failed:\n{error}", err=True)
        raise typer.Exit(code=1) from None
    if worksheet:
        notice = (
            "Offline pending review worksheet; no choices or acknowledgements made, no inference."
        )
    elif decisions is not None:
        notice = (
            "Offline user decision snapshot; no inference, semantic proof "
            "or rendering authorization."
        )
    else:
        notice = "Offline draft inspection; no inference, semantic proof or claim approval."
    typer.echo(notice, err=True)
    typer.echo(result.model_dump_json(indent=2))
    if blocked:
        typer.echo(
            "Review remains pending, rejected or plan-blocked; inspect the result.", err=True
        )
        raise typer.Exit(code=3)


@app.command("review-metadata")
def review_metadata_command(
    profile: Annotated[Path, typer.Option("--profile", help="Explicit local Markdown profile.")],
    job: Annotated[Path, typer.Option("--job", help="Exact local job source.")],
    requirements: Annotated[
        Path, typer.Option("--requirements", help="Reviewed JobRequirements JSON; no inference.")
    ],
    selection: Annotated[
        Path, typer.Option("--selection", help="Reviewed version-1 content selection JSON.")
    ],
    draft: Annotated[
        Path, typer.Option("--draft", help="Explicit current wording ResumeDocument.")
    ],
    metadata_selection: Annotated[
        Path,
        typer.Option(
            "--metadata-selection", help="Explicit metadata fields to expose in private output."
        ),
    ],
    decisions: Annotated[
        Path | None,
        typer.Option(
            "--decisions", help="Explicit version-1 metadata field decisions, not bullet decisions."
        ),
    ] = None,
    confirm_decisions: Annotated[
        bool,
        typer.Option(
            "--confirm-decisions", help="Attest that you reviewed these exact metadata decisions."
        ),
    ] = False,
    confirm_review: Annotated[
        bool,
        typer.Option(
            "--confirm-review",
            help="Acknowledge requirements, content and metadata selections, not approval.",
        ),
    ] = False,
) -> None:
    """Inspect selected metadata or apply narrow snapshot-bound user attestations."""
    if not confirm_review:
        raise typer.BadParameter(
            "Review requirements, content and metadata selections, then pass --confirm-review."
        )
    if decisions is not None and not confirm_decisions:
        raise typer.BadParameter("--decisions requires separate --confirm-decisions.")
    if confirm_decisions and decisions is None:
        raise typer.BadParameter("--confirm-decisions requires --decisions.")
    try:
        document = load_job(job)
        analysis = analyze_job(document, FakeProvider.from_file(requirements))
        choices = load_selection(selection)
        proposed = load_resume_document(draft)
        metadata_choices = load_metadata_selection(metadata_selection)
        field_decisions = load_metadata_decisions(decisions) if decisions is not None else None
        candidate = load_profile(profile)
        result: MetadataReview | MetadataDecisionResult
        if field_decisions is not None:
            result = apply_metadata_decisions(
                candidate.profile,
                document,
                analysis.requirements,
                choices,
                proposed,
                metadata_choices,
                field_decisions,
                requirements_reviewed=True,
                selection_reviewed=True,
                metadata_selection_reviewed=True,
                decisions_confirmed=confirm_decisions,
            )
            blocked = result.status != "metadata_fields_approved_by_user"
        else:
            result = review_metadata(
                candidate.profile,
                document,
                analysis.requirements,
                choices,
                proposed,
                metadata_choices,
                requirements_reviewed=True,
                selection_reviewed=True,
                metadata_selection_reviewed=True,
            )
            blocked = result.status == "blocked_by_plan"
    except (ProfileError, InputError, JobAnalysisError, PlanningError, ResumeError) as error:
        typer.echo(f"Metadata review failed:\n{error}", err=True)
        raise typer.Exit(code=1) from None
    notice = (
        "Offline user metadata attestations; no inference, semantic proof "
        "or rendering authorization."
        if decisions is not None
        else "Offline selected metadata inspection; no inference, approval "
        "or rendering authorization."
    )
    typer.echo(notice, err=True)
    typer.echo(result.model_dump_json(indent=2))
    if blocked:
        raise typer.Exit(code=3)


@app.command("assemble-resume")
def assemble_resume_command(
    profile: Annotated[Path, typer.Option("--profile", help="Explicit local Markdown profile.")],
    job: Annotated[Path, typer.Option("--job", help="Exact local job source.")],
    requirements: Annotated[
        Path, typer.Option("--requirements", help="Reviewed requirements JSON.")
    ],
    selection: Annotated[
        Path, typer.Option("--selection", help="Reviewed content selection JSON.")
    ],
    draft: Annotated[
        Path, typer.Option("--draft", help="Explicit current wording ResumeDocument.")
    ],
    metadata_selection: Annotated[
        Path, typer.Option("--metadata-selection", help="Explicit fields to expose; no defaults.")
    ],
    bullet_decisions: Annotated[
        Path | None,
        typer.Option("--bullet-decisions", help="Current v3 bullet decisions, not a receipt."),
    ] = None,
    metadata_decisions: Annotated[
        Path | None,
        typer.Option("--metadata-decisions", help="Current v1 metadata field decisions."),
    ] = None,
    confirm_review: Annotated[
        bool,
        typer.Option(
            "--confirm-review", help="Acknowledge reviewed requirements and both selections."
        ),
    ] = False,
    confirm_bullet_decisions: Annotated[
        bool,
        typer.Option("--confirm-bullet-decisions", help="Confirm these exact bullet decisions."),
    ] = False,
    confirm_metadata_decisions: Annotated[
        bool,
        typer.Option(
            "--confirm-metadata-decisions", help="Confirm these exact metadata decisions."
        ),
    ] = False,
) -> None:
    """Assemble selected components and unresolved issues; no full-resume or rendering approval."""
    if not confirm_review:
        raise typer.BadParameter(
            "Review requirements and both selections, then pass --confirm-review."
        )
    if (bullet_decisions is not None) != confirm_bullet_decisions:
        raise typer.BadParameter("Pair --bullet-decisions with --confirm-bullet-decisions.")
    if (metadata_decisions is not None) != confirm_metadata_decisions:
        raise typer.BadParameter("Pair --metadata-decisions with --confirm-metadata-decisions.")
    try:
        document = load_job(job)
        analysis = analyze_job(document, FakeProvider.from_file(requirements))
        choices = load_selection(selection)
        proposed = load_resume_document(draft)
        metadata_choices = load_metadata_selection(metadata_selection)
        bullet_choices = load_review_decisions(bullet_decisions) if bullet_decisions else None
        field_choices = load_metadata_decisions(metadata_decisions) if metadata_decisions else None
        candidate = load_profile(profile)
        result = assemble_resume(
            candidate.profile,
            document,
            analysis.requirements,
            choices,
            proposed,
            metadata_choices,
            bullet_decisions=bullet_choices,
            metadata_decisions=field_choices,
            requirements_reviewed=True,
            selection_reviewed=True,
            metadata_selection_reviewed=True,
            bullet_decisions_confirmed=confirm_bullet_decisions,
            metadata_decisions_confirmed=confirm_metadata_decisions,
        )
    except (ProfileError, InputError, JobAnalysisError, PlanningError, ResumeError) as error:
        typer.echo(f"Structured assembly failed:\n{error}", err=True)
        raise typer.Exit(code=1) from None
    typer.echo(
        "Offline component assembly; no inference, full-resume approval or rendering authority.",
        err=True,
    )
    typer.echo(result.model_dump_json(indent=2))
    if result.status != "components_reviewed":
        raise typer.Exit(code=3)


@app.command("review-content")
def review_content_command(
    profile: Annotated[Path, typer.Option("--profile", help="Explicit local Markdown profile.")],
    job: Annotated[Path, typer.Option("--job", help="Exact local job source.")],
    requirements: Annotated[
        Path, typer.Option("--requirements", help="Reviewed requirements JSON.")
    ],
    selection: Annotated[Path, typer.Option("--selection", help="Reviewed plan selection JSON.")],
    draft: Annotated[
        Path, typer.Option("--draft", help="Explicit current wording ResumeDocument.")
    ],
    content_selection: Annotated[
        Path,
        typer.Option(
            "--content-selection",
            help="Explicit skill/coursework source indices, labels and context refs.",
        ),
    ],
    confirm_review: Annotated[
        bool,
        typer.Option(
            "--confirm-review",
            help="Acknowledge requirements, plan and content selection review; not approval.",
        ),
    ] = False,
) -> None:
    """Inspect pending selected skills/coursework and context; no verification or rendering."""
    if not confirm_review:
        raise typer.BadParameter(
            "Review requirements and both selections, then pass --confirm-review."
        )
    try:
        document = load_job(job)
        analysis = analyze_job(document, FakeProvider.from_file(requirements))
        choices = load_selection(selection)
        proposed = load_resume_document(draft)
        content_choices = load_section_content_selection(content_selection)
        candidate = load_profile(profile)
        result = review_section_content(
            candidate.profile,
            document,
            analysis.requirements,
            choices,
            proposed,
            content_choices,
            requirements_reviewed=True,
            selection_reviewed=True,
            content_selection_reviewed=True,
        )
    except (ProfileError, InputError, JobAnalysisError, PlanningError, ResumeError) as error:
        typer.echo(f"Section content review failed:\n{error}", err=True)
        raise typer.Exit(code=1) from None
    typer.echo(
        "Offline pending skill/coursework review; no inference, verification "
        "or rendering authority.",
        err=True,
    )
    typer.echo(result.model_dump_json(indent=2))
    if result.status == "blocked_by_plan":
        raise typer.Exit(code=3)
