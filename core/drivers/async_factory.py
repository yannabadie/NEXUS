"""
Async Driver Factory - Create and Manage Async Drivers.

NEXUS V9.0 Async-First Architecture

Provides a unified interface for creating and managing async drivers:
- AsyncClaudeDriver
- AsyncGeminiDriver

Handles:
- Driver configuration from NEXUS config
- Session isolation
- Centralized cancellation via ProcessHandleRegistry

Usage:
    factory = AsyncDriverFactory(config, workspace_path)

    # Get drivers
    claude = factory.get_claude_driver()
    gemini = factory.get_gemini_driver()

    # Cancel all processes
    await factory.cancel_all()

    # Get active processes
    processes = await factory.list_active_processes()
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Optional, Dict, Any, TYPE_CHECKING

from pathlib import Path
from typing import Optional, Dict, Any, TYPE_CHECKING
from core.async_primitives.process_handle import get_process_registry

# Legacy Imports (Required for Dual Mode)
from .async_claude_driver import AsyncClaudeDriver, AsyncClaudeDriverConfig
from .async_gemini_driver import AsyncGeminiDriver, AsyncGeminiDriverConfig

if TYPE_CHECKING:
    from core.config import NexusConfig


class AsyncDriverFactory:
    """
    Factory for creating and managing async drivers.

    Singleton pattern ensures only one driver per type exists,
    which is important for proper process tracking.
    """

    def __init__(self, config: Any, workspace_path: Path):
        """
        Initialize factory.

        Args:
            config: NEXUS config object (or mock with required attributes)
            workspace_path: Workspace path for file I/O
        """
        self.config = config
        self.workspace_path = Path(workspace_path)
        self._registry = get_process_registry()

        # Lazy-initialized drivers
        self._claude_driver: Optional[AsyncClaudeDriver] = None
        self._gemini_driver: Optional[AsyncGeminiDriver] = None

    def get_claude_driver(
        self,
        model: Optional[str] = None
    ):
        """
        Get or create the Co-Pilot driver (Claude or DeepSeek).
        Controlled by NEXUS_CO_PILOT env var (default: CLAUDE).
        """
        if self._claude_driver is None:
            # Check Co-Pilot Preference
            import os
            co_pilot = os.getenv("NEXUS_CO_PILOT", "CLAUDE").upper()
            
            if co_pilot == "DEEPSEEK":
                from core.drivers.api_adapters.deepseek_adapter import DeepSeekAdapter
                self._claude_driver = DeepSeekAdapter(self.config)
            else:
                # Default: Claude
                use_sdk = getattr(self.config, 'use_official_sdk', True)
                
                if use_sdk:
                    from core.drivers.api_adapters.anthropic_adapter import AnthropicAdapter
                    self._claude_driver = AnthropicAdapter(self.config)
                else:
                    # Legacy CLI Driver
                    config = AsyncClaudeDriverConfig(
                        cli_path=getattr(self.config, 'claude_cli_path', 'claude'),
                        timeout=getattr(self.config, 'timeout', 300.0),
                        model=model or getattr(self.config, 'claude_sonnet_model', 'claude-sonnet-4-5-20250929'),
                        workspace_path=self.workspace_path,
                        verbose=getattr(self.config, 'verbose', False),
                    )
                    self._claude_driver = AsyncClaudeDriver(config)
            
        return self._claude_driver

    def get_gemini_driver(
        self,
        model: Optional[str] = None
    ):
        """
        Get or create the Gemini user driver.
        Supports both Official SDK (Preferred) and Legacy CLI.
        """
        if self._gemini_driver is None:
            use_sdk = getattr(self.config, 'use_official_sdk', True)
            
            if use_sdk:
                from core.drivers.api_adapters.gemini_adapter import GeminiAdapter
                self._gemini_driver = GeminiAdapter(self.config)
            else:
                # Legacy CLI Driver
                config = AsyncGeminiDriverConfig(
                    cli_path=getattr(self.config, 'gemini_cli_path', 'gemini'),
                    timeout=getattr(self.config, 'timeout', 300.0),
                    model=model or getattr(self.config, 'gemini_default_model', 'gemini-3-pro-preview'),
                    workspace_path=self.workspace_path,
                    verbose=getattr(self.config, 'verbose', False),
                    use_session_resume=getattr(self.config, 'gemini_persistent_mode', True),
                )
                self._gemini_driver = AsyncGeminiDriver(config)
            
        return self._gemini_driver

    def get_driver(
        self,
        agent_id: str,
        model: Optional[str] = None
    ):
        agent_lower = agent_id.lower()

        if agent_lower == "claude":
            return self.get_claude_driver(model)
        elif agent_lower == "gemini":
            return self.get_gemini_driver(model)
        else:
            raise ValueError(f"Unknown agent: {agent_id}. Use 'claude' or 'gemini'.")

    async def cancel_by_uuid(self, session_uuid: str) -> bool:
        """
        Cancel a specific process by UUID across all drivers.

        Args:
            session_uuid: The UUID to cancel

        Returns:
            True if found and cancelled
        """
        return await self._registry.cancel_by_uuid(session_uuid)

    async def cancel_by_task_id(self, task_id: str) -> int:
        """
        Cancel all processes for a task.

        Args:
            task_id: The task ID

        Returns:
            Count of processes cancelled
        """
        return await self._registry.cancel_by_task_id(task_id)

    async def cancel_all(self) -> int:
        """
        Cancel ALL active processes (for Ctrl+C handler).

        Returns:
            Number of processes cancelled
        """
        count = 0

        # Cancel via registry (catches all)
        count += await self._registry.cancel_all()

        return count

    async def list_active_processes(self) -> list[Dict[str, Any]]:
        """
        List all active processes across all drivers.

        Returns:
            List of process info dicts
        """
        return await self._registry.list_active()

    @property
    def active_process_count(self) -> int:
        """Get count of all active processes."""
        count = 0
        if self._claude_driver:
            count += self._claude_driver.active_process_count
        if self._gemini_driver:
            count += self._gemini_driver.active_process_count
        return count


# Global factory instance for convenience
_global_factory: Optional[AsyncDriverFactory] = None


def get_driver_factory() -> Optional[AsyncDriverFactory]:
    """Get the global driver factory instance."""
    return _global_factory


def set_driver_factory(factory: AsyncDriverFactory) -> None:
    """Set the global driver factory instance."""
    global _global_factory
    _global_factory = factory


def create_driver_factory(config: Any, workspace_path: Path) -> AsyncDriverFactory:
    """
    Create and register a global driver factory.

    Args:
        config: NEXUS config object
        workspace_path: Workspace path for file I/O

    Returns:
        New factory instance
    """
    factory = AsyncDriverFactory(config, workspace_path)
    set_driver_factory(factory)
    return factory
