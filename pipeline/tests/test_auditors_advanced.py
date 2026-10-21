"""Tests for design age, broken links, tech stack, and orchestrator."""
from unittest.mock import patch, MagicMock

import pytest

from auditor.design_age import detect_design_age
from auditor.broken_links import check_broken_links
from auditor.tech_stack import detect_tech_stack


# ── design_age ────────────────────────────────────────────────────────────────

OLD_HTML = b"""<!DOCTYPE html>
<html>
<head>
<meta name="generator" content="WordPress 4.9.8">
<script src="/js/jquery-1.11.3.min.js"></script>
<link rel="stylesheet" href="/css/bootstrap.min.css?ver=3.3.7">
</head>
<body>
<p>Copyright &copy; 2017 Old Roofing Ltd</p>
</body>
</html>"""

MODERN_HTML = b"""<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<script src="https://cdn.jsdelivr.net/npm/jquery@3.7.1/jquery.min.js"></script>
</head>
<body>
<p>Copyright &copy; 2024 Modern Builders</p>
</body>
</html>"""


def test_design_age_old_site():
    result = detect_design_age(OLD_HTML)
    assert result["jquery_version"] is not None
    assert result["jquery_version"].startswith("1.")
    assert result["copyright_year"] == 2017
    assert result["estimated_design_year"] is not None
    assert result["estimated_design_year"] <= 2018


def test_design_age_modern_site():
    result = detect_design_age(MODERN_HTML)
    assert result["copyright_year"] == 2024
    assert result["estimated_design_year"] is not None
    assert result["estimated_design_year"] >= 2020


def test_design_age_no_signals():
    result = detect_design_age(b"<html><body>No signals</body></html>")
    assert result["copyright_year"] is None
    assert result["jquery_version"] is None


def test_design_age_detects_bootstrap_version():
    result = detect_design_age(OLD_HTML)
    assert result["bootstrap_version"] is not None
    assert result["bootstrap_version"].startswith("3.")


def test_design_age_detects_wordpress():
    result = detect_design_age(OLD_HTML)
    assert result["cms_name"] == "WordPress"
    assert result["cms_version"] is not None


# ── broken_links ──────────────────────────────────────────────────────────────

PAGE_HTML = b"""<!DOCTYPE html>
<html><body>
<a href="/page1">Good page</a>
<a href="/missing">Missing page</a>
<a href="https://external.com/ok">External</a>
</body></html>"""


def test_broken_links_counts_404s():
    def fake_head(url, **kw):
        m = MagicMock()
        m.status_code = 404 if "missing" in url else 200
        return m

    with patch("auditor.broken_links.httpx.Client") as MockClient:
        instance = MockClient.return_value.__enter__.return_value
        instance.head.side_effect = fake_head

        result = check_broken_links("https://example.com", PAGE_HTML)

    assert result["total_links"] == 3
    assert result["broken_links"] == 1
    assert any("missing" in u for u in result["broken_link_urls"])


def test_broken_links_empty_page():
    with patch("auditor.broken_links.httpx.Client"):
        result = check_broken_links("https://example.com", b"<html><body></body></html>")
    assert result["broken_links"] == 0
    assert result["total_links"] == 0


# ── tech_stack ────────────────────────────────────────────────────────────────

WP_HTML = b"""<!DOCTYPE html>
<html>
<head><link rel="stylesheet" href="/wp-content/themes/theme/style.css"></head>
<body class="wp-site"><script src="/wp-includes/js/wp-embed.min.js"></script></body>
</html>"""

WIX_HTML = b"""<!DOCTYPE html>
<html>
<head><script src="https://static.wixstatic.com/services/wix-thunderbolt.js"></script></head>
</html>"""


def test_tech_stack_detects_wordpress():
    result = detect_tech_stack(WP_HTML, headers={})
    assert result.get("cms") == "WordPress"


def test_tech_stack_detects_wix():
    result = detect_tech_stack(WIX_HTML, headers={})
    assert result.get("cms") == "Wix"


def test_tech_stack_returns_dict():
    result = detect_tech_stack(b"<html></html>", headers={})
    assert isinstance(result, dict)
