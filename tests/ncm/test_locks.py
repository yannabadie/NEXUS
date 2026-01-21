"""
Unit tests for NCM file locking system.

Tests:
- Lock acquisition and release
- Timeout mechanism
- Context manager interface
- Bulk lock acquisition
- Deadlock prevention (sorted order)
- Concurrent access scenarios
- Lock status monitoring
"""

import pytest
import asyncio
from pathlib import Path
from datetime import datetime

from core.ncm.locks import LockManager, LockTimeout


@pytest.fixture
def lock_manager():
    """Create LockManager instance for testing."""
    return LockManager(timeout=1.0)  # Short timeout for tests


@pytest.fixture
def temp_files(tmp_path):
    """Create temporary files for lock testing."""
    files = []
    for i in range(5):
        file_path = tmp_path / f"test_file_{i}.py"
        file_path.write_text(f"# Test file {i}")
        files.append(file_path)
    return files


class TestLockManagerInit:
    """Test LockManager initialization."""

    def test_init_default_timeout(self):
        """Test LockManager with default timeout."""
        manager = LockManager()
        assert manager.timeout == 300.0
        assert len(manager.locks) == 0
        assert manager.active_locks == 0

    def test_init_custom_timeout(self):
        """Test LockManager with custom timeout."""
        manager = LockManager(timeout=60.0)
        assert manager.timeout == 60.0

    def test_init_invalid_timeout(self):
        """Test LockManager with invalid timeout raises ValueError."""
        with pytest.raises(ValueError, match="timeout must be positive"):
            LockManager(timeout=0)

        with pytest.raises(ValueError, match="timeout must be positive"):
            LockManager(timeout=-10)


class TestSingleFileLock:
    """Test single file locking operations."""

    @pytest.mark.asyncio
    async def test_acquire_lock_context_manager(self, lock_manager, temp_files):
        """Test lock acquisition via context manager."""
        file_path = temp_files[0]

        async with lock_manager.acquire_lock(file_path):
            # Lock should be held
            assert lock_manager.active_locks == 1
            assert file_path.resolve() in lock_manager.lock_info

        # Lock should be released
        assert lock_manager.active_locks == 0
        assert file_path.resolve() not in lock_manager.lock_info

    @pytest.mark.asyncio
    async def test_acquire_lock_with_identifier(self, lock_manager, temp_files):
        """Test lock acquisition with acquired_by identifier."""
        file_path = temp_files[0]

        async with lock_manager.acquire_lock(file_path, acquired_by="STORY-0001"):
            info = lock_manager.lock_info[file_path.resolve()]
            assert info["acquired_by"] == "STORY-0001"
            assert isinstance(info["acquired_at"], datetime)

    @pytest.mark.asyncio
    async def test_path_normalization(self, lock_manager, temp_files):
        """Test that paths are normalized (relative and absolute treated same)."""
        file_path = temp_files[0]
        norm_path = file_path.resolve()

        async with lock_manager.acquire_lock(file_path):
            # Lock should exist for normalized path
            assert norm_path in lock_manager.lock_info

            # Another lock on same file (normalized) should wait
            with pytest.raises(LockTimeout):
                async with lock_manager.acquire_lock(norm_path):
                    pass  # Should timeout

    @pytest.mark.asyncio
    async def test_lock_timeout(self, lock_manager, temp_files):
        """Test that lock acquisition times out when file already locked."""
        file_path = temp_files[0]

        async def holder():
            """Hold lock for 2 seconds."""
            async with lock_manager.acquire_lock(file_path, acquired_by="HOLDER"):
                await asyncio.sleep(2.0)

        async def waiter():
            """Try to acquire lock (should timeout)."""
            async with lock_manager.acquire_lock(file_path, acquired_by="WAITER"):
                pass

        # Start holder
        holder_task = asyncio.create_task(holder())

        # Wait a bit to ensure holder acquires lock
        await asyncio.sleep(0.1)

        # Try to acquire (should timeout after 1 second)
        with pytest.raises(LockTimeout, match="Failed to acquire lock"):
            await waiter()

        # Cancel holder
        holder_task.cancel()
        try:
            await holder_task
        except asyncio.CancelledError:
            pass


