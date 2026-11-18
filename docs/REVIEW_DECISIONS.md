# Snapshot-bound human wording decisions — 0.15.0

This slice adds explicit per-bullet **user attestations**, applied only to an exact current draft
and plan. It does not prove factual truth, authenticate a reviewer, approve metadata/job fit/layout,
generate wording or authorize rendering. Profile verification flags and source facts are unchanged.

## Workflow

For less manual copying, `review-resume --draft ... --worksheet --confirm-review` now emits fresh
review context and an unfilled decision template. Extract only `decision_template`, deliberately
complete the records actually reviewed, and remove unresolved placeholder records. Nulls are not
valid decisions; this does not preselect approval, acknowledge findings or bypass confirmation.
See `docs/REVIEW_WORKSHEETS.md`. The existing v3 decision format and all gates below are unchanged.

1. Use `review-resume` as documented in `docs/RESUME_DRAFTS.md`. Save its inner `document`
   privately, inspect the full source statements, scope caveats, job context and plan findings,
   and deliberately edit wording if necessary.
2. Inspect that exact edited document with `--draft`. Use the resulting inspection version,
   document, plan, findings and fragment hashes when authoring a separate private decision file.
3. For each bullet you actually reviewed, record `approve` or `reject`, a nonblank reason and
   explicit `acknowledged_finding_ids` (empty if none). Inspect findings before acknowledging them.
    Do not bulk-approve because a schema passed, wording is verbatim, or an LLM suggested approval.
   Also record explicit `fragment_decisions` for source fragments not retained verbatim: link an
   exact draft passage, accept an omission with a reason, or mark it as needing revision. Missing
   fragment reviews and revision requests keep approval pending; see `docs/SOURCE_FRAGMENT_REVIEW.md`.
4. Apply the file with both source-review acknowledgement and separate decision confirmation:

```bash
resumeforge review-resume \
  --profile data/profile/user_information.md \
  --job artifacts/job.md \
  --requirements artifacts/reviewed-requirements.json \
  --selection artifacts/selection.json \
  --draft artifacts/draft.json \
  --decisions artifacts/decisions.json \
  --confirm-review --confirm-decisions
```

All files are explicit local inputs that you must create/review privately. The command writes
nothing unless you deliberately redirect stdout. No private profile, draft or decisions were
approved or migrated as part of implementing this feature. Normal tests use fictional assertions.

`--confirm-review` still acknowledges requirements/selection review; it does not approve wording.
`--confirm-decisions` additionally asserts that you reviewed the submitted decisions. Decisions
require an explicit `--draft`; implicit source-seed approvals and confirmation without a decision
file are usage errors. These option checks occur before any input I/O. JSON text cannot supply
either CLI confirmation or activate a provider/tool.

## Decision file contract (version 3)

Version-1/2 files are deliberately rejected. Inspect the current snapshot and author new decisions;
do not mechanically change versions/hashes to carry earlier attestations forward.

The root has exactly these fields:

| Field | Required value/source |
| --- | --- |
| `schema_version` | Strict integer `3`. |
| `review_version` | Current `resume-draft-review-v3`, copied from the draft inspection. |
| `plan_sha256` | `inspection.document.plan_sha256`, not a file hash. |
| `document_sha256` | `inspection.document_sha256`, including exact wording/IDs/order/default states. |
| `findings_sha256` | `inspection.findings_sha256`, binding policy and all ordered literal findings. |
| `fragments_sha256` | `inspection.fragments_sha256`, binding fragment policy and ordered source observations. |
| `bullets` | Distinct records with `bullet_id`, `decision`, `reason`, `acknowledged_finding_ids` and `fragment_decisions`, using actual IDs from the current inspection. |

`decision` is exactly `approve` or `reject`. A nonblank reason of at most 8,192 characters is required
for either choice. Empty `bullets` and omitted individual bullets are allowed but remain pending;
duplicate/conflicting decisions or unknown bullet IDs are rejected, not merged or silently ignored.
Input order does not reorder the draft; output decisions follow draft order.

`acknowledged_finding_ids` is required, contains distinct lowercase SHA-256 IDs, and may reference
only current findings on the same bullet. Approval needs every finding acknowledged or stays
pending. Rejection needs no acknowledgement. Acknowledgement is not resolution or semantic
support; findings stay visible. See `docs/CLAIM_FINDINGS.md` for rules, spans, limits and blind spots.

`fragment_decisions` is required (possibly empty) and contains distinct records with `fragment_id`,
`disposition`, nonblank `reason` and explicit `draft_span`. Dispositions are `represented_in_draft`
(requires an exact nonempty passage in that same draft bullet), `omission_accepted` (null span),
or `needs_revision` (null span). A passage is `{start, end, text}` using Python Unicode offsets;
code checks literal agreement, not equivalence. Only current same-bullet fragments may be reviewed.
Every observed fragment needs a non-revision disposition for approval. Rejection needs no fragment
decisions, but all supplied records must be valid. Accepting an omission is a user attestation,
not proof of safe qualifier removal. See `docs/SOURCE_FRAGMENT_REVIEW.md` for the exact policy.

