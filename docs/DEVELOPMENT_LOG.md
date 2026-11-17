# Development log

## Session 001 — Phase 0 foundation

- Inspected an empty, non-Git directory. Python 3.12.3 and Git 2.43.0 are available.
- A system `uv` file lacks execute permission; standard `venv`/pip works without modifying it.
- Defined a modular monolith, evidence-first pipeline boundaries, generation-MVP gates and a
  phased roadmap; deferred parser, Pydantic, AI, rendering, storage, API and Docker implementation.
- Added a typed installable Typer help/version CLI, unit/integration tests, locked tooling,
  CI quality/build checks, private-data ignores, writing policy and cross-agent documentation.
- Initial checks exposed missing subprocess coverage and a missing Hatchling `editables` helper
  in the clean non-isolated install. Enabled real subprocess coverage and locked the helper;
  reran the failing paths successfully rather than excluding them or weakening checks.
- Verification on Python 3.12.3: 7 unit tests and 3 integration tests passed; full suite passed
  with 90.91% branch-aware coverage. Ruff lint/format, strict mypy (6 source files), and
  `pip check` passed. Built sdist and wheel, inspected contents for accidental private/build files,
  validated the documented locked editable installation, then ran all 10 tests against the wheel
  from outside the repository. Wheel includes the typed marker and both working entry points.
- Git outcome: foundation recorded in an initial local commit on `main`. No remote is configured;
  no push or hosted CI run occurred. User must supply an existing repository URL and approve
  adding the remote before publishing. CI targets 3.12/3.13; only 3.12 was locally verified.
- Not attempted: live LLM calls, parsing, resume generation, PDF checks, Docker or deployment.
- Next: Phase 1 profile format, Pydantic evidence schemas and parser/validation tests.

## Session 002 — Phase 1 profile knowledge base

- Inspected a clean worktree and read the current project context. The user configured `origin`;
  remote `main` already contains the Phase 0 foundation. Worked on `feat/profile-knowledge-base`
  without changing remote settings or modifying `main`.
- Added schema version 1: explicit YAML facts in a Markdown file, eight typed background
  categories, contact/skills/coursework, stable entry/accomplishment/bullet IDs and evidence links.
  Documented the convention and supplied a fully fictional example; no real profile was created.
- Added independent profile schemas/parser/gap detection and a thin `validate-profile` command.
  Pydantic/PyYAML are direct dependencies; YAML stubs are development-only. Updated the lock
  without unrelated upgrades and bumped application metadata to 0.2.0.
- Preserve original decoded source and Markdown body, including BOM/CRLF/Unicode. Reject unknown
  fields, duplicate keys/IDs, invalid dates, dangling references and bullets citing unverified
  evidence. Verification defaults false; missing information produces warnings, not guessed facts.
- Restrict YAML object tags/anchors/aliases, cap input at 1 MiB and nesting at 32 collections,
  and display sanitized errors without source snippets or private input values. Verified labels
  and valid references do not establish semantic truth; that remains user review/Phase 4 work.
- Initial checks caught an assumption about Typer's current test runner API; replaced its absent
  filesystem helper with pytest's temporary directory/chdir fixture. Strict typing and formatting
  issues were fixed and all checks rerun, without weakening quality gates.
- Verification on Python 3.12.3: 74 unit + 9 integration = 83 tests passed; full branch-aware
  coverage 99.69%. Ruff lint/format, strict mypy (15 source files), and `pip check` passed.
  Built/inspected sdist and wheel; clean locked editable install passed both test groups;
  all 83 tests passed against the installed wheel outside the repository. A separate runtime-only
  environment passed version/help/profile smoke checks and dependency validation.
- Extended the existing CI wheel smoke test to validate the sample. Python 3.13 remains a CI
  target, not locally tested; hosted CI results have not been verified in this session.
- Next: populate/review a private profile using the format guide; then Phase 2 local job inputs,
  structured job requirements and a deterministic provider contract/fake. No live LLM calls,
  generation, PDF compilation, persistent history, API or Docker were introduced.

## Session 003 — Private narrative profile onboarding

- Reviewed an existing narrative and curated it into the supported profile format using the
  existing loader/CLI, rather than adding an importer or beginning another pipeline phase.
  The personal profile and local validation report remain exclusively under ignored `data/profile/`;
  no biographical facts, contact details, actual ID mappings or private sources enter public fixtures.
- Kept imported accomplishments pending individual user review, left disputed/unknown dates
  unset, preserved metric bounds and prototype/in-progress/authorship qualifications, and
  documented the curated import's provenance privately. Parsing does not substantiate metadata.
- Recorded planning/layout/export preferences as notes, not active configuration. Documented
  the need for validated completion-state/preferences before future selection relies on them,
  and for explicit readable-text versus verbatim-TeX-mirror export semantics.
- Added synthetic regression tests for notes not approving/completing claims, historical
  "Present" not implying current membership, and lower-bound metrics remaining qualified.
- Verification on Python 3.12.3: the private profile passes schema/reference and CLI checks;
  completeness warnings are expected while evidence/dates await review. All 86 automated tests
  passed with 99.69% branch-aware coverage; Ruff lint/format, strict mypy and dependency checks
  passed. Built sdist/wheel and checked both for private paths and contact-detail leakage.
  Private directories use mode 700 and files mode 600; Git tracks no `data/` content.
- Public changes are limited to generic guidance, roadmap/context and synthetic tests on
  `docs/profile-import-review`. Application version/API remain unchanged. Private data is
  intentionally not committed or pushed; hosted CI has not been verified in this session.
- Next: user review of provisional facts and missing dates; Phase 2 local job input and fake
  structured-analysis provider can proceed independently. No matching, rendering or live AI
  integration was added, and no resume was generated.
