# Roadmap

## Scope and MVP

Build one small verified feature per iteration. A useful **generation MVP** ends at Phase 5:
one user, a local validated Markdown profile, one local job file, evidence-based tailoring,
explicit review of flagged claims, and PDF/TeX/text/report exports using one template.
It must work with a deterministic fake provider in tests; real-provider activation and its
data/cost implications require discussion. It is not a web service or application bot.

MVP acceptance: stable fact references; schema-valid requirements and resume; no knowingly
unsupported approved claims; actionable missing-evidence errors; safe template rendering;
successful compilation; exactly one page with extractable expected text and readability
constraints; manual factual/visual review; deterministic end-to-end smoke test. No universal
ATS or automated factual-correctness guarantee. The first practical release adds Phase 6 history.

## Phase 0 — Engineering foundation (complete)

- Package and CLI help/version; no placeholder generation commands.
- pytest unit and installed-entry-point integration tests, Ruff, strict mypy, coverage.
- Locked dependencies and source/wheel build checks; GitHub Actions for Python 3.12/3.13.
- Architecture, decisions, policy, agent guidance, contributor workflow, privacy defaults.
- Gate: clean local checks and initial commit; push only if a configured remote permits it.

Verified on Python 3.12.3: 7 unit and 3 integration tests, 90.91% branch-aware coverage including
subprocesses, Ruff lint/format, strict mypy, dependency checks, source/wheel builds, clean editable
installation, and wheel-installed tests outside the repository. The user subsequently configured
`origin`; remote `main` contains the foundation commit. Python 3.13 is configured in CI but
not locally verified.

## Phase 1 — Profile knowledge base (complete locally)

Implemented: documented version-1 Markdown/YAML convention, strict Pydantic schemas for all
background categories, stable IDs and evidence links, safe bounded parser, exact source/body
preservation, completeness warnings, `validate-profile`, fictional sample, and automated tests.
No profile rewriting, prose fact extraction or semantic claim checking is implied.

Gate: round-trip/source evidence preservation, duplicate/dangling IDs rejected, required-field
and malformed-file tests, Unicode and rough-note handling, synthetic fixtures only. Include
contact, education, experience, projects, skills/tools, coursework, certifications, awards,
organizations, research, quantitative accomplishments and verified bullets in the design.

Verified on Python 3.12.3: 74 unit and 9 integration tests, 99.69% branch-aware coverage, Ruff
lint/format, strict mypy, dependency checks, source/wheel builds, fresh locked editable install,
all tests against the installed wheel outside the repository, and a runtime-only wheel/profile
smoke test. No live services or private profile data were used. Hosted CI is not locally verified.

## Phase 2 — Local jobs and structured analysis (local adapter implemented)

Accept local text/Markdown, introduce provider contracts and deterministic fakes, validate job
requirements and malformed responses, separate required/preferred qualifications. Decide on
a real provider before enabling external calls. Gate: unit/integration tests without API costs.

Implemented: bounded local UTF-8 job/response inputs, source hashes, strict quoted requirement
schemas and IDs, provider Protocol, deterministic explicit fake replay, malformed-response and
quotation checks, `analyze-job`, fictional fixtures, and installed-CLI tests. See `docs/JOB_ANALYSIS.md`.
The fake does not extract requirements from arbitrary jobs. The user selected local-only Ollama
with Qwen3:4b. Its adapter now enforces loopback/no-proxy/no-redirect operation, server cloud
disablement, local-model checks, bounded context/response/time/output and complete-message checks.
See `docs/OLLAMA.md`. No cloud adapter, automatic install/pull, retry or inference fallback exists.
**Quality boundary:** evaluate local extraction on varied synthetic jobs and review classification,
coverage and failures without weakening fact validation. Larger/different models or cloud use
require deliberate resource/data decisions; normal tests must stay independent of real models.

Offline-slice verification on Python 3.12.3: 151 unit + 16 integration = 167 tests passed,
99.83% branch-aware coverage, Ruff lint/format, strict mypy, dependency checks and package builds.
Fresh locked editable installation, all tests against the installed wheel outside the repository,
and runtime-only help/profile/job smoke tests passed. Hosted CI/Python 3.13 are not locally verified.

