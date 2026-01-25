"""
V12.3 SCALE-OUT - Distributed Lock Tests

Tests:
- Lock acquire/release
- No-op mode (when Redis unavailable)
- Context manager usage
- Owner verification
- TTL behavior

Author: Claude (NEXUS V12.3 SCALE-OUT)
Date: 2025-12-16
"""

import asyncio
import pytest
from unittest.mock import AsyncMock

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.workflow import (
    DistributedLock,
    LockAcquisitionError,
    acquire_workflow_lock,
    try_acquire_workflow_lock,
)
from typing import Any


class TestDistributedLockNoOp:
    """Tests for no-op mode (when Redis is None)."""

    @pytest.mark.asyncio
    async def test_acquire_without_redis(self) -> None:
        """Test lock acquisition without Redis (no-op)."""
        lock = DistributedLock(redis=None, resource="test:123")

        acquired = await lock.acquire()

        assert acquired == True
        assert lock.is_acquired == True

    @pytest.mark.asyncio
    async def test_release_without_redis(self) -> None:
        """Test lock release without Redis."""
        lock = DistributedLock(redis=None, resource="test:456")
        await lock.acquire()

        released = await lock.release()

        assert released == True
        assert lock.is_acquired == False

    @pytest.mark.asyncio
    async def test_context_manager_without_redis(self) -> None:
        """Test async context manager without Redis."""
        async with DistributedLock(redis=None, resource="ctx:test") as lock:
            assert lock.is_acquired == True

        assert lock.is_acquired == False

    @pytest.mark.asyncio
    async def test_multiple_locks_without_redis(self) -> None:
        """Test multiple locks can be acquired without Redis."""
        lock1 = DistributedLock(redis=None, resource="multi:1")
        lock2 = DistributedLock(redis=None, resource="multi:1")  # Same resource

        assert await lock1.acquire() == True
        assert await lock2.acquire() == True  # No conflict in no-op mode


class TestDistributedLockWithMockRedis:
    """Tests with mocked Redis."""

    @pytest.fixture
    def mock_redis(self) -> Any:
        """Create a mock Redis client."""
        redis = AsyncMock()
        redis.set = AsyncMock(return_value=True)
        redis.eval = AsyncMock(return_value=1)
        return redis

    @pytest.mark.asyncio
    async def test_acquire_success(self, mock_redis):
        """Test successful lock acquisition with Redis."""
        lock = DistributedLock(mock_redis, "test:acquire", ttl=30)

        acquired = await lock.acquire()

        assert acquired == True
        assert lock.is_acquired == True
        mock_redis.set.assert_called_once()
        call_kwargs = mock_redis.set.call_args.kwargs
        assert call_kwargs["nx"] == True
        assert call_kwargs["ex"] == 30

    @pytest.mark.asyncio
    async def test_acquire_failure(self, mock_redis):
        """Test lock acquisition failure (already held)."""
        mock_redis.set = AsyncMock(return_value=None)  # Key exists

        lock = DistributedLock(mock_redis, "test:conflict")

        acquired = await lock.acquire()

        assert acquired == False
        assert lock.is_acquired == False

    @pytest.mark.asyncio
    async def test_release_success(self, mock_redis):
        """Test successful lock release."""
        lock = DistributedLock(mock_redis, "test:release")
        await lock.acquire()

        released = await lock.release()

        assert released == True
        assert lock.is_acquired == False
        mock_redis.eval.assert_called_once()

    @pytest.mark.asyncio
    async def test_release_not_acquired(self, mock_redis):
        """Test release without prior acquisition."""
        lock = DistributedLock(mock_redis, "test:no-acquire")

        released = await lock.release()

        assert released == False
        mock_redis.eval.assert_not_called()

    @pytest.mark.asyncio
    async def test_release_wrong_owner(self, mock_redis):
        """Test release fails if not owner."""
        mock_redis.eval = AsyncMock(return_value=0)  # Not owner

        lock = DistributedLock(mock_redis, "test:wrong-owner")
        await lock.acquire()

        released = await lock.release()

        assert released == False

    @pytest.mark.asyncio
    async def test_extend_success(self, mock_redis):
        """Test TTL extension."""
        lock = DistributedLock(mock_redis, "test:extend", ttl=30)
        await lock.acquire()

        extended = await lock.extend(additional_ttl=60)

        assert extended == True
        mock_redis.eval.assert_called()

    @pytest.mark.asyncio
    async def test_extend_not_acquired(self, mock_redis):
        """Test extend without acquisition."""
        lock = DistributedLock(mock_redis, "test:no-extend")

        extended = await lock.extend()

        assert extended == False

    @pytest.mark.asyncio
    async def test_context_manager_success(self, mock_redis):
        """Test context manager with Redis."""
        async with DistributedLock(mock_redis, "ctx:redis") as lock:
            assert lock.is_acquired == True

        assert lock.is_acquired == False
        mock_redis.eval.assert_called()  # Release was called

    @pytest.mark.asyncio
    async def test_context_manager_acquisition_failure(self, mock_redis):
        """Test context manager raises on acquisition failure."""
        mock_redis.set = AsyncMock(return_value=None)

        with pytest.raises(LockAcquisitionError):
            async with DistributedLock(mock_redis, "ctx:fail"):
                pass


