# Evidence-linked wording drafts — updated for 0.15.0

This first Phase 4 slice adds `ResumeDocument` and `review-resume`: an offline boundary for
structured bullet wording and pending review. **Inspection does not generate polished wording,
approve claims, prove semantic support or render a resume.** The document is a narrow wording draft,
not a complete renderable resume: contact/entry metadata and skills/coursework remain references
or review placeholders in the accompanying plan.

## Run a source seed

```bash
resumeforge review-resume \
  --profile examples/profiles/sample.md \
  --job examples/jobs/backend_intern.md \
  --requirements examples/jobs/backend_intern.response.json \
  --selection examples/plans/backend_intern.selection.json \
  --confirm-review
```

Without `--draft`, the command copies each selected eligible accomplishment's **entire unchanged
statement** into one pending bullet. It does not condense statements or reuse profile bullet
wording. IDs are document-local `bullet_draft_<accomplishment suffix>` identifiers, not new profile
evidence IDs. All planned sections/entries, including empty mandatory placeholders, remain present.

The fictional example intentionally exits **3**: its education bullet-count conflict still blocks
the plan. No educational claim is invented. A user must deliberately resolve count preferences or
review/add genuine evidence, not fabricate facts to make the command pass. The profile is never
rewritten automatically. See `docs/PLANNING.md`.

## Inspect an edited draft

Success emits a review envelope with `document`, `plan`, per-bullet `bullets` observations, version,
document digest and warnings. To inspect edits, deliberately save **only its inner `document`** to
a private JSON file, edit wording there, then pass the same four inputs plus:

```text
--draft artifacts/private-draft.json --confirm-review
```

The outer review envelope, plan report, selection and historical profile bullets are not accepted
as draft input. No filename has implicit approval meaning. Four source paths remain explicit;
`--draft` is optional for inspection. Confirmation acknowledges review of requirements and
selection, **not bullet approval**, and is required before any input I/O. There is no provider,
network access, automatic profile read, write-back or model call. Version 0.10.0 adds a separate
`--decisions`/`--confirm-decisions` mode requiring an explicit draft; see `docs/REVIEW_DECISIONS.md`.

## Version-1 document contract

- `schema_version`: strict integer 1.
- `plan_sha256`: lowercase SHA-256 of the freshly recomputed plan snapshot.
- `status`: only `needs_review` (also the default); `approved` is rejected.
- `sections`: ordered records with `section` and ordered `entries`.
- Each entry has `entry_id` and ordered `bullets`; metadata-only entries have an empty list.
- Each bullet has a unique `id`, one `accomplishment_id`, nonblank `text` and
  `review_status: pending_review` (the only allowed state, also the default).

Sections, entries, bullet IDs and accomplishment references cannot be duplicated. The draft must
exactly preserve the current plan's sections, entries, evidence slots and their order. This version
supports one accomplishment per bullet, not splitting/merging evidence. To change content/order,
revise the explicit selection and seed/review a new draft rather than detach references.

The engine recomputes planning/matching from revalidated inputs; it accepts no caller-supplied
plan or review result as authority. Unknown, unselected, excluded, ineligible, cross-parent,
missing or reordered evidence cannot enter a current draft by supplying its hash. Any changed
profile model, preferences, exact job, reviewed requirements, selection, algorithm version or
other plan field invalidates the old binding. Notes are not enforced planning inputs and are not
part of the profile model hash. Hashes bind snapshots; they are not authentication or proof of
truth/review. Copying a current hash cannot bypass structural alignment checks.

`plan_sha256` hashes `asdict(plan)` JSON with sorted keys, compact separators, Unicode preserved,
and UTF-8 encoding. `document_sha256` hashes the validated document's compact Pydantic JSON,
including exact wording/IDs/order/default review states. These are model hashes, not file hashes.
Neither permits historical approval to transfer to changed wording or evidence.

## What review observations mean

Every bullet review contains its ID, entry/accomplishment IDs, complete source statement, original
in-progress-parent caveat where applicable, and one literal wording observation:

- `verbatim_source`: wording equals the entire selected source statement, case/whitespace included.
- `edited_requires_review`: any wording change, including harmless edits, introduced claims or
  lost qualifiers. No edits are repaired, normalized or silently approved.

