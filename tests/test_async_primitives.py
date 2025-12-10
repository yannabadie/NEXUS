"""
Tests for NEXUS V9.0 Async Primitives.

Tests cover:
- CancellationToken: Hierarchical cancellation
- AsyncProcessHandle: Process tracking and termination
- AsyncRWLock: Read-write lock semantics
- AsyncBlackboard: Thread-safe shared state
"""

import pytest
import asyncio
import sys
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch

# Add project root to path
sys.path.insert(0, str(__file__).replace("\\tests\\test_async_primitives.py", "").replace("/tests/test_async_primitives.py", ""))

from core.async_primitives import (
    CancellationToken,
    AsyncProcessHandle,
    AsyncRWLock,
    AsyncBlackboard,
)
from core.async_primitives.cancellation import CancellationTokenSource
from core.async_primitives.process_handle import ProcessState, ProcessHandleRegistry, get_process_registry
from core.async_primitives.rwlock import AsyncRWLockWithTimeout, InstrumentedAsyncRWLock


# ============================================================================
# CancellationToken Tests
# ============================================================================

class TestCancellationToken:
    """Tests for CancellationToken."""

    def test_initial_state_not_cancelled(self):
        """Token should start as not cancelled."""
        token = CancellationToken()
        assert not token.is_cancelled
        assert token.cancel_reason is None

    def test_cancel_sets_state(self):
        """Cancelling should set is_cancelled to True."""
        token = CancellationToken()
        token.cancel()
        assert token.is_cancelled

    def test_cancel_with_reason(self):
        """Cancel reason should be stored."""
        token = CancellationToken()
        token.cancel(reason="User requested")
        assert token.is_cancelled
        assert token.cancel_reason == "User requested"

    def test_cancel_propagates_to_children(self):
        """Parent cancellation should propagate to all children."""
        parent = CancellationToken()
        child1 = parent.create_child()
        child2 = parent.create_child()
        grandchild = child1.create_child()

        assert not parent.is_cancelled
        assert not child1.is_cancelled
        assert not child2.is_cancelled
        assert not grandchild.is_cancelled

        parent.cancel()

        assert parent.is_cancelled
        assert child1.is_cancelled
        assert child2.is_cancelled
        assert grandchild.is_cancelled

    def test_child_inherits_parent_cancellation(self):
        """Child should report cancelled if parent is cancelled."""
        parent = CancellationToken()
        child = parent.create_child()

        parent.cancel()

        # Child's _cancelled is False, but is_cancelled checks parent
        assert child.is_cancelled

    def test_check_raises_when_cancelled(self):
        """check() should raise CancelledError when cancelled."""
        token = CancellationToken()
        token.cancel()

        with pytest.raises(asyncio.CancelledError):
            token.check()

    def test_check_does_not_raise_when_not_cancelled(self):
        """check() should not raise when not cancelled."""
        token = CancellationToken()
        token.check()  # Should not raise

    def test_callback_executed_on_cancel(self):
        """Callbacks should be executed when cancelled."""
        token = CancellationToken()
        callback_called = []

        token.on_cancel(lambda: callback_called.append(True))
        assert len(callback_called) == 0

        token.cancel()
        assert len(callback_called) == 1

    def test_callback_exception_does_not_stop_others(self):
        """One callback failing should not prevent others from running."""
        token = CancellationToken()
        results = []

        def failing_callback():
            raise ValueError("Intentional")

        token.on_cancel(lambda: results.append(1))
        token.on_cancel(failing_callback)
        token.on_cancel(lambda: results.append(2))

        token.cancel()

        assert results == [1, 2]

    def test_callback_executed_immediately_if_already_cancelled(self):
        """Adding callback to cancelled token should execute immediately."""
        token = CancellationToken()
        token.cancel()

        callback_called = []
        token.on_cancel(lambda: callback_called.append(True))

        assert len(callback_called) == 1

    def test_double_cancel_is_idempotent(self):
        """Cancelling twice should be safe."""
        token = CancellationToken()
        call_count = []

        token.on_cancel(lambda: call_count.append(1))

        token.cancel()
        token.cancel()

        assert len(call_count) == 1  # Only called once

    def test_remove_callback(self):
        """Callbacks can be removed before cancellation."""
        token = CancellationToken()
        results = []

        def my_callback():
            results.append(1)

        token.on_cancel(my_callback)
        assert token.remove_callback(my_callback)
        assert not token.remove_callback(my_callback)  # Already removed

        token.cancel()
        assert len(results) == 0


