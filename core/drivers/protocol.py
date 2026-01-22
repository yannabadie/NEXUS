"""
Driver Protocol - V11 Abstraction Layer for CLI/API Independence.

F31 Fix: Decouples orchestration from CLI-bound implementation.

This protocol defines the contract that ALL drivers must implement,
whether CLI-based (current) or API-based (future).

Benefits:
1. Orchestration code works with any driver implementation
2. Can swap CLI for API without changing HiveMind/Swarm/FSM code
3. Enables testing with mock drivers
4. Prepares for CEREBRO UI backend (needs API drivers for WebSocket)

Architecture:
```
                    ┌──────────────────┐
                    │  DriverProtocol  │ (ABC)
                    └────────┬─────────┘
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
     ┌────────────────┐ ┌────────────────┐ ┌────────────────┐
     │ AsyncCLIDriver │ │ AsyncAPIDriver │ │   MockDriver   │
     │  (subprocess)  │ │   (httpx)      │ │   (testing)    │
     └────────────────┘ └────────────────┘ └────────────────┘
              │              │              │
     ┌────────┴────────┐    ...           ...
     ▼                 ▼
  Gemini CLI      Claude CLI
```

Usage:
    from core.drivers.protocol import DriverProtocol, DriverResponse

    # Any driver implementing DriverProtocol can be used
    async def run_agent(driver: DriverProtocol, prompt: str):
        response = await driver.invoke(prompt)
        return response.content

Author: Claude (NEXUS V11)
Date: 2025-12-15
"""

from __future__ import annotations

import abc
from dataclasses import dataclass, field
from typing import (
    AsyncIterator,
    Dict,
    List,
    Optional,
    Any,
    Protocol,
    runtime_checkable,
)
from datetime import datetime
from enum import Enum, auto


# =============================================================================
# Response Types
# =============================================================================


class DriverResponseStatus(Enum):
    """Status of a driver response."""

    SUCCESS = auto()
    ERROR = auto()
    TIMEOUT = auto()
    CANCELLED = auto()
    RATE_LIMITED = auto()


