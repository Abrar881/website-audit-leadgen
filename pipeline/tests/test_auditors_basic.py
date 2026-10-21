"""Tests for PageSpeed, SSL, and mobile auditors."""
import json
import ssl
import socket
from unittest.mock import patch, MagicMock

import pytest

from auditor.pagespeed import PageSpeedClient, _extract_metrics
from auditor.ssl_check import check_ssl
from auditor.mobile_check import check_mobile


# ── PageSpeed ─────────────────────────────────────────────────────────────────

SAMPLE_PSI_RESPONSE = {
    "lighthouseResult": {
        "categories": {
            "performance": {"score": 0.23},
            "accessibility": {"score": 0.81},
            "best-practices": {"score": 0.92},
            "seo": {"score": 0.77},
        },
        "audits": {
            "first-contentful-paint": {"numericValue": 1800},
            "largest-contentful-paint": {"numericValue": 4200},
            "cumulative-layout-shift": {"numericValue": 0.15},
            "interactive": {"numericValue": 6800},
            "speed-index": {"numericValue": 3400},
        },
    }
}


def test_extract_metrics_scores():
    m = _extract_metrics(SAMPLE_PSI_RESPONSE)
    assert m["psi_performance"] == 23
    assert m["psi_accessibility"] == 81
    assert m["psi_best_practices"] == 92
    assert m["psi_seo"] == 77


def test_extract_metrics_timings():
    m = _extract_metrics(SAMPLE_PSI_RESPONSE)
    assert m["fcp_ms"] == 1800
    assert m["lcp_ms"] == 4200
    assert abs(m["cls"] - 0.15) < 0.001
    assert m["tti_ms"] == 6800
    assert m["speed_index_ms"] == 3400


def test_pagespeed_client_calls_api_and_parses(tmp_path):
    with patch("auditor.pagespeed.httpx.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.json.return_value = SAMPLE_PSI_RESPONSE
        mock_get.return_value = mock_resp

        client = PageSpeedClient(api_key="test", cache_dir=tmp_path)
        result = client.audit("https://example.com")

    assert result["psi_performance"] == 23
    assert result["lcp_ms"] == 4200
    assert "raw_psi_json" in result


def test_pagespeed_client_uses_cache(tmp_path):
    with patch("auditor.pagespeed.httpx.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.json.return_value = SAMPLE_PSI_RESPONSE
        mock_get.return_value = mock_resp

        client = PageSpeedClient(api_key="test", cache_dir=tmp_path)
        client.audit("https://example.com")
        client.audit("https://example.com")

    assert mock_get.call_count == 1  # second call served from cache


# ── SSL Check ─────────────────────────────────────────────────────────────────

def test_ssl_check_valid_cert():
    mock_cert = {
        "subject": ((("commonName", "example.com"),),),
        "issuer": ((("organizationName", "Let's Encrypt"),),),
        "notAfter": "Nov  1 00:00:00 2027 GMT",
    }
    with patch("auditor.ssl_check.ssl.create_default_context") as mock_ctx_fn:
        mock_ctx = MagicMock()
        mock_sock = MagicMock()
        mock_ctx.wrap_socket.return_value.__enter__.return_value = mock_sock
        mock_sock.getpeercert.return_value = mock_cert
        mock_ctx_fn.return_value = mock_ctx
        with patch("auditor.ssl_check.socket.create_connection"):
            result = check_ssl("https://example.com")

    assert result["has_ssl"] is True
    assert "Let's Encrypt" in result["ssl_issuer"]


def test_ssl_check_no_ssl():
    with patch("auditor.ssl_check.ssl.create_default_context") as mock_ctx_fn:
        mock_ctx = MagicMock()
        mock_ctx.wrap_socket.side_effect = ssl.SSLError("no ssl")
        mock_ctx_fn.return_value = mock_ctx
        with patch("auditor.ssl_check.socket.create_connection"):
            result = check_ssl("https://nossl.example.com")

    assert result["has_ssl"] is False


# ── Mobile Check ─────────────────────────────────────────────────────────────

RESPONSIVE_HTML = b"""<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body><p>Content</p></body>
</html>"""

NON_RESPONSIVE_HTML = b"""<!DOCTYPE html>
<html>
<head><title>Old Site</title></head>
<body><table width="800"><tr><td>Content</td></tr></table></body>
</html>"""


def test_mobile_check_responsive_site():
    with patch("auditor.mobile_check.httpx.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.content = RESPONSIVE_HTML
        mock_resp.raise_for_status.return_value = None
        mock_get.return_value = mock_resp

        result = check_mobile("https://example.com")

    assert result["has_viewport_meta"] is True
    assert result["is_responsive"] is True


def test_mobile_check_non_responsive_site():
    with patch("auditor.mobile_check.httpx.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.content = NON_RESPONSIVE_HTML
        mock_resp.raise_for_status.return_value = None
        mock_get.return_value = mock_resp

        result = check_mobile("https://old.example.com")

    assert result["has_viewport_meta"] is False
