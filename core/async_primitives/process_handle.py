"""
AsyncProcessHandle - Track Async Subprocess with Session Context.

NEXUS V9.0 Async-First Architecture

Critical component for:
- UUID-based process tracking (each process has a session_uuid)
- Graceful termination with timeout fallback to kill
- Orphan process prevention on cancellation
- Integration with SwarmSessionManager

This solves the "orphan process" problem where Ctrl+C might leave
CLI processes (claude, gemini) running in the background.

Usage:
    proc = await asyncio.create_subprocess_exec(...)
    handle = AsyncProcessHandle(proc=proc, session_uuid="abc123")

    # Later, to cancel:
    await handle.terminate_gracefully(timeout=2.0)

References:
- https://docs.python.org/3/library/asyncio-subprocess.html
- https://superfastpython.com/asyncio-subprocess/
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum


class ProcessState(str, Enum):
    """State of an async process."""
    RUNNING = "running"
    TERMINATED = "terminated"
    KILLED = "killed"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class AsyncProcessHandle:
    """
    Track an async subprocess with its session context.

    Attributes:
        proc: The asyncio subprocess object
        session_uuid: Unique identifier for session isolation
        task_id: Optional task ID from SwarmSessionManager
        agent_id: Which agent owns this process (gemini/claude)
        created_at: When the process was started
        terminated_at: When the process was terminated (if applicable)
        state: Current process state
        metadata: Additional tracking metadata
    """
    proc: asyncio.subprocess.Process
    session_uuid: str
    task_id: Optional[str] = None
    agent_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    terminated_at: Optional[datetime] = None
    state: ProcessState = ProcessState.RUNNING
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_running(self) -> bool:
        """Check if the process is still running."""
        return self.proc.returncode is None

    @property
    def returncode(self) -> Optional[int]:
        """Get the process return code (None if still running)."""
        return self.proc.returncode

    @property
    def pid(self) -> Optional[int]:
        """Get the process ID."""
        return self.proc.pid

    @property
    def runtime_seconds(self) -> float:
        """Get how long the process has been running."""
        end_time = self.terminated_at or datetime.now()
        return (end_time - self.created_at).total_seconds()

    async def terminate_gracefully(self, timeout: float = 2.0) -> bool:
        """
        Terminate the process gracefully with timeout fallback to kill.

        1. First tries SIGTERM (terminate)
        2. Waits up to `timeout` seconds
        3. If still running, sends SIGKILL (kill)

        Args:
            timeout: Seconds to wait after terminate before killing

        Returns:
            True if process was terminated/killed, False if already dead
        """
        if not self.is_running:
            self.state = ProcessState.COMPLETED
            return False

        # Try graceful termination first
        try:
            self.proc.terminate()
            self.state = ProcessState.TERMINATED
        except ProcessLookupError:
            # Process already gone
            self.state = ProcessState.COMPLETED
            self.terminated_at = datetime.now()
            return False

        try:
            await asyncio.wait_for(self.proc.wait(), timeout=timeout)
            self.terminated_at = datetime.now()
            self.state = ProcessState.TERMINATED
            return True
        except asyncio.TimeoutError:
            # Terminate didn't work, force kill
            try:
                self.proc.kill()
                await self.proc.wait()
                self.state = ProcessState.KILLED
            except ProcessLookupError:
                # Already gone
                self.state = ProcessState.COMPLETED

            self.terminated_at = datetime.now()
            return True

    async def wait(self, timeout: Optional[float] = None) -> int:
        """
        Wait for the process to complete.

        Args:
            timeout: Optional timeout in seconds

        Returns:
            Process exit code

        Raises:
            asyncio.TimeoutError: If timeout is exceeded
        """
        if timeout is not None:
            return await asyncio.wait_for(self.proc.wait(), timeout=timeout)
        return await self.proc.wait()

    async def read_stdout(self) -> bytes:
        """Read all stdout (only if pipe was set up)."""
        if self.proc.stdout:
            return await self.proc.stdout.read()
        return b""

    async def read_stderr(self) -> bytes:
        """Read all stderr (only if pipe was set up)."""
        if self.proc.stderr:
            return await self.proc.stderr.read()
        return b""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging/debugging."""
        return {
            "session_uuid": self.session_uuid,
            "task_id": self.task_id,
            "agent_id": self.agent_id,
            "pid": self.pid,
            "state": self.state.value,
            "is_running": self.is_running,
            "returncode": self.returncode,
            "created_at": self.created_at.isoformat(),
            "terminated_at": self.terminated_at.isoformat() if self.terminated_at else None,
            "runtime_seconds": self.runtime_seconds,
        }

    def __repr__(self) -> str:
        return (
            f"AsyncProcessHandle("
            f"uuid={self.session_uuid[:8]}..., "
            f"pid={self.pid}, "
            f"state={self.state.value})"
        )


