# Profile format — schema version 1

## Why YAML inside Markdown?

Use YAML front matter for explicit, machine-validated facts and stable identifiers, followed
by unrestricted Markdown for explanations, rough notes and wording ideas. Unlike guessing
structure from prose headings, this makes evidence references deterministic and exposes typos.
Tradeoff: YAML indentation takes care. Start from the fictional
[`examples/profiles/sample.md`](../examples/profiles/sample.md), not a blank document.

The parser does **not** extract or verify facts from prose. Notes remain available to future
review workflows, but must be deliberately transferred into structured, reviewed evidence
before they can support a generated claim. No AI calls occur during profile validation.

## Private setup and usage

From the repository root, after installation:

```bash
mkdir -p data/profile
cp examples/profiles/sample.md data/profile/user_information.md
# Edit only the private copy with your own information.
resumeforge validate-profile
resumeforge validate-profile --profile examples/profiles/sample.md
```

`data/` is ignored by Git. Do not force-add it or edit the tracked example with personal data.
An explicitly supplied path can be elsewhere, but you are responsible for keeping it private.
The CLI reads only the selected local file, writes nothing, and prints counts and findings,
not contact details or evidence text. Do not redirect real profiles into public logs.

Exit codes: **0** = structurally valid, possibly with warnings; **1** = file/format/schema/reference
failure; **2** = CLI usage error. Warnings do not mean the profile is ready for generation.
Neither successful parsing nor a `verified: true` field proves factual correctness.

## Importing an existing narrative profile

There is no automatic narrative-import command. Curate an existing document into the schema
and retain qualifications, unresolved conflicts, source history and preferences in private notes.
This is a data-preparation task, not permission to rewrite a biography as confirmed facts.

- Create only a private copy under ignored `data/profile/`; never replace the fictional fixture
  with real information or paste the source into public docs, tests, issues or commit messages.
- Keep experience/project/organization IDs when valid. If an older accomplishment ID lacks
  `acc_`, prefix it once and record the original-to-canonical mapping in the private notes.
  Do not renumber existing IDs to improve appearance.
- Keep imported accomplishments `verified: false` until the user reviews each statement,
  attribution, technology and metric. Do not bulk-approve claims just because parsing succeeds.
  Entry metadata and skill/course lists also need review; their schema validity is not proof.
- Preserve lower bounds, uncertainty, supervision and contribution scope. Do not turn a quantity
  into an exact count, or a prototype/design/testability goal into implemented, tested behavior.
- Leave disputed or unknown dates unset and record alternatives in notes. Do not infer a month
  from an event year, or current membership from an old resume's "Present" label.
- Keep unconfirmed awards/certifications and pre-approved bullets empty; do not create them
  merely to populate every supported section. Keep student/client work distinct from paid roles.
- Do not duplicate one position under both experience and research, or repeat its accomplishments
  under an organization just to add more entries.
- If reorganizing or condensing a narrative, describe the import as curated rather than claiming
  it is a verbatim archive. Record evidence sources and substantive editorial choices privately.

Check locally with `resumeforge validate-profile` and verify ignore coverage:

```bash
git check-ignore data/profile/user_information.md
git ls-files -- data/
```

The first command should show the ignored path; the second should show no tracked private files.
Keep any saved validation report under ignored private storage too. Ignore rules are not
encryption; review staged changes and restrict local file permissions where appropriate.

### Completion state and preferences (additive support in 0.5.0)

Schema version 1 now accepts typed `completion_status` on background entries and accomplishments,
plus an optional root `resume_preferences` object. Existing version-1 profiles remain valid:
omitted states become `unknown`, preferences are unspecified, and nothing is inferred from dates,
entry details, old "Present" labels or Markdown notes. Unknown states produce review warnings.
The parser never rewrites an old file or migrates notes into structured facts automatically.

These are **validated input contracts**, not implemented content selection or layout controls.
Notes remain human context until deliberately transferred into the typed fields. `verified`
still defaults false and means something different from completion; see the field reference below.

Mandatory sections/entries, desired bullet counts and project counts may conflict with readable
one-page output. A future planner must surface that conflict rather than silently omit required
content or shrink typography. Also distinguish readable resume text from a verbatim `.tex`
mirror stored with a `.txt` extension; define separate export semantics before implementing them.
None of these planning or export capabilities exists at this stage.

## Minimal valid file

```markdown
---
schema_version: 1
person:
  name: Alex Example
---
# Rough notes

Keep detailed explanations here until you have reviewed the underlying facts.
```

Only `schema_version` and `person.name` are required at the root. Missing sections default
to empty lists; no experience, dates or metrics are inferred. This permits gradual profile
building. The minimal file produces completeness warnings.

## Field reference

Unknown fields, blank required text, wrong types and unsupported schema versions are errors.
Strings follow YAML scalar rules; fields are not stripped or rewritten. Exact raw formatting
is retained in `source_text`, and Markdown notes are not normalized.
Optional scalar fields may be omitted or `null`; optional collections should be omitted or `[]`,
not `null`. A collection must be a list even when it contains only one item.

