from __future__ import annotations

from app.config import AppConfig
from app.contact_extractor import extract_emails, extract_phones
from app.confidence import calculate_confidence
from app.curated_research import curated_program_research
from app.linkedin_discovery import discover_linkedin_from_pages
from app.models import OrganisationResult, Page
from app.person_ranker import extract_people, rank_people
from app.program_extractor import extract_program_research
from app.relevance_classifier import classify_roles, score_relevance


def build_result(pages: list[Page], config: AppConfig, errors: list[str], organisation_name: str = "", website: str = "") -> OrganisationResult:
    text = "\n".join(page.text for page in pages)
    emails = extract_emails(pages)
    phones = extract_phones(pages, config.country_default)
    people = extract_people(pages)
    key_person, alt_person = rank_people(people)
    relevance_score, evidence = score_relevance(pages, config)
    program_research = extract_program_research(pages, organisation_name)
    curated = curated_program_research(organisation_name, website)

    result = OrganisationResult()
    result.errors = errors.copy()
    result.role_in_deal = classify_roles(text, config)
    result.evidence_relevance = evidence
    result.named_programme = program_research.named_programme or curated.named_programme
    result.what_they_do = program_research.what_they_do or curated.what_they_do
    result.custom_appreciation = program_research.custom_appreciation or curated.custom_appreciation
    result.why_xperimentor_fits = program_research.why_xperimentor_fits or curated.why_xperimentor_fits
    result.source = "; ".join(sorted({page.source_label for page in pages}))
    result.linkedin_url = discover_linkedin_from_pages(pages) if config.enable_linkedin_discovery else ""

    usable_emails = [item for item in emails if item.category != "irrelevant"]
    if key_person:
        result.key_person = key_person.name
        result.designation = key_person.designation
    elif usable_emails or phones:
        result.key_person = "General contact"
        result.designation = "Organisation contact"

    if alt_person:
        result.alt_person = alt_person.name
        result.alt_designation = alt_person.designation

    if usable_emails:
        result.email = usable_emails[0].email
        result.other_emails = "; ".join(item.email for item in usable_emails[1:])
    else:
        result.errors.append("NO_EMAIL_FOUND")
    if phones:
        result.phone = phones[0].phone
        result.other_phones_routes = "; ".join(item.phone for item in phones[1:])
    else:
        result.errors.append("NO_PHONE_FOUND")

    result.confidence, result.verification_status = calculate_confidence(result)
    result.notes_next_step = notes_for(result, relevance_score)
    return result


def notes_for(result: OrganisationResult, relevance_score: int) -> str:
    if relevance_score >= 70 and result.key_person and result.email:
        return "Strong education/STEM relevance. Contact recommended person first."
    if relevance_score >= 70 and result.email:
        return "Strong education/STEM relevance. General contact found; manual leader verification recommended."
    if result.key_person and not result.email:
        return "Leader identified but no direct email. Use official contact route or verify manually."
    if not result.email and not result.phone:
        return "No usable public contact found. Manual review required."
    if relevance_score < 25:
        return "Limited education/STEM evidence found. Review fit before outreach."
    return "Public organisation contact found. Review before adding to outreach sequence."
