"""
Tests for API Rate Limiter (V9.0)

Tests the token bucket rate limiter implementation used for API call
throttling in PARALLEL mode and other concurrent scenarios.
"""
import pytest
import asyncio
import time
import threading
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.api.rate_limiter import (
    APIRateLimiter,
    RateLimitExceeded,
    RateLimitConfig,
    RateLimiterRegistry,
    get_rate_limiter,
    get_rate_limiter_registry,
    DEFAULT_LIMITS,
)


# =============================================================================
# Test RateLimitConfig
# =============================================================================

class TestRateLimitConfig:
    """Tests for RateLimitConfig dataclass."""

    def test_default_values(self):
        """Test default configuration values."""
        config = RateLimitConfig()
        assert config.requests_per_minute == 60
        assert config.burst_size == 10
        assert config.retry_after_seconds == 1.0

    def test_custom_values(self):
        """Test custom configuration values."""
        config = RateLimitConfig(
            requests_per_minute=100,
            burst_size=20,
            retry_after_seconds=0.5
        )
        assert config.requests_per_minute == 100
        assert config.burst_size == 20
        assert config.retry_after_seconds == 0.5


class TestDefaultLimits:
    """Tests for DEFAULT_LIMITS dictionary."""

    def test_gemini_limits_exist(self):
        """Test Gemini provider has configured limits."""
        assert "gemini" in DEFAULT_LIMITS
        assert DEFAULT_LIMITS["gemini"].requests_per_minute == 60
        assert DEFAULT_LIMITS["gemini"].burst_size == 10

    def test_claude_limits_exist(self):
        """Test Claude provider has configured limits."""
        assert "claude" in DEFAULT_LIMITS
        assert DEFAULT_LIMITS["claude"].requests_per_minute == 50
        assert DEFAULT_LIMITS["claude"].burst_size == 8

    def test_default_limits_exist(self):
        """Test default fallback limits exist."""
        assert "default" in DEFAULT_LIMITS
        assert DEFAULT_LIMITS["default"].requests_per_minute == 30


# =============================================================================
# Test APIRateLimiter - Basic Operations
# =============================================================================

class TestAPIRateLimiterBasic:
    """Tests for APIRateLimiter basic operations."""

    def test_initialization(self):
        """Test rate limiter initialization."""
        limiter = APIRateLimiter(
            requests_per_minute=60,
            burst_size=10,
            provider="test"
        )
        assert limiter.rpm == 60
        assert limiter.burst == 10
        assert limiter.provider == "test"

    def test_initial_stats(self):
        """Test initial statistics are zero."""
        limiter = APIRateLimiter()
        stats = limiter.get_stats()
        assert stats["total_requests"] == 0
        assert stats["total_waits"] == 0
        assert stats["total_wait_time"] == 0.0
        assert stats["current_bucket_size"] == 0

    def test_try_acquire_success(self):
        """Test successful token acquisition."""
        limiter = APIRateLimiter(requests_per_minute=60, burst_size=10)
        # Should be able to acquire burst_size tokens immediately
        for i in range(10):
            assert limiter._try_acquire() is True

    def test_try_acquire_exceeds_burst(self):
        """Test acquisition fails when burst exceeded."""
        limiter = APIRateLimiter(requests_per_minute=60, burst_size=5)
        # Acquire all burst tokens
        for _ in range(5):
            limiter._try_acquire()
        # Next should fail
        assert limiter._try_acquire() is False

    def test_stats_after_requests(self):
        """Test statistics update after requests."""
        limiter = APIRateLimiter(requests_per_minute=60, burst_size=10)
        for _ in range(5):
            limiter._try_acquire()

        stats = limiter.get_stats()
        assert stats["total_requests"] == 5
        assert stats["current_bucket_size"] == 5

    def test_reset(self):
        """Test reset clears state and statistics."""
        limiter = APIRateLimiter(requests_per_minute=60, burst_size=10)
        for _ in range(5):
            limiter._try_acquire()

        limiter.reset()
        stats = limiter.get_stats()
        assert stats["total_requests"] == 0
        assert stats["total_waits"] == 0
        assert stats["current_bucket_size"] == 0


# =============================================================================
# Test APIRateLimiter - Sync Operations
# =============================================================================

