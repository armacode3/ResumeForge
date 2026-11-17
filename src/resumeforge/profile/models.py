"""Version-one profile contracts; accepting structure does not prove factual truth."""

from typing import Annotated, ClassVar, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, StringConstraints, model_validator

Text = Annotated[str, StringConstraints(min_length=1, pattern=r"\S")]
EntryId = Annotated[
    str, StringConstraints(pattern=r"^(edu|exp|proj|org|res|cert|award|other)_[a-z0-9_]+$")
]
AccomplishmentId = Annotated[str, StringConstraints(pattern=r"^acc_[a-z0-9_]+$")]
BulletId = Annotated[str, StringConstraints(pattern=r"^bullet_[a-z0-9_]+$")]
Month = Annotated[str, StringConstraints(pattern=r"^[1-9][0-9]{3}-(0[1-9]|1[0-2])$")]
Email = Annotated[str, StringConstraints(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")]


class ProfileModel(BaseModel):
    """Reject typos/coercion and suppress private input values in validation errors."""

    model_config = ConfigDict(extra="forbid", strict=True, hide_input_in_errors=True)


class Contact(ProfileModel):
    name: Text
    email: Email | None = None
    phone: Text | None = None
    location: Text | None = None
    links: list[HttpUrl] = Field(default_factory=list)


class Skills(ProfileModel):
    languages: list[Text] = Field(default_factory=list)
    frameworks: list[Text] = Field(default_factory=list)
    libraries: list[Text] = Field(default_factory=list)
    tools: list[Text] = Field(default_factory=list)
    platforms: list[Text] = Field(default_factory=list)
    other: list[Text] = Field(default_factory=list)


class ProfileEntry(ProfileModel):
    """Shared record for education, employment, projects and other background sections."""

    id: EntryId
    title: Text
    organization: Text | None = None
    location: Text | None = None
    start_date: Month | None = None
    end_date: Month | Literal["present"] | None = None
    details: list[Text] = Field(default_factory=list)
    technologies: list[Text] = Field(default_factory=list)

    @model_validator(mode="after")
    def check_dates(self) -> Self:
        if (
            self.start_date is not None
            and self.end_date is not None
            and self.end_date != "present"
            and self.end_date < self.start_date
        ):
            raise ValueError("end_date must not precede start_date")
        return self


class Accomplishment(ProfileModel):
    id: AccomplishmentId
    entry_id: EntryId
    statement: Text
    verified: bool = False
    technologies: list[Text] = Field(default_factory=list)
    metrics: list[Text] = Field(default_factory=list)


class VerifiedBullet(ProfileModel):
    """User-provided verified wording, not historical model output."""

    id: BulletId
    text: Text
    accomplishment_ids: list[AccomplishmentId] = Field(min_length=1)

    @model_validator(mode="after")
    def check_distinct_references(self) -> Self:
        if len(set(self.accomplishment_ids)) != len(self.accomplishment_ids):
            raise ValueError("accomplishment_ids must not contain duplicate references")
        return self


class UserProfile(ProfileModel):
    schema_version: Annotated[int, Field(ge=1, le=1)]
    person: Contact
    education: list[ProfileEntry] = Field(default_factory=list)
    experiences: list[ProfileEntry] = Field(default_factory=list)
    projects: list[ProfileEntry] = Field(default_factory=list)
    organizations: list[ProfileEntry] = Field(default_factory=list)
    research: list[ProfileEntry] = Field(default_factory=list)
    certifications: list[ProfileEntry] = Field(default_factory=list)
    awards: list[ProfileEntry] = Field(default_factory=list)
    additional_experience: list[ProfileEntry] = Field(default_factory=list)
    skills: Skills = Field(default_factory=Skills)
    coursework: list[Text] = Field(default_factory=list)
    accomplishments: list[Accomplishment] = Field(default_factory=list)
    verified_bullets: list[VerifiedBullet] = Field(default_factory=list)

    SECTION_PREFIXES: ClassVar[dict[str, str]] = {
        "education": "edu_",
        "experiences": "exp_",
        "projects": "proj_",
        "organizations": "org_",
        "research": "res_",
        "certifications": "cert_",
        "awards": "award_",
        "additional_experience": "other_",
    }

    def entries(self) -> list[ProfileEntry]:
        """Return entries in stable section and source order."""
        return [entry for section in self.SECTION_PREFIXES for entry in getattr(self, section)]

    @model_validator(mode="after")
    def check_evidence_graph(self) -> Self:
        seen: set[str] = set()
        for section, prefix in self.SECTION_PREFIXES.items():
            for entry in getattr(self, section):
                if not entry.id.startswith(prefix):
                    raise ValueError(f"{section} IDs must start with {prefix}")
        identifiers = [entry.id for entry in self.entries()]
        identifiers.extend(item.id for item in self.accomplishments)
        identifiers.extend(bullet.id for bullet in self.verified_bullets)
        for identifier in identifiers:
            if identifier in seen:
                raise ValueError(f"duplicate ID: {identifier}")
            seen.add(identifier)
        entry_ids = {entry.id for entry in self.entries()}
        evidence = {item.id: item for item in self.accomplishments}
        for item in self.accomplishments:
            if item.entry_id not in entry_ids:
                raise ValueError(f"{item.id} references unknown entry_id: {item.entry_id}")
        for bullet in self.verified_bullets:
            for reference in bullet.accomplishment_ids:
                if reference not in evidence:
                    raise ValueError(f"{bullet.id} references unknown accomplishment: {reference}")
                if not evidence[reference].verified:
                    raise ValueError(
                        f"{bullet.id} references unverified accomplishment: {reference}"
                    )
        return self
