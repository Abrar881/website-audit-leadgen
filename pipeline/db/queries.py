"""Typed helper functions for DB reads and writes."""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ── businesses ──────────────────────────────────────────────────────────────

def upsert_business(conn: sqlite3.Connection, data: dict) -> int:
    """Insert or update a business. Returns the row id."""
    _BUSINESS_DEFAULTS = {
        "address": None, "postcode": None, "lat": None, "lng": None,
        "phone": None, "website": None, "google_rating": None,
        "review_count": 0, "business_status": "OPERATIONAL", "types": None,
    }
    data = {**_BUSINESS_DEFAULTS, **dict(data)}
    data.setdefault("scraped_at", _now())
    data["updated_at"] = _now()
    if isinstance(data.get("types"), list):
        data["types"] = json.dumps(data["types"])

    conn.execute("""
        INSERT INTO businesses
            (place_id, name, trade_category, address, postcode, lat, lng,
             phone, website, google_rating, review_count, business_status,
             types, scraped_at, updated_at)
        VALUES
            (:place_id, :name, :trade_category, :address, :postcode, :lat, :lng,
             :phone, :website, :google_rating, :review_count, :business_status,
             :types, :scraped_at, :updated_at)
        ON CONFLICT(place_id) DO UPDATE SET
            name=excluded.name,
            address=excluded.address,
            postcode=excluded.postcode,
            phone=excluded.phone,
            website=excluded.website,
            google_rating=excluded.google_rating,
            review_count=excluded.review_count,
            business_status=excluded.business_status,
            types=excluded.types,
            updated_at=excluded.updated_at
    """, data)
    row = conn.execute(
        "SELECT id FROM businesses WHERE place_id=?", (data["place_id"],)
    ).fetchone()
    return row["id"]


def get_business_by_place_id(conn: sqlite3.Connection, place_id: str) -> sqlite3.Row | None:
    return conn.execute(
        "SELECT * FROM businesses WHERE place_id=?", (place_id,)
    ).fetchone()


def get_unaudited_businesses(conn: sqlite3.Connection, limit: int = 50) -> list[sqlite3.Row]:
    return conn.execute("""
        SELECT b.* FROM businesses b
        LEFT JOIN audits a ON a.business_id = b.id
        WHERE a.id IS NULL
          AND b.website IS NOT NULL
          AND b.business_status = 'OPERATIONAL'
        LIMIT ?
    """, (limit,)).fetchall()


