# Qwen3:4b rough-source objective comparison — 2026-11-18

## Outcome and decision

Both objectives produced **3/3 structurally valid responses** on the same three new evaluation
cases, containing four bullets per objective. `source_faithful` copied all four statements.
`concise_rewrite` edited all four, reducing text from **1,262 to 633 Unicode characters**, but
introduced source-fidelity problems, including a changed project relationship and broadened
negative claims. **Shortening was demonstrated; reliable faithful rewriting was not.**

Keep `source_faithful` as the original default and deterministic source seeding as the baseline.
The new objective remains explicit and experimental, not suitable for unattended generation.
No document was approved, corrected, rendered or promoted to verified facts. All eight output
bullets remain pending. This source-by-source coding-agent review is fallible and is not an
independent human wording/factual attestation or a semantic correctness guarantee.

## Frozen design and execution

- The user separately approved this six-call comparison on fictional data, reusing the cached
  runtime/model with no downloads. No private profile, notes or historical wording was loaded.
- The candidate prompt was fixed before authoring the new evaluation fixtures. Three development
  fixtures were exercised offline only. Three evaluation cases/four bullets were held out from
  output-driven tuning. These agent-authored cases are not independently curated, representative
  or hidden from the coding agent; no broad held-out accuracy claim is made.
- Original corpus, protocol and [original live result](qwen3-4b-wording-v1.md) are untouched.
  Regression tests preserve the six original v1 request hashes. Both objectives used the same
  minimized payloads, response schema, source/seed bindings, slots and validators; only trusted
  instructions differed. Neither condition used gold wording or review-focus annotations as input.
- Order: one `source_faithful` pass across all three evaluation cases, then one `concise_rewrite`
  pass in the same case order. Six requests total; no development-case inference, retries,
  prompt tuning, changed validators, response repair or replacement runs.
- Cached Ollama **0.40.16**, **qwen3:4b** digest
  `359d7dd4bcdab3d86b87d73ac27966f4dbb9f5efdfcc75d34a8764a09474fae7`.
  Temporary server: `127.0.0.1:11435`, cloud disabled/local GGUF completion metadata checked,
  no proxy/redirect/tools/fallback. It was stopped after comparison and offline replay.
- Context/output **16,384 / 4,096**, temperature/seed 0, non-thinking/non-streaming, unload after
  each call, 600-second client budget per case. Started **2026-11-18 17:25:20 UTC**; observed
  elapsed times **221.75 seconds** (v1), **205.00 seconds** (v2), **426.75 seconds** total. These
  include cold loads and concurrent development checks; not a speed benchmark or causal estimate.
- Frozen protocol: `docs/WORDING_REWRITE_EVALUATION.md`, SHA-256
  `dcaf4d3936ee598f8c89bdf2b86076170e90c9f3c89aed32f359dc110e45a604`.
  v1 instructions SHA-256:
  `083d944093809247a98467f0d546df6d76fedb600f2fa6efec503c443df7ce02`.
  v2 instructions SHA-256:
  `ef00943c8dce38ba826d1b1209e336a2c33c0362314be354b0d5d111fe4bc0a7`.
  Unchanged canonical response-schema SHA-256:
  `e22ffb5e1de5fdf44ada3ee709f2dfdd0fd797972f570db72090011c2ff1d6b7`.

Complete frozen manifest, captures and live/replay reports remain outside Git at
`/tmp/opencode/resumeforge-wording-rewrite.9k8xtH/`; temporary storage may expire. Manifest SHA-256:
`5d7a2e523d672274d1fb414742c415e03c2583ffb8c52cead62daa70b2a9396f`.
No raw generated responses, prompts, thinking or runtime/model data are committed.

## Paired source-by-source review

Schema/hash/reference/order validation passed for every row under both objectives. V1 preserved
all source text and qualifiers but supplied no rewriting benefit. V2 removed repeated narration
and reduced length; the following issues prevent treating that as a successful quality result.
Counts are descriptive, not an automated or human-approved factuality score.

