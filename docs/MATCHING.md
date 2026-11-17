# Offline evidence eligibility and lexical matching — 0.6.0

## What this slice does

`match-evidence` retrieves review candidates from verified, explicitly completed accomplishments
against **manually reviewed** job requirements. It is deterministic and offline: no LLM, network,
embeddings, automatic inference, ranking, resume selection or generation is involved.

**A lexical candidate is not a qualification verdict or proof of entailment.** A shared technology
can be incidental, negated or refer to a different responsibility. An unmatched item may reflect
different wording or missing extraction, not missing experience. Review the original profile and
full job, not just the report. This feature does not reverse the local-model quality limitations.

## Run the fictional example

```bash
resumeforge match-evidence \
  --profile examples/profiles/sample.md \
  --job examples/jobs/backend_intern.md \
  --requirements examples/jobs/backend_intern.response.json \
  --confirm-review
```

All three paths are explicit; this command has **no default private-profile access** and no provider
option. Requirements are raw `JobRequirements` JSON, like the hand-authored fixture, not the outer
`JobAnalysis` result. For an existing analysis, deliberately review/edit its inner `requirements`
object against the full source and save that object privately before matching. The command never
extracts requirements or automatically runs a live provider to fill a missing file.

`--confirm-review` acknowledges that you reviewed required/preferred distinctions, metadata,
alternatives, negation, qualifiers and completeness against the full job. It is a user assertion,
**not software verification, authorization embedded in job text or a permanent approval record**.
Without it, the command exits with a usage error before reading inputs. Literal quotes are still
validated; confirming review cannot bypass schema/source checks or approve candidate evidence.

Success emits one JSON report to stdout and an offline/review notice to stderr, without writing
files. Store real reports under ignored `artifacts/` if needed. They deliberately contain eligible
profile statements and job text/quotes; they are private output, not safe public logs. The person/
contact fields, Markdown notes and statements of ineligible accomplishments are not included.
Hashes do not anonymize personal data. Normal application logging remains unchanged.

Exit codes: **0** = report produced (including unmatched items/review findings); **1** = invalid
input, source mismatch or comparison budget exceeded; **2** = usage error/missing confirmation.
There is no partial JSON on failure and no automatic retry or fallback.

## Eligibility is not completion inference

Every accomplishment receives a stable-ID decision, in accomplishment-ID order:

| Decision | Rule |
| --- | --- |
| `excluded` | Its parent entry is explicitly excluded. Exclusion wins over other reasons. |
| `unverified` | Not excluded, but `verified` is false. Neither preferences nor keywords approve it. |
| `status_review_required` | Verified, but its own state is not `completed`, or the parent is not `completed`/`in_progress`. |
| `eligible_for_matching` | Verified, explicitly completed scoped work with a completed/in-progress, non-excluded parent. |

All applicable reason codes are retained, not only the winning decision. Unknown state remains
unknown; no dates, prose or old "Present" labels supply completion. Planned, ongoing, paused or
cancelled accomplishments stay out of retrieval until reviewed rather than being treated as
completed results. A verified statement describing those states remains stored; it is simply not
automatically retrieved by this conservative first policy.

A completed subtask may be retrieved from an in-progress parent, but carries
`parent_entry_in_progress` and both original statuses in the report. This does not complete the
parent or approve a broader claim. Unknown/on-hold/planned/cancelled parent states require review
before automated retrieval; this is a versioned retrieval policy, not a claim those records are
untrue or should be deleted. Legacy profiles remain valid but often need explicit status review.

Only scoped accomplishment statements and their own technology lists participate. A skill list,
parent entry's technology list, coursework, notes or historical/verified bullet wording cannot
substitute for accomplishment evidence. Excluded accomplishments cannot re-enter through bullets:
bullets are never independently matched, and their evidence references are not rewritten.
The `verified` flag still records the user's factual assertion, not semantic proof by the software.

## Retrieval rules (`evidence-matching-v1`)

For every item in all eight reviewed job categories, preserve its ID, category, exact text and
source quote. Company/title are metadata, not matching targets. Retrieve an eligible accomplishment
when either of these literal relationships exists:

1. **`technology_mention`:** a technology explicitly listed on that accomplishment appears in
   the job item's text.
2. **`job_phrase_in_statement`:** the entire job item's text occurs within the verified scoped
   statement. This allows phrases such as `automated tests` without treating them as technology names.

Comparison uses case-insensitive escaped literal regexes, with Unicode word/`+`/`#` boundaries.
Thus Java is not JavaScript, SQL is not PostgreSQL, and C is not C++ or C#. It is not fuzzy matching,
stemming, synonym expansion, technology inference or a universal tokenizer. Names such as `Go`
can collide with ordinary prose. Case-insensitive technology duplicates produce one technology
overlap; distinct relationship types may both be recorded, with **no score inflation or ranking**.
Original evidence/job spans are returned without normalizing facts or inventing wording.

Candidates are ordered by accomplishment ID, not relevance or keyword count. Job categories/items
retain source order. Matching scans qualification/duty text as well as taxonomy categories, so
omitting a SQL language tag does not hide a reviewed preferred clause that still mentions SQL.
It does not repair omitted clauses or establish absence from the full original job.

Both `Python or Java; either is sufficient` and `Python is not required` can produce a Python
lexical candidate. They remain single, unchanged contextual items—not split into mandatory skills
or declared satisfied. Required/preferred distinctions are never upgraded by a tag or overlap.
Interpretation and claim support remain human-review/Phase 4 responsibilities.

## Review findings and remaining planning work

The report flags required entries/sections with no eligible accomplishment evidence, required
skills/coursework sections needing a separate evidence-review model, and a project minimum above
the number of projects with eligible evidence. These are review findings, not invented support,
silent omissions or a finished plan. Required entries remain marked required even if unrelated
to the job or blocked from lexical retrieval.

Project/bullet maxima, per-entry bullet allocation, relevance ranking, section assembly and
readable-one-page feasibility are **not** allocated or solved here. The profile boundary already
rejects structural preference contradictions; the matcher does not override those constraints or
choose content. A future planner must honor exclusions transitively and surface remaining conflicts.

## API, provenance and limits

```python
from resumeforge.matching import match_evidence

# profile: validated UserProfile; document: exact JobDocument;
# requirements: manually reviewed JobRequirements
report = match_evidence(profile, document, requirements, requirements_reviewed=True)
```

The API accepts no provider, file paths or Markdown notes. It revalidates input snapshots and
quote grounding rather than trusting mutated Pydantic objects. Review acknowledgement must be
boolean true, not a truthy string/integer. Failures raise static, safe `MatchingError` messages.

`MatchingReport` contains algorithm version, source identity, evidence decisions, per-item
candidates and constraint findings. `job_source_sha256` hashes exact job UTF-8 bytes.
`profile_model_sha256` and `requirements_model_sha256` hash the validated models' JSON (including
profile preferences), **not** original file bytes or proof of review; ordering can change those
model hashes. Outputs are immutable dataclass/tuple snapshots, not references to mutable inputs.

At most **20,000 eligible-accomplishment/job-item pairs** are compared. Larger requests fail
before retrieval instead of truncating evidence or job content. This is a comparison-count
guard, not a hard CPU/process sandbox. Existing bounded file/schema loaders still apply to CLI
inputs. Normal tests use fictional inputs and fake JSON only, never a model or private profile.

Next: measured, explainable relevance signals and constrained resume planning as separate slices;
never use lexical-count ranking alone or promote a retrieval candidate into an approved claim.
