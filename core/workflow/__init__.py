"""
NEXUS V12.3 SCALE-OUT - Workflow Module

Redis-backed workflow registry with graceful degradation to in-memory.
Enables multi-instance deployment where workflows are visible across all nodes.

Components:
- RedisWorkflowRegistry: Redis-backed workflow storage
- DistributedLock: Redlock pattern for concurrent safety
- get_workflow_registry(): Factory function with graceful degradation

Author: Claude (NEXUS V12.3 SCALE-OUT)
Date: 2025-12-16
"""

from .redis_registry import (
    RedisWorkflowRegistry,
    WorkflowStatus,
    get_workflow_registry,
    reset_workflow_registry,
)
from .distributed_lock import (
    DistributedLock,
    LockAcquisitionError,
    acquire_workflow_lock,
    try_acquire_workflow_lock,
)

__all__ = [
    # Registry
    "RedisWorkflowRegistry",
    "WorkflowStatus",
    "get_workflow_registry",
    "reset_workflow_registry",
    # Locks
    "DistributedLock",
    "LockAcquisitionError",
    "acquire_workflow_lock",
    "try_acquire_workflow_lock",
]
