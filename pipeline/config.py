"""Central configuration — loads .env and defines constants."""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

# ── API keys ──────────────────────────────────────────────────────────────────
GOOGLE_API_KEY: str = os.environ.get("GOOGLE_API_KEY", "")

# ── Paths ─────────────────────────────────────────────────────────────────────
_root = Path(__file__).parent.parent
DB_PATH: Path = Path(os.environ.get("DB_PATH", str(_root / "data" / "leads.db")))
CACHE_DIR: Path = Path(os.environ.get("CACHE_DIR", str(_root / "data" / "cache")))

# ── Trades ────────────────────────────────────────────────────────────────────
TRADE_CATEGORIES: list[str] = [
    "solar panel installer",
    "window and door installer",
    "kitchen fitter",
    "roofing contractor",
    "house extension builder",
    "loft conversion specialist",
]

# ── Postcode areas ────────────────────────────────────────────────────────────
LONDON_POSTCODE_DISTRICTS: list[str] = [
    # Central
    "EC1", "EC2", "EC3", "EC4",
    "WC1", "WC2",
    "W1", "W2", "W3", "W4", "W5", "W6", "W7", "W8", "W9", "W10", "W11", "W12", "W13", "W14",
    "SW1", "SW2", "SW3", "SW4", "SW5", "SW6", "SW7", "SW8", "SW9",
    "SW10", "SW11", "SW12", "SW13", "SW14", "SW15", "SW16", "SW17", "SW18", "SW19", "SW20",
    "SE1", "SE2", "SE3", "SE4", "SE5", "SE6", "SE7", "SE8", "SE9",
    "SE10", "SE11", "SE12", "SE13", "SE14", "SE15", "SE16", "SE17", "SE18", "SE19",
    "SE20", "SE21", "SE22", "SE23", "SE24", "SE25", "SE26", "SE27", "SE28",
    "E1", "E2", "E3", "E4", "E5", "E6", "E7", "E8", "E9",
    "E10", "E11", "E12", "E13", "E14", "E15", "E16", "E17", "E18",
    "N1", "N2", "N3", "N4", "N5", "N6", "N7", "N8", "N9",
    "N10", "N11", "N12", "N13", "N14", "N15", "N16", "N17", "N18", "N19", "N20", "N21", "N22",
    "NW1", "NW2", "NW3", "NW4", "NW5", "NW6", "NW7", "NW8", "NW9", "NW10", "NW11",
]

SE_ENGLAND_POSTCODE_AREAS: list[str] = [
    "BR", "CR", "DA", "TN", "ME", "CT",
    "SS", "CM", "RH", "GU", "BN", "PO",
    "SL", "HP", "AL", "EN", "HA", "UB",
    "TW", "KT", "SM", "IG", "RM",
]

POSTCODE_GROUPS: dict[str, list[str]] = {
    "london": LONDON_POSTCODE_DISTRICTS,
    "se_england": SE_ENGLAND_POSTCODE_AREAS,
    "all": LONDON_POSTCODE_DISTRICTS + SE_ENGLAND_POSTCODE_AREAS,
}

# ── Scoring weights ────────────────────────────────────────────────────────────
WEBSITE_WEIGHT: float = 0.40
ACTIVITY_WEIGHT: float = 0.35
BUDGET_WEIGHT: float = 0.25

# ── Freshness thresholds (days) ────────────────────────────────────────────────
SCRAPE_FRESHNESS_DAYS: int = 30
AUDIT_FRESHNESS_DAYS: int = 14

# ── Rate limits ────────────────────────────────────────────────────────────────
PLACES_API_RPS: float = 5.0
PSI_API_RPS: float = 3.0
LINK_CHECK_CONCURRENCY: int = 5

# ── Qualification thresholds ───────────────────────────────────────────────────
MIN_REVIEWS_TO_AUDIT: int = 3

# ── Trade budget weights (for budget_score) ───────────────────────────────────
TRADE_BUDGET_WEIGHTS: dict[str, float] = {
    "solar panel installer": 100,
    "house extension builder": 100,
    "loft conversion specialist": 90,
    "kitchen fitter": 80,
    "window and door installer": 70,
    "roofing contractor": 60,
}

# Domains to skip (listing sites, not real business sites)
SKIP_DOMAINS: set[str] = {
    "yell.com", "checkatrade.com", "trustatrader.com", "ratedpeople.com",
    "mybuilder.com", "houzz.com", "bark.com", "yelp.com", "facebook.com",
    "instagram.com", "twitter.com", "linkedin.com", "google.com",
}