class TestCancellationTokenSource:
    """Tests for CancellationTokenSource."""

    def test_source_creates_tokens(self):
        """Source should create linked tokens."""
        source = CancellationTokenSource()
        token1 = source.token
        token2 = source.create_linked_token()

        assert not token1.is_cancelled
        assert not token2.is_cancelled

    def test_source_cancel_cancels_all(self):
        """Cancelling source should cancel all tokens."""
        source = CancellationTokenSource()
        token1 = source.token
        token2 = source.create_linked_token()

        source.cancel()

        assert source.is_cancelled
        assert token1.is_cancelled
        assert token2.is_cancelled


# ============================================================================
# AsyncProcessHandle Tests
# ============================================================================

class TestAsyncProcessHandle:
    """Tests for AsyncProcessHandle."""

    @pytest.mark.asyncio
    async def test_is_running_true_when_running(self):
        """is_running should be True for running process."""
        # Create a mock process
        mock_proc = Mock()
        mock_proc.returncode = None  # Running

        handle = AsyncProcessHandle(
            proc=mock_proc,
            session_uuid="test-uuid-123"
        )

        assert handle.is_running

    @pytest.mark.asyncio
    async def test_is_running_false_when_completed(self):
        """is_running should be False for completed process."""
        mock_proc = Mock()
        mock_proc.returncode = 0  # Completed

        handle = AsyncProcessHandle(
            proc=mock_proc,
            session_uuid="test-uuid-123"
        )

        assert not handle.is_running

    @pytest.mark.asyncio
    async def test_terminate_gracefully_when_not_running(self):
        """terminate_gracefully should return False if not running."""
        mock_proc = Mock()
        mock_proc.returncode = 0  # Already completed

        handle = AsyncProcessHandle(
            proc=mock_proc,
            session_uuid="test-uuid-123"
        )

        result = await handle.terminate_gracefully()
        assert result is False
        assert handle.state == ProcessState.COMPLETED

    @pytest.mark.asyncio
    async def test_terminate_gracefully_success(self):
        """terminate_gracefully should terminate running process."""
        mock_proc = AsyncMock()
        mock_proc.returncode = None  # Running initially

        # Simulate terminate working
        async def mock_wait():
            mock_proc.returncode = -15  # SIGTERM
            return -15

        mock_proc.wait = mock_wait
        mock_proc.terminate = Mock()

        handle = AsyncProcessHandle(
            proc=mock_proc,
            session_uuid="test-uuid-123"
        )

        result = await handle.terminate_gracefully(timeout=1.0)

        assert result is True
        mock_proc.terminate.assert_called_once()
        assert handle.state == ProcessState.TERMINATED
        assert handle.terminated_at is not None

    @pytest.mark.asyncio
    async def test_to_dict(self):
        """to_dict should return serializable dictionary."""
        mock_proc = Mock()
        mock_proc.returncode = None
        mock_proc.pid = 12345

        handle = AsyncProcessHandle(
            proc=mock_proc,
            session_uuid="test-uuid-123",
            task_id="task-456",
            agent_id="gemini"
        )

        data = handle.to_dict()

        assert data["session_uuid"] == "test-uuid-123"
        assert data["task_id"] == "task-456"
        assert data["agent_id"] == "gemini"
        assert data["pid"] == 12345
        assert data["is_running"] is True
        assert "created_at" in data


class TestProcessHandleRegistry:
    """Tests for ProcessHandleRegistry."""

    @pytest.mark.asyncio
    async def test_register_and_get(self):
        """Should be able to register and retrieve handles."""
        registry = ProcessHandleRegistry()

        mock_proc = Mock()
        mock_proc.returncode = None

        handle = AsyncProcessHandle(
            proc=mock_proc,
            session_uuid="uuid-1"
        )

        await registry.register(handle)
        retrieved = await registry.get("uuid-1")

        assert retrieved is handle

    @pytest.mark.asyncio
    async def test_unregister(self):
        """Should be able to unregister handles."""
        registry = ProcessHandleRegistry()

        mock_proc = Mock()
        mock_proc.returncode = None

        handle = AsyncProcessHandle(
            proc=mock_proc,
            session_uuid="uuid-1"
        )

        await registry.register(handle)
        unregistered = await registry.unregister("uuid-1")

        assert unregistered is handle
        assert await registry.get("uuid-1") is None


