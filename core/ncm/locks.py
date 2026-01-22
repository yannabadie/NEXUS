"""
File Locking System - Race Condition Prevention

Implements advisory locks to prevent multiple agents from modifying
the same file simultaneously (Blind Spot #2 mitigation).

Architecture:
    - Per-file asyncio.Lock instances
    - Timeout mechanism to prevent deadlock
    - Context manager interface for safe lock acquisition/release
    - Bulk lock acquisition for multi-file operations

Blind Spot #2 Mitigation:
    Multiple agents working on same file → conflicts
    Solution: Advisory locks ensure only one agent can modify a file at a time

Usage:
    from core.ncm.locks import LockManager

    lock_manager = LockManager(timeout=300.0)

    # Single file lock
    async with lock_manager.acquire_lock(Path("core/auth.py")):
        await edit_file(Path("core/auth.py"), ...)

    # Multiple files lock
    files = [Path("core/auth.py"), Path("core/user.py")]
    locks = await lock_manager.acquire_locks(files)
    try:
        # Modify files
        pass
    finally:
        await lock_manager.release_locks(locks)
"""

from pathlib import Path
from typing import List, Dict, Optional, Set, Any
from datetime import datetime, timedelta
import asyncio
from contextlib import asynccontextmanager

from core.logging import get_logger


class LockTimeout(Exception):
    """
    Raised when lock acquisition times out.

    This typically indicates:
        - Deadlock condition
        - Long-running operation holding lock
        - Multiple agents competing for same file

    Recovery:
        - Retry with exponential backoff
        - Escalate to human if repeated timeouts
    """
    pass


