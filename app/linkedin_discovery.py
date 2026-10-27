from __future__ import annotations

from urllib.parse import quote_plus

from app.models import Page


def discover_linkedin_from_pages(pages: list[Page]) -> str:
    for page in pages:
        marker = "linkedin.com/"
        index = page.html.lower().find(marker)
        if index >= 0:
            start = max(0, index - 30)
            end = min(len(page.html), index + 180)
            snippet = page.html[start:end]
            for quote in ('"', "'", " "):
                if quote in snippet:
                    pass
            parts = snippet.replace("'", '"').split('"')
            for part in parts:
                if "linkedin.com/" in part:
                    return part.strip()
    return ""


def public_search_url(ngo_name: str, website: str) -> str:
    query = quote_plus(f"{ngo_name} LinkedIn site:linkedin.com/company OR site:linkedin.com/in {website}")
    return f"https://www.google.com/search?q={query}"
