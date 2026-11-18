# Controlled wording assistance — 0.12.0

`suggest-wording` requests one proposed bullet per explicitly selected accomplishment, then
passes the resulting document through current inspection. It is not automatic selection,
verified biography, semantic proof, a complete resume or rendering authorization. Model wording
quality has **not** been evaluated. A valid response can still invent claims or lose qualifiers.

## Workflow and data policy

Supply the same four original source paths as `review-resume` and acknowledge requirements/
selection review. No prior draft, decision receipt or historical bullet text is an evidence input.
The engine revalidates sources and builds a fresh source seed before any wording-provider call.
Conflicted plans return that blocked review (exit 3); an empty plan returns the pending empty seed
(exit 0). Neither calls the wording provider. Required placeholders and findings remain visible.

Fake replay is the default and requires an explicitly authored, snapshot-bound response:

```bash
resumeforge suggest-wording \
  --profile artifacts/private-profile.md --job artifacts/job.md \
  --requirements artifacts/reviewed-requirements.json --selection artifacts/selection.json \
  --mock-response artifacts/wording.response.json --confirm-review
```

**Fake replay does not generate or improve wording.** To author its response, first inspect the
same sources with `review-resume --confirm-review`, then use that seed's hashes and ordered bullet
IDs as described below. Write suggestions deliberately in the separate private response file;
do not treat them as verified facts. The repository sample intentionally has a count conflict.
Resolve preferences/evidence deliberately in a private copy, not by bypassing the conflict or
inventing education evidence. No private file is migrated, rewritten or supplied by this feature.

For optional real local inference, use an already installed, cloud-disabled loopback Ollama and
downloaded local model. There are **two different acknowledgements**, neither approving wording:

```bash
resumeforge suggest-wording \
  --profile artifacts/private-profile.md --job artifacts/job.md \
  --requirements artifacts/reviewed-requirements.json --selection artifacts/selection.json \
  --provider ollama --model qwen3:4b --confirm-review --confirm-local-data
```

`--confirm-local-data` explicitly permits this invocation to send:

- Each selected eligible accomplishment's full statement, bullet/accomplishment IDs and parent
  completion caveats, plus plan and seed-document hashes.
- All reviewed job items with complete text, category, quote and selected lexical associations,
  preserving required/preferred distinctions. The full raw job and company/title fields are not
  separately included (a quote can still contain such details).

No contact fields, Markdown notes, parent metadata, unselected/ineligible statements, skills,
metric metadata or historical bullets/decisions are included. Statements/quotes can themselves
contain identifying information; **this is data minimization, not anonymization**. All selected
statements are in the same batch; instructions prohibit transferring facts across bullets, but
there is no semantic guarantee that a model obeys. Trust your local server/OS and review its logging.

Local mode requires explicit selection and this additional acknowledgement, forbids mock input,
and reuses fixed-loopback, cloud-disabled/local-model, no-proxy/redirect/tool, context/output/
deadline guards. No remote host or cloud provider can be selected. No model is installed, pulled,
started, retried or substituted automatically. Local use has no paid API subscription but consumes
hardware/electricity. No live inference or private-data evaluation was run while implementing this
feature. See `docs/OLLAMA.md`; start with synthetic data if explicitly testing live quality.

## Response contract and control boundary

The strict `WordingResponse` object has exactly:

| Field | Value |
| --- | --- |
| `schema_version` | Strict integer `1`. |
| `plan_sha256` | Current source seed's `document.plan_sha256`. |
| `seed_document_sha256` | Current source seed's `document_sha256`, not an edited document hash. |
| `bullets` | Ordered `{ "bullet_id": "bullet_draft_api", "accomplishment_id": "acc_api", "text": "Proposed wording." }` records for every seeded bullet. IDs/text in this example are fictional. |

No missing/extra/repeated/reordered bullets, detached evidence, changed IDs/hashes, self-approval,
model findings, section/layout fields or unknown keys are accepted. The engine owns the document's
sections, entries, ordering, evidence and pending states. It replaces only validated text, then
freshly recomputes inspection from original sources. Concurrent source changes fail safely rather
than combining old evidence and new proposals. Rejection yields no partial JSON and no retry.

Response JSON uses existing bounded strict parsing: 1 MiB UTF-8, optional BOM, 32 nested collections,
8,192 characters/nonblank bullet text, duplicate-key/nonstandard-constant rejection. The complete
instructions/input/schema request is also limited to 1 MiB; Ollama applies its smaller conservative
context budget before any HTTP call. Findings/draft/planning limits still apply. Never truncate
evidence or drop slots to fit a response budget. Text is inert untrusted data, even if it contains
markup, executable-looking content or instructions; nothing compiles, executes or renders it.

## Result, review and provenance

`WordingResult` identifies `source-bound-wording-v1` and `source-bound-wording-prompt-v1`, has
`status: needs_review` or `blocked_by_plan`, and always `rendering_authorized: false`. `review`
contains the current document, full source context, plan/caveats and literal findings. If no
wording call was made, `attempt` is null; otherwise it records adapter-reported provider/model,
request SHA-256 and raw UTF-8 response SHA-256. Fake metadata means replay, not the model that may
have authored an external fixture. The request hash covers sorted-key compact Unicode-preserving
JSON of the structured instructions/input/schema request. Hashes are not authentication, proof
of review, pinned model weights or semantic support. Raw prompts/responses are not logged/stored.

Save only `result.review.document` privately for further `review-resume --draft` inspection and
separate version-2 human decisions. There is no approval input or automatic decision carry-forward.
Changed wording invalidates old document-bound decisions; identical wording has the same document
identity but does not acquire a new approval. Missing finding acknowledgements remain pending.
Even all acknowledged/user-approved bullet wording cannot authorize rendering or full-resume use.

Exit **0** emits an unapproved result, even with literal findings; **3** emits a blocked plan without
a wording attempt; **1** rejects input/provider/schema/snapshot/budget failure without partial JSON;
**2** rejects usage/acknowledgement combinations before source I/O. Stdout is private JSON;
stderr has safe notices/errors. There is no write-back, history, automatic resume generation or
page/readability check. Keep real profiles/responses/results under ignored private storage.

Python API: `suggest_wording(profile, job, requirements, selection, provider,
requirements_reviewed=True, selection_reviewed=True, provider_data_confirmed=True)` returns
`WordingResult`. `parse_wording_response` and `WordingResponse` are exported from `resumeforge.resume`.
Injected adapters are trusted application code; the CLI constrains them to fake/guarded Ollama.
`ProviderError` messages must be static/safe; unexpected adapter exceptions are sanitized.

Next: explicitly opt-in synthetic wording-quality evaluation before claiming local-model utility.
Semantic proof, metadata/full-resume review, rendering, ranking, history and cloud use remain deferred.
