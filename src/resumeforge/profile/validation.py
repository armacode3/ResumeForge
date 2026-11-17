"""Non-fatal completeness findings, separate from structural/schema errors."""

from resumeforge.profile.models import UserProfile


def find_profile_gaps(profile: UserProfile) -> list[str]:
    """Flag gaps without inferring facts or requiring numerical impact."""
    warnings: list[str] = []
    if not profile.person.email and not profile.person.phone:
        warnings.append(
            "person: no email or phone supplied; add a contact method before rendering."
        )
    if not profile.education:
        warnings.append("education: no entries supplied.")
    if not profile.experiences and not profile.projects:
        warnings.append("No experience or project entries supplied; add relevant background.")
    if not any(item.verified for item in profile.accomplishments):
        warnings.append("No verified accomplishments; review evidence before tailoring.")
    verified_entries = {item.entry_id for item in profile.accomplishments if item.verified}
    for entry in profile.entries():
        if entry.id.startswith(("edu_", "exp_")) and entry.organization is None:
            warnings.append(f"{entry.id}: missing institution or employer name.")
        if entry.start_date is None or entry.end_date is None:
            warnings.append(
                f"{entry.id}: incomplete dates; supply known dates rather than guessing."
            )
        if entry.id not in verified_entries:
            warnings.append(f"{entry.id}: no verified accomplishment evidence linked.")
    for item in profile.accomplishments:
        if not item.verified:
            warnings.append(f"{item.id}: unverified; user review required before use as evidence.")
    return warnings
