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

## Phase 0 — Engineering foundation (complete locally)

- Package and CLI help/version; no placeholder generation commands.
- pytest unit and installed-entry-point integration tests, Ruff, strict mypy, coverage.
- Locked dependencies and source/wheel build checks; GitHub Actions for Python 3.12/3.13.
- Architecture, decisions, policy, agent guidance, contributor workflow, privacy defaults.
- Gate: clean local checks and initial commit; push only if a configured remote permits it.

Verified on Python 3.12.3: 7 unit and 3 integration tests, 90.91% branch-aware coverage including
subprocesses, Ruff lint/format, strict mypy, dependency checks, source/wheel builds, clean editable
installation, and wheel-installed tests outside the repository. No Git remote is configured;
push and hosted CI are blocked. Python 3.13 is configured in CI but not locally verified.

## Phase 1 — Profile knowledge base (next)

Suggested first feature: document a Markdown/YAML-front-matter convention and validate a small
sanitized profile with Pydantic, stable experience/accomplishment IDs, and actionable errors.
Then add remaining sections and `validate-profile` incrementally.

Gate: round-trip/source evidence preservation, duplicate/dangling IDs rejected, required-field
and malformed-file tests, Unicode and rough-note handling, synthetic fixtures only. Include
contact, education, experience, projects, skills/tools, coursework, certifications, awards,
organizations, research, quantitative accomplishments and verified bullets in the design.

## Phase 2 — Local jobs and structured analysis

Accept local text/Markdown, introduce provider contracts and deterministic fakes, validate job
requirements and malformed responses, separate required/preferred qualifications. Decide on
a real provider before enabling external calls. Gate: unit/integration tests without API costs.

## Phase 3 — Matching and planning

Rank evidence beyond keywords, honor mandatory sections/experiences, produce structured plans
with evidence references, space budgets and review flags. Gate: deterministic selection/ranking
and contradictory-constraint tests; explanations correspond to actual decisions.

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
