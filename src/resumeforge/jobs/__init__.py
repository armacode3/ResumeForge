"""Local job loading and validated, evidence-linked structured analysis."""

from resumeforge.jobs.analysis import JobAnalysisError, analyze_job
from resumeforge.jobs.models import JobAnalysis, JobRequirements
from resumeforge.jobs.source import JobDocument, load_job

__all__ = [
    "JobAnalysis",
    "JobAnalysisError",
    "JobDocument",
    "JobRequirements",
    "analyze_job",
    "load_job",
]
