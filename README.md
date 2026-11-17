# ResumeForge

An evidence-first resume tailoring application, built incrementally. The goal is to turn
a verified Markdown profile and a job description into a reviewable, one-page resume
without inventing experience, technologies, or metrics.

## Current status: Phase 1 — profile knowledge base

Implemented: an installable Typer CLI with help/version output, unit and installed-entry-point
tests, privacy-ignore regression coverage, linting, formatting, strict typing, packaging checks,
and a GitHub Actions workflow. Profile support now includes a documented Markdown/YAML format,
Pydantic schemas, stable evidence IDs, safe parsing, source preservation, completeness warnings,
and the `validate-profile` command. A fictional sample covers every supported background section.

**Resume generation is not implemented.** There are no AI calls, job analyzer, database,
templates, PDF compiler, API, or browser extension yet. Local verification and hosted CI
results are reported separately.

## Prerequisites and installation

- Python 3.12+ with `pip` and `venv` (on Ubuntu, install `python3.12-venv` if needed).
- Git. No API key, TeX installation, Docker, or paid service is required for Phase 1.
- The CI workflow targets Python 3.12 and 3.13 on Linux.

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
```

Running `resumeforge` without arguments also displays help and exits successfully.
Unknown commands/options fail with exit code 2. No generation commands are advertised
until implemented. Profile validation is local and read-only; help/version do not read the profile.

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

## Configuration and privacy

There are no active configuration settings or environment variables yet. `.env.example`
documents this intentionally; it is not loaded by the application.
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
Normal tests require no credentials, network requests, or live LLM calls. Dependency installation
does require package-index access.
The wheel smoke test also validates the fictional profile. This is **not** an end-to-end
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
