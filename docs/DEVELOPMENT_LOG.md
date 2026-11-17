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