class TestBulkLockAcquisition:
    """Test bulk lock acquisition."""

    @pytest.mark.asyncio
    async def test_acquire_multiple_locks(self, lock_manager, temp_files):
        """Test acquiring locks for multiple files."""
        files = temp_files[:3]

        locks = await lock_manager.acquire_locks(files, acquired_by="STORY-0001")

        try:
            # All locks acquired
            assert len(locks) == 3
            assert lock_manager.active_locks == 3

            # All files in lock_info
            for file_path in files:
                assert file_path.resolve() in lock_manager.lock_info

        finally:
            await lock_manager.release_locks(locks)

        # All locks released
        assert lock_manager.active_locks == 0

    @pytest.mark.asyncio
    async def test_acquire_empty_list(self, lock_manager):
        """Test acquiring locks for empty list returns empty list."""
        locks = await lock_manager.acquire_locks([])
        assert locks == []

    @pytest.mark.asyncio
    async def test_acquire_duplicate_paths(self, lock_manager, temp_files):
        """Test that duplicate paths are deduplicated."""
        file_path = temp_files[0]
        files = [file_path, file_path, file_path]  # Same file 3 times

        locks = await lock_manager.acquire_locks(files)

        try:
            # Only one lock acquired (deduplicated)
            assert len(locks) == 1
            assert lock_manager.active_locks == 1

        finally:
            await lock_manager.release_locks(locks)

    @pytest.mark.asyncio
    async def test_sorted_lock_acquisition(self, lock_manager, temp_files):
        """Test that locks are acquired in sorted order (deadlock prevention)."""
        files = [temp_files[3], temp_files[1], temp_files[4]]  # Unsorted order

        # Track lock acquisition order
        acquisition_order = []

        # Override _get_or_create_lock to track order
        original_get_or_create = lock_manager._get_or_create_lock

        def track_get_or_create(path):
            acquisition_order.append(path)
            return original_get_or_create(path)

        lock_manager._get_or_create_lock = track_get_or_create

        locks = await lock_manager.acquire_locks(files)

        try:
            # Should acquire in sorted order
            sorted_files = sorted([f.resolve() for f in files])
            assert acquisition_order == sorted_files

        finally:
            await lock_manager.release_locks(locks)
            lock_manager._get_or_create_lock = original_get_or_create

    @pytest.mark.asyncio
    async def test_bulk_timeout_releases_acquired(self, lock_manager, temp_files):
        """Test that timeout during bulk acquisition releases already-acquired locks."""
        file1 = temp_files[0]
        file2 = temp_files[1]

        # Hold lock on file2
        async def holder():
            async with lock_manager.acquire_lock(file2):
                await asyncio.sleep(3.0)

        holder_task = asyncio.create_task(holder())
        await asyncio.sleep(0.1)  # Ensure holder has lock

        # Try to acquire both files (should timeout on file2)
        with pytest.raises(LockTimeout):
            await lock_manager.acquire_locks([file1, file2])

        # No locks should be held (file1 should have been released)
        assert lock_manager.active_locks <= 1  # Only holder's lock

        # Cancel holder
        holder_task.cancel()
        try:
            await holder_task
        except asyncio.CancelledError:
            pass


