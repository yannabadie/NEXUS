"""
AsyncClaudeDriver - TRUE Non-blocking Claude CLI Driver.

NEXUS V9.0 Async-First Architecture

CRITICAL ARCHITECTURE DIFFERENCE FROM SYNC DRIVER:
- Uses asyncio.create_subprocess_exec (NOT subprocess.Popen)
- Uses async for line in proc.stdout (NOT iter(readline))
- This ensures the Event Loop is NOT blocked during CLI execution
- Tracks processes by session_uuid via AsyncProcessHandle

This solves:
1. REPL blocking during Claude execution
2. Ctrl+C not working (orphan processes)
3. No streaming capability

Usage:
    driver = AsyncClaudeDriver(config)

    # Non-streaming (collects full response)
    result = await driver.invoke(context, session_uuid="abc123")

    # Streaming (yields tokens)
    async for chunk in driver.invoke_stream(context, session_uuid="abc123"):
        print(chunk, end="")

References:
- https://docs.python.org/3/library/asyncio-subprocess.html
- https://superfastpython.com/asyncio-subprocess/
"""

from __future__ import annotations

import asyncio
import json
import os
import re
import uuid
import sys
from pathlib import Path
from datetime import datetime
from typing import AsyncIterator, Optional, Dict, Any, Callable
from dataclasses import dataclass, field

from core.async_primitives import CancellationToken, AsyncProcessHandle, create_safe_task
from core.async_primitives.process_handle import get_process_registry
from core.agents.unified_registry import get_registry
from core.security.path_guardian import PathGuardian


@dataclass
class AsyncClaudeDriverConfig:
    """Configuration for AsyncClaudeDriver."""
    cli_path: str = "claude"
    timeout: float = 300.0
    model: str = "claude-sonnet-4-5-20250929"
    workspace_path: Path = field(default_factory=Path.cwd)
    verbose: bool = False


