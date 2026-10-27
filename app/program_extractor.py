from __future__ import annotations

import re
from dataclasses import dataclass

from bs4 import BeautifulSoup

from app.models import Page

PROGRAM_KEYWORDS = (
    "programme",
    "program",
    "initiative",
    "project",
    "campaign",
    "mission",
    "model",
    "school",
    "education",
    "stem",
    "science",
    "teacher",
    "learning",
    "classroom",
    "csr",
)


@dataclass(frozen=True)
class ProgramResearch:
    named_programme: str = ""
    what_they_do: str = ""
    custom_appreciation: str = ""
    why_xperimentor_fits: str = ""


def extract_program_research(pages: list[Page], organisation_name: str = "") -> ProgramResearch:
    candidates = []
    summaries = []
    for page in pages:
        soup = BeautifulSoup(page.html, "html.parser")
        for tag in soup(["script", "style", "noscript", "nav", "footer"]):
            tag.decompose()
        for heading in soup.find_all(["h1", "h2", "h3", "h4"]):
            heading_text = clean_heading(heading.get_text(" ", strip=True))
            if not useful_heading(heading_text):
                continue
            context = nearby_text(heading)
            score = relevance_score(f"{heading_text} {context}", page.url)
            if score > 0:
                candidates.append((score, heading_text, context, page.url))
        for sentence in sentence_candidates(page.text):
            score = relevance_score(sentence, page.url)
            if score > 0:
                summaries.append((score, sentence, page.url))

    candidates = dedupe_candidates(sorted(candidates, reverse=True))
    summaries = dedupe_summaries(sorted(summaries, reverse=True))
    named = "; ".join(item[1] for item in candidates[:3])
    what = choose_summary(candidates, summaries)
    appreciation = build_appreciation(organisation_name, named, what)
    fit = build_fit_reason(f"{named} {what}")
    return ProgramResearch(
        named_programme=named,
        what_they_do=what,
        custom_appreciation=appreciation,
        why_xperimentor_fits=fit,
    )


def useful_heading(text: str) -> bool:
    if not text or len(text) < 4 or len(text) > 90:
        return False
    lowered = text.lower()
    ignored = ("home", "menu", "contact", "privacy", "terms", "donate now", "read more")
    return not any(lowered == item for item in ignored)


def nearby_text(heading) -> str:
    parts = []
    for sibling in heading.find_next_siblings(limit=4):
        if sibling.name in {"h1", "h2", "h3", "h4"}:
            break
        text = clean_text(sibling.get_text(" ", strip=True))
        if text:
            parts.append(text)
    return short_join(parts, 320)


def sentence_candidates(text: str) -> list[str]:
    normalized = clean_text(text)
    pieces = re.split(r"(?<=[.!?])\s+", normalized)
    return [piece for piece in pieces if 70 <= len(piece) <= 260]


def relevance_score(text: str, url: str = "") -> int:
    lowered = text.lower()
    score = 0
    weighted = {
        "stem": 8,
        "science": 7,
        "teacher": 6,
        "government school": 6,
        "school": 5,
        "classroom": 5,
        "learning": 4,
        "education": 4,
        "csr": 4,
        "programme": 3,
        "program": 3,
        "initiative": 3,
        "project": 2,
    }
    for keyword, points in weighted.items():
        if keyword in lowered:
            score += points
    if any(keyword in url.lower() for keyword in ("program", "project", "education", "school", "impact", "csr")):
        score += 2
    if any(term in lowered for term in ("copyright", "cookie", "privacy policy", "all rights reserved")):
        score -= 10
    return score


def dedupe_candidates(items: list[tuple[int, str, str, str]]) -> list[tuple[int, str, str, str]]:
    seen = set()
    result = []
    for score, heading, context, url in items:
        key = normalize_key(heading)
        if key in seen:
            continue
        seen.add(key)
        result.append((score, heading, context, url))
    return result


def dedupe_summaries(items: list[tuple[int, str, str]]) -> list[tuple[int, str, str]]:
    seen = set()
    result = []
    for score, sentence, url in items:
        key = normalize_key(sentence[:90])
        if key in seen:
            continue
        seen.add(key)
        result.append((score, sentence, url))
    return result


def choose_summary(candidates: list[tuple[int, str, str, str]], summaries: list[tuple[int, str, str]]) -> str:
    if candidates:
        _, heading, context, _ = candidates[0]
        if context:
            return trim_sentence(f"{heading}: {context}", 360)
        return heading
    if summaries:
        return trim_sentence(summaries[0][1], 360)
    return ""


def build_appreciation(organisation_name: str, named_programme: str, what_they_do: str) -> str:
    if named_programme and what_they_do:
        first_program = named_programme.split(";", 1)[0]
        detail = remove_repeated_heading(what_they_do, first_program)
        return (
            f"We were glad to see your work through {first_program}, especially the focus on "
            f"{lower_first(detail)}"
        )
    if what_they_do:
        return f"We were glad to learn about your work, especially how it connects to {lower_first(what_they_do)}"
    if named_programme:
        return f"We were glad to see your initiatives such as {named_programme}."
    return ""


def build_fit_reason(text: str) -> str:
    lowered = text.lower()
    if "government school" in lowered or "school" in lowered:
        return "Xperimentor can add a hands-on science and math layer to the schools already being served, without requiring a separate lab room or major infrastructure."
    if "teacher" in lowered or "training" in lowered:
        return "Xperimentor can support this by giving teachers structured experiments, onboarding, mentoring, and assessment data they can use in regular classrooms."
    if "csr" in lowered or "partner" in lowered:
        return "Xperimentor can give CSR partners a measurable STEM education outcome with classroom usage, teacher adoption, and impact reporting."
    if any(term in lowered for term in ("stem", "science", "math", "learning")):
        return "Xperimentor can make the science and math learning component more hands-on, measurable, and easy for teachers to run."
    return "Xperimentor can add a practical, measurable science and math learning component to the existing education work."


def clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip(" -|")


def clean_heading(text: str) -> str:
    text = clean_text(text)
    text = re.sub(r"[:;,\-–—]+$", "", text).strip()
    return text


def remove_repeated_heading(text: str, heading: str) -> str:
    cleaned = clean_text(text)
    pattern = re.escape(heading).replace("\\ ", r"\s+")
    cleaned = re.sub(rf"^{pattern}\s*[:\-–—]\s*", "", cleaned, flags=re.I)
    return cleaned or text


def short_join(parts: list[str], max_chars: int) -> str:
    joined = " ".join(parts)
    return trim_sentence(joined, max_chars)


def trim_sentence(text: str, max_chars: int) -> str:
    text = clean_text(text)
    if len(text) <= max_chars:
        return text
    trimmed = text[:max_chars].rsplit(" ", 1)[0]
    return trimmed.rstrip(" ,;:") + "."


def normalize_key(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def lower_first(text: str) -> str:
    if not text:
        return text
    return text[0].lower() + text[1:]
