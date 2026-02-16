"""
Per-Provider Rate Limiter - Token bucket rate limiting for API providers.

V12.4 COGNITIVE BOOST - Task #38

Prevents API rate limit errors by enforcing local request throttling
before calls are made. Uses the token bucket algorithm with per-provider
configurable RPM (requests per minute) and TPM (tokens per minute) limits.

Usage:
    from core.resilience.rate_limiter import RateLimiter, ProviderLimits

    limiter = RateLimiter()
    limiter.configure("gemini", ProviderLimits(rpm=60, tpm=1_000_000))
    limiter.configure("claude", ProviderLimits(rpm=50, tpm=400_000))

    # Before making an API call:
    if limiter.acquire("gemini"):
        # OK to proceed
        pass
    else:
        wait_time = limiter.retry_after("gemini")

    # After the call, record token usage:
    limiter.record_tokens("gemini", input_tokens=500, output_tokens=200)
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from threading import Lock
from typing import Any, Dict, List, Optional

_logger = logging.getLogger(__name__)


# =============================================================================
# Configuration
# =============================================================================

@dataclass
class ProviderLimits:
    """Rate limits for an API provider."""
    rpm: int = 60  # Requests per minute
    tpm: int = 1_000_000  # Tokens per minute
    max_burst: int = 0  # Max burst above RPM (0 = no burst)

    def __post_init__(self):
        if self.max_burst == 0:
            self.max_burst = max(1, self.rpm // 5)


# Default limits per provider
DEFAULT_LIMITS: Dict[str, ProviderLimits] = {
    "gemini": ProviderLimits(rpm=60, tpm=1_000_000),
    "claude": ProviderLimits(rpm=50, tpm=400_000),
    "ollama": ProviderLimits(rpm=120, tpm=10_000_000),  # Local = generous
}


# =============================================================================
# Token Bucket
# =============================================================================

class TokenBucket:
    """
    Token bucket rate limiter.

    Tokens are added at a constant rate up to max_tokens.
    Each request consumes one token. If no tokens are available,
    the request must wait.
    """

    def __init__(self, rate: float, max_tokens: int):
        """
        Initialize token bucket.

        Args:
            rate: Tokens added per second
            max_tokens: Maximum tokens in bucket
        """
        self.rate = rate
        self.max_tokens = max_tokens
        self._tokens = float(max_tokens)
        self._last_refill = time.monotonic()
        self._lock = Lock()

    def acquire(self, tokens: int = 1) -> bool:
        """
        Try to acquire tokens from the bucket.

        Args:
            tokens: Number of tokens to acquire

        Returns:
            True if tokens acquired, False if bucket empty
        """
        with self._lock:
            self._refill()
            if self._tokens >= tokens:
                self._tokens -= tokens
                return True
            return False

    def wait_time(self) -> float:
        """
        Calculate time to wait until a token is available.

        Returns:
            Seconds to wait (0 if tokens available)
        """
        with self._lock:
            self._refill()
            if self._tokens >= 1:
                return 0.0
            deficit = 1.0 - self._tokens
            return deficit / self.rate if self.rate > 0 else float("inf")

    @property
    def available(self) -> float:
        """Current available tokens."""
        with self._lock:
            self._refill()
            return self._tokens

    def _refill(self) -> None:
        """Refill tokens based on elapsed time."""
        now = time.monotonic()
        elapsed = now - self._last_refill
        self._last_refill = now
        self._tokens = min(
            self.max_tokens,
            self._tokens + elapsed * self.rate,
        )


# =============================================================================
# Provider State
# =============================================================================

@dataclass
class ProviderState:
    """Tracks rate limiting state for a single provider."""
    provider: str
    limits: ProviderLimits
    request_bucket: TokenBucket = field(init=False)
    token_bucket: TokenBucket = field(init=False)
    total_requests: int = 0
    total_tokens: int = 0
    blocked_requests: int = 0
    last_request_time: float = 0.0

    def __post_init__(self):
        # RPM -> requests per second
        rps = self.limits.rpm / 60.0
        max_burst = self.limits.rpm + self.limits.max_burst
        self.request_bucket = TokenBucket(rate=rps, max_tokens=max_burst)

        # TPM -> tokens per second
        tps = self.limits.tpm / 60.0
        self.token_bucket = TokenBucket(rate=tps, max_tokens=self.limits.tpm)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "provider": self.provider,
            "rpm_limit": self.limits.rpm,
            "tpm_limit": self.limits.tpm,
            "total_requests": self.total_requests,
            "total_tokens": self.total_tokens,
            "blocked_requests": self.blocked_requests,
            "request_tokens_available": round(self.request_bucket.available, 1),
            "token_tokens_available": round(self.token_bucket.available, 0),
        }


# =============================================================================
# Rate Limiter
# =============================================================================

class RateLimiter:
    """
    Per-provider rate limiter using token buckets.

    Enforces both RPM (requests per minute) and TPM (tokens per minute)
    limits locally before making API calls.
    """

    def __init__(self, defaults: Optional[Dict[str, ProviderLimits]] = None):
        """
        Initialize rate limiter.

        Args:
            defaults: Provider limit overrides (merged with DEFAULT_LIMITS)
        """
        self._lock = Lock()
        self._providers: Dict[str, ProviderState] = {}

        # Initialize with defaults
        limits = dict(DEFAULT_LIMITS)
        if defaults:
            limits.update(defaults)

        for provider, provider_limits in limits.items():
            self._providers[provider] = ProviderState(
                provider=provider,
                limits=provider_limits,
            )

    def configure(self, provider: str, limits: ProviderLimits) -> None:
        """
        Configure or update limits for a provider.

        Args:
            provider: Provider name
            limits: Rate limits
        """
        with self._lock:
            self._providers[provider] = ProviderState(
                provider=provider,
                limits=limits,
            )

    def acquire(self, provider: str, estimated_tokens: int = 0) -> bool:
        """
        Try to acquire permission to make an API call.

        Args:
            provider: Provider name
            estimated_tokens: Estimated token usage (for TPM check)

        Returns:
            True if allowed to proceed
        """
        with self._lock:
            state = self._providers.get(provider)
            if not state:
                return True  # Unknown provider = no limits

            # Check RPM
            if not state.request_bucket.acquire():
                state.blocked_requests += 1
                _logger.debug(f"Rate limit: {provider} RPM exceeded")
                return False

            # Check TPM (if estimated tokens provided)
            if estimated_tokens > 0:
                if not state.token_bucket.acquire(estimated_tokens):
                    # Refund the request token
                    state.request_bucket._tokens = min(
                        state.request_bucket.max_tokens,
                        state.request_bucket._tokens + 1,
                    )
                    state.blocked_requests += 1
                    _logger.debug(f"Rate limit: {provider} TPM exceeded")
                    return False

            state.total_requests += 1
            state.last_request_time = time.monotonic()
            return True

    def record_tokens(
        self,
        provider: str,
        input_tokens: int = 0,
        output_tokens: int = 0,
    ) -> None:
        """
        Record actual token usage after a call completes.

        Args:
            provider: Provider name
            input_tokens: Input tokens used
            output_tokens: Output tokens used
        """
        total = input_tokens + output_tokens
        with self._lock:
            state = self._providers.get(provider)
            if state:
                state.total_tokens += total

    def retry_after(self, provider: str) -> float:
        """
        Get recommended wait time before retrying.

        Args:
            provider: Provider name

        Returns:
            Seconds to wait (0 if no wait needed)
        """
        with self._lock:
            state = self._providers.get(provider)
            if not state:
                return 0.0
            return state.request_bucket.wait_time()

    def get_state(self, provider: str) -> Optional[Dict[str, Any]]:
        """
        Get current rate limiting state for a provider.

        Args:
            provider: Provider name

        Returns:
            State dict or None
        """
        with self._lock:
            state = self._providers.get(provider)
            return state.to_dict() if state else None

    def get_all_states(self) -> Dict[str, Dict[str, Any]]:
        """Get state for all providers."""
        with self._lock:
            return {
                name: state.to_dict()
                for name, state in self._providers.items()
            }

    def reset(self, provider: Optional[str] = None) -> None:
        """
        Reset rate limiter state.

        Args:
            provider: Specific provider to reset (None = all)
        """
        with self._lock:
            if provider:
                state = self._providers.get(provider)
                if state:
                    self._providers[provider] = ProviderState(
                        provider=provider,
                        limits=state.limits,
                    )
            else:
                for name, state in list(self._providers.items()):
                    self._providers[name] = ProviderState(
                        provider=name,
                        limits=state.limits,
                    )

    @property
    def providers(self) -> List[str]:
        """List configured providers."""
        return list(self._providers.keys())

    def to_dict(self) -> Dict[str, Any]:
        """Export limiter state."""
        states = self.get_all_states()
        total_blocked = sum(
            s.get("blocked_requests", 0) for s in states.values()
        )
        return {
            "provider_count": len(self._providers),
            "total_blocked_requests": total_blocked,
            "providers": states,
        }
