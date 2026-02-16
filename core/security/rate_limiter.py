"""
Rate Limiter - Token bucket rate limiting for API and tool calls.

V12.4 COGNITIVE BOOST - Task #66

Provides per-key rate limiting using the token bucket algorithm.
Supports burst allowance, multiple limit tiers, and statistics.

Usage:
    from core.security.rate_limiter import get_rate_limiter

    limiter = get_rate_limiter()

    # Configure a limit
    limiter.configure("api", tokens_per_second=10, bucket_size=20)

    # Check before calling
    if limiter.allow("api", "user-123"):
        # proceed
    else:
        wait = limiter.retry_after("api", "user-123")
"""

from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

_logger = logging.getLogger(__name__)


# =============================================================================
# Constants
# =============================================================================

DEFAULT_TOKENS_PER_SECOND = 10.0
DEFAULT_BUCKET_SIZE = 20
MAX_LIMITS = 500
MAX_KEYS_PER_LIMIT = 50000


# =============================================================================
# Types
# =============================================================================

@dataclass
class RateLimitConfig:
    """Configuration for a rate limit."""
    name: str
    tokens_per_second: float = DEFAULT_TOKENS_PER_SECOND
    bucket_size: int = DEFAULT_BUCKET_SIZE

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "tokens_per_second": self.tokens_per_second,
            "bucket_size": self.bucket_size,
        }


@dataclass
class BucketState:
    """Internal state for a token bucket."""
    tokens: float
    last_refill: float
    total_allowed: int = 0
    total_denied: int = 0


@dataclass
class RateLimitResult:
    """Result of a rate limit check."""
    allowed: bool
    remaining_tokens: float = 0.0
    retry_after_seconds: float = 0.0
    limit_name: str = ""
    key: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "allowed": self.allowed,
            "remaining_tokens": round(self.remaining_tokens, 2),
            "retry_after_seconds": round(self.retry_after_seconds, 3),
            "limit_name": self.limit_name,
            "key": self.key,
        }


@dataclass
class LimiterStats:
    """Rate limiter statistics."""
    configured_limits: int
    total_keys: int
    total_allowed: int
    total_denied: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "configured_limits": self.configured_limits,
            "total_keys": self.total_keys,
            "total_allowed": self.total_allowed,
            "total_denied": self.total_denied,
        }


# =============================================================================
# Rate Limiter
# =============================================================================

