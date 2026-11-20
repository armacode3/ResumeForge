# Structured component assembly and finite readiness — 0.19.0

`assemble-resume` places the **exact current wording and explicitly selected source metadata**
in one immutable structured document. It reports unresolved content/field/review issues and can
reapply separately confirmed bullet and metadata decisions. It never renders, infers missing
values, edits wording, copies old approvals or grants full-resume/publication approval.

This is a prerequisite to complete resume content, not a complete generation workflow. In
particular, skills/coursework remain unresolved placeholders; there is no full-resume attestation,
required contact-method policy, layout/one-page check, renderer or PDF. A passing finite checklist
is neither semantic/factual proof nor evidence that a resume is sufficient or safe to publish.

## Explicit private inputs

```bash
resumeforge assemble-resume \
  --profile artifacts/private-profile.md \
  --job artifacts/job.md \
  --requirements artifacts/reviewed-requirements.json \
  --selection artifacts/selection.json \
  --draft artifacts/draft.json \
  --metadata-selection artifacts/metadata-fields.json \
  --confirm-review
```

All six paths are required, including the inner current wording `ResumeDocument` and explicit
metadata field selection. The command has no default profile, implicit seed, provider option,
URL fetching or automatic writes. Stdout is private JSON, stderr contains static notices/errors.
`--confirm-review` acknowledges requirements and both selections, not content approval.
The same three exact-true acknowledgements are required in the Python API.

Inspection without decisions works and retains all pending records. To apply actual reviewed
user decisions, additionally supply either or both **independent** pairs:

```text
--bullet-decisions artifacts/bullet-decisions.json --confirm-bullet-decisions
--metadata-decisions artifacts/metadata-decisions.json --confirm-metadata-decisions
```

Each file requires its own confirmation; a flag without its file also fails. There is no combined
`--decisions`/`--confirm-decisions` shorthand or inferred consent across scopes. Usage validation
precedes input I/O, and both decision files are parsed before profile access. The files retain
their existing formats/gates: [bullet v3](REVIEW_DECISIONS.md) and [metadata v1](METADATA_DECISIONS.md).
An inspection, worksheet, prior receipt, assembly or edited metadata copy is never input authority.
Malformed, stale or unselected supplied decisions fail; they are not ignored as if absent.

Assembly freshly reconstructs metadata and wording review from original sources, and uses the
existing decision engines to reapply submitted choices. Recomputed reviews must agree with that
same assembly snapshot. All policy/hash/ref, finding acknowledgement and fragment-disposition gates
remain unchanged. No profile verification or historical receipt substitutes for deliberate review.

## Output-only structured document

`StructuredResume` uses schema version 1 and `assembly_version: structured-resume-assembly-v1`.
It is **not** a new `ResumeDocument` input format and has no loader/editor/approval mechanism.
It binds current `plan_sha256`, `wording_document_sha256`, `metadata_selection_sha256` and
`metadata_document_sha256`. The outer `document_sha256` hashes its validated compact UTF-8 model
JSON, including default pending status. Hashes are snapshot identities, not signatures or proof.

- `header`: only explicitly selected `person.*` source-copy fields, in field-selection order.
- `sections`: exactly the plan's sections/order and `required` flags, including placeholders.
- Entries retain exact plan order/IDs and independent recorded completion status. Their `metadata`
  contains only explicitly selected fields for that same entry, retaining field-selection order.
  Metadata selection/decision order cannot reorder planned entries or bullets.
- `bullets`: unchanged submitted bullet IDs, evidence refs, text, order and pending status. No
  shortening, replacement, dropping rejected content or reuse of historical wording occurs.
- Skills/coursework sections contain no entries or raw profile values. They remain visible
  placeholders, even when included only through required preferences.

No name/title/contact value is copied merely because the readiness policy needs it. Missing
selected scalars/links stay null/empty; dates, `present`, statuses, qualifiers and caveats are
never inferred. Original plan findings, selected source statements and complete reviewed job
context remain visible in the single fresh `review: MetadataReview` envelope.

`AssemblyResult` separately contains `bullet_attestations` and `metadata_attestations` (null if
not submitted). These retain the existing decision version, scope, collective status, validated
decision-model hash, ordered applied records/reasons and warnings, without duplicating the full
review envelope. Bullet finding acknowledgements, unreviewed/revision fragment IDs and user
dispositions remain visible. Underlying metadata/wording records stay pending regardless of
attestations. The structured document/hash does not change merely because decision reasons change.

## Limited version-1 readiness policy

`readiness_version: structured-resume-readiness-v1` is a finite prerequisite checklist, **not a
universal resume completeness standard**. It requires:

