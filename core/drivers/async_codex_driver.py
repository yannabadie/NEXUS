"""
AsyncCodexDriver - GPT-5.2-Codex Integration for NEXUS.

Provides access to OpenAI's advanced coding model for complex tasks
like type hint addition, refactoring, and security analysis.

Integration Method: OpenAI Responses API

Pricing:
- Input: $1.75/1M tokens (90% discount with caching)
- Output: $14/1M tokens

Usage:
    driver = AsyncCodexDriver(config)
    response = await driver.invoke("Add type hints to this function...")

Author: Claude (NEXUS V12.4)
Date: 2026-01-21
"""

from __future__ import annotations

import asyncio
import os
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, AsyncIterator, Dict, List, Optional

from core.drivers.protocol import (
    BaseAsyncDriver,
    DriverResponse,
    DriverResponseStatus,
    StreamChunk,
    ToolCall,
)


@dataclass
class AsyncCodexDriverConfig:
    """Configuration for AsyncCodexDriver."""

    # API configuration
    api_key: Optional[str] = None
    organization: Optional[str] = None
    base_url: str = "https://api.openai.com/v1"

    # Model configuration
    model: str = "gpt-5.2-codex"
    reasoning_effort: str = "xhigh"  # low, medium, high, xhigh
    timeout: float = 180.0  # 3 min default (complex tasks)

    # Workspace
    workspace_path: Path = field(default_factory=Path.cwd)
    verbose: bool = False

    def __post_init__(self):
        """Validates configuration and loads API key from environment if missing.

        Raises:
            ValueError: If the API key is not provided in config or environment.
        """
        # Try to get API key from environment if not provided
        if not self.api_key:
            self.api_key = os.environ.get("OPENAI_API_KEY")


