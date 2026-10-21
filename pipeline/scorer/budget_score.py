"""Budget potential score: higher = more likely to afford services (0-100)."""
from __future__ import annotations

from config import TRADE_BUDGET_WEIGHTS


def _clamp(v: float) -> float:
    return max(0.0, min(100.0, v))


def score_budget(business: dict) -> float:
    """Return 0-100 where 100 = highest estimated budget potential."""

    # ── Trade category value (40%) ───────────────────────────────────────
    trade = (business.get("trade_category") or "").lower()
    trade_factor = float(TRADE_BUDGET_WEIGHTS.get(trade, 50))

    # ── Review count as company size proxy (30%) ─────────────────────────
    reviews = business.get("review_count") or 0
    if reviews >= 100:
        size_factor = 100
    elif reviews >= 50:
        size_factor = 70
    elif reviews >= 20:
        size_factor = 40
    else:
        size_factor = 15

    # ── Paid ads presence (15%) — not detectable at basic API tier,
    # use review count + trade tier as proxy for marketing-minded businesses
    ads_factor = min(100, (trade_factor + size_factor) / 2)

    # ── Multi-location signals (15%) — proxy from very high review count
    multiloc_factor = 80 if reviews >= 100 else 20

    score = (
        trade_factor   * 0.40
        + size_factor  * 0.30
        + ads_factor   * 0.15
        + multiloc_factor * 0.15
    )
    return round(_clamp(score), 2)
