# Concise wording objective — frozen comparison protocol, 0.14.0

This is a separate iteration after the original six-case pass copied seven short statements.
The original corpus, pre-run protocol and result note are unchanged. The default objective remains
`source_faithful` with the original v1 instructions/request bytes. A new opt-in `concise_rewrite`
objective uses wording/prompt v2; it does not replace the default or relax any validator.

## Objective and invariants

The v2 prompt asks for readable wording by combining redundant clauses and removing repeated setup
or first-person narration, **not by dropping distinct facts or qualifiers**. It retains tools,
quantities/units/bounds, attribution, explicit negative scope and completion limitations. There is
no target word count, forced edit or shorter-is-better score. Copying the whole statement remains
the fallback for uncertain or already concise text. No previous model output is source evidence.

Both objectives use the same minimized data, response schema, exact plan/seed bindings and ordered
slots. Only trusted instructions differ. Every proposal goes through fresh inspection and stays
pending, including verbatim copies. Unknown objectives fail before source/provider use. Existing
finding acknowledgements, user decisions, plan conflicts and rendering prohibition are unchanged.
`WordingResult.objective` labels the requested objective, not the provenance of a replay fixture.

## Development versus evaluation

Two new fixed suites are separate from the original baseline:

| Suite | Cases | Use |
| --- | --- | --- |
| `rewrite_development` | `dev_supervision`, `dev_prototype`, `dev_team` (3 bullets) | Offline pipeline/examples only; not included in live outcome totals. |
| `rewrite_holdout` | `eval_bound_tests`, `eval_components`, `eval_survey` (4 bullets) | Frozen comparison data; no model output is seen before candidate prompt freeze. |

The candidate prompt was specified before authoring the evaluation fixtures. These are agent-
authored, deliberately redundant fictional statements, not a representative or independently
curated held-out benchmark. They are held out from **output-driven prompt tuning**, not hidden from
the coding agent. No gold preferred wording is used or fed to the model. Review-focus annotations
are outside the provider payload. Do not reuse the evaluation outputs as tuning examples here.

## Predeclared comparison

With explicit user opt-in, reuse the cached Qwen3:4b/runtime without downloads. Freeze candidate
and legacy instructions, schema, both suites/corpus hashes, source/inspection code, model digest,
runtime/settings and expected request hashes before inference. Run `source_faithful` once for all
three evaluation cases, then `concise_rewrite` once for the same cases in the same order: **six
calls total**. No live development-case calls, correction, retries, tuning, validator changes or
replacement runs after outputs. Missing/failed cases stay in their three-case denominator.

Use the original guarded local adapter: cloud-disabled literal loopback, local-model checks,
16,384 context / 4,096 output, temperature/seed 0, non-thinking/no-tools, unload per call, up to
600 seconds per case. This fixed order is not randomized or a repeated/counterbalanced experiment;
timing is descriptive only. A single deterministic-settings pair is not repeatability evidence.

Review every bullet against its entire cited statement, never another slot or job preference:

| Case | Material facts/qualifiers that must survive |
| --- | --- |
| `eval_bound_tests` | Assistance, Python, **at least 18** internal validators, valid and malformed requests, mentor review, completed testing but no service ownership, no measured performance gain. |
| `eval_components`, importer | Local Python prototype, **6** importer error cases, never deployed, no SQLite, no measured speed improvement. |
| `eval_components`, queue | Completed SQLite retry checks for **30 synthetic tasks**, not the whole in-progress project, no importer implementation and no Python. |
| `eval_survey` | Contribution/team scope, Python missing-value checks, café survey/bilingual team, explicit non-leadership, no measured numeric improvement/impact. |

Record structural/schema/hash/order validity separately from source fidelity, qualifier retention,
cross-evidence/job-data transfer, readability and conciseness. Use `no issue observed`, `issue
observed`, `unclear` or `not reviewed`, with reasons. Inspect invalid text diagnostically only;
never treat it as an accepted document. Coding-agent review is fallible and is **not** a human
wording attestation or semantic proof. Literal cue alarms can be harmless paraphrases; empty
findings can conceal changed meaning. All approval/rendering fields remain untouched.

Count edits and source/draft Unicode characters as descriptive observations **only for validated
results**. Compare paired cases with denominators visible; a failure or omitted claim must not
look like successful compression. No automatic usefulness/faithfulness score or pass threshold.
No shorter document is approved merely because a length count decreased.

## Commands and reproducibility

Offline replay is still the default and does not generate wording:

```bash
python scripts/evaluate_wording.py
python scripts/evaluate_wording.py --suite rewrite_development --objective concise_rewrite
python scripts/evaluate_wording.py --suite rewrite_holdout --objective concise_rewrite
```

Each source-seed replay copies full statements even under v2. A live comparison uses two separate
invocations only after explicit authorization, with new capture directories for each objective:

```bash
python scripts/evaluate_wording.py --suite rewrite_holdout --objective source_faithful \
  --provider ollama --confirm-local-data --ollama-port 11435 --timeout 600 \
  --capture-responses-dir /private/new-baseline-capture
python scripts/evaluate_wording.py --suite rewrite_holdout --objective concise_rewrite \
  --provider ollama --confirm-local-data --ollama-port 11435 --timeout 600 \
  --capture-responses-dir /private/new-candidate-capture
```

Live inference is never a side effect of tests, replay, credentials or generic continuation.
Raw captures/runtime/reports stay outside Git and exclusive capture never overwrites data. Replay
each capture offline with its matching suite/objective and verify source/request/response hashes
and inspections without more inference. Published outcomes belong in a separate note; do not edit
this frozen protocol or the original baseline measurement to suit the results.

The application command also accepts `suggest-wording --objective concise_rewrite` with the same
source/review/provider gates. Fake remains default. An opt-in objective is a request, not a quality
guarantee; absent measured benefit, retain deterministic source seeding rather than forcing edits.
