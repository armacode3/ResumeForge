# Source-bound pending metadata — 0.17.0

`review-metadata` makes explicitly chosen contact and background-entry fields visible beside a
fresh wording review. Inspection **copies profile-model values into pending records**; it does not
edit/approve metadata, verify identity/dates, assemble a complete resume or authorize rendering.
Separate explicitly confirmed user field attestations are now available; see
`docs/METADATA_DECISIONS.md`. Bullet wording decisions do not substantiate metadata.

The command is offline, read-only and separate from ordinary wording review. Contact values are
not added to ordinary reviews, worksheets, prompts or provider requests. No URL is fetched, model
called, old approval imported or private source migrated.
The retained wording/job context can itself contain identifying strings. Field selection is data
minimization, not anonymization; inspect the original profile as well as chosen values. Details/
notes may contain caveats this slice does not interpret or copy. Pending metadata is not safe-to-
publish content merely because its source value was copied.

## Explicit field selection and use

Use the same four original inputs as wording review, an explicit current inner `ResumeDocument`,
and a separate field-selection JSON file. A version-1 selection has exactly:

```json
{
  "schema_version": 1,
  "person_fields": ["name", "email"],
  "entries": [
    {"entry_id": "exp_example", "fields": ["title", "organization", "start_date", "end_date"]}
  ]
}
```

The ID/example is fictional. Choose real fields deliberately in private storage, not by copying
every available field. Both `person_fields` and `entries` are required and may be empty. A chosen
entry requires one or more distinct fields; duplicate person fields, entry IDs or entry fields
fail rather than being merged. The complete whitelist is:

- Person: `name`, `email`, `phone`, `location`, `links`. Nothing is selected implicitly, including
  name. Selecting `links` exposes **all recorded links**, not a selected link or inferred homepage.
- Entry: `title`, `organization`, `location`, `start_date`, `end_date`. The entry must already be in
  the fresh non-excluded content plan, including deliberately required metadata-only placeholders.
  All eight background categories are supported. Unknown/unselected/excluded entries fail closed.
- No `details`, technologies, skills, coursework, notes, accomplishment text/metrics or historical
  bullet fields are selectable here. Skills/coursework need a separate content/evidence boundary.

Fields on metadata-only/status-review entries can be inspected, but remain pending; this does not
make their accomplishments eligible. The original plan's required placeholders, caveats and
conflicts remain visible. Metadata selection cannot add an entry to the content plan or bypass an
exclusion. Change the reviewed content selection explicitly if different entries are needed.

```bash
resumeforge review-metadata \
  --profile artifacts/private-profile.md \
  --job artifacts/job.md \
  --requirements artifacts/reviewed-requirements.json \
  --selection artifacts/selection.json \
  --draft artifacts/draft.json \
  --metadata-selection artifacts/metadata-fields.json \
  --confirm-review
```

These are private files you must create/review. `--confirm-review` acknowledges the reviewed job,
content selection and intended field exposure, **not metadata or wording approval**. All paths and
confirmation are required before input I/O. There is no provider option, implicit source
seed, default private profile or automatic file write. Optional `--decisions` additionally requires
separate `--confirm-decisions`; ordinary inspection without these options is unchanged. Stdout is
private JSON; explicitly redirect
it to a new private file if needed. Redirection can overwrite files and is not performed by the app.

`examples/metadata/backend_intern.fields.json` is a fictional selection for the shared sample. To
try it, first seed/save the sample's inner wording document using `review-resume`, then pass that
explicit draft and original sample sources. The sample deliberately has a count conflict: exit 3
preserves it, not a generation failure to conceal or a reason to invent evidence.

## Source semantics and report

Values are copied from a freshly validated **profile model**, not raw Markdown/YAML slices.
Strings retain their model value; links use the existing `HttpUrl` model's string normalization
(such as host casing or a trailing slash). No further URL validation/fetching or metadata rewriting
is performed. Correct disputed values in the private profile, leave uncertain dates unset, then
seed/review a new wording draft. Profile changes invalidate the existing plan/draft bindings.

