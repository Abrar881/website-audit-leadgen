"""Tests for rate limiter and disk cache."""
import time
import tempfile
from pathlib import Path

import pytest

from utils.rate_limiter import RateLimiter
from utils.cache import DiskCache


# ── RateLimiter ──────────────────────────────────────────────────────────────

def test_rate_limiter_allows_burst_up_to_capacity():
    limiter = RateLimiter(rate=10.0, capacity=3)
    # Should acquire 3 without sleeping
    t0 = time.monotonic()
    for _ in range(3):
        limiter.acquire()
    elapsed = time.monotonic() - t0
    assert elapsed < 0.2, f"burst of 3 took too long: {elapsed:.2f}s"


def test_rate_limiter_throttles_beyond_capacity():
    limiter = RateLimiter(rate=10.0, capacity=1)
    # First free, second must wait ~0.1s
    limiter.acquire()
    t0 = time.monotonic()
    limiter.acquire()
    elapsed = time.monotonic() - t0
    assert elapsed >= 0.08, f"should have waited but only took {elapsed:.3f}s"


# ── DiskCache ────────────────────────────────────────────────────────────────

@pytest.fixture
def cache(tmp_path):
    return DiskCache(tmp_path, ttl_seconds=60)


def test_disk_cache_miss_returns_none(cache):
    assert cache.get("missing_key") is None


def test_disk_cache_stores_and_retrieves(cache):
    cache.set("my_key", {"result": 42})
    assert cache.get("my_key") == {"result": 42}


def test_disk_cache_expired_returns_none(tmp_path):
    cache = DiskCache(tmp_path, ttl_seconds=0)
    cache.set("key", {"x": 1})
    time.sleep(0.01)
    assert cache.get("key") is None


def test_disk_cache_key_is_deterministic(cache):
    cache.set("k", {"v": 1})
    assert cache.get("k") == {"v": 1}
    # Setting again overwrites
    cache.set("k", {"v": 2})
    assert cache.get("k") == {"v": 2}
