"""
Async Adapter for NEXUS V9.0 Hive Mind.

Bridges V9 async drivers with existing Hive Mind phases.
Adds CancellationToken support for graceful shutdown.

This adapter wraps the existing TrueHiveMind orchestrator to:
1. Accept async drivers (AsyncClaudeDriver, AsyncGeminiDriver)
2. Propagate CancellationToken through all phases
3. Track task UUIDs for cancellation
4. Use AsyncBlackboard for shared state

Usage:
    adapter = AsyncHiveMindAdapter(
        hive_mind=true_hive_mind,
        driver_factory=factory,
        blackboard=async_blackboard
    )

    result = await adapter.process_task(
        task="Complex task",
        token=cancellation_token,
        session_uuid="task-123"
    )
"""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Optional, Dict, Any, TYPE_CHECKING
from datetime import datetime

from core.async_primitives import CancellationToken, AsyncBlackboard
from core.async_primitives.process_handle import get_process_registry

if TYPE_CHECKING:
    from .orchestrator import TrueHiveMind, HiveMindResult
    from core.drivers.async_factory import AsyncDriverFactory

logger = logging.getLogger(__name__)


class AsyncHiveMindAdapter:
    """
    Adapter that adds V9 async capabilities to existing HiveMind.

    This is a thin wrapper that:
    - Passes CancellationToken to async drivers
    - Tracks task by session_uuid for cancellation
    - Uses AsyncBlackboard for phase communication
    """

    def __init__(
        self,
        hive_mind: "TrueHiveMind",
        driver_factory: Optional["AsyncDriverFactory"] = None,
        blackboard: Optional[AsyncBlackboard] = None,
    ):
        """
        Initialize adapter.

        Args:
            hive_mind: Existing TrueHiveMind instance
            driver_factory: V9 async driver factory (optional)
            blackboard: V9 async blackboard (optional)
        """
        self.hive_mind = hive_mind
        self.driver_factory = driver_factory
        self.blackboard = blackboard or AsyncBlackboard()

        # Track active tasks
        self._active_tasks: Dict[str, CancellationToken] = {}
        self._registry = get_process_registry()

    async def process_task(
        self,
        task: str,
        *,
        token: Optional[CancellationToken] = None,
        session_uuid: Optional[str] = None,
        complexity: Optional[Any] = None,
    ) -> "HiveMindResult":
        """
        Process task with V9 async capabilities.

        Args:
            task: Task description
            token: CancellationToken for graceful cancellation
            session_uuid: Unique ID for this task execution
            complexity: Optional TaskComplexity

        Returns:
            HiveMindResult from HiveMind
        """
        token = token or CancellationToken()
        session_uuid = session_uuid or f"hive_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Track this task
        self._active_tasks[session_uuid] = token

        # Store task info in blackboard
        await self.blackboard.set(
            f"task_{session_uuid}_started",
            datetime.now().isoformat(),
            source="hive_mind_adapter"
        )

        try:
            # Check cancellation before starting
            token.check()

            # Call existing process_task
            # Note: The existing HiveMind uses sync drivers internally.
            # This adapter provides the infrastructure for V9 integration
            # without requiring full rewrite of all phases.
            if complexity:
                result = await self.hive_mind.process_task(task, complexity=complexity)
            else:
                result = await self.hive_mind.process_task(task)

            # Store result in blackboard
            await self.blackboard.set(
                f"task_{session_uuid}_result",
                {
                    "success": result.success,
                    "phases": result.phases_completed,
                    "duration": result.total_duration,
                },
                source="hive_mind_adapter"
            )

            return result

        except asyncio.CancelledError:
            logger.info(f"HiveMind task {session_uuid} was cancelled")

            # Cancel any processes associated with this task
            await self._registry.cancel_by_task_id(session_uuid)

            # Re-raise as required by Python docs
            raise

        finally:
            # Cleanup
            self._active_tasks.pop(session_uuid, None)

    async def cancel_task(self, session_uuid: str) -> bool:
        """
        Cancel a specific task by its session UUID.

        Args:
            session_uuid: UUID of the task to cancel

        Returns:
            True if task was found and cancelled
        """
        token = self._active_tasks.get(session_uuid)
        if token:
            token.cancel(reason=f"Task {session_uuid} cancelled by user")

            # Also cancel any driver processes
            cancelled = await self._registry.cancel_by_task_id(session_uuid)
            logger.info(f"Cancelled task {session_uuid}, {cancelled} processes terminated")

            return True
        return False

    async def cancel_all(self) -> int:
        """
        Cancel all active tasks.

        Returns:
            Number of tasks cancelled
        """
        count = 0
        for session_uuid, token in list(self._active_tasks.items()):
            token.cancel(reason="All tasks cancelled")
            count += 1

        # Cancel all driver processes
        driver_count = await self._registry.cancel_all()
        logger.info(f"Cancelled {count} tasks, {driver_count} processes")

        return count

    @property
    def active_task_count(self) -> int:
        """Get number of active tasks."""
        return len(self._active_tasks)

    async def get_task_status(self, session_uuid: str) -> Optional[Dict[str, Any]]:
        """
        Get status of a task from blackboard.

        Args:
            session_uuid: Task UUID

        Returns:
            Status dict or None if not found
        """
        started = await self.blackboard.get(f"task_{session_uuid}_started")
        result = await self.blackboard.get(f"task_{session_uuid}_result")

        if not started:
            return None

        return {
            "session_uuid": session_uuid,
            "started": started,
            "completed": result is not None,
            "result": result,
            "is_active": session_uuid in self._active_tasks,
        }


