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

## ADR-011 — Offline candidate retrieval before ranking or claim approval

**Status:** Implemented in 0.6.0; semantic qualification, ranking and resume planning remain deferred.

Use explicit manual job-review acknowledgement, source/schema revalidation and versioned
deterministic retrieval before selecting resume content. Only verified, completed accomplishments
with non-excluded completed/in-progress parents are eligible; completed subtasks retain the
parent's in-progress caveat. Other statuses require review rather than inferring completion from
dates/prose. Required preferences cannot approve evidence, and excluded records cannot re-enter
via independently matched bullet wording.

Literal technology mentions from scoped accomplishment metadata and full job phrases found in
verified statements yield **lexical candidates**, not satisfied qualifications. Keep all job
categories, complete qualification text and quotes so preferences, alternatives and negation
are not converted into mandatory skill lists. Do not inherit technologies from unscoped skills,
parent entries or historical wording. No stemming, aliases, embeddings, LLM judging, numeric
relevance score or keyword-count ranking is justified for this first retrieval boundary.

Return immutable typed decisions, stable IDs, exact overlap spans, canonical input hashes and
explicit required-content review findings. Missing lexical matches are not missing experience
or proof of job absence. Preserve all inputs; enforce a pair-comparison guard without truncation.
The offline CLI requires explicit file paths and acknowledgement, no default private-profile
access and no provider selection. Existing JSON validation is reused with deterministic replay
to ingest reviewed requirements, not to imply extraction or record an inferred model provenance.

This remains a human-reviewed retrieval aid. False positives from negation/common words and
false negatives from wording are expected limits. Later ranking must use additional evidence
signals and selection must honor required/excluded content, budgets and readable layout; candidate
retrieval is not permission to author or approve claims. See `docs/MATCHING.md`.

## ADR-012 — Source-backed observations before relevance scoring

**Status:** Implemented in 0.7.0; relevance ordering/weights and resume planning remain deferred.

Annotate only already-retrieved eligible candidates with immutable, independently versioned
signals. Reuse existing full-phrase/technology overlaps and the same literal boundary policy;
distinguish technology mentions in the scoped statement from metadata-only overlaps. Preserve
explicit accomplishment metric records and show nullable literal statement spans. Stable IDs,
exact labels/spans and complete statements provide inspectable provenance without inventing
quantities, ownership, responsibility, scale, relevance or semantic proof.

Do not introduce arbitrary weights, keyword/metric-count ranking, action-verb quality heuristics
or LLM judging. Metrics need not be numeric or aligned with the statement/job; a negated mention
still has a literal span. Nulls/empty fields are unknown, not penalties or proof of absent skills.
Neither numbers in prose nor parent/bullet/skill metadata supply inferred facts. Signals cannot
create candidates, bypass eligibility/review/budget gates, change ID order or approve claims.

This small step exposes useful distinctions for manual review while keeping future scoring
policy separate. Synthetic tests check source agreement and invariants, not semantic or ranking
quality. `matching_version` stays v1 for unchanged retrieval; additive report fields identify
`signals_version: evidence-signals-v1`. Profiles need no rewrite. Output gains scoped candidate
metric text and remains private. See `docs/MATCHING.md` for the exact contract and limitations.

## ADR-013 — Explicit reviewed selections before automatic planning/ranking

**Status:** Implemented in 0.8.0; automatic relevance selection, wording and layout remain deferred.

Use a separate version-1 `PlanSelection` JSON contract for deliberate entry/accomplishment choices
and an optional total bullet-slot cap. Existing typed profile preferences constrain that selection.
One selected eligible accomplishment reserves one slot; it is not approved resume wording.
Alternative automatic count/keyword/metric-based selection would imply an unchosen ranking policy
and silently trade off evidence/content. Keep selection explicit instead; choose no arbitrary
weights or default page/slot limits. No new dependency or profile migration is necessary.

