"""Integration test: cli stats command runs without error."""
import tempfile
from pathlib import Path
from click.testing import CliRunner

from cli import cli
from db.connection import init_db
from db.queries import upsert_business, start_scrape_run, finish_scrape_run


def make_db(tmp_path: Path):
    db_path = tmp_path / "test.db"
    conn = init_db(db_path)
    bid = upsert_business(conn, {
        "place_id": "test001",
        "name": "Test Solar",
        "trade_category": "solar panel installer",
        "website": "https://example.com",
        "business_status": "OPERATIONAL",
        "review_count": 30,
        "google_rating": 4.5,
    })
    run_id = start_scrape_run(conn, "solar panel installer", "SE1")
    finish_scrape_run(conn, run_id, found=1, new=1, api_calls=2)
    conn.commit()
    return db_path


def test_stats_shows_counts(tmp_path):
    db_path = make_db(tmp_path)
    runner = CliRunner()
    result = runner.invoke(cli, ["--db", str(db_path), "stats"])
    assert result.exit_code == 0, result.output
    assert "1" in result.output  # at least 1 business


def test_export_creates_csv(tmp_path):
    db_path = make_db(tmp_path)
    out = tmp_path / "leads.csv"
    runner = CliRunner()
    result = runner.invoke(cli, ["--db", str(db_path), "export",
                                  "--output", str(out)])
    assert result.exit_code == 0, result.output
    assert out.exists()
