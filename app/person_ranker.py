from __future__ import annotations

import re

from app.models import Page, Person

RANKED_TITLES = [
    "founder",
    "ceo",
    "chief executive officer",
    "executive director",
    "managing director",
    "director education",
    "director programs",
    "director programme",
    "head of stem",
    "head of science",
    "head of education",
    "head of partnerships",
    "csr head",
    "institutional relations",
    "program head",
    "programme head",
    "program manager",
    "programme manager",
    "regional head",
]
LOW_PRIORITY = ("hr", "careers", "administration", "accounts", "it support", "procurement")
NAME_RE = re.compile(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z.]+){1,3})\b")


def extract_people(pages: list[Page]) -> list[Person]:
    people: list[Person] = []
    seen: set[tuple[str, str]] = set()
    title_pattern = "|".join(re.escape(title) for title in RANKED_TITLES)
    line_re = re.compile(rf"(?P<name>[A-Z][A-Za-z.]+(?:\s+[A-Z][A-Za-z.]+){{1,3}}).{{0,80}}(?P<title>{title_pattern})", re.I)
    reverse_re = re.compile(rf"(?P<title>{title_pattern}).{{0,80}}(?P<name>[A-Z][A-Za-z.]+(?:\s+[A-Z][A-Za-z.]+){{1,3}})", re.I)
    for page in pages:
        for line in page.text.splitlines():
            if len(line) > 220:
                continue
            for regex in (line_re, reverse_re):
                match = regex.search(line)
                if not match:
                    continue
                name = clean_name(match.group("name"))
                title = clean_title(match.group("title"))
                key = (name.lower(), title.lower())
                if name and key not in seen:
                    seen.add(key)
                    people.append(Person(name=name, designation=title, source_url=page.url, relevance_score=score_title(title)))
    return sorted(people, key=lambda person: (-person.relevance_score, person.name))


def rank_people(people: list[Person]) -> tuple[Person | None, Person | None]:
    ranked = sorted(people, key=lambda person: (-person.relevance_score, person.name))
    key = ranked[0] if ranked else None
    alt = ranked[1] if len(ranked) > 1 else None
    return key, alt


def score_title(title: str) -> int:
    lowered = normalize_title(title)
    if any(term in lowered for term in LOW_PRIORITY):
        return 1
    for index, ranked_title in enumerate(RANKED_TITLES):
        if ranked_title in lowered:
            return 100 - index
    return 10


def normalize_title(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", title.lower()).strip()


def clean_name(name: str) -> str:
    return re.sub(r"\s+", " ", name).strip(" -:|,")


def clean_title(title: str) -> str:
    return re.sub(r"\s+", " ", title).strip(" -:|,").title()
