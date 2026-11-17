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

## ADR-007 — Provider-neutral job contracts with explicit offline replay first

**Status:** Offline contracts implemented first in Phase 2; local inference added under ADR-008.

Use a small Python Protocol and dependency injection for structured JSON completion, not a
framework, a hard-coded remote SDK or model-generated executable tools. Requests separate
versioned trusted instructions, untrusted job text and a JSON schema. The job service has no
candidate-profile input. This tests the integration boundary without data disclosure or API costs.

The initial adapter was a fake returning an explicitly supplied fixture. Alternative:
pretend a fixed/keyword-based fake is useful semantic extraction for arbitrary jobs. Reject that
ambiguity: `analyze-job` requires `--mock-response`, identifies fake provider/model, and prints an
offline notice. Structured extraction by a real provider remains a distinct authorized feature.
The fake is also useful for repeatable failure, Unicode/layout and packaging tests.

Require literal job facts with source quotations rather than unconstrained paraphrased summaries
in this initial schema. Validate text-within-quote and quote-within-source, stable unique job IDs,
strict field types, explicit empty categories and nullable unknown metadata. Quotation existence
does not prove correct interpretation, classification or completeness; retain human review.
Hash exact source bytes and record provider/model/prompt version for later history provenance.

Fail on duplicate/nonstandard/malformed JSON and bounded size/depth violations; sanitize errors,
including provider exceptions. Call once, with no implicit retry/provider fallback. A live adapter
will need explicit network timeouts/limits and structured-output compatibility decisions.
Keep stdout machine-readable; diagnostic/mock notices go to stderr. Do not add paid dependencies
or claim live extraction is complete until an adapter is selected, approved and tested.

## ADR-008 — Explicit local-only Ollama with fail-closed inference

**Status:** Implemented following user selection of Ollama; model quality remains review-dependent.

Use Qwen3:4b initially through Ollama's HTTP API and the existing provider Protocol. The user
preferred free/local inference and approved this local setup. Alternatives: a free cloud tier
(quotas/data-use constraints, private data leaves the machine) or a larger local model (more
memory/download/latency). Do not activate a cloud fallback or pull another model automatically.

Use HTTPX rather than a provider-specific SDK so loopback address, disabled environment proxies,
no redirects, bounded response reads and timeouts are explicit and mockable. A separate server
process must report cloud disabled via `/api/status`; `/api/show` must identify a local GGUF
completion model with no remote host/model. Only then transmit job text. A trusted local server
is still required; its metadata is not cryptographic attestation or OS isolation.

Keep fake mode the default for compatibility and zero implicit inference. Ollama mode is explicit,
mutually exclusive with mock input, and uses validated model/port/time/output flags, schema-guided
non-thinking generation, no tools, conservative context budgeting, no retry and unload-on-finish.
Client cancellation does not guarantee server computation stopped; model tags are not pinned
weight digests. Runtime installation/pulls and opt-in evaluations are separate operator actions.

Map adapter failures to explicitly safe `ProviderError` messages; preserve them through the engine
without exposing server bodies. All model content still passes existing strict schema, provenance
and quotation checks. Early live trials exposed casing, absent-metadata and duplicate-ID failures;
add regression tests and refine prompt/schema descriptions rather than silently repairing facts
or weakening validators. Structured JSON and two passing examples would not prove general accuracy.

## ADR-009 — Small exact-reference evaluation before relying on extraction tags

**Status:** Implemented; the initial six-case local review is complete, not a quality approval.

Use six fictional sources and manually authored `JobRequirements` references, validated through
the same engine as model output. Compare exact case-sensitive text sets per category, ignoring
generated IDs, ordering and valid quote-length differences. Report missing/unexpected spans,
item precision/recall (undefined denominators null), separate nullable metadata checks, and all
validation failures. Do not drop invalid responses from case counts or label annotation agreement
as universal accuracy. Alternative semantic/LLM judging introduces additional model variability
and cannot prove truth; embeddings/benchmark frameworks are unnecessary for this initial corpus.

Keep the runner repository-only and default to explicit reference replay, clearly labeled as a
harness check. Independently captured raw responses can be replayed offline; their original model
identity is not inferred from the JSON. Local inference is explicit, synthetic-only and guarded
by the existing Ollama adapter. No live run, model pull, profile access or cloud fallback is a test
side effect. Unmatched alternate spans need review, not silent fact normalization or weaker
quotation checks. This does not implement matching/planning or candidate-claim approval.

The unchanged prompt-v3 Qwen3:4b single pass validated all six responses but exactly matched none
of the references. Missing tags and known metadata remain review blockers for unattended ranking;
see `docs/evaluations/qwen3-4b-v3.md`. Typed completion/preference work can proceed independently,
but future matching must use reviewed requirements or deterministic fixtures and preserve context.

## ADR-010 — Additive typed completion states and profile preferences before planning

**Status:** Implemented as the first Phase 3 prerequisite; selection/ranking/layout remain deferred.

Keep existing schema-version-1 profiles valid by adding optional `completion_status` to both
entries and accomplishments, defaulting to `unknown`. Never infer completion from prose, dates
or verification, and never propagate parent/subtask states. The exact lifecycle vocabulary is
`unknown`, `planned`, `in_progress`, `completed`, `on_hold`, `cancelled`; retain detailed qualifiers
in factual text. A verified statement of ongoing work is not proof of a completed achievement.
Unknown states warn without silently excluding content or invalidating old reviewed graphs.

Store a separate optional `ResumePreferences` object in profile front matter, not in evidence or
unparsed notes. Accept required sections/entry IDs, excluded entry IDs and nullable 0–20 integer
project/per-entry bullet bounds. Validate strict types, duplicates, min/max ordering, overlapping
instructions and existing references. Reject required empty/all-excluded sections, impossible
project minima and maxima conflicting with required project content. Standalone preference models
cannot resolve profile references; those checks belong to `UserProfile`.

Alternative: a new separate preferences file/loader or a breaking profile-version migration.
For this small local slice, one optional root object reuses the bounded parser, evidence graph
and existing read-only CLI without introducing another command or guessing private migration.
Schema version 1 remains appropriate because old inputs/field meanings stay valid; older app
versions reject added fields rather than misreading them. Application version is 0.5.0.

These constraints do not prove verified-evidence sufficiency or readable one-page feasibility.
Preferences must not approve claims, erase excluded source evidence, or override completion
caveats. Later planning must honor exclusions transitively for claims, preserve required content
or surface conflicts, and use reviewed job requirements. No model calls, ranking, generation,
font/layout policy, automatic profile edits or new dependencies are part of this feature.