1. At least one planned background entry and at least one eligible selected bullet overall.
2. Explicit selection of `person.name` and each planned entry's `title`. These are minimum
   identification fields only; no email, phone, links, organization or date is mandatory in v1.
3. Every selected source value nonempty and separately user-approved through current metadata
   decisions. Unknown values cannot be filled or waived through rationale. Deliberately revise
   optional field selection or correct private sources and review again; never invent facts.
4. Every included bullet has an effective current `approved_by_user` attestation, including all
   existing finding/fragment gates. Missing or rejected decisions stay unresolved.
5. No plan conflict, empty background-section placeholder, required entry added without explicit
   content selection, or entry whose completion state is other than `completed`/`in_progress`.
   Metadata-only entries are allowed when explicitly selected and meeting the field/state gates;
   no educational/accomplishment claim is invented to give them a bullet.
6. No selected/required skills or coursework section: their content/evidence review is not yet
   implemented. Resolve through a future explicit workflow, not implicit omission or bulk approval.

All issues are blocking for this checklist, with stable codes and logical refs (not executable
paths). Order is deterministic: plan conflicts, missing name selection, plan-ordered section/entry
issues, empty overall content, bullet decision issues, then selected-field missing/decision issues.

| Issue codes | Meaning |
| --- | --- |
| `plan_conflict` | Current conflict; `plan_finding_code` links the preserved original finding. |
| `no_entries`, `no_bullets`, `empty_section` | Empty content cannot pass by vacuity. |
| `unscoped_section_unresolved` | Skills/coursework placeholder requires a separate future workflow. |
| `required_entry_not_explicitly_selected` | Required placeholder was added by policy, not explicit content selection. |
| `entry_status_unresolved` | Recorded completion state needs resolution; dates/verification cannot supply it. |
| `required_field_unselected` | A minimum name/title field was not explicitly exposed; its private value is not copied. |
| `selected_field_missing` | Selected source is null/empty, not proof that the real-world fact does not exist. |
| `bullet_decision_pending`, `bullet_decision_rejected`, `bullet_decision_blocked` | Current bullet effective state is not user-approved. |
| `metadata_decision_pending`, `metadata_decision_rejected`, `metadata_decision_blocked` | Current metadata effective state is not user-approved. |

Outer status is `blocked_by_plan` whenever the fresh plan conflicts, otherwise `needs_review` if
any issue remains, otherwise `components_reviewed`. The last means only that these finite gates
passed for these snapshots. All results have `scope: structured_components_only` and
`rendering_authorized: false`. No full-resume approval or factual/qualifier safety follows even if
all user choices approve and all observations were acknowledged. Existing plan review findings
remain visible; no lexical match or count budget proves qualification, support or layout.

## Bounds and privacy

All existing bounded local loaders, strict schema/API revalidation and eligibility/exclusion
checks apply. Default indented **complete** assembly output is capped at 1 MiB with no truncation
or partial JSON. Input decisions/wording/metadata selections retain their existing bounds. Reduce
explicit selections or rationale deliberately if output exceeds the cap; do not silently omit facts.
These are application bounds, not a process-isolation/cryptographic concurrency guarantee.

No extra contact, notes, parent details, unselected/unfinished claims or skills/coursework values
are exposed. Selected wording/job/source/rationale may itself identify people or contain malicious
instructions; treat it as private data, never commands. IDs/hashes are not anonymization. Do not
commit real assembly output/decisions or publish them because a checklist passed. No private-user
review/migration, inference, model setup, new dependency or frozen evaluation is part of this feature.

Exit **0** means `components_reviewed` only; **3** emits the complete unresolved/blocked report;
**1** fails invalid/stale/oversized input/output without partial JSON; **2** is a usage error before I/O.
Python API: `assemble_resume(profile, job, requirements, selection, draft, metadata_selection, *,
bullet_decisions=None, metadata_decisions=None, requirements_reviewed=True, selection_reviewed=True,
metadata_selection_reviewed=True, bullet_decisions_confirmed=False, metadata_decisions_confirmed=False)`.
Set each decision confirmation to exact `True` only when that file was actually reviewed and supplied;
absent decisions require exact `False`. The API and `AssemblyResult`/`StructuredResume` are exported
from `resumeforge.resume`. Safe failures raise `ResumeError`; local file reads can raise `InputError`.

Separate `review-content` now inspects pending explicitly selected skill/coursework names and
user-cited accomplishment contexts; see `SECTION_CONTENT_REVIEW.md`. It is not assembly input and
does not clear the blockers above. Next: a separately confirmed content-decision contract and
deliberate assembly integration, before full-resume/publication attestation or trusted rendering.
