"""Composite lead score: weighted combination of all three components."""
from __future__ import annotations

from config import WEBSITE_WEIGHT, ACTIVITY_WEIGHT, BUDGET_WEIGHT
from scorer.website_score import score_website
from scorer.activity_score import score_activity
from scorer.budget_score import score_budget


def compute_composite(
    website_score: float,
    activity_score: float,
    budget_score: float,
    business: dict,
    audit: dict,
) -> dict:
    """Return composite_score (0-100) and a score_breakdown dict."""
    composite = (
        website_score  * WEBSITE_WEIGHT
        + activity_score * ACTIVITY_WEIGHT
        + budget_score * BUDGET_WEIGHT
    )
    composite = round(max(0.0, min(100.0, composite)), 2)

    return {
        "website_score": website_score,
        "activity_score": activity_score,
        "budget_score": budget_score,
        "composite_score": composite,
        "score_breakdown": {
            "weights": {
                "website": WEBSITE_WEIGHT,
                "activity": ACTIVITY_WEIGHT,
                "budget": BUDGET_WEIGHT,
            },
            "components": {
                "website": website_score,
                "activity": activity_score,
                "budget": budget_score,
            },
        },
    }


def score_lead(business: dict, audit: dict) -> dict:
    """Convenience: compute all three components + composite from raw dicts."""
    ws = score_website(audit)
    as_ = score_activity(business)
    bs = score_budget(business)
    return compute_composite(ws, as_, bs, business=business, audit=audit)
