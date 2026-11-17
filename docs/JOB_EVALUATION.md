# Synthetic job-analysis evaluation

## Purpose and scope

Schema/quotation validation cannot detect a missing tag or a preference assigned to the wrong
category. This small developer benchmark compares validated extraction against human-authored,
source-grounded reference texts. It is a Phase 2 quality tool, **not** a matching/ranking engine,
semantic truth test, general accuracy certification, or resume generator.

The reusable scorer is `resumeforge.jobs.evaluation.evaluate_analysis`. A repository-only runner,
`scripts/evaluate_jobs.py`, covers a fixed fictional corpus. It accepts no profile or arbitrary
job path, performs no model downloads, and uses the existing guarded provider/validation path.
No new installed CLI command or external dependency was added. Version: ResumeForge 0.4.1.

## Run offline first

From the repository root after the normal editable installation:

```bash
python scripts/evaluate_jobs.py
```

Default `reference_replay` compares each hand-authored reference with its own validated replay.
All six cases should match. **This tests the references and harness, not extraction by a model.**
Normal pytest/CI tests additionally inject omissions, category swaps and invalid responses;
they never invoke a real model. CI runs the runner's integration test as part of the full suite.

To compare independently captured raw provider responses without inference:

```bash
python scripts/evaluate_jobs.py --responses-dir artifacts/evaluation-responses
```

Each selected case needs `<case_id>.response.json` containing raw `JobRequirements` JSON, not the
outer `JobAnalysis` envelope. Missing files are explicit failed cases, never silently skipped.
Use repeated `--case` flags for a subset; duplicate selections are evaluated only once:

```bash
python scripts/evaluate_jobs.py --case backend_intern --case missing_metadata \
  --responses-dir artifacts/evaluation-responses
```

Replay metadata truthfully says `fake` / `fixture-v1`; the script cannot establish which model
originally produced a raw response. Record original runtime/model digest/settings separately.
Never copy real provider responses, private job data or generated reports into public fixtures.

## Explicit local evaluation (operator opt-in only)

Only when a live evaluation is deliberately requested, start the separate cloud-disabled Ollama
runtime as in [OLLAMA.md](OLLAMA.md), then run:

```bash
mkdir -p artifacts
python scripts/evaluate_jobs.py --provider ollama --model qwen3:4b \
  --ollama-port 11435 --timeout 600 > artifacts/job-evaluation.json
```

Port 11435 is the earlier temporary development setup; the default is 11434. A full run makes
one inference per selected case, so six CPU cases can take several minutes. The deadline is
per case, not a whole-benchmark deadline. The adapter rechecks local-only guards before every
request. There are no retries, corrective model calls or fallbacks. No live evaluation is run
automatically, and no model is installed/pulled by the script. `--responses-dir` and live mode
are mutually exclusive; nondefault Ollama-only options are rejected in replay mode.

The runner emits one JSON report to stdout and creates no files itself. CLI usage errors go
to stderr. Exit codes: **0** = all selected cases exactly match the reference; **1** = at least
one mismatch, missing response, provider failure or validation failure; **2** = invalid options.
A nonzero exact-match exit is a review signal, not proof that every alternative span is wrong.

Reports do not include raw API envelopes, thinking or full prompts. They do contain source-derived
reference/result texts, so retain reports in ignored storage. The fixed corpus is synthetic;
this is not permission to put private data in a benchmark or default logs.

## Corpus `synthetic-jobs-v1`

| Case ID | Source under `examples/jobs/` | Focus |
| --- | --- | --- |
| `backend_intern` | `backend_intern.md` | Required/preferred clauses, frameworks, testing tags. |
| `missing_metadata` | `missing_metadata.txt` | Null company/title, SQL tagging, plain text/Unicode. |
| `mixed_priority` | `evaluation/mixed_priority.md` | Preserve `or` and optional clauses; do not require both alternatives. |
| `negated_requirement` | `evaluation/negated_requirement.txt` | A negated technology is not a positive qualification. |
| `untrusted_instructions` | `evaluation/untrusted_instructions.md` | Exclude unrelated footer instructions; no profile/tools are available. |
| `regulated_unicode` | `evaluation/regulated_unicode.txt` | Non-software domain terms, Unicode employer/location, empty software categories. |

Each adjacent `.response.json` is a **hand-authored annotation**, not model output or guaranteed
exhaustive ground truth. Edit/review the source and reference together. IDs are stable manual
references; evaluation does not require model-generated IDs to match them.

