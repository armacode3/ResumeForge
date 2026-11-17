"""Regression-test private-path safeguards without creating private data."""

import subprocess
from pathlib import Path

import pytest

pytestmark = pytest.mark.integration


def test_gitignore_protects_private_paths_but_allows_sanitized_examples(tmp_path: Path) -> None:
    repository_root = Path(__file__).resolve().parents[2]
    (tmp_path / ".gitignore").write_text(
        (repository_root / ".gitignore").read_text(encoding="utf-8"), encoding="utf-8"
    )
    subprocess.run(
        ["git", "init", "--quiet", str(tmp_path)],
        check=True,
        capture_output=True,
        text=True,
        timeout=10,
    )
    private_paths = [
        ".env",
        ".env.production",
        "data/profile/user_information.md",
        "artifacts/resume.txt",
        "outputs/tailoring_report.md",
        "resume.pdf",
        "resume.tex",
        "history.sqlite3",
        "history.sqlite3-wal",
        ".venv/pyvenv.cfg",
    ]
    public_paths = [
        ".env.example",
        "examples/profiles/sample.md",
        "tests/fixtures/profile.md",
        "templates/jakes/resume.tex",
        "config/resume_rules.md",
    ]

    result = subprocess.run(
        ["git", "check-ignore", "--no-index", "--stdin"],
        cwd=tmp_path,
        input="\n".join([*private_paths, *public_paths]) + "\n",
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert set(result.stdout.splitlines()) == set(private_paths)
    assert result.stderr == ""
