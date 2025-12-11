"""
AsyncClaudeDriver - TRUE Non-blocking Claude CLI Driver.

NEXUS V9.0 Async-First Architecture

Architecture:
- asyncio.create_subprocess_exec (NOT subprocess.Popen)
- async for line in proc.stdout (NOT iter(readline))
- AsyncProcessHandle tracking by session_uuid
- Session isolation via unique context files (Claude CLI doesn't support --resume like Gemini)

Key Claude-specific features:
- Hybrid Mode (Natural Language + XML Tools)
- Dynamic Model Selection (Opus/Sonnet)
- Streaming via --output-format stream-json

Usage:
    driver = AsyncClaudeDriver(config)

    # With session isolation
    result = await driver.invoke(context, session_uuid="abc123")

    # Streaming
    async for chunk in driver.invoke_stream(context, session_uuid="abc123"):
        print(chunk, end="")
"""

from __future__ import annotations

import asyncio
import json
import shutil
import platform
import uuid as uuid_module
import sys
import re
from pathlib import Path
from datetime import datetime
from typing import AsyncIterator, Optional, Dict, Any, Callable
from dataclasses import dataclass, field

from core.async_primitives import CancellationToken, AsyncProcessHandle
from core.async_primitives.process_handle import get_process_registry
from core.agents.unified_registry import get_registry
from core.utils.stream_parser import parse_stream_chunk, is_result_message, extract_stats, extract_final_result


@dataclass
class AsyncClaudeDriverConfig:
    """Configuration for AsyncClaudeDriver."""
    cli_path: str = "claude"
    timeout: float = 300.0
    model: Optional[str] = None  # None = use CLI default or Sonnet
    workspace_path: Path = field(default_factory=Path.cwd)
    verbose: bool = False


