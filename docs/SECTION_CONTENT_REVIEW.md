# Pending selected skills/coursework and explicit source context — 0.20.0

`review-content` makes **explicitly chosen recorded skill/course names** visible beside the
current wording/plan inspection. Optional user-cited accomplishment references preserve original
statements and scope; they are context for review, **not semantic support or verified proficiency**.
Every item stays pending. A course name establishes no enrollment, completion, grade or institution.
This first slice provides neutral review questions; it does not save answers, import new facts,
apply decisions, resolve assembly blockers or authorize rendering.

## Explicit private workflow

Use the original profile, exact local job, reviewed requirements, reviewed plan selection, explicit
current wording draft and a separate content selection. `--confirm-review` acknowledges reviewed
requirements and both selections, not skill verification or wording/content approval.

```bash
resumeforge review-content \
  --profile artifacts/private-profile.md \
  --job artifacts/job.md \
  --requirements artifacts/reviewed-requirements.json \
  --selection artifacts/plan-selection.json \
  --draft artifacts/draft.json \
  --content-selection artifacts/section-content.json \
  --confirm-review
```

All six paths and confirmation are required before input I/O. Content selection JSON is parsed
before profile access. No implicit profile/seed, provider, research, URL fetching, generic approval,
interactive input, automatic file writing or migration exists. Keep all real inputs/reports private.
The plan must already include the selected `skills`/`coursework` sections, either explicitly through
`include_sections` or required preferences. Change plan selection and reseed/review the draft when
needed; content choices cannot create a new section behind your back.

## Version-1 content selection

The strict root has exactly `schema_version: 1`, `skills` and `coursework` arrays. Both arrays may
be empty. The shape below is fictional, **not an approved skill or course**:

```json
{
  "schema_version": 1,
  "skills": [
    {"category": "languages", "source_index": 0, "expected_text": "Python",
     "accomplishment_ids": ["acc_api"]}
  ],
  "coursework": [
    {"source_index": 1, "expected_text": "Databases", "accomplishment_ids": []}
  ]
}
```

- Skill `category` is exactly one existing profile category: `languages`, `frameworks`, `libraries`,
  `tools`, `platforms`, `other`. No inferred taxonomy, arbitrary model path or attribute expression.
- `source_index` is a strict nonnegative **zero-based** index into that skill category or the root
  coursework list. `expected_text` must equal the entire current model string, case/whitespace
  included. No synonyms, normalization, replacements or new skill labels. A shifted index with a
  different label fails safely; inspect/reselect current sources rather than blindly updating it.
- Source refs such as `skills.languages.0` and `coursework.1` are opaque logical references, not
  executable paths or durable skill IDs. Profile lists currently have no stable skill/course IDs.
  Duplicate recorded text at different indices is not silently deduplicated; no identity is inferred.
- Each item may cite up to 32 distinct accomplishment IDs, **all already selected and eligible in
  the current freshly recomputed plan**. Unknown, unselected, excluded, unverified or unfinished
  references fail without partial output. Citation order is explicit user order, not relevance.
- Empty citation arrays are allowed and flagged as missing context, never filled by searching
  parent technology lists, notes, old bullets, job text, other courses or unselected accomplishments.

Select at most 512 combined skill/course items and 512 combined links. Duplicate source-item choices
are rejected independently of duplicate labels. Labels are nonblank and at most 8,192 characters.
Retain strict UTF-8 1 MiB/32-level JSON limits, optional BOM, duplicate-key/nonstandard-number,
wrong-type, unknown-field and self-declared approval/proficiency rejection. API objects are
revalidated and byte-checked; unchecked model construction cannot bypass the boundary.

## What the report means

The engine snapshots/revalidates source profile and content selection, requires an explicit draft
and three exact-true review flags, and freshly runs existing plan/wording inspection. Source indices
and expected labels must agree with that snapshot. It accepts no prior review/assembly/decision
receipt or edited content document as evidence. Existing schemas, evidence eligibility and bullet
policies are unchanged.

The output-only `SectionContentDocument` has schema 1 and independent policy
`source-bound-section-content-v1`. It binds the current plan, exact wording document and validated
compact content-selection JSON hashes. Outer `document_sha256` hashes the validated compact UTF-8
content document. These are model snapshot hashes, not file hashes, authenticated review or truth.
Source/job/requirements/preferences/selection/wording/policy changes conservatively change relevant
bindings or reject the stale draft. Notes remain outside enforced model hashes; review originals.

