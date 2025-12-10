"""
AsyncBlackboard - Thread-Safe Async Shared State.

NEXUS V9.0 Async-First Architecture

The Blackboard is NEXUS's shared memory space where:
- Agents store intermediate results
- Phases communicate context
- Tool results are cached

This async version uses AsyncRWLock for safe concurrent access,
replacing the sync RLock-based implementation.

Features:
- Multiple concurrent reads (via AsyncRWLock)
- Exclusive writes
- Atomic get-or-set operations
- Snapshot for safe iteration
- Namespaced keys for organization

Usage:
    bb = AsyncBlackboard()

    await bb.set("analysis_result", {"score": 0.95})
    result = await bb.get("analysis_result")

    # Atomic get-or-set
    value = await bb.get_or_set("cache_key", compute_default)

    # Safe iteration via snapshot
    data = await bb.snapshot()
    for key, value in data.items():
        process(key, value)
"""

from __future__ import annotations

import copy
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union
from dataclasses import dataclass, field

from .rwlock import AsyncRWLock, InstrumentedAsyncRWLock

T = TypeVar('T')


@dataclass
class BlackboardEntry:
    """
    A single entry in the blackboard with metadata.

    Attributes:
        value: The stored value
        created_at: When the entry was created
        updated_at: When the entry was last updated
        source: What created this entry (agent, phase, etc.)
        ttl_seconds: Optional time-to-live
    """
    value: Any
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    source: Optional[str] = None
    ttl_seconds: Optional[float] = None

    @property
    def is_expired(self) -> bool:
        """Check if entry has expired based on TTL."""
        if self.ttl_seconds is None:
            return False
        age = (datetime.now() - self.updated_at).total_seconds()
        return age > self.ttl_seconds