class AsyncClaudeDriver:
    """
    TRUE Async Claude CLI Driver.

    Key differences from sync ClaudeDriverHybrid:
    - Uses asyncio.create_subprocess_exec
    - Uses async for line in proc.stdout
    - Tracks processes by session_uuid via AsyncProcessHandle
    - Properly handles asyncio.CancelledError
    """

    def __init__(self, config: AsyncClaudeDriverConfig):
        """
        Initialize async Claude driver.

        Args:
            config: Driver configuration
        """
        self.config = config
        self.workspace_path = Path(config.workspace_path)
        self.io_buffer = self.workspace_path / "_IO_BUFFER"
        self.io_buffer.mkdir(parents=True, exist_ok=True)

        # Track active processes by UUID
        self._active_handles: Dict[str, AsyncProcessHandle] = {}

        # Global registry
        self._registry = get_process_registry()

    async def invoke(
        self,
        context: str,
        *,
        session_uuid: Optional[str] = None,
        token: Optional[CancellationToken] = None,
        task_id: Optional[str] = None,
        on_token: Optional[Callable[[str], None]] = None,
    ) -> Dict[str, Any]:
        """
        Non-blocking invoke that collects full response.

        Args:
            context: Markdown context with system prompt
            session_uuid: Unique ID for session isolation
            token: CancellationToken for graceful cancellation
            task_id: Optional task ID for tracking
            on_token: Optional callback for each token

        Returns:
            Dict structured NEXUS response (Hybrid parsed)
        """
        chunks = []
        final_result_text = None
        final_stats = {}

        async for chunk in self.invoke_stream(
            context,
            session_uuid=session_uuid,
            token=token,
            task_id=task_id,
            on_token=on_token
        ):
            # Check if chunk is a special result object (from stream parser)
            # But invoke_stream yields strings. We need to capture stats differently?
            # Actually invoke_stream implementation below handles parsing and yields text.
            # We need a way to get stats out.
            # For now, let's just collect text.
            chunks.append(chunk)

        full_response = "".join(chunks)
        return self._parse_hybrid_response(full_response)

    async def invoke_stream(
        self,
        context: str,
        *,
        session_uuid: Optional[str] = None,
        token: Optional[CancellationToken] = None,
        task_id: Optional[str] = None,
        on_token: Optional[Callable[[str], None]] = None,
    ) -> AsyncIterator[str]:
        """
        TRUE Non-blocking streaming invoke.

        Args:
            context: Markdown context with system prompt
            session_uuid: Unique ID for session isolation
            token: CancellationToken for graceful cancellation
            task_id: Optional task ID for tracking
            on_token: Optional callback for each token

        Yields:
            Text chunks as they arrive from Claude CLI
        """
        token = token or CancellationToken()
        unique_id = session_uuid or str(uuid_module.uuid4())[:8]

        # Write context to isolated file
        context_file = self.io_buffer / f"claude_context_{unique_id}.md"
        context_file.write_text(context, encoding="utf-8")
        
        # Restrict permissions if possible
        try:
            import os
            os.chmod(context_file, 0o600)
        except OSError:
            pass

        # Find CLI executable
        cli_executable = shutil.which(str(self.config.cli_path))
        if not cli_executable:
            cli_executable = str(self.config.cli_path)

        # Build command parts
        # Claude streaming requires: --verbose --output-format stream-json --include-partial-messages
        cmd = [
            cli_executable,
            "-p", f"@{context_file}",
            "--dangerously-skip-permissions",
            "--verbose",
            "--output-format", "stream-json",
            "--include-partial-messages"
        ]

        if self.config.model:
            cmd.extend(["-m", self.config.model])

        handle: Optional[AsyncProcessHandle] = None

        try:
            # TRUE ASYNC: create_subprocess_exec
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(self.workspace_path),
            )

            # Track by UUID
            handle = AsyncProcessHandle(
                proc=proc,
                session_uuid=unique_id,
                task_id=task_id,
                agent_id="claude",
                created_at=datetime.now()
            )
            self._active_handles[unique_id] = handle
            await self._registry.register(handle)

            # Register cancellation callback
            async def cancel_process():
                if handle and handle.is_running:
                    await handle.terminate_gracefully()

            token.on_cancel(lambda: asyncio.create_task(cancel_process()))

            if self.config.verbose:
                print(f"[AsyncClaudeDriver] Started process pid={proc.pid}, uuid={unique_id[:8]}", file=sys.stderr)

            # TRUE ASYNC STREAMING
            start_time = datetime.now()
            async for line_bytes in proc.stdout:
                token.check()

                # Check timeout
                elapsed = (datetime.now() - start_time).total_seconds()
                if elapsed > self.config.timeout:
                    await handle.terminate_gracefully()
                    raise TimeoutError(f"Claude CLI timed out after {self.config.timeout}s")

                line = line_bytes.decode('utf-8', errors='replace')
                if line:
                    # Parse stream chunk using core utility
                    text_chunk, data = parse_stream_chunk(line, "claude")

                    if text_chunk:
                        yield text_chunk
                        if on_token:
                            on_token(text_chunk)

            # Wait for process completion
            await proc.wait()

            if proc.returncode != 0:
                stderr_bytes = await proc.stderr.read()
                stderr = stderr_bytes.decode('utf-8', errors='replace')
                raise RuntimeError(f"Claude CLI failed (code {proc.returncode}): {stderr}")

            if self.config.verbose:
                print(f"[AsyncClaudeDriver] Process completed, code={proc.returncode}", file=sys.stderr)

        except asyncio.CancelledError:
            if self.config.verbose:
                print(f"[AsyncClaudeDriver] Cancelled, cleaning up...", file=sys.stderr)
            raise

        finally:
            # Cleanup
            if handle and handle.is_running:
                await handle.terminate_gracefully()

            self._active_handles.pop(unique_id, None)
            await self._registry.unregister(unique_id)

            try:
                if context_file.exists():
                    context_file.unlink()
            except Exception:
                pass

    async def cancel_by_uuid(self, session_uuid: str) -> bool:
        """Cancel a specific task by its session UUID."""
        handle = self._active_handles.get(session_uuid)
        if handle:
            await handle.terminate_gracefully()
            self._active_handles.pop(session_uuid, None)
            await self._registry.unregister(session_uuid)
            return True
        return False

    async def cancel_all(self) -> int:
        """Cancel all active processes."""
        count = 0
        for uuid_key in list(self._active_handles.keys()):
            handle = self._active_handles.pop(uuid_key, None)
            if handle and handle.is_running:
                await handle.terminate_gracefully()
                await self._registry.unregister(uuid_key)
                count += 1
        return count

    def _parse_hybrid_response(self, raw_text: str) -> Dict[str, Any]:
        """
        Parse Claude's natural language response with XML tags.
        Same logic as sync driver.
        """
        # Extract tool use blocks (XML pattern)
        tool_pattern = r'<tool_use\s+name="(\w+)">(.*?)</tool_use>'
        tool_matches = list(re.finditer(tool_pattern, raw_text, re.DOTALL))

        # Extract content (everything OUTSIDE tool blocks)
        content = raw_text
        for match in tool_matches:
            content = content.replace(match.group(0), '')
        content = content.strip()

        # Parse tool use if present
        tool_use = None
        action_type = "TALK"

        if tool_matches:
            # Use first tool block found
            match = tool_matches[0]
            tool_name = match.group(1)
            tool_args_raw = match.group(2).strip()

            # Parse arguments (JSON or key=value)
            try:
                arguments = json.loads(tool_args_raw)
            except json.JSONDecodeError:
                # Fallback: parse key=value format
                arguments = self._parse_keyvalue_args(tool_args_raw)

            tool_use = {
                "tool_name": tool_name,
                "arguments": arguments,
                "expected_outcome": f"Execute {tool_name} successfully"
            }
            action_type = "TOOL_USE"

        # Detect status from content
        status = "CONTINUE"
        finish_keywords = ["task complete", "finished", "done", "terminé", "fini"]
        if any(keyword in content.lower() for keyword in finish_keywords):
            status = "FINISHED"

        registry = get_registry()
        next_agent = registry.get_alternate("claude")

        return {
            "sender": registry.get_display_name("claude"),
            "action_type": action_type,
            "content": content,
            "tool_use": tool_use,
            "status": status,
            "next_agent": next_agent
        }

    def _parse_keyvalue_args(self, args_text: str) -> Dict[str, str]:
        """Parse key=value arguments."""
        args = {}
        for line in args_text.split('\n'):
            line = line.strip()
            if '=' in line:
                key, value = line.split('=', 1)
                args[key.strip()] = value.strip()
        return args


# Factory function
def create_async_claude_driver(
    config: Any,
    workspace_path: Path,
    model: Optional[str] = None
) -> AsyncClaudeDriver:
    """Create an AsyncClaudeDriver from a NEXUS config object."""
    return AsyncClaudeDriver(AsyncClaudeDriverConfig(
        cli_path=getattr(config, 'claude_cli_path', 'claude'),
        timeout=getattr(config, 'timeout', 300.0),
        model=model or getattr(config, 'claude_sonnet_model', None),
        workspace_path=workspace_path,
        verbose=getattr(config, 'verbose', False),
    ))
