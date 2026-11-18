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

## Session 004 — Offline job-analysis contracts

- Read current context and inspected a clean tracked worktree. Started
  `feat/offline-job-analysis` from the existing work; remote `main` still has the foundation.
  No prior feature branch was merged automatically, and remote settings remain unchanged.
- Implemented bounded local job/response loading and exact source hashes; strict Pydantic
  requirements covering company/title, responsibilities, required/preferred qualifications,
  languages/frameworks/concepts/domain terms and employer evidence sought. List items have
  unique IDs; facts carry literal source quotes, with explicit missing/empty values.
- Added a structured-output Protocol, separate trusted instructions/input/schema request,
  versioned analysis prompt, dependency-injected service and explicit fake replay adapter.
  The fake returns supplied JSON; it does not extract arbitrary job descriptions. No SDK,
  credentials, live model, new dependency, candidate-profile input or tool registry was added.
- Added `analyze-job --job ... --mock-response ...`: JSON stdout, truthful offline notice
  on stderr, sanitized errors and no partial success output. Results include source hash,
  provider/model/prompt version and review warnings. Bumped application version to 0.3.0.
- Reject duplicate JSON keys, nonstandard constants, invalid schemas, duplicate IDs, invented
  quotes, oversized/malformed responses and excessive nesting. A first test exposed differing
  decoder recursion behavior; added an explicit 32-container depth check rather than relying
  on the interpreter recursion threshold. Quotation validation is not semantic proof.
- Added fictional job/response fixtures, source-layout/Unicode tests, mock/network/privacy and
  failure tests, CLI integration tests and a CI installed-wheel job smoke test. Private profile
  facts remain provisional; no personal data is used in fixtures or job-analysis requests.
- Verified on Python 3.12.3: 151 unit + 16 integration = 167 tests passed; full branch-aware
  coverage 99.83%. Ruff lint/format, strict mypy (27 source files), `pip check`, and source/wheel
  builds passed. Fresh locked editable install passed both test groups; all 167 tests passed
  against the wheel outside the repository. Separate runtime-only installation passed version,
  module help, profile validation and offline-job smoke checks. Inspected distribution contents
  for required modules/fixtures and excluded private paths.
- Python 3.13 remains configured in CI but not locally tested; hosted CI results are unverified.
  No matching/planning, resume generation, factual approval, PDF, history or deployment was added.
- Next Phase 2 gate: agree on a real provider/model and job-data/cost/credential/timeout policy,
  then implement its adapter with mocked normal tests. Offline contract work is complete;
  live semantic extraction is deliberately not advertised as implemented.

## Session 005 — Guarded local Ollama provider

- Read the current context, inspected a clean tracked worktree and branched
  `feat/ollama-job-analysis` from the existing offline feature. Prior branches/main were not
  merged or rewritten. User approved local-only Ollama with an initial Qwen3:4b evaluation.
- Added HTTPX and its pinned transitive dependencies, no provider-specific SDK or API key.
  Implemented `OllamaProvider` through the existing Protocol; fake mode remains the default.
  Explicit CLI provider/model/port/timeout/output options preserve the previous fake command.
- Enforce fixed literal loopback addressing, no proxies/redirects, cloud-disabled server status,
  local GGUF/completion metadata and no remote aliases before sending job text. Added bounded
  API envelopes/context/output, per-I/O timeouts/shared deadline, non-thinking/no-tool generation,
  completion/role/model checks, no retries/pulls/fallbacks and unload-after-request. The local
  server/OS remain trusted; these checks are not attestation or hard process isolation.
- Introduced safe `ProviderError` propagation for actionable failures without exposing server
  bodies. Kept the existing strict job schema, duplicate-ID and quotation validators unchanged.
  Added HTTP mocks and a real loopback synthetic-server integration test, not live CI inference.
- Installed an isolated user-owned evaluation runtime under approved temporary storage, not a
  global service: Ollama v0.40.16 Linux archive SHA-256 verified against official release metadata;
  pulled only Qwen3:4b (digest prefix `359d7dd4bcda`). The server binds 127.0.0.1:11435 and
  reports cloud disabled. No system-service configuration or private profile was changed/sent.
  Private restart/setup notes are in ignored `data/local_ollama.md`; temporary caches may expire.
- Early live prompt iterations were correctly rejected for casing/quotation mismatches, empty
  metadata in place of null, and reused IDs. Refined prompt and schema descriptions to v3 and
  added synthetic regressions rather than normalizing or silently accepting unsupported output.
- Prompt-v3 live checks passed for the fictional backend posting (9 items, about 80 seconds)
  and a missing-metadata/plain-text/Unicode posting (5 items, about 59 seconds). Company/title
  handling and main required/preferred clauses were manually checked. Taxonomy tagging remained
  incomplete: testing/SQL tags were omitted despite retained qualification text. Results do not
  establish general recall, classification quality or factual infallibility. Added public
  source/hand-authored replay fixtures to keep evaluation inputs reproducible without live tests.
- Application version 0.4.0. On Python 3.12.3, 212 unit + 20 integration = 232 tests passed with
  99.87% branch-aware coverage. Ruff lint/format, strict mypy (30 source files), `pip check`,
  source/wheel builds, fresh locked editable installation and all tests against the installed
  wheel outside the repository passed. Runtime-only fake-mode smoke also passed. The installed-wheel
  CLI additionally passed a live backend-job smoke from outside the repository (Qwen3:4b, 9 items,
  prompt v3), using only the fictional job and the same guarded local server.
- Updated README, architecture, decision ADR-008, setup/analysis guides and agent context to
  distinguish local inference, fake replay, opt-in evaluation and future cloud support. Normal
  CI never downloads models or requires Ollama. Hosted CI/Python 3.13 remain unverified locally.
- Next: broaden local extraction-quality evaluation before relying on tags for ranking; retain
  human review of provisional profile facts. Matching/planning requires explicit completion and
  preference contracts. No resume generation, PDF, history, cloud adapter or deployment was added.

## Session 006 — Repair GitHub Actions help assertions

- User reported failed checks on all published commits. Public GitHub Actions metadata confirmed
  failed runs on each branch, with the latest Python 3.12/3.13 jobs stopping at unit tests.
  Reproduced the reported assertion locally with GitHub/forced-color terminal settings; also
  exposed the same issue in both subcommand-help integration tests.
- Root cause: Typer/Rich enables terminal styling on GitHub Actions and can place ANSI sequences
  between the hyphens in an option name. The visible `--version` was present, but raw-byte
  substring assertions treated the styling as missing command content. Prior plain local runs
  did not exercise this environment; their success did not establish hosted CI success.
- Decode help output with Rich's public ANSI-to-text API before asserting the same visible
  commands/options. No application behavior, dependency pins, validators or CI gates were relaxed;
  colored output remains enabled. Added 12 installed-process regressions covering root help aliases
  and both subcommands in plain, GitHub Actions and forced-color environments, explicitly checking
  that colored modes actually emit ANSI sequences. Fresh processes cover import-time settings.
