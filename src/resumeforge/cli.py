"""Command-line boundary; future domain logic belongs outside this module."""

from enum import StrEnum
from pathlib import Path
from typing import Annotated

import typer

from resumeforge import __version__
from resumeforge.inputs import InputError
from resumeforge.jobs import JobAnalysisError, analyze_job, load_job
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


class ProviderChoice(StrEnum):
    FAKE = "fake"
    OLLAMA = "ollama"


app = typer.Typer(
    help="ResumeForge: evidence-first resumes. Profile validation and local/offline job analysis.",
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
