"""Disk-based JSON cache keyed by a string, with TTL."""
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path


class DiskCache:
    """Simple disk cache: each entry is a JSON file with a TTL wrapper.

    Args:
        directory: where cache files are stored (created if absent)
        ttl_seconds: how long entries are considered fresh (0 = never fresh)
    """

    def __init__(self, directory: str | Path, ttl_seconds: int = 86400) -> None:
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        self.ttl_seconds = ttl_seconds

    def _path(self, key: str) -> Path:
        digest = hashlib.sha256(key.encode()).hexdigest()[:32]
        return self.directory / f"{digest}.json"

    def get(self, key: str) -> object | None:
        """Return cached value or None if missing / expired."""
        p = self._path(key)
        if not p.exists():
            return None
        try:
            envelope = json.loads(p.read_text())
            if self.ttl_seconds == 0:
                return None
            if time.time() - envelope["ts"] > self.ttl_seconds:
                return None
            return envelope["data"]
        except (json.JSONDecodeError, KeyError, OSError):
            return None

    def set(self, key: str, value: object) -> None:
        """Store value under key."""
        p = self._path(key)
        envelope = {"ts": time.time(), "data": value}
        p.write_text(json.dumps(envelope))

    def delete(self, key: str) -> None:
        self._path(key).unlink(missing_ok=True)