class TestAPIRateLimiterSync:
    """Tests for synchronous rate limiting."""

    def test_acquire_sync_immediate(self):
        """Test immediate sync acquisition."""
        limiter = APIRateLimiter(requests_per_minute=60, burst_size=10)
        # Should not raise
        limiter.acquire_sync(timeout=1.0)
        assert limiter.get_stats()["total_requests"] == 1

    def test_acquire_sync_timeout(self):
        """Test sync acquisition timeout."""
        limiter = APIRateLimiter(requests_per_minute=60, burst_size=2)
        # Fill the bucket
        limiter.acquire_sync(timeout=1.0)
        limiter.acquire_sync(timeout=1.0)

        # Next should timeout quickly
        with pytest.raises(RateLimitExceeded) as exc_info:
            limiter.acquire_sync(timeout=0.1)

        assert "Rate limit exceeded" in str(exc_info.value)
        assert limiter.provider in str(exc_info.value)

    def test_acquire_sync_multiple_fast(self):
        """Test multiple fast sync acquisitions within burst."""
        limiter = APIRateLimiter(requests_per_minute=1000, burst_size=20)
        for _ in range(10):
            limiter.acquire_sync(timeout=1.0)

        stats = limiter.get_stats()
        assert stats["total_requests"] == 10


# =============================================================================
# Test APIRateLimiter - Async Operations
# =============================================================================

class TestAPIRateLimiterAsync:
    """Tests for asynchronous rate limiting."""

    @pytest.mark.asyncio
    async def test_acquire_async_immediate(self):
        """Test immediate async acquisition."""
        limiter = APIRateLimiter(requests_per_minute=60, burst_size=10)
        await limiter.acquire_async(timeout=1.0)
        assert limiter.get_stats()["total_requests"] == 1

    @pytest.mark.asyncio
    async def test_acquire_async_timeout(self):
        """Test async acquisition timeout."""
        limiter = APIRateLimiter(requests_per_minute=60, burst_size=2)
        # Fill the bucket
        await limiter.acquire_async(timeout=1.0)
        await limiter.acquire_async(timeout=1.0)

        # Next should timeout quickly
        with pytest.raises(RateLimitExceeded):
            await limiter.acquire_async(timeout=0.1)

    @pytest.mark.asyncio
    async def test_acquire_async_multiple_concurrent(self):
        """Test multiple concurrent async acquisitions."""
        limiter = APIRateLimiter(requests_per_minute=1000, burst_size=20)

        async def acquire():
            await limiter.acquire_async(timeout=1.0)

        # Run 10 concurrent acquisitions
        await asyncio.gather(*[acquire() for _ in range(10)])

        stats = limiter.get_stats()
        assert stats["total_requests"] == 10


# =============================================================================
# Test Token Bucket Algorithm
# =============================================================================

class TestTokenBucket:
    """Tests for token bucket algorithm behavior."""

    def test_tokens_expire_after_60_seconds(self):
        """Test tokens are removed after 60 seconds."""
        limiter = APIRateLimiter(requests_per_minute=60, burst_size=5)

        # Fill bucket
        for _ in range(5):
            limiter._try_acquire()

        # Verify bucket is full
        assert len(limiter._tokens) == 5

        # Manually age all tokens by modifying timestamps
        current_time = time.time()
        limiter._tokens.clear()
        for _ in range(5):
            # Add tokens that are 61 seconds old
            limiter._tokens.append(current_time - 61)

        # Refill should clear old tokens
        available = limiter._refill_tokens()

        # Bucket should be cleared (tokens expired)
        assert len(limiter._tokens) == 0
        # All burst capacity should be available
        assert available == limiter.burst

    def test_time_until_available_empty_bucket(self):
        """Test time calculation with empty bucket."""
        limiter = APIRateLimiter(requests_per_minute=60, burst_size=10)
        assert limiter._time_until_available() == 0.0

    def test_time_until_available_full_bucket(self):
        """Test time calculation with full bucket."""
        limiter = APIRateLimiter(requests_per_minute=60, burst_size=5)
        for _ in range(5):
            limiter._try_acquire()

        wait_time = limiter._time_until_available()
        # Should be close to 60 seconds (oldest token just added)
        assert 0 < wait_time <= 60.0


# =============================================================================
# Test RateLimiterRegistry
# =============================================================================

