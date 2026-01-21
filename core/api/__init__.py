"""
API Module - Rate Limiting and API Management

NEXUS V8.4.5 - Bug Fixes Phase

Provides:
- APIRateLimiter: Token bucket rate limiter for API calls
- Prevents 429 Too Many Requests errors in PARALLEL mode
"""

from .rate_limiter import APIRateLimiter, RateLimitExceeded

__all__ = ["APIRateLimiter", "RateLimitExceeded"]
