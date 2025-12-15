"""NEXUS V9 Drivers Module

V9 Async-First Architecture:
- AsyncClaudeDriver: True non-blocking Claude CLI driver
- AsyncGeminiDriver: True non-blocking Gemini CLI driver
- AsyncDriverFactory: Unified driver creation and management

Legacy sync drivers kept for backwards compatibility.
"""

# V9 Async Drivers (preferred)
from .async_claude_driver import AsyncClaudeDriver, AsyncClaudeDriverConfig, create_async_claude_driver
from .async_gemini_driver import AsyncGeminiDriver, AsyncGeminiDriverConfig, create_async_gemini_driver
from .async_factory import AsyncDriverFactory, get_driver_factory, set_driver_factory, create_driver_factory

# Legacy sync drivers (backwards compatibility)
from .gemini_driver_v7 import GeminiDriverV7
from .claude_driver_hybrid import ClaudeDriverHybrid

__all__ = [
    # V9 Async (preferred)
    "AsyncClaudeDriver",
    "AsyncClaudeDriverConfig",
    "create_async_claude_driver",
    "AsyncGeminiDriver",
    "AsyncGeminiDriverConfig",
    "create_async_gemini_driver",
    "AsyncDriverFactory",
    "get_driver_factory",
    "set_driver_factory",
    "create_driver_factory",
    # Legacy sync
    "GeminiDriverV7",
    "ClaudeDriverHybrid",
]
