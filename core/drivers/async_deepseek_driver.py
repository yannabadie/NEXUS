"""
Async DeepSeek Driver - API-based DeepSeek client.

Uses standard library HTTP to avoid extra dependencies.
Provides async wrappers via asyncio.to_thread().
"""

from __future__ import annotations

import asyncio
import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional, AsyncIterator
from urllib import request, error

from core.async_primitives import CancellationToken
from core.utils.ssl_utils import SslConfig, urlopen_ssl


@dataclass
class AsyncDeepSeekDriverConfig:
    """Configuration for AsyncDeepSeekDriver."""
    api_key: str
    api_base: str = "https://api.deepseek.com/v1"
    model: str = "deepseek-reasoner"
    timeout: float = 60.0
    max_tokens: int = 4096
    temperature: float = 0.2
    max_retries: int = 2
    verify_ssl: bool = True
    ca_bundle: Optional[str] = None
    ssl_mode: str = "strict"


class AsyncDeepSeekDriver:
    """Async API driver for DeepSeek (OpenAI-compatible)."""

    def __init__(self, config: AsyncDeepSeekDriverConfig) -> None:
        self.config = config

    async def invoke(
        self,
        context: str,
        *,
        session_uuid: Optional[str] = None,
        token: Optional[CancellationToken] = None,
    ) -> Dict[str, Any]:
        """Invoke DeepSeek API and return parsed response."""
        return await asyncio.to_thread(
            self._invoke_sync,
            context,
            session_uuid=session_uuid,
            token=token,
        )

    async def invoke_stream(
        self,
        context: str,
        *,
        session_uuid: Optional[str] = None,
        token: Optional[CancellationToken] = None,
    ) -> AsyncIterator[str]:
        """Stream response (non-streaming API fallback)."""
        response = await self.invoke(context, session_uuid=session_uuid, token=token)
        content = response.get("content", "")
        if content:
            yield content

    def _invoke_sync(
        self,
        context: str,
        *,
        session_uuid: Optional[str] = None,
        token: Optional[CancellationToken] = None,
    ) -> Dict[str, Any]:
        if token:
            token.check()

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

        ssl_mode = self.config.ssl_mode
        if not self.config.verify_ssl:
            ssl_mode = "insecure"
        ssl_config = SslConfig(
            ssl_mode=ssl_mode,
            ca_bundle_path=Path(self.config.ca_bundle) if self.config.ca_bundle else None,
        )

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

        raise RuntimeError(f"DeepSeek API request failed: {last_error}")