Taxonomy tags record mentions, not requirement strength: the negation case includes `Kubernetes`
as a concept mention but never as a required/preferred qualification. A match on that tag alone
must not be used to require Kubernetes experience. The current schema lacks typed negation and
alternative-group semantics; literal qualification text must retain those caveats. The footer
case is a limited regression scenario, not proof of prompt-injection resistance.

## Scoring `job-evaluation-v1`

1. Validate both reference and response with the unchanged job-analysis engine.
2. The scorer checks source hash and rechecks quote grounding on both sides.
3. Within each of the eight item categories, compare **case-sensitive exact text sets**.
   Item order, IDs and different valid quote lengths do not affect agreement.
4. Report matched, missing and unexpected text spans per category. Moving a preference into
   required qualifications produces a missing preferred item **and** an unexpected required item.
5. Per-category and micro item precision = matched / actual; recall = matched / reference.
   Zero denominators produce JSON `null`, not artificial 100% values. Metadata is checked
   separately for exact company/title text or null; it does not inflate item scores.
6. An exact-match case has no missing/unexpected items and both metadata fields match.
   Two empty item sets may agree exactly while precision/recall remain unknown (`null`).

Validation failures have no item score. Summary counts include **all selected cases**, validated
cases and exact-match cases separately, so invalid model outputs cannot disappear from results.
There is deliberately no overall model-accuracy percentage that averages away validation failures.

These are **annotation agreement** metrics. A correct longer/shorter source span can score as a
mismatch. An unexpected item may be useful, and a reference can itself be incomplete/wrong.
Conversely, exact agreement only covers these annotations, not general semantic correctness or
complete extraction. Review required/preferred interpretation, negation, alternatives and quotes
manually; do not tune validators to turn a red score green. Do not normalize facts silently.
Prompt/model changes need held-out examples before any quality claim beyond this tiny corpus.

### Single-pass live review protocol

Freeze the corpus, reference texts, prompt and runtime settings for a review pass. Record the
application Git revision, source/reference hashes, model weight digest, Ollama version and
per-case wall time outside Git. Run each selected case once, with no retries or silent repairs;
keep schema/quotation failures in the denominator and retain only deliberately captured
synthetic responses in private storage for inspection. Default application logging stays unchanged.

Review the source and response together, distinguishing:

- **Annotation-span differences:** a valid shorter/longer literal span needs review, not automatic
  semantic rejection or a changed reference merely to raise the score.
- **Coverage gaps:** a clause or taxonomy tag is absent even though the response validates.
- **Meaning/classification problems:** negation, alternatives, optional status or metadata are
  interpreted incorrectly despite genuine source quotations.
- **Validation failures:** invalid structure, IDs, casing or quotes are rejected, not usable analyses.

Synthetic regression tests separately demonstrate that source-grounded output can still drop an
alternative's qualifier, treat a negated technology as required, or copy an employer from an
untrusted footer. These constructed mutations are not real model responses or a proof that the
reference comparator detects every semantic problem. Quotation checks are not instruction-defense
or classification guarantees, and this schema still has no typed negation/alternative groups.

## Recorded-response check (no new inference)

Offline comparison of the two saved prompt-v3 Qwen3:4b development responses confirmed:

| Case | Schema/source checks | Exact-reference item agreement | Missing annotation |
| --- | --- | --- | --- |
| `backend_intern` | Passed | 9/10; precision 1.0, recall 0.9 | `automated tests` concept |
| `missing_metadata` | Passed | 5/6; precision 1.0, recall about 0.833 | `SQL` language |

Both metadata checks matched. Main qualification text remained present, but both cases correctly
reported `mismatch`. At the time of that offline check, the four new cases had only been
reference-replayed; it was not a broader live-model result. The recorded responses remain in ignored
temporary storage, not Git. Original live runtime/model/prompt details are in [OLLAMA.md](OLLAMA.md).

## Completed single-pass local review

The subsequently requested six-case live pass used the unchanged prompt v3, corpus and validators:
**6/6 schema/quote-valid responses, 0/6 exact reference matches**. Missing tags affected every
case; the footer case also lost known company/title metadata. One SQL preference was shortened
in item text while retaining its caveat in the quote and remaining in the preferred category.
The run took about 475 seconds, with no retries. See the
[full review and per-case results](evaluations/qwen3-4b-v3.md).

This completes the initial broader review, **not** a quality approval for unattended ranking.
Next: typed completion-state/preferences before Phase 3 matching/planning, with reviewed
requirements or deterministic fixtures until extraction quality is improved separately. Do not
rely on taxonomy tags alone or treat historical AI output as verified candidate evidence.
