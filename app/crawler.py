from __future__ import annotations

import logging
import time
from collections import deque
from dataclasses import dataclass
from typing import Iterable
from urllib.parse import urldefrag, urljoin, urlparse
from urllib.robotparser import RobotFileParser

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from app.config import AppConfig
from app.models import Page
from app.validators import normalize_website, same_domain


@dataclass
class CrawlResult:
    pages: list[Page]
    errors: list[str]


class WebsiteCrawler:
    def __init__(self, config: AppConfig, logger: logging.Logger):
        self.config = config
        self.logger = logger
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": config.user_agent})
        retry = Retry(
            total=config.max_retries,
            backoff_factor=0.5,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=("GET", "HEAD"),
        )
        self.session.mount("http://", HTTPAdapter(max_retries=retry))
        self.session.mount("https://", HTTPAdapter(max_retries=retry))

    def crawl(self, website: str) -> CrawlResult:
        start_url = normalize_website(website)
        if not start_url:
            return CrawlResult([], ["DOMAIN_UNREACHABLE"])
        robots = self._robots(start_url)
        queue: deque[str] = deque([start_url])
        visited: set[str] = set()
        pages: list[Page] = []
        errors: list[str] = []

        while queue and len(pages) < self.config.max_pages_per_domain:
            url = queue.popleft()
            if url in visited:
                continue
            visited.add(url)
            if robots and not robots.can_fetch(self.config.user_agent, url):
                errors.append("BLOCKED")
                continue
            try:
                response = self.session.get(url, timeout=self.config.request_timeout, allow_redirects=True)
                response.raise_for_status()
            except requests.exceptions.SSLError as exc:
                errors.append("SSL_ERROR")
                self.logger.warning("SSL error for %s: %s", url, exc)
                continue
            except requests.exceptions.Timeout as exc:
                errors.append("TIMEOUT")
                self.logger.warning("Timeout for %s: %s", url, exc)
                continue
            except requests.RequestException as exc:
                errors.append("DOMAIN_UNREACHABLE")
                self.logger.warning("Fetch failed for %s: %s", url, exc)
                continue

            content_type = response.headers.get("content-type", "")
            if "text/html" not in content_type and "application/xhtml" not in content_type:
                continue
            page = self._parse_page(response.url, response.text)
            pages.append(page)
            for link in self._prioritized_links(response.url, response.text, start_url):
                if link not in visited and link not in queue:
                    queue.append(link)
            time.sleep(self.config.request_delay_seconds)

        if pages and not any("contact" in page.url.lower() for page in pages):
            errors.append("NO_CONTACT_PAGE")
        return CrawlResult(pages=pages, errors=sorted(set(errors)))

    def _robots(self, start_url: str) -> RobotFileParser | None:
        if not self.config.respect_robots_txt:
            return None
        parsed = urlparse(start_url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
        parser = RobotFileParser()
        parser.set_url(robots_url)
        try:
            parser.read()
            return parser
        except Exception as exc:
            self.logger.info("Could not read robots.txt for %s: %s", start_url, exc)
            return None

    def _parse_page(self, url: str, html: str) -> Page:
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()
        title = soup.title.get_text(" ", strip=True) if soup.title else ""
        text = soup.get_text("\n", strip=True)
        return Page(url=url, title=title, text=text, html=html, source_label=source_label(url))

    def _prioritized_links(self, base_url: str, html: str, start_url: str) -> Iterable[str]:
        soup = BeautifulSoup(html, "html.parser")
        scored: list[tuple[int, str]] = []
        for anchor in soup.select("a[href]"):
            href = anchor.get("href", "")
            url = urldefrag(urljoin(base_url, href)).url.rstrip("/")
            if not url.startswith(("http://", "https://")) or not same_domain(start_url, url):
                continue
            lowered_url = url.lower()
            if any(token in lowered_url for token in ("linkedin.com/", "facebook.com/", "twitter.com/", "x.com/")):
                continue
            if lowered_url.split("?", 1)[0].endswith((".pdf", ".doc", ".docx", ".xls", ".xlsx", ".zip")):
                continue
            text = f"{anchor.get_text(' ', strip=True)} {url}".lower()
            score = min((i for i, kw in enumerate(self.config.priority_link_keywords) if kw in text), default=999)
            if score < 999:
                scored.append((score, url))
        for _, url in sorted(set(scored)):
            yield url


def source_label(url: str) -> str:
    lowered = url.lower()
    if "contact" in lowered:
        return "Website-Contact"
    if "team" in lowered or "leadership" in lowered:
        return "Website-Team"
    if "program" in lowered or "project" in lowered:
        return "Website-Programs"
    if "annual" in lowered:
        return "Annual Report"
    return "Website"
