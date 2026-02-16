"""
Async Driver Factory - Create and Manage Async Drivers.

NEXUS V12.4 COGNITIVE BOOST - SDK-First Architecture

Provides a unified interface for creating and managing drivers:
- CLI drivers (AsyncClaudeDriver, AsyncGeminiDriver) - subprocess-based
- SDK drivers (AnthropicSDKDriver, GoogleGenAISDKDriver) - API-first

Driver selection:
- driver_mode="auto" (default): SDK when API key available, else CLI
- driver_mode="sdk": SDK only (fails if no API key)
- driver_mode="cli": CLI only (original behavior)

Usage:
    factory = AsyncDriverFactory(config, workspace_path)

    # CLI drivers (backward compatible)
    claude_cli = factory.get_claude_driver()
    gemini_cli = factory.get_gemini_driver()

    # SDK drivers (V12.4)
    claude_sdk = factory.get_claude_sdk()
    gemini_sdk = factory.get_gemini_sdk()

    # Smart routing (respects driver_mode config)
    driver = factory.get_driver("claude")

    # Cancel all processes
    await factory.cancel_all()
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, Optional, Union, TYPE_CHECKING

from .async_claude_driver import AsyncClaudeDriver, AsyncClaudeDriverConfig
from .async_gemini_driver import AsyncGeminiDriver, AsyncGeminiDriverConfig
from core.async_primitives.process_handle import get_process_registry

if TYPE_CHECKING:
    from .anthropic_sdk_driver import AnthropicSDKDriver
    from .google_genai_sdk_driver import GoogleGenAISDKDriver
    from .protocol import BaseAsyncDriver

logger = logging.getLogger(__name__)


class AsyncDriverFactory:
    """
    Factory for creating and managing async drivers.

    V12.4: Supports both CLI (subprocess) and SDK (API) drivers.
    Singleton pattern ensures only one driver per type exists.
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

        # Driver mode: "auto", "sdk", "cli"
        self._driver_mode: str = getattr(config, 'driver_mode', 'auto')

        # API keys for SDK drivers
        self._anthropic_api_key: Optional[str] = getattr(config, 'anthropic_api_key', None)
        self._google_api_key: Optional[str] = getattr(config, 'google_api_key', None)

        # Lazy-initialized CLI drivers
        self._claude_driver: Optional[AsyncClaudeDriver] = None
        self._gemini_driver: Optional[AsyncGeminiDriver] = None

        # Lazy-initialized SDK drivers (V12.4)
        self._claude_sdk: Optional["AnthropicSDKDriver"] = None
        self._gemini_sdk: Optional["GoogleGenAISDKDriver"] = None

    # =========================================================================
    # CLI Drivers (backward compatible)
    # =========================================================================

    def get_claude_driver(
        self,
        model: Optional[str] = None
    ) -> AsyncClaudeDriver:
        """
        Get or create the Claude CLI driver.

        Args:
            model: Optional model override (uses config default if None)

        Returns:
            AsyncClaudeDriver instance
        """
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
            self._claude_driver.config.model = model

        return self._claude_driver

    def get_gemini_driver(
        self,
        model: Optional[str] = None
    ) -> AsyncGeminiDriver:
        """
        Get or create the Gemini CLI driver.

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

    # =========================================================================
    # SDK Drivers (V12.4 API-First)
    # =========================================================================

    def get_claude_sdk(
        self,
        model: Optional[str] = None,
    ) -> "AnthropicSDKDriver":
        """
        Get or create the Claude SDK driver (API-first).

        Args:
            model: Optional model override

        Returns:
            AnthropicSDKDriver instance

        Raises:
            RuntimeError: If no ANTHROPIC_API_KEY is configured
        """
        if self._claude_sdk is None:
            if not self._anthropic_api_key:
                raise RuntimeError(
                    "AnthropicSDKDriver requires ANTHROPIC_API_KEY. "
                    "Set it in .env or environment."
                )
            from .anthropic_sdk_driver import AnthropicSDKDriver

            self._claude_sdk = AnthropicSDKDriver(
                model=model or getattr(self.config, 'claude_sonnet_model', 'claude-sonnet-4-5-20250929'),
                api_key=self._anthropic_api_key,
                max_tokens=getattr(self.config, 'max_tokens', 8192),
                timeout=float(getattr(self.config, 'timeout', 300)),
                enable_caching=True,
            )
            logger.info(f"Created AnthropicSDKDriver (model={getattr(self._claude_sdk, '_model', 'unknown')})")
        elif model and hasattr(self._claude_sdk, '_model'):
            self._claude_sdk._model = model

        return self._claude_sdk

    def get_gemini_sdk(
        self,
        model: Optional[str] = None,
    ) -> "GoogleGenAISDKDriver":
        """
        Get or create the Gemini SDK driver (API-first).

        Args:
            model: Optional model override

        Returns:
            GoogleGenAISDKDriver instance

        Raises:
            RuntimeError: If no GOOGLE_API_KEY is configured
        """
        if self._gemini_sdk is None:
            if not self._google_api_key:
                raise RuntimeError(
                    "GoogleGenAISDKDriver requires GOOGLE_API_KEY or GEMINI_API_KEY. "
                    "Set it in .env or environment."
                )
            from .google_genai_sdk_driver import GoogleGenAISDKDriver

            self._gemini_sdk = GoogleGenAISDKDriver(
                model=model or getattr(self.config, 'gemini_default_model', 'gemini-3-pro-preview'),
                api_key=self._google_api_key,
                timeout=float(getattr(self.config, 'timeout', 300)),
            )
            logger.info(f"Created GoogleGenAISDKDriver (model={getattr(self._gemini_sdk, '_model', 'unknown')})")
        elif model and hasattr(self._gemini_sdk, '_model'):
            self._gemini_sdk._model = model

        return self._gemini_sdk

    # =========================================================================
    # Smart Driver Selection (V12.4)
    # =========================================================================

    @property
    def claude_sdk_available(self) -> bool:
        """Check if Claude SDK driver can be created (API key present)."""
        return bool(self._anthropic_api_key) and self._driver_mode != "cli"

    @property
    def gemini_sdk_available(self) -> bool:
        """Check if Gemini SDK driver can be created (API key present)."""
        return bool(self._google_api_key) and self._driver_mode != "cli"

    def get_best_claude(self, model: Optional[str] = None) -> Any:
        """
        Get the best available Claude driver based on driver_mode.

        Returns SDK driver if API key available and mode allows,
        otherwise falls back to CLI driver.
        """
        if self._driver_mode == "sdk":
            return self.get_claude_sdk(model)

        if self._driver_mode == "auto" and self._anthropic_api_key:
            try:
                return self.get_claude_sdk(model)
            except Exception as e:
                logger.warning(f"SDK driver failed, falling back to CLI: {e}")

        return self.get_claude_driver(model)

    def get_best_gemini(self, model: Optional[str] = None) -> Any:
        """
        Get the best available Gemini driver based on driver_mode.

        Returns SDK driver if API key available and mode allows,
        otherwise falls back to CLI driver.
        """
        if self._driver_mode == "sdk":
            return self.get_gemini_sdk(model)

        if self._driver_mode == "auto" and self._google_api_key:
            try:
                return self.get_gemini_sdk(model)
            except Exception as e:
                logger.warning(f"SDK driver failed, falling back to CLI: {e}")

        return self.get_gemini_driver(model)

    def get_driver(
        self,
        agent_id: str,
        model: Optional[str] = None,
        prefer_sdk: bool = False,
    ) -> Any:
        """
        Get a driver by agent ID.

        Args:
            agent_id: "claude" or "gemini"
            model: Optional model override
            prefer_sdk: If True, use SDK driver when available (respects driver_mode)

        Returns:
            Appropriate driver (CLI or SDK based on config/preference)

        Raises:
            ValueError: If agent_id is unknown
        """
        agent_lower = agent_id.lower()

        if prefer_sdk or self._driver_mode == "sdk":
            if agent_lower == "claude":
                return self.get_best_claude(model)
            elif agent_lower == "gemini":
                return self.get_best_gemini(model)
        else:
            if agent_lower == "claude":
                return self.get_claude_driver(model)
            elif agent_lower == "gemini":
                return self.get_gemini_driver(model)

        raise ValueError(f"Unknown agent: {agent_id}. Use 'claude' or 'gemini'.")

    # =========================================================================
    # Driver Info (V12.4)
    # =========================================================================

    def get_driver_info(self) -> Dict[str, Any]:
        """
        Get information about available drivers and their status.

        Returns:
            Dict with driver availability and mode info
        """
        return {
            "driver_mode": self._driver_mode,
            "claude_cli_available": True,  # Always available
            "claude_sdk_available": self.claude_sdk_available,
            "claude_sdk_active": self._claude_sdk is not None,
            "gemini_cli_available": True,
            "gemini_sdk_available": self.gemini_sdk_available,
            "gemini_sdk_active": self._gemini_sdk is not None,
            "anthropic_api_key_set": bool(self._anthropic_api_key),
            "google_api_key_set": bool(self._google_api_key),
        }

    # =========================================================================
    # Process Management
    # =========================================================================

    async def cancel_by_uuid(self, session_uuid: str) -> bool:
        """Cancel a specific process by UUID across all drivers."""
        return await self._registry.cancel_by_uuid(session_uuid)

    async def cancel_by_task_id(self, task_id: str) -> int:
        """Cancel all processes for a task."""
        return await self._registry.cancel_by_task_id(task_id)

    async def cancel_all(self) -> int:
        """Cancel ALL active processes (for Ctrl+C handler)."""
        count = await self._registry.cancel_all()
        return count

    async def list_active_processes(self) -> list[Dict[str, Any]]:
        """List all active processes across all drivers."""
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
