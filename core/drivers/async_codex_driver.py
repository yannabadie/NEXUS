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
from datetime import datetime
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
        super().__init__(
            provider="codex",
            model=config.model,
            timeout=config.timeout,
        )
        self.config = config
        self._client = None

    async def _get_client(self):
        """Get or create OpenAI client."""
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
        return "codex"

    @property
    def model(self) -> str:
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
        """
        Invoke GPT-5.2-Codex via Responses API.

        Args:
            prompt: The prompt to send
            session_id: Optional session identifier
            system_prompt: Optional system prompt
            tools: Optional function definitions for function calling
            isolated_env: Not used for API
            timeout: Optional timeout override

        Returns:
            DriverResponse with content and metadata
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
        """
        Stream response from GPT-5.2-Codex.

        Uses the streaming capability of the Responses API.
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
        """Cancel not directly supported by API."""
        return False

    async def health_check(self) -> bool:
        """Check if OpenAI API is available."""
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
        """Close client."""
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
        super().__init__(
            provider="codex",
            model=config.model,
            timeout=config.timeout,
        )
        self.config = config
        self._client = None

    async def _get_client(self):
        """Get or create OpenAI client."""
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
        """Invoke using Chat Completions API."""
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
        """Stream using Chat Completions."""
        response = await self.invoke(prompt, **kwargs)
        yield StreamChunk(
            content=response.content,
            is_final=True,
            latency_ms=response.latency_ms,
        )

    async def cancel(self, session_id: Optional[str] = None) -> bool:
        return False

    async def health_check(self) -> bool:
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
