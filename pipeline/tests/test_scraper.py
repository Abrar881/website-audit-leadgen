"""Tests for Google Places scraper and deduplicator."""
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from scraper.deduplicator import Deduplicator, normalize_domain
from scraper.google_places import PlacesClient, _extract_postcode, _parse_place


# ── normalize_domain ─────────────────────────────────────────────────────────

def test_normalize_domain_strips_www():
    assert normalize_domain("https://www.example.com/page") == "example.com"


def test_normalize_domain_strips_trailing_slash():
    assert normalize_domain("http://example.com/") == "example.com"


def test_normalize_domain_handles_none():
    assert normalize_domain(None) is None


def test_normalize_domain_handles_listing_sites():
    assert normalize_domain("https://www.yell.com/biz/foo") == "yell.com"


# ── Deduplicator ─────────────────────────────────────────────────────────────

def make_place(place_id="abc", domain="example.com", phone="+441234567890"):
    return {"place_id": place_id, "website": f"https://{domain}", "phone": phone}


def test_deduplicator_allows_first_occurrence():
    d = Deduplicator()
    assert d.is_duplicate(make_place("a", "a.com", "+441")) is False


def test_deduplicator_blocks_same_place_id():
    d = Deduplicator()
    d.is_duplicate(make_place("a", "a.com", "+441"))
    assert d.is_duplicate(make_place("a", "b.com", "+442")) is True


def test_deduplicator_blocks_same_domain():
    d = Deduplicator()
    d.is_duplicate(make_place("a", "same.com", "+441"))
    assert d.is_duplicate(make_place("b", "same.com", "+442")) is True


def test_deduplicator_blocks_same_phone():
    d = Deduplicator()
    d.is_duplicate(make_place("a", "a.com", "+441234567890"))
    assert d.is_duplicate(make_place("b", "b.com", "+441234567890")) is True


def test_deduplicator_allows_different_businesses():
    d = Deduplicator()
    d.is_duplicate(make_place("a", "a.com", "+441"))
    assert d.is_duplicate(make_place("b", "b.com", "+442")) is False


# ── _extract_postcode ─────────────────────────────────────────────────────────

def test_extract_postcode_from_full_address():
    addr = "123 High Street, London SE1 7PB, UK"
    assert _extract_postcode(addr) == "SE1"


def test_extract_postcode_none_when_missing():
    assert _extract_postcode("No postcode here") is None


# ── _parse_place ──────────────────────────────────────────────────────────────

SAMPLE_PLACE = {
    "id": "ChIJ_sample",
    "displayName": {"text": "Test Solar Ltd"},
    "formattedAddress": "1 Test St, London SE5 8AB, UK",
    "location": {"latitude": 51.47, "longitude": -0.07},
    "nationalPhoneNumber": "+44 20 9876 5432",
    "websiteUri": "https://testsolar.co.uk",
    "rating": 4.5,
    "userRatingCount": 28,
    "businessStatus": "OPERATIONAL",
    "types": ["electrician", "establishment"],
}


def test_parse_place_extracts_all_fields():
    result = _parse_place(SAMPLE_PLACE, trade_category="solar panel installer")
    assert result["place_id"] == "ChIJ_sample"
    assert result["name"] == "Test Solar Ltd"
    assert result["trade_category"] == "solar panel installer"
    assert result["website"] == "https://testsolar.co.uk"
    assert result["google_rating"] == 4.5
    assert result["review_count"] == 28
    assert result["postcode"] == "SE5"
    assert result["lat"] == pytest.approx(51.47)


def test_parse_place_handles_missing_website():
    place = {**SAMPLE_PLACE, "websiteUri": None}
    result = _parse_place(place, trade_category="roofing contractor")
    assert result["website"] is None


# ── PlacesClient (mocked HTTP) ────────────────────────────────────────────────

def test_places_client_search_returns_parsed_places(tmp_path):
    mock_response = {
        "places": [SAMPLE_PLACE],
    }
    with patch("scraper.google_places.httpx.Client") as MockClient:
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.json.return_value = mock_response
        MockClient.return_value.__enter__.return_value.post.return_value = mock_resp

        client = PlacesClient(api_key="test_key", cache_dir=tmp_path)
        results = client.text_search("solar installer in SE5", "solar panel installer")

    assert len(results) == 1
    assert results[0]["place_id"] == "ChIJ_sample"
    assert results[0]["name"] == "Test Solar Ltd"
