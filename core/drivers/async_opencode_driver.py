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
import re
from pathlib import Path

from core.drivers.protocol import (
    BaseAsyncDriver,
    DriverResponse,
    DriverResponseStatus,
    StreamChunk,
    ToolCall,
)
from core.security.path_guardian import PathGuardian


@dataclass
class AsyncOpenCodeDriverConfig:
    """Configuration for AsyncOpenCodeDriver.

    Attributes:
        server_url: The URL of the OpenCode server. Defaults to "http://localhost:5173".
        api_key: The API key for OpenCode Zen. Defaults to None.
        model: The model identifier to use (e.g., "glm-4.7"). Defaults to "glm-4.7".
        timeout: Request timeout in seconds. Defaults to 120.0.
        workspace_path: Path to the workspace directory. Defaults to CWD.
        verbose: Whether to enable verbose logging. Defaults to False.
    """

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
        """Post-initialization processing to set up defaults.

        Automatically retrieves the API key from the environment variable
        'OPENCODE_ZEN_API_KEY' if it was not provided in the configuration.

        Args:
            None

        Returns:
            None

        Raises:
            None
        """
        # Try to get API key from environment if not provided
        if not self.api_key:
            self.api_key = os.environ.get("OPENCODE_ZEN_API_KEY")


class AsyncOpenCodeDriver(BaseAsyncDriver):
    """OpenCode driver using HTTP API.

    OpenCode can run in server mode, exposing an HTTP API.
    This driver communicates with that server for LLM invocations.

    Supported Models (Zen):
    - glm-4.7 (FREE - limited time)
    - grok-code-fast-1 (FREE - limited time)
    - minimax-m2.1 (FREE - limited time)

    Attributes:
        config: Configuration object containing server URL, model, and API key.
    """

    def __init__(self, config: AsyncOpenCodeDriverConfig):
        """Initializes the AsyncOpenCodeDriver.

        Args:
            config: Configuration object containing server URL, model, and API key.

        Returns:
            None

        Raises:
            None
        """
        super().__init__(
            provider="opencode",
            model=config.model,
            timeout=config.timeout,
        )
        self.config = config
        self._client: Optional[httpx.AsyncClient] = None
        self._active_requests: Dict[str, asyncio.Task] = {}
        
        # SECURITY: Initialize PathGuardian for path validation
        self.path_guardian = PathGuardian(
            workspace_path=config.workspace_path,
            parent_path=config.workspace_path.parent
        )
        
        # SECURITY: Validate configuration
        self._validate_config()

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create the underlying HTTP client.

        Creates a new httpx.AsyncClient if one does not exist or is closed.
        Configures headers with the API key if available.

        Args:
            None

        Returns:
            httpx.AsyncClient: The configured HTTP client instance.

        Raises:
            None
        """
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
    
    def _validate_config(self) -> None:
        """
        SECURITY: Validate critical configuration values to prevent injection attacks.
        
        Validates:
        - model: Must be a valid model identifier without injection characters
        """
        # Validate model parameter if present
        if self.config.model and not self._is_safe_model_name(self.config.model):
            raise ValueError(f"[SECURITY] Invalid model name: {self.config.model}")
    
    def _is_safe_model_name(self, model: str) -> bool:
        """
        Check if model name is safe from parameter injection.
        
        Allowed: Alphanumeric characters, hyphens, underscores, dots
        Rejected: Shell metacharacters, path traversal, command injection
        """
        # Model names should consist of safe characters only
        # Pattern: alphanumeric, hyphens, underscores, dots (common in model names)
        if not re.match(r'^[a-zA-Z0-9._-]+$', model):
            return False
        
        # Additional checks for suspicious patterns
        dangerous_patterns = ['..', ';', '|', '&', '`', '$', '(', ')', '<', '>', '\\', '/']
        if any(pattern in model for pattern in dangerous_patterns):
            return False
        
        return True
    
    def _sanitize_model_param(self, model: str) -> str:
        """
        Sanitize model parameter before using in command or request.
        
        Args:
            model: The model name to sanitize
            
        Returns:
            Sanitized model name
        """
        # Only allow safe characters
        sanitized = re.sub(r'[^a-zA-Z0-9._-]', '', model)
        return sanitized

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
        """Invoke OpenCode via HTTP API.

        Args:
            prompt: The prompt to send.
            session_id: Optional session identifier.
            system_prompt: Optional system prompt.
            tools: Not used (OpenCode handles tools internally).
            isolated_env: Not used for HTTP API.
            timeout: Optional timeout override.
            **kwargs: Additional keyword arguments.

        Returns:
            DriverResponse: Response object with content and metadata.

        Raises:
            asyncio.CancelledError: If the operation is cancelled.
        """
        start_time = time.time()
        request_id = session_id or str(uuid.uuid4())

        try:
            client = await self._get_client()

            # Build request payload
            sanitized_model = self._sanitize_model_param(self.config.model)
            
            # SECURITY: Validate prompt doesn't contain dangerous characters
            if not self._is_safe_prompt(prompt):
                return self._create_error_response(
                    "Invalid prompt: contains dangerous characters",
                    error_code="INVALID_PROMPT"
                )
            
            payload = {
                "prompt": prompt,
                "model": sanitized_model,
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
        """Stream response from OpenCode via HTTP API.

        Falls back to non-streaming if the server does not support SSE.

        Args:
            prompt: The input prompt text.
            session_id: Optional unique identifier for the session.
            system_prompt: Optional system instructions.
            tools: List of tools (not currently supported by OpenCode API).
            isolated_env: Environment variables (not used for HTTP API).
            timeout: Request timeout in seconds.
            **kwargs: Additional keyword arguments.

        Yields:
            StreamChunk: Chunks of the generated response.

        Raises:
            asyncio.CancelledError: If the operation is cancelled.
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
        """Cancels an active request associated with a session ID.

        Args:
            session_id: The session identifier of the request to cancel.

        Returns:
            bool: True if a request was found and cancelled, False otherwise.
        """
        if session_id and session_id in self._active_requests:
            task = self._active_requests.pop(session_id)
            task.cancel()
            return True
        return False
    
    def _is_safe_prompt(self, prompt: str) -> bool:
        """
        Check if prompt is safe from injection attacks.
        
        Rejects prompts with null bytes or extreme sizes that could cause DoS.
        """
        # Reject null bytes
        if '\x00' in prompt:
            return False
        
        # Reject extremely large prompts (potential DoS)
        if len(prompt) > 1024 * 1024:  # 1MB limit
            return False
        
        return True

    async def health_check(self) -> bool:
        """Checks if the OpenCode server is reachable and healthy.

        Args:
            None

        Returns:
            bool: True if the server responds with HTTP 200, False otherwise.

        Raises:
            None
        """
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
        """Closes the underlying HTTP client.

        Ensures resources are freed by closing the httpx client if it exists
        and is open.

        Args:
            None

        Returns:
            None

        Raises:
            None
        """
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None