### Person

`person`: `name` (required string), optional `email`, `phone`, `location`, and `links` (list of
HTTP/HTTPS URLs). Email uses a basic syntax check, not delivery verification or exhaustive RFC
validation. Phone is free text; no country or numbering format is assumed. Links are validated,
not fetched, and may be normalized by Pydantic; original source text is retained separately.
No email/phone yields a warning.

### Background entries

Each section contains records with these fields:

| Field | Meaning |
| --- | --- |
| `id` | Required stable ID with the section prefix below. |
| `title` | Required role, degree/program, project, certificate, award or activity title. |
| `organization` | Optional employer, institution, issuer or organization. Missing employer/institution is flagged. |
| `location` | Optional free text. |
| `start_date`, `end_date` | Optional quoted `YYYY-MM` (years 1000–9999); `end_date` also accepts `present`. |
| `details` | Optional list of user-supplied factual context, e.g. specialization or supervised scope. |
| `technologies` | Optional list of documented tools/technologies used in this entry. |
| `completion_status` | Optional exact status string, default `unknown`; independent of dates and verification. |

| Section | ID prefix | Example |
| --- | --- | --- |
| `education` | `edu_` | `edu_example` |
| `experiences` | `exp_` | `exp_internship` |
| `projects` | `proj_` | `proj_queue` |
| `organizations` | `org_` | `org_computing` |
| `research` | `res_` | `res_storage` |
| `certifications` | `cert_` | `cert_python` |
| `awards` | `award_` | `award_demo` |
| `additional_experience` | `other_` | `other_tutor` |

Suffixes use lowercase ASCII letters, digits and underscores. Assign IDs yourself once and
keep them across edits/reordering; the application never renumbers them. All IDs must be unique.
Missing dates are warnings, not invitations to guess. End dates cannot precede start dates.
Expected graduation dates may be in the future. Month precision is the current convention;
year-only/day-precise dates and uncertain intervals are not yet supported. Keep uncertainty in notes.

### Skills and coursework

`skills` has optional string lists: `languages`, `frameworks`, `libraries`, `tools`, `platforms`,
`other`. `coursework` is a top-level list of course names. These are user assertions, not
technologies to populate from job keywords. Numeric skill ratings are not supported.

### Accomplishments and quantifiable results

```yaml
accomplishments:
  - id: acc_tests
    entry_id: exp_internship
    statement: Added tests for 12 existing internal API endpoints under mentor review.
    verified: true
    technologies: [Python, pytest]
    metrics:
      - 12 existing endpoints covered by the added tests.
```

Required: `id` (`acc_` prefix), `entry_id` pointing to an existing background entry, and
nonblank `statement`. Optional: `completion_status` (below), `technologies`, `metrics` (string lists), `verified`
(boolean, **defaults to false**). Store scope, units and qualifiers in metric strings; quote
purely numeric values to keep them strings. Metrics are never required. Multiple accomplishments
can point to the same entry; all categories, including awards and research, can have evidence.

`verified: true` means **you have reviewed the source facts**, not that software checked them
against external records. Unverified records are retained and flagged, not promoted into usable
evidence. Missing verified evidence for any entry produces a warning. Keep unsupported impact,
ownership, technologies and measurements out of verified statements.

### Completion status is not verification

Both background entries and accomplishments accept these exact, lowercase `completion_status`
strings: `unknown`, `planned`, `in_progress`, `completed`, `on_hold`, `cancelled`.
Omission means `unknown`; `null`, booleans, alternate casing and guessed synonyms are errors.
Use `details` or the accomplishment statement to retain prototype/supervision/scope caveats;
this small lifecycle vocabulary does not replace that factual text.

Entry status describes the overall record's lifecycle, while accomplishment status describes
only its scoped work. A completed, verified subtask may belong to an in-progress project.
Neither status propagates to the other. Status also does not set, infer or revise dates:
`present` is not automatically `in_progress`, and an old end date is not proof of completion.
The validator does not infer whether a real-world date/status combination is factually consistent.

`completed` never sets `verified: true`. Conversely, a reviewed statement about planned or
ongoing work may be verified as a statement of that limited scope; it is not thereby a completed
achievement. Existing verified bullets still need verified accomplishment references, but that
graph check does not prove completion or semantic entailment. Unknown entry/accomplishment
statuses produce warnings so a future selection/review step cannot quietly assume completion.

### Resume preferences

Preferences are user instructions in a separate root object, **not candidate evidence**:

```yaml
resume_preferences:
  required_sections: [education, projects]
  required_entry_ids: [proj_queue]
  excluded_entry_ids: [other_tutor]
  min_projects: 1
  max_projects: 2
  min_bullets_per_entry: 1
  max_bullets_per_entry: 3
```

Use IDs that already exist in your own file. The example above refers to the fictional sample;
these are not defaults or a recommendation to include those records. There is no planner yet.

