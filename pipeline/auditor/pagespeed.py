"""Google PageSpeed Insights API auditor."""
from __future__ import annotations

import json
from pathlib import Path

import httpx

from utils.cache import DiskCache
from utils.rate_limiter import RateLimiter
from config import PSI_API_RPS

_PSI_URL = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"


def _extract_metrics(data: dict) -> dict:
    """Pull scores and core web vitals from a PSI API response."""
    lr = data.get("lighthouseResult", {})
    cats = lr.get("categories", {})
    audits = lr.get("audits", {})

    def score(cat: str) -> int | None:
        s = (cats.get(cat) or {}).get("score")
        return round(s * 100) if s is not None else None

    def ms(key: str) -> int | None:
        v = (audits.get(key) or {}).get("numericValue")
        return round(v) if v is not None else None

    def flt(key: str) -> float | None:
        v = (audits.get(key) or {}).get("numericValue")
        return round(v, 4) if v is not None else None

    return {
        "psi_performance": score("performance"),
        "psi_accessibility": score("accessibility"),
        "psi_best_practices": score("best-practices"),
        "psi_seo": score("seo"),
        "fcp_ms": ms("first-contentful-paint"),
        "lcp_ms": ms("largest-contentful-paint"),
        "cls": flt("cumulative-layout-shift"),
        "tti_ms": ms("interactive"),
        "speed_index_ms": ms("speed-index"),
    }


class PageSpeedClient:
    """Audits a URL via Google PageSpeed Insights (mobile strategy)."""

    def __init__(self, api_key: str, cache_dir: str | Path) -> None:
        self.api_key = api_key
        self._cache = DiskCache(cache_dir, ttl_seconds=60 * 60 * 24 * 7)  # 7 days
        self._limiter = RateLimiter(rate=PSI_API_RPS, capacity=PSI_API_RPS)
        self.api_calls_made = 0

    def audit(self, url: str, strategy: str = "mobile") -> dict:
        """Return parsed metrics dict for the given URL."""
        cache_key = f"psi:{strategy}:{url}"
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached

        self._limiter.acquire()
        resp = httpx.get(
            _PSI_URL,
            params={
                "url": url,
                "strategy": strategy,
                "key": self.api_key,
                "category": ["performance", "accessibility", "best-practices", "seo"],
            },
            timeout=60,
        )
        resp.raise_for_status()
        self.api_calls_made += 1

        data = resp.json()
        result = _extract_metrics(data)
        result["raw_psi_json"] = json.dumps(data)

        self._cache.set(cache_key, result)
        return result
