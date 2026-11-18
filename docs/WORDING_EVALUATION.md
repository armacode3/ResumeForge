# Synthetic wording evaluation — 0.13.0

The repository-only `scripts/evaluate_wording.py` runs six fixed fictional cases through the
unchanged `suggest_wording` engine. It evaluates **structural behavior and supports manual
quality review**; it does not assign an automatic factuality, usefulness or resume-readiness score.
No private profile is loaded, no source is promoted and rendering stays unauthorized.

## Frozen corpus and pre-run review protocol

`examples/wording/evaluation/*.json` contains explicit synthetic profiles, local job text,
manually reviewed quoted requirements, deliberate selections and review focus. The six cases
contain seven bullets:

| Case | Source-fidelity risks to inspect |
| --- | --- |
| `supervised_bounds` | Assisted/supervised scope; at least 12, not exactly 12; no service ownership. |
| `negated_prototype` | Local prototype, no production deployment, no measured improvement; no job-derived Kubernetes. |
| `ongoing_parent` | Completed tests for 8 failures versus an in-progress larger project. |
| `cross_evidence` | Keep 5 parser cases/Python separate from 20 synthetic queue tasks/SQLite; no fact transfer or merged slots. |
| `unicode_qualitative` | Contribution/team scope and café context; no invented numeric gains. |
| `untrusted_job` | Ignore an adversarial footer inside a literal quote; no ownership, Kubernetes or self-approval. |

Before a live pass, freeze corpus hashes, response schema, instructions/prompt version, runtime,
model digest and settings. Run one sequential request per case, without prompt tuning, retries,
reference edits or weakening validators based on outcomes. Every selected case stays in totals,
including invalid output, provider failures or unavailable responses. No cherry-picked reruns.

Review **every output bullet against only its cited entire statement**, with the full job and
parent caveat for context. Separately record:

1. Response/schema/ID/hash/order validity (deterministic engine result).
2. Source fidelity: invented numbers/tools/impact/dates/ownership or facts borrowed across slots.
3. Qualifier fidelity: bounds, negation, supervision, prototype and completion limitations.
4. Job-data separation and handling of the untrusted footer.
5. Readability and conciseness: is the text useful as wording, without rewarding omission of
   qualifications or claiming that shorter text is more truthful?

For manual items use `no issue observed`, `issue observed`, `unclear` or `not reviewed`, with a
short source/output explanation. A schema-invalid response may be inspected diagnostically but
cannot become a valid pipeline result. Manual evaluation notes are not user wording decisions,
authenticated review or proof of truth. Unchanged source text may be faithful but not useful
compression; an empty literal finding list may conceal semantic errors. Harmless paraphrases can
trigger caveat findings. Do not score by matching one preferred wording or by counting findings.
This small, software-focused, mostly English corpus is not a representative held-out benchmark.
The single unpaired footer case cannot establish causal effects or general injection resistance.

## Offline modes

```bash
python scripts/evaluate_wording.py
python scripts/evaluate_wording.py --case cross_evidence
python scripts/evaluate_wording.py --responses-dir /private/captured-responses
```

Default `source_seed_replay` constructs snapshot-bound verbatim responses for all slots. It checks
the harness only, **not model wording quality**. `response_replay` loads bounded
`<case>.response.json` files; original author/model provenance is not inferred from replay input.
No installed public command or new dependency is added. The corpus remains repository data,
not candidate evidence bundled into a wheel. Scripts call installed typed modules, so install the
package first; do not use `PYTHONPATH` workarounds.

All corpus cases preflight before any wording call. Invalid/missing cases produce explicit
`case_input_failed` records; the others become `not_run` and no provider is consulted. Repeated
`--case` arguments deduplicate in first-selected order. There is no arbitrary-profile/corpus CLI
input. Missing replay files and invalid responses are failures, not dropped denominators.

## Explicit local pass and capture

Only with separate user authorization and an already prepared runtime:

```bash
python scripts/evaluate_wording.py --provider ollama --confirm-local-data \
  --model qwen3:4b --ollama-port 11435 --timeout 600 \
  --capture-responses-dir /private/new-wording-capture
```

This sends only the fictional selected statements/IDs/caveats and reviewed job items through the
existing guarded local adapter. Local hardware/electricity are consumed; no cloud, tool calls,
runtime installation, downloads or automatic provider/model fallback occur in the runner. Runtime
setup/pulls need separate operator approval. Fake mode rejects local-only flags. Live mode requires
the acknowledgement and forbids response replay. Normal tests/CI use replay or mocks only.

Capture is **optional and explicit**, unlike normal application behavior. Its directory must be
new under an existing parent (mode 700); response files use exclusive creation and mode 600.
Existing directories/files are never overwritten. It captures bounded UTF-8 assistant text even
when JSON is invalid, but never full prompts, thinking or API error bodies. Unencodable/oversized
responses are not persisted. A capture failure invalidates that case rather than claiming success.
Keep captures/reports/runtime files outside Git; no private or raw generated outputs belong in
examples. Hashes are not anonymization or authenticated provenance.

## Report interpretation

`synthetic-wording-v1` reports mode, current wording/prompt versions, requested local settings,
case source hashes, response hashes, provider-call counts and validated pending `WordingResult`
objects. Case statuses are `validated_needs_review`, `validation_failed`, `case_input_failed` and
`not_run`. Adapter/response errors remain static/safe. Result context retains source statements,
snapshot identities, job qualifiers and literal findings; validation failures have no partial
approved document. Response hashes/captures help reproduce failures but do not assert model identity.

`inspected_bullets`, `edited_bullets` and `literal_findings` count **validated results only**; cases
that fail are still in `total_cases`. These counts are observations, not accuracy or usefulness.
`manual_review_status` always remains `not_performed` in machine output; deliberate review belongs
in a separate evaluation note, never automatic application attestations. Rendering is always false.

Exit 0 means all selected responses passed the structural pipeline, **not a quality pass**. Exit 1
retains all selected cases with one or more failures; exit 2 rejects usage/activation/capture setup.
JSON goes to stdout and safe notices/errors to stderr. Default mode writes nothing.

The initial live review, when performed, is documented separately with actual runtime/source
identity, results, limits and next action. Keep the observation policy and prompt unchanged for
that measurement; later improvements need a separate, clearly labeled iteration.