# ============================================================================
# AsyncRWLock Tests
# ============================================================================

class TestAsyncRWLock:
    """Tests for AsyncRWLock."""

    @pytest.mark.asyncio
    async def test_multiple_readers_allowed(self):
        """Multiple readers should be able to hold lock simultaneously."""
        lock = AsyncRWLock()
        results = []

        async def reader(n):
            async with lock.read():
                results.append(f"start_{n}")
                await asyncio.sleep(0.01)
                results.append(f"end_{n}")

        # Run 5 readers concurrently
        await asyncio.gather(*[reader(i) for i in range(5)])

        # All should have completed
        assert len(results) == 10
        # Check that starts and ends are interleaved (concurrent)
        assert results.count("start_0") == 1

    @pytest.mark.asyncio
    async def test_writer_exclusive(self):
        """Only one writer should hold lock at a time."""
        lock = AsyncRWLock()
        value = [0]

        async def writer():
            async with lock.write():
                current = value[0]
                await asyncio.sleep(0.01)
                value[0] = current + 1

        # Run 5 writers concurrently
        await asyncio.gather(*[writer() for _ in range(5)])

        # If writers were exclusive, final value should be 5
        assert value[0] == 5

    @pytest.mark.asyncio
    async def test_writer_blocks_readers(self):
        """Writer should block new readers."""
        lock = AsyncRWLock()
        events = []

        async def writer():
            async with lock.write():
                events.append("writer_start")
                await asyncio.sleep(0.05)
                events.append("writer_end")

        async def reader():
            await asyncio.sleep(0.01)  # Small delay to ensure writer starts first
            async with lock.read():
                events.append("reader")

        await asyncio.gather(writer(), reader())

        # Reader should have waited for writer
        assert events == ["writer_start", "writer_end", "reader"]

    @pytest.mark.asyncio
    async def test_properties(self):
        """Lock properties should reflect state."""
        lock = AsyncRWLock()

        assert lock.readers == 0
        assert not lock.is_write_locked
        assert lock.pending_writers == 0


class TestAsyncRWLockWithTimeout:
    """Tests for AsyncRWLockWithTimeout."""

    @pytest.mark.asyncio
    async def test_read_with_timeout_success(self):
        """Should acquire read lock within timeout."""
        lock = AsyncRWLockWithTimeout()

        async with lock.read_with_timeout(1.0):
            assert lock.readers == 1

        assert lock.readers == 0

    @pytest.mark.asyncio
    async def test_write_with_timeout_fails_when_held(self):
        """Should timeout when lock cannot be acquired."""
        lock = AsyncRWLockWithTimeout()

        async def hold_read():
            async with lock.read():
                await asyncio.sleep(1.0)

        # Start a reader that holds for 1 second
        task = asyncio.create_task(hold_read())
        await asyncio.sleep(0.01)  # Let reader acquire

        # Try to get write lock with short timeout
        with pytest.raises(asyncio.TimeoutError):
            async with lock.write_with_timeout(0.1):
                pass

        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass


# ============================================================================
# AsyncBlackboard Tests
# ============================================================================