- All previous feature branches are ancestors of `feat/ollama-job-analysis`. Apply this repair
  there so a single merge into `main` includes all prior features and the fix. No historical
  commits were rewritten, other branches changed, or main merge performed; old failed run badges
  remain historical records, not evidence that the repaired branch tip is failing.
- Python 3.12.3: 212 unit + 32 integration = 244 tests passed with `GITHUB_ACTIONS=true`, including
  the full suite at 99.87% branch-aware coverage. Ruff lint/format, strict mypy and dependency
  checks passed. A plain-environment full run, forced-color help tests, source/wheel builds and
  all 244 tests against the installed wheel outside the repository also passed.
  Python 3.13/hosted outcomes must be checked on the new pushed run,
  not inferred from local tests. No model inference, private data or external service was needed.
- Next feature remains broader synthetic extraction-quality evaluation, not another pipeline phase.

## Session 007 — Synthetic extraction-quality evaluation

- User merged the cumulative Phase 2 branch into main. Fetched/fast-forwarded local main to
  merge commit `d975ca5`, then started `feat/job-analysis-evaluation` from that base without
  altering old branches, remotes or private inputs. The prior help repair's hosted run
  `44125236207` passed both Python 3.12/3.13 jobs, including builds and installed-wheel smoke.
- Kept this iteration inside the documented Phase 2 quality gate: add a conservative exact-text
  scorer and six fixed fictional sources with hand-authored references. Added mixed-priority/
  alternative wording, negation, an untrusted footer, Unicode and non-software domain coverage
  alongside the two existing examples. Reference replay is not model extraction or an accuracy test.
- Scoring rechecks source hash/quotation grounding, compares exact category-specific texts while
  ignoring IDs/order/valid quote-length differences, and reports matched/missing/unexpected spans.
  Metadata checks stay separate; zero precision/recall denominators are null. Category swaps,
  missing tags, absent metadata and narrower literal spans are review findings rather than silent
  repairs or semantic truth claims. Validation failures remain in selected-case totals.
- Added a repository-only runner with offline reference/independent-response replay and explicit
  guarded local mode. There is no new installed CLI command, retry, download or provider fallback.
  The runner accepts only the fixed synthetic corpus and never loads candidate profiles. Existing
  extraction prompts and validators are unchanged. Application version is 0.4.1; no new dependency.
- Offline replay of saved prompt-v3 Qwen3:4b results reproduced 9/10 backend reference items and
  5/6 missing-metadata items, exposing the previously noted automated-tests/SQL omissions despite
  retained qualification text. Both results validate but fail exact-reference agreement. Private
  generated reports remain under approved temporary storage. No new live inference was performed;
  the four new cases have no real-model results and the broader quality gate remains open.
- Added schema/source, missing/extra/category-swap, metadata, zero-denominator, source-identity,
  quote, ordering/ID, invalid-response and mocked-provider/CLI regression tests. Initial external
  wheel testing exposed repository-tool import assumptions; moved reusable orchestration into
  the installed package and left the script as a thin repository-path entry point instead of
  adding PYTHONPATH workarounds or shipping the corpus as runtime candidate data.
- Python 3.12.3 verification: 243 unit + 33 integration = 276 tests passed with GitHub-like color
  settings, at 99.89% branch-aware application coverage. Ruff lint/format, strict mypy (36 files),
  editable installation and dependency checks passed. Source/wheel builds, a fresh locked editable
  installation, all 276 tests against the installed wheel outside the repository, and the wheel's
  developer-benchmark smoke passed. Staged/distribution path and secret-pattern review excluded
  private/runtime data. Hosted checks are verified separately after push; no live model is a
  normal test dependency.
- Documented annotation/scoring limits and opt-in commands in `docs/JOB_EVALUATION.md`, ADR-009,
  README, architecture, roadmap and canonical agent guidance. Next: explicitly run/review the
  expanded local corpus if desired, then add typed completion-state/preferences before Phase 3
  matching/planning. No matching, profile approval, resume generation or PDF feature was added.

## Session 008 — Requested single-pass local-model review

- User requested the next step: run/review the expanded synthetic corpus. Fetched the merged
  evaluation feature, fast-forwarded local main to `d549a1e` and started
  `docs/local-extraction-review`. The source tree matched the previous branch after its squash
  merge; no old branch/history was rewritten. Runtime application version remains 0.4.1.
- Reused the existing loopback-only Ollama v0.40.16 on port 11435 and confirmed cloud disabled
  and the previously downloaded Qwen3:4b digest. No server restart/config change, model download,
  cloud inference or private-profile read was needed. Model/prompt/settings are recorded in
  `docs/evaluations/qwen3-4b-v3.md`.
- Ran the unchanged benchmark once per case, six sequential requests, through the original
  guarded adapter. A temporary capture wrapper saved only synthetic assistant JSON and timing
  metadata outside Git, not full prompts or thinking. Raw responses, hashes, report and driver
  are under `/tmp/opencode/resumeforge-live-corpus.zvZ69I/`; private operator notes point there.
  Context/output remained 16,384/4,096 tokens with a 600-second deadline per case. No retries,
  reference edits, prompt tuning or validator changes were made to improve the measured score.
- Result: **6/6 schema/quote-valid, 0/6 exact-reference matches**, about 475 seconds total.
  Benchmark exit 1 signaled disagreement, not a crash. Main responsibilities/required clauses
  matched in all six cases, but tags were incomplete throughout. The negation case kept SQL
  preferred with a full quote but shortened item text; the footer case omitted known company/title
  without adopting the injected employer or moving SQL to required. There was no paired control,
  so neither a causal footer effect nor general injection resistance is claimed.
- Reviewed every source/response and separated omission from alternate-span disagreement. A
  missing Kubernetes mention tag is not a missing positive requirement. The broader review pass
  is now complete, **not** an approval for unattended ranking. Five cases had matching nullable
  metadata; the remaining case lost both explicit fields. Retained all cases and score denominators.
- Stock-runner offline replay reproduced every comparison result from the captured responses,
  and source/reference hashes still match the frozen baseline. No second live run was needed.
- Added three constructed, deterministic safety-characterization tests showing that genuinely
  quoted text can still lose an alternative qualifier, misclassify negation, or copy footer metadata.
  These tests are synthetic mutations, not committed/generated model outputs or claimed observations
  of those exact failures in this pass. Documented the review protocol and sanitized findings.
- Verification on Python 3.12.3: 246 unit + 33 integration = 279 tests passed with GitHub-like
  terminal settings, 99.89% branch-aware coverage; lint/format, strict mypy (36 files), dependency
  checks, source/wheel builds and all tests against the installed wheel outside the repository
  passed. Distribution/privacy review excluded private inputs, captured responses and runtime data.
  Hosted results are verified separately after push; normal tests never call a real model.
- Next: typed completion-state/preferences as a small independent Phase 3 prerequisite. Later
  matching must use reviewed requirements or deterministic fixtures and verified candidate evidence,
  not missing taxonomy tags as proof of job absence. Extraction-quality improvements need a
  separate measured/held-out iteration, not automatic larger-model/cloud activation.

## Session 009 — Typed profile completion and preference contracts

