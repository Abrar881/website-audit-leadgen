"""Business activity score: higher = more active = more likely to buy (0-100)."""
from __future__ import annotations


def _clamp(v: float) -> float:
    return max(0.0, min(100.0, v))


def score_activity(business: dict) -> float:
    """Return 0-100 where 100 = most active/established business."""

    # ── Review count (30%) ───────────────────────────────────────────────
    reviews = business.get("review_count") or 0
    if reviews >= 50:
        review_factor = 100
    elif reviews >= 20:
        review_factor = 70
    elif reviews >= 10:
        review_factor = 40
    elif reviews >= 5:
        review_factor = 20
    else:
        review_factor = 0

    # ── Google rating (20%) ──────────────────────────────────────────────
    rating = business.get("google_rating")
    if rating is None:
        rating_factor = 30
    elif rating >= 4.5:
        rating_factor = 100
    elif rating >= 4.0:
        rating_factor = 70
    elif rating >= 3.5:
        rating_factor = 40
    else:
        rating_factor = 10

    # ── Review recency proxy (25%) — we approximate from review_count
    # High review count = likely recent reviews too (no access to review dates via basic API tier)
    recency_factor = min(100, reviews * 1.5)

    # ── Has photos on Google (10%) — approximated: high-review businesses tend to have photos
    photos_factor = 60 if reviews >= 10 else 20

    # ── Fresh content / active web presence (15%) — proxy: review count + rating quality
    freshness_factor = (review_factor + rating_factor) / 2

    score = (
        review_factor   * 0.30
        + rating_factor * 0.20
        + recency_factor * 0.25
        + photos_factor  * 0.10
        + freshness_factor * 0.15
    )
    return round(_clamp(score), 2)
