"""
Async DeepSeek Driver - API-based DeepSeek client.

Uses standard library HTTP to avoid extra dependencies.
Provides async wrappers via asyncio.to_thread().
"""

from __future__ import annotations

import asyncio
import json
import logging
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional, AsyncIterator
from urllib import request, error

from core.async_primitives import CancellationToken
from core.utils.ssl_utils import SslConfig, urlopen_ssl

logger = logging.getLogger("nexus.driver.deepseek")

_AUTO_MODEL_TOKENS = {"auto", "latest", "latest-reasoning", "reasoning-latest"}


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
        self._resolved_model: Optional[str] = None

    def _build_ssl_config(self) -> SslConfig:
        ssl_mode = self.config.ssl_mode
        if not self.config.verify_ssl:
            ssl_mode = "insecure"
        return SslConfig(
            ssl_mode=ssl_mode,
            ca_bundle_path=Path(self.config.ca_bundle) if self.config.ca_bundle else None,
        )

    def _is_reasoning_model(self, model_id: str) -> bool:
        lower = model_id.lower()
        return "reason" in lower or lower.startswith("deepseek-r1") or "r1" in lower

    def _model_sort_key(self, model_id: str) -> tuple:
        digits = [int(value) for value in re.findall(r"\d+", model_id)] or [0]
        return (digits, len(model_id), model_id)

    def _fetch_models(self, ssl_config: SslConfig) -> list[str]:
        endpoint = self.config.api_base.rstrip("/") + "/models"
        headers = {"Authorization": f"Bearer {self.config.api_key}"}
        req = request.Request(endpoint, headers=headers, method="GET")
        with urlopen_ssl(req, timeout=self.config.timeout, ssl_config=ssl_config) as response:
            raw = response.read().decode("utf-8")
        parsed = json.loads(raw)
        data = parsed.get("data", [])
        model_ids = [
            item.get("id")
            for item in data
            if isinstance(item, dict) and item.get("id")
        ]
        return model_ids

    def _discover_latest_reasoning_model(self, ssl_config: SslConfig) -> Optional[str]:
        try:
            model_ids = self._fetch_models(ssl_config)
        except Exception as exc:
            logger.debug("DeepSeek model discovery failed: %s", exc)
            return None

        reasoning_models = [model_id for model_id in model_ids if self._is_reasoning_model(model_id)]
        if not reasoning_models:
            return None
        return max(reasoning_models, key=self._model_sort_key)

    def _resolve_model(self, ssl_config: SslConfig) -> str:
        if self._resolved_model:
            return self._resolved_model

        model = (self.config.model or "").strip()
        if model and model.lower() not in _AUTO_MODEL_TOKENS:
            self._resolved_model = model
            return model

        resolved = self._discover_latest_reasoning_model(ssl_config)
        if resolved:
            self._resolved_model = resolved
            return resolved

        self._resolved_model = "deepseek-reasoner"
        return self._resolved_model

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

        ssl_config = self._build_ssl_config()
        model = self._resolve_model(ssl_config)
        endpoint = self.config.api_base.rstrip("/") + "/chat/completions"
        payload = {
            "model": model,
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

        raise RuntimeError(f"DeepSeek API request failed: {last_error}")
