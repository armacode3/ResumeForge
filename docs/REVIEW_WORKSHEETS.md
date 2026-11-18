# Pending review worksheets — 0.16.0

`review-resume --worksheet` reduces manual copying when preparing human wording decisions. It
freshly inspects the original sources and explicit draft, then emits the full review context
alongside an **unfilled** version-3 decision template. It never chooses approval/rejection,
acknowledges findings, accepts omissions, supplies reasons or links draft passages for the user.

This is an offline JSON authoring aid, not a resume renderer, interactive editor, semantic judge,
decision receipt or proof that anyone reviewed the source. All draft/inspection bullets remain
pending. Rendering authorization is always false; approval scope remains bullet wording only.

## Workflow

1. Seed/save an inner `ResumeDocument`, or deliberately edit an existing draft, using
   `docs/RESUME_DRAFTS.md`. Keep original sources and draft in private local storage.
2. Supply all four original sources, the explicit draft, `--confirm-review` and `--worksheet`:

```bash
resumeforge review-resume \
  --profile data/profile/user_information.md \
  --job artifacts/job.md \
  --requirements artifacts/reviewed-requirements.json \
  --selection artifacts/selection.json \
  --draft artifacts/draft.json \
  --confirm-review --worksheet > artifacts/worksheet.json
```

These paths are private files you must create/review; this command does not create their parent
directories or seed an implicit draft. Choose a new output path and private permissions; shell
redirection, not the application, writes the file and can overwrite an existing file.

3. Inspect `review`: the exact draft is in `review.document`; complete selected source statements,
   caveats, numeric/cue findings and source fragments are in `review.bullets`, keyed by bullet ID.
   `review.plan` retains complete reviewed job context, required placeholders and conflicts. Check
   the entire source and wording together; literal observations are not semantic support verdicts.
4. Extract **only `decision_template`** into a separate private decision JSON file. For each bullet
   actually reviewed, deliberately choose `approve` or `reject` and a nonblank reason. Add only
   finding IDs actually reviewed to `acknowledged_finding_ids`. For reviewed fragments, fill the
   disposition/reason and, for `represented_in_draft`, an exact nonblank draft passage. The existing
   [decision](REVIEW_DECISIONS.md) and [fragment](SOURCE_FRAGMENT_REVIEW.md) guides define these fields.
5. Remove entire bullet records you have not reviewed; absent decisions remain pending. Within a
   completed bullet decision, remove unreviewed fragment placeholder records rather than inventing
   a disposition. Those fragments remain unreviewed and block approval. A rejection needs no
   fragment review, so an empty fragment list is allowed. **Leaving any null placeholder record
   in a decision file is invalid**, not an implicit pending decision or approval.
6. Apply the completed decision file through the unchanged explicit confirmation gate:

```bash
resumeforge review-resume \
  --profile data/profile/user_information.md \
  --job artifacts/job.md \
  --requirements artifacts/reviewed-requirements.json \
  --selection artifacts/selection.json \
  --draft artifacts/draft.json \
  --decisions artifacts/decisions.json --confirm-review --confirm-decisions
```

`needs_revision` dispositions, missing fragment reviews or missing finding acknowledgements keep
requested approvals pending. Rejection preserves content; plan conflicts block approvals. An exact
passage link is a user equivalence assertion, not software proof; accepted omission does not prove
that losing a qualifier is safe. Do not bulk-fill choices merely to obtain a successful exit code.

## Worksheet contract

`ReviewWorksheet` contains:

| Field | Value |
| --- | --- |
| `worksheet_version` | `pending-review-worksheet-v1`. |
| `scope`, `rendering_authorized` | `bullet_wording_only`, false. |
| `status` | Fresh inspection's `needs_review` or `blocked_by_plan`. |
| `review` | Complete freshly recomputed `ResumeReview`, not a supplied historical report. |
| `decision_template` | Current version-3 root bindings, with ordered pending bullet/fragment records. |
| `warnings` | Instructions and approval/semantic/privacy limits. |

The template has the existing decision fields: `schema_version: 3`, current `review_version`,
plan/document/finding/fragment hashes and `bullets`. All hashes and IDs come from fresh inspection.
Every bullet's `decision`/`reason` starts null, `acknowledged_finding_ids` starts empty, and each
observed fragment has its ID plus null `disposition`/`reason`/`draft_span`. No automatic passage,
omission acceptance or rationale is generated. Verbatim bullets also get blank choices; an empty
document has no bullet records and can never become approved by vacuity.

The worksheet envelope is **not accepted** by `--draft` or `--decisions`. Its pending template is
deliberately not valid decision input for nonempty drafts until the user completes/removes pending
records. There is no worksheet loader/converter that infers missing choices. The typed worksheet
models are immutable output-only pending scaffolds; completed input is validated separately by the
unchanged strict `ReviewDecisions` schema and fresh source-bound decision engine.

Generating a new worksheet does not import previous choices or carry attestations forward. Changed
sources, wording, selection or policies require fresh review; updating hashes alone cannot make old
finding/fragment IDs current. Hashes are neither authentication nor anonymization. These files can
contain sensitive sources, wording, job data and review rationale; never commit them or log them.

## Gates, limits and compatibility

- `--worksheet` requires `--draft` and `--confirm-review`, and cannot be combined with `--decisions`
  or `--confirm-decisions`. Invalid combinations fail before all input reads. No default private
  profile, provider option, model call, network access, write-back or history is introduced.
- Worksheet **exit 0** means an unfilled worksheet without plan conflicts, **3** emits a complete
  plan-blocked worksheet, **1** rejects invalid/stale/oversized input/output with no partial JSON,
  and **2** rejects usage/confirmation errors before source reads. JSON is on stdout; notices/errors
  are static on stderr. Ordinary inspection and decision modes keep their original behavior.
- The default indented UTF-8 worksheet serialization is capped at 1 MiB, without truncation. A
  large valid ordinary inspection can therefore fail worksheet generation: reduce the explicit
  selection deliberately and review again. Existing source/draft/decision limits still apply.
- Profile/draft/response schemas stay version 1; decisions/inspection stay v3. Existing valid v3
  decisions need no rewrite; old formats are not migrated. Provider instructions, request data,
  finite observation policies, frozen corpora/protocols and historical results are unchanged.

Python API: `build_review_worksheet(profile, job, requirements, selection, draft,
requirements_reviewed=True, selection_reviewed=True)` returns `ReviewWorksheet`. It requires exact
boolean confirmations, an explicit draft and original sources, not an input review/worksheet.
Both names are exported from `resumeforge.resume`; safe failures raise `ResumeError`. No live
evaluation or private-user review was performed to implement this feature. Metadata/full-resume
approval, rendering/PDFs, semantic proof, ranking, persistence and cloud inference remain separate.
