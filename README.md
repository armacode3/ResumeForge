# ResumeForge

An evidence-first resume tailoring application, built incrementally. The goal is to turn
a verified Markdown profile and a job description into a reviewable, one-page resume
without inventing experience, technologies, or metrics.

## Current status: Phase 3 — offline retrieval and source-backed review signals

Implemented: an installable Typer CLI with help/version output, unit and installed-entry-point
tests, privacy-ignore regression coverage, linting, formatting, strict typing, packaging checks,
and a GitHub Actions workflow. Profile support now includes a documented Markdown/YAML format,
Pydantic schemas, stable evidence IDs, safe parsing, source preservation, completeness warnings,
and the `validate-profile` command. A fictional sample covers every supported background section.
Job analysis includes local files, quoted structured requirements, provider injection, explicit
fake-response replay and a local-only Ollama adapter. **The fake replays supplied JSON; Ollama
performs inference, with results still subject to strict validation and human review.**

A six-case synthetic evaluation tool now checks exact reference-text agreement, metadata and
category/tag omissions separately from schema validity. Run `python scripts/evaluate_jobs.py`
for **offline reference replay, not a model accuracy test**; see [docs/JOB_EVALUATION.md](docs/JOB_EVALUATION.md).
The initial live six-case review found valid schema/quotes but incomplete tags and lost known
metadata; see [results and limitations](docs/evaluations/qwen3-4b-v3.md). Human review remains necessary.

Profile validation now also accepts explicit completion states and resume preferences, with
checks for required/excluded references and contradictory count bounds. Offline `match-evidence`
now retrieves literal review candidates from eligible scoped accomplishments and reviewed job
requirements. **It does not prove qualifications, rank evidence, select content or validate layout.**
Candidates now distinguish literal statement mentions from metadata-only technology overlaps and
preserve explicitly recorded scoped metrics. These unweighted observations are not semantic
support, inferred impact or a relevance score; candidate ordering remains by evidence ID.

**Resume generation is not implemented.** There is no cloud provider, ranking/planning engine,
database, template renderer, PDF compiler, API, or browser extension yet.
Local verification and hosted CI results are reported separately.

## Prerequisites and installation

- Python 3.12+ with `pip` and `venv` (on Ubuntu, install `python3.12-venv` if needed).
- Git. No API key, TeX installation, Docker, or paid service is required for offline Phase 2.
- The CI workflow targets Python 3.12 and 3.13 on Linux.
- Optional local inference: separately installed/running Ollama and a downloaded model such as
  Qwen3:4b. See [docs/OLLAMA.md](docs/OLLAMA.md); normal tests and fake mode do not require it.

From the repository root (Linux/macOS):

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.lock
python -m pip install --no-build-isolation --no-deps -e .
python -m pip check
```

On Windows, use `py -3.12 -m venv .venv` and `.venv\Scripts\Activate.ps1` instead.
The editable install points Python at `src/`, so source changes do not require reinstallation.

## Usage

```bash
resumeforge --help
resumeforge --version
python -m resumeforge --help
resumeforge validate-profile --profile examples/profiles/sample.md
resumeforge analyze-job --job examples/jobs/backend_intern.md \
  --mock-response examples/jobs/backend_intern.response.json
resumeforge match-evidence --profile examples/profiles/sample.md \
  --job examples/jobs/backend_intern.md \
  --requirements examples/jobs/backend_intern.response.json --confirm-review
```

Running `resumeforge` without arguments also displays help and exits successfully.
Unknown commands/options fail with exit code 2. No generation commands are advertised
until implemented. Profile validation is local and read-only; help/version do not read the profile.
In default fake mode, `analyze-job` reads only the selected job and response fixture, not the
profile. It emits JSON to stdout and an offline notice to stderr. The required mock fixture is
not generated from the job.

For real local extraction, after starting a cloud-disabled Ollama server and downloading its model:

```bash
resumeforge analyze-job --job examples/jobs/backend_intern.md \
  --provider ollama --model qwen3:4b --timeout 600