class TestRateLimiterRegistry:
    """Tests for RateLimiterRegistry singleton."""

    def test_singleton_pattern(self):
        """Test registry is a singleton."""
        reg1 = RateLimiterRegistry()
        reg2 = RateLimiterRegistry()
        assert reg1 is reg2

    def test_get_limiter_creates_new(self):
        """Test get_limiter creates new limiter for unknown provider."""
        # Use fresh registry by clearing internal state
        registry = get_rate_limiter_registry()
        registry._limiters.clear()

        limiter = registry.get_limiter("test_provider")
        assert limiter is not None
        assert limiter.provider == "test_provider"

    def test_get_limiter_returns_cached(self):
        """Test get_limiter returns same instance for same provider."""
        registry = get_rate_limiter_registry()
        registry._limiters.clear()

        limiter1 = registry.get_limiter("cached_test")
        limiter2 = registry.get_limiter("cached_test")
        assert limiter1 is limiter2

    def test_get_limiter_uses_default_config(self):
        """Test unknown provider uses default config."""
        registry = get_rate_limiter_registry()
        registry._limiters.clear()

        limiter = registry.get_limiter("unknown_provider")
        default_config = DEFAULT_LIMITS["default"]
        assert limiter.rpm == default_config.requests_per_minute
        assert limiter.burst == default_config.burst_size

    def test_get_limiter_uses_provider_config(self):
        """Test known provider uses its specific config."""
        registry = get_rate_limiter_registry()
        registry._limiters.clear()

        limiter = registry.get_limiter("gemini")
        gemini_config = DEFAULT_LIMITS["gemini"]
        assert limiter.rpm == gemini_config.requests_per_minute
        assert limiter.burst == gemini_config.burst_size

    def test_get_all_stats(self):
        """Test get_all_stats returns stats for all providers."""
        registry = get_rate_limiter_registry()
        registry._limiters.clear()

        # Create some limiters
        registry.get_limiter("provider_a")
        registry.get_limiter("provider_b")

        stats = registry.get_all_stats()
        assert "provider_a" in stats
        assert "provider_b" in stats

    def test_reset_all(self):
        """Test reset_all clears all limiters."""
        registry = get_rate_limiter_registry()
        registry._limiters.clear()

        # Create and use limiters
        limiter_a = registry.get_limiter("reset_test_a")
        limiter_b = registry.get_limiter("reset_test_b")
        limiter_a._try_acquire()
        limiter_b._try_acquire()

        registry.reset_all()

        assert limiter_a.get_stats()["total_requests"] == 0
        assert limiter_b.get_stats()["total_requests"] == 0


# =============================================================================
# Test Convenience Functions
# =============================================================================

class TestConvenienceFunctions:
    """Tests for module-level convenience functions."""

    def test_get_rate_limiter_registry(self):
        """Test get_rate_limiter_registry returns singleton."""
        reg = get_rate_limiter_registry()
        assert isinstance(reg, RateLimiterRegistry)

    def test_get_rate_limiter(self):
        """Test get_rate_limiter returns limiter for provider."""
        limiter = get_rate_limiter("convenience_test")
        assert isinstance(limiter, APIRateLimiter)
        assert limiter.provider == "convenience_test"


# =============================================================================
# Test Thread Safety
# =============================================================================

class TestThreadSafety:
    """Tests for thread safety of rate limiter."""

    def test_concurrent_sync_access(self):
        """Test concurrent access from multiple threads."""
        limiter = APIRateLimiter(requests_per_minute=1000, burst_size=50)
        results = []
        errors = []

        def worker():
            try:
                limiter.acquire_sync(timeout=5.0)
                results.append(True)
            except RateLimitExceeded:
                results.append(False)
            except Exception as e:
                errors.append(str(e))

        # Start 20 threads
        threads = [threading.Thread(target=worker) for _ in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # No errors should occur
        assert len(errors) == 0
        # All should succeed (within burst)
        assert sum(results) == 20

    def test_registry_thread_safe(self):
        """Test registry is thread-safe."""
        registry = get_rate_limiter_registry()
        registry._limiters.clear()
        errors = []

        def worker(provider_id):
            try:
                limiter = registry.get_limiter(f"thread_test_{provider_id}")
                limiter._try_acquire()
            except Exception as e:
                errors.append(str(e))

        # Start threads with same and different providers
        threads = []
        for i in range(10):
            threads.append(threading.Thread(target=worker, args=(i % 3,)))
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0


# =============================================================================
# Test Edge Cases
# =============================================================================

class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_zero_burst_size(self):
        """Test behavior with minimal burst size."""
        limiter = APIRateLimiter(requests_per_minute=60, burst_size=1)
        assert limiter._try_acquire() is True
        assert limiter._try_acquire() is False

    def test_very_high_rpm(self):
        """Test with very high RPM."""
        limiter = APIRateLimiter(requests_per_minute=10000, burst_size=100)
        # Token interval should be small
        assert limiter._token_interval < 0.01

    def test_stats_provider_name(self):
        """Test stats include provider name."""
        limiter = APIRateLimiter(provider="my_custom_provider")
        stats = limiter.get_stats()
        assert stats["provider"] == "my_custom_provider"

    def test_exception_message_format(self):
        """Test RateLimitExceeded message format."""
        limiter = APIRateLimiter(
            requests_per_minute=60,
            burst_size=1,
            provider="test_provider"
        )
        limiter._try_acquire()

        with pytest.raises(RateLimitExceeded) as exc_info:
            limiter.acquire_sync(timeout=0.05)

        error_msg = str(exc_info.value)
        assert "test_provider" in error_msg
        assert "timeout" in error_msg.lower()


# =============================================================================
# Run Tests
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
