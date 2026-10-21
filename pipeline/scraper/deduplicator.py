"""Deduplicates business records across scrape batches."""
from __future__ import annotations

import re
from urllib.parse import urlparse

from config import SKIP_DOMAINS


def normalize_domain(url: str | None) -> str | None:
    """Extract bare domain (no www, no path) from a URL string."""
    if not url:
        return None
    try:
        parsed = urlparse(url if "://" in url else f"https://{url}")
        host = parsed.hostname or ""
        return host.removeprefix("www.")
    except Exception:
        return None


def normalize_phone(phone: str | None) -> str | None:
    """Strip whitespace and punctuation, keep digits and leading +."""
    if not phone:
        return None
    digits = re.sub(r"[^\d+]", "", phone)
    return digits or None


class Deduplicator:
    """Tracks seen place_ids, domains, and phones to detect duplicates.

    Usage:
        d = Deduplicator()
        for place in places:
            if not d.is_duplicate(place):
                yield place
    """

    def __init__(self) -> None:
        self._place_ids: set[str] = set()
        self._domains: set[str] = set()
        self._phones: set[str] = set()

    def is_duplicate(self, place: dict) -> bool:
        """Return True if this place was already seen; else record and return False."""
        place_id = place.get("place_id", "")
        domain = normalize_domain(place.get("website"))
        phone = normalize_phone(place.get("phone"))

        if place_id and place_id in self._place_ids:
            return True
        if domain and domain in self._domains and domain not in SKIP_DOMAINS:
            return True
        if phone and phone in self._phones:
            return True

        # Record
        if place_id:
            self._place_ids.add(place_id)
        if domain and domain not in SKIP_DOMAINS:
            self._domains.add(domain)
        if phone:
            self._phones.add(phone)
        return False

    def is_skip_domain(self, url: str | None) -> bool:
        domain = normalize_domain(url)
        return domain in SKIP_DOMAINS if domain else False
