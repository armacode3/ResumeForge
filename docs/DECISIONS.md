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

**Status:** Profile schemas and provenance-link validation implemented; generation pipeline deferred.

The profile is the fact source. Pydantic profile models and stable accomplishment IDs establish
provenance for future matching, generation and validation. Historical approvals improve wording,
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

## ADR-006 — Explicit versioned profile facts plus preserved Markdown notes

**Status:** Implemented in Phase 1.

Use YAML front matter for structured fields and a Markdown body for rough notes. Alternative:
infer facts/IDs from arbitrary prose headings. Explicit structure is less forgiving to author,
but deterministic, reviewable, and independent of an LLM. A complete fictional example and
`docs/PROFILE_FORMAT.md` document the convention. Exact decoded source/body are retained;
this is not an auto-rewriting Markdown serializer.

Use a common typed background-entry shape across eight sections, with section-specific ID
prefixes and optional metadata; defer profession-specific models until real requirements arise.
Require explicit schema version 1 and a name, but allow incomplete background with warnings.
Unknown fields, duplicate IDs/keys, reversed dates and invalid evidence references are hard errors.
Dates use month precision; do not invent precision for uncertain dates. ID assignment is explicit
and stable across edits, not generated from list positions.

Accomplishments default to unverified. Verified bullet references must exist and point to
verified accomplishments; this validates the graph, not semantic entailment. The `verified`
flag records the user's assertion. Markdown notes and historical AI output do not become facts
through parsing. Missing metrics are not errors or prompts to fabricate values.

Use PyYAML with a bounded SafeLoader subset, duplicate-key rejection, explicit booleans,
no YAML object tags/anchors/aliases, and a depth cap. The CLI displays safe domain errors rather
than raw YAML/Pydantic exception dumps, while a separate gap pass reports incomplete details.
No generic Markdown parser, email-validation dependency or provider SDK is needed for this feature.
