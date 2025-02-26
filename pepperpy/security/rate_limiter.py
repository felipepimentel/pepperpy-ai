"""Rate limiting functionality.

This module provides rate limiting functionality to prevent API abuse
and ensure fair resource usage.
"""

import asyncio
import time
from typing import Dict, Optional

from pepperpy.monitoring import logger


class RateLimiter:
    """Rate limiter for API requests."""

    def __init__(
        self,
        requests_per_minute: int = 60,
        burst_size: int = 10,
    ) -> None:
        """Initialize rate limiter.

        Args:
            requests_per_minute: Maximum number of requests per minute
            burst_size: Maximum burst size
        """
        self.requests_per_minute = requests_per_minute
        self.burst_size = burst_size
        self.window_size = 60  # 1 minute in seconds
        self._requests: Dict[str, list] = {}
        self._locks: Dict[str, asyncio.Lock] = {}

    async def check_rate(self, key: str) -> bool:
        """Check if a request is allowed under the rate limit.

        Args:
            key: Key to track rate limit for

        Returns:
            bool: True if request is allowed, False if rate limit exceeded
        """
        # Get or create lock for this key
        if key not in self._locks:
            self._locks[key] = asyncio.Lock()

        async with self._locks[key]:
            # Initialize request list if needed
            if key not in self._requests:
                self._requests[key] = []

            # Clean old requests
            current_time = time.time()
            window_start = current_time - self.window_size
            self._requests[key] = [t for t in self._requests[key] if t > window_start]

            # Check rate limit
            if len(self._requests[key]) >= self.requests_per_minute:
                logger.warning(
                    "Rate limit exceeded for %s: %d requests (limit: %d)",
                    key,
                    len(self._requests[key]),
                    self.requests_per_minute,
                )
                return False

            # Check burst limit
            recent_requests = [
                t
                for t in self._requests[key]
                if t > current_time - 1  # Last second
            ]
            if len(recent_requests) >= self.burst_size:
                logger.warning(
                    "Burst limit exceeded for %s: %d requests (limit: %d)",
                    key,
                    len(recent_requests),
                    self.burst_size,
                )
                return False

            # Record request
            self._requests[key].append(current_time)
            return True

    async def wait_for_token(
        self,
        key: str,
        timeout: Optional[float] = None,
    ) -> bool:
        """Wait for a rate limit token to become available.

        Args:
            key: Key to track rate limit for
            timeout: Maximum time to wait in seconds

        Returns:
            bool: True if token was acquired, False if timeout
        """
        start_time = time.time()
        while True:
            if await self.check_rate(key):
                return True

            if timeout is not None:
                if time.time() - start_time >= timeout:
                    return False

            # Wait before retrying
            await asyncio.sleep(1)

    def reset(self, key: str) -> None:
        """Reset rate limit for a key.

        Args:
            key: Key to reset rate limit for
        """
        if key in self._requests:
            del self._requests[key]
        if key in self._locks:
            del self._locks[key]