class ProcessHandleRegistry:
    """
    Registry for tracking all active AsyncProcessHandles.

    Provides methods to:
    - Track processes by session_uuid
    - Cancel specific processes by UUID
    - Cancel all processes (for Ctrl+C handler)
    - Query active processes

    Thread-safe via asyncio.Lock.
    """

    def __init__(self):
        self._handles: Dict[str, AsyncProcessHandle] = {}
        self._lock = asyncio.Lock()

    async def register(self, handle: AsyncProcessHandle) -> None:
        """Register a process handle."""
        async with self._lock:
            self._handles[handle.session_uuid] = handle

    async def unregister(self, session_uuid: str) -> Optional[AsyncProcessHandle]:
        """Unregister and return a process handle."""
        async with self._lock:
            return self._handles.pop(session_uuid, None)

    async def get(self, session_uuid: str) -> Optional[AsyncProcessHandle]:
        """Get a process handle by UUID."""
        async with self._lock:
            return self._handles.get(session_uuid)

    async def cancel_by_uuid(self, session_uuid: str, timeout: float = 2.0) -> bool:
        """
        Cancel a specific process by its session UUID.

        Args:
            session_uuid: The UUID of the process to cancel
            timeout: Timeout for graceful termination

        Returns:
            True if process was found and terminated
        """
        handle = await self.get(session_uuid)
        if handle:
            result = await handle.terminate_gracefully(timeout)
            await self.unregister(session_uuid)
            return result
        return False

    async def cancel_by_task_id(self, task_id: str, timeout: float = 2.0) -> int:
        """
        Cancel all processes associated with a task ID.

        Args:
            task_id: The task ID to cancel
            timeout: Timeout for each termination

        Returns:
            Number of processes terminated
        """
        count = 0
        async with self._lock:
            handles_to_cancel = [
                h for h in self._handles.values()
                if h.task_id == task_id
            ]

        for handle in handles_to_cancel:
            await handle.terminate_gracefully(timeout)
            await self.unregister(handle.session_uuid)
            count += 1

        return count

    async def cancel_all(self, timeout: float = 2.0) -> int:
        """
        Cancel all active processes.

        Used by Ctrl+C handler to clean up all processes.

        Args:
            timeout: Timeout for each termination

        Returns:
            Number of processes terminated
        """
        count = 0
        async with self._lock:
            handles = list(self._handles.values())
            self._handles.clear()

        for handle in handles:
            if handle.is_running:
                await handle.terminate_gracefully(timeout)
                count += 1

        return count

    async def list_active(self) -> list[Dict[str, Any]]:
        """List all active process handles as dictionaries."""
        async with self._lock:
            return [h.to_dict() for h in self._handles.values() if h.is_running]

    @property
    def active_count(self) -> int:
        """Get count of active processes (non-async for quick checks)."""
        return sum(1 for h in self._handles.values() if h.is_running)

    def __len__(self) -> int:
        return len(self._handles)


# Global registry instance with thread-safe initialization (V9)
import threading
_global_registry: Optional[ProcessHandleRegistry] = None
_registry_lock = threading.Lock()


def get_process_registry() -> ProcessHandleRegistry:
    """
    Get the global process handle registry.

    V9: Thread-safe singleton with double-checked locking to prevent
    race conditions during initialization.
    """
    global _global_registry
    if _global_registry is None:
        with _registry_lock:
            # Double-check inside lock
            if _global_registry is None:
                _global_registry = ProcessHandleRegistry()
    return _global_registry


def reset_process_registry() -> None:
    """
    Reset the global process handle registry.

    CRIT-005: For test isolation - allows tests to start with fresh registry.
    Also cancels any active processes to prevent orphans.

    Usage in tests:
        @pytest.fixture(autouse=True)
        def reset_singletons():
            yield
            reset_process_registry()
    """
    global _global_registry
    if _global_registry is not None:
        # Cancel all active processes first
        import asyncio
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(_global_registry.cancel_all())
        except RuntimeError:
            # No event loop - try sync cleanup
            pass
    _global_registry = None