Local-adapter verification on Python 3.12.3: 212 unit + 20 integration = 232 tests passed,
99.87% branch-aware coverage, lint/format/types/dependency checks and package builds. Normal tests
use only mocks or synthetic loopback HTTP. Separately, two fictional live examples passed strict
schema/quote/basic-metadata checks with Qwen3:4b and prompt v3 after earlier failures were caught;
manual review still found incomplete taxonomy tags. This is not a general accuracy certification.

Added in 0.4.1: exact-reference evaluation and a six-case synthetic corpus, with offline replay
as the default and explicit validation/mismatch counts. Saved Qwen3:4b outputs agree on 9/10 and
5/6 annotated items, exposing the known testing/SQL tag omissions. Reference replay alone does
not close the model-quality gate.
See `docs/JOB_EVALUATION.md`. The help-assertion repair passed hosted Python 3.12/3.13 CI before
the user merged Phase 2 into main; local and hosted results for this evaluation slice are separate.

The subsequently requested single-pass local review is complete: **6/6 schema/quote-valid results,
0/6 exact reference matches**; five cases had correct nullable metadata, while the footer case
lost known company/title. Tag omissions were widespread; a shortened SQL preferred span retained
its modifier only in the quote. No preference promotion or injected employer was observed in this
limited run. See `docs/evaluations/qwen3-4b-v3.md`. This is **not** approval for unattended ranking.
Typed completion-state/preferences can be developed independently of model quality; later
matching uses reviewed requirements or deterministic fixtures, never model tag absence as proof.

## Phase 3 — Matching and planning (typed input prerequisite implemented)

Rank evidence beyond keywords, honor mandatory sections/experiences, produce structured plans
with evidence references, space budgets and review flags. Gate: deterministic selection/ranking
and contradictory-constraint tests; explanations correspond to actual decisions.
Implemented in 0.5.0: independent entry/accomplishment completion states (default unknown) and
root typed resume preferences for required/excluded content and optional project/per-entry bullet
bounds. Old version-1 profiles still validate; no dates, facts or preferences are inferred from
notes. The profile boundary rejects bad references, empty/all-excluded required sections and
contradictory ranges/project counts. Unknown states warn; completion does not imply verification.
See `docs/PROFILE_FORMAT.md` and ADR-010. No private profile was migrated.

**Next:** deterministic evidence eligibility/matching using reviewed job requirements, these
constraints and verified source evidence. Ranking, selection and `ResumePlan` are not implemented
yet. Preserved Markdown notes are not enforced constraints. Later planning must also surface
insufficient evidence and mandatory-content/readable-one-page conflicts; validated counts alone
cannot guarantee layout feasibility.

## Phase 4 — Bullets, claims and review

Generate structured bullets with accomplishment IDs, check unsupported tools/metrics/ownership,
dates and contradictions, report gaps, and implement review/approval. Gate: fabricated-claim
regressions and actionable validation failures; approved content is separately represented.

## Phase 5 — Trusted rendering and PDF (generation MVP)

Verify Jake's Resume license/attribution; version a Jinja2 template; escape content; enforce
compilation limits; export PDF/TeX/text/report; validate content/page count/readability; bound
content reduction. Add layout config, TeX/PDF integration tests and isolated CI compilation
smoke test. Gate: complete deterministic generation, explicit tool prerequisites and manual review.

## Phase 6 — Persistent history (first practical release)

SQLite schema/migrations, generation and resume lineage, provider/rules/template provenance,
selected IDs, approved wording, edits, validation, decisions and artifact paths. Implement
history/retrieval/comparison and deletion incrementally. Gate: persistence, rollback, migration,
version comparison and privacy tests; historical output never becomes verified fact automatically.

## Phase 7 — Docker and production readiness

Non-root reproducible image with TeX, mounted private data, no secrets; container smoke test
in CI; operational documentation, bounded failures and privacy-conscious logs. Keep local setup.
No automatic cloud deployment. Compose only when it adds value.

## Phase 8 — FastAPI and Manifest V3 extension

Choose API security/access model first. Reuse engine contracts; support preview/download/history.
User-invoked extraction with minimal permissions and editable job preview; treat webpages as
untrusted. Keep secrets server-side. Gate: API integration, authorization and extension E2E tests.

## Phase 9 — Optional enhancements, not commitments

Additional professions/templates, batch runs, comparison UI, preferences, assisted profile
questions, cover letters, application tracking, semantic retrieval only if needed, multi-user
authentication, and explicitly chosen hosting. Reassess value and scope before starting.
