"""Run the repository-only benchmark in a fresh process without a live model."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.integration


def test_developer_tool_defaults_to_read_only_reference_replay(tmp_path: Path) -> None:
    script = Path(__file__).resolve().parents[2] / "scripts/evaluate_jobs.py"
    result = subprocess.run(
        [sys.executable, str(script)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report["mode"] == "reference_replay"
    assert report["total_cases"] == report["exact_match_cases"] == 6
    assert result.stderr == ""
    assert list(tmp_path.iterdir()) == []
