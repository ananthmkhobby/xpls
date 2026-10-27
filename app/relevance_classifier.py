from __future__ import annotations

from app.config import AppConfig
from app.models import Page


def classify_roles(text: str, config: AppConfig) -> str:
    lowered = text.lower()
    roles: list[str] = []
    for role, keywords in config.role_keywords.items():
        if any(keyword.lower() in lowered for keyword in keywords):
            roles.append(role)
    return "; ".join(roles or ["Other"])


def score_relevance(pages: list[Page], config: AppConfig) -> tuple[int, str]:
    text = " ".join(page.text for page in pages).lower()
    matched: list[str] = []
    score = 0
    for keyword, points in config.relevance_keywords.items():
        if keyword.lower() in text:
            matched.append(keyword)
            score += int(points)
    score = min(score, 100)
    if matched:
        evidence = f"Found education/STEM signals: {', '.join(matched[:8])}."
    else:
        evidence = "Limited public evidence of school, STEM, science education, or teacher-training programs."
    return score, evidence
