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
