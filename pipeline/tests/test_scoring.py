"""Tests for the three scoring components and composite score."""
import pytest

from scorer.website_score import score_website
from scorer.activity_score import score_activity
from scorer.budget_score import score_budget
from scorer.composite import compute_composite


# ── website_score ─────────────────────────────────────────────────────────────

def test_website_score_terrible_site():
    audit = {
        "psi_performance": 10,     # very slow
        "lcp_ms": 8000,             # >4s
        "has_ssl": False,
        "has_viewport_meta": False,
        "is_responsive": False,
        "estimated_design_year": 2012,
        "broken_links": 6,
        "total_links": 20,
    }
    score = score_website(audit)
    assert score > 80, f"Expected terrible site to score >80, got {score}"


def test_website_score_modern_site():
    audit = {
        "psi_performance": 92,
        "lcp_ms": 1200,
        "has_ssl": True,
        "has_viewport_meta": True,
        "is_responsive": True,
        "estimated_design_year": 2024,
        "broken_links": 0,
        "total_links": 10,
    }
    score = score_website(audit)
    assert score < 20, f"Expected modern site to score <20, got {score}"


def test_website_score_returns_0_to_100(tmp_path):
    for psi in [0, 50, 100]:
        audit = {"psi_performance": psi, "has_ssl": True, "is_responsive": True}
        s = score_website(audit)
        assert 0 <= s <= 100


def test_website_score_no_ssl_increases_score():
    base = {"psi_performance": 70, "has_ssl": True, "is_responsive": True}
    no_ssl = {**base, "has_ssl": False}
    assert score_website(no_ssl) > score_website(base)


# ── activity_score ────────────────────────────────────────────────────────────

def test_activity_score_high_review_count():
    biz = {"review_count": 80, "google_rating": 4.6}
    score = score_activity(biz)
    assert score > 60


def test_activity_score_few_reviews():
    biz = {"review_count": 2, "google_rating": 3.0}
    score = score_activity(biz)
    assert score < 30


def test_activity_score_returns_0_to_100():
    biz = {"review_count": 500, "google_rating": 5.0}
    s = score_activity(biz)
    assert 0 <= s <= 100


# ── budget_score ──────────────────────────────────────────────────────────────

def test_budget_score_solar_high():
    biz = {"trade_category": "solar panel installer", "review_count": 60}
    score = score_budget(biz)
    assert score > 70


def test_budget_score_lower_trade():
    biz = {"trade_category": "roofing contractor", "review_count": 5}
    score = score_budget(biz)
    assert score < 50


def test_budget_score_returns_0_to_100():
    for trade in ["solar panel installer", "kitchen fitter", "roofing contractor"]:
        biz = {"trade_category": trade, "review_count": 30}
        s = score_budget(biz)
        assert 0 <= s <= 100


# ── composite ────────────────────────────────────────────────────────────────

def test_composite_uses_correct_weights():
    # All three at 100: composite should be 100
    result = compute_composite(
        website_score=100.0,
        activity_score=100.0,
        budget_score=100.0,
        business={"trade_category": "solar panel installer", "review_count": 100},
        audit={},
    )
    assert abs(result["composite_score"] - 100.0) < 0.01


def test_composite_returns_breakdown():
    result = compute_composite(
        website_score=70.0,
        activity_score=60.0,
        budget_score=80.0,
        business={"trade_category": "solar panel installer", "review_count": 30},
        audit={"psi_performance": 30},
    )
    assert "composite_score" in result
    assert "score_breakdown" in result
    assert 0 <= result["composite_score"] <= 100


def test_composite_end_to_end_bad_lead():
    """Low reviews + good site = low composite score."""
    bad_audit = {"psi_performance": 90, "has_ssl": True, "is_responsive": True,
                 "estimated_design_year": 2023, "broken_links": 0}
    inactive_biz = {"trade_category": "roofing contractor", "review_count": 1,
                    "google_rating": 2.0}
    ws = score_website(bad_audit)
    as_ = score_activity(inactive_biz)
    bs = score_budget(inactive_biz)
    result = compute_composite(ws, as_, bs, business=inactive_biz, audit=bad_audit)
    assert result["composite_score"] < 40, f"Expected low score for bad lead, got {result['composite_score']}"
