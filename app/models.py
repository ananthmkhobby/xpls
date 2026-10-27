from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Page:
    url: str
    title: str
    text: str
    html: str
    source_label: str = "Website"


@dataclass
class Person:
    name: str
    designation: str = ""
    email: str = ""
    phone: str = ""
    source_url: str = ""
    relevance_score: int = 0


@dataclass
class OrganisationResult:
    city: str = ""
    role_in_deal: str = ""
    key_person: str = ""
    designation: str = ""
    email: str = ""
    confidence: int = 0
    phone: str = ""
    linkedin_url: str = ""
    alt_person: str = ""
    alt_designation: str = ""
    alt_email: str = ""
    alt_phone: str = ""
    other_emails: str = ""
    other_phones_routes: str = ""
    source: str = ""
    evidence_relevance: str = ""
    named_programme: str = ""
    what_they_do: str = ""
    custom_appreciation: str = ""
    why_xperimentor_fits: str = ""
    notes_next_step: str = ""
    verification_status: str = "REVIEW_REQUIRED"
    errors: list[str] = field(default_factory=list)
