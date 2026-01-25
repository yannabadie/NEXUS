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

from .async_claude_driver import AsyncClaudeDriver, AsyncClaudeDriverConfig
from .async_gemini_driver import AsyncGeminiDriver, AsyncGeminiDriverConfig
from .async_kimi_driver import AsyncKimiDriver, AsyncKimiDriverConfig
from .async_deepseek_driver import AsyncDeepSeekDriver, AsyncDeepSeekDriverConfig
from .async_glm_driver import AsyncGLMDriver, AsyncGLMDriverConfig
from core.async_primitives.process_handle import get_process_registry

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
        self._kimi_driver: Optional[AsyncKimiDriver] = None
        self._deepseek_driver: Optional[AsyncDeepSeekDriver] = None
        self._glm_driver: Optional[AsyncGLMDriver] = None

    def get_claude_driver(
        self,
        model: Optional[str] = None
    ) -> AsyncClaudeDriver:
        """
        Get or create the Claude driver.

        Args:
            model: Optional model override (uses config default if None)

        Returns:
            AsyncClaudeDriver instance
        """
        use_glm = getattr(self.config, "use_glm_for_claude", False)
        if use_glm and getattr(self.config, "glm_api_key", None):
            return self.get_glm_driver()

        if self._claude_driver is None:
            config = AsyncClaudeDriverConfig(
                cli_path=getattr(self.config, 'claude_cli_path', 'claude'),
                timeout=getattr(self.config, 'timeout', 300.0),
                model=model or getattr(self.config, 'claude_sonnet_model', 'claude-sonnet-4-5-20250929'),
                workspace_path=self.workspace_path,
                verbose=getattr(self.config, 'verbose', False),
            )
            self._claude_driver = AsyncClaudeDriver(config)
        elif model:
            # Update model if different
            self._claude_driver.config.model = model

        return self._claude_driver

    def get_gemini_driver(
        self,
        model: Optional[str] = None
    ) -> AsyncGeminiDriver:
        """
        Get or create the Gemini driver.

        Args:
            model: Optional model override (uses config default if None)

        Returns:
            AsyncGeminiDriver instance
        """
        if self._gemini_driver is None:
            config = AsyncGeminiDriverConfig(
                cli_path=getattr(self.config, 'gemini_cli_path', 'gemini'),
                timeout=getattr(self.config, 'timeout', 300.0),
                model=model or getattr(self.config, 'gemini_default_model', 'gemini-3-pro-preview'),
                workspace_path=self.workspace_path,
                verbose=getattr(self.config, 'verbose', False),
                use_session_resume=getattr(self.config, 'gemini_persistent_mode', True),
            )
            self._gemini_driver = AsyncGeminiDriver(config)
        elif model:
            self._gemini_driver.config.model = model

        return self._gemini_driver

    def get_kimi_driver(
        self,
        model: Optional[str] = None
    ) -> AsyncKimiDriver:
        """
        Get or create the Kimi driver.

        Args:
            model: Optional model override

        Returns:
            AsyncKimiDriver instance
        """
        if self._kimi_driver is None:
            api_key = getattr(self.config, "kimi_api_key", None)
            if not api_key:
                raise ValueError("KIMI_API_KEY is not configured")

            config = AsyncKimiDriverConfig(
                api_key=api_key,
                api_base=getattr(self.config, "kimi_api_base", "https://api.moonshot.ai/v1"),
                model=model or getattr(self.config, "kimi_model", "kimi-k2-thinking"),
                timeout=getattr(self.config, "kimi_timeout", 60.0),
                max_tokens=getattr(self.config, "kimi_max_tokens", 4096),
                temperature=getattr(self.config, "kimi_temperature", 0.2),
                verify_ssl=getattr(self.config, "kimi_verify_ssl", True),
                ca_bundle=getattr(self.config, "kimi_ca_bundle", None),
                ssl_mode=getattr(self.config, "kimi_ssl_mode", "strict"),
            )
            self._kimi_driver = AsyncKimiDriver(config)
        elif model:
            self._kimi_driver.config.model = model

        return self._kimi_driver

    def get_deepseek_driver(
        self,
        model: Optional[str] = None
    ) -> AsyncDeepSeekDriver:
        """
        Get or create the DeepSeek driver.

        Args:
            model: Optional model override

        Returns:
            AsyncDeepSeekDriver instance
        """
        if self._deepseek_driver is None:
            api_key = getattr(self.config, "deepseek_api_key", None)
            if not api_key:
                raise ValueError("DEEPSEEK_API_KEY is not configured")

            config = AsyncDeepSeekDriverConfig(
                api_key=api_key,
                api_base=getattr(self.config, "deepseek_api_base", "https://api.deepseek.com/v1"),
                model=model or getattr(self.config, "deepseek_model", "deepseek-reasoner"),
                timeout=getattr(self.config, "deepseek_timeout", 60.0),
                max_tokens=getattr(self.config, "deepseek_max_tokens", 4096),
                temperature=getattr(self.config, "deepseek_temperature", 0.2),
                verify_ssl=getattr(self.config, "deepseek_verify_ssl", True),
                ca_bundle=getattr(self.config, "deepseek_ca_bundle", None),
                ssl_mode=getattr(self.config, "deepseek_ssl_mode", "strict"),
            )
            self._deepseek_driver = AsyncDeepSeekDriver(config)
        elif model:
            self._deepseek_driver.config.model = model

        return self._deepseek_driver

    def get_glm_driver(
        self,
        model: Optional[str] = None
    ) -> AsyncGLMDriver:
        """
        Get or create the GLM driver.

        Args:
            model: Optional model override

        Returns:
            AsyncGLMDriver instance
        """
        if self._glm_driver is None:
            api_key = getattr(self.config, "glm_api_key", None)
            if not api_key:
                raise ValueError("GLM_API_KEY is not configured")

            config = AsyncGLMDriverConfig(
                api_key=api_key,
                api_base=getattr(self.config, "glm_api_base", "https://api.z.ai/api/paas/v4"),
                model=model or getattr(self.config, "glm_model", "glm-4.7"),
                timeout=getattr(self.config, "glm_timeout", 60.0),
                max_tokens=getattr(self.config, "glm_max_tokens", 4096),
                temperature=getattr(self.config, "glm_temperature", 0.2),
                max_retries=getattr(self.config, "glm_max_retries", 2),
                verify_ssl=getattr(self.config, "glm_verify_ssl", True),
                ca_bundle=getattr(self.config, "glm_ca_bundle", None),
                ssl_mode=getattr(self.config, "glm_ssl_mode", "strict"),
            )
            self._glm_driver = AsyncGLMDriver(config)
        elif model:
            # Only update if model is a GLM model override.
            self._glm_driver.config.model = model

        return self._glm_driver

    def get_driver(
        self,
        agent_id: str,
        model: Optional[str] = None
    ):
        """
        Get a driver by agent ID.

        Args:
            agent_id: "claude" or "gemini"
            model: Optional model override

        Returns:
            Appropriate async driver

        Raises:
            ValueError: If agent_id is unknown
        """
        agent_lower = agent_id.lower()

        if agent_lower == "claude":
            if getattr(self.config, "use_glm_for_claude", False) and getattr(self.config, "glm_api_key", None):
                return self.get_glm_driver()
            return self.get_claude_driver(model)
        elif agent_lower == "gemini":
            return self.get_gemini_driver(model)
        elif agent_lower == "kimi":
            return self.get_kimi_driver(model)
        elif agent_lower == "deepseek":
            return self.get_deepseek_driver(model)
        elif agent_lower == "glm":
            return self.get_glm_driver(model)
        else:
            raise ValueError(
                f"Unknown agent: {agent_id}. Use 'claude', 'gemini', 'kimi', 'deepseek', or 'glm'."
            )

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
        if self._glm_driver:
            count += self._glm_driver.active_process_count
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