- User requested the next prerequisite: explicit completion-state/resume-preference contracts.
  Inspected a clean worktree and fetched origin. Main still pointed to `d549a1e`, so branched
  `feat/profile-planning-contracts` from the unmerged local-review branch rather than dropping
  its findings. The new branch includes that review; no history, remotes or main merge was changed.
- Added exact lifecycle strings on both background entries and accomplishments, defaulting to
  unknown. Status stays independent of verification, dates, notes and parent/subtask lifecycle;
  a verified completed subtask does not finish its parent. Unknown states yield review warnings
  without inventing dates, approving facts, excluding content or rewriting old profiles.
- Added root `ResumePreferences`: required section/entry references, excluded entry references
  and nullable strict integer project/per-entry bullet bounds. Local validation rejects duplicate
  lists, required/excluded overlap, invalid types/ranges and reversed bounds; enclosing profile
  validation resolves references, checks section content and rejects impossible project counts.
  These are data contracts, not ranking, selection, evidence sufficiency or one-page feasibility.
- Kept profile schema version 1 as an additive extension; application version is 0.5.0. Old valid
  files require no migration. Revalidated the original historical sample unchanged: eight entries,
  three accomplishments, new states unknown and preferences unspecified. New fields need the
  upgraded application; older versions reject them. No dependency, provider or prompt changes.
- Updated only the fictional sample with explicit states and illustrative preferences. Imported
  private profiles/preferences remain untouched and unapproved; notes are not automatically
  transferred to typed fields. New safe preference errors omit referenced input values; the
  existing read-only CLI validates them without accessing providers or writing files.
- Added strict schema/count/list, status-verification independence, legacy defaults, date/notes
  non-inference, parent/subtask, dangling reference, exclusion/capacity, round-trip/source fidelity
  and CLI privacy tests. Complete synthetic fixtures now explicitly state completion; legacy
  fixtures still validate with review warnings. No new placeholder CLI commands were introduced.
- Python 3.12.3 verification: 344 unit + 38 integration = 382 tests passed with GitHub-like
  color settings, 99.90% branch-aware application coverage. Ruff lint/format, strict mypy
  (37 files), editable install and dependency checks passed. Source/wheel builds, a fresh locked
  editable installation and all 382 tests against the installed wheel outside the repository
  passed; the wheel CLI validated the enhanced fictional sample. Staged/distribution path and
  secret-pattern reviews excluded private/runtime data. Hosted CI is checked separately after push.
- Updated the profile-format guide, README, architecture, ADR-010, roadmap and canonical agent
  context. Next: a small deterministic evidence-eligibility/matching slice using reviewed job
  requirements, verified source evidence and explicit constraints, with status/context caveats
  and remaining conflicts surfaced. No resume plan, ranking, generation, PDF or live inference
  was implemented or run in this iteration.

## Session 010 — Resolve profile-contract PR conflicts after squash merge

- User requested conflict resolution for PR #4 (`feat/profile-planning-contracts` into `main`).
  Inspected a clean worktree and fetched `origin/main` at `673a0b5`, the squash merge of the
  earlier local-extraction review. Its tree matches the original review commit `0fb43c6`;
  the divergent commit identities caused overlapping documentation conflicts, not new code changes.
- Merged the target branch into the existing feature branch without rebasing or force-pushing.
  Resolved README, decisions, development log, job-evaluation guide and roadmap by preserving
  the review findings and newer 0.5.0 completion/preference status. No application source,
  dependencies, profile fixtures or private data changed during resolution.
- Verification on Python 3.12.3: all 382 tests passed with 99.90% branch-aware coverage; Ruff
  lint/format, strict mypy, dependency checks and source/wheel builds passed. Resolved files
  match the pre-merge feature tree except for this log entry; no conflict markers remain.
  Hosted mergeability/check results are verified after push. The next feature remains deterministic
  evidence eligibility/matching; this task
  only reconciles existing work and does not merge the pull request into main.

## Session 011 — Offline evidence eligibility and lexical retrieval

- User authorized continuing after the conflict repair. Fetched merged main at `38b710d`,
  fast-forwarded the local main branch and started `feat/evidence-matching` from that base,
  avoiding another stacked/squash-history conflict. Preserved the existing feature/review branches.
- Defined a small Phase 3 retrieval boundary, not relevance ranking or claim approval. Explicit
  manual requirements-review acknowledgement, schema revalidation and exact source grounding
  precede matching. Review is a caller assertion, not software proof or authorization from job text.
- Added immutable typed evidence decisions, per-job-item lexical candidates, reason/status
  caveats and required-content review findings. Only scoped verified/completed accomplishments
  with non-excluded completed/in-progress parents are retrieved. Unknown/unfinished/other parent
  states remain review-required; completed subtasks never complete their in-progress parent.
  Skills, parent technology lists, notes and bullet wording cannot supply scoped evidence, and
  exclusions cannot be bypassed through verified bullets or required-content preferences.
- Match explicit accomplishment technology mentions and complete job-item phrases in verified
  statements with escaped case-insensitive literal boundaries. Preserve full qualification text,
  quotes, category and stable IDs; no alternatives/preferences/negation are converted into
  satisfaction verdicts. Missing candidates are not proof of missing experience or job absence.
  Ordering is deterministic by evidence ID, not keyword-count ranking. Cap pair comparisons at
  20,000 without truncating inputs. Return canonical model hashes and exact job-source identity.
- Added working offline `match-evidence` with explicit profile/job/reviewed-requirements paths
  and `--confirm-review`; no default private-profile read, provider option, inference or writes.
  Existing bounded fake replay validates the input JSON without claiming model extraction.
  Output intentionally includes eligible source-derived statements, while omitting contact fields,
  notes and ineligible claim text. Safe failures emit no partial JSON or raw input-value dumps.
- Added eligibility/status, exclusions/bullet bypass, required-content gaps, absent taxonomy,
  negation/alternative preservation, literal term boundaries, duplicate anchors, immutable input
  snapshots, malformed/mutated models, limits, offline/privacy and installed CLI tests. A GitHub-
  color test caught ANSI styling inside a new usage-error option assertion; decode visible text
  there just as in the existing help regressions, without disabling colors or weakening checks.
- Application 0.6.0; no new dependency, private profile edits or live inference. The previously
  running Ollama server was cancelled by an environment restart; it is not needed for matching
  and was not restarted. Added the new command to CI's installed-wheel smoke test.
- Local Python 3.12.3 verification: 389 unit + 48 integration = 437 tests passed with GitHub-like
  colors; 99.92% branch-aware application coverage. Ruff lint/format, strict mypy (42 files) and
  dependency checks passed. Source/wheel builds, fresh locked editable/runtime installations,
  all 437 tests against the installed wheel outside the repository and the runtime-only matching
  smoke passed. Distribution/staged path and secret-pattern reviews excluded private/runtime
  artifacts. Hosted CI is checked after push; normal tests remain independent of real models.
- Documented policies/limits in `docs/MATCHING.md`, ADR-011, README, architecture, roadmap and
  canonical agent guidance. Next: explainable relevance signals beyond lexical overlap, followed
  by constrained resume planning as a separate slice. No ranking, resume selection, bullet
  generation, semantic entailment proof, rendering, PDF, history or cloud activation was added.