Sections preserve current plan order/required flags, including empty skills/coursework placeholders.
Items follow explicit source-selection order within each section, with exact `source_ref`, source
`text`, `review_status: pending_review`, `cited_context` and two neutral `review_questions`.
Questions have **no answers, chosen options, proficiency labels or confirmations**. They ask about
personal usage/contribution/supervision and allow “not used” or uncertainty; course questions ask
what the record means and what original source supports it. Do not fabricate an answer from a
selected citation. Saving/reviewing new answers is a separate future source-intake workflow.

Each cited context retains accomplishment/entry/section IDs, the **entire original statement**,
recorded parent completion state, plan caveats and `literal_label_mention`. This nullable string
is only the first case-insensitive bounded literal name match in that statement, retaining source
case. The existing Unicode word/`+`/`#` boundaries distinguish C/C++/C# and Java/JavaScript.
No exact offsets, inferred tool use, skill level, class/job equivalence or qualification verdict
is claimed. Mentions may be negated/incidental; absence is unknown. Coursework project citations
do not prove attendance/completion. No claims/metrics transfer between sources.

The accompanying `wording_review` retains full current selected evidence, complete reviewed job
categories/quotes, original literal findings/fragments, completion caveats and plan conflicts.
These may contain identifying strings or the same words as unselected skills: selective disclosure
is **not anonymization or keyword redaction**. Only explicitly chosen skill/course source values
are copied into the content document; contact, notes, parent details and other raw lists are not.

### Finite observations, not a gap/satisfaction report

| Finding | Meaning |
| --- | --- |
| `skill_usage_requires_user_review` | Every selected skill still needs deliberate usage/context review. |
| `coursework_context_requires_user_review` | Every selected course still needs original context review. |
| `no_cited_accomplishments` | No current selected accomplishment was explicitly cited; do not infer absence of experience. |
| `label_not_literal_in_cited_statement` | That name was not a bounded literal substring of this cited statement; not an unsupported-claim verdict. |
| `section_without_selected_items` | A planned skill/coursework section has no explicitly chosen items. |
| `no_selected_items` | Neither source list has selected content; empty selections do not approve anything. |

Findings follow skills then coursework selection/citation order, then plan-ordered empty-section
observations, then the empty-overall observation. No score/rank, requirement satisfaction, “missing
and false” inference or automatic content selection. Review full sources even when a mention exists.

All records, including exact source copies, stay pending. No bullet/metadata attestation transfers
to skill/course claims. `assemble-resume` deliberately still reports `unscoped_section_unresolved`:
this review is not an assembly input or a new approval path. Scope is
`selected_section_content_only`, `rendering_authorized: false` for every result.

## Limits, examples and next boundary

Complete default indented review output is capped at 1 MiB, without truncation or partial JSON.
Reduce deliberate selections/citations if necessary; never shorten sources silently. Structured
source data is untrusted: malicious skill names/statements cannot grant tool or provider permission.
Keep results, statements, reasons/answers and hashes private; no real data belongs in examples/Git.

`examples/content/backend_intern.plan.json` and `backend_intern.content.json` are fictional choices
for the shared sample. First seed a wording draft using that plan and extract its inner `document`,
then inspect content with the same sources and plan. The unchanged sample intentionally exits 3
for its education bullet-count conflict; selected labels/context/questions remain pending/visible.
This is deterministic replay/inspection, not extraction, a live-model test or a human review.

Exit **0** produces pending inspection without plan conflicts, **3** produces pending inspection
with plan conflicts, **1** rejects invalid/stale/oversized inputs/output without JSON, **2** rejects
usage/confirmation errors before I/O. No exit code approves content or authorizes rendering.

Python API: `review_section_content(profile, job, requirements, selection, draft, content_selection,
requirements_reviewed=True, selection_reviewed=True, content_selection_reviewed=True)` returns
`SectionContentReview`. It, `SectionContentSelection`, `parse_section_content_selection` and
`load_section_content_selection` are exported from `resumeforge.resume`. Safe failures raise
`ResumeError`; local file loading can raise `InputError`.

Next: a separately confirmed snapshot-bound skill/coursework user-decision contract and deliberate
assembly integration, retaining source questions/context and unresolved states. New-answer intake,
before-edit requirement gap reports and proposed change/omission reports remain separate work;
see [TAILORING_WORKFLOW.md](TAILORING_WORKFLOW.md). No research, new inference or PDF work is implied.