class AsyncBlackboard:
    """
    Thread-safe async shared state container.

    Provides dictionary-like access with async methods and
    proper locking for concurrent access.
    """

    def __init__(
        self,
        initial_data: Optional[Dict[str, Any]] = None,
        instrumented: bool = False
    ):
        """
        Initialize the blackboard.

        Args:
            initial_data: Optional initial data to populate
            instrumented: If True, use instrumented lock for stats
        """
        self._data: Dict[str, BlackboardEntry] = {}
        self._lock = InstrumentedAsyncRWLock() if instrumented else AsyncRWLock()

        if initial_data:
            for key, value in initial_data.items():
                self._data[key] = BlackboardEntry(value=value)

    async def get(
        self,
        key: str,
        default: T = None,
        include_expired: bool = False
    ) -> Union[Any, T]:
        """
        Get a value from the blackboard.

        Args:
            key: The key to look up
            default: Value to return if key not found
            include_expired: If True, return expired values too

        Returns:
            The value or default if not found
        """
        async with self._lock.read():
            entry = self._data.get(key)
            if entry is None:
                return default
            if entry.is_expired and not include_expired:
                return default
            return entry.value

    async def set(
        self,
        key: str,
        value: Any,
        source: Optional[str] = None,
        ttl_seconds: Optional[float] = None
    ) -> None:
        """
        Set a value in the blackboard.

        Args:
            key: The key to set
            value: The value to store
            source: Optional source identifier
            ttl_seconds: Optional time-to-live in seconds
        """
        async with self._lock.write():
            now = datetime.now()
            if key in self._data:
                # Update existing
                entry = self._data[key]
                entry.value = value
                entry.updated_at = now
                if source:
                    entry.source = source
                if ttl_seconds is not None:
                    entry.ttl_seconds = ttl_seconds
            else:
                # Create new
                self._data[key] = BlackboardEntry(
                    value=value,
                    created_at=now,
                    updated_at=now,
                    source=source,
                    ttl_seconds=ttl_seconds
                )

    async def delete(self, key: str) -> bool:
        """
        Delete a key from the blackboard.

        Args:
            key: The key to delete

        Returns:
            True if key existed and was deleted
        """
        async with self._lock.write():
            if key in self._data:
                del self._data[key]
                return True
            return False

    async def update(
        self,
        updates: Dict[str, Any],
        source: Optional[str] = None
    ) -> None:
        """
        Update multiple values atomically.

        Args:
            updates: Dictionary of key-value pairs to update
            source: Optional source identifier for all updates
        """
        async with self._lock.write():
            now = datetime.now()
            for key, value in updates.items():
                if key in self._data:
                    entry = self._data[key]
                    entry.value = value
                    entry.updated_at = now
                    if source:
                        entry.source = source
                else:
                    self._data[key] = BlackboardEntry(
                        value=value,
                        created_at=now,
                        updated_at=now,
                        source=source
                    )

    async def get_or_set(
        self,
        key: str,
        default_factory: Callable[[], T],
        source: Optional[str] = None,
        ttl_seconds: Optional[float] = None
    ) -> T:
        """
        Get a value, or set it if not present (atomic operation).

        Args:
            key: The key to look up
            default_factory: Callable that returns default value if key not found
            source: Optional source identifier
            ttl_seconds: Optional TTL if creating new entry

        Returns:
            The existing or newly created value
        """
        # First try read-only check
        async with self._lock.read():
            entry = self._data.get(key)
            if entry is not None and not entry.is_expired:
                return entry.value

        # Need to write
        async with self._lock.write():
            # Double-check after acquiring write lock
            entry = self._data.get(key)
            if entry is not None and not entry.is_expired:
                return entry.value

            # Create new entry
            value = default_factory()
            now = datetime.now()
            self._data[key] = BlackboardEntry(
                value=value,
                created_at=now,
                updated_at=now,
                source=source,
                ttl_seconds=ttl_seconds
            )
            return value

    async def snapshot(self, deep_copy: bool = True) -> Dict[str, Any]:
        """
        Get a snapshot of all current values.

        Safe to iterate over without holding the lock.

        Args:
            deep_copy: If True, deep copy values to prevent mutation

        Returns:
            Dictionary of all key-value pairs
        """
        async with self._lock.read():
            if deep_copy:
                return {
                    k: copy.deepcopy(v.value)
                    for k, v in self._data.items()
                    if not v.is_expired
                }
            else:
                return {
                    k: v.value
                    for k, v in self._data.items()
                    if not v.is_expired
                }

    async def keys(self, include_expired: bool = False) -> List[str]:
        """Get all keys in the blackboard."""
        async with self._lock.read():
            if include_expired:
                return list(self._data.keys())
            return [k for k, v in self._data.items() if not v.is_expired]

    async def contains(self, key: str) -> bool:
        """Check if a key exists (and is not expired)."""
        async with self._lock.read():
            entry = self._data.get(key)
            return entry is not None and not entry.is_expired

    async def clear(self) -> int:
        """
        Clear all data from the blackboard.

        Returns:
            Number of entries cleared
        """
        async with self._lock.write():
            count = len(self._data)
            self._data.clear()
            return count

    async def clear_expired(self) -> int:
        """
        Remove all expired entries.

        Returns:
            Number of entries removed
        """
        async with self._lock.write():
            expired_keys = [k for k, v in self._data.items() if v.is_expired]
            for key in expired_keys:
                del self._data[key]
            return len(expired_keys)

    async def get_metadata(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Get metadata for an entry.

        Returns:
            Dictionary with created_at, updated_at, source, ttl, is_expired
        """
        async with self._lock.read():
            entry = self._data.get(key)
            if entry is None:
                return None
            return {
                "created_at": entry.created_at.isoformat(),
                "updated_at": entry.updated_at.isoformat(),
                "source": entry.source,
                "ttl_seconds": entry.ttl_seconds,
                "is_expired": entry.is_expired,
            }

    async def namespaced_keys(self, namespace: str) -> List[str]:
        """
        Get all keys with a given namespace prefix.

        Args:
            namespace: Prefix to match (e.g., "hive_" matches "hive_analysis")

        Returns:
            List of matching keys
        """
        async with self._lock.read():
            return [
                k for k, v in self._data.items()
                if k.startswith(namespace) and not v.is_expired
            ]

    async def size(self) -> int:
        """Get the number of entries (excluding expired)."""
        async with self._lock.read():
            return sum(1 for v in self._data.values() if not v.is_expired)

    def __repr__(self) -> str:
        # Sync repr for debugging - don't acquire lock
        return f"AsyncBlackboard(entries={len(self._data)})"


# Convenience function for creating a blackboard
def create_blackboard(
    initial_data: Optional[Dict[str, Any]] = None,
    instrumented: bool = False
) -> AsyncBlackboard:
    """Create a new AsyncBlackboard instance."""
    return AsyncBlackboard(initial_data, instrumented)
