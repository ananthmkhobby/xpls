from __future__ import annotations

from typing import Any, Protocol


class AIProvider(Protocol):
    def extract_structured_data(self, page_text: str) -> dict[str, Any]:
        """Return structured JSON without mutating crawler behavior."""


class NullAIProvider:
    def extract_structured_data(self, page_text: str) -> dict[str, Any]:
        return {
            "people": [],
            "organisation_type": "",
            "city": "",
            "education_relevance": "",
            "evidence": "",
            "recommended_contact": "",
        }
