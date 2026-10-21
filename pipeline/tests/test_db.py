"""Tests for DB layer: connection, schema init, and queries."""
import json
import tempfile
from pathlib import Path

import pytest

from db.connection import init_db
from db.queries import (
    upsert_business,
    get_business_by_place_id,
    get_unaudited_businesses,
    insert_audit,
    get_latest_audit,
    upsert_score,
    start_scrape_run,
    finish_scrape_run,
)


@pytest.fixture
def conn():
    with tempfile.TemporaryDirectory() as d:
        yield init_db(Path(d) / "test.db")


def make_business(**overrides) -> dict:
    base = {
        "place_id": "ChIJ_test_001",
        "name": "London Solar Ltd",
        "trade_category": "solar panel installer",
        "address": "1 Test Street, London",
        "postcode": "SE1",
        "lat": 51.5,
        "lng": -0.1,
        "phone": "+44 20 1234 5678",
        "website": "https://londonsolar.co.uk",
        "google_rating": 4.7,
        "review_count": 42,
        "business_status": "OPERATIONAL",
        "types": ["establishment"],
    }
    return {**base, **overrides}


def test_init_db_creates_all_tables(conn):
    tables = {
        row[0]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
    }
    assert "businesses" in tables
    assert "audits" in tables
    assert "scores" in tables
    assert "scrape_runs" in tables
    assert "lead_status" in tables


def test_upsert_business_returns_id(conn):
    bid = upsert_business(conn, make_business())
    assert isinstance(bid, int)
    assert bid > 0


def test_upsert_business_deduplicates_on_place_id(conn):
    b = make_business()
    id1 = upsert_business(conn, b)
    id2 = upsert_business(conn, {**b, "name": "London Solar Updated"})
    assert id1 == id2
    row = get_business_by_place_id(conn, b["place_id"])
    assert row["name"] == "London Solar Updated"


def test_get_unaudited_businesses_excludes_no_website(conn):
    upsert_business(conn, make_business(place_id="has_site", website="https://example.com"))
    upsert_business(conn, make_business(place_id="no_site", website=None))
    conn.commit()
    rows = get_unaudited_businesses(conn, limit=10)
    place_ids = [r["place_id"] for r in rows]
    assert "has_site" in place_ids
    assert "no_site" not in place_ids


def test_insert_audit_increments_version(conn):
    bid = upsert_business(conn, make_business())
    conn.commit()
    aid1 = insert_audit(conn, {
        "business_id": bid,
        "psi_performance": 25,
        "has_ssl": 1,
        "audited_at": "2026-10-20T10:00:00+00:00",
    })
    conn.commit()
    aid2 = insert_audit(conn, {
        "business_id": bid,
        "psi_performance": 30,
        "has_ssl": 1,
        "audited_at": "2026-10-21T10:00:00+00:00",
    })
    conn.commit()
    assert aid1 != aid2
    latest = get_latest_audit(conn, bid)
    assert latest["psi_performance"] == 30


def test_upsert_score_stores_breakdown(conn):
    bid = upsert_business(conn, make_business())
    conn.commit()
    aid = insert_audit(conn, {"business_id": bid, "psi_performance": 20})
    conn.commit()
    upsert_score(conn, {
        "business_id": bid,
        "audit_id": aid,
        "website_score": 75.0,
        "activity_score": 60.0,
        "budget_score": 80.0,
        "composite_score": 71.25,
        "score_breakdown": {"website": {"psi": 80}},
    })
    conn.commit()
    row = conn.execute(
        "SELECT composite_score, score_breakdown FROM scores WHERE business_id=?", (bid,)
    ).fetchone()
    assert abs(row["composite_score"] - 71.25) < 0.01
    breakdown = json.loads(row["score_breakdown"])
    assert breakdown["website"]["psi"] == 80


def test_scrape_run_lifecycle(conn):
    run_id = start_scrape_run(conn, "solar panel installer", "SE1")
    conn.commit()
    finish_scrape_run(conn, run_id, found=15, new=10, api_calls=3)
    conn.commit()
    row = conn.execute("SELECT * FROM scrape_runs WHERE id=?", (run_id,)).fetchone()
    assert row["status"] == "completed"
    assert row["businesses_new"] == 10
