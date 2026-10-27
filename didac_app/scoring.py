from __future__ import annotations

from datetime import date, timedelta

from didac_app.config import DidacConfig
from didac_app.models import Lead


def enrich_lead(lead: Lead, config: DidacConfig) -> Lead:
    lead.score = score_lead(lead)
    lead.priority = priority_for(lead.score)
    lead.owner = owner_for(lead, config)
    lead.next_action = next_action_for(lead)
    if not lead.follow_up_date:
        lead.follow_up_date = default_follow_up_date(lead.priority)
    lead.email_subject = email_subject(lead)
    lead.email_draft = email_draft(lead)
    lead.whatsapp_draft = whatsapp_draft(lead)
    return lead


def score_lead(lead: Lead) -> int:
    text = joined(lead.lead_type, lead.role, lead.interest, lead.notes, lead.tags, lead.org)
    score = 0
    if any(term in text for term in ("csr", "foundation", "trust", "ngo", "government", "school network")):
        score += 25
    if any(term in text for term in ("stem", "science", "lab", "math", "robotics")):
        score += 25
    if any(term in text for term in ("government school", "govt school", "schools")):
        score += 15
    if any(term in text for term in ("budget", "proposal", "demo", "pilot")):
        score += 15
    if lead.timeline:
        score += 10
    if lead.email or lead.phone:
        score += 10
    if numeric_schools(lead.schools_count) >= 10:
        score += 10
    if any(term in text for term in ("student", "vendor", "job", "career")):
        score -= 20
    return max(0, min(100, score))


def priority_for(score: int) -> str:
    if score >= 75:
        return "Hot"
    if score >= 50:
        return "Warm"
    if score >= 25:
        return "Nurture"
    return "Low priority"


def owner_for(lead: Lead, config: DidacConfig) -> str:
    declared_role = joined(lead.lead_type, lead.organisation_type, lead.role)
    if "distributor" in declared_role or "dealer" in declared_role or "channel" in declared_role:
        return config.distributor_owner
    if "csr" in declared_role:
        return config.csr_owner
    if "ngo" in declared_role or "foundation" in declared_role or "trust" in declared_role:
        return config.ngo_owner
    if "school" in declared_role or "principal" in declared_role:
        return config.school_owner
    text = joined(lead.lead_type, lead.role, lead.notes, lead.tags)
    if "csr" in text:
        return config.csr_owner
    if "ngo" in text or "foundation" in text or "trust" in text:
        return config.ngo_owner
    if "school" in text or "principal" in text:
        return config.school_owner
    if "distributor" in text or "dealer" in text or "channel" in text:
        return config.distributor_owner
    if "student" in text or "vendor" in text or "media" in text:
        return config.low_priority_owner
    return config.default_owner


def next_action_for(lead: Lead) -> str:
    if lead.priority == "Hot":
        return "Send brochure now, then call or book demo within 24 hours."
    if lead.priority == "Warm":
        return "Send brochure/case study and schedule follow-up after the event."
    if lead.priority == "Nurture":
        return "Add to post-event nurture campaign."
    return "Review manually before follow-up."


def default_follow_up_date(priority: str) -> str:
    days = 1 if priority == "Hot" else 2 if priority == "Warm" else 7
    return (date.today() + timedelta(days=days)).isoformat()


def email_subject(lead: Lead) -> str:
    org = lead.org or "your schools"
    return f"DIDAC follow-up: Xperimentor Lab-in-Classroom for {org}"


def email_draft(lead: Lead) -> str:
    greeting = first_name(lead.name)
    org = lead.org or "your organisation"
    context = lead.interest or "hands-on science and math learning"
    return (
        f"Dear {greeting},\n\n"
        "It was good meeting you at DIDAC. I'm Chethan, writing on behalf of Xperimentor "
        "(Scikraft Education and Engineering Design Pvt. Ltd.), a Bengaluru-based organisation "
        "working with CSR teams, NGOs, and schools to bring curriculum-aligned Physics, Chemistry, "
        "Biology, and Mathematics labs into regular classrooms.\n\n"
        f"Based on our conversation, {org} may be exploring {context}. Xperimentor's Lab-in-Classroom "
        "system can convert an existing classroom into a functional science and math lab without a "
        "separate room or major infrastructure.\n\n"
        "We currently support 100+ government schools across 4 states, with 10,000+ students impacted, "
        "500+ teachers trained, and 94.9% active teacher adoption.\n\n"
        "Would you be open to a short follow-up call after DIDAC? I can share the brochure, case studies, "
        "and a pilot plan relevant to your schools.\n\n"
        "Best,\nChethan"
    )


def whatsapp_draft(lead: Lead) -> str:
    org = lead.org or "your organisation"
    return (
        f"Thank you for visiting the Xperimentor stall at DIDAC. Based on our discussion with {org}, "
        "I’m sharing our Lab-in-Classroom details. We can support hands-on Physics, Chemistry, Biology "
        "and Math learning in existing classrooms, with teacher training and impact reporting."
    )


def joined(*values: str) -> str:
    return " ".join(value or "" for value in values).lower()


def first_name(name: str) -> str:
    return name.split()[0] if name else "there"


def numeric_schools(value: str) -> int:
    digits = "".join(ch for ch in value if ch.isdigit())
    return int(digits) if digits else 0
