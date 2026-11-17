# Architectural decisions

## ADR-001 — Modular monolith with an interface-independent engine

**Status:** Accepted for Phase 0.

Use one Python package with a thin Typer boundary and future focused domain modules.
The alternative, building FastAPI/extension/services first, adds deployment and security
complexity before the core workflow works. A shared engine later supports CLI and API callers.
Do not create empty module hierarchies just to mirror the long-term design.

## ADR-002 — Installable `src/` package and explicit engineering gates

**Status:** Implemented in Phase 0.

Use Hatchling, `pyproject.toml`, Python 3.12+, Typer, pytest, Ruff, strict mypy, and GitHub Actions.
An editable install supports development; tests from outside the repository and a wheel smoke
test verify packaging rather than relying on `PYTHONPATH` tricks. Metadata is the version source.
Alternatives: a root-level script (easy initially, harder to reuse/test) or larger scaffolding
frameworks (unnecessary). Start with 90% branch-aware coverage, not coverage as a correctness claim.

Use standard-library `venv` and pip for accessible setup. A pip-compatible exact-version snapshot
pins runtime, development and build tools; supported ranges remain in `pyproject.toml`.
The snapshot is not hash-verified and must be tested across CI interpreters. Alternative dedicated
lock tooling may become worthwhile later; do not require a system `uv` installation now.
Include Hatchling's dynamic `editables` helper in development dependencies so the documented
locked, non-isolated editable install works in a fresh environment, not only an existing one.

## ADR-003 — Evidence-first data and human review

**Status:** Accepted design; pipeline deferred.

The profile is the fact source. Future Pydantic models and stable accomplishment IDs carry
provenance through matching, generation and validation. Historical approvals improve wording,
not verified biography. Prefer deterministic checks plus explicit human review over treating
an LLM's self-review as proof. Keep rules separate from machine-readable layout constraints.

## ADR-004 — Add infrastructure only at the point of need

**Status:** Accepted design; implementations deferred.

Use Jinja2 and trusted Jake's Resume LaTeX after license review, then `latexmk`/PyMuPDF.
Use SQLite for initial history; defer ORM and vector database until justified. Add provider SDKs,
Docker, FastAPI and the extension only in their roadmap phases. This reduces dependencies,
testing costs and attack surface. No cloud provider or production deployment is selected.

## ADR-005 — Private by default

**Status:** Git safeguards implemented; runtime safeguards deferred with features.

Ignore private inputs, artifacts, databases and secrets; track synthetic fixtures separately.
Document untrusted-content boundaries before enabling providers, URL ingestion or compilation.
Git ignores are not encryption or a substitute for staged-diff review. Provider data disclosure,
history deletion, compiler isolation and API access control require tests when implemented.
No project license is assumed on the user's behalf; decide before public distribution.
