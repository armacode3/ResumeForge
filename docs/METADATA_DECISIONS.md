# Snapshot-bound metadata field decisions — 0.18.0

`review-metadata --decisions ... --confirm-decisions` applies explicit local user approve/reject
attestations to **selected nonempty source metadata values**, not to bullet wording or a whole
resume. Original sources, the exact wording draft and explicit field selection are still required.
Every application freshly reconstructs metadata/wording inspection; an old report, edited metadata
copy or approval receipt is never authority. There is no inference, write-back or rendering.

These are unsigned user assertions, not authenticated identity, proof of truth/contact accuracy,
semantic support, safe publication or profile fact promotion. Review original profile context,
including date qualifiers and details/notes the finite inspector does not interpret. Do not bulk-
approve merely because values match source strings or schemas pass.

## Private workflow

1. Run `review-metadata` without decisions as in `docs/METADATA_REVIEW.md`. Inspect the selected
   source copies, missing-value findings, dates/completion contexts and original wording/plan.
2. Author a separate private metadata decision file with the **current** bindings below. For each
   field actually reviewed, choose `approve` or `reject` and supply a nonblank reason. Omit records
   for unreviewed fields; they stay pending. No helper preselects choices or copies old approvals.
3. Apply the decisions with separate confirmation:

```bash
resumeforge review-metadata \
  --profile artifacts/private-profile.md \
  --job artifacts/job.md \
  --requirements artifacts/reviewed-requirements.json \
  --selection artifacts/selection.json \
  --draft artifacts/draft.json \
  --metadata-selection artifacts/metadata-fields.json \
  --decisions artifacts/metadata-decisions.json \
  --confirm-review --confirm-decisions
```

These are private local inputs you must author/review. The command writes nothing automatically.
`--confirm-review` still acknowledges requirements and both selections, not approval.
`--confirm-decisions` separately asserts review of the submitted metadata choices. A decision file
without this flag, the flag without a file, missing source acknowledgement or required paths are
usage errors before input reads. Metadata and bullet decision files are **different formats**;
neither can stand in for the other, nor can inspection/decision-result envelopes.

## Version-1 decision contract

The root has exactly these fields (hashes come from an ordinary metadata inspection):

| Field | Required value/source |
| --- | --- |
| `schema_version` | Strict integer `1`. |
| `decision_version` | `metadata-field-decisions-v1`. |
| `metadata_version` | Current `source-bound-metadata-v1`, matching `inspection.document.metadata_version`. |
| `plan_sha256` | `inspection.document.plan_sha256`. |
| `wording_document_sha256` | `inspection.document.wording_document_sha256`. |
| `metadata_selection_sha256` | `inspection.document.metadata_selection_sha256`. |
| `metadata_document_sha256` | `inspection.document_sha256`, not a file hash. |
| `fields` | Distinct `{source_ref, decision, reason}` records; may be empty or partial. |

A fictional individual record's shape is:

```json
{"source_ref": "person.name", "decision": "approve", "reason": "Reviewed this exact recorded name."}
```

This is a format example, not approval of real content. Use actual refs from the current selected
metadata fields; refs are opaque exact logical model references, not paths to execute. Unknown,
unselected or duplicate/conflicting refs fail without partial results, even for rejections.
`decision` is exactly `approve` or `reject`; either requires a nonblank reason of at most 8,192
characters. No replacement `value`, approval scope, metadata text or self-declared status is
accepted. `person.links` refers to the entire selected tuple of recorded model-normalized URLs;
there is no individual-URL decision or live link/identity validation.

The strict JSON loader retains existing 1 MiB UTF-8/32-level bounds, optional BOM, duplicate-key,
nonstandard-number, scalar-type and unknown-field rejection. At most 512 decision records are
allowed, independently of source selection limits. API models are revalidated and byte-checked;
unchecked `model_copy`/`model_construct` values cannot bypass the application boundary.

## Effective states and missing values