class AsyncClaudeDriver:
    """
    TRUE Async Claude CLI Driver.

    Key differences from sync ClaudeDriverHybrid:
    - Uses asyncio.create_subprocess_exec (NOT subprocess.Popen)
    - Uses async for line in proc.stdout (NOT iter(readline))
    - Tracks processes by session_uuid via AsyncProcessHandle
    - Properly handles asyncio.CancelledError with re-raise

    The sync driver blocks the event loop during:
    - proc.stdout.readline() - BLOCKING
    - proc.wait() - BLOCKING (without timeout)

    This async driver uses:
    - async for line in proc.stdout - NON-BLOCKING
    - await proc.wait() - NON-BLOCKING
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
        self.io_buffer.mkdir(exist_ok=True)

        # SECURITY: Initialize PathGuardian for path validation
        self.path_guardian = PathGuardian(
            workspace_path=self.workspace_path,
            parent_path=self.workspace_path.parent
        )

        # Track ALL active processes by UUID for cancellation
        self._active_handles: Dict[str, AsyncProcessHandle] = {}

        # Global registry for cross-driver coordination
        self._registry = get_process_registry()

        # SECURITY: Prepare sanitized environment for subprocess
        self._sanitized_env = self._create_sanitized_env()

        # SECURITY: Validate critical config values
        self._validate_config()

    def _validate_config(self) -> None:
        """
        SECURITY: Validate critical configuration values to prevent injection attacks.
        
        Validates:
        - cli_path: Must be a simple command name without path traversal or shell metacharacters
        - model: Must be a valid model identifier without injection characters
        - workspace_path: Must be within allowed boundaries
        """
        # Validate cli_path (should be a simple command, not a path with traversal)
        cli_path = str(self.config.cli_path)
        if not self._is_safe_cli_path(cli_path):
            raise ValueError(f"[SECURITY] Invalid cli_path: {cli_path}")
        
        # Validate model parameter if present
        if self.config.model and not self._is_safe_model_name(self.config.model):
            raise ValueError(f"[SECURITY] Invalid model name: {self.config.model}")

    def _is_safe_cli_path(self, path: str) -> bool:
        """
        Check if cli_path is safe from command injection.
        
        Allowed: Simple command names like 'claude', 'gemini', '/usr/local/bin/claude'
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
            allowed_prefixes = ['/usr/local/bin/', '/usr/bin/', '/bin/']
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
        import re
        # Pattern: alphanumeric, hyphens, underscores, dots (common in model names)
        if not re.match(r'^[a-zA-Z0-9._-]+$', model):
            return False
        
        # Additional checks for suspicious patterns
        dangerous_patterns = ['..', ';', '|', '&', '`', '$', '(', ')']
        if any(pattern in model for pattern in dangerous_patterns):
            return False
        
        return True

    def _is_safe_session_uuid(self, session_uuid: str) -> bool:
        """
        SECURITY: Validate session UUID format to prevent path traversal.
        
        Session UUIDs should be simple identifiers without path separators
        or traversal patterns.
        
        Args:
            session_uuid: The session UUID to validate
            
        Returns:
            True if the UUID is safe, False otherwise
        """
        import re
        
        # Block anything with path separators or traversal patterns
        dangerous_patterns = [
            '/', '\\',  # Path separators (both Unix and Windows)
            '..',       # Directory traversal
            '~',        # Home directory expansion
            '$',        # Variable expansion
            '%',        # Windows variable expansion
            '|', '&', ';', '`', '"', "'",  # Command injection
            '\x00',     # Null byte injection
        ]
        
        # Check for dangerous patterns first
        for pattern in dangerous_patterns:
            if pattern in session_uuid:
                return False
        
        # Allow alphanumeric, hyphens, and underscores (common in generated IDs)
        # This covers:
        # - Standard UUIDs: '123e4567-e89b-12d3-a456-426614174000'
        # - Shortened UUIDs: '1a2b3c4d'
        # - Simple identifiers: 'safe-uuid-123', 'session_abc'
        safe_pattern = r'^[a-zA-Z0-9_-]+$'
        
        if not re.match(safe_pattern, session_uuid):
            return False
        
        return True

    def _is_safe_workspace_path(self, workspace_path: str) -> bool:
        """
        Check if workspace path is safe for use as subprocess cwd.
        
        Validates that the workspace path:
        - Does not contain shell metacharacters
        - Is a proper directory path
        - Does not attempt path traversal beyond allowed boundaries
        """
        # Reject shell metacharacters
        dangerous_chars = [';', '|', '&', '$', '`', '(', ')', '<', '>']
        if any(char in workspace_path for char in dangerous_chars):
            return False
        
        # Check for path traversal patterns
        if '..' in workspace_path and not self._is_valid_traversal(workspace_path):
            return False
        
        return True

    def _is_valid_traversal(self, path: str) -> bool:
        """
        Check if path traversal in workspace path is legitimate.
        
        Some valid paths might contain '..' as part of normal structure,
        but we need to ensure they don't escape allowed boundaries.
        """
        try:
            resolved = Path(path).resolve()
            # Must be within the original workspace or parent (for reading)
            return (self._is_under(resolved, self.workspace_path.resolve()) or 
                    self._is_under(resolved, self.workspace_path.parent.resolve()))
        except Exception:
            return False

    def _is_under(self, path: Path, parent: Path) -> bool:
        """
        Check if path is under parent directory (copied from PathGuardian).
        
        Uses relative_to() for proper containment check.
        """
        try:
            path.relative_to(parent)
            return True
        except ValueError:
            return False

    def _is_safe_task_id(self, task_id: str) -> bool:
        """
        SECURITY: Validate task_id format to prevent injection attacks.
        
        Task IDs should be simple identifiers without dangerous characters.
        
        Args:
            task_id: The task ID to validate
            
        Returns:
            True if the task_id is safe, False otherwise
        """
        # Block dangerous patterns (similar to session UUID but allow more flexibility)
        dangerous_patterns = [
            '/', '\\',  # Path separators
            '..',       # Directory traversal
            '~', '$', '%',  # Variable expansion
            '|', '&', ';', '`', '\x00',  # Command injection
        ]
        
        for pattern in dangerous_patterns:
            if pattern in task_id:
                return False
        
        # Allow alphanumeric, hyphens, underscores, and dots (common in task IDs)
        safe_pattern = r'^[a-zA-Z0-9._-]+$'
        return bool(re.match(safe_pattern, task_id))

    def _sanitize_context_content(self, context: str) -> str:
        """
        SECURITY: Sanitize context content before writing to file.
        
        Prevents potential issues with:
        - Null bytes that could cause file corruption
        - Extremely long lines that could cause DoS
        - Control characters that could be problematic
        
        Args:
            context: Raw context content
            
        Returns:
            Sanitized context content
        """
        # Remove null bytes which can be used for attacks
        if '\x00' in context:
            context = context.replace('\x00', '')
        
        # Limit line length to prevent resource exhaustion
        max_line_length = 10000
        lines = context.split('\n')
        sanitized_lines = []
        for line in lines:
            if len(line) > max_line_length:
                # Truncate extremely long lines
                sanitized_lines.append(line[:max_line_length] + '... [truncated]')
            else:
                sanitized_lines.append(line)
        
        return '\n'.join(sanitized_lines)

    def _create_sanitized_env(self) -> Dict[str, str]:
        """
        SECURITY: Create a sanitized environment for subprocess execution.
        
        Prevents leaking sensitive environment variables to child processes.
        Only includes safe, necessary environment variables.
        
        Returns:
            Dictionary of safe environment variables
        """
        safe_vars = [
            'PATH', 'HOME', 'USER', 'LANG', 'LC_ALL', 'TERM',
            'PYTHONPATH', 'SYSTEMROOT', 'COMSPEC', 'PATHEXT'
        ]
        
        sanitized_env = {}
        for var in safe_vars:
            if var in os.environ:
                sanitized_env[var] = os.environ[var]
        
        return sanitized_env

    def _sanitize_model_param(self, model: str) -> str:
        """
        SECURITY: Sanitize model parameter before using in command.
        
        Args:
            model: The model name to sanitize
            
        Returns:
            Sanitized model name
            
        Raises:
            ValueError: If model name contains dangerous characters
        """
        if not self._is_safe_model_name(model):
            raise ValueError(f"[SECURITY] Invalid model name format: {model}")
        return model

    async def invoke(
        self,
        context: str,
        *,
        session_uuid: Optional[str] = None,
        token: Optional[CancellationToken] = None,
        task_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Non-blocking invoke that collects full response.

        Args:
            context: Markdown context with system prompt
            session_uuid: Unique ID for file isolation (from SwarmSessionManager)
            token: CancellationToken for graceful cancellation
            task_id: Optional task ID for tracking

        Returns:
            Dict structured NEXUS response with:
            - sender: "Claude"
            - action_type: "TALK" or "TOOL_USE"
            - content: Response text
            - tool_use: Optional tool use dict
            - status: "CONTINUE" or "FINISHED"
            - next_agent: Suggested next agent
        """
        chunks = []
        async for chunk in self.invoke_stream(
            context,
            session_uuid=session_uuid,
            token=token,
            task_id=task_id
        ):
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
        # SECURITY: Validate task_id if provided
        if task_id is not None and not self._is_safe_task_id(task_id):
            raise RuntimeError(f"[SECURITY] Invalid task_id format: {task_id}")
        """
        TRUE Non-blocking streaming invoke.

        CRITICAL: Uses async for line in proc.stdout
        This does NOT block the Event Loop (unlike iter(readline))

        Args:
            context: Markdown context with system prompt
            session_uuid: Unique ID for isolation (from SwarmSessionManager)
            token: CancellationToken for graceful cancellation
            task_id: Optional task ID for tracking
            on_token: Optional callback for each token (in addition to yield)

        Yields:
            Text chunks as they arrive from Claude CLI
        """
        token = token or CancellationToken()
        unique_id = session_uuid or str(uuid.uuid4())[:8]

        # SECURITY: Validate session UUID format first (no path separators)
        if not self._is_safe_session_uuid(unique_id):
            raise RuntimeError(f"[SECURITY] Invalid session UUID format: {unique_id}")

        # Write context to isolated file with path validation
        context_file_name = f"claude_context_{unique_id}.md"
        
        # SECURITY: Validate file path to prevent path traversal
        is_valid, resolved_path, message = self.path_guardian.validate_write(context_file_name)
        if not is_valid:
            raise RuntimeError(f"[SECURITY] Invalid context file path: {message}")
        
        context_file = resolved_path
        # SECURITY: Sanitize context content before writing to file
        sanitized_context = self._sanitize_context_content(context)
        context_file.write_text(sanitized_context, encoding="utf-8")

        # Build command with validated parameters
        cmd = [
            str(self.config.cli_path),
            "-p", f"@{context_file}",
            "--dangerously-skip-permissions",
        ]

        # SECURITY: Validate model parameter to prevent injection
        if self.config.model:
            model = self._sanitize_model_param(self.config.model)
            cmd.extend(["--model", model])

        handle: Optional[AsyncProcessHandle] = None

        try:
            # TRUE ASYNC: create_subprocess_exec (NOT Popen!)
            # SECURITY: Validate workspace path before using as cwd
            workspace_cwd = str(self.workspace_path)
            if not self._is_safe_workspace_path(workspace_cwd):
                raise RuntimeError(f"[SECURITY] Unsafe workspace path: {workspace_cwd}")
            
            import os  # Add import for sanitized environment
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=workspace_cwd,
                env=self._sanitized_env,  # SECURITY: Use sanitized environment
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

            # V9.5: Use SafeTaskManager for error tracking
            token.on_cancel(lambda: create_safe_task(cancel_process(), name="claude_cancel"))

            if self.config.verbose:
                print(f"[AsyncClaudeDriver] Started process pid={proc.pid}, uuid={unique_id[:8]}", file=sys.stderr)

            # V11 SYNCHROTRON: Parallel stderr drain to prevent deadlock
            # Problem: If stderr buffer fills (64KB) while we read stdout, subprocess blocks
            # Solution: Background task drains stderr continuously
            stderr_buffer = []

            async def drain_stderr():
                """Background task to drain stderr and prevent buffer fill deadlock."""
                try:
                    async for line_bytes in proc.stderr:
                        stderr_buffer.append(line_bytes.decode('utf-8', errors='replace'))
                except asyncio.CancelledError:
                    pass  # Expected on cleanup

            stderr_task = asyncio.create_task(drain_stderr())

            # TRUE ASYNC STREAMING: async for (NOT iter(readline)!)
            # This yields control to Event Loop between lines
            start_time = datetime.now()
            try:
                async for line_bytes in proc.stdout:
                    token.check()  # Check cancellation between lines

                    # Check timeout
                    elapsed = (datetime.now() - start_time).total_seconds()
                    if elapsed > self.config.timeout:
                        stderr_task.cancel()
                        await handle.terminate_gracefully()
                        raise TimeoutError(f"Claude CLI timed out after {self.config.timeout}s")

                    line = line_bytes.decode('utf-8', errors='replace')
                    if line:
                        yield line
                        if on_token:
                            on_token(line)

                # Wait for process completion with timeout
                try:
                    await asyncio.wait_for(proc.wait(), timeout=10.0)
                except asyncio.TimeoutError:
                    await handle.terminate_gracefully()

                # Cancel stderr task (should be done by now)
                stderr_task.cancel()
                try:
                    await stderr_task
                except asyncio.CancelledError:
                    pass

                if proc.returncode != 0:
                    stderr_content = ''.join(stderr_buffer)
                    raise RuntimeError(f"Claude CLI failed (code {proc.returncode}): {stderr_content}")

                if self.config.verbose:
                    print(f"[AsyncClaudeDriver] Process completed, code={proc.returncode}", file=sys.stderr)

            except asyncio.CancelledError:
                stderr_task.cancel()
                raise

        except asyncio.CancelledError:
            # CRITICAL: Re-raise after cleanup (don't swallow!)
            if self.config.verbose:
                print(f"[AsyncClaudeDriver] Cancelled, cleaning up...", file=sys.stderr)
            raise

        finally:
            # Cleanup: terminate process if still running
            if handle and handle.is_running:
                await handle.terminate_gracefully()

            # Remove from tracking
            self._active_handles.pop(unique_id, None)
            await self._registry.unregister(unique_id)

            # Cleanup context file
            try:
                if context_file.exists():
                    context_file.unlink()
            except Exception:
                pass

    async def cancel_by_uuid(self, session_uuid: str) -> bool:
        """
        Cancel a specific task by its session UUID.

        Args:
            session_uuid: The UUID of the process to cancel

        Returns:
            True if process was found and terminated
        """
        handle = self._active_handles.get(session_uuid)
        if handle:
            await handle.terminate_gracefully()
            self._active_handles.pop(session_uuid, None)
            await self._registry.unregister(session_uuid)
            return True
        return False

    async def cancel_all(self) -> int:
        """
        Cancel all active processes (for Ctrl+C handler).

        Returns:
            Number of processes terminated
        """
        count = 0
        for uuid_key in list(self._active_handles.keys()):
            handle = self._active_handles.pop(uuid_key, None)
            if handle and handle.is_running:
                await handle.terminate_gracefully()
                await self._registry.unregister(uuid_key)
                count += 1
        return count

    @property
    def active_process_count(self) -> int:
        """Get count of active processes."""
        return sum(1 for h in self._active_handles.values() if h.is_running)

    def list_active_processes(self) -> list[Dict[str, Any]]:
        """List all active processes."""
        return [h.to_dict() for h in self._active_handles.values() if h.is_running]

    def _parse_hybrid_response(self, raw_text: str) -> Dict[str, Any]:
        """
        Parse Claude's natural language response with XML tags.

        Claude uses a hybrid format:
        - Natural language response text
        - Tool use in <tool_use name="...">...</tool_use> blocks

        Returns:
            Dict with sender, action_type, content, tool_use, status, next_agent
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
            match = tool_matches[0]
            tool_name = match.group(1)
            tool_args_raw = match.group(2).strip()

            try:
                arguments = json.loads(tool_args_raw)
            except json.JSONDecodeError:
                # Try parsing as key=value
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

        # Get display name and alternate from registry
        registry = get_registry()

        return {
            "sender": registry.get_display_name("claude"),
            "action_type": action_type,
            "content": content,
            "tool_use": tool_use,
            "status": status,
            "next_agent": registry.get_alternate("claude"),
        }

    def _parse_keyvalue_args(self, args_text: str) -> Dict[str, str]:
        """
        Parse arguments in key=value format (fallback if not JSON).
        
        SECURITY: Sanitize keys and values to prevent injection attacks.
        """
        args = {}
        for line in args_text.split('\n'):
            line = line.strip()
            if '=' in line:
                key, value = line.split('=', 1)
                # SECURITY: Sanitize key and value
                key = key.strip()
                value = value.strip()
                
                # Validate key is safe (alphanumeric, underscore, hyphen)
                if not re.match(r'^[a-zA-Z0-9_-]+$', key):
                    continue  # Skip unsafe keys
                
                # Remove null bytes and limit value length
                if '\x00' in value:
                    value = value.replace('\x00', '')
                if len(value) > 10000:  # Prevent DoS with huge values
                    value = value[:10000] + '... [truncated]'
                
                args[key] = value
        return args


    def invoke_sync(
        self,
        context: str,
        *,
        session_uuid: Optional[str] = None,
        task_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Synchronous invoke for backward compatibility.

        DEPRECATED: Use `await invoke()` for async code.

        This method runs the async invoke in a new event loop.
        It's intended for gradual migration from sync to async.

        Args:
            context: Markdown context with system prompt
            session_uuid: Unique ID for file isolation
            task_id: Optional task ID for tracking

        Returns:
            Dict structured NEXUS response

        .. deprecated:: V8.4.4
            Use `await driver.invoke()` in async code.
        """
        raise RuntimeError(
            "invoke_sync() has been removed. Use `await driver.invoke()`."
        )


# Factory function for easy creation
def create_async_claude_driver(
    config: Any,
    workspace_path: Path,
    model: Optional[str] = None
) -> AsyncClaudeDriver:
    """
    Create an AsyncClaudeDriver from a NEXUS config object.

    Args:
        config: NEXUS config object with claude_cli_path, timeout, etc.
        workspace_path: Workspace path for file I/O
        model: Optional model override

    Returns:
        Configured AsyncClaudeDriver
    """
    return AsyncClaudeDriver(AsyncClaudeDriverConfig(
        cli_path=getattr(config, 'claude_cli_path', 'claude'),
        timeout=getattr(config, 'timeout', 300.0),
        model=model or getattr(config, 'claude_sonnet_model', 'claude-sonnet-4-5-20250929'),
        workspace_path=workspace_path,
        verbose=getattr(config, 'verbose', False),
    ))
