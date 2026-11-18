# Reviewed-selection resume plans — 0.8.0

`plan-resume` assembles a private, structured **draft** from explicit entry/accomplishment IDs,
profile preferences and manually reviewed job requirements. It checks count constraints and
preserves source references; it does not invent a ranking policy, choose evidence from keywords,
generate resume wording, approve claims or establish readable one-page feasibility.

## Workflow and fictional example

1. Validate/review your profile facts, completion states and typed preferences.
2. Review requirements against the full job, including omissions, required/preferred distinctions,
   alternatives and negation. `match-evidence` can help inspect candidates; it is not proof.
3. Deliberately choose entries and scoped accomplishment IDs in a private selection file.
4. Run `plan-resume`, inspect every finding, and revise inputs deliberately. The command does not
   write back to profiles, selections or reports. No live provider, network or default private
   profile access is involved.

```bash
resumeforge plan-resume \
  --profile examples/profiles/sample.md \
  --job examples/jobs/backend_intern.md \
  --requirements examples/jobs/backend_intern.response.json \
  --selection examples/plans/backend_intern.selection.json \
  --confirm-review
```

**This example intentionally exits 3 with a draft and a conflict.** The fictional profile requires
education and at least one bullet per selected entry, but has no selected eligible education
accomplishment. Education stays visible with zero slots; the planner does not invent a bullet or
silently ignore that minimum. A user may explicitly revise their preferences to permit metadata-
only entries, or review/add genuine evidence. Do not fabricate evidence to make the command pass.

Requirements are raw `JobRequirements` JSON, not the outer analysis envelope or a matching report.
The existing bounded offline replay loader validates them; this is ingestion, not extraction.
`--confirm-review` acknowledges review of both requirements and selection; it is a caller assertion,
not semantic proof, permanent approval or authorization embedded in JSON/job/profile text. It is
required before any input I/O. Selection content cannot enable a provider or approve claims.

## Selection format (version 1)

```json
{
  "schema_version": 1,
  "entries": [
    {"entry_id": "edu_example", "accomplishment_ids": []},
    {"entry_id": "exp_example", "accomplishment_ids": ["acc_api"]},
    {"entry_id": "proj_queue", "accomplishment_ids": ["acc_queue"]}
  ],
  "include_sections": ["skills"],
  "max_total_bullets": 4
}
```

`schema_version` and `entries` are required. An empty entries list is valid input, not a finished
resume. Every selected entry requires an explicit `accomplishment_ids` list, possibly empty for
metadata-only content. Entry IDs must be unique; accomplishment IDs within an entry must be unique,
exist and belong to that exact parent. Bullet IDs, invented references and detached evidence are
rejected. No wording is accepted in this format, and no old verified bullet is reused implicitly.

Optional `include_sections` is a distinct list containing only `skills` and/or `coursework`; those
are review placeholders, not scoped accomplishment evidence. Other sections follow selected entries
and required preferences. Omission means no additional sections. Empty requested skills/coursework
produce conflicts. Even populated sections require separate evidence/metadata review; their values
are not automatically copied or treated as verified claim support.

Optional `max_total_bullets` is a strict integer 0–20 or null, default unspecified. It is a total
**slot count** upper budget, independent of the profile's per-entry bullet bounds. The limit is not
a default target or promise of readable space. JSON rejects unknown fields, duplicate keys,
nonstandard constants, malformed IDs/types and excessive values/nesting. Files are bounded to
1 MiB of UTF-8 (optional BOM), with at most 32 nested collections. No new dependency is required.

## Assembly policy (`reviewed-selection-plan-v1`)

- Revalidate profile/selection snapshots and freshly recompute matching from the exact job and
  reviewed requirements. The API accepts no precomputed report whose eligibility/provenance could
  be forged or stale. The existing 20,000 eligible-evidence/job-item comparison guard still applies.
- Reject unknown/cross-parent references with static safe errors. These are input failures, not
  partial plans. Retain excluded-entry requests as explicit conflicts, but never emit those entries
  or their source statements as planned content. Other ineligible selected evidence yields conflicts
  and no slots; it cannot be promoted through preferences, metadata or verified bullet wording.
- Use only verified, completed accomplishments under non-excluded completed/in-progress parents
  for slots, exactly as in matching. One distinct selected accomplishment reserves **one** slot;
  this is a planning unit, not an instruction to copy the statement as an approved bullet or a
  guarantee that it fits a line. No splitting, merging, filling, rewriting or automatic trimming.
