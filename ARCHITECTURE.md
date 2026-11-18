# Architecture

## Status and approach

Phases 0–2 include profile validation and fake/local Ollama job analysis. Phase 3 now has typed
completion states/preferences, offline evidence eligibility/lexical retrieval and source-backed
candidate review signals. Reviewed-selection draft planning now checks count constraints and
preserves mandatory content. The first Phase 4 boundary adds structured wording drafts with
pending review and exact plan binding. Separate snapshot-bound human decisions can now attest
to individual bullet wording. Literal numeric/caveat observations now require explicit finding
acknowledgements before user approval. Controlled wording assistance now supports explicit fake
replay or opted-in local Ollama proposals with minimized source/job data and fresh inspection.
Wording quality is unevaluated. Relevance ranking, semantic claim proof and full-resume/rendering
approval are not implemented.
No cloud provider is enabled.
Everything below labeled **planned** is a design boundary, not a
working feature. Prefer a modular monolith: one Python package, with small components and
explicit typed contracts, rather than services or unnecessary infrastructure.

## Current repository

```text
src/resumeforge/
  __init__.py       installed distribution version
  __main__.py       python -m entry point
  cli.py            Typer help/version, validation, offline matching and draft planning
  inputs.py         bounded local UTF-8 loading for jobs and fake response fixtures
  py.typed          typed-package marker
  profile/
    models.py       strict Pydantic schemas and evidence-reference validation
    parser.py       bounded safe YAML/front-matter parsing and source preservation
    validation.py   non-fatal missing-detail / unverified-evidence warnings
  jobs/
    source.py       exact local job text and SHA-256 identity
    models.py       strict extracted facts, stable item IDs and source quotes
    analysis.py     request orchestration, JSON/schema/quotation checks and audit metadata
    evaluation.py   exact reference-text agreement, separate from semantic proof
    benchmark.py    fixed synthetic-case orchestration and developer argument handling
  providers/
    base.py         structured-output Protocol and separate instructions/input/schema request
    fake.py         explicit offline JSON replay, not language-model extraction
    ollama.py       guarded loopback-only structured inference via HTTPX
  matching/
    models.py       immutable retrieval decisions, overlaps and review findings
    engine.py       explicit review gate, eligibility and literal candidate retrieval
    literals.py     shared bounded case-insensitive literal-span policy
    signals.py      unweighted statement-mention and scoped metric observations
  planning/
    models.py       strict reviewed selection schema and immutable draft-plan snapshots
    selection.py    bounded safe local JSON selection loader
    engine.py       explicit assembly, mandatory placeholders and count-conflict findings
  resume/
    models.py       frozen versioned wording drafts and pending review observations
    documents.py    bounded strict draft/decision/wording response JSON loaders
    engine.py       source seeds, fresh plan binding and literal wording-change observations
    decisions.py    snapshot-bound user attestations, never full-resume/rendering approval
    findings.py     versioned finite numeric/caveat observations and provenance-bound fingerprints
    wording.py      source-bound provider proposals, minimized inputs, exact slots and fresh review
tests/
  unit/             CLI/schema/parser/gap contracts and invalid inputs
  integration/      installed entry points, profile validation, privacy safeguards
examples/profiles/   fictional comprehensive profile; shared test fixture
examples/jobs/       fictional job and hand-authored fake response; shared smoke fixtures
scripts/             repository-only synthetic evaluation runner, offline by default
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
The additive schema-version-1 extension in 0.5.0 records independent completion status on entries
and accomplishments (`unknown` by default), without deriving it from dates/notes or changing
verification. Unknown states yield review warnings. Root `ResumePreferences` records required
sections/entries, excluded entries and optional project/per-entry bullet bounds. Local constraints
validate in that model; `UserProfile` resolves references, checks available content and rejects
contradictory project capacity. No preferences are inferred and no private profiles are migrated.
These are validated input contracts; the reviewed-selection planner now preserves status caveats,
uses eligible evidence and reports count/evidence conflicts. They do not guarantee layout. Notes
are still not enforced constraints. See `docs/PROFILE_FORMAT.md` for defaults and compatibility.

The parser accepts a bounded regular UTF-8 file (1 MiB), uses a restricted SafeLoader with duplicate
key rejection and explicit boolean behavior, and rejects anchors/aliases/tags and nesting beyond
32 collections. Errors shown by the CLI omit private input values/YAML snippets. Private source
text and models are available in memory to callers, which must not log them indiscriminately.

## Implemented job-analysis boundary

`JobDocument` preserves source text and hashes its exact UTF-8 bytes. `analyze_job` constructs
versioned instructions separately from untrusted job text and injects a `StructuredOutputProvider`.
`FakeProvider` returns supplied JSON unchanged, not extracted facts inferred from the job.
`OllamaProvider` performs real local inference when explicitly selected. Fake remains default,
requiring `--mock-response`; local mode requires `--provider ollama` and cannot take that fixture.

`JobRequirements` separates responsibilities, required/preferred qualifications, languages,
frameworks, concepts, domain terms and evidence sought, with nullable company/title. All fields
are explicit. List items have globally unique `job_` IDs; every fact carries literal text and a
quote. Strict types/field validation, duplicate-key/ID checks and bounded JSON handling precede
source-quotation checks. `JobAnalysis` records source hash, provider/model and prompt version.
Unknown/missing metadata and empty results produce review warnings, not invented values.

Literal quotation checks do not establish semantic interpretation or complete extraction. The
fake does not analyze arbitrary jobs; local results are interpretations requiring review.
The user selected local-only Ollama/Qwen3:4b, not a paid/cloud adapter. The service has no profile
dependency or tool registry. Errors omit input/provider exception dumps; stdout JSON deliberately
contains selected job content. See `docs/JOB_ANALYSIS.md` for schemas, limits and safety boundaries.

The Ollama adapter uses HTTPX with a fixed literal loopback host, disabled environment proxies
and redirects, and validated CLI model/port/time/output settings. Before transmitting job text,
it requires `/api/status` to report cloud disabled and `/api/show` to identify a non-remote GGUF
completion model. It sends separate system/schema and job messages, `think: false`, no tools,
temperature/seed 0, context/output limits and unload-after-request. Context budget, shared client
deadline, per-I/O timeouts, bounded API envelopes and complete-assistant-response checks fail
closed. Static safe adapter errors remain actionable; raw server/transport bodies are not echoed.
These guards trust the local server/OS, not cryptographic attestation or process isolation.
See `docs/OLLAMA.md`; runtime installation/model pulls remain separate operator actions.

`jobs/evaluation.py` compares a validated analysis with source-grounded, manually authored
`JobRequirements`. It checks source identity/quotes again, compares exact text by category,
ignores IDs/order/quote length, and reports missing/unexpected spans with precision/recall and
separate metadata agreement. Undefined ratios remain null; a mismatch is not semantic disproof.
The repository-only `scripts/evaluate_jobs.py` runs six fixed fictional sources with explicit
failure denominators. Default reference replay tests the harness, not extraction; real local
evaluation requires explicit opt-in and existing guards. See `docs/JOB_EVALUATION.md`.

## Implemented evidence retrieval boundary

`matching.match_evidence` accepts a validated profile, exact job and manually reviewed structured
requirements, not a provider or notes. Explicit review acknowledgement and schema/source
revalidation precede retrieval. Excluded/unverified/uncertain or unfinished evidence cannot
produce candidates. Verified completed subtasks may be retrieved from in-progress parents with
explicit caveats. Only scoped accomplishment statements/technologies participate, not unscoped
skills/entry metadata or bullet wording. Literal technology mentions and full job phrases produce
review candidates, never satisfaction/entailment verdicts. No ranking or content selection occurs.
Versioned candidate signals annotate existing overlaps with literal statement spans and explicit
scoped metric records. They are not inferred responsibility, semantic support or weighted scores;
absence is unknown, not a quality judgment. Signal construction occurs only for retrieved eligible
records after the pair-budget gate. It cannot change retrieval, ordering or caveats.

The read-only `match-evidence` CLI requires explicit profile/job/requirements paths and confirmation,
performs no inference, and emits private source-derived JSON with IDs, statuses, preserved job
context and canonical model/source hashes. Findings expose required-content eligibility gaps;
allocation/layout remain deferred. A comparison-count cap fails without truncation. See
`docs/MATCHING.md` for the versioned policy and limitations.

## Implemented reviewed-selection planning boundary

`planning.plan_resume` accepts profile/job/requirements plus explicit `PlanSelection`, with separate
boolean review acknowledgements. It revalidates snapshots and recomputes matching rather than
trusting a supplied report. One selected eligible accomplishment reserves one bullet slot with
unchanged source text, stable ID, job links and caveats. No relevance scores or inferred facts
drive selection. Required entries/sections remain visible; excluded/ineligible selections cannot
enter planned content. Count conflicts never trigger silent trimming or invented evidence.

`ResumePlan` is an immutable, independently versioned draft with count-budget actuals/bounds,
source/selection hashes, complete job items and actionable findings. Metadata-only and unscoped
content remain review needs; all plans stay `needs_review`, even when counts pass. No page/line
feasibility or wording approval is claimed. The read-only `plan-resume` CLI requires four explicit
paths and acknowledgement, emits private JSON, and exits 3 for a conflict-bearing draft (0 for a
draft without detected conflicts, 1 for safe input errors). See `docs/PLANNING.md`.

## Implemented wording-draft boundary

`resume.review_resume` rebuilds the plan from original inputs and explicit review acknowledgements.
It either seeds complete unchanged source statements or revalidates a submitted `ResumeDocument`.
The document binds a canonical plan hash and must preserve every planned section/entry/evidence
slot in order. Frozen nested records use immutable tuples; no input can declare itself approved.
Every bullet has one selected accomplishment reference and remains `pending_review`.

Literal comparison distinguishes unchanged source text from edited wording, not supported from
unsupported claims. Plan conflicts block the outer review; semantic proof remains deferred.
The read-only `review-resume` command emits
private documents/review context, not renderable output. See `docs/RESUME_DRAFTS.md`.

`resume.apply_review_decisions` requires original inputs, an explicit draft, a strict decision file
and separate exact-boolean confirmation. It freshly recomputes inspection and checks policy,
document/plan hashes and every referenced bullet. Missing decisions stay pending, rejection keeps
content visible, and plan conflicts block approvals. No input report supplies trusted approval.
The output records narrow user attestations separately from pending draft/inspection state, with
mandatory `rendering_authorized: false`. This is not identity authentication, semantic proof or
metadata/job-fit approval. Version-2 decisions additionally bind the current finding fingerprint;
unknown/cross-bullet acknowledgements fail and unacknowledged findings keep approvals pending.
`resume.findings` compares only selected statements with draft wording, using literal numeric
tokens and a finite cue vocabulary. Exact spans and empty/acknowledged findings are observations,
never semantic verdicts. Limits fail closed, not truncated. See `docs/REVIEW_DECISIONS.md` and
`docs/CLAIM_FINDINGS.md`.

`resume.suggest_wording` first seeds a fresh reviewed plan from original sources. Conflicted or
empty plans return that inspection without a provider call. Otherwise one structured request sends
only selected source statements, stable bullet/evidence IDs, status caveats, snapshot hashes and
complete reviewed job items/quotes/categories. Contact, notes, metadata fields and old wording are
excluded. Separate trusted instructions prohibit fact invention/transfer; job data is not evidence.
Explicit data-use confirmation precedes provider access; the CLI defaults to fake replay and
requires separate `--confirm-local-data` for guarded local inference. No new cloud path exists.

The provider returns only snapshot hashes and exactly ordered bullet IDs/evidence references/text.
Code owns section/entry/status structure, replaces only wording and runs fresh inspection. Stale,
missing, extra, reordered, self-approved, malformed or excessive responses fail without partial
success/retry. All proposals stay pending; old decisions do not transfer to changed wording.
Reports record provider/model, prompt/policy versions and request/raw-response hashes, not raw
prompt logs or semantic truth. No persistence/rendering is added. See `docs/WORDING_ASSISTANCE.md`.

## Planned module responsibilities

Create these modules only as their features are implemented:

| Component | Responsibility and contract |
| --- | --- |
| Other provider adapters | Add only when explicitly approved; retain structured interface, data disclosure, limits and safe failure policy. No automatic fallback. |
| Matching ranking | Evaluate relevance ordering beyond the implemented source observations; never rank by keyword/metric counts alone. |
| Planning extensions | Add evaluated automatic relevance selection and actual space/layout budgets beyond reviewed-selection count plans. |
| Generation extensions | Extend current source-bound wording assistance only after evaluation; complete resume metadata and rendering authorization remain separate, never raw model-authored LaTeX. |
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

Profile/job/selection schemas, draft-plan snapshots and narrow evidence-linked wording-draft
schemas and narrow human bullet-wording decisions now exist. Complete renderable resume content,
metadata review and rendering authorization remain deferred.
Pydantic validates profile input and untrusted structured job responses, which fail actionably.
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

Local Ollama inference uses HTTPX, not a paid SDK/API key. A future cloud adapter needs a separate
provider/data/cost decision. Fake replay remains deterministic and does not extract requirements.
Normal tests use mocked HTTP or a synthetic loopback server, not live models or remote APIs.

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
handling. No application API/deployment is configured in Phase 2; local Ollama is a separate runtime.

The Manifest V3 extension will extract a job only on user invocation using minimal permissions
(such as `activeTab` and `scripting` if sufficient), let the user edit it, then call the secured
API to generate/preview/download artifacts and browse history. Keys stay on the backend.
Webpage instructions cannot access unrelated user data or override system rules.

Docker comes after the generation workflow. Plan a non-root image with reproducible Python/TeX
dependencies, explicit workdir, mounted inputs/outputs, no secrets, and compilation smoke tests.
Compose is optional when an API adds meaningful multi-component coordination. A cloud provider,
production deployment, multi-user authentication, and associated costs need explicit decisions.
