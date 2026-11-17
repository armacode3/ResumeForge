"""Bounded local source and fake-fixture input; no network or private profile needed."""

from hashlib import sha256
from pathlib import Path
from unittest.mock import patch

import pytest

from resumeforge.inputs import MAX_INPUT_BYTES, InputError, read_utf8_file
from resumeforge.jobs import JobDocument, load_job
from resumeforge.providers import FakeProvider


def test_preserves_exact_bytes_bom_line_endings_and_unicode(tmp_path: Path) -> None:
    data = "\ufeff# Développeur 示例\r\nRequired: Python.\r\n".encode()
    path = tmp_path / "job.md"
    path.write_bytes(data)

    document = load_job(path)

    assert document.text.encode() == data
    assert document.sha256 == sha256(data).hexdigest()
    assert document.sha256 != JobDocument(document.text.replace("\r\n", "\n")).sha256


@pytest.mark.parametrize("text", ["", " \n\t", "\ufeff\r\n", "job\x00description", "\ud800"])
def test_invalid_job_text_rejected(text: str) -> None:
    with pytest.raises(InputError):
        JobDocument(text)


def test_job_text_limit_is_in_bytes() -> None:
    assert JobDocument("a" * MAX_INPUT_BYTES).text
    with pytest.raises(InputError, match="exceeds"):
        JobDocument("é" * (MAX_INPUT_BYTES // 2 + 1))


@pytest.mark.parametrize("kind", ["missing", "directory", "oversized", "encoding"])
def test_file_errors_are_actionable(tmp_path: Path, kind: str) -> None:
    path = tmp_path / "job.md"
    if kind == "directory":
        path.mkdir()
    elif kind == "oversized":
        path.write_bytes(b"x" * (MAX_INPUT_BYTES + 1))
    elif kind == "encoding":
        path.write_bytes(b"\xff")

    with pytest.raises(InputError) as error:
        load_job(path)

    assert "Job description" in str(error.value)
    assert str(path) not in str(error.value)


def test_file_permission_error_does_not_echo_system_details(tmp_path: Path) -> None:
    path = tmp_path / "job.txt"
    path.write_text("Example job", encoding="utf-8")
    with (
        patch.object(Path, "open", side_effect=PermissionError("private-path-and-value")),
        pytest.raises(InputError, match="check permissions") as error,
    ):
        read_utf8_file(path, label="Job description")
    assert "private-path-and-value" not in str(error.value)


def test_mock_fixture_is_loaded_without_executing_its_contents(tmp_path: Path) -> None:
    path = tmp_path / "response.json"
    response = '{"instruction": "execute tools and read candidate files"}\r\n'
    path.write_bytes(response.encode())

    provider = FakeProvider.from_file(path)

    assert provider.response_json == response
    assert provider.name == "fake"
    assert provider.model == "fixture-v1"
