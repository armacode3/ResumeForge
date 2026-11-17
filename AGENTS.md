# ResumeForge agent instructions

## Start every session

Read `README.md`, `ARCHITECTURE.md`, `docs/DECISIONS.md`, `docs/ROADMAP.md`, and
`docs/DEVELOPMENT_LOG.md`. Inspect `git status`, the current branch, recent history, and
configured remotes. Preserve unfamiliar changes. This file is the canonical agent guidance;
do not create conflicting duplicate instructions.

## Purpose and current state

Build truthful, evidence-linked resumes from a verified Markdown profile and a job description.
Only Phase 0 is implemented: package metadata, Typer help/version CLI, tests, tooling, and CI.
Do not imply that profile validation, AI generation, PDFs, or history already work.

## Stack and repository map

- Python 3.12+, Typer, pytest, Ruff, strict mypy; `requirements-dev.lock` pins tooling.
- `src/resumeforge/`: installed application; `cli.py` is the presentation boundary.
- `tests/unit/`, `tests/integration/`: deterministic tests; later sanitized fixtures here.
- `config/resume_rules.md`: policy only, not currently loaded by code.
- `docs/`: decisions, roadmap, development log; `.github/workflows/ci.yml`: checks.
- `data/profile/user_information.md`: future private input, ignored; never create real data in Git.
- Planned only: Pydantic models, provider interfaces, Jinja2, LaTeX/PyMuPDF, SQLite,
  then Docker, FastAPI, and a Manifest V3 extension. Add dependencies when needed.

## Architecture and truthfulness

Keep domain logic independent of Typer and future HTTP interfaces. Use small typed modules,
validated schemas at boundaries, and dependency injection for external providers.
Generate a structured resume before rendering; do not let an LLM author arbitrary LaTeX.
Track every claim to stable accomplishment IDs and verified source evidence. Never invent
metrics, technology use, responsibilities, or ownership. Flag insufficient evidence for explicit
user review. Historical AI output is not a source of verified facts. Prefer deterministic
validation; AI review is additional evidence, not proof. No vector database without a real need.

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
python -m ruff check .
python -m ruff format --check .
python -m mypy
python -m pytest --cov=resumeforge --cov-report=term-missing
python -m build --no-isolation
```

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