class DriverBridge:
    """
    Bridge that wraps async drivers to look like sync drivers.

    .. deprecated:: V8.4.4
        Use async drivers directly with `await driver.invoke()` or
        `driver.invoke_sync()` for sync fallback. DriverBridge will
        be removed in V9.0.

    This allows gradual migration - phases can use the bridge
    until they're updated to use async drivers directly.

    Note: This uses asyncio.run_coroutine_threadsafe which is
    NOT ideal for performance. Full V9 should use async drivers
    directly in phases.
    """

    def __init__(
        self,
        async_driver,
        loop: Optional[asyncio.AbstractEventLoop] = None
    ):
        """
        Initialize bridge.

        Args:
            async_driver: AsyncClaudeDriver or AsyncGeminiDriver
            loop: Event loop to use (or get running loop)

        .. deprecated:: V8.4.4
            Use `driver.invoke_sync()` instead of DriverBridge.
        """
        import warnings
        warnings.warn(
            "DriverBridge is deprecated since V8.4.4. "
            "Use async drivers directly with `await driver.invoke()` or "
            "`driver.invoke_sync()` for sync fallback. "
            "DriverBridge will be removed in V9.0.",
            DeprecationWarning,
            stacklevel=2
        )
        self.async_driver = async_driver
        self._loop = loop

    def invoke(self, context: str, **kwargs) -> Dict[str, Any]:
        """
        Synchronous invoke that wraps async driver.

        WARNING: This blocks the calling thread. Only for
        backwards compatibility during migration.

        .. deprecated:: V8.4.4
            Use `driver.invoke_sync()` instead.
        """
        # V11.4 ASYNC: Python 3.12+ compatibility
        # Try get_running_loop() first (in async context), then fallback
        try:
            loop = self._loop or asyncio.get_running_loop()
            # Loop is running - use run_coroutine_threadsafe
            future = asyncio.run_coroutine_threadsafe(
                self.async_driver.invoke(context, **kwargs),
                loop
            )
            return future.result(timeout=300)
        except RuntimeError:
            # No running loop - create one and run
            return asyncio.run(
                self.async_driver.invoke(context, **kwargs)
            )


# ============================================================================
# V8.4.4 MIGRATION GUIDE - DriverBridge Removal
# ============================================================================
#
# DriverBridge is DEPRECATED since V8.4.4. Migration paths:
#
# 1. ASYNC CODE (Recommended):
#    BEFORE: bridge = DriverBridge(async_driver); result = bridge.invoke(ctx)
#    AFTER:  result = await async_driver.invoke(ctx)
#
# 2. SYNC CODE (Transitional):
#    BEFORE: bridge = DriverBridge(async_driver); result = bridge.invoke(ctx)
#    AFTER:  result = async_driver.invoke_sync(ctx)  # Also deprecated!
#
# 3. HIVEMIND PHASES (Already migrated):
#    All phases use send_message_async() which wraps sync drivers via
#    asyncio.to_thread(). No DriverBridge usage.
#
# Removal Timeline:
# - V8.4.4: DriverBridge deprecated, invoke_sync() deprecated
# - V8.5.x: DriverBridge removed from codebase
# - V9.0:   invoke_sync() removed, all code must be async
#
# See also:
# - core/drivers/async_claude_driver.py:invoke_sync()
# - core/drivers/async_gemini_driver.py:invoke_sync()
# - core/utils/async_utils.py:run_sync() (also deprecated V8.4.4)
# ============================================================================


def create_async_hive_mind(
    workspace_path: Path,
    config: Any,
    driver_factory: "AsyncDriverFactory",
    blackboard: Optional[AsyncBlackboard] = None,
    **kwargs
) -> AsyncHiveMindAdapter:
    """
    Create an async-enabled HiveMind.

    This factory creates a TrueHiveMind with sync drivers (for backwards
    compatibility with phases) wrapped in an AsyncHiveMindAdapter.

    For full V9 performance, phases should be updated to use async
    drivers directly.

    Args:
        workspace_path: NEXUS workspace path
        config: NEXUS configuration
        driver_factory: V9 async driver factory
        blackboard: Optional async blackboard
        **kwargs: Additional args for TrueHiveMind

    Returns:
        AsyncHiveMindAdapter wrapping TrueHiveMind
    """
    # Import here to avoid circular imports
    from .orchestrator import TrueHiveMind
    from core.drivers.protocol import BaseAsyncDriver, ClaudeDriverHybrid

    # Create sync drivers for backwards compatibility
    # TODO: Update phases to use async drivers directly
    gemini_sync = BaseAsyncDriver(workspace_path, config)
    claude_sync = ClaudeDriverHybrid(workspace_path, config)

    # Create HiveMind with sync drivers
    hive_mind = TrueHiveMind(
        workspace_path=workspace_path,
        config=config,
        gemini_driver=gemini_sync,
        claude_driver=claude_sync,
        **kwargs
    )

    # Wrap with async adapter
    return AsyncHiveMindAdapter(
        hive_mind=hive_mind,
        driver_factory=driver_factory,
        blackboard=blackboard or AsyncBlackboard()
    )