| Evaluation bullet | Source / v1 characters | V2 characters | V2 source/qualifier review |
| --- | ---: | ---: | --- |
| `eval_bound_tests` | 381 | 176 | **Issue observed:** retained assistance, Python, at least 18, mentor review and both request types. However, “no performance improvement was measured” became “without ... performance improvements,” turning an absence of measurement into a stronger negative result. Explicit completed-test wording also disappeared; no ownership claim was added. |
| `eval_components`: importer | 275 | 152 | **Qualifier issue observed:** retained local Python prototype, 6 error cases, no SQLite and no measured speed improvement. “Never deployed **to production**” became “never deployed,” omitting the production-only limit and potentially broadening the negative claim. Zero literal findings did not establish equivalence. |
| `eval_components`: queue | 273 | 141 | **Clear relationship error observed:** completed checks were **part of** the larger project, not completion of the whole project. V2 instead said the work “was not part of the larger queue project.” It also dropped explicit in-progress wording and the no-Python caveat. SQLite, 30 synthetic tasks and no importer implementation survived. Parent status remained visible in inspection but did not repair the wrong wording. |
| `eval_survey` | 333 | 164 | **Unclear/broadened scope; needs review:** retained contribution, Python missing-value checks, café/bilingual-team context and no numeric improvement measured. “Did not lead the study” became broader “no leadership role”; “no measured numeric impact” became “no measurable impact reported,” dropping numeric/measurement qualifications. No invented positive metric was observed, but equivalence is not established. |

Across the four candidate bullets, the review did not observe a newly invented positive numeric
gain or job-preferred technology/ownership claim. That limited observation does **not** excuse
negative-scope distortion, omissions or altered relationships, nor certify source fidelity.

The three existing literal findings were missing-cue observations: `not` in the validation and
survey bullets, and `in progress` in the queue bullet. They were not semantic verdicts. Replacing
`not` with `without` can be harmless in isolation; retaining `never` can still broaden its scope.
The importer had no finding despite the lost production qualifier. The queue's substantive
relationship error and dropped no-Python clause were not classified by those finite checks.
All edits still require human review, even with zero findings or every finding acknowledged.

## Reproduction identity

Frozen corpus, instructions/schema/protocol and expected request hashes were checked unchanged
after the run. Offline replay with each matching suite/objective reproduced all six inspections
and source/request/response hashes, without another inference call. Replay metadata identifies
fake replay, not a new Qwen run or authenticated original author.

| Case | Corpus-file SHA-256 |
| --- | --- |
| `eval_bound_tests` | `42981befb40ce64beeb62d02bf10baa2982471630e80b5ee224629c65975c55c` |
| `eval_components` | `47694e430653d9e43459028362de0914ba4e7a43c1ebe0e1f4b87e21aa6b2feb` |
| `eval_survey` | `161d4279ef9c49792baf1b963df86ef8f78290e6c0691bd0bca630ea02d8682f` |

| Case | V1 raw assistant-response SHA-256 | V2 raw assistant-response SHA-256 |
| --- | --- | --- |
| `eval_bound_tests` | `20ea1c404e0a869831396ea2f6a1f16b4864e35e510ad7f54b773256df333bf3` | `135587035e6773552e6594773e31d627d081d86b8d932a6d4dc856b0bc7f4a2c` |
| `eval_components` | `c3d0be1f4edbbcf53ac57ad44309009e52466a8d862c1a81305b497e35afe05c` | `53835dc10daa638ae5153c81d32a902687fd201cfdf8746e28430bf8d0bf4c07` |
| `eval_survey` | `eb7dd195914cab8bb224e4401f084b6fa8cdafa65f3459a547fb2221f15c6683` | `330922e7527c73c34f08d78f07242f5ed6718042d21591ca8853138bf280e815` |

Hashes bind this observation; they are not anonymity, identity authentication or proof of truth.
No response failed structural validation in this pass. Failure retention remains a separately
tested invariant, not an observed live failure or omitted denominator.

## Limits and next action

One fixed-order pair on three software/research cases cannot estimate general accuracy,
repeatability, domain/language coverage, causal prompt effects or injection resistance. The
fixtures deliberately repeat facts and negative clauses and may overrepresent this failure mode.
V2 remains opt-in; do not promote it to the default, auto-approve it, weaken checks or rerun until
green. The original frozen measurement is not replaced by this comparison.

The next small slice should make **source-fragment omissions and qualifier review explicit**,
with source/draft-bound observations and deliberate user review, rather than treating character
reduction or an LLM judge as semantic proof. Preserve copy fallback and the conservative default.
Metadata/full-resume approval, rendering, automatic ranking, history and cloud inference remain
outside scope. No further live comparison is authorized implicitly by these results.