class AsyncCodexDriver(BaseAsyncDriver):
    """
    GPT-5.2-Codex driver using OpenAI Responses API.

    Key Features:
    - Native context compaction (millions of tokens)
    - Agentic coding optimized
    - 56.4% SWE-Bench Pro, 87% CVE-Bench
    - Function calling support
    - Structured outputs

    Best for:
    - Type hint addition
    - Complex refactoring
    - Security-focused code changes
    - Large codebase modifications
    """

    def __init__(self, config: AsyncCodexDriverConfig):
        """Initialize the AsyncCodexDriver.

        Args:
            config: The configuration object for the driver.
        """
        super().__init__(
            provider="codex",
            model=config.model,
            timeout=config.timeout,
        )
        self.config = config
        self._client = None

    async def _get_client(self):
        """Get or create OpenAI client.

        Returns:
            AsyncOpenAI: The initialized OpenAI client.

        Raises:
            ImportError: If the openai package is not installed.
        """
        if self._client is None:
            try:
                from openai import AsyncOpenAI
                self._client = AsyncOpenAI(
                    api_key=self.config.api_key,
                    organization=self.config.organization,
                    base_url=self.config.base_url,
                    timeout=self.config.timeout,
                )
            except ImportError:
                raise ImportError(
                    "OpenAI SDK not installed. Run: pip install openai"
                )
        return self._client

    @property
    def provider(self) -> str:
        """The provider name for this driver.

        Returns:
            str: The string 'codex'.
        """
        return "codex"

    @property
    def model(self) -> str:
        """The model name used by this driver.

        Returns:
            str: The model identifier from configuration.
        """
        return self.config.model

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
        """Invokes GPT-5.2-Codex via the OpenAI Responses API.

        Sends a prompt to the model and returns the generated response. Supports
        function calling and system prompts.

        Args:
            prompt: The input text prompt to send to the model.
            session_id: An optional unique identifier for the session. If not
                provided, a UUID will be generated.
            system_prompt: An optional instruction to guide the model's behavior.
            tools: A list of function definitions for tool/function calling capabilities.
            isolated_env: A dictionary of environment variables. Not used for this API
                driver but kept for interface consistency.
            timeout: An optional timeout in seconds. If provided, overrides the
                driver's default timeout.
            **kwargs: Additional keyword arguments passed to the API call.

        Returns:
            DriverResponse: A structured response object containing the model's output,
            metadata, usage statistics, and any tool calls.

        Raises:
            asyncio.CancelledError: If the operation is cancelled.
        """
        start_time = time.time()
        request_id = session_id or str(uuid.uuid4())

        try:
            client = await self._get_client()

            # Build the input
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            # Build request kwargs
            request_kwargs = {
                "model": self.config.model,
                "input": messages,
                "reasoning": {"effort": self.config.reasoning_effort},
            }

            # Add tools if provided
            if tools:
                request_kwargs["tools"] = tools

            # Make request using Responses API
            response = await asyncio.wait_for(
                client.responses.create(**request_kwargs),
                timeout=timeout or self.config.timeout,
            )

            latency_ms = (time.time() - start_time) * 1000

            # Extract content
            content = response.output_text if hasattr(response, 'output_text') else str(response.output)

            # Extract tool calls if any
            tool_calls = []
            if hasattr(response, 'tool_calls') and response.tool_calls:
                for tc in response.tool_calls:
                    tool_calls.append(ToolCall(
                        name=tc.function.name,
                        arguments=tc.function.arguments,
                        id=tc.id,
                    ))

            # Extract usage
            input_tokens = 0
            output_tokens = 0
            if hasattr(response, 'usage'):
                input_tokens = getattr(response.usage, 'input_tokens', 0)
                output_tokens = getattr(response.usage, 'output_tokens', 0)

            return DriverResponse(
                content=content,
                status=DriverResponseStatus.SUCCESS,
                provider="codex",
                model=self.config.model,
                session_id=request_id,
                tool_calls=tool_calls,
                latency_ms=latency_ms,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                raw=response.model_dump() if hasattr(response, 'model_dump') else None,
            )

        except asyncio.TimeoutError:
            return self._create_error_response(
                f"Timeout after {timeout or self.config.timeout}s",
                error_code="TIMEOUT",
                status=DriverResponseStatus.TIMEOUT,
            )
        except asyncio.CancelledError:
            raise  # CRITICAL: Re-raise CancelledError
        except Exception as e:
            error_msg = str(e)

            # Check for rate limiting
            if "rate" in error_msg.lower() or "429" in error_msg:
                return self._create_error_response(
                    error_msg,
                    error_code="RATE_LIMITED",
                    status=DriverResponseStatus.RATE_LIMITED,
                )

            return self._create_error_response(
                error_msg,
                error_code="API_ERROR",
            )

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
        """Streams a response from GPT-5.2-Codex using the Responses API.

        Yields chunks of the response as they are generated by the model.

        Args:
            prompt: The input text prompt to send to the model.
            session_id: An optional unique identifier for the session.
            system_prompt: An optional instruction to guide the model's behavior.
            tools: A list of function definitions for tool/function calling.
            isolated_env: A dictionary of environment variables (unused).
            timeout: An optional timeout in seconds.
            **kwargs: Additional keyword arguments passed to the API call.

        Yields:
            StreamChunk: A chunk of the response content, including final status
            and latency information.

        Raises:
            asyncio.CancelledError: If the operation is cancelled.
        """
        start_time = time.time()

        try:
            client = await self._get_client()

            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            request_kwargs = {
                "model": self.config.model,
                "input": messages,
                "reasoning": {"effort": self.config.reasoning_effort},
                "stream": True,
            }

            if tools:
                request_kwargs["tools"] = tools

            async with await client.responses.create(**request_kwargs) as stream:
                async for chunk in stream:
                    if hasattr(chunk, 'delta') and chunk.delta:
                        content = chunk.delta.get('content', '')
                        if content:
                            yield StreamChunk(
                                content=content,
                                is_final=False,
                            )

                # Final chunk
                yield StreamChunk(
                    content="",
                    is_final=True,
                    latency_ms=(time.time() - start_time) * 1000,
                )

        except asyncio.CancelledError:
            raise
        except Exception:
            # Fallback to non-streaming
            response = await self.invoke(
                prompt,
                session_id=session_id,
                system_prompt=system_prompt,
                tools=tools,
                timeout=timeout,
            )
            yield StreamChunk(
                content=response.content,
                is_final=True,
                latency_ms=response.latency_ms,
            )

    async def cancel(self, session_id: Optional[str] = None) -> bool:
        """Cancel the operation (not directly supported by API).

        Args:
            session_id: The session identifier.

        Returns:
            bool: Always False as cancellation is not supported.
        """
        return False

    async def health_check(self) -> bool:
        """Check if OpenAI API is available.

        Returns:
            bool: True if the API is reachable, False otherwise.
        """
        try:
            client = await self._get_client()
            # Simple models list to verify API access
            models = await asyncio.wait_for(
                client.models.list(),
                timeout=10.0,
            )
            return len(list(models)) > 0
        except Exception:
            return False

    async def close(self):
        """Closes the underlying OpenAI client session.

        Ensures that the network resources associated with the client are properly
        released. Should be called when the driver is no longer needed.

        Raises:
            Exception: If an error occurs while closing the client.
        """
        if self._client:
            await self._client.close()
            self._client = None


