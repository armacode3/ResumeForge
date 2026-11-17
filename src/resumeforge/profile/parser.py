"""Bounded, safe loading of a documented Markdown/YAML profile convention."""

import re
from collections.abc import Hashable
from dataclasses import dataclass
from pathlib import Path

import yaml
from pydantic import ValidationError
from yaml.events import CollectionEndEvent, CollectionStartEvent
from yaml.nodes import MappingNode

from resumeforge.profile.models import UserProfile

MAX_PROFILE_BYTES = 1_048_576
MAX_YAML_DEPTH = 32


class ProfileError(ValueError):
    """An actionable profile error safe for CLI display without input-value dumps."""


@dataclass(frozen=True)
class ProfileDocument:
    profile: UserProfile
    markdown_notes: str
    source_text: str


class _ProfileLoader(yaml.SafeLoader):
    """Safe YAML subset: unique string keys, literal dates, true/false booleans only."""

    def construct_mapping(self, node: MappingNode, deep: bool = False) -> dict[Hashable, object]:
        result: dict[Hashable, object] = {}
        for key_node, value_node in node.value:
            key = self.construct_object(key_node, deep=deep)
            if not isinstance(key, str) or key in result:
                raise yaml.constructor.ConstructorError(
                    None, None, "Mapping keys must be unique strings", key_node.start_mark
                )
            result[key] = self.construct_object(value_node, deep=deep)
        return result


_ProfileLoader.yaml_implicit_resolvers = {
    key: [
        (tag, pattern)
        for tag, pattern in resolvers
        if tag not in {"tag:yaml.org,2002:bool", "tag:yaml.org,2002:timestamp"}
    ]
    for key, resolvers in yaml.SafeLoader.yaml_implicit_resolvers.items()
}
_ProfileLoader.add_implicit_resolver("tag:yaml.org,2002:bool", re.compile(r"^(true|false)$"), "tf")


def _load_front_matter(front_matter: str) -> object:
    depth = 0
    try:
        for event in yaml.parse(front_matter):
            if getattr(event, "anchor", None) is not None or isinstance(
                event, yaml.events.AliasEvent
            ):
                raise ProfileError(
                    "YAML anchors and aliases are not supported; write values explicitly."
                )
            if getattr(event, "tag", None) is not None:
                raise ProfileError("Explicit YAML tags are not supported; use plain values.")
            if isinstance(event, CollectionStartEvent):
                depth += 1
                if depth > MAX_YAML_DEPTH:
                    raise ProfileError(f"YAML nesting exceeds {MAX_YAML_DEPTH} levels.")
            elif isinstance(event, CollectionEndEvent):
                depth -= 1
        return yaml.load(front_matter, Loader=_ProfileLoader)
    except yaml.MarkedYAMLError as error:
        mark = error.problem_mark
        location = (
            f" near front-matter line {mark.line + 1}, column {mark.column + 1}" if mark else ""
        )
        raise ProfileError(
            f"Invalid YAML{location}; check syntax and use unique string keys."
        ) from None
    except yaml.YAMLError:
        raise ProfileError("Invalid YAML; check front-matter syntax.") from None


def parse_profile(source_text: str) -> ProfileDocument:
    """Parse text, preserving the exact original source and Markdown body."""
    try:
        size = len(source_text.encode("utf-8"))
    except UnicodeEncodeError:
        raise ProfileError("Profile must contain valid UTF-8 text.") from None
    if size > MAX_PROFILE_BYTES:
        raise ProfileError(
            f"Profile exceeds {MAX_PROFILE_BYTES} bytes; split or shorten the notes."
        )
    lines = source_text.removeprefix("\ufeff").splitlines(keepends=True)
    if not lines or lines[0].rstrip("\r\n") != "---":
        raise ProfileError("Start the profile with a YAML front-matter delimiter: ---")
    closing = next((i for i in range(1, len(lines)) if lines[i].rstrip("\r\n") == "---"), None)
    if closing is None:
        raise ProfileError("Close the YAML front matter with --- on its own line.")
    data = _load_front_matter("".join(lines[1:closing]))
    if not isinstance(data, dict):
        raise ProfileError("YAML front matter must be a mapping of profile fields.")
    try:
        profile = UserProfile.model_validate(data)
    except ValidationError as error:
        messages: list[str] = []
        for detail in error.errors(include_input=False, include_url=False):
            path = ".".join(
                str(part) if re.fullmatch(r"[a-z_][a-z0-9_]*|[0-9]+", str(part)) else "<field>"
                for part in detail["loc"]
            )
            messages.append(f"{path or 'profile'}: {detail['msg']}")
        raise ProfileError("\n".join(messages)) from None
    return ProfileDocument(profile, "".join(lines[closing + 1 :]), source_text)


def load_profile(path: Path) -> ProfileDocument:
    """Read a bounded regular UTF-8 file, preserving line endings without logging data."""
    try:
        if not path.is_file():
            raise ProfileError("Profile path must point to an existing regular file.")
        with path.open("rb") as handle:
            data = handle.read(MAX_PROFILE_BYTES + 1)
    except OSError:
        raise ProfileError(
            "Unable to read profile; check file permissions and availability."
        ) from None
    if len(data) > MAX_PROFILE_BYTES:
        raise ProfileError(
            f"Profile exceeds {MAX_PROFILE_BYTES} bytes; split or shorten the notes."
        )
    try:
        source_text = data.decode("utf-8")
    except UnicodeDecodeError:
        raise ProfileError("Profile must be a UTF-8 encoded Markdown file.") from None
    return parse_profile(source_text)