class LockManager:
    """
    File locking manager using asyncio.Lock.

    Responsibilities:
        - Manage per-file lock instances
        - Prevent race conditions between agents
        - Provide timeout mechanism for deadlock prevention
        - Track lock acquisition/release for debugging

    Lock Strategy:
        - Advisory locks (not OS-level file locks)
        - Per-file asyncio.Lock instances
        - Timeout default: 300 seconds (5 minutes)
        - Automatic cleanup of unused locks

    Usage:
        lock_manager = LockManager(timeout=300.0)

        # Context manager (recommended)
        async with lock_manager.acquire_lock(file_path):
            await modify_file(file_path)

        # Manual acquisition (for bulk operations)
        locks = await lock_manager.acquire_locks(file_list)
        try:
            await modify_files(file_list)
        finally:
            await lock_manager.release_locks(locks)
    """

    def __init__(self, timeout: float = 300.0):
        """
        Initialize lock manager.

        Args:
            timeout: Lock acquisition timeout in seconds (default 5 minutes)
                     Increase for complex operations, decrease for simple ones.

        Raises:
            ValueError: If timeout <= 0
        """
        if timeout <= 0:
            raise ValueError(f"timeout must be positive, got {timeout}")

        self.timeout = timeout
        self.logger = get_logger()

        # Fallback if logger is None (can happen in test environments)
        if self.logger is None:
            import logging
            self.logger = logging.getLogger(__name__)

        # Per-file lock instances
        # Key: Path (normalized absolute path)
        # Value: asyncio.Lock
        self.locks: Dict[Path, asyncio.Lock] = {}

        # Lock acquisition tracking (for debugging)
        # Key: Path
        # Value: {acquired_at: datetime, acquired_by: Optional[str]}
        self.lock_info: Dict[Path, Dict[str, Any]] = {}

        # Active locks count (for monitoring)
        self.active_locks = 0

        self.logger.info("lock_manager_initialized", {
            "timeout": timeout
        })

    def _normalize_path(self, path: Path) -> Path:
        """
        Normalize path for lock dictionary key.

        Converts to absolute path and resolves symlinks to ensure
        the same file always uses the same lock.

        Args:
            path: File path (relative or absolute)

        Returns:
            Normalized absolute path
        """
        try:
            # Resolve to absolute path and resolve symlinks
            return path.resolve()
        except Exception as e:
            self.logger.warning("path_normalization_failed", {
                "path": str(path),
                "error": str(e)
            })
            # Fallback: just convert to absolute
            return path.absolute()

    def _get_or_create_lock(self, path: Path) -> asyncio.Lock:
        """
        Get existing lock for path or create new one.

        Args:
            path: Normalized file path

        Returns:
            asyncio.Lock instance for this path
        """
        if path not in self.locks:
            self.locks[path] = asyncio.Lock()
            self.logger.debug("lock_created", {
                "path": str(path)
            })

        return self.locks[path]

    @asynccontextmanager
    async def acquire_lock(
        self,
        path: Path,
        acquired_by: Optional[str] = None
    ):
        """
        Context manager for single file lock acquisition.

        Args:
            path: File path to lock
            acquired_by: Optional identifier for lock holder (e.g., agent_id, story_id)

        Yields:
            None (lock is acquired within context)

        Raises:
            LockTimeout: If lock not acquired within timeout

        Usage:
            async with lock_manager.acquire_lock(Path("core/auth.py"), acquired_by="STORY-0001"):
                await edit_file(Path("core/auth.py"), ...)
        """
        # Normalize path
        norm_path = self._normalize_path(path)

        # Get or create lock
        lock = self._get_or_create_lock(norm_path)

        # Acquire with timeout
        try:
            await asyncio.wait_for(
                lock.acquire(),
                timeout=self.timeout
            )

            # Track acquisition
            self.lock_info[norm_path] = {
                "acquired_at": datetime.now(),
                "acquired_by": acquired_by
            }
            self.active_locks += 1

            self.logger.debug("lock_acquired", {
                "path": str(norm_path),
                "acquired_by": acquired_by
            })

            # Yield control to caller (lock is held)
            yield

        except asyncio.TimeoutError:
            # Log timeout details
            lock_holder = self.lock_info.get(norm_path, {})
            elapsed = None
            if lock_holder.get("acquired_at"):
                elapsed = (datetime.now() - lock_holder["acquired_at"]).total_seconds()

            self.logger.error("lock_timeout", {
                "path": str(norm_path),
                "timeout": self.timeout,
                "current_holder": lock_holder.get("acquired_by"),
                "held_for_seconds": elapsed
            })

            raise LockTimeout(
                f"Failed to acquire lock for {norm_path} within {self.timeout}s "
                f"(currently held by {lock_holder.get('acquired_by', 'unknown')})"
            )

        finally:
            # Release lock
            if lock.locked():
                lock.release()

                # Update tracking
                if norm_path in self.lock_info:
                    del self.lock_info[norm_path]
                self.active_locks = max(0, self.active_locks - 1)

                self.logger.debug("lock_released", {
                    "path": str(norm_path)
                })

    async def acquire_locks(
        self,
        paths: List[Path],
        acquired_by: Optional[str] = None
    ) -> List[asyncio.Lock]:
        """
        Acquire locks for multiple files (bulk acquisition).

        Args:
            paths: List of file paths to lock
            acquired_by: Optional identifier for lock holder

        Returns:
            List of acquired locks (in same order as paths)

        Raises:
            LockTimeout: If any lock not acquired within timeout
                         (already-acquired locks will be released)

        Process:
            1. Normalize all paths
            2. Sort paths (to prevent deadlock)
            3. Acquire locks one by one with timeout
            4. If any timeout → release all and raise
            5. Return acquired locks

        Deadlock Prevention:
            - Locks are always acquired in sorted order
            - This ensures consistent lock ordering across agents
            - Example: Agent A wants [file1, file2], Agent B wants [file2, file1]
              → Both will acquire in order [file1, file2], preventing deadlock

        Usage:
            files = [Path("core/auth.py"), Path("core/user.py")]
            locks = await lock_manager.acquire_locks(files, acquired_by="STORY-0001")
            try:
                # Modify files
                pass
            finally:
                await lock_manager.release_locks(locks)
        """
        if not paths:
            return []

        self.logger.debug("bulk_lock_acquisition_start", {
            "file_count": len(paths),
            "acquired_by": acquired_by
        })

        # Normalize paths
        norm_paths = [self._normalize_path(p) for p in paths]

        # Sort to prevent deadlock
        sorted_paths = sorted(set(norm_paths))  # Also removes duplicates

        # Acquire locks one by one
        acquired_locks: List[asyncio.Lock] = []

        try:
            for path in sorted_paths:
                lock = self._get_or_create_lock(path)

                # Acquire with timeout
                await asyncio.wait_for(
                    lock.acquire(),
                    timeout=self.timeout
                )

                acquired_locks.append(lock)

                # Track acquisition
                self.lock_info[path] = {
                    "acquired_at": datetime.now(),
                    "acquired_by": acquired_by
                }
                self.active_locks += 1

                self.logger.debug("bulk_lock_acquired", {
                    "path": str(path),
                    "progress": f"{len(acquired_locks)}/{len(sorted_paths)}"
                })

            self.logger.debug("bulk_lock_acquisition_complete", {
                "file_count": len(acquired_locks),
                "acquired_by": acquired_by
            })

            return acquired_locks

        except asyncio.TimeoutError as e:
            # Timeout on one lock → release all already-acquired locks
            self.logger.error("bulk_lock_timeout", {
                "acquired_count": len(acquired_locks),
                "total_count": len(sorted_paths),
                "acquired_by": acquired_by
            })

            # Release already-acquired locks
            await self.release_locks(acquired_locks)

            raise LockTimeout(
                f"Failed to acquire all {len(sorted_paths)} locks within {self.timeout}s "
                f"(acquired {len(acquired_locks)} before timeout)"
            )

    async def release_locks(self, locks: List[asyncio.Lock]) -> None:
        """
        Release acquired locks (bulk release).

        Args:
            locks: List of locks to release (from acquire_locks)

        Process:
            1. Release each lock if still held
            2. Update tracking info
            3. Log release

        NOTE: It's safe to call this multiple times on the same locks.
              Only locks that are currently held will be released.
        """
        if not locks:
            return

        released_count = 0

        for lock in locks:
            if lock.locked():
                lock.release()
                released_count += 1

        # Clean up tracking info
        # (Note: We can't easily map lock → path, so just decrement counter)
        self.active_locks = max(0, self.active_locks - released_count)

        self.logger.debug("bulk_locks_released", {
            "released_count": released_count
        })

    def get_lock_status(self) -> Dict[str, any]:
        """
        Get current lock status for monitoring.

        Returns:
            Dict with lock information:
                - total_locks: Number of lock instances created
                - active_locks: Number of currently held locks
                - lock_details: List of currently held locks with info

        Usage:
            status = lock_manager.get_lock_status()
            print(f"Active locks: {status['active_locks']}")
        """
        lock_details = []

        for path, info in self.lock_info.items():
            acquired_at = info.get("acquired_at")
            held_duration = None
            if acquired_at:
                held_duration = (datetime.now() - acquired_at).total_seconds()

            lock_details.append({
                "path": str(path),
                "acquired_by": info.get("acquired_by"),
                "acquired_at": acquired_at.isoformat() if acquired_at else None,
                "held_for_seconds": held_duration
            })

        return {
            "total_locks": len(self.locks),
            "active_locks": self.active_locks,
            "lock_details": lock_details
        }

    async def check_deadlock(self) -> List[Dict[str, Any]]:
        """
        Check for potential deadlock conditions.

        Returns:
            List of potentially deadlocked locks (held longer than timeout)

        A lock is considered potentially deadlocked if:
            - It's been held longer than self.timeout
            - This suggests the holder may have crashed or is stuck

        Recovery:
            - Human intervention required
            - Force-release locks if necessary
            - Investigate holder (agent, story)

        Usage:
            deadlocked = await lock_manager.check_deadlock()
            if deadlocked:
                print(f"Warning: {len(deadlocked)} potential deadlocks")
        """
        now = datetime.now()
        deadlocked = []

        for path, info in self.lock_info.items():
            acquired_at = info.get("acquired_at")
            if not acquired_at:
                continue

            held_duration = (now - acquired_at).total_seconds()

            if held_duration > self.timeout:
                deadlocked.append({
                    "path": str(path),
                    "acquired_by": info.get("acquired_by"),
                    "held_for_seconds": held_duration,
                    "timeout": self.timeout
                })

                self.logger.warning("potential_deadlock_detected", {
                    "path": str(path),
                    "acquired_by": info.get("acquired_by"),
                    "held_for_seconds": held_duration
                })

        return deadlocked

    def cleanup_unused_locks(self):
        """
        Clean up lock instances that are not currently held.

        This helps reduce memory usage for long-running NCM sessions.

        Process:
            1. Identify locks not in lock_info (not currently held)
            2. Remove from self.locks dict
            3. Log cleanup count

        NOTE: This is safe because new locks are created on-demand
              via _get_or_create_lock().

        Usage:
            # Call periodically (e.g., every 100 stories)
            lock_manager.cleanup_unused_locks()
        """
        held_paths = set(self.lock_info.keys())
        all_paths = set(self.locks.keys())
        unused_paths = all_paths - held_paths

        for path in unused_paths:
            del self.locks[path]

        if unused_paths:
            self.logger.debug("unused_locks_cleaned", {
                "cleaned_count": len(unused_paths),
                "remaining_locks": len(self.locks)
            })
