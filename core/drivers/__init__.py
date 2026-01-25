"""NEXUS V11 Drivers Module

V11 Abstraction Layer (F31-F33 fixes):
- DriverProtocol: Unified interface for CLI/API drivers
- CLIAdapters: Protocol-compliant wrappers for existing CLI drivers
- SessionProtocol: Abstracted session management (F32)
- ToolExecutorProtocol: Abstracted tool execution (F33)

V9 Async-First Architecture:
- AsyncClaudeDriver: True non-blocking Claude CLI driver
- AsyncGeminiDriver: True non-blocking Gemini CLI driver
- AsyncDriverFactory: Unified driver creation and management

Legacy sync drivers kept for backwards compatibility.
"""

# V11 Abstraction Layer (F31-F33)
from .protocol import (
    DriverProtocol,
    DriverResponse,
    DriverResponseStatus,
    ToolCall,
    StreamChunk,
    SessionProtocol,
    ToolExecutorProtocol,
    BaseAsyncDriver,
)
from .cli_adapter import (
    GeminiCLIAdapter,
    ClaudeCLIAdapter,
    GLMAPIAdapter,
    create_cli_adapter,
)
from .session_abstraction import (
    SessionMode,
    SessionState,
    SessionMetadata,
    SessionManager,
    CLISessionManager,
    SessionRegistry,
    get_session_registry,
)
from .tool_executor import (
    ToolResult,
    ToolSchema,
    ToolExecutor,
    LocalToolExecutor,
    ToolRegistry,
    create_local_executor,
    create_tool_registry,
)

# V9 Async Drivers (preferred)
from .async_claude_driver import AsyncClaudeDriver, AsyncClaudeDriverConfig, create_async_claude_driver
from .async_gemini_driver import AsyncGeminiDriver, AsyncGeminiDriverConfig, create_async_gemini_driver
from .async_kimi_driver import AsyncKimiDriver, AsyncKimiDriverConfig
from .async_deepseek_driver import AsyncDeepSeekDriver, AsyncDeepSeekDriverConfig
from .async_glm_driver import AsyncGLMDriver, AsyncGLMDriverConfig
from .async_factory import AsyncDriverFactory, get_driver_factory, set_driver_factory, create_driver_factory

# Legacy sync drivers (backwards compatibility)
from .gemini_driver_v7 import GeminiDriverV7
from .claude_driver_hybrid import ClaudeDriverHybrid
from .glm_driver_hybrid import GLMDriverHybrid

__all__ = [
    # V11 Abstraction Layer (F31)
    "DriverProtocol",
    "DriverResponse",
    "DriverResponseStatus",
    "ToolCall",
    "StreamChunk",
    "SessionProtocol",
    "ToolExecutorProtocol",
    "BaseAsyncDriver",
    "GeminiCLIAdapter",
    "ClaudeCLIAdapter",
    "GLMAPIAdapter",
    "create_cli_adapter",
    # V11 Session Abstraction (F32)
    "SessionMode",
    "SessionState",
    "SessionMetadata",
    "SessionManager",
    "CLISessionManager",
    "SessionRegistry",
    "get_session_registry",
    # V11 Tool Abstraction (F33)
    "ToolResult",
    "ToolSchema",
    "ToolExecutor",
    "LocalToolExecutor",
    "ToolRegistry",
    "create_local_executor",
    "create_tool_registry",
    # V9 Async (preferred)
    "AsyncClaudeDriver",
    "AsyncClaudeDriverConfig",
    "create_async_claude_driver",
    "AsyncGeminiDriver",
    "AsyncGeminiDriverConfig",
    "create_async_gemini_driver",
    "AsyncKimiDriver",
    "AsyncKimiDriverConfig",
    "AsyncDeepSeekDriver",
    "AsyncDeepSeekDriverConfig",
    "AsyncGLMDriver",
    "AsyncGLMDriverConfig",
    "AsyncDriverFactory",
    "get_driver_factory",
    "set_driver_factory",
    "create_driver_factory",
    # Legacy sync
    "GeminiDriverV7",
    "ClaudeDriverHybrid",
    "GLMDriverHybrid",
]