class TestDistributedLockKey:
    """Tests for lock key generation."""

    def test_key_format(self):
        """Test lock key follows expected format."""
        lock = DistributedLock(redis=None, resource="workflow:abc123")
        assert lock.key == "lock:workflow:abc123"

    def test_key_prefix(self):
        """Test KEY_PREFIX constant."""
        assert DistributedLock.KEY_PREFIX == "lock"


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    @pytest.mark.asyncio
    async def test_acquire_workflow_lock_success(self):
        """Test acquire_workflow_lock convenience function."""
        lock = await acquire_workflow_lock(redis=None, workflow_id="wf-123", ttl=30)

        assert lock is not None
        assert lock.is_acquired == True
        assert "workflow:wf-123" in lock.key

    @pytest.mark.asyncio
    async def test_acquire_workflow_lock_failure(self):
        """Test acquire_workflow_lock raises on failure."""
        mock_redis = AsyncMock()
        mock_redis.set = AsyncMock(return_value=None)

        with pytest.raises(LockAcquisitionError) as exc_info:
            await acquire_workflow_lock(mock_redis, "wf-fail")

        assert "already being processed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_try_acquire_workflow_lock_success(self):
        """Test try_acquire_workflow_lock returns lock on success."""
        lock = await try_acquire_workflow_lock(redis=None, workflow_id="wf-try")

        assert lock is not None
        assert lock.is_acquired == True

    @pytest.mark.asyncio
    async def test_try_acquire_workflow_lock_failure(self):
        """Test try_acquire_workflow_lock returns None on failure."""
        mock_redis = AsyncMock()
        mock_redis.set = AsyncMock(return_value=None)

        lock = await try_acquire_workflow_lock(mock_redis, "wf-try-fail")

        assert lock is None


class TestGracefulDegradation:
    """Tests for graceful degradation on Redis errors."""

    @pytest.mark.asyncio
    async def test_acquire_on_redis_error(self):
        """Test acquisition succeeds on Redis error (degradation)."""
        mock_redis = AsyncMock()
        mock_redis.set = AsyncMock(side_effect=Exception("Connection refused"))

        lock = DistributedLock(mock_redis, "error:acquire")
        acquired = await lock.acquire()

        # Should succeed despite error (graceful degradation)
        assert acquired == True
        assert lock.is_acquired == True

    @pytest.mark.asyncio
    async def test_release_on_redis_error(self):
        """Test release handles Redis error gracefully."""
        mock_redis = AsyncMock()
        mock_redis.set = AsyncMock(return_value=True)
        mock_redis.eval = AsyncMock(side_effect=Exception("Connection lost"))

        lock = DistributedLock(mock_redis, "error:release")
        await lock.acquire()

        released = await lock.release()

        # Should handle error gracefully
        assert released == False
        assert lock.is_acquired == False

    @pytest.mark.asyncio
    async def test_extend_on_redis_error(self):
        """Test extend handles Redis error gracefully."""
        mock_redis = AsyncMock()
        mock_redis.set = AsyncMock(return_value=True)
        mock_redis.eval = AsyncMock(side_effect=Exception("Timeout"))

        lock = DistributedLock(mock_redis, "error:extend")
        await lock.acquire()

        extended = await lock.extend()

        assert extended == False


class TestLockOwnership:
    """Tests for lock ownership verification."""

    def test_custom_owner_id(self):
        """Test custom owner ID is used."""
        lock = DistributedLock(
            redis=None,
            resource="owner:test",
            owner_id="my-custom-id",
        )
        assert lock._owner_id == "my-custom-id"

    def test_auto_generated_owner_id(self):
        """Test owner ID is auto-generated when not provided."""
        lock = DistributedLock(redis=None, resource="owner:auto")
        assert lock._owner_id is not None
        assert len(lock._owner_id) > 0

    def test_different_instances_different_owners(self):
        """Test different lock instances have different owner IDs."""
        lock1 = DistributedLock(redis=None, resource="owner:diff")
        lock2 = DistributedLock(redis=None, resource="owner:diff")
        assert lock1._owner_id != lock2._owner_id


class TestDefaultTTL:
    """Tests for TTL settings."""

    def test_default_ttl(self):
        """Test DEFAULT_TTL constant."""
        assert DistributedLock.DEFAULT_TTL == 30

    def test_custom_ttl(self):
        """Test custom TTL is used."""
        lock = DistributedLock(redis=None, resource="ttl:test", ttl=60)
        assert lock._ttl == 60