- Keep each slot's stable ID, unchanged statement (including qualifiers), job-item links and
  in-progress-parent caveat. An eligible user-selected accomplishment may have no lexical link;
  retain it with a review finding rather than declare missing experience or force keyword overlap.
- Add omitted `required_entry_ids` as visible metadata-only entries, marked
  `required_by_preferences`. Do not pick accomplishments on their behalf. Preserve all required
  sections. A required background section with no selected entries stays an empty placeholder and
  produces a conflict: the planner will not choose an arbitrary experience to satisfy it.
- Required sections do not require every entry. Required entries need not overlap the job.
  Metadata-only entries retain their original status and a review finding; unknown/planned/paused/
  cancelled entry states require additional review, never guessed completion. Education may be
  metadata-only only when the applicable count bounds allow it; metadata still needs review.
- Sections follow the profile's eight-section order, then skills/coursework. Within a section,
  explicit selection order is preserved, followed by newly added required entries in preference
  order. Accomplishment order follows explicit selection. This is **not relevance ranking**;
  keyword/metric counts, action verbs and signal presence do not influence content or ordering.

## Constraints and review states

The planner checks the profile's project minimum/maximum and per-entry bullet minimum/maximum,
plus the selection's optional total-slot maximum. Project counts include selected metadata-only
projects, not every available project or the number of project slots. Per-entry bounds apply to
every planned background entry, including required metadata-only entries; skills/coursework are
not bullet-budgeted entries. Missing bounds remain unspecified. Zero is honored, not replaced
with a default. A distinct evidence ID cannot be duplicated to meet a minimum.

Count conflicts report actual and bound values without removing selected/required eligible
content, loosening constraints or adding unsupported evidence. Ineligible/explicitly excluded
selections and missing required-section content are also conflicts. They cannot appear as a
conflict-free success just because eligible slot counts happen to satisfy a budget.

All outputs have `status: needs_review`. `constraint_status: within_count_constraints` means only
that this explicit assembly has no detected conflicts under this narrow policy; it is **not**
fact approval, sufficient job coverage, a final resume or layout feasibility. Other review findings
(metadata, unscoped sections, unmatched selections) remain visible even when counts pass.

Full job-item IDs, categories, text and quotes are preserved, with links only to selected eligible
accomplishments. Links are lexical associations, never requirement-satisfied verdicts. Unmatched
job items stay present; no match is not proof of missing experience or absence from the full job.
Company/title metadata are not planning targets. Source statements remain authoritative, not
generated/historical wording. Phase 4 now has a narrow wording-draft boundary; see
`docs/RESUME_DRAFTS.md`. Semantic claim checks and human approval workflows remain deferred.

## Output, errors and privacy

- **0:** draft emitted with no detected conflicts; still needs review.
- **3:** draft emitted with explicit conflicts; resolve/review before proceeding.
- **1:** invalid/missing input, broken references, source mismatch or comparison-budget failure;
  no partial JSON.
- **2:** usage error, including missing acknowledgement; inputs are not read.

One JSON draft goes to stdout; static offline/conflict notices go to stderr. Output contains
selected eligible statements, job text/quotes, stable IDs, statuses, budgets and findings. Person/
contact fields, notes, parent details/technology lists, unselected/ineligible claim text and metrics
are not copied. IDs/hashes do not anonymize private output. Store real selections/reports only
under ignored private directories, not examples, logs or Git. The provided selection is fictional.

`profile_model_sha256`, `requirements_model_sha256`, `selection_model_sha256` hash revalidated
model JSON, including preferences and selection order; they are not original-file hashes or proof
of review. `job_source_sha256` identifies exact job UTF-8 bytes. Matching/signal versions are carried
alongside the independent planning version. Results are immutable dataclass/tuple snapshots.

```python
from resumeforge.planning import plan_resume

# Validated profile, exact JobDocument, reviewed JobRequirements and PlanSelection:
plan = plan_resume(
    profile, job, requirements, selection, requirements_reviewed=True, selection_reviewed=True
)
```

Both acknowledgements require boolean true, not a truthy string/integer. Boundary errors raise
safe `PlanningError`; file loading can also raise `InputError`. No private migration is performed.
No font/line/page budget, rendering, readable-one-page test, automatic relevance selection, wording
generation, claim approval, PDF, history or cloud inference is implemented by this slice.
