from __future__ import annotations

import re
from dataclasses import dataclass

import phonenumbers
from bs4 import BeautifulSoup

from app.models import Page

EMAIL_RE = re.compile(r"(?<![\w.+-])([A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,})(?![\w.+-])", re.I)
BAD_EMAIL_PREFIXES = ("careers", "jobs", "noreply", "no-reply", "webmaster", "example", "test")
BAD_EMAIL_DOMAINS = ("example.com", "example.org", "example.net", "test.com", "test.org", "test.net")
ROLE_PREFIXES = ("partnership", "partnerships", "program", "programs", "director", "office", "csr")
GENERAL_PREFIXES = ("info", "contact", "hello", "admin", "enquiry", "enquiries", "mail")


@dataclass(frozen=True)
class EmailCandidate:
    email: str
    category: str
    source_url: str


@dataclass(frozen=True)
class PhoneCandidate:
    phone: str
    source_url: str


def extract_emails(pages: list[Page]) -> list[EmailCandidate]:
    seen: set[str] = set()
    found: list[EmailCandidate] = []
    for page in pages:
        soup = BeautifulSoup(page.html, "html.parser")
        candidates = set(EMAIL_RE.findall(page.text or ""))
        for link in soup.select("a[href^='mailto:']"):
            candidates.add(link.get("href", "").split(":", 1)[-1].split("?", 1)[0])
        for raw in candidates:
            email = raw.strip().lower()
            if not email or email in seen:
                continue
            seen.add(email)
            found.append(EmailCandidate(email=email, category=categorize_email(email), source_url=page.url))
    return sorted(found, key=email_priority)


def categorize_email(email: str) -> str:
    prefix, domain = email.split("@", 1)
    prefix = prefix.lower()
    domain = domain.lower()
    if domain in BAD_EMAIL_DOMAINS:
        return "irrelevant"
    if prefix.startswith(BAD_EMAIL_PREFIXES):
        return "irrelevant"
    if "." in prefix and not prefix.startswith(GENERAL_PREFIXES):
        return "personal/direct"
    if prefix.startswith(ROLE_PREFIXES):
        return "role-based"
    if prefix.startswith(GENERAL_PREFIXES):
        return "general organisation"
    return "role-based"


def email_priority(candidate: EmailCandidate) -> tuple[int, str]:
    order = {
        "personal/direct": 0,
        "role-based": 1,
        "general organisation": 2,
        "irrelevant": 3,
    }
    prefix = candidate.email.split("@", 1)[0]
    bonus = 0 if prefix.startswith(ROLE_PREFIXES) else 1
    return (order.get(candidate.category, 9), bonus, candidate.email)


def extract_phones(pages: list[Page], region: str = "IN") -> list[PhoneCandidate]:
    seen: set[str] = set()
    phones: list[PhoneCandidate] = []
    for page in pages:
        text = page.text or ""
        for match in phonenumbers.PhoneNumberMatcher(text, region):
            formatted = normalize_phone(match.raw_string, region)
            if formatted and formatted not in seen:
                seen.add(formatted)
                phones.append(PhoneCandidate(phone=formatted, source_url=page.url))
    return phones


def normalize_phone(value: str, region: str = "IN") -> str:
    try:
        number = phonenumbers.parse(value, region)
    except phonenumbers.NumberParseException:
        digits = re.sub(r"\D", "", value)
        if region == "IN" and len(digits) == 10 and digits[0] in "6789":
            return f"+91 {digits}"
        return ""
    if not phonenumbers.is_possible_number(number):
        return ""
    if region == "IN" and number.country_code == 91:
        national = str(number.national_number)
        if len(national) == 10 and national[0] in "6789":
            return f"+91 {national}"
    return phonenumbers.format_number(number, phonenumbers.PhoneNumberFormat.INTERNATIONAL)
