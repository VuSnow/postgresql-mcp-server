"""
RateLimiter — thread-safe sliding-window rate limiter.

Tracks query timestamps and rejects calls that exceed the configured
max_calls within the window_seconds period.
"""

import logging
import time
import threading
from collections import deque

logger = logging.getLogger(__name__)


class RateLimiter:
    """Sliding-window rate limiter. Thread-safe."""

    def __init__(self, max_calls: int = 100, window_seconds: int = 3600):
        self._max_calls = max_calls
        self._window_seconds = window_seconds
        self._timestamps: deque[float] = deque()
        self._lock = threading.Lock()

    @property
    def max_calls(self) -> int:
        return self._max_calls

    @property
    def window_seconds(self) -> int:
        return self._window_seconds

    def _purge_expired(self, now: float) -> None:
        """Remove timestamps outside the current window."""
        cutoff = now - self._window_seconds
        while self._timestamps and self._timestamps[0] < cutoff:
            self._timestamps.popleft()

    def check(self) -> bool:
        """
        Check if a new call is allowed.
        Returns True if allowed, False if rate limit exceeded.
        Does NOT record the call — use record() after successful execution.
        """
        now = time.time()
        with self._lock:
            self._purge_expired(now)
            return len(self._timestamps) < self._max_calls

    def record(self) -> None:
        """Record a successful call timestamp."""
        now = time.time()
        with self._lock:
            self._timestamps.append(now)

    def check_and_record(self) -> bool:
        """
        Atomic check + record. Returns True if allowed (and recorded),
        False if rate limit exceeded (not recorded).
        """
        now = time.time()
        with self._lock:
            self._purge_expired(now)
            if len(self._timestamps) >= self._max_calls:
                return False
            self._timestamps.append(now)
            return True

    def remaining(self) -> int:
        """Return number of remaining calls in current window."""
        now = time.time()
        with self._lock:
            self._purge_expired(now)
            return max(0, self._max_calls - len(self._timestamps))

    def reset(self) -> None:
        """Clear all recorded timestamps."""
        with self._lock:
            self._timestamps.clear()
