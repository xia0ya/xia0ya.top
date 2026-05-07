"""Rate limiter for Amazon scraper."""

import asyncio
import random
import time

from config import config


class RateLimiter:
    """Rate limiter with configurable delay bounds."""

    def __init__(self, min_delay: float | None = None, max_delay: float | None = None):
        """Initialize rate limiter.

        Args:
            min_delay: Minimum delay in seconds. Defaults to config.MIN_DELAY.
            max_delay: Maximum delay in seconds. Defaults to config.MAX_DELAY.
        """
        self.min_delay = min_delay if min_delay is not None else config.MIN_DELAY
        self.max_delay = max_delay if max_delay is not None else config.MAX_DELAY

    def random_delay(self) -> float:
        """Generate random delay between min and max delay.

        Returns:
            Random float between min_delay and max_delay.
        """
        return random.uniform(self.min_delay, self.max_delay)

    async def wait(self) -> None:
        """Asynchronously wait for a random delay period."""
        delay = self.random_delay()
        await asyncio.sleep(delay)

    def sync_wait(self) -> None:
        """Synchronously wait for a random delay period."""
        delay = self.random_delay()
        time.sleep(delay)