@dataclass
class ToolCall:
    """Represents a tool/function call from the LLM."""

    name: str
    arguments: Dict[str, Any]
    id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Converts the ToolCall instance to a dictionary.

        Returns:
            Dict[str, Any]: A dictionary representation of the ToolCall, containing
                'name', 'arguments', and 'id' keys.
        """
        return {
            "name": self.name,
            "arguments": self.arguments,
            "id": self.id,
        }


@dataclass
class DriverResponse:
    """Unified response format from any driver implementation.

    Abstracts away CLI vs API response differences:
    - CLI: Parses JSON from stdout, extracts tool calls from message
    - API: Parses response JSON directly, tool calls in structured format

    Both result in the same DriverResponse for orchestration code.

    Attributes:
        content: The text content of the response.
        status: The status of the response (SUCCESS, ERROR, etc.).
        model: The model identifier used for the response.
        provider: The provider identifier (e.g., "gemini", "claude").
        session_id: The session ID associated with the response.
        tool_calls: A list of tool calls made by the model.
        latency_ms: The time taken to generate the response in milliseconds.
        input_tokens: The number of tokens in the input prompt.
        output_tokens: The number of tokens in the generated response.
        error_message: A descriptive error message if status is not SUCCESS.
        error_code: A specific error code if status is not SUCCESS.
        raw: The raw response data for debugging purposes.
        timestamp: The timestamp when the response was created.
    """

    # Core content
    content: str
    status: DriverResponseStatus = DriverResponseStatus.SUCCESS

    # Metadata
    model: Optional[str] = None
    provider: str = "unknown"  # "gemini" or "claude"
    session_id: Optional[str] = None

    # Tool calls (if any)
    tool_calls: List[ToolCall] = field(default_factory=list)

    # Timing and metrics
    latency_ms: float = 0.0
    input_tokens: int = 0
    output_tokens: int = 0

    # Error information (if status != SUCCESS)
    error_message: Optional[str] = None
    error_code: Optional[str] = None

    # Raw response (for debugging)
    raw: Optional[Dict[str, Any]] = None

    # Timestamp
    timestamp: datetime = field(default_factory=datetime.now)

    @property
    def is_success(self) -> bool:
        """Check if response was successful."""
        return self.status == DriverResponseStatus.SUCCESS

    @property
    def has_tool_calls(self) -> bool:
        """Check if response contains tool calls."""
        return len(self.tool_calls) > 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization.

        Returns:
            Dict[str, Any]: A dictionary containing all response fields including
                content, status, metadata, tool calls, and error information.
        """
        return {
            "content": self.content,
            "status": self.status.name,
            "model": self.model,
            "provider": self.provider,
            "session_id": self.session_id,
            "tool_calls": [tc.to_dict() for tc in self.tool_calls],
            "latency_ms": self.latency_ms,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "error_message": self.error_message,
            "error_code": self.error_code,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class StreamChunk:
    """A chunk of streamed response.

    Attributes:
        content: The text content of the chunk.
        is_final: Whether this is the last chunk in the stream.
        tool_call: Optional tool call included in this chunk.
        latency_ms: The total latency (only populated in final chunk).
        input_tokens: The total input tokens (only populated in final chunk).
        output_tokens: The total output tokens (only populated in final chunk).
    """

    content: str
    is_final: bool = False
    tool_call: Optional[ToolCall] = None

    # Metadata (only populated in final chunk)
    latency_ms: float = 0.0
    input_tokens: int = 0
    output_tokens: int = 0


# =============================================================================
# Driver Protocol (ABC)
# =============================================================================


@runtime_checkable
class DriverProtocol(Protocol):
    """
    Protocol that ALL drivers must implement.

    This is the contract between orchestration code and driver implementations.
    Whether a driver uses CLI subprocess or direct API calls, it must implement
    these methods with the same signature.

    F31: This protocol enables CLI/API independence.
    """

    @property
    def provider(self) -> str:
        """
        Provider identifier ("gemini" or "claude").

        Used for routing, metrics, and logging.
        """
        ...

    @property
    def model(self) -> str:
        """
        Model identifier (e.g., "gemini-3-pro-preview", "claude-sonnet-4-5-20250929").

        Used for routing and metrics.
        """
        ...

    async def invoke(
        self,
        prompt: str,
        *,
        session_id: Optional[str] = None,
        system_prompt: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        isolated_env: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None,
        **kwargs: Any,
    ) -> DriverResponse:
        """
        Invoke the LLM and return the complete response.

        Args:
            prompt: The user prompt/message to send
            session_id: Optional session ID for context persistence
            system_prompt: Optional system prompt override
            tools: Optional list of tools to make available
            isolated_env: Optional environment dict for CLI isolation (V9.7.1)
            timeout: Optional timeout override in seconds
            **kwargs: Additional driver-specific options

        Returns:
            DriverResponse with content, status, and metadata

        Raises:
            asyncio.TimeoutError: If timeout exceeded
            asyncio.CancelledError: If cancelled (MUST be re-raised)
        """
        ...

    async def invoke_stream(
        self,
        prompt: str,
        *,
        session_id: Optional[str] = None,
        system_prompt: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        isolated_env: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None,
        **kwargs: Any,
    ) -> AsyncIterator[StreamChunk]:
        """Invoke the LLM and stream the response.

        Args:
            prompt: The user prompt/message to send.
            session_id: Optional session ID for context persistence.
            system_prompt: Optional system prompt override.
            tools: Optional list of tools to make available.
            isolated_env: Optional environment dict for CLI isolation (V9.7.1).
            timeout: Optional timeout override in seconds.
            **kwargs: Additional driver-specific options.

        Yields:
            StreamChunk: StreamChunk objects as they become available.
                The final chunk will have is_final=True.

        Raises:
            asyncio.TimeoutError: If timeout exceeded.
            asyncio.CancelledError: If cancelled (MUST be re-raised).
        """
        ...
        yield StreamChunk(content="")  # Make this a generator

    async def cancel(self, session_id: Optional[str] = None) -> bool:
        """
        Cancel an ongoing invocation.

        Args:
            session_id: If provided, cancel specific session.
                       If None, cancel all active invocations.

        Returns:
            True if cancellation was successful
        """
        ...

    async def health_check(self) -> bool:
        """
        Check if the driver/provider is healthy.

        Used by circuit breaker and monitoring.

        Returns:
            True if healthy and ready to accept requests
        """
        ...


# =============================================================================
# Session Protocol (F32 preparation)
# =============================================================================


@runtime_checkable
class SessionProtocol(Protocol):
    """
    Protocol for session management abstraction.

    F32: Decouples session handling from CLI-specific features like --resume.

    CLI sessions: Use --resume flag, session stored in ~/.gemini/tmp/
    API sessions: Use conversation_id in request body
    """

    @property
    def session_id(self) -> str:
        """Unique session identifier."""
        ...

    @property
    def is_active(self) -> bool:
        """Whether session is currently active."""
        ...

    async def start(self) -> str:
        """Starts a new session.

        Initializes a new session context, generating a unique identifier and setting
        up any necessary state or resources required for the session.

        Returns:
            str: The unique identifier (ID) of the newly created session.

        Raises:
            RuntimeError: If a session is already active and cannot be overwritten.
        """
        ...

    async def resume(self, session_id: str) -> bool:
        """Resumes an existing session.

        Attempts to restore the state of a previously active session using its
        identifier.

        Args:
            session_id: The unique identifier of the session to resume.

        Returns:
            bool: True if the session was successfully found and resumed, False otherwise.

        Raises:
            ValueError: If the provided session_id format is invalid.
        """
        ...

    async def end(self) -> None:
        """Ends the current session.

        Terminates the active session, performing any necessary cleanup such as
        saving state, releasing resources, or logging completion.

        Raises:
            RuntimeError: If no session is currently active to end.
        """
        ...

    def get_context_for_driver(self) -> Dict[str, Any]:
        """Retrieves session context formatted for the driver.

        Constructs a dictionary containing the necessary context information required
        by the driver to maintain continuity, such as resume flags for CLI drivers
        or conversation IDs for API drivers.

        Returns:
            Dict[str, Any]: A dictionary containing context information.
                For example:
                - CLI: {"resume_flag": "--resume latest"}
                - API: {"conversation_id": "123-abc-456"}

        Raises:
            RuntimeError: If the session is not active or context cannot be generated.
        """
        ...


# =============================================================================
# Tool Executor Protocol (F33 preparation)
# =============================================================================


@runtime_checkable
class ToolExecutorProtocol(Protocol):
    """
    Protocol for tool execution abstraction.

    F33: Decouples tool execution from CLI-provided tools.

    CLI: Tools like read_file, grep are executed by the CLI
    API: We must implement tool execution ourselves
    """

    async def execute(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        *,
        workspace_path: Optional[str] = None,
        timeout: float = 30.0,
    ) -> Dict[str, Any]:
        """
        Execute a tool and return the result.

        Args:
            tool_name: Name of the tool to execute (e.g., "read_file")
            arguments: Tool arguments
            workspace_path: Working directory for file operations
            timeout: Maximum execution time

        Returns:
            Tool result as dictionary
        """
        ...

    def list_available_tools(self) -> List[str]:
        """
        List all available tools.

        Returns:
            List of tool names
        """
        ...

    def get_tool_schema(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """
        Get JSON schema for a tool.

        Args:
            tool_name: Tool to get schema for

        Returns:
            JSON schema dict, or None if tool not found
        """
        ...


# =============================================================================
# Abstract Base Classes (for implementation guidance)
# =============================================================================


class BaseAsyncDriver(abc.ABC):
    """
    Abstract base class for async drivers.

    Provides common functionality and enforces DriverProtocol.
    Implementations should inherit from this class.
    """

    def __init__(
        self,
        provider: str,
        model: str,
        timeout: float = 300.0,
    ):
        """Initializes the BaseAsyncDriver.

        Args:
            provider: The name of the AI provider (e.g., "gemini", "claude").
            model: The specific model identifier to use.
            timeout: The default timeout for requests in seconds. Defaults to 300.0.
        """
        self._provider = provider
        self._model = model
        self._timeout = timeout

    @property
    def provider(self) -> str:
        return self._provider

    @property
    def model(self) -> str:
        return self._model

    @abc.abstractmethod
    async def invoke(
        self,
        prompt: str,
        *,
        session_id: Optional[str] = None,
        system_prompt: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        isolated_env: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None,
        **kwargs: Any,
    ) -> DriverResponse:
        """Invoke the LLM and return the complete response.

        Args:
            prompt: The user prompt/message to send.
            session_id: Optional session ID for context persistence.
            system_prompt: Optional system prompt override.
            tools: Optional list of tools to make available.
            isolated_env: Optional environment dict for CLI isolation (V9.7.1).
            timeout: Optional timeout override in seconds.
            **kwargs: Additional driver-specific options.

        Returns:
            DriverResponse: The complete response containing content, status, and metadata.

        Raises:
            asyncio.TimeoutError: If timeout exceeded.
            asyncio.CancelledError: If cancelled (MUST be re-raised).
        """
        ...

    @abc.abstractmethod
    async def invoke_stream(
        self,
        prompt: str,
        *,
        session_id: Optional[str] = None,
        system_prompt: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        isolated_env: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None,
        **kwargs: Any,
    ) -> AsyncIterator[StreamChunk]:
        """Invoke the LLM and stream the response.

        Args:
            prompt: The user prompt/message to send.
            session_id: Optional session ID for context persistence.
            system_prompt: Optional system prompt override.
            tools: Optional list of tools to make available.
            isolated_env: Optional environment dict for CLI isolation (V9.7.1).
            timeout: Optional timeout override in seconds.
            **kwargs: Additional driver-specific options.

        Yields:
            StreamChunk: StreamChunk objects as they become available.
                The final chunk will have is_final=True.

        Raises:
            asyncio.TimeoutError: If timeout exceeded.
            asyncio.CancelledError: If cancelled (MUST be re-raised).
        """
        ...
        yield StreamChunk(content="")  # pragma: no cover

    @abc.abstractmethod
    async def cancel(self, session_id: Optional[str] = None) -> bool:
        """Cancel an ongoing invocation.

        Args:
            session_id: If provided, cancel specific session.
                If None, cancel all active invocations.

        Returns:
            bool: True if cancellation was successful, False otherwise.

        Raises:
            Exception: If cancellation fails due to driver error.
        """
        ...

    async def health_check(self) -> bool:
        """Default health check - can be overridden.

        Returns:
            bool: True if healthy and ready to accept requests.
                Subclasses should implement actual health checking (API ping, etc.).
        """
        return True

    def _create_error_response(
        self,
        error_message: str,
        error_code: str = "DRIVER_ERROR",
        status: DriverResponseStatus = DriverResponseStatus.ERROR,
    ) -> DriverResponse:
        """Creates a standardized error response.

        Args:
            error_message: A descriptive error message.
            error_code: A specific error code for categorization. Defaults to "DRIVER_ERROR".
            status: The status enum to assign. Defaults to DriverResponseStatus.ERROR.

        Returns:
            DriverResponse: A DriverResponse object populated with the error details
                and the current provider/model context.
        """
        return DriverResponse(
            content="",
            status=status,
            provider=self._provider,
            model=self._model,
            error_message=error_message,
            error_code=error_code,
        )


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    # Response types
    "DriverResponseStatus",
    "DriverResponse",
    "ToolCall",
    "StreamChunk",
    # Protocols
    "DriverProtocol",
    "SessionProtocol",
    "ToolExecutorProtocol",
    # Base class
    "BaseAsyncDriver",
]
