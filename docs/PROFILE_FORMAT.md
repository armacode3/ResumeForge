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
nonblank `statement`. Optional: `technologies`, `metrics` (lists of strings), `verified`
(boolean, **defaults to false**). Store scope, units and qualifiers in metric strings; quote
purely numeric values to keep them strings. Metrics are never required. Multiple accomplishments
can point to the same entry; all categories, including awards and research, can have evidence.

`verified: true` means **you have reviewed the source facts**, not that software checked them
against external records. Unverified records are retained and flagged, not promoted into usable
evidence. Missing verified evidence for any entry produces a warning. Keep unsupported impact,
ownership, technologies and measurements out of verified statements.

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