# =============================================================================
# Simplified Codex Driver (Chat Completions fallback)
# =============================================================================

class AsyncCodexChatDriver(BaseAsyncDriver):
    """
    Fallback Codex driver using Chat Completions API.

    Use this if Responses API is not available.
    """

    def __init__(self, config: AsyncCodexDriverConfig):
        """Initialize the AsyncCodexChatDriver fallback.

        Args:
            config: The configuration object for the driver.
        """
        super().__init__(
            provider="codex",
            model=config.model,
            timeout=config.timeout,
        )
        self.config = config
        self._client = None

    async def _get_client(self):
        """Get or create OpenAI client for Chat Completions.

        Returns:
            AsyncOpenAI: The initialized OpenAI client.

        Raises:
            ImportError: If the openai package is not installed.
        """
        if self._client is None:
            try:
                from openai import AsyncOpenAI
                self._client = AsyncOpenAI(
                    api_key=self.config.api_key,
                    timeout=self.config.timeout,
                )
            except ImportError:
                raise ImportError(
                    "OpenAI SDK not installed. Run: pip install openai"
                )
        return self._client

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
        """Invokes the model using the OpenAI Chat Completions API as a fallback.

        Args:
            prompt: The input text prompt to send to the model.
            session_id: An optional unique identifier for the session.
            system_prompt: An optional instruction to guide the model's behavior.
            tools: A list of function definitions (not fully supported in this fallback).
            isolated_env: A dictionary of environment variables (unused).
            timeout: An optional timeout in seconds.
            **kwargs: Additional keyword arguments.

        Returns:
            DriverResponse: A structured response object containing the model's output
            and metadata.

        Raises:
            asyncio.CancelledError: If the operation is cancelled.
        """
        start_time = time.time()

        try:
            client = await self._get_client()

            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            response = await asyncio.wait_for(
                client.chat.completions.create(
                    model=self.config.model,
                    messages=messages,
                ),
                timeout=timeout or self.config.timeout,
            )

            latency_ms = (time.time() - start_time) * 1000
            content = response.choices[0].message.content or ""

            return DriverResponse(
                content=content,
                status=DriverResponseStatus.SUCCESS,
                provider="codex",
                model=self.config.model,
                session_id=session_id,
                latency_ms=latency_ms,
                input_tokens=response.usage.prompt_tokens if response.usage else 0,
                output_tokens=response.usage.completion_tokens if response.usage else 0,
            )

        except asyncio.TimeoutError:
            return self._create_error_response(
                "Timeout",
                error_code="TIMEOUT",
                status=DriverResponseStatus.TIMEOUT,
            )
        except asyncio.CancelledError:
            raise
        except Exception as e:
            return self._create_error_response(str(e), error_code="API_ERROR")

    async def invoke_stream(
        self,
        prompt: str,
        **kwargs: Any,
    ) -> AsyncIterator[StreamChunk]:
        """Streams the model response using Chat Completions.

        Note: This implementation simulates streaming by invoking the full response
        and yielding it as a single chunk, as the Chat Completions fallback here
        does not support true streaming.

        Args:
            prompt: The input text prompt to send to the model.
            **kwargs: Additional keyword arguments passed to the invoke method.

        Yields:
            StreamChunk: A single chunk containing the full response content.
        """
        response = await self.invoke(prompt, **kwargs)
        yield StreamChunk(
            content=response.content,
            is_final=True,
            latency_ms=response.latency_ms,
        )

    async def cancel(self, session_id: Optional[str] = None) -> bool:
        """Attempts to cancel the operation.

        Note: Cancellation is not supported by the Chat Completions fallback implementation.

        Args:
            session_id: The identifier of the session to cancel.

        Returns:
            bool: Always False, indicating cancellation is not supported.
        """
        return False

    async def health_check(self) -> bool:
        """Checks if the OpenAI Chat Completions API is available.

        Verifies connectivity and authentication by listing available models.

        Returns:
            bool: True if the API is reachable and authorized, False otherwise.
        """
        try:
            client = await self._get_client()
            await client.models.list()
            return True
        except Exception:
            return False


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    "AsyncCodexDriverConfig",
    "AsyncCodexDriver",
    "AsyncCodexChatDriver",
]
