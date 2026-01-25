"""
Async GLM Driver - API-based GLM client for NEXUS.

Implements a Claude-compatible response shape (natural text + <tool_use> XML)
so it can temporarily replace the Claude CLI without changing orchestration.
"""

from __future__ import annotations

import asyncio
import json
import time
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional, AsyncIterator, Callable
from urllib import request, error

from core.async_primitives import CancellationToken
from core.agents.unified_registry import get_registry
from core.utils.ssl_utils import SslConfig, urlopen_ssl


@dataclass
class AsyncGLMDriverConfig:
    """Configuration for AsyncGLMDriver."""
    api_key: str
    api_base: str = "https://api.z.ai/api/paas/v4"
    model: str = "glm-4.7"
    timeout: float = 60.0
    max_tokens: int = 4096
    temperature: float = 0.2
    max_retries: int = 2
    verify_ssl: bool = True
    ca_bundle: Optional[str] = None
    ssl_mode: str = "strict"


class AsyncGLMDriver:
    """Async API driver for GLM (OpenAI-compatible chat completions)."""

    def __init__(self, config: AsyncGLMDriverConfig) -> None:
        self.config = config
        self._registry = get_registry()

    def _build_ssl_config(self) -> SslConfig:
        ssl_mode = self.config.ssl_mode
        if not self.config.verify_ssl:
            ssl_mode = "insecure"
        return SslConfig(
            ssl_mode=ssl_mode,
            ca_bundle_path=Path(self.config.ca_bundle) if self.config.ca_bundle else None,
        )

    async def invoke(
        self,
        context: str,
        *,
        session_uuid: Optional[str] = None,
        token: Optional[CancellationToken] = None,
        task_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Invoke GLM API and return NEXUS-style response dict."""
        response = await asyncio.to_thread(
            self._invoke_sync,
            context,
            session_uuid=session_uuid,
            token=token,
        )
        content = response.get("content", "")
        return self._parse_hybrid_response(content)

    async def invoke_stream(
        self,
        context: str,
        *,
        session_uuid: Optional[str] = None,
        token: Optional[CancellationToken] = None,
        task_id: Optional[str] = None,
        on_token: Optional[Callable[[str], None]] = None,
    ) -> AsyncIterator[str]:
        """Stream response (non-streaming API fallback)."""
        response = await asyncio.to_thread(
            self._invoke_sync,
            context,
            session_uuid=session_uuid,
            token=token,
        )
        content = response.get("content", "")
        if not content:
            return
        chunk_size = 1024
        for idx in range(0, len(content), chunk_size):
            chunk = content[idx:idx + chunk_size]
            if on_token:
                on_token(chunk)
            yield chunk

    def _invoke_sync(
        self,
        context: str,
        *,
        session_uuid: Optional[str] = None,
        token: Optional[CancellationToken] = None,
    ) -> Dict[str, Any]:
        if token:
            token.check()

        ssl_config = self._build_ssl_config()
        endpoint = self.config.api_base.rstrip("/") + "/chat/completions"
        payload = {
            "model": self.config.model,
            "messages": [{"role": "user", "content": context}],
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
            "stream": False,
        }

        data = json.dumps(payload).encode("utf-8")
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
        }

        last_error: Optional[Exception] = None
        for attempt in range(self.config.max_retries + 1):
            if token:
                token.check()
            try:
                req = request.Request(endpoint, data=data, headers=headers, method="POST")
                with urlopen_ssl(req, timeout=self.config.timeout, ssl_config=ssl_config) as response:
                    raw = response.read().decode("utf-8")
                parsed = json.loads(raw)
                content = ""
                choices = parsed.get("choices") or []
                if choices:
                    message = choices[0].get("message") or {}
                    content = message.get("content", "")
                return {
                    "content": content,
                    "raw": parsed,
                    "usage": parsed.get("usage", {}),
                    "session_uuid": session_uuid,
                }
            except (error.HTTPError, error.URLError, json.JSONDecodeError) as exc:
                last_error = exc
                if attempt >= self.config.max_retries:
                    break
                time.sleep(0.5 * (2 ** attempt))

        raise RuntimeError(f"GLM API request failed: {last_error}")

    def _parse_hybrid_response(self, raw_text: str) -> Dict[str, Any]:
        """Parse natural language response with XML tool_use blocks."""
        tool_pattern = r'<tool_use\\s+name="(\\w+)">(.*?)</tool_use>'
        tool_matches = list(re.finditer(tool_pattern, raw_text, re.DOTALL))

        content = raw_text
        for match in tool_matches:
            content = content.replace(match.group(0), '')
        content = content.strip()

        tool_use = None
        action_type = "TALK"
        if tool_matches:
            match = tool_matches[0]
            tool_name = match.group(1)
            tool_args_raw = match.group(2).strip()
            try:
                arguments = json.loads(tool_args_raw)
            except json.JSONDecodeError:
                arguments = self._parse_keyvalue_args(tool_args_raw)
            tool_use = {
                "tool_name": tool_name,
                "arguments": arguments,
                "expected_outcome": f"Execute {tool_name} successfully",
            }
            action_type = "TOOL_USE"

        status = "CONTINUE"
        finish_keywords = ["task complete", "finished", "done", "termine", "fini"]
        if any(keyword in content.lower() for keyword in finish_keywords):
            status = "FINISHED"

        return {
            "sender": self._registry.get_display_name("claude"),
            "action_type": action_type,
            "content": content,
            "tool_use": tool_use,
            "status": status,
            "next_agent": self._registry.get_alternate("claude"),
        }

    def _parse_keyvalue_args(self, args_text: str) -> Dict[str, str]:
        args: Dict[str, str] = {}
        for line in args_text.split("\\n"):
            line = line.strip()
            if "=" in line:
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip()
                if not re.match(r'^[a-zA-Z0-9_-]+$', key):
                    continue
                if "\x00" in value:
                    value = value.replace("\x00", "")
                if len(value) > 10000:
                    value = value[:10000] + "... [truncated]"
                args[key] = value
        return args

    async def cancel_by_uuid(self, session_uuid: str) -> bool:
        """Cancellation is not supported for API calls."""
        return False

    async def cancel_all(self) -> int:
        """Cancellation is not supported for API calls."""
        return 0

    @property
    def active_process_count(self) -> int:
        """API driver does not spawn subprocesses."""
        return 0

    def list_active_processes(self) -> list[Dict[str, Any]]:
        """API driver does not spawn subprocesses."""
        return []
