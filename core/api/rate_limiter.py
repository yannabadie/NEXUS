"""
BACKWARD COMPATIBILITY RE-EXPORT

All API rate limiting functionality has been consolidated into:
  core/resilience/unified_rate_limiter.py

This file re-exports APIRateLimiter for backward compatibility.

DEPRECATED: This file will be removed in V13.0. Update imports to:
  from core.resilience.unified_rate_limiter import APIRateLimiter

Sprint 1 Consolidation: Eliminated 384 lines of duplicate token bucket code.
"""

from core.resilience.unified_rate_limiter import (
    APIRateLimiter,
    APIRateLimiterRegistry as RateLimiterRegistry,
    get_api_rate_limiter_registry as get_rate_limiter_registry,
    get_api_rate_limiter as get_rate_limiter,
    RateLimitExceeded,
    APIRateLimitConfig as RateLimitConfig,
    DEFAULT_API_LIMITS as DEFAULT_LIMITS,
)

__all__ = [
    "APIRateLimiter",
    "RateLimiterRegistry",
    "get_rate_limiter_registry",
    "get_rate_limiter",
    "RateLimitExceeded",
    "RateLimitConfig",
    "DEFAULT_LIMITS",
]
