"""
AsyncOpenCodeDriver - OpenCode/Zen Integration for NEXUS.

Provides access to OpenCode Zen models (GLM 4.7, Grok Code Fast, etc.)
for simple coding tasks like docstring generation.

Integration Method: HTTP API (OpenCode server mode)

Usage:
    driver = AsyncOpenCodeDriver(config)
    response = await driver.invoke("Add docstring to this function...")

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

import httpx

from core.drivers.protocol import (
    BaseAsyncDriver,
    DriverResponse,
    DriverResponseStatus,
    StreamChunk,
    ToolCall,
)


@dataclass
class AsyncOpenCodeDriverConfig:
    """Configuration for AsyncOpenCodeDriver."""

    # Server configuration
    server_url: str = "http://localhost:5173"  # OpenCode server default
    api_key: Optional[str] = None  # Zen API key

    # Model configuration
    model: str = "glm-4.7"  # Free model on Zen
    timeout: float = 120.0  # 2 min default (simple tasks)

    # Workspace
    workspace_path: Path = field(default_factory=Path.cwd)
    verbose: bool = False

    def __post_init__(self):
        # Try to get API key from environment if not provided
        if not self.api_key:
            self.api_key = os.environ.get("OPENCODE_ZEN_API_KEY")


class AsyncOpenCodeDriver(BaseAsyncDriver):
    """
    OpenCode driver using HTTP API.

    OpenCode can run in server mode, exposing an HTTP API.
    This driver communicates with that server for LLM invocations.

    Supported Models (Zen):
    - glm-4.7 (FREE - limited time)
    - grok-code-fast-1 (FREE - limited time)
    - minimax-m2.1 (FREE - limited time)

    Best for:
    - Simple coding tasks (docstrings, comments)
    - Quick iterations
    - Cost-sensitive operations
    """

    def __init__(self, config: AsyncOpenCodeDriverConfig):
        super().__init__(
            provider="opencode",
            model=config.model,
            timeout=config.timeout,
        )
        self.config = config
        self._client: Optional[httpx.AsyncClient] = None
        self._active_requests: Dict[str, asyncio.Task] = {}

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None or self._client.is_closed:
            headers = {}
            if self.config.api_key:
                headers["Authorization"] = f"Bearer {self.config.api_key}"

            self._client = httpx.AsyncClient(
                base_url=self.config.server_url,
                headers=headers,
                timeout=httpx.Timeout(self.config.timeout),
            )
        return self._client

    @property
    def provider(self) -> str:
        return "opencode"

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
        Invoke OpenCode via HTTP API.

        Args:
            prompt: The prompt to send
            session_id: Optional session identifier
            system_prompt: Optional system prompt
            tools: Not used (OpenCode handles tools internally)
            isolated_env: Not used for HTTP API
            timeout: Optional timeout override

        Returns:
            DriverResponse with content and metadata
        """
        start_time = time.time()
        request_id = session_id or str(uuid.uuid4())

        try:
            client = await self._get_client()

            # Build request payload
            payload = {
                "prompt": prompt,
                "model": self.config.model,
            }

            if system_prompt:
                payload["system"] = system_prompt

            # Make request
            response = await asyncio.wait_for(
                client.post("/api/invoke", json=payload),
                timeout=timeout or self.config.timeout,
            )

            latency_ms = (time.time() - start_time) * 1000

            if response.status_code == 200:
                data = response.json()
                return DriverResponse(
                    content=data.get("content", ""),
                    status=DriverResponseStatus.SUCCESS,
                    provider="opencode",
                    model=self.config.model,
                    session_id=request_id,
                    latency_ms=latency_ms,
                    input_tokens=data.get("input_tokens", 0),
                    output_tokens=data.get("output_tokens", 0),
                    raw=data,
                )
            elif response.status_code == 429:
                return self._create_error_response(
                    "Rate limited",
                    error_code="RATE_LIMITED",
                    status=DriverResponseStatus.RATE_LIMITED,
                )
            else:
                return self._create_error_response(
                    f"HTTP {response.status_code}: {response.text}",
                    error_code=f"HTTP_{response.status_code}",
                )

        except asyncio.TimeoutError:
            return self._create_error_response(
                f"Timeout after {timeout or self.config.timeout}s",
                error_code="TIMEOUT",
                status=DriverResponseStatus.TIMEOUT,
            )
        except asyncio.CancelledError:
            raise  # CRITICAL: Re-raise CancelledError
        except httpx.ConnectError:
            return self._create_error_response(
                f"Cannot connect to OpenCode server at {self.config.server_url}",
                error_code="CONNECTION_ERROR",
            )
        except Exception as e:
            return self._create_error_response(
                str(e),
                error_code="UNKNOWN_ERROR",
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
        Stream response from OpenCode.

        Note: Falls back to non-streaming if server doesn't support SSE.
        """
        start_time = time.time()

        try:
            client = await self._get_client()

            payload = {
                "prompt": prompt,
                "model": self.config.model,
                "stream": True,
            }

            if system_prompt:
                payload["system"] = system_prompt

            async with client.stream(
                "POST",
                "/api/invoke/stream",
                json=payload,
                timeout=timeout or self.config.timeout,
            ) as response:
                if response.status_code != 200:
                    # Fallback to non-streaming
                    full_response = await self.invoke(
                        prompt,
                        session_id=session_id,
                        system_prompt=system_prompt,
                        timeout=timeout,
                    )
                    yield StreamChunk(
                        content=full_response.content,
                        is_final=True,
                        latency_ms=full_response.latency_ms,
                    )
                    return

                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        import json
                        try:
                            data = json.loads(line[6:])
                            is_final = data.get("done", False)
                            yield StreamChunk(
                                content=data.get("content", ""),
                                is_final=is_final,
                                latency_ms=(time.time() - start_time) * 1000 if is_final else 0,
                            )
                            if is_final:
                                return
                        except json.JSONDecodeError:
                            continue

        except asyncio.CancelledError:
            raise
        except Exception:
            # Fallback to non-streaming on any error
            full_response = await self.invoke(
                prompt,
                session_id=session_id,
                system_prompt=system_prompt,
                timeout=timeout,
            )
            yield StreamChunk(
                content=full_response.content,
                is_final=True,
                latency_ms=full_response.latency_ms,
            )

    async def cancel(self, session_id: Optional[str] = None) -> bool:
        """Cancel active request."""
        if session_id and session_id in self._active_requests:
            task = self._active_requests.pop(session_id)
            task.cancel()
            return True
        return False

    async def health_check(self) -> bool:
        """Check if OpenCode server is available."""
        try:
            client = await self._get_client()
            response = await asyncio.wait_for(
                client.get("/health"),
                timeout=5.0,
            )
            return response.status_code == 200
        except Exception:
            return False

    async def close(self):
        """Close HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None


# =============================================================================
# CLI Fallback (if HTTP server not available)
# =============================================================================

class AsyncOpenCodeCLIDriver(BaseAsyncDriver):
    """
    OpenCode driver using CLI subprocess.

    Fallback when HTTP server is not running.
    Uses: opencode --model glm-4.7 "prompt"
    """

    def __init__(self, config: AsyncOpenCodeDriverConfig):
        super().__init__(
            provider="opencode",
            model=config.model,
            timeout=config.timeout,
        )
        self.config = config
        self._cli_path = "opencode"

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
        """Invoke OpenCode via CLI."""
        start_time = time.time()

        cmd = [
            self._cli_path,
            "--model", self.config.model,
            "--non-interactive",
            prompt,
        ]

        if system_prompt:
            cmd.extend(["--system", system_prompt])

        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=isolated_env or os.environ.copy(),
            )

            stdout, stderr = await asyncio.wait_for(
                proc.communicate(),
                timeout=timeout or self.config.timeout,
            )

            latency_ms = (time.time() - start_time) * 1000

            if proc.returncode == 0:
                return DriverResponse(
                    content=stdout.decode().strip(),
                    status=DriverResponseStatus.SUCCESS,
                    provider="opencode",
                    model=self.config.model,
                    session_id=session_id,
                    latency_ms=latency_ms,
                )
            else:
                return self._create_error_response(
                    stderr.decode().strip() or "CLI error",
                    error_code=f"EXIT_{proc.returncode}",
                )

        except asyncio.TimeoutError:
            return self._create_error_response(
                "CLI timeout",
                error_code="TIMEOUT",
                status=DriverResponseStatus.TIMEOUT,
            )
        except asyncio.CancelledError:
            raise
        except FileNotFoundError:
            return self._create_error_response(
                "OpenCode CLI not found. Install with: npm i -g opencode-ai",
                error_code="CLI_NOT_FOUND",
            )

    async def invoke_stream(
        self,
        prompt: str,
        **kwargs: Any,
    ) -> AsyncIterator[StreamChunk]:
        """Stream not supported in CLI mode - return full response."""
        response = await self.invoke(prompt, **kwargs)
        yield StreamChunk(
            content=response.content,
            is_final=True,
            latency_ms=response.latency_ms,
        )

    async def cancel(self, session_id: Optional[str] = None) -> bool:
        return False

    async def health_check(self) -> bool:
        """Check if OpenCode CLI is available."""
        try:
            proc = await asyncio.create_subprocess_exec(
                self._cli_path, "--version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await asyncio.wait_for(proc.wait(), timeout=5.0)
            return proc.returncode == 0
        except Exception:
            return False


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    "AsyncOpenCodeDriverConfig",
    "AsyncOpenCodeDriver",
    "AsyncOpenCodeCLIDriver",
]
