"""
Async Kimi Driver - API-based Moonshot/Kimi client.

Uses standard library HTTP to avoid extra dependencies.
Provides async wrappers via asyncio.to_thread().
"""

from __future__ import annotations

import asyncio
import json
import ssl
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional, AsyncIterator
from urllib import request, error

from core.async_primitives import CancellationToken


@dataclass
class AsyncKimiDriverConfig:
    """Configuration for AsyncKimiDriver."""
    api_key: str
    api_base: str = "https://api.moonshot.ai/v1"
    model: str = "kimi-k2-thinking"
    timeout: float = 60.0
    max_tokens: int = 4096
    temperature: float = 0.2
    max_retries: int = 2
    verify_ssl: bool = True
    ca_bundle: Optional[str] = None


class AsyncKimiDriver:
    """Async API driver for Kimi (Moonshot)."""

    def __init__(self, config: AsyncKimiDriverConfig) -> None:
        self.config = config

    async def invoke(
        self,
        context: str,
        *,
        session_uuid: Optional[str] = None,
        token: Optional[CancellationToken] = None,
    ) -> Dict[str, Any]:
        """
        Invoke Kimi API and return parsed response.
        """
        return await asyncio.to_thread(
            self._invoke_sync,
            context,
            session_uuid=session_uuid,
            token=token
        )

    async def invoke_stream(
        self,
        context: str,
        *,
        session_uuid: Optional[str] = None,
        token: Optional[CancellationToken] = None,
    ) -> AsyncIterator[str]:
        """
        Stream response (non-streaming API fallback).
        """
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

        ssl_context = None
        if not self.config.verify_ssl:
            ssl_context = ssl._create_unverified_context()
        elif self.config.ca_bundle:
            ssl_context = ssl.create_default_context(cafile=self.config.ca_bundle)

        last_error: Optional[Exception] = None
        for attempt in range(self.config.max_retries + 1):
            if token:
                token.check()
            try:
                req = request.Request(endpoint, data=data, headers=headers, method="POST")
                with request.urlopen(req, timeout=self.config.timeout, context=ssl_context) as response:
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

        raise RuntimeError(f"Kimi API request failed: {last_error}")
