"""The CLI and profile engine integrate without exposing private contents or writing output."""

import subprocess
import sys
from pathlib import Path

import pytest
from rich.text import Text
from typer.testing import CliRunner

from resumeforge.cli import app
from resumeforge.profile import parse_profile

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
    help_text = Text.from_ansi(result.stdout).plain

    assert result.exit_code == 0
    assert "--profile" in help_text


def test_status_and_preferences_validate_read_only_without_provider_access(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def forbid_network(*args: object, **kwargs: object) -> None:
        raise AssertionError("Profile contracts must not trigger inference")

    monkeypatch.setattr("socket.socket", forbid_network)
    source = """---
schema_version: 1
person: {name: Example}
projects:
  - id: proj_demo
    title: Fictional private project title
    completion_status: in_progress
accomplishments:
  - id: acc_demo
    entry_id: proj_demo
    statement: Fictional private subtask statement
    completion_status: completed
resume_preferences:
  required_sections: [projects]
  required_entry_ids: [proj_demo]
  min_projects: 1
  max_projects: 1
  min_bullets_per_entry: 1
  max_bullets_per_entry: 2
---
Unknown notes are not more preferences.
"""
    path = tmp_path / "profile.md"
    path.write_bytes(source.encode("utf-8"))
    result = runner.invoke(app, ["validate-profile", "--profile", str(path)])
    assert result.exit_code == 0
    assert "acc_demo: unverified" in result.stdout
    assert "Fictional private" not in result.output
    assert path.read_bytes() == source.encode("utf-8")
    assert list(tmp_path.iterdir()) == [path]
    assert parse_profile(source).profile.resume_preferences.required_entry_ids == ["proj_demo"]


@pytest.mark.parametrize(
    "preferences",
    [
        "required_entry_ids: [proj_fictional_sensitive_unknown]",
        "required_entry_ids: [proj_demo]\n  excluded_entry_ids: [proj_demo]",
        "required_sections: [projects]\n  max_projects: 0",
        "max_projects: true",
    ],
)
def test_bad_preferences_fail_safely_without_echoing_input_values(
    tmp_path: Path, preferences: str
) -> None:
    source = (
        "---\nschema_version: 1\nperson: {name: Fictional sensitive name}\n"
        "projects: [{id: proj_demo, title: Fictional sensitive title}]\n"
        f"resume_preferences:\n  {preferences}\n---\n"
    )
    path = tmp_path / "invalid.md"
    path.write_text(source, encoding="utf-8")
    result = runner.invoke(app, ["validate-profile", "--profile", str(path)])
    assert result.exit_code == 1
    assert "resume_preferences" in result.stderr
    assert "Fictional sensitive" not in result.output
    assert "proj_fictional_sensitive_unknown" not in result.output
    assert "Traceback" not in result.output