The engine requires all four exact-boolean confirmations: reviewed requirements, content selection,
metadata selection and submitted decisions. It recomputes `MetadataReview` and checks decision/
metadata policy, every explicit snapshot binding and field membership before applying anything.

Each applied field retains `source_ref`, requested `decision`/`reason` (null if absent),
`source_value_missing` and an effective `review_status`:

- Missing decision: `pending_review`, even when the source is copied verbatim.
- Reject: `rejected_by_user`; the value/context is retained, not removed from the document.
- Approve with a plan conflict: `blocked_by_plan`.
- Approve with a null value or empty link tuple: `pending_review`. **Unknown source values cannot
  be approved, filled or waived through reasons.** Missing findings remain visible.
- Approve a nonempty value without plan conflicts: `approved_by_user` for this exact source snapshot.

Field output follows source-document order, not input decision order. Collective status prioritizes
`blocked_by_plan`, then `has_rejections`, then `needs_review` for any pending field or no selected
fields. Only a nonempty wholly approved selected set yields `metadata_fields_approved_by_user`.
An individual rejection remains visible even when plan conflicts dominate collective status.

If an optional field is genuinely unset and should not be published, deliberately revise the field
selection rather than invent a value or an approval. If a source value is wrong, correct the private
profile and seed/review a new wording draft. Both changes require fresh metadata review/decisions;
they do not transfer approvals. Separate `assemble-resume` now checks limited name/title and
component prerequisites; see `docs/STRUCTURED_ASSEMBLY.md`. It is not a full-resume completeness
policy or publication authorization, and does not change metadata decision semantics.

`MetadataDecisionResult` contains `decision_version`, `scope: selected_metadata_only`,
`rendering_authorized: false`, status, `decisions_model_sha256` (validated compact input JSON),
the fresh `review`, ordered applied `fields` and warnings. The underlying metadata and wording
records **stay pending**; user attestations are separate records. Findings, completion contexts,
selected source copies, job context and plan conflicts stay visible. A user-approved metadata set
does not clear wording findings or attest to unselected metadata, skills/coursework or a final resume.

## Snapshot and privacy limits

Whole-document bindings conservatively invalidate old metadata attestations after changes to
source models, entry completion context, dates, job/requirements, preferences, content/metadata
selection or exact wording. Current metadata-inspection and metadata-decision policies must also
agree. Raw Markdown notes remain outside model hashes/enforced planning; no semantic interpretation
of those notes is claimed. Copying current hashes cannot authorize refs no longer selected, but
software cannot prove human attention or prevent someone authoring false unsigned attestations.
Never mechanically update hashes to carry old approvals forward.

Default indented result serialization is capped at 1 MiB, without partial JSON/truncation. If the
combined review/reasons exceed that limit, shorten rationale or deliberately reduce/review the
selection. Metadata contact values, sources, reasons and hashes remain private, not anonymized.
Do not commit actual decisions/results or log their contents by default.

Decision mode exits **0** only for wholly user-approved nonempty selected metadata, **3** for
pending/rejected/plan-blocked results, **1** for invalid/stale/oversized input/output without JSON,
and **2** for invalid usage/confirmations before I/O. Ordinary metadata inspection keeps its prior
exit behavior. No exit code approves a complete resume, proves truth or authorizes rendering.

Python API: `apply_metadata_decisions(profile, job, requirements, selection, draft,
metadata_selection, decisions, requirements_reviewed=True, selection_reviewed=True,
metadata_selection_reviewed=True, decisions_confirmed=True)` returns `MetadataDecisionResult`.
It, `MetadataDecisions`, `parse_metadata_decisions` and `load_metadata_decisions` are exported from
`resumeforge.resume`. Safe failures raise `ResumeError` (file reads can raise `InputError`).
Existing metadata source-copy schema/policy v1, bullet inspection/decision v3, profiles/drafts/
responses, worksheets, provider payloads and frozen evaluations remain unchanged. No migration,
private-user approval, live evaluation, new dependency, history or cloud inference was performed.
