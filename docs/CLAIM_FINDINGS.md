# Literal claim-review findings — 0.11.0

`review-resume` includes **deterministic observations**, not supported/unsupported or true/false
verdicts. No model is called, no wording rewritten, and all inspected bullets stay pending. Empty
findings are not evidence of correctness. Human decisions remain separate unsigned attestations
with `rendering_authorized: false`.

## Versioned contract

Inspection policy: `resume-draft-review-v2`. Finding policy: `literal-claim-findings-v1`, exposed
as `findings_version`. Each bullet retains its complete scoped statement, caveats and wording
status, plus `findings`. Each finding has:

- `id`: SHA-256 bound to finding policy, bullet/accomplishment IDs, full source/draft text, code,
  cue and both span fields.
- `code`: `numeric_token_absent_from_source` or `source_caveat_cue_not_retained`.
- `cue`: canonical lowercase cue for caveat findings, otherwise null.
- `source_span`: exact source cue occurrence, otherwise null.
- `draft_span`: exact new numeric occurrence, otherwise null.

Spans contain `start`, `end`, and unchanged `text`: **zero-based, end-exclusive Python Unicode
string indexes**, not UTF-8 byte offsets or JavaScript UTF-16 indexes. Slicing the cited text must
reproduce `text`. Null means that rule has no corresponding span, not missing input. The containing
bullet/document identify provenance. Numeric occurrences come first in draft-offset order, then
cue occurrences in source-offset order (canonical cue breaks ties). Repeated absent occurrences
have distinct IDs, not a deduplicated count.

`findings_sha256` binds finding policy, plan/document hashes and ordered bullet IDs with complete
finding records, including empty lists. Both finding hashes use sorted-key compact JSON, Unicode
preserved, UTF-8 encoded. No paths, timestamps or random IDs enter these hashes. These are snapshot
bindings, not identity authentication or evidence of truth/review.

Only the **selected accomplishment's entire statement** supplies comparison evidence. Other
accomplishments, metric fields, skills, parent lists/notes, old bullet wording and job text cannot
justify tokens. Existing eligibility/exclusion checks precede observations; no retrieval is widened
and no extra private source fields are copied into reports.

## Numeric rule

Tokenization uses this Python regex, without normalization:

```text
[0-9]+(?:[.,][0-9]+)*(?:%|[kKmMbB](?!\w))?
```

Each draft token not equal to any whole source token yields a finding. Membership is case-sensitive
and ignores frequency/location. `120` differs from `12`, and `12%` from `12`. Harmless equivalents
also flag: `1000` versus `1,000`, `5K` versus `5k`, `2.50%` versus `2.5%`. Embedded digits such as
`Python3` count. Tokens are not quantities or necessarily metrics; dates/IDs/versions can flag.
Commas and periods join runs alike, not as locale-aware separators.

Blind spots: number words, non-ASCII digits, arithmetic, units, signs, currencies, leading decimal
punctuation, ranges and scientific-notation semantics. `+12 ms` to `-12 seconds` yields no finding;
`.5` and `5` yield the same token. `1e3` splits into `1` and `3`; dates/ranges may split too. A number
retained in a different false claim escapes the rule. There is no technology/ownership detector.

## Finite caveat-cue rule

The complete vocabulary is:

```text
not; never; only; assisted; supported; contributed; under supervision;
under mentor review; under a mentor's review; prototype; experimental;
approximately; up to; in progress
```

Cues use Python case-insensitive matching, word boundaries and one-or-more whitespace characters
between words. A source occurrence flags only if **no occurrence of the same cue anywhere in the
draft** remains. Spans preserve original case/whitespace. Punctuation/hyphen changes are not
equivalent. The two mentor phrases are separate literals, not interchangeable synonyms.

This is not a qualifier, negation, completion-state or ownership parser. Harmless paraphrases
flag (`under mentor review` to `with a mentor checking work`). Curly apostrophes, inflections,
synonyms, other languages and unlisted qualifiers are not covered. A cue in unrelated/reversed/
negated context suppresses findings; repeated-cue count reductions are not checked. Existing
`parent_entry_in_progress` caveats stay visible independently; no inference is made about whether
parent status must appear in each bullet's wording.

## Measured characterization, not semantic accuracy

`tests/unit/test_claim_findings.py` fixes 20 synthetic source/draft pairs with exact expected
tokens/cues/spans: **10 numeric occurrences and 11 missing-cue occurrences** in total. All 20 match
those literal expectations. Cases include unchanged wording, changed numbers/formatting,
paraphrases, repeated cues/tokens, boundaries, Unicode, versions and deliberate misses. Additional
tests exercise all 14 published cues, provenance/policy hashes, Unicode offsets, immutability,
budgets and the decision/CLI gates. This is rule characterization, not real-world precision/recall,
a model evaluation or a guarantee against fabricated claims.

## Acknowledgements, limits and privacy

Inspect edits before deciding. Version-2 decision files bind `findings_sha256` and require an
explicit `acknowledged_finding_ids` list per decision (even empty). Copy only IDs actually reviewed
from that bullet's current findings; reasons remain required. Unknown/cross-bullet, duplicate,
malformed or stale acknowledgements fail. Version-1 decisions must be reviewed and authored anew,
not mechanically upgraded. See `docs/REVIEW_DECISIONS.md` for schema/status/exit details.

Approval with any unacknowledged finding stays pending. The result shows acknowledged and
unacknowledged IDs. All acknowledged permits only the existing narrow user-attestation state under
a conflict-free plan, **not issue resolution, semantic support, fact promotion or rendering**.
Findings stay visible unchanged. Rejection needs no acknowledgement and preserves content;
missing decisions stay pending, and plan conflicts take precedence.

Existing 1 MiB input, 8,192-character bullet and planning budgets remain. Maximum observations:
1,024 per bullet and 4,096 per inspection. Exceeding either fails safely with no partial JSON;
never truncate findings. These are resource limits, not resume length/evidence sufficiency checks.
No network, downloads, write-back or history persistence occurs. Spans/IDs/hashes, reports and
decision reasons remain private. Untrusted text cannot activate tools or grant approval.

Next: controlled wording assistance under the explicit local-model policy. Semantic proof,
metadata/full-resume approval, rendering, automatic ranking and cloud inference remain out of
scope. Changed observation policies must be versioned to invalidate prior attestations.
