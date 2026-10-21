"""Check for broken links (404s, 5xx, timeouts) on a page."""
from __future__ import annotations

from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from config import LINK_CHECK_CONCURRENCY

_SKIP_SCHEMES = {"mailto", "tel", "javascript", "data", "#"}


def _extract_links(base_url: str, html: bytes) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    links: list[str] = []
    for tag in soup.find_all("a", href=True):
        href = tag["href"].strip()
        if not href or any(href.startswith(s) for s in _SKIP_SCHEMES):
            continue
        if href.startswith("#"):
            continue
        full = urljoin(base_url, href)
        # Only check http/https
        if urlparse(full).scheme in ("http", "https"):
            links.append(full)
    # Deduplicate while preserving order
    seen: set[str] = set()
    unique: list[str] = []
    for link in links:
        if link not in seen:
            seen.add(link)
            unique.append(link)
    return unique[:50]  # cap at 50 links


def check_broken_links(base_url: str, html: bytes) -> dict:
    """HEAD-check all links on a page, return broken count and URLs."""
    links = _extract_links(base_url, html)
    broken: list[str] = []

    with httpx.Client(
        timeout=10,
        follow_redirects=True,
        headers={"User-Agent": "WebsiteAuditBot/1.0"},
    ) as client:
        for url in links:
            try:
                resp = client.head(url)
                if resp.status_code in (404, 410) or resp.status_code >= 500:
                    broken.append(url)
            except Exception:
                broken.append(url)

    return {
        "total_links": len(links),
        "broken_links": len(broken),
        "broken_link_urls": broken,
    }
