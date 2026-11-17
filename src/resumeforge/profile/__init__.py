"""Validated profile loading, independent of command-line and future HTTP interfaces."""

from resumeforge.profile.models import UserProfile
from resumeforge.profile.parser import ProfileDocument, ProfileError, load_profile, parse_profile
from resumeforge.profile.validation import find_profile_gaps

__all__ = [
    "ProfileDocument",
    "ProfileError",
    "UserProfile",
    "find_profile_gaps",
    "load_profile",
    "parse_profile",
]
