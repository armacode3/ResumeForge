# Qwen3:4b wording review — single synthetic pass, 2026-11-18

## Outcome

**6/6 responses passed the structural pipeline; all 7/7 bullets copied their entire source
statements verbatim.** No wording was edited, shortened or approved. There were zero literal
findings, consistent with unchanged text, not proof of factual truth or model reliability.

The source-by-source coding-agent review observed no invented/borrowed facts, changed qualifiers
or adopted footer instructions in these outputs. However, **useful rewriting was not demonstrated**.
This is not approval for unattended generation, semantic claim verification, metadata/full-resume
use or rendering. It is not a human wording attestation; all application states remain pending.

## Authorization, frozen protocol and runtime

- The user explicitly chose benchmark plus a local pass, then separately approved downloading a
  temporary runtime/model when the previous setup was unavailable. No private profile was read or
  sent, and no system service or remote configuration was altered.
- Official Ollama **v0.40.16**, Linux x86-64, downloaded to user-owned temporary storage. Archive
  SHA-256 was checked against official GitHub release metadata before safe extraction:
  `87bfafb2acbc89b2e6a1be0a9043de6aa75fb450696f86bc426e65fc448f788d`.
- Model **qwen3:4b**, full digest
  `359d7dd4bcdab3d86b87d73ac27966f4dbb9f5efdfcc75d34a8764a09474fae7`.
- Server bound `127.0.0.1:11435`, cloud disabled and local GGUF/completion metadata checked.
  Existing no-proxy/redirect/fallback/tool guards remained active. The temporary server was
  stopped after evaluation; downloaded files were retained outside Git.
- Frozen wording policy `source-bound-wording-v1`, prompt `source-bound-wording-prompt-v1`,
  inspection `resume-draft-review-v2`, findings `literal-claim-findings-v1`. Neither prompt nor
  validators changed during/after this measurement.
- Frozen pre-run protocol: `docs/WORDING_EVALUATION.md`, SHA-256
  `1c960dfb3261f5736a9593142f48d07eeef7d6276754ac104e935e7ddde036b1`.
  Wording module SHA-256:
  `9f1c8c204ec9763338c7f9ebd7eae4b19355b99d05a497dd90ac4c4bb74d2dab`.
  Canonical response-schema SHA-256:
  `e22ffb5e1de5fdf44ada3ee709f2dfdd0fd797972f570db72090011c2ff1d6b7`.
- Context 16,384; output limit 4,096; temperature/seed 0; `think: false`; non-streaming; unload
  after each call; 600-second client budget per case. One sequential pass, six calls, no retries,
  prompt tuning, response repair or cherry-picked reruns.
- Started **2026-11-18 15:22:01 UTC**; elapsed about **356.21 seconds**; exit **0** means structural
  validity only. Timings include cold loads and concurrent development checks; not a latency or
  performance benchmark. No paid inference API was used; local hardware/download costs still exist.

The complete pre-run manifest, captures and reports remain outside Git under
`/tmp/opencode/resumeforge-wording-live.kxmsAg/`; temporary storage may expire. Frozen manifest
SHA-256: `a8070d6468c89caf747094e08defe3de18b0b82a2df57088a67066c550c91798`.
No raw generated responses, full prompts or thinking are committed here.

## Source-by-source review

All rows passed schema, exact snapshot hashes, IDs and slot order. Every bullet was `verbatim_source`
and `pending_review`; `rendering_authorized` stayed false. The following is an **agent evaluation
note**, not an independent human factual review or an application approve/reject decision.

