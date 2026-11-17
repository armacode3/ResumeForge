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
CompletionStatus = Literal["unknown", "planned", "in_progress", "completed", "on_hold", "cancelled"]
ResumeSection = Literal[
    "education",
    "experiences",
    "projects",
    "organizations",
    "research",
    "certifications",
    "awards",
    "additional_experience",
    "skills",
    "coursework",
]
ContentCount = Annotated[int, Field(ge=0, le=20)]


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
    completion_status: CompletionStatus = "unknown"

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
    completion_status: CompletionStatus = "unknown"


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


class ResumePreferences(ProfileModel):
    """User constraints, not verified facts or a guarantee of feasible resume layout."""

    required_sections: list[ResumeSection] = Field(default_factory=list)
    required_entry_ids: list[EntryId] = Field(default_factory=list)
    excluded_entry_ids: list[EntryId] = Field(default_factory=list)
    min_projects: ContentCount | None = None
    max_projects: ContentCount | None = None
    min_bullets_per_entry: ContentCount | None = None
    max_bullets_per_entry: ContentCount | None = None

    @model_validator(mode="after")
    def check_constraints(self) -> Self:
        for name in ("required_sections", "required_entry_ids", "excluded_entry_ids"):
            values = getattr(self, name)
            if len(values) != len(set(values)):
                raise ValueError(f"resume_preferences.{name} must not contain duplicates")
        if set(self.required_entry_ids) & set(self.excluded_entry_ids):
            raise ValueError("resume_preferences cannot both require and exclude an entry")
        for minimum, maximum, label in (
            (self.min_projects, self.max_projects, "projects"),
            (self.min_bullets_per_entry, self.max_bullets_per_entry, "bullets_per_entry"),
        ):
            if minimum is not None and maximum is not None and minimum > maximum:
                raise ValueError(f"resume_preferences min_{label} must not exceed max_{label}")
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
    resume_preferences: ResumePreferences = Field(default_factory=ResumePreferences)

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

    def _section_has_available_content(self, section: ResumeSection, excluded: set[str]) -> bool:
        if section == "skills":
            return any(getattr(self.skills, name) for name in Skills.model_fields)
        if section == "coursework":
            return bool(self.coursework)
        return any(entry.id not in excluded for entry in getattr(self, section))

    @model_validator(mode="after")
    def check_resume_preferences(self) -> Self:
        preferences = self.resume_preferences
        entry_ids = {entry.id for entry in self.entries()}
        for name in ("required_entry_ids", "excluded_entry_ids"):
            if not set(getattr(preferences, name)) <= entry_ids:
                raise ValueError(
                    f"resume_preferences.{name} must reference existing profile entries"
                )
        excluded = set(preferences.excluded_entry_ids)
        for section in preferences.required_sections:
            if not self._section_has_available_content(section, excluded):
                raise ValueError(
                    "resume_preferences.required_sections must have non-excluded content"
                )
        available_projects = sum(entry.id not in excluded for entry in self.projects)
        if preferences.min_projects is not None and preferences.min_projects > available_projects:
            raise ValueError("resume_preferences.min_projects exceeds non-excluded project count")
        required_projects = sum(
            entry.id in preferences.required_entry_ids for entry in self.projects
        )
        if "projects" in preferences.required_sections:
            required_projects = max(1, required_projects)
        if preferences.max_projects is not None and required_projects > preferences.max_projects:
            raise ValueError(
                "resume_preferences.max_projects conflicts with required project content"
            )
        return self
