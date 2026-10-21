"""Website Audit Lead Gen — pipeline CLI entry point."""
from __future__ import annotations

import csv
import sys
from pathlib import Path

import click
from tqdm import tqdm

import config as cfg
from db.connection import init_db
from db import queries as q
from scraper.google_places import PlacesClient
from scraper.deduplicator import Deduplicator
from auditor.orchestrator import AuditOrchestrator
from scorer.composite import score_lead


# ── CLI group ─────────────────────────────────────────────────────────────────

@click.group()
@click.option("--db", "db_path", default=None,
              help="Override DB path (default: data/leads.db)")
@click.pass_context
def cli(ctx: click.Context, db_path: str | None) -> None:
    """Website Audit Lead Gen pipeline."""
    ctx.ensure_object(dict)
    path = Path(db_path) if db_path else cfg.DB_PATH
    ctx.obj["conn"] = init_db(path)
    ctx.obj["db_path"] = path


# ── scrape ────────────────────────────────────────────────────────────────────

@cli.command()
@click.option("--trade", default="all",
              help="Trade category key or 'all'. E.g. 'solar panel installer'")
@click.option("--postcode", default="london",
              help="Postcode district(s) comma-separated or group name (london/se_england/all)")
@click.pass_context
def scrape(ctx: click.Context, trade: str, postcode: str) -> None:
    """Scrape businesses from Google Places and store them."""
    if not cfg.GOOGLE_API_KEY:
        click.echo("Error: GOOGLE_API_KEY not set in .env", err=True)
        sys.exit(1)

    conn = ctx.obj["conn"]
    client = PlacesClient(api_key=cfg.GOOGLE_API_KEY, cache_dir=cfg.CACHE_DIR)
    dedup = Deduplicator()

    trades = cfg.TRADE_CATEGORIES if trade == "all" else [trade]
    postcodes = cfg.POSTCODE_GROUPS.get(postcode, postcode.split(","))

    total_found = 0
    total_new = 0

    for t in trades:
        for pc in tqdm(postcodes, desc=f"Scraping {t}"):
            query = f"{t} in {pc}"
            run_id = q.start_scrape_run(conn, t, pc)
            found = 0
            new = 0

            try:
                places = client.text_search(query, t)
                for place in places:
                    found += 1
                    # Skip listing sites, closed businesses, few reviews
                    if not place.get("website"):
                        continue
                    if place.get("business_status") != "OPERATIONAL":
                        continue
                    if (place.get("review_count") or 0) < cfg.MIN_REVIEWS_TO_AUDIT:
                        continue
                    if dedup.is_skip_domain(place.get("website")):
                        continue
                    if dedup.is_duplicate(place):
                        continue
                    q.upsert_business(conn, place)
                    new += 1

                conn.commit()
                q.finish_scrape_run(conn, run_id, found, new, client.api_calls_made)
            except Exception as e:
                conn.rollback()
                q.finish_scrape_run(conn, run_id, found, new, 0, status="failed")
                click.echo(f"  Error scraping {query}: {e}", err=True)

            conn.commit()
            total_found += found
            total_new += new

    click.echo(f"Scrape complete. Found {total_found}, stored {total_new} new businesses.")


# ── audit ─────────────────────────────────────────────────────────────────────

@cli.command()
@click.option("--batch", default=50, help="Number of businesses to audit per run")
@click.option("--business-id", default=None, type=int, help="Audit a specific business by ID")
@click.pass_context
def audit(ctx: click.Context, batch: int, business_id: int | None) -> None:
    """Audit websites for unaudited businesses."""
    if not cfg.GOOGLE_API_KEY:
        click.echo("Error: GOOGLE_API_KEY not set in .env", err=True)
        sys.exit(1)

    conn = ctx.obj["conn"]
    orchestrator = AuditOrchestrator(api_key=cfg.GOOGLE_API_KEY, cache_dir=cfg.CACHE_DIR)

    if business_id:
        row = conn.execute("SELECT * FROM businesses WHERE id=?", (business_id,)).fetchone()
        businesses = [row] if row else []
    else:
        businesses = q.get_unaudited_businesses(conn, limit=batch)

    for biz in tqdm(businesses, desc="Auditing"):
        if not biz["website"]:
            continue
        try:
            audit_data = orchestrator.audit_url(biz["website"])
            audit_data["business_id"] = biz["id"]
            q.insert_audit(conn, audit_data)
            conn.commit()
        except Exception as e:
            conn.rollback()
            click.echo(f"  Error auditing {biz['name']}: {e}", err=True)

    click.echo(f"Audit complete. Processed {len(businesses)} businesses.")


# ── score ─────────────────────────────────────────────────────────────────────

@cli.command()
@click.option("--all", "score_all", is_flag=True, default=True, help="Score all unscored leads")
@click.option("--recalculate", is_flag=True, default=False,
              help="Recalculate scores for already-scored leads")
