"""Detect the approximate design/build year of a website from its HTML."""
from __future__ import annotations

import re
import statistics
from bs4 import BeautifulSoup

# ── regex patterns ────────────────────────────────────────────────────────────

_COPYRIGHT_RE = re.compile(
    r"(?:copyright|&copy;|©|\(c\))[^\d]*(\d{4})", re.IGNORECASE
)
_JQUERY_RE = re.compile(
    r"jquery[.-](\d+\.\d+(?:\.\d+)?)", re.IGNORECASE
)
_BOOTSTRAP_RE = re.compile(
    r"bootstrap(?:\.min)?\.(?:css|js)\?(?:ver=)?(\d+\.\d+(?:\.\d+)?)|"
    r"bootstrap@(\d+\.\d+(?:\.\d+)?)",
    re.IGNORECASE,
)
_WP_GENERATOR_RE = re.compile(r"WordPress\s*([\d.]+)", re.IGNORECASE)

# Maps jQuery major.minor to approximate year
_JQUERY_YEAR: dict[tuple[int, int], int] = {
    (1, 4): 2010, (1, 5): 2011, (1, 6): 2011, (1, 7): 2011,
    (1, 8): 2012, (1, 9): 2013, (1, 10): 2013, (1, 11): 2014,
    (1, 12): 2016, (2, 0): 2013, (2, 1): 2014, (2, 2): 2016,
    (3, 0): 2016, (3, 1): 2016, (3, 2): 2017, (3, 3): 2018,
    (3, 4): 2019, (3, 5): 2020, (3, 6): 2021, (3, 7): 2023,
}

_BOOTSTRAP_YEAR: dict[int, int] = {2: 2013, 3: 2014, 4: 2018, 5: 2021}

_WP_YEAR: dict[str, int] = {
    "3.": 2013, "4.": 2015, "4.4": 2015, "4.5": 2016, "4.6": 2016,
    "4.7": 2016, "4.8": 2017, "4.9": 2017, "5.0": 2018, "5.1": 2019,
    "5.2": 2019, "5.3": 2019, "5.4": 2020, "5.5": 2020, "5.6": 2020,
    "5.7": 2021, "5.8": 2021, "5.9": 2022, "6.": 2022,
}


def _wp_version_year(ver: str) -> int:
    for prefix, year in sorted(_WP_YEAR.items(), key=lambda x: -len(x[0])):
        if ver.startswith(prefix):
            return year
    return 2020


def detect_design_age(html: bytes) -> dict:
    """Parse HTML and return design-age signals."""
    try:
        text = html.decode("utf-8", errors="replace")
    except Exception:
        text = ""

    soup = BeautifulSoup(html, "html.parser")
    signals: list[int] = []

    # ── copyright year ────────────────────────────────────────────────────
    copyright_year: int | None = None
    m = _COPYRIGHT_RE.search(text)
    if m:
        y = int(m.group(1))
        if 2000 <= y <= 2030:
            copyright_year = y
            signals.append(y)

    # ── jQuery version ────────────────────────────────────────────────────
    jquery_version: str | None = None
    scripts = " ".join(str(s) for s in soup.find_all("script", src=True))
    jm = _JQUERY_RE.search(scripts)
    if jm:
        jquery_version = jm.group(1)
        parts = tuple(int(x) for x in jquery_version.split(".")[:2])
        year = _JQUERY_YEAR.get(parts)
        if year:
            signals.append(year)

    # ── Bootstrap version ────────────────────────────────────────────────
    bootstrap_version: str | None = None
    links = " ".join(str(tag) for tag in soup.find_all(["link", "script"]))
    bm = _BOOTSTRAP_RE.search(links)
    if not bm:
        bm = _BOOTSTRAP_RE.search(text)
    if bm:
        bootstrap_version = bm.group(1) or bm.group(2)
        if bootstrap_version:
            major = int(bootstrap_version.split(".")[0])
            year = _BOOTSTRAP_YEAR.get(major)
            if year:
                signals.append(year)

    # ── CMS detection ─────────────────────────────────────────────────────
    cms_name: str | None = None
    cms_version: str | None = None

    generator = soup.find("meta", attrs={"name": lambda n: n and n.lower() == "generator"})
    gen_content = (generator or {}).get("content", "") if generator else ""

    wpm = _WP_GENERATOR_RE.search(gen_content or text)
    if wpm or "/wp-content/" in text or "/wp-includes/" in text:
        cms_name = "WordPress"
        if wpm:
            cms_version = wpm.group(1)
            signals.append(_wp_version_year(cms_version))

    elif "wixstatic.com" in text or "wix-thunderbolt" in text:
        cms_name = "Wix"
        signals.append(2016)
    elif "squarespace.com" in text:
        cms_name = "Squarespace"
        signals.append(2016)
    elif "shopify" in text.lower() and "cdn.shopify.com" in text:
        cms_name = "Shopify"
        signals.append(2020)

    # ── Google Analytics version ─────────────────────────────────────────
    if "gtag(" in text or "gtag.js" in text:
        signals.append(2017)
    elif "analytics.js" in text:
        signals.append(2013)

    # ── Modern CSS signals ────────────────────────────────────────────────
    if "display:grid" in text.replace(" ", "") or "display: grid" in text:
        signals.append(2018)

    # ── estimated_design_year = floor(median of signals) ─────────────────
    estimated_design_year: int | None = None
    if signals:
        estimated_design_year = int(statistics.median(signals))

    return {
        "copyright_year": copyright_year,
        "cms_name": cms_name,
        "cms_version": cms_version,
        "jquery_version": jquery_version,
        "bootstrap_version": bootstrap_version,
        "estimated_design_year": estimated_design_year,
    }
