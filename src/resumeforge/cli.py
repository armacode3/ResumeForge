"""Command-line boundary; future domain logic belongs outside this module."""

from pathlib import Path
from typing import Annotated

import typer

from resumeforge import __version__
from resumeforge.inputs import InputError
from resumeforge.jobs import JobAnalysisError, analyze_job, load_job
from resumeforge.profile import ProfileError, find_profile_gaps, load_profile
from resumeforge.providers import FakeProvider

app = typer.Typer(
    help="ResumeForge: evidence-first resumes. Profile validation and offline job analysis.",
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
    """Validate profile structure and evidence references; report missing details."""
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
        Path,
        typer.Option("--mock-response", help="Required JSON fixture; offline replay, not live AI."),
    ],
) -> None:
    """Validate a fake structured analysis against a local job; emit JSON to stdout."""
    try:
        document = load_job(job)
        provider = FakeProvider.from_file(mock_response)
        analysis = analyze_job(document, provider)
    except (InputError, JobAnalysisError) as error:
        typer.echo(f"Job analysis failed:\n{error}", err=True)
        raise typer.Exit(code=1) from None
    typer.echo("Offline fake response replay; no live AI extraction was performed.", err=True)
    typer.echo(analysis.model_dump_json(indent=2))