@click.pass_context
def score(ctx: click.Context, score_all: bool, recalculate: bool) -> None:
    """Compute composite scores for audited businesses."""
    conn = ctx.obj["conn"]
    rows = q.get_businesses_for_scoring(conn)

    for row in tqdm(rows, desc="Scoring"):
        biz = dict(row)
        audit_id = biz.pop("audit_id")
        audit_row = q.get_latest_audit(conn, biz["id"])
        if not audit_row:
            continue
        audit_data = dict(audit_row)
        result = score_lead(biz, audit_data)
        result["business_id"] = biz["id"]
        result["audit_id"] = audit_id
        q.upsert_score(conn, result)

    conn.commit()
    click.echo(f"Scoring complete. Scored {len(rows)} leads.")


# ── run-all ───────────────────────────────────────────────────────────────────

@cli.command("run-all")
@click.option("--trade", default="all")
@click.option("--postcode", default="london")
@click.option("--batch", default=50)
@click.pass_context
def run_all(ctx: click.Context, trade: str, postcode: str, batch: int) -> None:
    """Run scrape → audit → score in sequence."""
    ctx.invoke(scrape, trade=trade, postcode=postcode)
    ctx.invoke(audit, batch=batch)
    ctx.invoke(score, score_all=True, recalculate=False)


# ── stats ─────────────────────────────────────────────────────────────────────

@cli.command()
@click.pass_context
def stats(ctx: click.Context) -> None:
    """Print pipeline statistics."""
    conn = ctx.obj["conn"]

    total_biz = conn.execute("SELECT COUNT(*) FROM businesses").fetchone()[0]
    with_website = conn.execute(
        "SELECT COUNT(*) FROM businesses WHERE website IS NOT NULL"
    ).fetchone()[0]
    audited = conn.execute(
        "SELECT COUNT(DISTINCT business_id) FROM audits"
    ).fetchone()[0]
    scored = conn.execute(
        "SELECT COUNT(DISTINCT business_id) FROM scores"
    ).fetchone()[0]

    score_dist = conn.execute("""
        SELECT
            SUM(CASE WHEN composite_score >= 80 THEN 1 ELSE 0 END) as priority,
            SUM(CASE WHEN composite_score >= 60 AND composite_score < 80 THEN 1 ELSE 0 END) as strong,
            SUM(CASE WHEN composite_score >= 40 AND composite_score < 60 THEN 1 ELSE 0 END) as review,
            SUM(CASE WHEN composite_score < 40 THEN 1 ELSE 0 END) as skip
        FROM scores
    """).fetchone()

    last_runs = conn.execute("""
        SELECT trade_category, postcode_area, status, businesses_new, started_at
        FROM scrape_runs ORDER BY id DESC LIMIT 5
    """).fetchall()

    click.echo(f"\n{'='*50}")
    click.echo(f"  Website Audit Lead Gen — Stats")
    click.echo(f"{'='*50}")
    click.echo(f"  Businesses scraped:  {total_biz}")
    click.echo(f"  With website:        {with_website}")
    click.echo(f"  Audited:             {audited}")
    click.echo(f"  Scored:              {scored}")
    if scored:
        click.echo(f"\n  Score distribution:")
        click.echo(f"    80-100 (Priority): {score_dist['priority']}")
        click.echo(f"    60-79  (Strong):   {score_dist['strong']}")
        click.echo(f"    40-59  (Review):   {score_dist['review']}")
        click.echo(f"    0-39   (Skip):     {score_dist['skip']}")
    if last_runs:
        click.echo(f"\n  Last 5 scrape runs:")
        for r in last_runs:
            click.echo(f"    [{r['status']}] {r['trade_category']} / {r['postcode_area']} "
                       f"— {r['businesses_new']} new — {r['started_at'][:19]}")
    click.echo()


# ── export ────────────────────────────────────────────────────────────────────

@cli.command()
@click.option("--min-score", default=0.0, type=float, help="Minimum composite score")
@click.option("--output", default="leads.csv", help="Output CSV file path")
@click.option("--format", "fmt", default="csv", type=click.Choice(["csv"]))
@click.pass_context
def export(ctx: click.Context, min_score: float, output: str, fmt: str) -> None:
    """Export scored leads to CSV."""
    conn = ctx.obj["conn"]
    rows = conn.execute("""
        SELECT
            b.name, b.trade_category, b.postcode, b.address, b.phone, b.website,
            b.google_rating, b.review_count,
            s.composite_score, s.website_score, s.activity_score, s.budget_score,
            a.psi_performance, a.lcp_ms, a.has_ssl, a.estimated_design_year,
            a.cms_name, a.broken_links
        FROM businesses b
        JOIN scores s ON s.business_id = b.id
        LEFT JOIN audits a ON a.id = s.audit_id
        WHERE s.composite_score >= ?
        ORDER BY s.composite_score DESC
    """, (min_score,)).fetchall()

    FIELDS = [
        "name", "trade_category", "postcode", "address", "phone", "website",
        "google_rating", "review_count",
        "composite_score", "website_score", "activity_score", "budget_score",
        "psi_performance", "lcp_ms", "has_ssl", "estimated_design_year",
        "cms_name", "broken_links",
    ]
    out = Path(output)
    with out.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows([dict(r) for r in rows])

    if rows:
        click.echo(f"Exported {len(rows)} leads to {out}")
    else:
        click.echo(f"No leads found (headers written to {out})")


if __name__ == "__main__":
    cli()
