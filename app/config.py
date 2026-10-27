from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class AppConfig:
    max_pages_per_domain: int = 20
    request_timeout: int = 15
    request_delay_seconds: float = 1.0
    max_retries: int = 2
    user_agent: str = "NEAL-NGO-Enricher/1.0"
    enable_playwright: bool = False
    enable_linkedin_discovery: bool = True
    checkpoint_every: int = 10
    country_default: str = "IN"
    respect_robots_txt: bool = True
    priority_link_keywords: list[str] = field(default_factory=list)
    relevance_keywords: dict[str, int] = field(default_factory=dict)
    role_keywords: dict[str, list[str]] = field(default_factory=dict)


def load_config(path: str | Path = "config.yaml") -> AppConfig:
    config_path = Path(path)
    data: dict[str, Any] = {}
    if config_path.exists():
        data = yaml.safe_load(config_path.read_text()) or {}
    return AppConfig(**data)