Strict JSON is limited to 1 MiB UTF-8 and 32 nested collections, with optional BOM. Reject unknown
fields, wrong scalar types/versions, duplicate keys, nonstandard constants and excessive values.
The loader shares the draft reader's bounded checks. API models are revalidated and size-checked;
unchecked `model_copy`/`model_construct` values cannot bypass the boundary.

## Applying decisions (`snapshot-bound-decisions-v3`)

Finding fingerprints must also agree; even unchanged document/plan hashes cannot bypass a changed
finding policy. Fragment fingerprints must also agree. Unknown/cross-bullet acknowledgements,
fragment IDs and invalid draft spans fail without partial approval output.

The engine requires exact-boolean acknowledgements for requirements, selection and decisions.
It rebuilds inspection/planning/matching from the source inputs; it accepts no prior report or
receipt as authority. Current inspection policy, document hash, plan hash and bullet references
must agree before decisions can apply. The original draft still cannot declare itself approved.

Changes to wording, bullet IDs, source models/evidence, preferences, exact job, requirements,
selection or other plan fields invalidate earlier bindings. Review changed snapshots afresh.
Whole-document binding intentionally invalidates all old decisions, even if one bullet alone
changed. Copying current hashes does not bypass plan alignment, eligibility, exclusions or unknown
decision-reference checks. Notes remain outside enforced profile/planning models.

Hash bindings are not signatures, authenticated reviewer identity, proof that a human reviewed
anything, a history database or a semantic support test. A caller can author incorrect attestations;
the software does not certify their truth. Never use a historical receipt as new verified biography.

The immutable result contains the fresh, still-pending `review`, a separate ordered `bullets` list,
`decisions_model_sha256` (validated compact decision JSON), scope and warnings. Each applied record
retains the requested decision/reason and an effective status:

- No decision: `pending_review`, with null decision/reason.
- Reject: `rejected_by_user`; content and references remain visible, including mandatory content.
- Approve with plan conflicts: `blocked_by_plan`, not approved.
- Approve without plan conflicts but with unacknowledged findings, unreviewed fragments or any
  fragment needing revision: `pending_review`.
- Approve without plan conflicts, with every finding acknowledged and every fragment reviewed
  without revision requests: `approved_by_user`, only
  for the current bullet wording snapshot.

Applied records expose `acknowledged_finding_ids` and `unacknowledged_finding_ids`. Missing decisions
acknowledge nothing. They also expose source-ordered `fragment_decisions`,
`unreviewed_fragment_ids` and `revision_fragment_ids`. Observations stay visible in all states.

Result status prioritizes `blocked_by_plan`, then `has_rejections`, then `needs_review` for missing
decisions, unacknowledged findings, unreviewed/revision fragments or a document with no bullets.
Only a nonempty set of wholly
approved bullet records yields `bullet_wording_approved_by_user`. Verbatim wording gets no
automatic decision.

**The result always has `scope: bullet_wording_only` and `rendering_authorized: false`.** Even all
approved bullet wording does not approve education/contact/entry metadata, unscoped sections,
job fit, readability or a final resume. Draft/inspection pending fields stay unchanged; applied
decisions are separate records, not self-approval flags. Plan findings/caveats are never erased.

## Exit codes and privacy

In decision mode, **0** emits a result only when all nonempty bullet wording is approved by the
user under a conflict-free plan; this is not full resume approval. **3** emits a complete pending,
rejected or plan-blocked result. **1** rejects invalid/stale input with no partial JSON; **2** is a
usage/acknowledgement error before input reads. Ordinary inspection without decisions keeps its
existing exit behavior. Diagnostics are static and go to stderr; JSON goes to stdout.

Decision files/reasons and results are private. They can contain sensitive wording, source context,
job text and review rationale; do not commit them or put them in public logs. IDs/hashes are not
anonymization. Contact fields, notes and ineligible source claim text remain excluded from normal
reports. No files are rewritten, no facts promoted, no inference called and no history persisted.

Python API: `apply_review_decisions(profile, job, requirements, selection, draft, decisions,
requirements_reviewed=True, selection_reviewed=True, decisions_confirmed=True)` returns
`ReviewDecisionResult`. `ReviewDecisions`, `parse_review_decisions` and `load_review_decisions` are
exported from `resumeforge.resume`. Safe failures raise `ResumeError` (file reads may raise
`InputError`). Source-bound wording proposals are available separately in 0.12.0; see
`docs/WORDING_ASSISTANCE.md`. They cannot author or carry forward decisions. Source-fragment review
is offline and does not alter the frozen model comparisons or authorize another live run.

Separate `review-metadata` inspection now exposes only explicitly selected source-bound metadata
in pending records; it does not consume these bullet decisions or approve dates/contact/entry
fields. See `docs/METADATA_REVIEW.md`. The v3 bullet decision contract above is unchanged.
