"""Repository-only entry point for the fixed fictional job benchmark."""

from pathlib import Path

from resumeforge.jobs.benchmark import main

if __name__ == "__main__":
    raise SystemExit(main(corpus_root=Path(__file__).resolve().parents[1] / "examples/jobs"))
