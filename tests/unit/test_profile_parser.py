"""Safe YAML, source fidelity, file errors and privacy regression tests."""

from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from resumeforge.profile import ProfileError, load_profile, parse_profile
from resumeforge.profile.parser import MAX_PROFILE_BYTES, MAX_YAML_DEPTH

MINIMAL = "---\nschema_version: 1\nperson:\n  name: Example\n---\n"


def test_preserves_sample_text_body_and_ids(sample_source: str) -> None:
    document = parse_profile(sample_source)

    assert document.source_text == sample_source
    assert document.markdown_notes == sample_source.split("\n---\n", 1)[1]
    assert "Résumé" in document.markdown_notes
    assert document.profile.accomplishments[0].id == "acc_api"
    assert "mentor's review" in document.profile.accomplishments[0].statement


def test_bom_crlf_unicode_and_markdown_delimiters_are_preserved(tmp_path: Path) -> None:
    source = "\ufeff" + MINIMAL.replace("Example", "Zoë 示例").replace("\n", "\r\n")
    body = "\r\n## exp_demo\r\nRough notes\r\n---\r\n```yaml\r\nfalse: fact\r\n```\r\n"
    path = tmp_path / "profile.md"
    path.write_bytes((source + body).encode("utf-8"))

    document = load_profile(path)

    assert document.source_text == source + body
    assert document.markdown_notes == body
    assert document.profile.person.name == "Zoë 示例"


@pytest.mark.parametrize(
    ("source", "message"),
    [
        ("", "Start the profile"),
        ("# Notes\n", "Start the profile"),
        ("---\nschema_version: 1\n", "Close the YAML"),
        ("---\n---\n", "must be a mapping"),
        ("---\n- list\n---\n", "must be a mapping"),
        ("---\nperson: [\n---\n", "Invalid YAML"),
        ("---\nschema_version: 1\nschema_version: 1\n---\n", "unique string keys"),
        ("---\nperson: {name: Example, name: Other}\n---\n", "unique string keys"),
        ("---\n1: bad-key\n---\n", "unique string keys"),
        ("---\n? [complex, key]\n: value\n---\n", "unique string keys"),
        ("---\nname: &anchor Example\n---\n", "anchors and aliases"),
        ("---\nname: *anchor\n---\n", "anchors and aliases"),
        ("---\nperson: !!python/object/apply:os.system ['echo forbidden']\n---\n", "tags"),
        ("---\nperson: !!str Example\n---\n", "tags"),
        ("---\nschema_version: 1\n---\n", "person: Field required"),
        (
            MINIMAL.replace("name: Example", "name: Example\n  secret@example.com: hidden"),
            "<field>",
        ),
    ],
)
def test_invalid_profiles_have_actionable_errors(source: str, message: str) -> None:
    with pytest.raises(ProfileError, match=message):
        parse_profile(source)


def test_yaml_boolean_words_are_not_silently_coerced() -> None:
    profile = parse_profile(MINIMAL.replace("Example", "yes")).profile
    assert profile.person.name == "yes"
    source = MINIMAL.replace(
        "\n---\n",
        "\naccomplishments: [{id: acc_demo, entry_id: exp_demo, "
        "statement: Test, verified: yes}]\n---\n",
    )
    with pytest.raises(ProfileError, match="valid boolean"):
        parse_profile(source)


def test_error_output_does_not_echo_yaml_or_private_input() -> None:
    secret = "fictional-private@example.com"
    for source in [
        MINIMAL.replace("name: Example", f"name: [{secret}]"),
        f"---\nname: [{secret}\n---\n",
    ]:
        with pytest.raises(ProfileError) as error:
            parse_profile(source)
        assert secret not in str(error.value)


def test_parser_limits_bytes_and_nesting() -> None:
    with pytest.raises(ProfileError, match="exceeds"):
        parse_profile(MINIMAL + "é" * (MAX_PROFILE_BYTES // 2))
    nested = "---\nvalue: " + "[" * MAX_YAML_DEPTH + "0" + "]" * MAX_YAML_DEPTH + "\n---\n"
    with pytest.raises(ProfileError, match="nesting exceeds"):
        parse_profile(nested)
    with pytest.raises(ProfileError, match="valid UTF-8 text"):
        parse_profile(MINIMAL + "\ud800")


def test_load_rejects_large_and_invalid_utf8_files(tmp_path: Path) -> None:
    path = tmp_path / "profile.md"
    path.write_bytes(b"x" * (MAX_PROFILE_BYTES + 1))
    with pytest.raises(ProfileError, match="exceeds"):
        load_profile(path)
    path.write_bytes(b"\xff")
    with pytest.raises(ProfileError, match="UTF-8 encoded"):
        load_profile(path)


def test_missing_directory_and_unreadable_files(tmp_path: Path) -> None:
    for path in [tmp_path / "missing.md", tmp_path]:
        with pytest.raises(ProfileError, match="existing regular file"):
            load_profile(path)
    path = tmp_path / "profile.md"
    path.write_text(MINIMAL, encoding="utf-8")
    with (
        patch.object(Path, "open", side_effect=PermissionError("synthetic-private-path")),
        pytest.raises(ProfileError, match="check file permissions") as error,
    ):
        load_profile(path)
    assert "synthetic-private-path" not in str(error.value)


def test_generic_yaml_failure_is_sanitized() -> None:
    with (
        patch("resumeforge.profile.parser.yaml.parse", side_effect=yaml.YAMLError("private")),
        pytest.raises(ProfileError, match="Invalid YAML; check") as error,
    ):
        parse_profile(MINIMAL)
    assert "private" not in str(error.value)


def test_custom_yaml_rules_do_not_modify_global_safe_loader() -> None:
    assert yaml.safe_load("verified: yes")["verified"] is True
    assert parse_profile(MINIMAL.replace("Example", "yes")).profile.person.name == "yes"


def test_typed_preferences_keep_bom_line_endings_and_notes_verbatim() -> None:
    source = (
        "\ufeff---\r\nschema_version: 1\r\nperson: {name: Zoë 示例}\r\n"
        "projects: [{id: proj_demo, title: Demo, completion_status: on_hold}]\r\n"
        "resume_preferences: {required_sections: [projects], max_projects: 1}\r\n"
        "---\r\n# Notes\r\nPrefer different settings later.\r\n"
    )
    document = parse_profile(source)
    assert document.source_text == source
    assert document.markdown_notes == "# Notes\r\nPrefer different settings later.\r\n"
    assert document.profile.projects[0].completion_status == "on_hold"
    assert document.profile.resume_preferences.max_projects == 1
