"""Tests for rate_limiter module."""

import time
from unittest.mock import patch

import pytest

from rate_limiter import RateLimiter


class TestRateLimiterInit:
    """Tests for RateLimiter.__init__."""

    def test_uses_config_defaults(self):
        """Should use MIN_DELAY and MAX_DELAY from config when not provided."""
        limiter = RateLimiter()
        assert limiter.min_delay == 8.0
        assert limiter.max_delay == 15.0

    def test_custom_delays(self):
        """Should use provided delay values."""
        limiter = RateLimiter(min_delay=1.0, max_delay=2.0)
        assert limiter.min_delay == 1.0
        assert limiter.max_delay == 2.0

    def test_partial_custom_min_delay(self):
        """Should use custom min_delay with default max_delay."""
        limiter = RateLimiter(min_delay=5.0)
        assert limiter.min_delay == 5.0
        assert limiter.max_delay == 15.0

    def test_partial_custom_max_delay(self):
        """Should use custom max_delay with default min_delay."""
        limiter = RateLimiter(max_delay=20.0)
        assert limiter.min_delay == 8.0
        assert limiter.max_delay == 20.0


class TestRandomDelay:
    """Tests for RateLimiter.random_delay."""

    def test_returns_float(self):
        """Should return a float value."""
        limiter = RateLimiter(min_delay=1.0, max_delay=2.0)
        result = limiter.random_delay()
        assert isinstance(result, float)

    def test_within_bounds(self):
        """Should return value between min_delay and max_delay."""
        limiter = RateLimiter(min_delay=1.0, max_delay=2.0)
        for _ in range(100):
            result = limiter.random_delay()
            assert 1.0 <= result <= 2.0

    @patch("rate_limiter.random.uniform", return_value=1.5)
    def test_uses_random_uniform(self, mock_uniform):
        """Should use random.uniform for generation."""
        limiter = RateLimiter(min_delay=1.0, max_delay=2.0)
        result = limiter.random_delay()
        mock_uniform.assert_called_once_with(1.0, 2.0)
        assert result == 1.5


class TestAsyncWait:
    """Tests for RateLimiter.wait (async)."""

    async def test_waits_for_delay(self):
        """Should wait for approximately the random delay period."""
        limiter = RateLimiter(min_delay=0.1, max_delay=0.2)
        start = time.monotonic()
        await limiter.wait()
        elapsed = time.monotonic() - start
        assert 0.05 <= elapsed <= 0.35  # Allow some tolerance

    async def test_sleep_called_with_delay(self):
        """Should call asyncio.sleep with the random delay."""
        limiter = RateLimiter(min_delay=1.0, max_delay=2.0)
        with patch("rate_limiter.asyncio.sleep") as mock_sleep:
            with patch("rate_limiter.random.uniform", return_value=1.5):
                await limiter.wait()
            mock_sleep.assert_called_once_with(1.5)


class TestSyncWait:
    """Tests for RateLimiter.sync_wait."""

    def test_waits_for_delay(self):
        """Should wait for approximately the random delay period."""
        limiter = RateLimiter(min_delay=0.1, max_delay=0.2)
        start = time.monotonic()
        limiter.sync_wait()
        elapsed = time.monotonic() - start
        assert 0.05 <= elapsed <= 0.35  # Allow some tolerance

    def test_sleep_called_with_delay(self):
        """Should call time.sleep with the random delay."""
        limiter = RateLimiter(min_delay=1.0, max_delay=2.0)
        with patch("rate_limiter.time.sleep") as mock_sleep:
            with patch("rate_limiter.random.uniform", return_value=1.5):
                limiter.sync_wait()
            mock_sleep.assert_called_once_with(1.5)
