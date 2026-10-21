# Website Audit Lead Gen

Automated pipeline that finds local businesses with poor websites, audits them, scores them, and surfaces the highest-opportunity leads in a dashboard.

## Problem

Most local service businesses (plumbers, electricians, builders) have outdated websites — slow, broken links, no SSL, no mobile optimisation. This is a signal: they have the revenue to maintain a website but haven't invested in it recently. This tool systematically finds those businesses and ranks them by opportunity score.

## Architecture

```
Google Places API
      │
      ▼
  Scraper ──► Deduplicator
      │
      ▼
  Auditor
  ├── PageSpeed Insights (performance, LCP)
  ├── SSL checker
  ├── Mobile responsiveness
  ├── Design age estimator
  ├── Broken links scanner
  └── Tech stack detector
      │
      ▼
  Scorer (composite: website + activity + budget)
      │
      ▼
  SQLite DB ──► Next.js Dashboard
```

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Pipeline | Python 3.11, httpx, BeautifulSoup |
| CLI | Click |
| Database | SQLite (better-sqlite3) |
| Dashboard | Next.js 15, React 19, TypeScript |
| Styling | Tailwind CSS 4 |
| APIs | Google Places, PageSpeed Insights |

## Features

- Scrapes businesses by trade category and postcode area via Google Places API
- Multi-factor website audit: performance score, SSL, mobile, design age, broken links, CMS detection
- Composite scoring algorithm weighing website quality + business activity + budget signals
- Next.js dashboard with filtering (score range, trade, postcode), sorting, and CSV export
- CLI with subcommands for each pipeline stage (scrape, audit, score, stats, export)
- SQLite-backed with disk cache for API responses (avoids re-fetching on reruns)
- Rate limiter (token bucket) to stay within API quotas

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- Google Cloud API key with **Places API (New)** and **PageSpeed Insights API** enabled

### Pipeline setup

```bash
cd pipeline
python -m venv .venv && source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -e .

cp ../.env.example .env
# Edit .env — add your GOOGLE_API_KEY
```

### Run the pipeline

```bash
# Scrape businesses (by trade + postcode area)
python -m cli scrape --trade plumber --postcode SW

# Audit their websites
python -m cli audit --limit 50

# Score all audited leads
python -m cli score

# View stats
python -m cli stats

# Export top leads to CSV
python -m cli export --min-score 60
```

### Dashboard setup

```bash
cd dashboard
npm install

cp .env.example .env.local
# Set DB_PATH to point to ../data/leads.db

npm run dev
# Open http://localhost:3000
```

## How It Works

1. **Scrape** — queries Google Places API for businesses matching a trade category in a postcode area. Deduplicates by phone number and domain.
2. **Audit** — for each business with a website, runs 5 parallel checks: PageSpeed (performance + LCP), SSL validity, mobile viewport detection, design year estimation via HTTP headers and asset fingerprints, broken link scan.
3. **Score** — combines audit results into a composite 0–100 score: website quality (40%), business activity signals from reviews/recency (40%), budget proxy from review volume (20%).
4. **Dashboard** — Next.js app reads directly from SQLite. Filterable table with score badges, CSV export, paginated results.

## Project Structure

```
pipeline/
  scraper/      Google Places scraper + deduplicator
  auditor/      PageSpeed, SSL, mobile, design age, broken links, orchestrator
  scorer/       Per-factor + composite scoring
  db/           SQLite connection, schema, queries
  cli.py        Click CLI entry point
  config.py     Paths and defaults

dashboard/
  app/          Next.js App Router pages + API routes
  components/   LeadsTable, Filters, Pagination, ScoreBadge, StatsOverview
  lib/          DB client (better-sqlite3), TypeScript types
```
