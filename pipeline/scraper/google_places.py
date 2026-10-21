"""Google Places API (New) client with field masking, caching, and rate limiting."""
from __future__ import annotations

import json
import re
from pathlib import Path

import httpx

from utils.cache import DiskCache
from utils.rate_limiter import RateLimiter
from config import PLACES_API_RPS

_PLACES_URL = "https://places.googleapis.com/v1/places:searchText"

# Fields billed at basic+contact tier (not expensive pro fields like reviews text)
_FIELD_MASK = ",".join([
    "places.id",
    "places.displayName",
    "places.formattedAddress",
    "places.location",
    "places.nationalPhoneNumber",
    "places.websiteUri",
    "places.rating",
    "places.userRatingCount",
    "places.businessStatus",
    "places.types",
])

_UK_POSTCODE_RE = re.compile(
    r"\b([A-Z]{1,2}\d{1,2}[A-Z]?)\s*\d[A-Z]{2}\b", re.IGNORECASE
)


def _extract_postcode(address: str | None) -> str | None:
    """Extract the outward postcode area (e.g. 'SE1') from a formatted address."""
    if not address:
        return None
    m = _UK_POSTCODE_RE.search(address)
    return m.group(1).upper() if m else None


def _parse_place(place: dict, trade_category: str) -> dict:
    """Normalise a raw Places API place object into our business dict."""
    return {
        "place_id": place.get("id"),
        "name": (place.get("displayName") or {}).get("text"),
        "trade_category": trade_category,
        "address": place.get("formattedAddress"),
        "postcode": _extract_postcode(place.get("formattedAddress")),
        "lat": (place.get("location") or {}).get("latitude"),
        "lng": (place.get("location") or {}).get("longitude"),
        "phone": place.get("nationalPhoneNumber"),
        "website": place.get("websiteUri") or None,
        "google_rating": place.get("rating"),
        "review_count": place.get("userRatingCount", 0),
        "business_status": place.get("businessStatus", "UNKNOWN"),
        "types": place.get("types", []),
    }


class PlacesClient:
    """Thin wrapper around the Places API Text Search endpoint."""

    def __init__(self, api_key: str, cache_dir: str | Path) -> None:
        self.api_key = api_key
        self._cache = DiskCache(cache_dir, ttl_seconds=60 * 60 * 24 * 30)  # 30 days
        self._limiter = RateLimiter(rate=PLACES_API_RPS, capacity=PLACES_API_RPS)
        self.api_calls_made = 0

    def text_search(
        self,
        query: str,
        trade_category: str,
        page_token: str | None = None,
    ) -> list[dict]:
        """Search for places and return all paginated results (max 60)."""
        cache_key = f"places:{query}:{page_token or ''}"
        cached = self._cache.get(cache_key)
        if cached is not None:
            return [_parse_place(p, trade_category) for p in cached]

        all_raw: list[dict] = []
        next_token = page_token

        with httpx.Client(timeout=30) as client:
            while True:
                body: dict = {
                    "textQuery": query,
                    "locationRestriction": {
                        "rectangle": {
                            "low": {"latitude": 50.8, "longitude": -1.8},
                            "high": {"latitude": 51.9, "longitude": 0.4},
                        }
                    },
                    "pageSize": 20,
                }
                if next_token:
                    body["pageToken"] = next_token

                self._limiter.acquire()
                resp = client.post(
                    _PLACES_URL,
                    headers={
                        "X-Goog-Api-Key": self.api_key,
                        "X-Goog-FieldMask": _FIELD_MASK,
                        "Content-Type": "application/json",
                    },
                    json=body,
                )
                resp.raise_for_status()
                self.api_calls_made += 1

                data = resp.json()
                places = data.get("places", [])
                all_raw.extend(places)

                next_token = data.get("nextPageToken")
                if not next_token or len(all_raw) >= 60:
                    break

        self._cache.set(cache_key, all_raw)
        return [_parse_place(p, trade_category) for p in all_raw]
