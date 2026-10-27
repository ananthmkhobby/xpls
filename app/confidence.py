from __future__ import annotations

from app.models import OrganisationResult


def calculate_confidence(result: OrganisationResult) -> tuple[int, str]:
    has_person = bool(result.key_person and result.key_person.lower() not in {"not named publicly", "general contact"})
    has_designation = bool(result.designation)
    has_email = bool(result.email and "not " not in result.email.lower())
    has_phone = bool(result.phone and "not " not in result.phone.lower())
    if has_person and has_designation and has_email and has_phone:
        return 100, "VERIFIED"
    if has_person and has_designation and has_email:
        return 95, "VERIFIED"
    if has_person and has_designation:
        return 65, "PARTIALLY_VERIFIED"
    if has_email or has_phone:
        return 75, "PARTIALLY_VERIFIED"
    if result.errors:
        return 35, "REVIEW_REQUIRED"
    return 50, "REVIEW_REQUIRED"
