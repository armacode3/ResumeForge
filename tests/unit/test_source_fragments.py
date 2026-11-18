"""Literal fragment characterization is not semantic omission detection."""

import pytest
from pydantic import ValidationError

from resumeforge.resume import ResumeError
from resumeforge.resume.fragments import MAX_BULLET_FRAGMENTS, inspect_source_fragments


@pytest.mark.parametrize(
    ("source", "draft", "expected"),
    [
        (
            "Built tests. Never deployed to production.",
            "Built tests. Never deployed.",
            ["Never deployed to production."],
        ),
        ("No improvement was measured.", "No improvement.", ["No improvement was measured."]),
        (
            "Completed checks; the larger project remains in progress.",
            "Completed checks; not part of the larger project.",
            ["the larger project remains in progress."],
        ),
        ("Assisted with tests.", "Helped test.", ["Assisted with tests."]),
        ("A. B? C! D; E\nF", "Unrelated.", ["A.", "B?", "C!", "D;", "E", "F"]),
        (
            "Used Python 3.12 with 2.5% overhead.",
            "Reworded.",
            ["Used Python 3.12 with 2.5% overhead."],
        ),
        (
            "  😀 café tested.\r\n  No speed gain measured.  ",
            "😀 café tested.",
            ["No speed gain measured."],
        ),
        ("Tested. Tested.", "Reworded.", ["Tested.", "Tested."]),
        # Deliberate blind spots: membership, not order, counts or semantic scope.
        ("Tested. Tested.", "Tested.", []),
        ("A. B.", "B. A.", []),
        ("Led tests.", "Never Led tests.", []),
        # Literal case/whitespace/punctuation changes can flag harmless rewrites.
        ("Used Python.", "used Python.", ["Used Python."]),
        ("Used  Python.", "Used Python.", ["Used  Python."]),
        ("Tested.", "Tested!", ["Tested."]),
        ("Dr. Smith tested.", "Rephrased.", ["Dr.", "Smith tested."]),
        ('Said "tested." Then stopped.', "Rephrased.", ['Said "tested." Then stopped.']),
        ("測定。確認。", "Rephrased.", ["測定。確認。"]),
        ("Part: tested, checked", "Rephrased.", ["Part: tested, checked"]),
        ("", "New text.", []),
        (" \n\t", "Anything.", []),
        ("Tested.", "Tested.", []),
    ],
)
def test_fragment_characterization(source: str, draft: str, expected: list[str]) -> None:
    fragments = inspect_source_fragments("bullet_example", "acc_example", source, draft)
    assert [f.source_span.text for f in fragments] == expected
    assert len({f.id for f in fragments}) == len(fragments)
    for fragment in fragments:
        span = fragment.source_span
        assert source[span.start : span.end] == span.text
        assert fragment.code == "source_fragment_not_retained_verbatim"
        with pytest.raises(ValidationError):
            fragment.id = "0" * 64
    assert fragments == inspect_source_fragments("bullet_example", "acc_example", source, draft)


@pytest.mark.parametrize("change", ["bullet", "accomplishment", "source", "draft", "policy"])
def test_fragment_ids_bind_full_text_and_provenance(
    change: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    args = ["bullet_example", "acc_example", "Never deployed to production.", "Never deployed."]
    original = inspect_source_fragments(*args)[0]
    if change == "policy":
        monkeypatch.setattr("resumeforge.resume.fragments.FRAGMENTS_VERSION", "future-policy")
    else:
        args[["bullet", "accomplishment", "source", "draft"].index(change)] += " changed"
    assert inspect_source_fragments(*args)[0].id != original.id


def test_fragment_limits_fail_closed_and_do_not_disclose_source() -> None:
    source = "X; " * MAX_BULLET_FRAGMENTS
    assert (
        len(inspect_source_fragments("bullet_example", "acc_example", source, "Other."))
        == MAX_BULLET_FRAGMENTS
    )
    with pytest.raises(ResumeError, match="fragment limit") as error:
        inspect_source_fragments("bullet_example", "acc_example", source + "private;", "Other.")
    assert "private" not in str(error.value)


def test_source_offsets_are_unicode_string_not_bytes_or_utf16() -> None:
    source = "😀 Tested.  café checks."
    fragment = inspect_source_fragments("bullet_example", "acc_example", source, "😀 Tested.")[0]
    assert fragment.source_span.start == 11
    assert source[fragment.source_span.start : fragment.source_span.end] == "café checks."
