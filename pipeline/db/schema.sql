CREATE TABLE IF NOT EXISTS businesses (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    place_id        TEXT UNIQUE NOT NULL,
    name            TEXT NOT NULL,
    trade_category  TEXT NOT NULL,
    address         TEXT,
    postcode        TEXT,
    lat             REAL,
    lng             REAL,
    phone           TEXT,
    website         TEXT,
    google_rating   REAL,
    review_count    INTEGER DEFAULT 0,
    business_status TEXT,
    types           TEXT,
    scraped_at      TEXT NOT NULL,
    updated_at      TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS audits (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    business_id          INTEGER NOT NULL REFERENCES businesses(id),
    audit_version        INTEGER DEFAULT 1,
    psi_performance      INTEGER,
    psi_accessibility    INTEGER,
    psi_best_practices   INTEGER,
    psi_seo              INTEGER,
    fcp_ms               INTEGER,
    lcp_ms               INTEGER,
    cls                  REAL,
    tti_ms               INTEGER,
    speed_index_ms       INTEGER,
    has_ssl              INTEGER,
    ssl_issuer           TEXT,
    ssl_expiry           TEXT,
    has_viewport_meta    INTEGER,
    is_responsive        INTEGER,
    copyright_year       INTEGER,
    cms_name             TEXT,
    cms_version          TEXT,
    jquery_version       TEXT,
    bootstrap_version    TEXT,
    estimated_design_year INTEGER,
    total_links          INTEGER,
    broken_links         INTEGER,
    broken_link_urls     TEXT,
    tech_stack           TEXT,
    audited_at           TEXT NOT NULL,
    audit_duration_s     REAL,
    raw_psi_json         TEXT,
    UNIQUE(business_id, audit_version)
);

CREATE TABLE IF NOT EXISTS scores (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    business_id     INTEGER NOT NULL REFERENCES businesses(id),
    audit_id        INTEGER NOT NULL REFERENCES audits(id),
    website_score   REAL,
    activity_score  REAL,
    budget_score    REAL,
    composite_score REAL,
    score_breakdown TEXT,
    scored_at       TEXT NOT NULL,
    UNIQUE(business_id, audit_id)
);

CREATE TABLE IF NOT EXISTS scrape_runs (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at        TEXT NOT NULL,
    finished_at       TEXT,
    trade_category    TEXT,
    postcode_area     TEXT,
    businesses_found  INTEGER DEFAULT 0,
    businesses_new    INTEGER DEFAULT 0,
    api_calls_made    INTEGER DEFAULT 0,
    status            TEXT DEFAULT 'running'
);

CREATE TABLE IF NOT EXISTS lead_status (
    business_id INTEGER PRIMARY KEY REFERENCES businesses(id),
    status      TEXT DEFAULT 'new',
    updated_at  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS lead_notes (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    business_id INTEGER NOT NULL REFERENCES businesses(id),
    note        TEXT NOT NULL,
    author      TEXT,
    created_at  TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_businesses_postcode ON businesses(postcode);
CREATE INDEX IF NOT EXISTS idx_businesses_trade    ON businesses(trade_category);
CREATE INDEX IF NOT EXISTS idx_businesses_website  ON businesses(website);
CREATE INDEX IF NOT EXISTS idx_scores_composite    ON scores(composite_score DESC);
CREATE INDEX IF NOT EXISTS idx_audits_business     ON audits(business_id);
