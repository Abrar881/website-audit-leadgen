"""Token-bucket rate limiter. Thread-safe, blocking."""
from __future__ import annotations

import threading
import time


class RateLimiter:
    """Token-bucket rate limiter.

    Args:
        rate: tokens replenished per second
        capacity: maximum tokens in the bucket (burst size)
    """

    def __init__(self, rate: float, capacity: float | None = None) -> None:
        self.rate = rate
        self.capacity = capacity if capacity is not None else rate
        self._tokens = self.capacity
        self._last = time.monotonic()
        self._lock = threading.Lock()

    def acquire(self, tokens: float = 1.0) -> None:
        """Block until `tokens` are available, then consume them."""
        with self._lock:
            while True:
                now = time.monotonic()
                elapsed = now - self._last
                self._tokens = min(self.capacity, self._tokens + elapsed * self.rate)
                self._last = now

                if self._tokens >= tokens:
                    self._tokens -= tokens
                    return

                # Sleep until enough tokens accumulate
                deficit = tokens - self._tokens
                sleep_for = deficit / self.rate
                time.sleep(sleep_for)
