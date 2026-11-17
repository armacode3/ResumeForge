# Architecture

## Status and approach

Phases 0–1 are implemented. Everything below labeled **planned** is a design boundary, not a
working feature. Prefer a modular monolith: one Python package, with small components and
explicit typed contracts, rather than services or unnecessary infrastructure.

## Current repository

```text
src/resumeforge/
  __init__.py       installed distribution version
  __main__.py       python -m entry point
  cli.py            Typer presentation layer; help/version and validate-profile
  py.typed          typed-package marker
  profile/
    models.py       strict Pydantic schemas and evidence-reference validation
    parser.py       bounded safe YAML/front-matter parsing and source preservation
    validation.py   non-fatal missing-detail / unverified-evidence warnings
tests/
  unit/             CLI/schema/parser/gap contracts and invalid inputs
  integration/      installed entry points, profile validation, privacy safeguards
examples/profiles/   fictional comprehensive profile; shared test fixture
config/
  resume_rules.md   documented writing policy (not yet consumed)
docs/               decisions, roadmap, development log
.github/workflows/  lint, format, types, tests, build and CLI smoke checks
pyproject.toml      package, tools, dependency ranges, console script
requirements-dev.lock  exact resolved development/runtime/build dependencies
```

The `src/` layout prevents tests from accidentally importing a root-level source package that
has never been installed. Both entry points use the same Typer app. CLI commands will call
engine services, not contain parsing, provider, or rendering logic.

## Implemented profile boundary

See `docs/PROFILE_FORMAT.md` for schema version 1. YAML front matter explicitly records person,
background entries across eight categories, skills/coursework, accomplishments and verified bullets.
The Markdown body is retained as rough notes, not inferred evidence. `ProfileDocument` carries
`UserProfile`, exact decoded `source_text`, and verbatim `markdown_notes`; no writer is implemented.
The CLI calls `load_profile`/`find_profile_gaps`, which have no dependency on Typer or HTTP.

Strict Pydantic models reject unknown fields, incorrect types, invalid IDs/dates, duplicate IDs,
dangling evidence references, and verified bullets citing unverified records. Accomplishments
default to unverified. Completeness warnings cover missing contact/education/background, dates,
institutions/employers, and verified evidence. Parsing validates structure and provenance links,
not whether claims are true or semantically supported by the cited statements.
There are no typed completion-state or resume-preference contracts yet. Preserving these in
entry details/notes does not make them active planning constraints; implement validated contracts
before the matching/planning phases rely on them.

The parser accepts a bounded regular UTF-8 file (1 MiB), uses a restricted SafeLoader with duplicate
key rejection and explicit boolean behavior, and rejects anchors/aliases/tags and nesting beyond
32 collections. Errors shown by the CLI omit private input values/YAML snippets. Private source
text and models are available in memory to callers, which must not log them indiscriminately.

## Planned module responsibilities

Create these modules only as their features are implemented:

| Component | Responsibility and contract |
| --- | --- |
| `jobs/` | Accept local job text and validate structured `JobRequirements`, including required/preferred distinctions. |
| `providers/` | Configurable LLM interface, structured responses, bounded failures, deterministic fake; real provider added explicitly later. |
| `matching/` | Rank evidence by technical relevance, demonstrated responsibility, specificity and constraints, not keyword counts alone. |
| `planning/` | Produce `ResumePlan`: selected evidence, mandatory content, space budgets, review flags and concise decision explanations. |
| `generation/` | Produce structured `ResumeDocument` and bullets with supporting accomplishment IDs; never raw model-authored LaTeX. |
| `validation/` | Validate references and factual claims; produce `ValidationResult` and blocking/review flags. Later inspect PDFs. |
| `rendering/` | Escape dynamic text, render trusted versioned Jinja2/LaTeX templates, compile safely, export text and report. |
| `engine/` | Orchestrate pipeline through explicit inputs/outputs; no dependence on CLI or HTTP frameworks. |
| `history/` | SQLite generation/version metadata, approved wording and feedback; retrieval and deletion. |

