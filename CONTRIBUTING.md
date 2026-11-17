# Contributing

Read `AGENTS.md` and the current roadmap first. Work on one acceptance-tested feature at a time.
Discuss scope changes, new paid services, or major architecture changes before implementation.

## Local workflow

1. Follow the virtual-environment and locked installation instructions in `README.md`.
2. Inspect `git status`; preserve existing work. Start a focused branch, for example
   `git switch -c feat/profile-schema`.
3. Define behavior/acceptance criteria, then add tests alongside small typed modules.
4. Run all checks:

```bash
python -m ruff check .
python -m ruff format --check .
python -m mypy
python -m pytest --cov=resumeforge --cov-report=term-missing
python -m build --no-isolation
python -m pip check
```

Use `python -m ruff format .` to apply formatting. Keep tests deterministic and independent
of live LLM APIs, credentials and private data. Use `pytest -m integration` for installed CLI
checks; resume/PDF integration tests will be introduced with those implementations.

5. Update relevant docs and `docs/DEVELOPMENT_LOG.md`. State what actually ran, including skips.
6. Review `git diff` and `git diff --cached`, especially for private data and secrets. Stage
   intended files explicitly. Commit verified work; never bypass failing checks to claim completion.

Use small Conventional Commit-style messages: `feat: ...`, `fix: ...`, `test: ...`, `docs: ...`,
or `chore: ...`. Open a pull request where a remote/collaboration workflow exists. Never force-push
or change remotes without authorization. If no remote exists, report that blocker; do not create one.

## Dependencies

Add runtime dependencies only when a real feature needs them. `pyproject.toml` records compatible
ranges; `requirements-dev.lock` records exact resolved runtime, development and build-tool versions.
It is a pip-compatible snapshot, not a cryptographically hashed or universal resolver lock.

To deliberately refresh it, create a fresh temporary virtual environment using Python 3.12,
install `-e '.[dev]'`, then capture `python -m pip freeze --exclude-editable` into
`requirements-dev.lock`. Review the diff for editable paths, private index URLs and unexpected
packages. Validate a clean install using the README commands and run all checks on supported
Python versions. Commit the declaration and lock together. Do not refresh dependencies incidentally.

## Privacy, licenses and reporting

Use fictional sample information only. Keep private inputs under ignored `data/`, outputs under
ignored `artifacts/`, and secrets outside Git. Ignores do not protect files already tracked;
inspect staged content. If a secret leaks, rotate it and arrange history cleanup explicitly.

Do not add third-party templates/assets without license review and preserved attribution.
A project license remains to be chosen before public distribution. Avoid including private resume
or contact details in issue reports, logs, screenshots or test failures.