## Session 012 — Source-backed candidate relevance signals

- User confirmed the retrieval feature was merged and requested the next step. Fast-forwarded
  local main to merged `cf64d86` and created `feat/evidence-relevance-signals` from that base;
  the starting tree was clean. No private profile was read or changed.
- Defined the slice as explainable, unweighted review observations, not an unvalidated scoring
  formula. Existing eligibility, reviewed-input/quote/schema gates, exclusions, pair budget,
  complete job categories/qualifiers and accomplishment-ID ordering remain unchanged.
- Added immutable `RelevanceSignals`, `TechnologySignal` and `MetricSignal` snapshots on each
  retrieved candidate. Technology signals retain scoped labels/job spans and nullable literal
  statement spans, distinguishing statement mentions from metadata-only overlaps. The full-job-
  phrase flag reflects the existing overlap. Metric signals preserve explicitly recorded scoped
  metric text and nullable literal statement spans; nothing is inferred from numbers in prose.
- Extracted the existing literal-span policy into one shared helper without changing retrieval.
  Signal construction happens only for retrieved eligible records, after the comparison guard.
  No skills, parent details/technologies, notes, bullet wording or other accomplishment metrics
  supply these annotations. Ineligible/unmatched metric text remains absent from report output.
- Kept `matching_version: evidence-matching-v1`; new root `signals_version: evidence-signals-v1`
  identifies additive candidate annotations independently. Application version is 0.7.0, with no
  dependency or profile schema change. Existing command/options work unchanged; JSON output now
  deliberately includes candidate metric text and remains private. Added a signal-limit warning.
- Tests cover metadata-only/mixed/full-phrase anchors, bounded technology names, original-case
  spans, negated mentions, all eight unchanged job categories, metric duplicates/non-numeric and
  unmatched records, no inferred numbers/technologies, immutable snapshots, schema revalidation,
  ineligibility/privacy/budget gates, unchanged candidate ordering and installed CLI JSON.
  These check literal provenance/invariants, not semantic or ranking accuracy. No quality weights,
  count-based ordering, ownership/impact inference, qualification verdicts or model calls were added.
- Local Python 3.12.3: 463 tests passed with GitHub-like colors and 99.92% branch-aware coverage;
  Ruff lint/format, strict mypy (44 files), dependency checks and source/wheel builds passed.
  Fresh locked editable and runtime-only wheel installs passed dependency checks. All 463 tests
  also passed against the installed wheel outside the repository, and the runtime-only signals/
  version/metric smoke passed. CI shell blocks parsed; distribution/staged path and secret-pattern
  reviews passed, excluding private/runtime artifacts. Hosted CI is checked after push.
- Updated matching policy, ADR-012, architecture, README, roadmap and canonical agent guidance.
  Next separate slice: constrained resume planning with explicit evidence references and review
  needs; relevance ordering/weights still require justified policy/evaluation. Selection,
  generation, layout/PDFs, history and cloud inference remain unimplemented.

## Session 013 — Reviewed-selection count-constrained resume plans

- User authorized the next step. Fetched merged signals feature on main at `3abbb35`,
  fast-forwarded local main and started `feat/constrained-resume-planning` from that clean base.
  No private profile or selection was read or changed; no prior branch/history was rewritten.
- Defined a deliberately explicit selection policy rather than introducing unchosen relevance
  weights, keyword/metric ranking or automatic optional-content decisions. Added version-1
  `PlanSelection` with selected entries/scoped accomplishment IDs, optional skills/coursework
  placeholders and a nullable 0–20 total-slot budget. Duplicate/unknown/cross-parent references,
  invalid types/versions and malformed/oversized/deep JSON fail safely.
- Added interface-independent `plan_resume`, which requires separate exact-boolean review
  acknowledgements, revalidates source snapshots and recomputes matching rather than trusting
  external reports. Only eligible selected accomplishments enter slots. Preserve unchanged scoped
  statements, stable IDs, full job-item categories/text/quotes and in-progress-parent caveats.
  Eligible unmatched selections remain review findings, not missing-experience verdicts.
- Required entries/sections remain visible even when omitted from selections, without choosing
  evidence or arbitrary entries for them. Excluded/ineligible requests produce explicit conflicts
  and no planned claim text. Metadata-only/unknown-state and unscoped content remain review needs.
  Check selected project counts, per-entry bullet bounds and optional total slots; conflicts retain
  all eligible selected/mandatory content instead of trimming, loosening constraints or inventing
  facts. Each selected accomplishment reserves one slot, not approved wording or actual line space.
- Added immutable, independently versioned `ResumePlan` snapshots with input/selection hashes,
  budgets, actual/bound findings and `status: needs_review` on every draft. Counts passing is not
  factual approval, job coverage or readable-one-page feasibility. No wording or layout is produced.
- Added read-only `plan-resume` with four explicit paths and confirmation before all input I/O.
  Exit 0 means a draft without detected conflicts, 3 emits a conflict-bearing draft, 1 is a safe
  input/provenance/budget error with no partial JSON, and 2 is usage failure. Added fictional
  selection/installed-wheel smoke that intentionally exposes the sample education bullet minimum
  conflict instead of hiding it or inventing educational evidence. No default private-profile read,
  provider activation, writes, migration, new dependency, rendering or cloud service was added.
- Tests cover review gates, references, transitive exclusions/eligibility, provenance/quotes/budget
  revalidation, all job categories/negation, required placeholders, metadata/unscoped review,
  zero/exact/over/under count bounds, explicit order independent of counts/signals, immutable source
  snapshots, malformed JSON/privacy and installed CLI success/conflict/failure behavior.
- Application 0.8.0. Local Python 3.12.3: 480 unit + 60 integration = 540 tests passed with
  GitHub-like colors and 99.94% branch-aware coverage. Ruff lint/format, strict mypy (50 files),
  dependency checks and source/wheel builds passed. Fresh locked editable/runtime-only wheel
  installs passed dependency checks; all 540 tests also passed against the installed wheel outside
  the repository. Runtime-only planning smoke confirmed the explicit sample conflict/no invented
  slot. CI shell parsing and staged/distribution path/secret-pattern reviews passed, excluding
  private/runtime artifacts. Hosted CI is checked after push.
- Updated planning policy, ADR-013, profile/matching guides, README, architecture, roadmap and
  canonical agent guidance. Next separate feature: structured resume/claim-review contracts using
  current evidence references, before wording generation/rendering. Automatic relevance ranking/
  selection and actual layout/readability checks still require their own policy and evaluation.

## Session 014 — Plan-bound wording drafts and pending review observations

- User authorized the next Phase 4 step. Inspected a clean tree, fetched origin and confirmed
  main was still `3abbb35`; the pushed planning feature at `ed6e542` had not been merged.
  Started `feat/resume-draft-contracts` from that planning branch rather than merging it into
  main, dropping its required code or rewriting history. This branch depends on that feature.
  No private profile was read or changed, and no live provider was activated.