Revalidate snapshots and freshly run the reviewed-input matcher, not a caller-supplied report.
Unknown/cross-parent selection references fail safely. Excluded or ineligible evidence produces
explicit conflicts and no planned claim text. Omitted required entries/sections remain visible
as placeholders; do not choose accomplishments or arbitrary entries to fill them. Metadata and
unscoped sections require review. Unknown statuses/ongoing-parent caveats remain explicit.

Check project/per-entry counts plus the selection's total cap, preserving eligible selected and
required content on over-budget drafts. Report actuals/bounds, insufficient slots and unselected
required sections without fabricating support, relaxing constraints, trimming mandatory content
or shrinking typography. These are count constraints, not line/page/readability guarantees.

Return immutable `ResumePlan` snapshots with evidence/source/selection identity, full job context,
literal associations, budgets and findings. All plans remain `needs_review`; no claim or requirement
is declared approved/satisfied. A draft with conflicts exits 3; invalid inputs exit 1 with no partial
JSON; no-conflict drafts exit 0 but are not generation-ready. Explicit confirmation precedes all
CLI input I/O. No default private profile, inference, automatic writes or live services are added.
See `docs/PLANNING.md` for selection ordering, privacy and the intentional sample conflict.

## ADR-014 — Plan-bound wording drafts remain pending, including verbatim seeds

**Status:** Implemented as a Phase 4 prerequisite in 0.9.0; semantic checks and approval deferred.

Add a strict version-1 `ResumeDocument` boundary before model-assisted wording or rendering.
Recompute the reviewed-selection plan from source snapshots, then bind its canonical hash and
require exact section/entry/evidence-slot alignment. Preserve mandatory metadata placeholders,
full source statements and status caveats in review context. Do not trust supplied plan reports,
historical wording, claimed approval flags or copied hashes as evidence eligibility/claim proof.

Allow a deterministic source seed or submitted wording on the existing one-accomplishment/slot
model. All bullets stay `pending_review`; documents can only declare `needs_review`. Distinguish
literal `verbatim_source` from `edited_requires_review`, not semantic correctness. Flag every edit
without pretending a verb/number/technology heuristic proves support or detects every fabricated
claim. Even full source agreement cannot approve biography, metadata, qualifiers or resume fit.

Use frozen nested models/tuples, strict bounded JSON, safe errors and independently versioned
review output. Source seeds beyond draft limits fail rather than truncate facts. Preserve plan
conflicts as `blocked_by_plan` with exit 3; conflict-free reviews exit 0 but remain unapproved.
The offline command requires explicit source paths/review acknowledgement before I/O, accepts
only the inner document as optional draft input, and performs no inference, rendering or writes.

Next, human review decisions must bind exact wording and evidence snapshots; neither IDs nor old
review flags can transfer approval to changed content. No new dependency/profile migration,
automatic relevance ranking, semantic entailment guarantee or live-provider activation is added.
See `docs/RESUME_DRAFTS.md` for the exact contract, hashes, limitations and privacy boundaries.

## ADR-015 — Separate user attestations bind current bullet wording, not a whole resume

**Status:** Implemented in 0.10.0; semantic checks, metadata review and rendering remain deferred.

Accept a distinct strict decision file with inspection version, canonical plan/document hashes,
unique bullet IDs, approve/reject choices and required reasons. Require separate explicit caller
confirmation, original sources and an explicit draft; do not approve implicit seeds, trust prior
reports or let draft text declare itself approved. Rebuild inspection before applying decisions.

Whole-document binding conservatively invalidates earlier decisions after any wording/source/
plan change. Unknown, duplicate, stale or detached references fail closed. Missing decisions stay
pending, even for verbatim wording. Rejections retain content rather than silently dropping required
material. Plan conflicts block every attempted approval. Empty documents never pass by vacuity.

Keep pending draft/inspection records unchanged and return immutable, separate applied-decision
records. Only nonempty wholly approved wording under a conflict-free plan yields
`bullet_wording_approved_by_user`; scope is always `bullet_wording_only` and rendering authorization
is always false. This represents local unsigned user attestations, not authenticated identity,
semantic truth, promoted biography, metadata/job-fit review, final-resume approval or a history DB.