class RateLimiter:
    """
    Token bucket rate limiter.

    Features:
    - Per-key token bucket algorithm
    - Configurable rates and burst sizes
    - Multiple named limit tiers
    - Retry-after calculation
    - Statistics tracking
    - Thread-safe
    """

    def __init__(self):
        self._configs: Dict[str, RateLimitConfig] = {}
        self._buckets: Dict[str, Dict[str, BucketState]] = {}
        self._lock = threading.Lock()

    # =========================================================================
    # Configuration
    # =========================================================================

    def configure(
        self,
        name: str,
        *,
        tokens_per_second: float = DEFAULT_TOKENS_PER_SECOND,
        bucket_size: int = DEFAULT_BUCKET_SIZE,
    ) -> RateLimitConfig:
        """Configure a named rate limit."""
        config = RateLimitConfig(
            name=name,
            tokens_per_second=tokens_per_second,
            bucket_size=bucket_size,
        )
        with self._lock:
            if len(self._configs) >= MAX_LIMITS and name not in self._configs:
                raise ValueError(f"Maximum limits ({MAX_LIMITS}) reached")
            self._configs[name] = config
            if name not in self._buckets:
                self._buckets[name] = {}
        return config

    def unconfigure(self, name: str) -> bool:
        """Remove a rate limit configuration."""
        with self._lock:
            if name not in self._configs:
                return False
            del self._configs[name]
            self._buckets.pop(name, None)
            return True

    def get_config(self, name: str) -> Optional[RateLimitConfig]:
        """Get a rate limit configuration."""
        return self._configs.get(name)

    def list_configs(self) -> List[RateLimitConfig]:
        """List all configured rate limits."""
        return list(self._configs.values())

    # =========================================================================
    # Rate Limiting
    # =========================================================================

    def _refill(self, bucket: BucketState, config: RateLimitConfig, now: float) -> None:
        """Refill tokens based on elapsed time."""
        elapsed = now - bucket.last_refill
        if elapsed > 0:
            new_tokens = elapsed * config.tokens_per_second
            bucket.tokens = min(config.bucket_size, bucket.tokens + new_tokens)
            bucket.last_refill = now

    def _get_or_create_bucket(
        self, limit_name: str, key: str, config: RateLimitConfig, now: float
    ) -> BucketState:
        """Get or create a bucket for a key."""
        buckets = self._buckets.get(limit_name)
        if buckets is None:
            buckets = {}
            self._buckets[limit_name] = buckets

        bucket = buckets.get(key)
        if bucket is None:
            bucket = BucketState(
                tokens=float(config.bucket_size),
                last_refill=now,
            )
            buckets[key] = bucket
        return bucket

    def allow(self, limit_name: str, key: str, *, cost: float = 1.0) -> bool:
        """
        Check if a request is allowed under the rate limit.

        Args:
            limit_name: Name of the configured limit
            key: Unique key (e.g., user ID, IP)
            cost: Token cost of the request

        Returns:
            True if allowed, False if rate limited
        """
        result = self.check(limit_name, key, cost=cost)
        return result.allowed

    def check(self, limit_name: str, key: str, *, cost: float = 1.0) -> RateLimitResult:
        """
        Check rate limit and return detailed result.

        Args:
            limit_name: Name of the configured limit
            key: Unique key
            cost: Token cost

        Returns:
            RateLimitResult with details
        """
        with self._lock:
            config = self._configs.get(limit_name)
            if config is None:
                return RateLimitResult(
                    allowed=True,
                    limit_name=limit_name,
                    key=key,
                )

            now = time.monotonic()
            bucket = self._get_or_create_bucket(limit_name, key, config, now)
            self._refill(bucket, config, now)

            if bucket.tokens >= cost:
                bucket.tokens -= cost
                bucket.total_allowed += 1
                return RateLimitResult(
                    allowed=True,
                    remaining_tokens=bucket.tokens,
                    limit_name=limit_name,
                    key=key,
                )
            else:
                # Calculate retry-after
                needed = cost - bucket.tokens
                retry_after = needed / config.tokens_per_second if config.tokens_per_second > 0 else 0.0
                bucket.total_denied += 1
                return RateLimitResult(
                    allowed=False,
                    remaining_tokens=bucket.tokens,
                    retry_after_seconds=retry_after,
                    limit_name=limit_name,
                    key=key,
                )

    def retry_after(self, limit_name: str, key: str, *, cost: float = 1.0) -> float:
        """Get seconds until the next request would be allowed."""
        result = self.check(limit_name, key, cost=cost)
        if result.allowed:
            return 0.0
        return result.retry_after_seconds

    def reset_key(self, limit_name: str, key: str) -> bool:
        """Reset a specific key's bucket to full."""
        with self._lock:
            config = self._configs.get(limit_name)
            if config is None:
                return False
            buckets = self._buckets.get(limit_name, {})
            if key not in buckets:
                return False
            buckets[key] = BucketState(
                tokens=float(config.bucket_size),
                last_refill=time.monotonic(),
            )
            return True

    def remaining(self, limit_name: str, key: str) -> float:
        """Get remaining tokens for a key."""
        with self._lock:
            config = self._configs.get(limit_name)
            if config is None:
                return 0.0
            buckets = self._buckets.get(limit_name, {})
            bucket = buckets.get(key)
            if bucket is None:
                return float(config.bucket_size)
            now = time.monotonic()
            self._refill(bucket, config, now)
            return bucket.tokens

    # =========================================================================
    # Statistics
    # =========================================================================

    def get_stats(self) -> LimiterStats:
        """Get rate limiter statistics."""
        total_keys = 0
        total_allowed = 0
        total_denied = 0
        with self._lock:
            for buckets in self._buckets.values():
                total_keys += len(buckets)
                for bucket in buckets.values():
                    total_allowed += bucket.total_allowed
                    total_denied += bucket.total_denied
        return LimiterStats(
            configured_limits=len(self._configs),
            total_keys=total_keys,
            total_allowed=total_allowed,
            total_denied=total_denied,
        )

    # =========================================================================
    # State
    # =========================================================================

    @property
    def limit_count(self) -> int:
        return len(self._configs)

    def clear(self) -> None:
        """Clear all configurations and buckets."""
        with self._lock:
            self._configs.clear()
            self._buckets.clear()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "limit_count": self.limit_count,
            "stats": self.get_stats().to_dict(),
        }


# =============================================================================
# Global Instance
# =============================================================================

_limiter: Optional[RateLimiter] = None
_limiter_lock = threading.Lock()


def get_rate_limiter() -> RateLimiter:
    """Get or create the global rate limiter."""
    global _limiter
    if _limiter is None:
        with _limiter_lock:
            if _limiter is None:
                _limiter = RateLimiter()
    return _limiter


def reset_rate_limiter() -> None:
    """Reset the global rate limiter (for testing)."""
    global _limiter
    _limiter = None