```

Local mode reads only the selected job, not a mock fixture or profile. It checks server cloud
disablement and local model metadata before sending job text, uses only `127.0.0.1`, and has no
cloud fallback, auto-pull, proxy or redirect support. See [docs/JOB_ANALYSIS.md](docs/JOB_ANALYSIS.md)
for the schema and [docs/OLLAMA.md](docs/OLLAMA.md) for setup, guards and resource limits.

`match-evidence` is always offline and requires all three explicit paths plus review confirmation.
It never loads a default profile or starts inference. Its JSON includes private source-derived
evidence, not a resume or qualification verdict; see [docs/MATCHING.md](docs/MATCHING.md) for
eligibility, literal-match limits and review findings.

### Create your private profile

```bash
mkdir -p data/profile
cp examples/profiles/sample.md data/profile/user_information.md
# Replace the fictional information in the private copy.
resumeforge validate-profile
```

Read [docs/PROFILE_FORMAT.md](docs/PROFILE_FORMAT.md) for all fields and conventions.
Facts live in YAML front matter, with stable IDs such as `exp_example` and `acc_api`.
The Markdown body preserves rough notes without promoting them into verified facts.
Invalid files, duplicate IDs, broken references and reversed dates fail with exit code 1.
Structurally valid but incomplete profiles exit 0 with warnings. A `verified` label records
your review; the application does not prove factual truth or check bullet entailment yet.
For an existing narrative, follow the guide's import checklist: keep claims pending review,
preserve unfinished-work caveats and conflicting dates, and never put real data in examples/tests.
In 0.5.0, optional typed completion states and `resume_preferences` are validated in schema version 1.
Old profiles remain valid, with unknown-state warnings; notes are never migrated automatically.
Preferences do not approve facts or select content. See [the field reference](docs/PROFILE_FORMAT.md).

## Configuration and privacy

Provider/model/limits are explicit CLI options. ResumeForge does not load `.env` or read
`OLLAMA_HOST`; `.env.example` documents this. `OLLAMA_NO_CLOUD=1` and the loopback bind address
must be set on the separate Ollama server process, not inferred from a ResumeForge `.env` file.
`config/resume_rules.md` records future writing policy, not an active prompt or validator.

The default private profile location is `data/profile/user_information.md`, relative to your
working directory; use `--profile` for another location. All of `data/`,
generated artifact directories, `.env` files, PDFs, LaTeX output, and databases are ignored
by Git by default. Put future sanitized fixtures under `tests/fixtures/` or `examples/`,
not in private `data/`. Git ignores prevent accidental tracking, **not disclosure**:
review staged changes before every commit and never force-add private files.

## Development checks

```bash
python -m ruff check .
python -m ruff format --check .
python -m mypy
python -m pytest tests/unit
python -m pytest tests/integration
python -m pytest --cov=resumeforge --cov-report=term-missing
python -m build --no-isolation
```

CI runs these checks plus a wheel-install smoke test outside the repository. The initial
coverage threshold is 90%, with branch measurement and subprocess coverage.
Normal tests require no credentials, external network access, or live LLM calls; one integration
test uses a synthetic loopback HTTP server. Dependency installation does require package-index access.
The wheel smoke test also validates the fictional profile and replays a fictional job analysis.
This is **not** an end-to-end
resume-generation test; that comes in Phase 5.

`requirements-dev.lock` pins the development, runtime, and build-tool dependencies resolved
on Python 3.12; `pyproject.toml` declares supported ranges. See
[CONTRIBUTING.md](CONTRIBUTING.md) for deliberate dependency updates.

## Architecture and roadmap

The CLI will call an interface-independent engine:

```text
Markdown profile + job description
  -> validated facts and requirements
  -> evidence matching and resume plan
  -> structured bullets and claim validation
  -> user review / approval
  -> trusted LaTeX rendering and PDF checks
  -> PDF, editable TeX, plain text, tailoring report
```

SQLite history will store decisions and versions, never promote AI output into authoritative
biographical facts. A useful MVP spans Phases 1–5; simple persistent history follows in Phase 6.

See [ARCHITECTURE.md](ARCHITECTURE.md), [docs/ROADMAP.md](docs/ROADMAP.md),
[docs/DECISIONS.md](docs/DECISIONS.md), and [docs/DEVELOPMENT_LOG.md](docs/DEVELOPMENT_LOG.md).
Agent instructions live in [AGENTS.md](AGENTS.md).

## Docker and deployment

Not implemented. Local development does not require Docker. A non-root container with
pinned dependencies, TeX tooling, mounted private data, and no embedded secrets is planned
after the core generation workflow. No cloud resources or automatic deployment are configured.

## Limitations

No resume-generation, factual-correctness, ATS-compatibility, or one-page-layout guarantees
exist at this stage. Future automated checks will still require human review, including
visual PDF inspection. Before incorporating Jake's Resume, its upstream license and
attribution must be verified and preserved. A project license has not yet been selected.
