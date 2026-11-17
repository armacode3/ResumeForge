"""Exercise installed entry points from outside the source directory."""

import os
import subprocess
import sys
from pathlib import Path

import pytest

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