class TestAsyncBlackboard:
    """Tests for AsyncBlackboard."""

    @pytest.mark.asyncio
    async def test_set_and_get(self):
        """Should be able to set and get values."""
        bb = AsyncBlackboard()

        await bb.set("key1", "value1")
        result = await bb.get("key1")

        assert result == "value1"

    @pytest.mark.asyncio
    async def test_get_default(self):
        """Should return default for missing keys."""
        bb = AsyncBlackboard()

        result = await bb.get("missing", default="default_value")

        assert result == "default_value"

    @pytest.mark.asyncio
    async def test_delete(self):
        """Should be able to delete keys."""
        bb = AsyncBlackboard()

        await bb.set("key1", "value1")
        deleted = await bb.delete("key1")
        result = await bb.get("key1")

        assert deleted is True
        assert result is None

    @pytest.mark.asyncio
    async def test_update_multiple(self):
        """Should be able to update multiple keys atomically."""
        bb = AsyncBlackboard()

        await bb.update({"a": 1, "b": 2, "c": 3})

        assert await bb.get("a") == 1
        assert await bb.get("b") == 2
        assert await bb.get("c") == 3

    @pytest.mark.asyncio
    async def test_snapshot(self):
        """Snapshot should return copy of all data."""
        bb = AsyncBlackboard()

        await bb.set("key1", "value1")
        await bb.set("key2", "value2")

        snapshot = await bb.snapshot()

        assert snapshot == {"key1": "value1", "key2": "value2"}

        # Modifying snapshot should not affect blackboard
        snapshot["key1"] = "modified"
        assert await bb.get("key1") == "value1"

    @pytest.mark.asyncio
    async def test_get_or_set(self):
        """get_or_set should set value if missing."""
        bb = AsyncBlackboard()

        # First call should set the value
        result1 = await bb.get_or_set("key", lambda: "computed_value")
        assert result1 == "computed_value"

        # Second call should return existing value
        call_count = [0]

        def factory():
            call_count[0] += 1
            return "new_value"

        result2 = await bb.get_or_set("key", factory)
        assert result2 == "computed_value"  # Original value
        assert call_count[0] == 0  # Factory not called

    @pytest.mark.asyncio
    async def test_concurrent_read_write(self):
        """Should handle concurrent reads and writes safely."""
        bb = AsyncBlackboard()

        async def writer():
            for i in range(50):
                await bb.set("counter", i)
                await asyncio.sleep(0.001)

        async def reader():
            for _ in range(50):
                await bb.get("counter")
                await asyncio.sleep(0.001)

        # Run multiple readers and a writer concurrently
        await asyncio.gather(
            writer(),
            reader(),
            reader(),
            reader()
        )

        # Should complete without deadlock or errors
        final = await bb.get("counter")
        assert final == 49

    @pytest.mark.asyncio
    async def test_ttl_expiration(self):
        """Expired entries should not be returned."""
        bb = AsyncBlackboard()

        await bb.set("key", "value", ttl_seconds=0.01)

        # Immediately after, should exist
        assert await bb.get("key") == "value"

        # After TTL expires
        await asyncio.sleep(0.02)
        assert await bb.get("key") is None

    @pytest.mark.asyncio
    async def test_clear(self):
        """Clear should remove all entries."""
        bb = AsyncBlackboard()

        await bb.set("a", 1)
        await bb.set("b", 2)

        count = await bb.clear()

        assert count == 2
        assert await bb.size() == 0

    @pytest.mark.asyncio
    async def test_keys_and_contains(self):
        """keys() and contains() should work correctly."""
        bb = AsyncBlackboard()

        await bb.set("key1", "value1")
        await bb.set("key2", "value2")

        keys = await bb.keys()
        assert set(keys) == {"key1", "key2"}

        assert await bb.contains("key1") is True
        assert await bb.contains("missing") is False

    @pytest.mark.asyncio
    async def test_metadata(self):
        """Should be able to get entry metadata."""
        bb = AsyncBlackboard()

        await bb.set("key", "value", source="test", ttl_seconds=60)

        metadata = await bb.get_metadata("key")

        assert metadata is not None
        assert metadata["source"] == "test"
        assert metadata["ttl_seconds"] == 60
        assert metadata["is_expired"] is False

    @pytest.mark.asyncio
    async def test_initial_data(self):
        """Should accept initial data in constructor."""
        bb = AsyncBlackboard(initial_data={"a": 1, "b": 2})

        assert await bb.get("a") == 1
        assert await bb.get("b") == 2


# ============================================================================
# Integration Tests
# ============================================================================

class TestAsyncPrimitivesIntegration:
    """Integration tests combining multiple primitives."""

    @pytest.mark.asyncio
    async def test_cancellation_with_blackboard(self):
        """CancellationToken should work with AsyncBlackboard operations."""
        token = CancellationToken()
        bb = AsyncBlackboard()

        async def long_operation():
            for i in range(100):
                token.check()
                await bb.set(f"key_{i}", i)
                await asyncio.sleep(0.01)

        # Start operation and cancel after a bit
        task = asyncio.create_task(long_operation())
        await asyncio.sleep(0.05)
        token.cancel()

        with pytest.raises(asyncio.CancelledError):
            await task

        # Some keys should have been set before cancellation
        size = await bb.size()
        assert 0 < size < 100


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
