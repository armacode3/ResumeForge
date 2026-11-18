# Source-fragment review — 0.15.0

An edited bullet can retain a caveat word while losing its scope: “never deployed to production”
can become “never deployed.” The finite cue findings do not catch that change. Inspection now
also exposes **source fragments not retained verbatim**, so a user must account for those
fragments before approving wording. This is a conservative review aid, not semantic omission,
qualifier detection, coverage scoring or proof that a paraphrase is supported.

No model is called, no wording repaired, no source promoted, and no files are rewritten. All
draft/inspection bullets remain pending, including unchanged copies. User decisions remain
unsigned attestations with `scope: bullet_wording_only` and `rendering_authorized: false`.

## Observation contract

Inspection is now `resume-draft-review-v3`; fragment policy is `literal-source-fragments-v1`.
`ResumeReview` adds `fragments_version` and `fragments_sha256`. Each `BulletReview.source_fragments`
contains ordered records `{id, code, source_span}` with code
`source_fragment_not_retained_verbatim`. Only the selected accomplishment's entire statement
is compared with that bullet's wording. Other statements, metrics, parent fields, notes,
historical wording and job text are not evidence for retention.

The exact deterministic policy:

1. Split the source immediately **after** `.`, `!`, `?` or `;` when followed by Python whitespace
   or end of text; also split after CR/LF runs. Keep terminal punctuation.
2. Trim each segment's leading/trailing Python whitespace, preserving its remaining text and
   original zero-based, end-exclusive Python Unicode string offsets.
3. Ignore empty segments. Emit each remaining segment only if its exact, case-sensitive text
   is **not a substring anywhere in this bullet's draft text**. Preserve source-offset order.

The span's `text` must equal `source_statement[start:end]`. These are not byte or UTF-16 offsets.
Decimals/version strings without following whitespace do not split (`2.5`, `Python 3.12`).
Abbreviations such as `Dr. Smith` do split. Punctuation followed by a closing quote does not
create a boundary until the policy encounters another delimiter. Commas, colons and other-language
sentence marks do not split. This deliberately is not a linguistic sentence/clause parser.

Examples:

| Source | Draft | Observation |
| --- | --- | --- |
| `Built tests. Never deployed to production.` | `Built tests. Never deployed.` | `Never deployed to production.` needs review, even though `never` remains. |
| `No improvement was measured.` | `No improvement.` | Full fragment needs review; no automatic verdict about the stronger negative claim. |
| `Assisted with tests.` | `Helped test.` | Harmless paraphrase can flag. |
| `Tested. Tested.` | `Tested.` | No fragment flags: membership ignores repetition counts. |
| `Led tests.` | `Never Led tests.` | No fragment flags: substring retention cannot establish correct scope. |

Changed case, punctuation or internal whitespace can flag a whole sentence. Reordering retained
segments, repeated-source reduction and exact text reused in false/new context can escape. Added
unsupported claims are not classified by this policy. A single long unpunctuated statement is
one fragment, not independently extracted claims. **Empty fragment lists are not source coverage
or safety certificates; counts are not quality or relevance scores.** Existing literal numeric/
cue findings are unchanged, independent observations, not semantic proof either.

Fragment IDs hash sorted-key compact Unicode-preserving JSON of policy, bullet/accomplishment IDs,
full source/draft text and source span. Duplicate text occurrences have different offsets/IDs when
absent. `fragments_sha256` hashes policy, plan/document hashes and ordered bullet IDs with full
fragment records, including empty lists. No paths/times/random IDs enter either hash. These bind
snapshots, not identity, truth, human attention or correct semantic relationships.

Limits: at most 1,024 emitted fragments per bullet and 4,096 per inspection, separately from the
existing finding caps. Exceeding a cap fails safely without partial JSON or truncation. Existing
1 MiB JSON, 32-level nesting, 8,192-character bullet and planning limits remain in force.

## Explicit human dispositions

Run `review-resume --draft ... --confirm-review` on the original four source inputs. Inspect each
fragment alongside the **entire source and draft**, including the surrounding negation, bounds,
attribution and project relationships. Never assume the literal fragments are independent facts.

Decision schema **3** binds current `fragments_sha256` in addition to policy, plan, document and
findings bindings. Every bullet decision requires `fragment_decisions` (use `[]` only when no
fragment has been reviewed). Each record has exactly:

| Field | Meaning |
| --- | --- |
| `fragment_id` | Current fragment ID on this same bullet. |
| `disposition` | `represented_in_draft`, `omission_accepted` or `needs_revision`. |
| `reason` | Required nonblank user rationale, at most 8,192 characters. |
| `draft_span` | Exact nonblank `{start, end, text}` passage in this bullet for `represented_in_draft`; required explicit null for the other two dispositions. |

`represented_in_draft` means the user asserts the linked passage accounts for the fragment.
Code validates exact offsets/text, **not semantic equivalence**; a wrong user linkage remains
possible. `omission_accepted` records a deliberate user acceptance of omitted source content;
it does not certify that dropping a qualifier is safe. Do not accept omissions of material scope
merely to make wording shorter. `needs_revision` records an unresolved concern and blocks wording
approval. Edit the draft deliberately, inspect again and author fresh decisions to resolve it;
the application never repairs or removes content automatically.

Unknown/cross-bullet/stale IDs, duplicates, invalid spans and malformed/absent fields fail with no
partial approval. Any missing disposition or `needs_revision` keeps an attempted approval pending,
even if all old numeric/cue findings are acknowledged. Rejection needs no fragment review (use an
empty list), but any supplied records must still be valid. Plan conflicts still block approvals;
missing bullet decisions remain pending. Both numeric/cue acknowledgements and fragment review
are required, independently. Reversing decision input order does not reorder source observations.

Applied records retain `fragment_decisions` in source order, `unreviewed_fragment_ids`, and
`revision_fragment_ids`. All source observations and original content remain visible after user
approval, accepted omission or rejection. See `docs/REVIEW_DECISIONS.md` for the full file/CLI
contract and exit codes. These files, reasons, spans and hashes remain private, not anonymized.

## Compatibility and limits of this iteration

Version-1 profiles/drafts/wording responses remain valid with no rewrite. Provider instructions,
minimized request data and request digests remain unchanged; model responses cannot author fragment
decisions or approvals. Inspection now returns additional observations under a new policy.
Old decision formats 1/2 are rejected; re-inspect and deliberately author version-3 decisions.
Never mechanically copy hashes or upgrade attestations. No private decisions were migrated.

The frozen wording corpora, protocols and historical results are untouched. Synthetic tests
characterize literal behavior and decision invariants, not real-world semantic precision/recall.
No live evaluation was run or implicitly authorized. The concise objective stays experimental,
and the conservative source-faithful default stays unchanged. No semantic proof, full-resume/
metadata approval, rendering, automatic ranking, persistence or cloud inference is added.