# =============================================================================
# CLI Fallback (if HTTP server not available)
# =============================================================================

class AsyncOpenCodeCLIDriver(BaseAsyncDriver):
    """OpenCode driver using CLI subprocess.

    Fallback when HTTP server is not running.
    Uses: opencode --model glm-4.7 "prompt"

    Attributes:
        config: Configuration object specifying the model and timeout.
    """

    def __init__(self, config: AsyncOpenCodeDriverConfig):
        """Initializes the CLI driver.

        Args:
            config: Configuration object specifying the model and timeout.

        Returns:
            None

        Raises:
            None
        """
        super().__init__(
            provider="opencode",
            model=config.model,
            timeout=config.timeout,
        )
        self.config = config
        self._cli_path = "opencode"
        
        # SECURITY: Validate configuration
        self._validate_config()
    
    def _validate_config(self) -> None:
        """
        SECURITY: Validate critical configuration values to prevent injection attacks.
        
        Validates:
        - model: Must be a valid model identifier without injection characters
        """
        # Validate model parameter if present
        if self.config.model and not self._is_safe_model_name(self.config.model):
            raise ValueError(f"[SECURITY] Invalid model name: {self.config.model}")
        
        # Validate CLI path
        if not self._is_safe_cli_path(self._cli_path):
            raise ValueError(f"[SECURITY] Invalid CLI path: {self._cli_path}")
    
    def _is_safe_cli_path(self, path: str) -> bool:
        """
        Check if cli_path is safe from command injection.
        
        Allowed: Simple command names like 'opencode'
        Rejected: Paths with '..', shell metacharacters, or command chaining
        """
        # Reject shell metacharacters and command chaining
        dangerous_chars = [';', '|', '&', '$', '`', '(', ')', '<', '>']
        if any(char in path for char in dangerous_chars):
            return False
        
        # Reject path traversal attempts
        if '..' in path or path.startswith('~'):
            return False
        
        # If it's an absolute path, validate it's within reasonable system directories
        if Path(path).is_absolute():
            allowed_prefixes = ['/usr/local/bin/', '/usr/bin/', '/bin/', '/opt/homebrew/bin/']
            if not any(str(path).startswith(prefix) for prefix in allowed_prefixes):
                return False
        
        return True
    
    def _is_safe_model_name(self, model: str) -> bool:
        """
        Check if model name is safe from parameter injection.
        
        Allowed: Alphanumeric characters, hyphens, underscores, dots
        Rejected: Shell metacharacters, path traversal, command injection
        """
        # Model names should consist of safe characters only
        # Pattern: alphanumeric, hyphens, underscores, dots (common in model names)
        if not re.match(r'^[a-zA-Z0-9._-]+$', model):
            return False
        
        # Additional checks for suspicious patterns
        dangerous_patterns = ['..', ';', '|', '&', '`', '$', '(', ')', '<', '>', '\\\\', '/']
        if any(pattern in model for pattern in dangerous_patterns):
            return False
        
        return True
    
    def _sanitize_model_param(self, model: str) -> str:
        """
        Sanitize model parameter before using in command.
        
        Args:
            model: The model name to sanitize
            
        Returns:
            Sanitized model name
        """
        # Only allow safe characters
        sanitized = re.sub(r'[^a-zA-Z0-9._-]', '', model)
        return sanitized
    
    def _is_safe_prompt(self, prompt: str) -> bool:
        """
        Check if prompt is safe from injection attacks.
        
        Rejects prompts with null bytes or extreme sizes that could cause DoS.
        """
        # Reject null bytes
        if '\x00' in prompt:
            return False
        
        # Reject extremely large prompts (potential DoS)
        if len(prompt) > 1024 * 1024:  # 1MB limit
            return False
        
        return True

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
        """Invoke OpenCode via the command-line interface.

        Args:
            prompt: The input prompt text.
            session_id: Optional unique identifier for the session.
            system_prompt: Optional system instructions.
            tools: List of tools (not currently supported).
            isolated_env: Custom environment variables for the subprocess.
            timeout: Execution timeout in seconds.
            **kwargs: Additional keyword arguments.

        Returns:
            DriverResponse: The complete response from the CLI.

        Raises:
            asyncio.CancelledError: If the operation is cancelled.
        """
        start_time = time.time()

        # SECURITY: Sanitize model parameter before use
        sanitized_model = self._sanitize_model_param(self.config.model)
        
        # SECURITY: Validate prompt doesn't contain dangerous characters
        if not self._is_safe_prompt(prompt):
            return self._create_error_response(
                "Invalid prompt: contains dangerous characters",
                error_code="INVALID_PROMPT"
            )
        
        cmd = [
            self._cli_path,
            "--model", sanitized_model,
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
        """Stream response from OpenCode CLI (simulated).

        Since CLI mode does not support real streaming, this yields a single
        final chunk after the command completes.

        Args:
            prompt: The input prompt text.
            **kwargs: Additional arguments passed to invoke.

        Yields:
            StreamChunk: A single chunk containing the full response.
        """
        response = await self.invoke(prompt, **kwargs)
        yield StreamChunk(
            content=response.content,
            is_final=True,
            latency_ms=response.latency_ms,
        )

    async def cancel(self, session_id: Optional[str] = None) -> bool:
        """Attempt to cancel a running operation.

        Note:
            Cancellation is not currently supported for the CLI driver.

        Args:
            session_id: The session ID of the operation to cancel.

        Returns:
            bool: Always False, as cancellation is not supported.

        Raises:
            None
        """
        return False

    async def health_check(self) -> bool:
        """Checks if the OpenCode CLI tool is installed and executable.

        Args:
            None

        Returns:
            bool: True if 'opencode --version' exits with code 0, False otherwise.

        Raises:
            None
        """
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
