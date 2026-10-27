from __future__ import annotations

from urllib.parse import urlparse

import tldextract


def normalize_website(value: str) -> str:
    value = (value or "").strip()
    if not value:
        return ""
    if not value.startswith(("http://", "https://")):
        value = f"https://{value}"
    return value.rstrip("/")


def normalized_domain(url: str) -> str:
    parsed = urlparse(normalize_website(url))
    host = parsed.netloc.lower().removeprefix("www.")
    extracted = tldextract.extract(host)
    if extracted.domain and extracted.suffix:
        return f"{extracted.domain}.{extracted.suffix}"
    return host


def same_domain(base_url: str, candidate_url: str) -> bool:
    return normalized_domain(base_url) == normalized_domain(candidate_url)
