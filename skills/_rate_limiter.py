"""
Centralized rate limiter for API calls.
Prevents exceeding rate limits across all skills.
"""
import time
from threading import Lock


class RateLimiter:
    """Thread-safe rate limiter using token bucket algorithm."""

    def __init__(self, calls_per_second: float = 1.0):
        """
        Initialize rate limiter.

        Args:
            calls_per_second: Maximum calls allowed per second
        """
        self.min_interval = 1.0 / calls_per_second if calls_per_second > 0 else 0
        self.last_call = 0.0
        self._lock = Lock()

    def wait(self):
        """
        Wait if necessary to respect rate limit.
        Call this before every API request.
        """
        with self._lock:
            now = time.time()
            time_since_last = now - self.last_call

            if time_since_last < self.min_interval:
                sleep_time = self.min_interval - time_since_last
                time.sleep(sleep_time)

            self.last_call = time.time()


# Pre-configured limiters for common APIs
STEAM_LIMITER = RateLimiter(calls_per_second=1.0)  # Steam: 1 req/sec
GG_DEALS_LIMITER = RateLimiter(calls_per_second=2.0)  # GG.deals: 2 req/sec
ITAD_LIMITER = RateLimiter(calls_per_second=1.0)  # ITAD: 1 req/sec
DISCORD_LIMITER = RateLimiter(calls_per_second=5.0)  # Discord: 5 req/sec
