"""Strict extraction contracts carrying literal job-description evidence."""

from typing import Annotated, ClassVar, Self

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

Text = Annotated[str, StringConstraints(min_length=1, max_length=8192, pattern=r"\S")]
JobItemId = Annotated[str, StringConstraints(max_length=80, pattern=r"^job_[a-z0-9_]+$")]


class JobModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, hide_input_in_errors=True)


class QuotedFact(JobModel):
    text: Text = Field(
        description="Copy an exact source span, preserving capitalization; "
        "never title-case or paraphrase."
    )
    source_quote: Text = Field(
        description="Verbatim source span containing text with exactly the same capitalization."
    )

    @model_validator(mode="after")
    def check_literal_text(self) -> Self:
        if self.text not in self.source_quote:
            raise ValueError("text must appear exactly in source_quote; do not paraphrase")
        return self


class JobItem(QuotedFact):
    id: JobItemId


JobItems = Annotated[list[JobItem], Field(max_length=200)]


class JobRequirements(JobModel):
    schema_version: Annotated[int, Field(ge=1, le=1)]
    company: QuotedFact | None = Field(
        description="Explicit employer name, or JSON null if absent; "
        "never empty strings or an empty object."
    )
    job_title: QuotedFact | None = Field(
        description="Explicit role title, or JSON null if absent; "
        "do not infer a title from responsibilities."
    )
    responsibilities: JobItems
    required_qualifications: JobItems
    preferred_qualifications: JobItems
    programming_languages: JobItems
    frameworks: JobItems
    technical_concepts: JobItems
    domain_terms: JobItems
    evidence_sought: JobItems

    ITEM_FIELDS: ClassVar[tuple[str, ...]] = (
        "responsibilities",
        "required_qualifications",
        "preferred_qualifications",
        "programming_languages",
        "frameworks",
        "technical_concepts",
        "domain_terms",
        "evidence_sought",
    )

    def items(self) -> list[JobItem]:
        return [item for section in self.ITEM_FIELDS for item in getattr(self, section)]

    def facts(self) -> list[QuotedFact]:
        metadata = [fact for fact in [self.company, self.job_title] if fact is not None]
        return [*metadata, *self.items()]

    @model_validator(mode="after")
    def check_duplicates(self) -> Self:
        identifiers = [item.id for item in self.items()]
        if len(set(identifiers)) != len(identifiers):
            raise ValueError("Job item IDs must be unique across all sections")
        for section in self.ITEM_FIELDS:
            texts = [item.text.casefold().strip() for item in getattr(self, section)]
            if len(set(texts)) != len(texts):
                raise ValueError(f"Duplicate item text in {section}")
        return self


class JobAnalysis(JobModel):
    schema_version: Annotated[int, Field(ge=1, le=1)] = 1
    source_sha256: Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{64}$")]
    provider: Text
    model: Text
    prompt_version: Text
    requirements: JobRequirements
    warnings: list[str]
