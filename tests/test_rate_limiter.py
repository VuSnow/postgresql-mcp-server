"""Tests for RateLimiter — sliding window, concurrency."""

import time
import threading
import pytest
from postgresql_mcp.guardrails.rate_limiter import RateLimiter


class TestBasicBehavior:
    def test_allows_within_limit(self):
        rl = RateLimiter(max_calls=5, window_seconds=60)
        for _ in range(5):
            assert rl.check_and_record() is True

    def test_blocks_when_exceeded(self):
        rl = RateLimiter(max_calls=3, window_seconds=60)
        for _ in range(3):
            rl.check_and_record()
        assert rl.check() is False

    def test_remaining_count(self):
        rl = RateLimiter(max_calls=5, window_seconds=60)
        assert rl.remaining() == 5
        rl.check_and_record()
        assert rl.remaining() == 4

    def test_reset_clears(self):
        rl = RateLimiter(max_calls=3, window_seconds=60)
        for _ in range(3):
            rl.check_and_record()
        assert rl.check() is False
        rl.reset()
        assert rl.check() is True
        assert rl.remaining() == 3


class TestSlidingWindow:
    def test_expired_entries_purged(self):
        rl = RateLimiter(max_calls=2, window_seconds=1)
        rl.check_and_record()
        rl.check_and_record()
        assert rl.check() is False

        # Wait for window to expire
        time.sleep(1.1)
        assert rl.check() is True

    def test_partial_expiry(self):
        rl = RateLimiter(max_calls=3, window_seconds=1)
        rl.check_and_record()
        time.sleep(0.6)
        rl.check_and_record()
        rl.check_and_record()

        # First call should expire after 1s total
        time.sleep(0.5)
        # Now first call is >1s old, should be purged
        assert rl.remaining() >= 1


class TestCheckVsRecord:
    def test_check_does_not_record(self):
        rl = RateLimiter(max_calls=2, window_seconds=60)
        # check() alone doesn't consume quota
        for _ in range(10):
            assert rl.check() is True
        assert rl.remaining() == 2

    def test_record_consumes_quota(self):
        rl = RateLimiter(max_calls=2, window_seconds=60)
        rl.record()
        rl.record()
        assert rl.check() is False


class TestThreadSafety:
    def test_concurrent_access(self):
        rl = RateLimiter(max_calls=100, window_seconds=60)
        results = []

        def worker():
            for _ in range(20):
                results.append(rl.check_and_record())

        threads = [threading.Thread(target=worker) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # 200 attempts, only 100 should succeed
        assert sum(results) == 100
        assert results.count(False) == 100


class TestProperties:
    def test_max_calls_property(self):
        rl = RateLimiter(max_calls=42, window_seconds=300)
        assert rl.max_calls == 42

    def test_window_seconds_property(self):
        rl = RateLimiter(max_calls=10, window_seconds=600)
        assert rl.window_seconds == 600