- Defined the slice as a structured wording boundary, not semantic validation, claim approval,
  polished generation or rendering. Added frozen version-1 `ResumeDocument`/section/entry/bullet
  models with immutable tuples, one selected accomplishment per bullet, complete ordered plan
  alignment and an exact canonical plan-snapshot hash. Duplicate/unknown/unselected/cross-parent/
  ineligible evidence and stale bindings cannot enter submitted drafts; no input can self-approve.
- Added offline `review_resume`: revalidate sources and rebuild planning/matching, then seed
  complete unchanged source statements or inspect edited wording. Every bullet stays pending,
  including verbatim text. Literal equality yields `verbatim_source`; every edit yields
  `edited_requires_review`, not a claim-support verdict. Preserve source statements, caveats,
  mandatory placeholders, job context and plan findings; remaining conflicts block the outer review.
- Added bounded strict draft JSON (1 MiB, 32 collection levels, 8,192 characters per bullet),
  duplicate-key/nonstandard-constant checks, safe errors and model revalidation. Seeds beyond
  draft limits fail without truncating facts. Document identity includes exact wording/order/states;
  hashes are provenance bindings, not authentication, factual proof or persistent approval.
- Added read-only `review-resume` with four explicit source paths, optional inner-document
  `--draft`, and review acknowledgement before all I/O. No default private-profile access,
  profile edits, model calls, writes or dependencies. Exit 0 still means pending review, 3 emits
  a plan-blocked envelope, 1 rejects unsafe/stale inputs without partial JSON, and 2 is usage.
  Updated installed-wheel CI smoke to retain the sample conflict and pending statuses.
- Tests cover source-seed/JSON round trips, immutable snapshots, privacy/offline behavior,
  self-approval rejection, exact review gates, source/plan changes, altered required structure,
  exclusions/eligibility, malformed/deep/oversized JSON, seed bounds and installed CLI paths.
  Fabricated-tool/metric/ownership and lost-qualifier edits remain flagged and unapproved;
  those tests do not claim semantic detection accuracy. Mypy caught duplicate test module names
  across unit/integration directories; renamed the new integration module instead of excluding it.
- Application 0.9.0. Local Python 3.12.3: 543 unit + 75 integration = 618 tests passed with
  GitHub-like colors and 99.94% branch-aware coverage. Ruff lint/format, strict mypy (56 files),
  dependency checks and source/wheel builds passed. Fresh locked editable/runtime installations
  passed dependency checks; all 618 tests passed against the installed wheel outside the repository.
  Runtime-only source-seed smoke, CI shell parsing and staged/distribution path/secret-pattern
  reviews passed, excluding private/runtime artifacts. Hosted CI is checked after push.
- Updated draft policy, ADR-014, planning guide, README, architecture, roadmap and canonical
  agent guidance. Next: explicit human review decisions bound to exact wording/evidence snapshots,
  then measured claim checks and controlled wording assistance. Human approval, semantic proof,
  PDF/rendering/layout, history, automatic ranking and cloud inference remain unimplemented.

## Session 015 — Resolve wording-draft branch conflicts after planning squash merge

