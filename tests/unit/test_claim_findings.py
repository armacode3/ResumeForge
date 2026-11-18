"""Synthetic characterization of literal rules, including deliberate misses/false alarms."""

import pytest
from pydantic import ValidationError

from resumeforge.resume import ResumeError
from resumeforge.resume.findings import CAVEAT_CUES, MAX_BULLET_FINDINGS, inspect_claims


@pytest.mark.parametrize(
    ("source", "draft", "numbers", "cues"),
    [
        (
            "Tested 12 endpoints under mentor review.",
            "Tested 120 endpoints.",
            ["120"],
            ["under mentor review"],
        ),
        ("Tested 12 endpoints.", "Tested 12 endpoints.", [], []),
        ("Measured 1,000 at 2.5%.", "Measured 1000 at 2.50%.", ["1000", "2.50%"], []),
        ("Used Python3 and 5k records.", "Used Python4 and 5K records.", ["4", "5K"], []),
        ("Measured 12 and 4.", "Measured 12% and 40.", ["12%", "40"], []),
        ("Used 12 tests.", "Used 12 and 12 tests.", [], []),
        (
            "Not a prototype; only assisted.",
            "Led delivery.",
            [],
            ["not", "prototype", "only", "assisted"],
        ),
        ("Under mentor review.", "UNDER\nMENTOR  REVIEW.", [], []),
        ("Under mentor review.", "With a mentor checking work.", [], ["under mentor review"]),
        ("Assisted and assisted.", "Led delivery.", [], ["assisted", "assisted"]),
        ("Only tested.", "Lonely tester.", [], ["only"]),
        # Blind spots: same token/cue elsewhere is enough; meaning/context are not checked.
        ("Did not lead; tested 12 endpoints.", "Not incidental: led 12 teams.", [], []),
        ("Tested twelve endpoints.", "Tested ninety endpoints.", [], []),
        ("Measured +12 ms.", "Measured -12 seconds.", [], []),
        ("Helped with testing.", "Owned Kubernetes deployment.", [], []),
        ("測定１２", "測定９３", [], []),
        ("Measured .5.", "Measured 5.", [], []),
        ("Measured 1e3.", "Measured 1e4.", ["4"], []),
        ("", "99 99", ["99", "99"], []),
        ("In progress prototype.", "In-progress demonstration.", [], ["in progress", "prototype"]),
    ],
)
def test_literal_characterization(
    source: str, draft: str, numbers: list[str], cues: list[str]
) -> None:
    findings = inspect_claims("bullet_synthetic", "acc_synthetic", source, draft)
    assert [f.draft_span.text for f in findings if f.draft_span] == numbers
    assert [f.cue for f in findings if f.source_span] == cues
    assert len({f.id for f in findings}) == len(findings)
    for finding in findings:
        if finding.source_span:
            span = finding.source_span
            assert source[span.start : span.end] == span.text
            assert finding.draft_span is None
            assert finding.code == "source_caveat_cue_not_retained"
        else:
            assert finding.draft_span is not None
            span = finding.draft_span
            assert draft[span.start : span.end] == span.text
            assert finding.cue is None
            assert finding.code == "numeric_token_absent_from_source"
    assert findings == inspect_claims("bullet_synthetic", "acc_synthetic", source, draft)


@pytest.mark.parametrize("cue", CAVEAT_CUES)
def test_every_published_cue_is_observed_and_verbatim_has_no_findings(cue: str) -> None:
    source = f"😀 café {cue.upper()} in a fictional statement."
    findings = inspect_claims("bullet_example", "acc_example", source, "Reworded.")
    assert len(findings) == 1
    assert findings[0].source_span is not None
    assert findings[0].source_span.start == 7
    assert findings[0].cue == cue
    assert inspect_claims("bullet_example", "acc_example", source, source) == ()
    with pytest.raises(ValidationError):
        findings[0].id = "0" * 64


@pytest.mark.parametrize("change", ["bullet", "accomplishment", "source", "draft", "policy"])
def test_finding_identity_binds_full_text_provenance_and_policy(
    change: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    args = ["bullet_example", "acc_example", "Tested 12.", "Tested 99."]
    original = inspect_claims(*args)[0]
    if change == "policy":
        monkeypatch.setattr("resumeforge.resume.findings.FINDINGS_VERSION", "future-policy")
    else:
        args[["bullet", "accomplishment", "source", "draft"].index(change)] += " changed"
    current = inspect_claims(*args)[0]
    assert original.id != current.id


def test_excessive_findings_fail_without_truncation_or_input_disclosure() -> None:
    accepted = inspect_claims("bullet_example", "acc_example", "", "9 " * MAX_BULLET_FINDINGS)
    assert len(accepted) == MAX_BULLET_FINDINGS
    with pytest.raises(ResumeError, match="finding limit") as error:
        inspect_claims(
            "bullet_example", "acc_example", "private source", "9 " * (MAX_BULLET_FINDINGS + 1)
        )
    assert "private source" not in str(error.value)
