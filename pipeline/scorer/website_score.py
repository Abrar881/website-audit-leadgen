"""Website quality score: higher = worse site = better lead (0-100)."""
from __future__ import annotations


def _clamp(v: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, v))


def score_website(audit: dict) -> float:
    """Return a 0-100 score where 100 = worst possible website."""

    # ── PSI performance inverted (30%) ───────────────────────────────────
    psi = audit.get("psi_performance")
    psi_factor = (100 - psi) if psi is not None else 60  # assume mediocre if unknown

    # ── LCP speed (15%) ──────────────────────────────────────────────────
    lcp_ms = audit.get("lcp_ms")
    if lcp_ms is None:
        lcp_factor = 50
    elif lcp_ms > 4000:
        lcp_factor = 100
    elif lcp_ms > 2500:
        lcp_factor = 50
    else:
        lcp_factor = 10

    # ── No SSL (10%) ─────────────────────────────────────────────────────
    has_ssl = audit.get("has_ssl")
    if has_ssl is False:
        ssl_factor = 100
    elif has_ssl is True:
        ssl_factor = 0
    else:
        ssl_factor = 30  # unknown

    # ── Not mobile-friendly (15%) ─────────────────────────────────────────
    responsive = audit.get("is_responsive")
    viewport = audit.get("has_viewport_meta")
    if responsive is False:
        mobile_factor = 100
    elif viewport is False:
        mobile_factor = 60
    elif responsive is True:
        mobile_factor = 0
    else:
        mobile_factor = 30  # unknown

    # ── Design age (20%) ─────────────────────────────────────────────────
    year = audit.get("estimated_design_year")
    if year is None:
        age_factor = 40
    elif year < 2016:
        age_factor = 100
    elif year < 2018:
        age_factor = 70
    elif year < 2020:
        age_factor = 40
    elif year < 2022:
        age_factor = 20
    else:
        age_factor = 0

    # ── Broken links (10%) ───────────────────────────────────────────────
    broken = audit.get("broken_links")
    total = audit.get("total_links", 1) or 1
    if broken is None:
        link_factor = 0
    elif broken > 5:
        link_factor = 100
    elif broken >= 3:
        link_factor = 60
    elif broken >= 1:
        link_factor = 30
    else:
        link_factor = 0

    score = (
        psi_factor    * 0.30
        + lcp_factor  * 0.15
        + ssl_factor  * 0.10
        + mobile_factor * 0.15
        + age_factor  * 0.20
        + link_factor * 0.10
    )
    return round(_clamp(score), 2)
