"""The CLI and profile engine integrate without exposing private contents or writing output."""

import subprocess
import sys
from pathlib import Path

import pytest
from typer.testing import CliRunner

from resumeforge.cli import app

pytestmark = pytest.mark.integration
runner = CliRunner()


def test_validate_sample_with_installed_module(sample_path: Path, tmp_path: Path) -> None:
    result = subprocess.run(
        [sys.executable, "-m", "resumeforge", "validate-profile", "--profile", str(sample_path)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "8 entries, 3 accomplishments (2 verified)" in result.stdout
    assert "acc_queue_pending: unverified" in result.stdout
    assert "do not establish factual truth" in result.stdout
    assert "alex@example.com" not in result.stdout
    assert result.stderr == ""
    assert list(tmp_path.iterdir()) == []


def test_default_profile_path_is_relative_and_read_only(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    path = Path("data/profile/user_information.md")
    path.parent.mkdir(parents=True)
    text = "---\nschema_version: 1\nperson: {name: Example}\n---\nRough notes\n"
    path.write_text(text, encoding="utf-8")
    before = sorted(str(item) for item in Path.cwd().rglob("*"))

    result = runner.invoke(app, ["validate-profile"])

    assert result.exit_code == 0
    assert "Warning:" in result.stdout
    assert path.read_text(encoding="utf-8") == text
    assert sorted(str(item) for item in Path.cwd().rglob("*")) == before


@pytest.mark.parametrize("content", ["not front matter", "---\nperson: [private-value\n---\n"])
def test_invalid_profile_fails_without_traceback_or_input_values(
    tmp_path: Path, content: str
) -> None:
    path = tmp_path / "invalid.md"
    path.write_text(content, encoding="utf-8")

    result = runner.invoke(app, ["validate-profile", "-p", str(path)])

    assert result.exit_code == 1
    assert "Profile validation failed" in result.stderr
    assert "private-value" not in result.output
    assert "Traceback" not in result.output


def test_missing_profile_has_actionable_error(tmp_path: Path) -> None:
    result = runner.invoke(app, ["validate-profile", "--profile", str(tmp_path / "missing.md")])

    assert result.exit_code == 1
    assert "existing regular file" in result.stderr


def test_validate_profile_help_is_available() -> None:
    result = runner.invoke(app, ["validate-profile", "--help"])

    assert result.exit_code == 0
    assert "--profile" in result.stdout
