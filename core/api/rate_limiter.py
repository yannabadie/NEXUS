"""
API Rate Limiter - Token Bucket Implementation

NEXUS V8.4.5 - Bug Fixes Phase

Provides rate limiting for API calls to prevent 429 Too Many Requests errors,
especially important for PARALLEL mode where multiple agents invoke APIs concurrently.

Features:
- Token bucket algorithm with configurable RPM and burst
- Async-safe with asyncio.Lock
- Thread-safe with threading.Lock for sync code
- Per-provider rate limits (Gemini, Claude have different limits)
- Automatic token refill over time

Usage:
    # Async usage
    limiter = APIRateLimiter(requests_per_minute=60, burst_size=10)
    await limiter.acquire_async()  # Blocks until token available
    response = await api_call()

    # Sync usage (for ThreadPoolExecutor)
    limiter.acquire_sync(timeout=30.0)  # Blocks until token available
    response = api_call()
"""

import asyncio
import time
import threading
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Optional, Deque


class RateLimitExceeded(Exception):
    """Raised when rate limit is exceeded and timeout is reached."""
    pass


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting per provider."""
    requests_per_minute: int = 60
    burst_size: int = 10
    retry_after_seconds: float = 1.0


# Default rate limits per provider (based on API documentation)
DEFAULT_LIMITS: Dict[str, RateLimitConfig] = {
    "gemini": RateLimitConfig(requests_per_minute=60, burst_size=10),
    "claude": RateLimitConfig(requests_per_minute=50, burst_size=8),
    "default": RateLimitConfig(requests_per_minute=30, burst_size=5),
}


class APIRateLimiter:
    """
    Token bucket rate limiter for API calls.

    Thread-safe and async-safe implementation using both asyncio.Lock
    and threading.Lock for hybrid sync/async usage.

    Attributes:
        rpm: Requests per minute limit
        burst: Maximum burst size (tokens available at once)
        provider: Provider name for logging
    """

    def __init__(
        self,
        requests_per_minute: int = 60,
        burst_size: int = 10,
        provider: str = "default"
    ):
        """
        Initialize rate limiter.

        Args:
            requests_per_minute: Maximum requests per minute
            burst_size: Maximum burst size (concurrent requests)
            provider: Provider name (gemini, claude, etc.) for logging
        """
        self.rpm = requests_per_minute
        self.burst = burst_size
        self.provider = provider

        # Token bucket state
        self._tokens: Deque[float] = deque(maxlen=burst_size)
        self._token_interval = 60.0 / requests_per_minute  # Seconds per token

        # Thread safety
        self._async_lock = asyncio.Lock()
        self._sync_lock = threading.Lock()

        # Statistics
        self._total_requests = 0
        self._total_waits = 0
        self._total_wait_time = 0.0

    def _refill_tokens(self) -> int:
        """
        Refill tokens based on elapsed time.

        Returns:
            Number of tokens added
        """
        now = time.time()

        # Remove expired tokens (older than 60 seconds)
        while self._tokens and (now - self._tokens[0]) > 60.0:
            self._tokens.popleft()

        # Calculate available capacity
        current_tokens = len(self._tokens)
        available_capacity = self.burst - current_tokens

        return available_capacity

    def _try_acquire(self) -> bool:
        """
        Try to acquire a token without waiting.

        Returns:
            True if token acquired, False if rate limited
        """
        now = time.time()

        # Refill and check capacity
        available = self._refill_tokens()

        if available > 0 or len(self._tokens) < self.burst:
            # Add new token timestamp
            self._tokens.append(now)
            self._total_requests += 1
            return True

        return False

    def _time_until_available(self) -> float:
        """
        Calculate time until a token will be available.

        Returns:
            Seconds until next token available (0 if available now)
        """
        if not self._tokens:
            return 0.0

        # Oldest token will expire after 60 seconds
        oldest = self._tokens[0]
        now = time.time()
        time_until_expire = 60.0 - (now - oldest)

        return max(0.0, time_until_expire)

    async def acquire(self, timeout: float = 30.0) -> None:
        """
        V11 FIX F16: Async acquire alias for acquire_async().

        This method exists because base.py:356 calls acquire() but only
        acquire_async() and acquire_sync() existed before.

        Args:
            timeout: Maximum time to wait in seconds

        Raises:
            RateLimitExceeded: If timeout reached without acquiring token
        """
        await self.acquire_async(timeout)

    async def acquire_async(self, timeout: float = 30.0) -> None:
        """
        Acquire a rate limit token (async version).

        Blocks until a token is available or timeout is reached.

        Args:
            timeout: Maximum time to wait in seconds

        Raises:
            RateLimitExceeded: If timeout reached without acquiring token
        """
        start_time = time.time()

        async with self._async_lock:
            while True:
                if self._try_acquire():
                    return

                # Check timeout
                elapsed = time.time() - start_time
                if elapsed >= timeout:
                    raise RateLimitExceeded(
                        f"Rate limit exceeded for {self.provider}. "
                        f"Waited {elapsed:.1f}s (timeout: {timeout}s)"
                    )

                # Calculate wait time
                wait_time = min(
                    self._time_until_available(),
                    timeout - elapsed,
                    self._token_interval
                )

                self._total_waits += 1
                self._total_wait_time += wait_time

                # Wait before retry
                await asyncio.sleep(wait_time)

    def acquire_sync(self, timeout: float = 30.0) -> None:
        """
        Acquire a rate limit token (sync version for ThreadPoolExecutor).

        Blocks until a token is available or timeout is reached.

        Args:
            timeout: Maximum time to wait in seconds

        Raises:
            RateLimitExceeded: If timeout reached without acquiring token
        """
        start_time = time.time()

        with self._sync_lock:
            while True:
                if self._try_acquire():
                    return

                # Check timeout
                elapsed = time.time() - start_time
                if elapsed >= timeout:
                    raise RateLimitExceeded(
                        f"Rate limit exceeded for {self.provider}. "
                        f"Waited {elapsed:.1f}s (timeout: {timeout}s)"
                    )

                # Calculate wait time
                wait_time = min(
                    self._time_until_available(),
                    timeout - elapsed,
                    self._token_interval
                )

                self._total_waits += 1
                self._total_wait_time += wait_time

                # Release lock while waiting
                self._sync_lock.release()
                try:
                    time.sleep(wait_time)
                finally:
                    self._sync_lock.acquire()

    def get_stats(self) -> Dict:
        """
        Get rate limiter statistics.

        Returns:
            Dict with total_requests, total_waits, total_wait_time, avg_wait_time
        """
        avg_wait = (
            self._total_wait_time / self._total_waits
            if self._total_waits > 0
            else 0.0
        )

        return {
            "provider": self.provider,
            "rpm_limit": self.rpm,
            "burst_limit": self.burst,
            "total_requests": self._total_requests,
            "total_waits": self._total_waits,
            "total_wait_time": round(self._total_wait_time, 2),
            "avg_wait_time": round(avg_wait, 3),
            "current_bucket_size": len(self._tokens)
        }

    def reset(self) -> None:
        """Reset the rate limiter state and statistics."""
        with self._sync_lock:
            self._tokens.clear()
            self._total_requests = 0
            self._total_waits = 0
            self._total_wait_time = 0.0


class RateLimiterRegistry:
    """
    Registry of rate limiters per provider.

    Singleton pattern to ensure consistent rate limiting across the application.
    """

    _instance: Optional["RateLimiterRegistry"] = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._limiters: Dict[str, APIRateLimiter] = {}
        return cls._instance

    def get_limiter(self, provider: str) -> APIRateLimiter:
        """
        Get or create rate limiter for a provider.

        Args:
            provider: Provider name (gemini, claude, etc.)

        Returns:
            APIRateLimiter instance for the provider
        """
        if provider not in self._limiters:
            config = DEFAULT_LIMITS.get(provider, DEFAULT_LIMITS["default"])
            self._limiters[provider] = APIRateLimiter(
                requests_per_minute=config.requests_per_minute,
                burst_size=config.burst_size,
                provider=provider
            )
        return self._limiters[provider]

    def get_all_stats(self) -> Dict[str, Dict]:
        """
        Get statistics from all rate limiters.

        Returns:
            Dict mapping provider to stats
        """
        return {
            provider: limiter.get_stats()
            for provider, limiter in self._limiters.items()
        }

    def reset_all(self) -> None:
        """Reset all rate limiters."""
        for limiter in self._limiters.values():
            limiter.reset()


# =============================================================================
# V10 PRISM: Multi-Tenant Rate Limiter Access
# =============================================================================


def get_rate_limiter_registry() -> RateLimiterRegistry:
    """
    Get the rate limiter registry for the current tenant context.

    V10 PRISM: Returns tenant-scoped registry via ServiceFactory.
    Falls back to global singleton if no context is active.

    Returns:
        RateLimiterRegistry instance scoped to current tenant
    """
    # V10: Try ServiceFactory first (tenant-scoped)
    try:
        from ..context import has_active_session
        if has_active_session():
            from ..factory import ServiceFactory
            return ServiceFactory.get_rate_limiter_registry()
    except ImportError:
        pass  # context module not available, use legacy

    # Legacy fallback: global singleton
    return RateLimiterRegistry()


def get_rate_limiter(provider: str) -> APIRateLimiter:
    """
    Convenience function to get rate limiter for a provider.

    V10 PRISM: Uses tenant-scoped registry.

    Args:
        provider: Provider name (gemini, claude, etc.)

    Returns:
        APIRateLimiter instance scoped to current tenant
    """
    return get_rate_limiter_registry().get_limiter(provider)
