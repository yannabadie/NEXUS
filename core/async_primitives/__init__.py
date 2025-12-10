"""
NEXUS V9.0 Async Primitives
===========================

Core async building blocks for the Async-First architecture.

Components:
- CancellationToken: Hierarchical cancellation with propagation
- AsyncProcessHandle: Track subprocess by session_uuid
- AsyncRWLock: Multiple readers OR single writer lock
- AsyncBlackboard: Thread-safe async shared state

Usage:
    from core.async_primitives import (
        CancellationToken,
        AsyncProcessHandle,
        AsyncRWLock,
        AsyncBlackboard,
    )
"""

from .cancellation import CancellationToken
from .process_handle import AsyncProcessHandle
from .rwlock import AsyncRWLock
from .blackboard import AsyncBlackboard

__all__ = [
    'CancellationToken',
    'AsyncProcessHandle',
    'AsyncRWLock',
    'AsyncBlackboard',
]

__version__ = "9.0.0"