| Field | Contract for future content selection |
| --- | --- |
| `required_sections` | Distinct section names that must have non-excluded content. Allows the eight background section names above, plus `skills` and `coursework`; not `person`, `accomplishments` or `verified_bullets`. It does not require every entry in a section. |
| `required_entry_ids` | Distinct existing background-entry IDs that must be included. Accomplishment/bullet IDs are not accepted. |
| `excluded_entry_ids` | Distinct existing background-entry IDs that must not be selected; cannot overlap required IDs. Stored records/evidence are not deleted. A future planner must also exclude their claims and bullets rather than detach evidence references. |
| `min_projects`, `max_projects` | Optional bounds on the number of selected project entries, not project bullets. |
| `min_bullets_per_entry`, `max_bullets_per_entry` | Optional bounds for each selected background entry, not global/section bullet counts; skills/coursework lists are not bullet-budgeted entries. Zero permits a metadata-only entry where appropriate. |

All four count fields accept strict integers **0–20** or `null` (unspecified). The cap is an
input bound, not a claim that twenty projects/bullets will fit or be readable. Omitted counts
are unspecified and omitted lists are empty; no target page count, font policy, selection rule
or export preference is inferred. `resume_preferences: {}` is valid; the object/lists cannot
be `null`. Unknown settings and duplicate lists are errors, not silently ignored directives.

Validation rejects:

- Unknown required/excluded entry IDs, requiring and excluding the same entry, or requiring a
  section whose content is empty or whose background entries are all excluded.
- A minimum greater than its corresponding maximum.
- A project minimum exceeding the number of non-excluded projects.
- A project maximum smaller than the number of explicitly required projects, or zero while
  the projects section is required. A required projects section needs at least one project.

Standalone `ResumePreferences` validates local types/ranges/conflicts; the enclosing `UserProfile`
performs reference, section-availability and project-capacity checks. Preferences never approve
unverified evidence, complete unfinished work, remove source records or choose content now.
A profile may deliberately require an unfinished record, but its caveats must survive future
planning/review; completion statuses are not silently filtered here.

Passing these checks proves neither sufficient verified bullet evidence nor a feasible one-page
layout. Those remaining conflicts belong to matching/planning/rendering and must be reported,
not solved by inventing claims, dropping required content or shrinking text. Real private
preferences remain in notes until you explicitly review and enter the typed fields yourself.

#### Compatibility

This is an additive extension to **profile schema version 1**, first supported by ResumeForge
**0.5.0**. Old valid profiles need no migration and retain their source/IDs/notes; unknown-state
warnings are new. Older application versions reject the new fields, so upgrade before using
them. The application version changes; profile `schema_version` stays `1` because old field
meanings and required fields did not change. Incompatible future changes require a new format
version rather than heuristically interpreting old notes or silently rewriting private files.

### Existing verified resume bullets

```yaml
verified_bullets:
  - id: bullet_tests
    text: Added Python tests for 12 API endpoints under mentor review.
    accomplishment_ids: [acc_tests]
```

All three fields are required. IDs use `bullet_`; evidence references must be nonempty,
distinct, existing and verified. This checks the reference graph, **not semantic entailment**:
the parser cannot prove that a bullet's wording/metrics follow from its evidence. You must
review this when entering a verified bullet; claim validation will be added in Phase 4.
Historical AI output does not belong here unless independently checked against profile facts.

## Markdown notes and source fidelity

Everything after the closing `---` is preserved verbatim as `ProfileDocument.markdown_notes`.
Headings such as `## exp_internship` are useful conventions for people, but are not parsed,
validated or resolved as evidence references. Code fences, blank lines, Unicode, mixed line
endings and further `---` lines in the body are retained. The full decoded original text is
also preserved as `source_text`, including an optional leading UTF-8 BOM. This is preservation,
not a Markdown writer/serializer; there is no file-rewrite command.

## YAML subset and error handling

- UTF-8 regular local file, at most **1,048,576 bytes** including notes.
- Opening and closing `---` must each occupy their own line; no leading blank lines.
- Use spaces for indentation. Quote dates and ambiguous strings. Use lowercase `true`/`false`;
  words like `yes`, `no`, `on`, `off` remain strings, not verification flags.
- Duplicate/non-string mapping keys, anchors, aliases, merge keys and explicit tags are rejected.
  Nesting is limited to **32 collections**. YAML object construction is not permitted.
- Format errors report front-matter line/column when available; schema errors report field paths.
  Displayed errors omit input values and YAML snippets. The Python result intentionally contains
  sensitive data; do not log/print whole models, source documents or raw validation objects.

## Python interface

```python
from pathlib import Path
from resumeforge.profile import find_profile_gaps, load_profile

document = load_profile(Path("data/profile/user_information.md"))
warnings = find_profile_gaps(document.profile)
```

`parse_profile(text)` offers the same validation without file I/O. Both raise `ProfileError`
for invalid input. `UserProfile` is also exported for typed integration. All APIs are local and
independent of Typer, provider SDKs, rendering and persistent history.
