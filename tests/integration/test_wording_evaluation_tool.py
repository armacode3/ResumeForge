"""The repository runner works with installed modules and has no implicit live inference."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.integration


def test_wording_runner_default_is_read_only_source_replay(
    sample_path: Path, tmp_path: Path
) -> None:
    script = sample_path.parents[2] / "scripts/evaluate_wording.py"
    result = subprocess.run(
        [sys.executable, str(script)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
        timeout=15,
    )
    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report["mode"] == "source_seed_replay"
    assert report["total_cases"] == report["validated_cases"] == 6
    assert report["manual_review_status"] == "not_performed"
    assert report["provider_calls"] == 6 and not report["rendering_authorized"]
    assert list(tmp_path.iterdir()) == []
