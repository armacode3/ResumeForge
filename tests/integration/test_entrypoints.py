"""Exercise installed entry points from outside the source directory."""

import os
import subprocess
import sys
from pathlib import Path

import pytest
from rich.text import Text

from resumeforge import __version__

pytestmark = pytest.mark.integration


@pytest.mark.parametrize("entrypoint", ["console", "module"])
def test_installed_entrypoints_are_read_only(entrypoint: str, tmp_path: Path) -> None:
    executable = Path(sys.executable).with_name(
        "resumeforge.exe" if os.name == "nt" else "resumeforge"
    )
    command = (
        [str(executable)] if entrypoint == "console" else [sys.executable, "-m", "resumeforge"]
    )

    result = subprocess.run(
        [*command, "--version"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == f"ResumeForge {__version__}"
    assert result.stderr == ""
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("color_mode", ["plain", "github", "forced"])
@pytest.mark.parametrize(
    ("arguments", "expected_options"),
    [
        (["--help"], ["--version"]),
        (["-h"], ["--version"]),
        (["validate-profile", "--help"], ["--profile"]),
        (["analyze-job", "--help"], ["--mock-response", "--provider"]),
        (["match-evidence", "--help"], ["--profile", "--requirements", "--confirm-review"]),
        (["plan-resume", "--help"], ["--selection", "--confirm-review"]),
        (["review-resume", "--help"], ["--draft", "--confirm-review", "--worksheet"]),
        (
            ["review-metadata", "--help"],
            [
                "--draft",
                "--metadata-selection",
                "--confirm-review",
                "--decisions",
                "--confirm-decisions",
            ],
        ),
        (["suggest-wording", "--help"], ["--provider", "--confirm-local-data", "--objective"]),
        (
            ["assemble-resume", "--help"],
            [
                "--draft",
                "--metadata-selection",
                "--bullet-decisions",
                "--metadata-decisions",
                "--confirm-bullet-decisions",
                "--confirm-metadata-decisions",
            ],
        ),
    ],
)
def test_help_options_survive_terminal_styling(
    color_mode: str, arguments: list[str], expected_options: list[str], tmp_path: Path
) -> None:
    # Typer reads terminal settings at import time, so exercise fresh installed processes.
    environment = os.environ.copy()
    for name in (
        "GITHUB_ACTIONS",
        "FORCE_COLOR",
        "PY_COLORS",
        "NO_COLOR",
        "_TYPER_FORCE_DISABLE_TERMINAL",
    ):
        environment.pop(name, None)
    environment["TERM"] = "xterm-256color"
    environment["COLUMNS"] = "100"
    environment["TERMINAL_WIDTH"] = "100"
    if color_mode == "github":
        environment["GITHUB_ACTIONS"] = "true"
    elif color_mode == "forced":
        environment["FORCE_COLOR"] = "1"

    result = subprocess.run(
        [sys.executable, "-m", "resumeforge", *arguments],
        cwd=tmp_path,
        env=environment,
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert result.stderr == ""
    assert ("\x1b[" in result.stdout) == (color_mode != "plain")
    help_text = Text.from_ansi(result.stdout).plain
    for option in expected_options:
        assert option in help_text
    assert list(tmp_path.iterdir()) == []