## Planned data flow and models

1. Local Markdown profile -> validated `UserProfile` with stable experience/accomplishment IDs.
   The profile is the authoritative fact source; missing details become explicit gaps.
2. Local job description -> `JobRequirements`: company/title, responsibilities, required and
   preferred qualifications, languages/frameworks/concepts, and evidence sought.
3. Match verified evidence -> `ResumePlan` honoring required sections/experiences and space.
4. Generate `ResumeDocument` with evidence-linked bullets -> deterministic claim checks,
   optional AI review, and an explicit approval step for unsupported/flagged claims.
5. Render approved content -> compile -> validate exact page count, extractable text,
   expected content, corruption/empty output, and configured readability constraints.
6. Export `resume.pdf`, `resume.tex`, `resume.txt`, `tailoring_report.md`. If oversized,
   trim redundant/low-priority content before any bounded typography adjustment. Require visual review.
7. Once history is implemented, persist provenance, validation, decisions, versions and artifact
   references. Failed generations must not masquerade as approved final resumes.

Profile schemas exist now; job/plan/resume schemas remain deferred to their implementing phases.
Pydantic validates profile input and will validate untrusted model responses, which must fail actionably.
`config/resume_rules.md` holds writing policy; planned `config/layout.yaml` will separately
hold machine-readable page, spacing, and minimum-readability constraints.

## Planned memory architecture

Start with standard-library SQLite and explicit transactions/migrations. Add SQLAlchemy only
if complexity justifies it. Store generation IDs, timestamps, profile/job identifiers and hashes,
template/model/prompt/rules versions, selected evidence IDs, bullet variants, approval state,
user edits, validation findings, decision summaries, artifact paths and version lineage.
Persist concise explanations, not hidden model reasoning. Historical wording can be reused only
against current verified evidence; approval of phrasing does not establish a biographical fact.
Document artifact ownership, deletion semantics, retention and backup/privacy choices when implemented.
No vector database is needed for the initial deterministic history workflow.

## Planned templates and external integrations

Use Jake's Resume only after checking its upstream source, license and attribution. Store a
trusted versioned template, escape all dynamic LaTeX content, and keep an editable Overleaf-compatible
export. Use `latexmk` and a compatible TeX distribution, with PyMuPDF for inspection.
Page count alone cannot prove readable layout or ATS compatibility.

An eventual provider adapter may use OpenAI structured JSON outputs. No adapter, SDK, network
call, API key configuration or paid service is enabled now. Tests must use deterministic fakes.

## Security boundaries

- Private files and databases stay outside version control; examples/fixtures are synthetic.
- Profile/job/webpage contents and LLM responses are data, not executable instructions.
- Minimize provider payloads and disclose what leaves the machine before enabling real calls.
- Do not expose secrets or profile content in default logs; structured observability is future work.
- Escape LaTeX, disallow shell escape, enforce time/resource/output limits, isolate compilation;
  do not trust TeX compilation as inherently safe.
- Future URL ingestion needs SSRF protection, size limits and content validation.
- Human review is required for disputed claims and final visual layout; AI review is fallible.

## Future API, extension, and deployment

FastAPI will call the same engine and validated request/response contracts. Before exposing it,
choose authentication, authorization, artifact access, request limits, origin policy, and long-job
handling. No network service or deployment is configured in Phase 1.

The Manifest V3 extension will extract a job only on user invocation using minimal permissions
(such as `activeTab` and `scripting` if sufficient), let the user edit it, then call the secured
API to generate/preview/download artifacts and browse history. Keys stay on the backend.
Webpage instructions cannot access unrelated user data or override system rules.

Docker comes after the generation workflow. Plan a non-root image with reproducible Python/TeX
dependencies, explicit workdir, mounted inputs/outputs, no secrets, and compilation smoke tests.
Compose is optional when an API adds meaningful multi-component coordination. A cloud provider,
production deployment, multi-user authentication, and associated costs need explicit decisions.
