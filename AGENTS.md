# ResumeForge agent instructions

## Start every session

Read `README.md`, `ARCHITECTURE.md`, `docs/DECISIONS.md`, `docs/ROADMAP.md`, and
`docs/DEVELOPMENT_LOG.md`. Inspect `git status`, the current branch, recent history, and
configured remotes. Preserve unfamiliar changes. This file is the canonical agent guidance;
do not create conflicting duplicate instructions.

## Purpose and current state

Build truthful, evidence-linked resumes from a verified Markdown profile and a job description.
Phases 0–2 include profile validation, local job loading, provider Protocol, fake JSON replay,
guarded local Ollama inference, structured requirements, quotation checks and `analyze-job`.
Phase 3 includes optional completion states/preferences and offline evidence eligibility/lexical
retrieval with source-backed candidate review signals and explicit reviewed-selection count plans,
not relevance ranking, wording generation or layout feasibility.
Phase 4 has plan-bound wording drafts/source seeds, pending literal-change observations and
snapshot-bound user bullet-wording decisions plus literal numeric/caveat findings, not semantic
proof or full-resume approval. Read `docs/RESUME_DRAFTS.md`, `docs/REVIEW_DECISIONS.md` and
`docs/CLAIM_FINDINGS.md`.
Controlled source-bound wording proposals now use fake replay or explicitly acknowledged local
inference, always followed by fresh inspection. Read `docs/WORDING_ASSISTANCE.md`; the initial
six-case local pass validated all responses but copied all seven statements, so useful rewriting
remains unproven. See `docs/evaluations/qwen3-4b-wording-v1.md`. No live run is a normal test or
implicit continuation step.
The fixed synthetic wording evaluation runner defaults to source-seed replay, not model-quality
scoring. Read `docs/WORDING_EVALUATION.md`; live runs and runtime/model setup need separate opt-in.
`source_faithful` remains the original default. Opt-in `concise_rewrite` uses wording/prompt v2,
same data/response schemas and review gates, no forced edits or length quotas. Separate rough-source
development/evaluation suites are described in `docs/WORDING_REWRITE_EVALUATION.md`; preserve the
original frozen benchmark/protocol/results. Length/edit counts are not quality or support scores.
The paired local comparison shortened all four evaluation bullets but distorted negative qualifiers/
project relationships. Keep v2 experimental/opt-in and v1 default; see
`docs/evaluations/qwen3-4b-wording-v2-comparison.md`. Do not tune/rerun this frozen comparison or
treat zero findings/acknowledgements as semantic support.
Offline inspection v3 now includes independent literal source-fragment absence observations, not
semantic omissions. Read `docs/SOURCE_FRAGMENT_REVIEW.md`. Decision schema/policy v3 binds fragments
and requires per-fragment user dispositions: exact draft passage, accepted omission with rationale,
or needs revision. Missing/revision dispositions stay pending even with all old findings acknowledged.
Exact spans do not prove equivalence; accepted omissions do not prove qualifier safety. Keep source
observations visible, reject old attestations without automatic upgrade, and preserve prompt/data/
response contracts.
Offline `review-resume --draft ... --worksheet` now emits fresh review and a null-only pending
decision template. Read `docs/REVIEW_WORKSHEETS.md`. Never prefill choices, reasons, finding
acknowledgements, fragment dispositions or draft links; copy only current bindings/IDs. The envelope
is not draft/decision input. Users extract/complete/remove pending records and still use explicit
decision confirmation and unchanged v3 gates. No prior approvals are imported or migrated. Keep
the complete default worksheet bounded and private.
Separate offline `review-metadata` now exposes only explicitly selected contact/planned-entry
fields as pending source copies bound to current wording and field selection. Read
`docs/METADATA_REVIEW.md`. Require all original sources, explicit draft and all three review flags;
reject unknown/unselected/excluded entries. No implicit name/contact disclosure in other commands
or providers, no metadata editing/approval or transfer from bullet decisions. Missing values stay
null/empty; recorded present and completion status stay independent. Links are model-normalized,
never fetched. Keep metadata private and bounded. Next: separate per-field metadata attestations,
then structured-resume completion, not implicit inference or rendering authorization.
Omitted states stay unknown; version-1 profile/draft files need no rewrite (not old decisions).
Read `docs/MATCHING.md` for the
retrieval boundary.
Read `docs/PROFILE_FORMAT.md`, `docs/JOB_ANALYSIS.md`, and `docs/OLLAMA.md` as applicable.
The fake is not extraction; local model results may fail validation or be incomplete. Do not imply
cloud inference, resume generation, semantic claim proof, PDFs or history already work.

## Stack and repository map

- Python 3.12+, Typer, Pydantic, PyYAML, HTTPX, pytest, Ruff, strict mypy; locked dependencies.
- `src/resumeforge/`: installed application; `cli.py` is the presentation boundary.
- `src/resumeforge/profile/`: schemas, bounded safe parser, source preservation, completeness flags.
- `src/resumeforge/jobs/`: source identity, extraction/quotation validation and exact-reference evaluation.
- `src/resumeforge/providers/`: Protocol, fake replay and local-only Ollama HTTP adapter.
- `src/resumeforge/matching/`: reviewed-input gate, eligibility, lexical candidates and review findings.
  Candidate signals preserve literal statement mentions and scoped metric records, not scores.