def get_businesses_for_scoring(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    """Businesses with audits but no scores."""
    return conn.execute("""
        SELECT b.*, a.id as audit_id FROM businesses b
        JOIN audits a ON a.business_id = b.id
        LEFT JOIN scores s ON s.business_id = b.id AND s.audit_id = a.id
        WHERE s.id IS NULL
    """).fetchall()


# ── audits ───────────────────────────────────────────────────────────────────

_AUDIT_DEFAULTS = {
    "psi_performance": None, "psi_accessibility": None, "psi_best_practices": None,
    "psi_seo": None, "fcp_ms": None, "lcp_ms": None, "cls": None, "tti_ms": None,
    "speed_index_ms": None, "has_ssl": None, "ssl_issuer": None, "ssl_expiry": None,
    "has_viewport_meta": None, "is_responsive": None, "copyright_year": None,
    "cms_name": None, "cms_version": None, "jquery_version": None,
    "bootstrap_version": None, "estimated_design_year": None,
    "total_links": None, "broken_links": None, "broken_link_urls": None,
    "tech_stack": None, "audit_duration_s": None, "raw_psi_json": None,
}


def insert_audit(conn: sqlite3.Connection, data: dict) -> int:
    data = {**_AUDIT_DEFAULTS, **data}
    data.setdefault("audited_at", _now())
    if isinstance(data.get("broken_link_urls"), list):
        data["broken_link_urls"] = json.dumps(data["broken_link_urls"])
    if isinstance(data.get("tech_stack"), dict):
        data["tech_stack"] = json.dumps(data["tech_stack"])

    # Auto-increment audit_version
    last = conn.execute(
        "SELECT MAX(audit_version) as v FROM audits WHERE business_id=?",
        (data["business_id"],)
    ).fetchone()
    data["audit_version"] = (last["v"] or 0) + 1

    conn.execute("""
        INSERT INTO audits
            (business_id, audit_version, psi_performance, psi_accessibility,
             psi_best_practices, psi_seo, fcp_ms, lcp_ms, cls, tti_ms,
             speed_index_ms, has_ssl, ssl_issuer, ssl_expiry, has_viewport_meta,
             is_responsive, copyright_year, cms_name, cms_version,
             jquery_version, bootstrap_version, estimated_design_year,
             total_links, broken_links, broken_link_urls, tech_stack,
             audited_at, audit_duration_s, raw_psi_json)
        VALUES
            (:business_id, :audit_version, :psi_performance, :psi_accessibility,
             :psi_best_practices, :psi_seo, :fcp_ms, :lcp_ms, :cls, :tti_ms,
             :speed_index_ms, :has_ssl, :ssl_issuer, :ssl_expiry, :has_viewport_meta,
             :is_responsive, :copyright_year, :cms_name, :cms_version,
             :jquery_version, :bootstrap_version, :estimated_design_year,
             :total_links, :broken_links, :broken_link_urls, :tech_stack,
             :audited_at, :audit_duration_s, :raw_psi_json)
    """, data)
    return conn.execute("SELECT last_insert_rowid() as id").fetchone()["id"]


def get_latest_audit(conn: sqlite3.Connection, business_id: int) -> sqlite3.Row | None:
    return conn.execute("""
        SELECT * FROM audits WHERE business_id=?
        ORDER BY audit_version DESC LIMIT 1
    """, (business_id,)).fetchone()


# ── scores ───────────────────────────────────────────────────────────────────

def upsert_score(conn: sqlite3.Connection, data: dict) -> None:
    data = dict(data)
    data.setdefault("scored_at", _now())
    if isinstance(data.get("score_breakdown"), dict):
        data["score_breakdown"] = json.dumps(data["score_breakdown"])

    conn.execute("""
        INSERT INTO scores
            (business_id, audit_id, website_score, activity_score,
             budget_score, composite_score, score_breakdown, scored_at)
        VALUES
            (:business_id, :audit_id, :website_score, :activity_score,
             :budget_score, :composite_score, :score_breakdown, :scored_at)
        ON CONFLICT(business_id, audit_id) DO UPDATE SET
            website_score=excluded.website_score,
            activity_score=excluded.activity_score,
            budget_score=excluded.budget_score,
            composite_score=excluded.composite_score,
            score_breakdown=excluded.score_breakdown,
            scored_at=excluded.scored_at
    """, data)


# ── scrape_runs ───────────────────────────────────────────────────────────────

def start_scrape_run(conn: sqlite3.Connection, trade: str, postcode: str) -> int:
    conn.execute("""
        INSERT INTO scrape_runs (started_at, trade_category, postcode_area, status)
        VALUES (?, ?, ?, 'running')
    """, (_now(), trade, postcode))
    return conn.execute("SELECT last_insert_rowid() as id").fetchone()["id"]


def finish_scrape_run(conn: sqlite3.Connection, run_id: int,
                       found: int, new: int, api_calls: int, status: str = "completed") -> None:
    conn.execute("""
        UPDATE scrape_runs
        SET finished_at=?, businesses_found=?, businesses_new=?,
            api_calls_made=?, status=?
        WHERE id=?
    """, (_now(), found, new, api_calls, status, run_id))


# ── lead_status ───────────────────────────────────────────────────────────────

def set_lead_status(conn: sqlite3.Connection, business_id: int, status: str) -> None:
    conn.execute("""
        INSERT INTO lead_status (business_id, status, updated_at)
        VALUES (?, ?, ?)
        ON CONFLICT(business_id) DO UPDATE SET status=excluded.status, updated_at=excluded.updated_at
    """, (business_id, status, _now()))