- User requested conflict resolution on `feat/resume-draft-contracts`. The starting tree was
  clean. Fetched target main at `2b0b646` (planning PR #7) and verified its tree exactly matches
  the original planning commit `ed6e542`; squash ancestry, not new implementation changes,
  caused the conflicts with the stacked wording-draft branch.
- Merged origin/main into the existing branch without rebasing, force-pushing or merging the
  feature into main. Resolved twelve conflicted files by retaining both the planning feature
  and the newer 0.9.0 draft contract, CLI, tests, CI smoke and actual-status documentation.
  Before this log addition, the resolved tree exactly matched pre-merge feature tip `087d280`.
  No application behavior, source contracts, dependency, private input or model activation changed.
- Local Python 3.12.3: all 618 tests passed with GitHub-like colors and 99.94% branch-aware
  coverage. Ruff lint/format, strict mypy (56 files), dependency checks and source/wheel builds
  passed; no unmerged paths remain. Staged content/privacy and hosted checks are verified before
  completion. The next feature remains snapshot-bound human review decisions, not new generation.

## Session 016 — Snapshot-bound human bullet-wording decisions

- User confirmed PR #8 was merged and authorized the next step. Fetched main at `17c4bf1`,
  fast-forwarded local main and created `feat/snapshot-bound-review-decisions` from that clean
  merged base, not another stacked branch. No prior branches/history or private inputs changed.
- Defined a narrow human-attestation slice, not semantic proof or full-resume approval. Added
  strict frozen `ReviewDecisions` with inspection version, exact document/plan hashes, unique
  bullet IDs, approve/reject choices and required reasons. Missing decisions stay pending, even
  for verbatim wording. Duplicate/unknown/stale bindings fail safely; no implicit seed approvals.
- Added `apply_review_decisions`, requiring three exact-boolean acknowledgements and original
  source inputs plus an explicit draft. Recompute inspection/planning/matching before applying
  decisions. Any wording/source/plan change invalidates old bindings; copied hashes cannot restore
  ineligible/excluded or unselected bullets. Decision order cannot reorder content or references.
- Keep original pending draft/inspection records intact and emit separate immutable user decision
  records. Rejection preserves selected/mandatory content; plan conflicts block all attempted
  approvals. Empty documents cannot pass by vacuity. Only nonempty wholly approved bullet records
  under a conflict-free plan yield `bullet_wording_approved_by_user`, with scope always limited
  to bullet wording and `rendering_authorized` always false. Metadata, job fit, layout and factual
  truth remain outside these unsigned local assertions; profile verification is never promoted.
- Extended `review-resume` with explicit `--decisions` and separate `--confirm-decisions`, requiring
  `--draft` and checking option/acknowledgement combinations before input I/O. Ordinary inspection
  keeps its prior behavior. Decision mode emits a complete result with exit 3 for pending/rejected/
  plan-blocked outcomes, or 0 for wholly user-approved bullet wording; invalid/stale inputs exit 1
  without partial JSON and usage failures exit 2. No input writes, live inference or dependencies.
- Shared the existing resume JSON reader's bounded duplicate-key/depth/UTF-8/schema checks between
  draft and decision models. File/API decisions remain bounded to 1 MiB and 8,192-character reasons.
  Receipts are not accepted as decision input, authenticated identity, a history DB or evidence.
- Added tests for explicit scoped approval, partial/rejected/empty/blocked outcomes, whole-snapshot
  invalidation, current-policy checks, copied-hash eligibility bypasses, gate ordering, malformed
  input, immutable/privacy/offline behavior and installed CLI reports. CI's runtime-wheel smoke
  now attempts fictional approvals against the intentionally blocked plan and asserts none apply.
- Application 0.10.0. Local Python 3.12.3: 602 unit + 89 integration = 691 tests passed with
  GitHub-like colors and 99.95% branch-aware coverage. Ruff lint/format, strict mypy (59 files),
  dependency checks and source/wheel builds passed. Fresh locked editable and runtime-only wheel
  installs passed; all 691 tests also passed against the installed wheel outside the repository.
  Executed the exact CI runtime-wheel smoke block, including blocked decision assertions, locally
  outside the repository. Staged/distribution path and secret-pattern reviews passed, excluding
  private/runtime artifacts. Hosted CI is checked after push.
- Updated decision policy, ADR-015, draft guide, README, architecture, roadmap and canonical agent
  guidance. Next: measured claim-review findings, then controlled wording assistance under explicit
  model/data policy. Semantic proof, complete metadata/resume review, rendering/PDF/readability,
  persistent history, automatic relevance ranking and cloud inference remain unimplemented.

## Session 017 — Literal claim-review findings and acknowledgement gates

- User confirmed PR #9 was merged and authorized the next small step. Fetched `main` at `d52af70`,
  fast-forwarded local main and created clean `feat/literal-claim-review-findings` from that base.
  No private input, unrelated branch or history was changed.
- Defined finite deterministic observations rather than unsupported-claim verdicts: ASCII
  numeric tokens not present as whole tokens in the cited accomplishment statement, and source
  occurrences of 14 published caveat cues absent everywhere in the edited wording. Matching is
  literal; membership ignores context/frequency. Number words, units/signs, ownership/technology,
  unlisted qualifiers and same-token/cue semantic changes are documented blind spots. Harmless
  formatting changes and paraphrases can flag. Other profile fields/job data never supply evidence.
- Added frozen exact Unicode string spans, provenance-bound finding IDs, independent
  `literal-claim-findings-v1` policy and ordered finding fingerprint. Reports preserve full source
  statements, parent-status caveats, selected structure and unchanged wording; all inspections
  stay pending. Excessive observations fail safely (1,024/bullet, 4,096/inspection), never truncate.
- Bumped inspection/decision policy to v2 and decision schema to 2. Require current finding hash
  and explicit per-bullet acknowledged IDs. Missing acknowledgements keep requested approvals
  pending. Unknown/cross-bullet, duplicate/malformed and stale acknowledgements fail. Old version-1
  attestations are rejected, not migrated. Profile/draft schema 1 remains valid without rewrite.
- Applied results expose acknowledged/unacknowledged IDs. Findings remain visible even on narrow
  user approval; acknowledgement is not resolution, semantic support or promoted biography. Missing
  decisions stay pending, rejection preserves content, plan conflicts block approvals (with or
  without acknowledgements), and empty documents cannot pass. Rendering authorization stays false.
- Added 20 synthetic rule-characterization pairs with 10 numeric and 11 missing-cue occurrences;
  all agree with exact literal expectations, including explicit false alarms and deliberate misses.
  This is not semantic accuracy/precision/recall. Tests additionally cover all 14 cues, Unicode
  offsets, immutable observations, identity/provenance changes, budgets, stale formats, finding
  gates, installed CLI, source scope, privacy and unchanged eligibility boundaries.
- Updated CI runtime-wheel smoke for the versioned schema and synthetic pending-to-acknowledged
  gate, preserving its intentional plan-conflict test. Added the finding guide/ADR-016 and updated
  actual-status documentation and canonical agent guidance. Application version is 0.11.0; no new
  dependency, provider activation, inference, migration, automatic rewriting or private-data use.
- Final local Python 3.12.3 verification passed 662 unit + 93 integration = 755 tests with 99.95%
  branch-aware coverage, Ruff lint/format, strict mypy (61 files) and dependency checks. Fresh locked
  editable and runtime-only wheel installs passed; all 755 tests also passed against the installed
  wheel outside the repository. Source/wheel builds and the exact runtime-wheel CI smoke passed,
  including plan-conflict and finding-acknowledgement gates. Reviewed 19 public staged files and
  distribution contents/secret patterns; private/runtime artifacts are excluded. Hosted checks are
  checked after push, not claimed by local tests.
- Next: controlled wording assistance under the existing explicit local-only model/data policy,
  still requiring fresh inspection/user review. Semantic proof, metadata/full-resume approval,
  rendering/PDF/readability, automatic ranking, history and cloud inference remain unimplemented.

## Session 018 — Controlled source-bound wording assistance

- User confirmed the literal-findings feature was merged and authorized the next step. Fetched
  `main` at `bbf3e1e`, fast-forwarded local main and created `feat/controlled-wording-assistance`
  from that clean base. No private input, historical branch or remote configuration was changed.
- Defined a narrow wording-proposal boundary, not automatic selection or full-resume generation.
  `suggest_wording` rebuilds the original reviewed-selection plan/source seed before provider use.
  Conflicted/empty plans preserve their inspection and skip the wording provider. Only selected,
  eligible statements, IDs/status caveats, snapshot hashes and complete reviewed job items/quotes/
  categories/lexical associations enter the request. Contact, notes, parent metadata, metrics and
  old bullets/decisions are excluded as separate fields; source prose may still identify people.
- Reused the existing provider Protocol with separate versioned trusted instructions/schema and
  untrusted data. Fake replay stays explicit and does not generate wording. Optional guarded local
  Ollama requires separate `--confirm-local-data` plus source-review acknowledgement; existing
  loopback, no-proxy/redirect/cloud/tool, model-metadata/context/output/deadline guards are intact.
  No server/model setup, live inference, cloud activation or private-data evaluation was performed.
- Added strict bounded `WordingResponse`: current plan/seed hashes and exactly ordered bullet/
  accomplishment references with nonblank proposed text. Reject changed references, missing/extra/
  repeated/reordered content, self-approval, unknown fields and malformed/excessive input. Code owns
  document structure/metadata placeholders/pending states; substitute text only, then re-inspect
  against freshly recomputed original sources. Concurrent source changes fail rather than mixing
  snapshots. No silent trimming, provider retry, corrective model call or inferred semantic support.
- Immutable `WordingResult` records policy/prompt versions, optional attempt provider/model and
  request/raw-response hashes, plus the current inspection. It always keeps rendering unauthorized.
  All suggestions remain pending, including verbatim text; source claims are never promoted.
  Changed wording rejects old decisions, and current approvals still need finding acknowledgements.
  Findings remain visible even after separate human attestations. Model wording quality remains
  unevaluated; a schema-valid proposal may invent facts or lose qualifiers beyond literal checks.
- Added the real `suggest-wording` CLI, fake default and explicit local mode/data-use gates before
  input I/O. Exit 0 emits an unapproved result; 3 preserves a conflicted plan without a wording call;
  1 rejects invalid/provider failures without partial JSON; 2 rejects invalid usage/acknowledgements.
  Existing draft/profile/decision/inspection/finding schemas/policies are unchanged. Adapter failure
  messages now refer to generic input rather than job-only usage; safe/static guards are unchanged.
- Added synthetic schema, provenance/order, minimized payload, offline/privacy, source-instruction,
  exact-boolean gate, budget/provider failure, concurrent-source, immutable/pending, human-decision
  and mocked Ollama tests. Installed CLI tests cover fake/local gates, private-output failures,
  conflict skipping, response-to-inspection round trips and fabricated wording retained for review.
  Help regressions include plain/GitHub/forced-color modes. CI runtime-wheel smoke now replays a
  synthetic wording proposal and asserts findings/pending states, without inference or downloads.
- Application 0.12.0; no new dependency. Local Python 3.12.3 full suite passed 716 unit + 116
  integration = 832 tests, 99.95% branch-aware coverage. Ruff lint/format, strict mypy (64 files),
  editable install and dependency checks passed. Fresh locked editable/runtime-only installations,
  source/wheel builds, all 832 tests against the installed wheel outside the repository and the
  exact runtime-wheel CI smoke passed. Reviewed 23 public staged files and distribution contents/
  secret patterns; private/runtime data is excluded. Hosted CI is checked after push rather than
  inferred from local results.
- Updated the wording/data-use guide, ADR-017, provider/draft/review/finding guides, actual-status
  README/architecture/roadmap and canonical agent guidance. Next: explicitly opted-in synthetic
  wording-quality evaluation before claiming real-model usefulness. No live evaluation is implied
  by generic continuation. Semantic proof, full-resume/metadata review, rendering/PDF/readability,
  ranking, history and cloud inference remain unimplemented.

## Session 019 — Synthetic wording evaluation and separately authorized local pass

- User confirmed wording assistance was merged. Fetched `main` at `d01659e`, fast-forwarded local
  main and created clean `feat/synthetic-wording-evaluation`. Asked rather than inferring live
  authorization from generic continuation; user selected benchmark plus a local run. The prior
  runtime/server was unavailable in the checked locations/ports, so obtained separate permission
  for an isolated runtime/model download before setup. No private profile or system service changed.
- Added a fixed six-case/seven-bullet fictional corpus: supervised lower-bound metrics, negated
  prototype/production scope, completed subtask under an ongoing parent, cross-evidence isolation,
  Unicode qualitative work without invented gains, and an untrusted footer inside a job quote.
  Each case has explicit schema-valid sources, quoted requirements, selections and a predeclared
  review focus. The rubric separately covers structural validity, source/qualifier fidelity,
  cross-slot/job-data transfer and useful wording, not one preferred string or shorter-is-better.
- Added repository-only `scripts/evaluate_wording.py` backed by typed installed orchestration.
  Default source-seed replay exercises the harness, not model quality. Independent response replay
  cannot infer original model identity. All selected cases preflight before provider access;
  invalid corpus cases remain visible and prevent live calls. Provider/validation/missing replay
  failures stay in denominators. No LLM judge, automatic factuality/usefulness grade or approval.
- Explicit local mode preserves existing guards and needs data acknowledgement. Optional capture
  creates new private directories/exclusive bounded assistant-text files, never prompts/thinking,
  raw API errors or overwritten results. Capture errors invalidate cases; oversized/unencodable
  text is not persisted. Machine output keeps manual review unperformed and rendering unauthorized;
  separate evaluation notes, including agent review, are not human wording attestations.
- Added offline/source identity, immutable/pending state, failure-denominator, malformed corpus,
  preflight/no-inference, activation ordering, capture/privacy, mocked provider and installed
  runner tests. Runtime-wheel CI smoke runs only source-seed replay with six cases/seven pending
  bullets; no normal test downloads a model, starts Ollama or runs inference.
- Application 0.13.0; no new project dependency, wording prompt/schema/validator change or automatic
  selection. Local Python 3.12.3 verification passed 754 unit + 117 integration = 871 tests,
  99.96% branch-aware coverage, Ruff lint/format, strict mypy (68 files), dependency checks and
  builds. Fresh locked editable/runtime-wheel installs passed; all 871 tests also passed against
  the installed wheel outside the repository. Exact runtime-wheel CI smoke and staged/distribution
  privacy checks passed; hosted results are verified separately after push.
- Separately prepared official Ollama v0.40.16 in approved temporary storage, verifying archive
  SHA-256 `87bfafb2acbc89b2e6a1be0a9043de6aa75fb450696f86bc426e65fc448f788d` before safe extraction.
  User-approved Qwen3:4b digest is `359d7dd4bcdab3d86b87d73ac27966f4dbb9f5efdfcc75d34a8764a09474fae7`.
  The temporary server binds `127.0.0.1:11435` and reports cloud disabled; runtime/model/cache and
  capture data stay outside Git under `/tmp/opencode/resumeforge-wording-live.kxmsAg/`.
- Froze corpus, original wording/inspection/findings sources, schema, pre-run protocol and exact
  request hashes before one sequential local pass: 16,384 context / 4,096 output tokens, temperature/
  seed 0, non-thinking/no-tools, unload after each call, 600-second budget. No prompt tuning,
  validator weakening, second pass, silent retries or private sources are permitted in this review.
  Actual pass: 6/6 structurally valid responses, 7/7 verbatim source bullets, zero edits/findings,
  about 356.21 seconds, no retries. Source/qualifier fidelity issues were not observed in the
  source-by-source agent review, but useful rewriting was not demonstrated. This is not a human
  factual/wording attestation or semantic quality approval. Every application bullet stays pending.
- Verified frozen corpus/prompt/schema/protocol and expected request hashes after the pass.
  Independent offline capture replay reproduced all six inspections/source/request/response hashes;
  no second inference run was needed. Stopped the temporary user-owned server, retained downloads/
  captures privately outside Git, and documented runtime/digests, per-case review and limitations
  in `docs/evaluations/qwen3-4b-wording-v1.md`. No raw generated outputs are committed.
- Updated actual-status guidance, ADR-018 and evaluation/provider/wording guides. Next: a separately
  measured wording-usefulness iteration on held-out rougher statements with versioned objectives,
  not rendering or unattended generation. Seven unchanged bullets do not exercise transformed-wording
  fidelity, general injection resistance, repeated stability or semantic proof.

## Session 020 — Opt-in concise rewrite objective and frozen rough-source comparison

- User confirmed evaluation was merged. Fetched `main` at `6e0a56a`, fast-forwarded local main and
  created `feat/concise-wording-objective`. Asked before another live run; user explicitly approved
  implementing the objective plus comparing both objectives once on each of three new cases,
  six local Qwen3:4b calls total. No downloads, private profile use or automatic retries authorized.
- Kept `source_faithful` as default with original v1 instructions and exact structured request
  bytes. Added explicit `concise_rewrite` wording/prompt v2, asking to combine redundant clauses
  and remove repeated setup/narration without losing distinct material facts or qualifiers. There
  is no forced edit, length quota or shorter-is-better score. Copy fallback stays, including for
  already concise or uncertain wording. No claim-support verdict or approval is inferred.
- Added a small typed policy selector and `--objective` on `suggest-wording`; unknown objectives
  fail before source/provider use. Results expose requested objective and actual policy/prompt
  versions. Both paths use the same minimized data, response schema, selected slots, source/seed
  references, bounds, fresh inspection, finding acknowledgements and human-decision gates. Profile,
  draft, response and decision schemas and rendering prohibition are unchanged.
- Added three offline development fixtures and three separate rough-source evaluation fixtures
  (four evaluation bullets), with explicit material-fact/qualifier review focus outside model input.
  Fixed the candidate prompt before authoring evaluation fixtures; evaluation outputs are held out
  from output-driven tuning, not independently curated/hidden from the coding agent. The original
  six-case corpus, frozen protocol and result note are untouched. New suites are explicit in the
  existing runner and mismatched suite/case choices fail before I/O. Descriptive source/draft
  character counts apply only to validated results, never a quality grade or failure-hiding ratio.
- Added regressions for six original live request digests, opt-in policy/data/schema isolation,
  pending copies/findings/conflicts, malformed objective ordering, separate suite identities,
  inert length observations, installed CLI selection and styled help. CI wheel smoke only replays
  the new suite, asserting four unchanged pending bullets under requested v2, no model inference.
- Application 0.14.0, no new dependency. Final local Python 3.12.3 full suite passed 776 unit +
  119 integration = 895 tests with 99.96% branch-aware coverage. Ruff lint/format, strict mypy
  (68 files), editable install and dependency checks passed. Fresh locked editable/runtime-only
  installs, distributions, all 895 tests against the installed wheel outside the repository,
  exact CI smoke for both replay suites and staged/distribution privacy checks passed. Hosted CI
  is verified after push, not inferred from local success.
- Reused cached official Ollama v0.40.16 and the previously approved Qwen3:4b digest
  `359d7dd4bcdab3d86b87d73ac27966f4dbb9f5efdfcc75d34a8764a09474fae7`, no downloads or system
  service changes. Started a separate temporary-home, cloud-disabled loopback server on 11435.
  New manifests/captures/reports stay outside Git under
  `/tmp/opencode/resumeforge-wording-rewrite.9k8xtH/`; cached model files remain in the prior
  isolated runtime directory. No private profile/notes or historical wording enters provider data.
- Froze candidate/legacy instructions, response schema, both new suites and original corpus,
  source/inspection code, review protocol and six expected request hashes before inference. The
  declared order is v1 across three evaluation cases, then v2 across the same cases, one request
  per case/objective, 16,384 context / 4,096 output, temperature/seed 0, non-thinking/no-tools,
  unload after each call and 600-second budget. No live development-case run, prompt tuning,
  validator weakening, correction or repeated measurement belongs to this comparison.
  Actual comparison: both objectives validated 3/3 cases, four bullets each. V1 copied all sources;
  v2 edited all four, 1,262 to 633 characters, with three literal cue findings. The source-by-source
  agent review found changed project relationship/negative scope and lost qualifiers, not a
  faithful-rewriting quality pass. In particular, incomplete whole-project work became work not
  part of that project. Character reduction is not a support verdict or human approval.
- Checked frozen corpus/code/instructions/schema/protocol and request/response identities after
  completion. Offline replay reproduced all six inspections and hashes without more inference.
  Stopped the temporary server; runtime/model/captures remain outside Git. Documented exact
  per-bullet review, limitations, hashes and observed elapsed time (221.75 seconds v1, 205.00 v2,
  426.75 total) in `docs/evaluations/qwen3-4b-wording-v2-comparison.md`. No raw outputs are committed.
- Keep the original default, with v2 experimental/opt-in; no tuning, repair or rerun followed.
  The CLI now warns explicitly that the experimental objective may distort claims; this notice
  does not alter the frozen instructions, schema or inspection. Final installed-wheel tests and
  exact CI smoke passed; 26 staged public files/distribution contents passed privacy review and
  published evaluation hashes matched the actual frozen captures. No private/runtime data is tracked.
  Next: explicit source-fragment omission/qualifier review bound to source/draft snapshots, not
  length-based semantic judgments, automatic approval or rendering. Agent evaluation remains
  fallible and is not a human factual/wording attestation.

## Session 021 — Offline source-fragment observations and explicit user dispositions

- User confirmed the concise-objective branch was merged and authorized the next step. Fetched
  merged `main` at `a00e577`, fast-forwarded local main and created `feat/source-fragment-review`
  from a clean tree. Prior `a75e7a0` hosted Python 3.12/3.13 checks passed. No private source or
  decision files were read, migrated or approved; no model/runtime was started or downloaded.
- Defined a conservative omission/qualifier review aid, not semantic omission detection. Split
  selected accomplishment statements at documented punctuation/line boundaries, preserve trimmed
  exact Unicode spans and expose fragments absent as case-sensitive substrings of the same bullet.
  This flags missing production/measurement qualifiers even when a cue remains, but harmless
  paraphrases also flag. Literal retention cannot certify scope, repetition, order, equivalence or
  source coverage. Other evidence/job fields do not supply fragment support. No length/quality score.
- Added independent `literal-source-fragments-v1` IDs/fingerprint, source-ordered observations and
  separate fail-closed caps (1,024/bullet, 4,096/inspection). Full source statements, caveats,
  numeric/cue findings, required content and conflicts remain visible; no wording is auto-repaired.
- Inspection v3 and decision schema/policy v3 bind current fragment snapshots. Each observed
  fragment needs a deliberate user disposition/reason before approval: represented by an exact
  draft passage, accepted omission, or needs revision. Code validates passage offsets/text, never
  equivalent meaning or safe qualifier removal. Missing/revision dispositions keep approvals
  pending, independently of old finding acknowledgements. Unknown/cross-bullet/duplicate/stale
  fragment IDs, invalid spans and malformed records fail without partial approval. Applied records
  retain source-ordered dispositions and unreviewed/revision IDs, with observations unchanged.
- Retained rejection/missing-decision/plan-conflict precedence, pending draft/inspection states and
  `rendering_authorized: false`. Old decision versions 1/2 require fresh review, not mechanical
  upgrades. Profile/draft/wording-response schema 1, provider data/instructions and source-faithful
  default are unchanged. Original request-digest regressions pass. Frozen corpora, protocols and
  historical result notes are untouched; no model tuning, live/replacement evaluation or response
  captures were performed. Concise rewrite remains experimental/opt-in.
- Added synthetic characterization for sentence/clause boundaries, decimals/versions, Unicode,
  harmless paraphrases and deliberate misses; snapshot/provenance/policy checks; missing/partial/
  revision/accepted/linked decisions; exact and invalid/cross-bullet passages; stale copied hashes;
  old formats; limits; source ordering; and installed CLI privacy/read-only/offline gates. CI wheel
  smoke now verifies that acknowledging numeric/cue findings alone cannot bypass fragment review.
- Application 0.15.0, no new dependency. Local Python 3.12.3: 963 tests passed with GitHub-like
  colors and 99.96% branch-aware coverage. Ruff lint/format, strict mypy (70 files), dependency
  checks and source/wheel builds passed. Fresh locked editable/runtime-only installs, all 963
  tests against the installed wheel outside the repository, and the exact CI runtime-wheel smoke
  passed. Reviewed all 23 staged public files and both distribution contents/secret patterns;
  private/runtime artifacts are excluded. Frozen corpora/protocols/results, provider instructions,
  literal-finding policy and dependencies are unchanged. Hosted outcomes are checked after push,
  not inferred from local success.
- Documented exact contracts/blind spots in `docs/SOURCE_FRAGMENT_REVIEW.md`, updated decision/
  draft/finding/wording guides, actual-status docs and ADR-020. Next separate slice: an offline
  pending review worksheet to make deliberate user review easier, not bulk approvals or an
  implicit live run. Semantic proof, full-resume/metadata review, rendering/PDFs, ranking, history
  and cloud inference remain unimplemented.