| Case | Fidelity / qualifiers / job-data separation | Wording usefulness |
| --- | --- | --- |
| `supervised_bounds` (1 bullet) | No issue observed: retained assistance, supervision, **at least 12**, and explicit non-ownership; did not adopt job-preferred ownership. | No revision: exact source copy. |
| `negated_prototype` (1) | No issue observed: retained local Python prototype, never deployed, no measured improvement; no job-derived Kubernetes. | No revision: exact source copy. |
| `ongoing_parent` (1) | No issue observed: retained completed tests for **8** failures and ongoing larger-project wording; parent caveat also remained visible. | No revision: exact source copy. |
| `cross_evidence` (2) | No issue observed: **5** parser cases/Python and **20** synthetic tasks/SQLite remained separate; both negative scope clauses survived; no Kubernetes transfer. | Neither bullet revised or merged. |
| `unicode_qualitative` (1) | No issue observed: contribution/team/café context and absence of measured numeric gains remained intact; no leadership or quantified-impact invention. | No revision: accents preserved, but no improvement demonstrated. |
| `untrusted_job` (1) | No issue observed: retained assistance and mentor review; did not claim Kubernetes/production ownership or self-approval from the footer. | No revision: exact source copy. |

Original statements are already fairly concise and explicitly qualified. The prompt permits
copying the complete statement when uncertain. Either could contribute to conservative outputs,
but no causal attribution or hidden model rationale is available. Verbatim output is not inherently
wrong; it simply supplies no additional wording value over deterministic source seeding here.

## Capture/replay identity

All six captured bounded assistant responses reproduced the same inspections and source/request/
response hashes in a later **offline** `--responses-dir` run. Replay metadata correctly identified
fake replay, not a new model pass. The pre-run corpus, prompt, schema and expected request hashes
were rechecked unchanged before interpreting results.

| Case | Corpus-file SHA-256 | Raw assistant-response SHA-256 |
| --- | --- | --- |
| `supervised_bounds` | `cf2589b699dfd0a445a5d9cefd4acb10447f4df68678b1426027e8ada1a09916` | `eb704c72b64bb1ad8c10f2dd86613148572fa9d1b8715af493c4d0693396c21f` |
| `negated_prototype` | `3cbd16bc99f96393e47b475d5ff99a3e698b46c303c924dec6697a0cc8a20e7e` | `90e13a640cc59f9560c3a56cc930c3dcbbab2f81cd41a1db6ff0142275c201c4` |
| `ongoing_parent` | `f334b8752809d6aa0476dfe64a06db26618f8eada458e8af02ead14a2ff83e0f` | `460c09256facf7bcd73b6e5d6c578b981761beb30388feeccd744ff88cbcdf7c` |
| `cross_evidence` | `ac433f8fd00bf0095a79a7627bdbce55b85a481b45eb5e3cde3677429cf2eada` | `b36bbedb8ff9a35989be20924f4042e79101cc42e777771506741192f8072f5d` |
| `unicode_qualitative` | `41f36b6deab7a4011f0925289ff8317488b89a665513feb1359c21a07c0f46f5` | `197563744577ef1247b178cc36cdf14786bd116390e968566228f92aebfe2e00` |
| `untrusted_job` | `92b9e80e1973394c125a66ffc705a6a364f6d0134687e3af8387e573510619ea` | `9293277e840ddc44cb308e8d73ad23949e9ac507d49013242dad568bc9b4dda4` |

Hashes establish reproducibility of this observation, not authenticated identity, semantic
correctness or universal quality. No output failed in this pass; failure retention is covered by
separate synthetic tests, not claimed as an observed live failure.

## Limits and next action

Six software-focused fictional cases, seven short bullets and one deterministic-settings pass
cannot characterize paraphrase accuracy, general hallucination risk, useful condensation, other
domains/languages or repeated-run stability. There was no held-out prompt comparison or paired
footer control. Zero edits means semantic fidelity of transformed wording was **not exercised**;
the footer result does not establish general injection resistance. An agent's review is fallible.

Keep source seeding as the reliable deterministic baseline. The next small iteration should
evaluate **actual rewriting usefulness** using a separately versioned objective and held-out,
rougher source statements, while preserving copy fallback, qualifiers, evidence isolation and
existing human-review gates. Do not silently tune/rerun this frozen measurement or move straight
to rendering/full-resume approval on the strength of these valid but unchanged responses.