- Unset scalar values stay `null`; an empty link list stays `[]`. Each produces a
  `missing_source_value` finding. Missing is not proof that a fact/contact method does not exist.
- Month precision and literal `present` are preserved. `present` is copied only when recorded,
  never inferred from missing end dates, current time, parent/child state, verification or notes.
- Each chosen entry's recorded `completion_status` is preserved separately in `entry_contexts`,
  even when dates are unknown. A status does not resolve conflicting dates or approve metadata.
- Every selected field has `review_status: pending_review`. Empty selections remain pending and
  are not complete resumes or implicit approval. No required header/content-completeness policy
  exists yet. Separate version-1 metadata decisions can attest only to selected nonempty values;
  see `docs/METADATA_DECISIONS.md`. They do not change the pending source records.

`MetadataReview` contains `scope: selected_metadata_only`, `rendering_authorized: false`, status,
`document_sha256`, the pending `document`, missing-value `findings`, full fresh `wording_review`
and warnings. The wording review retains all job/plan/source context and pending states; no old
bullet decisions are applied or transferred.

The inner `MetadataDocument` has schema 1, `metadata_version: source-bound-metadata-v1`, current
`plan_sha256`, `wording_document_sha256`, `metadata_selection_sha256`, ordered `fields` and chosen
`entry_contexts`. A field is `{source_ref, value, review_status}`. Logical refs are `person.email`
or `experiences.exp_example.title`: these identify validated model fields/IDs, **not executable
path expressions, JSON-array pointers or raw-source offsets**. Values are strings, null, or a
tuple/JSON array for links. Person fields come first in explicit selection order, followed by
entry fields in their explicit entry/field order; this is not relevance ranking or a layout plan.

The selection hash covers validated compact Pydantic JSON (including order), not file whitespace
or a file hash. The document hash covers its compact Pydantic JSON, including policy, bindings,
values, contexts and default pending states; both use UTF-8. Hashes bind observations, not
authenticated identity, anonymity, factual truth or proof of review. A changed field selection or
wording snapshot produces a new metadata identity. Metadata output is not accepted as wording
draft/decision input and is never used as an authoritative source for new facts.

## Limits, errors and compatibility

Selections use strict bounded JSON: 1 MiB UTF-8, optional BOM, 32 nested collections, exact scalar
types/versions, duplicate-key/nonstandard-constant rejection and whitelisted fields. API models
are revalidated; profile values are copied from a private snapshot used for fresh inspection.
At most 512 metadata field records are allowed (one `links` field can contain multiple links),
each non-null string at most 8,192 characters. Complete default indented report serialization,
including wording context, is capped at 1 MiB. Excess fails without truncation or partial JSON.

Exit **0** emits a pending report without plan conflicts, including unset fields; **3** emits the
complete plan-blocked report; **1** rejects invalid/stale/unselected/oversized input/output without
partial JSON; **2** rejects usage/confirmation failures before source reads. Errors/notices are
static on stderr. There is no semantic approval or one-page/readability verdict in any exit code.

Existing profile/draft/wording-response schema 1, inspection/decision v3, worksheets, prompts,
provider minimization, observations and frozen comparisons are unchanged. No dependency, live run,
cloud activation, history, renderer or migration is added. Reports now intentionally expose the
selected contact/entry values: never commit real reports, profiles, IDs/hashes or stdout logs.

Python API: `review_metadata(profile, job, requirements, selection, draft, metadata_selection,
requirements_reviewed=True, selection_reviewed=True, metadata_selection_reviewed=True)` returns
`MetadataReview`. All three flags require exact true; no supplied report/receipt grants authority.
`MetadataSelection`, `MetadataDocument`, `MetadataReview`, `parse_metadata_selection` and
`load_metadata_selection` are exported from `resumeforge.resume`. Safe failures raise `ResumeError`
(file reads can raise `InputError`). Narrow per-field metadata attestations are available separately;
full-resume assembly/readiness and rendering authorization remain unimplemented.