class TestConcurrentAccess:
    """Test concurrent lock access scenarios."""

    @pytest.mark.asyncio
    async def test_sequential_access(self, lock_manager, temp_files):
        """Test that sequential access to same file works correctly."""
        file_path = temp_files[0]
        access_log = []

        async def accessor(name):
            async with lock_manager.acquire_lock(file_path, acquired_by=name):
                access_log.append(f"{name}_start")
                await asyncio.sleep(0.05)
                access_log.append(f"{name}_end")

        # Run accessors sequentially
        await accessor("A")
        await accessor("B")
        await accessor("C")

        # Should be fully sequential
        assert access_log == ["A_start", "A_end", "B_start", "B_end", "C_start", "C_end"]

    @pytest.mark.asyncio
    async def test_concurrent_different_files(self, lock_manager, temp_files):
        """Test concurrent access to different files works in parallel."""
        file1 = temp_files[0]
        file2 = temp_files[1]
        access_log = []

        async def accessor(file_path, name):
            async with lock_manager.acquire_lock(file_path, acquired_by=name):
                access_log.append(f"{name}_start")
                await asyncio.sleep(0.1)
                access_log.append(f"{name}_end")

        # Run accessors concurrently on different files
        await asyncio.gather(
            accessor(file1, "A"),
            accessor(file2, "B")
        )

        # Should run in parallel (starts interleaved)
        assert "A_start" in access_log
        assert "B_start" in access_log
        # Both should complete
        assert "A_end" in access_log
        assert "B_end" in access_log


class TestLockStatus:
    """Test lock status and monitoring."""

    @pytest.mark.asyncio
    async def test_get_lock_status_empty(self, lock_manager):
        """Test lock status when no locks held."""
        status = lock_manager.get_lock_status()

        assert status["total_locks"] == 0
        assert status["active_locks"] == 0
        assert status["lock_details"] == []

    @pytest.mark.asyncio
    async def test_get_lock_status_with_locks(self, lock_manager, temp_files):
        """Test lock status with active locks."""
        file1 = temp_files[0]
        file2 = temp_files[1]

        async with lock_manager.acquire_lock(file1, acquired_by="STORY-0001"):
            async with lock_manager.acquire_lock(file2, acquired_by="STORY-0002"):
                status = lock_manager.get_lock_status()

                assert status["total_locks"] == 2
                assert status["active_locks"] == 2
                assert len(status["lock_details"]) == 2

                # Check lock details
                details = status["lock_details"]
                acquired_by_list = [d["acquired_by"] for d in details]
                assert "STORY-0001" in acquired_by_list
                assert "STORY-0002" in acquired_by_list

    @pytest.mark.asyncio
    async def test_check_deadlock_none(self, lock_manager, temp_files):
        """Test deadlock check when no deadlocks."""
        async with lock_manager.acquire_lock(temp_files[0]):
            deadlocked = await lock_manager.check_deadlock()
            assert len(deadlocked) == 0

    @pytest.mark.asyncio
    async def test_cleanup_unused_locks(self, lock_manager, temp_files):
        """Test cleanup of unused lock instances."""
        file1 = temp_files[0]
        file2 = temp_files[1]

        # Acquire and release locks
        async with lock_manager.acquire_lock(file1):
            pass

        async with lock_manager.acquire_lock(file2):
            pass

        # Locks exist but not held
        assert len(lock_manager.locks) == 2
        assert lock_manager.active_locks == 0

        # Cleanup
        lock_manager.cleanup_unused_locks()

        # Unused locks removed
        assert len(lock_manager.locks) == 0


class TestEdgeCases:
    """Test edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_release_locks_idempotent(self, lock_manager, temp_files):
        """Test that releasing locks multiple times is safe."""
        files = temp_files[:2]
        locks = await lock_manager.acquire_locks(files)

        # Release once
        await lock_manager.release_locks(locks)
        assert lock_manager.active_locks == 0

        # Release again (should be safe)
        await lock_manager.release_locks(locks)
        assert lock_manager.active_locks == 0

    @pytest.mark.asyncio
    async def test_lock_acquisition_exception_handling(self, lock_manager, temp_files):
        """Test that exceptions during lock usage release lock."""
        file_path = temp_files[0]

        with pytest.raises(ValueError, match="Test exception"):
            async with lock_manager.acquire_lock(file_path):
                raise ValueError("Test exception")

        # Lock should be released despite exception
        assert lock_manager.active_locks == 0
        assert file_path.resolve() not in lock_manager.lock_info