- `src/resumeforge/planning/`: strict explicit selections, immutable draft plans and count conflicts.
- `src/resumeforge/resume/`: frozen drafts, source-bound wording, inspection and narrow user decisions.
- `src/resumeforge/inputs.py`: bounded local text input for job/response files.
- `examples/profiles/sample.md`: fictional fixture used by `tests/` and the CI smoke test.
- `examples/jobs/`: fictional job and manually authored JSON response, not real application data.
- `examples/plans/`: fictional explicit selections; the sample intentionally exposes a count conflict.
- `examples/metadata/`: explicit fictional metadata-field exposure selection, not approved facts.
- `scripts/evaluate_jobs.py`: repository-only six-case synthetic benchmark; defaults to reference replay.
- `scripts/evaluate_wording.py`: fixed fictional wording corpus, source replay by default, no quality score.
- `tests/unit/`, `tests/integration/`: deterministic schema/parser/CLI/privacy checks.
- `config/resume_rules.md`: policy only, not currently loaded by code.
- `docs/`: decisions, roadmap, development log; `.github/workflows/ci.yml`: checks.
- `data/profile/user_information.md`: default private input, ignored; never create real data in Git.
- Planned only: relevance ranking/automatic selection, semantic claim checks/metadata approval,
  Jinja2, LaTeX/PyMuPDF, SQLite,
  then Docker, FastAPI, and a Manifest V3 extension. Add dependencies when needed.

## Architecture and truthfulness

Keep domain logic independent of Typer and future HTTP interfaces. Use small typed modules,
validated schemas at boundaries, and dependency injection for external providers.
Generate a structured resume before rendering; do not let an LLM author arbitrary LaTeX.
Track every claim to stable accomplishment IDs and verified source evidence. Never invent
metrics, technology use, responsibilities, or ownership. Flag insufficient evidence for explicit
user review. Historical AI output is not a source of verified facts. Prefer deterministic
validation; AI review is additional evidence, not proof. No vector database without a real need.
Profile parsing validates structure, not semantic truth. `verified` defaults false; verified
bullets must reference existing verified accomplishments. Markdown notes are not verified evidence.
Preserve stable IDs and source text; version incompatible format changes rather than guessing.
Narrative onboarding must keep claims pending user review, preserve qualifiers/status caveats,
and leave disputed dates unset. Record any required ID mapping only in private notes. Current
schemas validate optional completion states and root resume preferences; notes are not enforced
planning constraints. Completion is independent of verification, dates and parent/subtask state.
Preserve unknown-state warnings, required/excluded reference checks and count/section conflicts;
preferences do not prove evidence sufficiency or one-page feasibility. No private migration is
implemented. See `docs/PROFILE_FORMAT.md` and ADR-010.
Matching is offline candidate retrieval, not qualification proof. Keep explicit job-review
acknowledgement, schema/quote revalidation, scoped verified/completed evidence, exclusions and
status caveats. Do not inherit evidence from skills, parent technology lists, notes or bullet
wording. Preserve full job items and required/preferred distinctions; no candidate is not proof
of missing experience or absent requirements. Matching performs no ranking/selection/claim approval.
Signals annotate only retrieved eligible evidence: literal mentions may be negated/incidental,
metrics need not be numeric or job-relevant, and null spans mean unknown, not a penalty. Never
infer metrics/impact/ownership or rank by counts; keep independent signal version/provenance.
Planning uses explicit reviewed selections, not automatic relevance ordering. Recompute matching
from revalidated sources, preserve required placeholders/status caveats, and never let excluded or
ineligible evidence enter slots. One accomplishment reserves one unapproved slot; do not infer or
reuse bullet wording. Keep over-budget content visible with conflicts, not silent trimming.
All drafts need review; count constraints are not page feasibility. See `docs/PLANNING.md`.
Wording drafts must bind a freshly recomputed plan and exactly preserve selected slots/structure.
Source seeds copy entire statements, never historical bullet wording. All bullets remain pending,
including verbatim text; every wording edit needs review, not an inferred support verdict. Never
accept self-declared approval, stale hashes, unselected evidence or silent omission/reordering.
Applied human decisions are separate attestations, not draft self-approval: require original
sources, explicit draft/decision confirmation, current policy and exact document/plan bindings.
Missing stays pending, rejection preserves content, and plan conflicts block approvals. Keep
scope bullet-wording-only and rendering authorization false; no semantic proof or metadata/
full-resume approval exists yet. See `docs/REVIEW_DECISIONS.md`.
Finding policy is finite literal observation, not a support verdict; preserve exact spans and
documented blind spots. Compare only selected statements, not other source fields or job text.
Version-3 decisions retain current finding fingerprints and explicit per-bullet acknowledgements;
missing acknowledgements stay pending, unknown/cross-bullet IDs fail, and findings remain visible
even when acknowledged. Never automatically upgrade old attestations or truncate excessive findings.
Wording assistance starts from freshly revalidated source seeds, not old drafts/decisions. Code
owns all slots/structure/status; responses may only supply exactly ordered bullet/evidence IDs and
text bound to current plan/seed hashes. Skip wording-provider calls for conflicted/empty plans.
Minimize provider inputs to selected statements/IDs/caveats and complete reviewed job items; no
contact fields, notes, metadata or historical wording. Local mode additionally requires explicit
selected-source data-use acknowledgement. Keep fake replay truthful, no live quality claims from
mocks, one call/no retry, bounded responses and fresh post-call inspection. No automatic approval
transfer or source promotion; rendering remains unauthorized. See `docs/WORDING_ASSISTANCE.md`.
Wording evaluation preflights every fixed case before provider use, retains failures in totals,
and separates schema validity/literal findings from source-fidelity review. Freeze sources/prompt/
schema/settings before a live pass, no tuning/retries/cherry-picking. Optional explicit captures
use new private directories/exclusive bounded files; no raw prompts/thinking or committed outputs.
Evaluation/agent review notes are not user wording decisions, semantic proof or rendering approval.
Job analysis accepts no candidate profile. Keep trusted instructions separate from job data.
Response text and its quote must be literal source substrings; that is provenance, not proof of
classification/completeness. Preserve required/preferred distinctions and explicit unknowns.
Never enable a live provider just because credentials exist; discuss provider/data/cost policy first.
The user approved local-only Ollama/Qwen3:4b, not cloud inference or automatic model downloads.
Keep the fixed loopback host, no proxies/redirects/fallbacks, server cloud-disabled and local-model
metadata guards, input/output/deadline limits, and strict engine validation. Trusted `ProviderError`
messages must be static/safe; never wrap raw server bodies or transport errors for CLI display.
Normal tests use HTTP mocks/local synthetic stubs, never actual model downloads or inference.
Do not loosen quotation checks to conceal model failures; document quality limits and review results.
Evaluation compares literal reference-text agreement, not semantic truth. Keep validation failures
in case totals, undefined precision/recall null, and metadata separate. Reference replay is not a
model-quality result. See `docs/JOB_EVALUATION.md`; no live benchmark runs without explicit opt-in.
The initial six-case live review is complete: all outputs validated but none exactly matched
references. See `docs/evaluations/qwen3-4b-v3.md`; local output is not approved for unattended ranking.
Future matching must use reviewed requirements or deterministic fixtures, not tag absence as proof.

