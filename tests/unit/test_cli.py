"""Fast CLI contract tests; no network, profile data, or credentials are needed."""

from importlib.metadata import version

import pytest
from typer.testing import CliRunner

from resumeforge import __version__
from resumeforge.cli import app

runner = CliRunner()


@pytest.mark.parametrize("option", ["--help", "-h"])
def test_help_describes_only_implemented_commands(option: str) -> None:
    result = runner.invoke(app, [option])

    assert result.exit_code == 0
    assert "ResumeForge" in result.output
    assert "validate-profile" in result.output
    assert "--version" in result.output
    assert "generate" not in result.output


@pytest.mark.parametrize("option", ["--version", "-V"])
def test_version_matches_installed_package(option: str) -> None:
    result = runner.invoke(app, [option])

    assert result.exit_code == 0
    assert result.output.strip() == f"ResumeForge {version('resumeforge')}"
    assert __version__ == version("resumeforge")


def test_no_arguments_displays_help_successfully() -> None:
    result = runner.invoke(app, [])

    assert result.exit_code == 0
    assert "Usage:" in result.output
    assert "ResumeForge" in result.output


@pytest.mark.parametrize("arguments", [["generate"], ["--unknown-option"]])
def test_unsupported_commands_and_options_fail_cleanly(arguments: list[str]) -> None:
    result = runner.invoke(app, arguments)

    assert result.exit_code == 2
    assert "Error" in result.output
    assert "Traceback" not in result.output
