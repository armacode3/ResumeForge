"""Repository-only entry point for fixed fictional wording evaluation."""

from pathlib import Path

from resumeforge.resume.benchmark import main

if __name__ == "__main__":
    raise SystemExit(
        main(corpus_root=Path(__file__).resolve().parents[1] / "examples/wording/evaluation")
    )