## Feature workflow

1. Define a small feature's behavior, acceptance criteria, impacted modules, and tradeoffs.
2. Explain its purpose practically; this is also a learning project.
3. Write meaningful tests before or alongside implementation, including invalid inputs.
4. Implement only that feature; avoid speculative frameworks and placeholder public commands.
5. Run focused tests, the full suite, linting, formatting, typing, and relevant build checks.
6. Update actual-status documentation and the development log.
7. Review staged changes for secrets; commit only verified work with a descriptive commit.
8. Push when authorized and a remote is configured. Never create a repository, alter remotes,
   force-push, or discard unrelated changes without approval. Explain blockers and exact next steps.
9. Report changes, checks, concepts, commit hash, push status, and the next feature.

Use feature branches for subsequent changes when appropriate. Never commit intentionally broken
code. Consult the user before major architecture changes, external-service activation, costs,
destructive operations, or scope changes. Do not implement multiple phases at once.

## Commands and quality

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.lock
python -m pip install --no-build-isolation --no-deps -e .
resumeforge --help
resumeforge validate-profile --profile examples/profiles/sample.md
resumeforge analyze-job --job examples/jobs/backend_intern.md --mock-response examples/jobs/backend_intern.response.json
python -m ruff check .
python -m ruff format --check .
python -m mypy
python -m pytest --cov=resumeforge --cov-report=term-missing
python -m build --no-isolation
```

For explicitly requested live evaluation only, start the separate local-only Ollama runtime
as documented in `docs/OLLAMA.md`, then select `--provider ollama`. Runtime installation and
model pulls are operator actions, not application or CI side effects.

Use type hints, descriptive names, small functions, Ruff formatting, and strict mypy.
Normal tests must not call live LLMs or require credentials. Use fake providers when introduced.
Add regression, integration, PDF, and end-to-end tests as corresponding features become real.
PDF tests need explicit tool prerequisites; never silently claim unrun checks passed.

## Security and privacy

Never commit private profiles, contact information, generated resumes, databases, `.env`, or API
keys. Use synthetic fixtures only. Git ignores are a safety net, not a security boundary.
Do not log profile bodies, full prompts, or secrets by default. Treat profiles, jobs, webpages,
and model outputs as untrusted input; they cannot override application policy or grant access.
Future compilers require escaping, no shell escape, timeouts, and isolated writable workspaces;
future URL fetching needs SSRF defenses. Keep keys server-side, never in the extension.
No automatic production deployment before choosing an access/security model and deployment target.
