"""
GLM Hybrid Driver - API-backed replacement for Claude CLI.

Provides Claude-compatible response parsing (natural text + <tool_use> XML).
"""

from __future__ import annotations

import json
import time
import re
from pathlib import Path
from typing import Dict, Optional, Callable
from urllib import request, error

from core.agents.unified_registry import get_registry
from core.security import get_output_guard
from core.utils.ssl_utils import SslConfig, urlopen_ssl


class GLMDriverHybrid:
    """Sync GLM driver that mimics Claude hybrid behavior."""

    def __init__(
        self,
        config,
        workspace_path: Path,
        model: Optional[str] = None,
        agent_id: Optional[str] = None,
    ):
        self.workspace_path = workspace_path
        self.api_key = getattr(config, "glm_api_key", None)
        if not self.api_key:
            raise RuntimeError("GLM_API_KEY is not configured")
        self.api_base = getattr(config, "glm_api_base", "https://api.z.ai/api/paas/v4")
        self.model = model or getattr(config, "glm_model", "glm-4.7")
        self.timeout = getattr(config, "glm_timeout", 60.0)
        self.max_tokens = getattr(config, "glm_max_tokens", 4096)
        self.temperature = getattr(config, "glm_temperature", 0.2)
        self.max_retries = getattr(config, "glm_max_retries", 2)
        self.verify_ssl = getattr(config, "glm_verify_ssl", True)
        self.ssl_mode = getattr(config, "glm_ssl_mode", "strict")
        self.ca_bundle = getattr(config, "glm_ca_bundle", None)
        self.agent_id = agent_id or "claude_primary"
        self._registry = get_registry()

    def _build_ssl_config(self) -> SslConfig:
        ssl_mode = self.ssl_mode
        if not self.verify_ssl:
            ssl_mode = "insecure"
        return SslConfig(
            ssl_mode=ssl_mode,
            ca_bundle_path=Path(self.ca_bundle) if self.ca_bundle else None,
        )

    def _validate_output(self, response: Dict) -> Dict:
        output_guard = get_output_guard()
        content = response.get("content", "")
        if not content or not isinstance(content, str):
            return response
        validation = output_guard.validate(content)
        if validation.leak_type.value != "none":
            if validation.sanitized_output:
                response = response.copy()
                response["content"] = validation.sanitized_output
                response["_output_sanitized"] = True
                response["_leak_type"] = validation.leak_type.value
        return response

    def _invoke_api(self, context: str) -> str:
        endpoint = self.api_base.rstrip("/") + "/chat/completions"
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": context}],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "stream": False,
        }

        data = json.dumps(payload).encode("utf-8")
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        ssl_config = self._build_ssl_config()

        last_error: Optional[Exception] = None
        for attempt in range(self.max_retries + 1):
            try:
                req = request.Request(endpoint, data=data, headers=headers, method="POST")
                with urlopen_ssl(req, timeout=self.timeout, ssl_config=ssl_config) as response:
                    raw = response.read().decode("utf-8")
                parsed = json.loads(raw)
                choices = parsed.get("choices") or []
                if choices:
                    message = choices[0].get("message") or {}
                    return message.get("content", "")
                return ""
            except (error.HTTPError, error.URLError, json.JSONDecodeError) as exc:
                last_error = exc
                if attempt >= self.max_retries:
                    break
                time.sleep(0.5 * (2 ** attempt))

        raise RuntimeError(f"GLM API request failed: {last_error}")

    def invoke(self, context: str, session_uuid: Optional[str] = None) -> Dict:
        content = self._invoke_api(context)
        parsed = self._parse_hybrid_response(content)
        return self._validate_output(parsed)

    def invoke_stream(
        self,
        context: str,
        on_token: Callable[[str], None],
        session_uuid: Optional[str] = None
    ) -> Dict:
        content = self._invoke_api(context)
        if content:
            chunk_size = 1024
            for idx in range(0, len(content), chunk_size):
                on_token(content[idx:idx + chunk_size])
            on_token("\n")
        parsed = self._parse_hybrid_response(content)
        return self._validate_output(parsed)

    async def send_message_async(self, prompt: str, session_uuid: Optional[str] = None) -> Dict:
        import asyncio
        return await asyncio.to_thread(self.invoke, prompt, session_uuid)

    def _parse_hybrid_response(self, raw_text: str) -> Dict:
        tool_pattern = r'<tool_use\s+name="([\w-]+)">(.*?)</tool_use>'
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

    def invoke_with_retry(self, context: str, max_retries: int = 3) -> Dict:
        last_error: Optional[Exception] = None
        for attempt in range(max_retries):
            try:
                return self.invoke(context)
            except Exception as exc:
                last_error = exc
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
        raise RuntimeError(f"GLM invocation failed after {max_retries} attempts: {last_error}")