class TestSecurityValidation:
    """Security tests for input validation."""

    @pytest.fixture
    def mock_redis(self):
        """Create a mock Redis client."""
        redis = AsyncMock()
        redis.set = AsyncMock(return_value=True)
        redis.eval = AsyncMock(return_value=1)
        return redis

    def test_valid_resource_characters(self):
        """Test that valid resource characters are accepted."""
        # Alphanumeric, underscore, hyphen, colon, dot
        valid_resources = [
            "workflow:abc123",
            "workflow-123",
            "workflow_123",
            "workflow.123",
            "WORKFLOW:ABC",
            "workflow123",
        ]
        for resource in valid_resources:
            lock = DistributedLock(redis=None, resource=resource, ttl=30)
            assert lock._resource == resource

    def test_invalid_resource_characters(self):
        """Test that invalid resource characters are rejected."""
        invalid_resources = [
            "workflow;abc",  # Semicolon
            "workflow abc",  # Space
            "workflow\nabc",  # Newline
            "workflow\tabc",  # Tab
            "workflow'abc",  # Quote
            'workflow"abc',  # Double quote
            "workflow`abc",  # Backtick
            "workflow$abc",  # Dollar sign
            "workflow&abc",  # Ampersand
            "workflow|abc",  # Pipe
            "workflow(abc",  # Parentheses
            "workflow[abc",  # Brackets
            "",  # Empty string
            " ",  # Just space
        ]
        for resource in invalid_resources:
            with pytest.raises(ValueError) as exc_info:
                DistributedLock(redis=None, resource=resource, ttl=30)
            assert "Invalid resource name" in str(exc_info.value)

    def test_invalid_resource_types(self):
        """Test that non-string resource types are rejected."""
        invalid_types = [None, 123, [], {}, True, b"workflow"]
        for resource in invalid_types:
            with pytest.raises(ValueError) as exc_info:
                DistributedLock(redis=None, resource=resource, ttl=30)  # type: ignore
            assert "Invalid resource name" in str(exc_info.value)

    def test_resource_length_limit(self):
        """Test that overly long resource names are rejected."""
        long_resource = "a" * 201  # Over 200 char limit
        with pytest.raises(ValueError) as exc_info:
            DistributedLock(redis=None, resource=long_resource, ttl=30)
        assert "Invalid resource name" in str(exc_info.value)

    def test_valid_ttl_range(self):
        """Test that valid TTL values are accepted."""
        valid_ttls = [1, 30, 60, 300, 3600, 86400]  # MIN to MAX
        for ttl in valid_ttls:
            lock = DistributedLock(redis=None, resource="test:ttl", ttl=ttl)
            assert lock._ttl == ttl

    def test_ttl_too_small(self):
        """Test that TTL below minimum is rejected."""
        with pytest.raises(ValueError) as exc_info:
            DistributedLock(redis=None, resource="test:ttl", ttl=0)
        assert "Invalid TTL" in str(exc_info.value)
        assert "between 1 and 86400" in str(exc_info.value)

    def test_ttl_too_large(self):
        """Test that TTL above maximum is rejected."""
        with pytest.raises(ValueError) as exc_info:
            DistributedLock(redis=None, resource="test:ttl", ttl=86401)  # MAX + 1
        assert "Invalid TTL" in str(exc_info.value)
        assert "between 1 and 86400" in str(exc_info.value)

    def test_ttl_negative(self):
        """Test that negative TTL is rejected."""
        with pytest.raises(ValueError) as exc_info:
            DistributedLock(redis=None, resource="test:ttl", ttl=-1)
        assert "Invalid TTL" in str(exc_info.value)

    def test_ttl_non_integer(self):
        """Test that non-integer TTL is rejected."""
        invalid_ttls = ["30", 30.5, None, [], {}]
        for ttl in invalid_ttls:
            with pytest.raises(ValueError) as exc_info:
                DistributedLock(redis=None, resource="test:ttl", ttl=ttl)  # type: ignore
            assert "Invalid TTL" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_extend_with_invalid_ttl(self, mock_redis):
        """Test that extend with invalid TTL is rejected."""
        lock = DistributedLock(mock_redis, "test:extend")
        await lock.acquire()

        # Try to extend with invalid TTL
        result = await lock.extend(additional_ttl=86401)
        assert result == False

    @pytest.mark.asyncio
    async def test_extend_edge_cases(self, mock_redis):
        """Test extend with edge case TTL values."""
        lock = DistributedLock(mock_redis, "test:extend-edge")
        await lock.acquire()

        # Valid minimum
        result = await lock.extend(additional_ttl=1)
        assert result == True

        # Valid maximum
        result = await lock.extend(additional_ttl=86400)
        assert result == True

    def test_security_constants(self):
        """Test that security constants are properly set."""
        assert DistributedLock._validate_ttl(1) == True  # MIN_TTL
        assert DistributedLock._validate_ttl(86400) == True  # MAX_TTL
        assert DistributedLock._validate_ttl(0) == False
        assert DistributedLock._validate_ttl(86401) == False

        # Test resource pattern validation function
        valid_func = DistributedLock._validate_resource("workflow:test")
        assert valid_func == True

        invalid_func = DistributedLock._validate_resource("workflow test")
        assert invalid_func == False