**Both remain `pending_review`.** Literal equality does not prove factual truth or fit in a resume.
Edited wording is not automatically semantically false or supported. Inspection version
`resume-draft-review-v3` retains per-bullet `findings`, outer `findings_version` and `findings_sha256`:
literal numeric tokens absent from the statement and missing cues from a finite caveat vocabulary.
Exact spans, policy, characterization and blind spots are documented in `docs/CLAIM_FINDINGS.md`.
Empty findings are not support; technology/ownership and many qualifier changes remain undetected.
Inspection also adds per-bullet `source_fragments` and outer `fragments_version`/`fragments_sha256`:
source sentences/clauses absent as exact substrings of this draft, not semantic omissions.
Harmless paraphrases can flag; unchanged text used in a false context can escape. See
`docs/SOURCE_FRAGMENT_REVIEW.md`. The document itself stays schema version 1. Decision files now
require version 3, explicit finding acknowledgements and fragment dispositions. No historical
attestation is automatically upgraded; unreviewed fragments or revision requests keep approval pending.

The outer review is `blocked_by_plan` when count/evidence/required-content conflicts remain;
otherwise it is `needs_review`. Neither state is generation-ready or approved. Full job categories,
text/quotes and lexical associations remain in `plan`, never satisfaction verdicts. Empty required
or unscoped sections and metadata findings cannot disappear through wording edits.

## Limits, errors and privacy

Draft JSON is bounded to **1 MiB UTF-8**, at most **32 nested collections** and **8,192 characters
per bullet text**. Strict types/IDs/version, duplicate keys, unknown fields and nonstandard numeric
constants are checked. JSON arrays become immutable tuples; all nested models are frozen. Python
API inputs are revalidated snapshots, not trusted `model_copy`/`model_construct` shortcuts. Source
seeds that exceed draft limits fail safely; facts are never truncated to fit. The existing planning
comparison budget still applies. Limits are not a process sandbox or layout budget.

- **0:** review envelope emitted, no plan conflicts; every bullet still pending.
- **3:** envelope emitted with `blocked_by_plan`; inspect plan findings.
- **1:** invalid input, source/plan mismatch or draft-limit failure; no partial JSON.
- **2:** usage error/missing confirmation; input files are not read.

Reports deliberately contain submitted wording, selected eligible source statements and job text.
They remain private, including when wording contains sensitive or untrusted instructions. Such
instructions are data: they cannot activate tools, inference or approval. Contact fields, Markdown
notes, parent details, unselected/ineligible source claims and recorded metrics are not copied.
IDs/hashes are not anonymization. Keep real documents/reviews under ignored private directories,
not examples, commits or public logs. No rendering/execution is performed on submitted text.

Python API: `resumeforge.resume.review_resume(profile, job, requirements, selection, draft=None,
requirements_reviewed=True, selection_reviewed=True)` returns `ResumeReview`; optional `draft`
is a `ResumeDocument`. `parse_resume_document`/`load_resume_document` validate private draft JSON.
Safe boundary failures raise `ResumeError` (file loading may also raise `InputError`).

With an explicit draft, add `--worksheet` to emit a fresh inspection plus a separate unfilled
decision template. It cannot be combined with decision application; ordinary inspection is
unchanged. This output is not a draft or approval receipt. See `docs/REVIEW_WORKSHEETS.md` for
private extraction/completion, pending placeholders, byte limits and the unchanged confirmation gate.

Separate snapshot-bound human bullet-wording decisions are now available; pending document/
inspection states remain unchanged. Literal findings and explicit source-fragment review are now
available. Source-bound `suggest-wording` proposals are available in
0.12.0 with fake replay or explicitly acknowledged guarded local inference; see
`docs/WORDING_ASSISTANCE.md`. Full-resume approval, PDF/layout/rendering, history, automatic ranking
and cloud inference remain unimplemented. Separate `assemble-resume` now combines current wording
with explicitly selected metadata and finite readiness issues; see `docs/STRUCTURED_ASSEMBLY.md`.
Its output-only structured document is not an input wording draft or rendering approval.