Extend the existing offline command with optional decisions and separate confirmation. Validate
option combinations before I/O, preserve safe failures and bounded JSON, write no input files,
and call no model. No new dependency or profile/draft schema rewrite is needed. See
`docs/REVIEW_DECISIONS.md` for exact status/exit behavior, snapshot limitations and privacy.

## ADR-016 — Finite literal findings with explicit snapshot-bound acknowledgement

**Status:** Implemented in 0.11.0. Semantic proof and model-assisted wording remain deferred.

Observe numeric-token additions and removal of a published finite caveat vocabulary against only
the selected accomplishment statement. Preserve exact Unicode string spans, full source context,
independent finding policy, deterministic provenance-bound IDs and an ordered snapshot fingerprint.
Do not classify factual support, inherit other fields as evidence, rewrite wording, or treat an
empty finding list as safety. Synthetic characterization includes false alarms and deliberate misses;
it measures literal-rule behavior, not semantic precision/recall. Fail on excessive observations,
never truncate them. No model, dependency, source migration or retrieval change is required.

Bump inspection/decision policy to v2 and decision schema to 2; draft/profile schemas stay intact.
Require current findings fingerprint and explicit per-bullet acknowledged IDs. Reject old formats,
stale fingerprints, duplicate/unknown/cross-bullet acknowledgements. Requested approvals with any
unacknowledged finding remain pending. Missing decisions, rejection and plan-conflict precedence
remain intact. Applied records expose acknowledged/unacknowledged IDs; findings stay visible even
on user approval. Acknowledgement is an unsigned attestation, never resolution or semantic proof.

This conservative contract is preferable to a broad unsupported-claim classifier without measured
quality or an LLM judge treated as truth. Full-resume/metadata approval and rendering remain outside
scope. Changed observation policies need explicit versioning; do not mechanically upgrade historical
decisions. See `docs/CLAIM_FINDINGS.md` and `docs/REVIEW_DECISIONS.md`.

## ADR-017 — Source-bound wording proposals, never provider-owned plans or approvals

**Status:** Implemented in 0.12.0; real-model wording quality has not been evaluated.

Reuse the existing structured-output provider Protocol and guarded local Ollama adapter, with
explicit offline replay as the default. Revalidate original sources and reviewed selections, seed
from entire scoped statements, and skip provider calls for conflicted/empty plans. Never feed old
bullet wording, user decisions, notes or parent metadata back as biographical evidence.

Minimize the request to selected statements/IDs/status caveats, snapshot hashes and complete
reviewed job items with categories/quotes/lexical associations. Keep trusted versioned instructions
separate; job context cannot supply candidate facts. Wording changes involve profile-derived data,
unlike job analysis, so require separate explicit `--confirm-local-data` for local mode in addition
to source-review acknowledgement. No contact fields, cloud fallback, runtime/model setup, implicit
inference, automatic retries or new dependencies. No live inference/private data was used to
implement this feature; mock tests are not model-quality or injection-resistance evidence.

Accept only a strict snapshot-bound list containing one text per existing bullet/evidence pair in
the same order. Code owns structure, metadata placeholders and pending states. Reject omission,
reordering, reference changes, self-approval, unknown fields and bounded-input violations. Rebuild
inspection after substitution, retaining findings and caveats. All wording stays pending; unchanged
text gains no new approval, and changed text invalidates prior document-bound decisions.

Record prompt/policy versions, provider/model and request/raw-response digests in an immutable
result, not raw prompt logs or stored source facts. Hashes are not identity, pinned weights, semantic
support or evidence that the provider obeyed its instructions. Suggestions may still transfer facts
between bullets, hallucinate, lose qualifiers or fail strict schema/budgets. The existing finite
findings cannot certify support. Full-resume/metadata approval, rendering, history and automatic
ranking remain separate. Next is an explicitly opted-in synthetic wording-quality evaluation.
See `docs/WORDING_ASSISTANCE.md`.
