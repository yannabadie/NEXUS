"""
AsyncGeminiDriver - TRUE Non-blocking Gemini CLI Driver.

NEXUS V9.0 Async-First Architecture
V9.7.1 - Context Bleeding Fix via HOME Spoofing (replaces V9.7 CWD Isolation)

Same architecture as AsyncClaudeDriver:
- asyncio.create_subprocess_exec (NOT subprocess.Popen)
- async for line in proc.stdout (NOT iter(readline))
- AsyncProcessHandle tracking by session_uuid

V9.7.1 HOME Spoofing (replaces V9.7 CWD Isolation):
- V9.7 CWD Isolation caused "ghost files" (writes to wrong directory)
- V9.7.1 uses HOME spoofing: CWD stays at project root, HOME is isolated
- Gemini CLI stores sessions in ~/.gemini/tmp/<hash(cwd)>/chats/
- Different HOME = Different session storage = Isolation without ghost files

Key Gemini-specific features:
- JSON strict mode (--output-format json)
- YOLO approval mode (--approval-mode yolo)
- Tool restrictions (--allowed-tools)

Session Isolation (V9.7.1):
- When isolated_env is provided: use --resume latest (safe with isolated HOME)
- Without isolated_env: start fresh (no context leakage in shared HOME)
- CWD always stays at project root (no ghost files)

Usage:
    driver = AsyncGeminiDriver(config)

    # With HOME isolation (V9.7.1 - recommended for parallel execution)
    result = await driver.invoke(context, isolated_env=isolated_env_dict)

    # Streaming with isolation
    async for chunk in driver.invoke_stream(context, isolated_env=isolated_env_dict):
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
from typing import AsyncIterator, Optional, Dict, Any, Callable, Tuple
from dataclasses import dataclass, field

from core.async_primitives import CancellationToken, AsyncProcessHandle, create_safe_task
from core.async_primitives.process_handle import get_process_registry
from core.agents.unified_registry import get_registry
from core.utils.json_extractor import extract_json_safe as robust_extract_json
from core.security.path_guardian import PathGuardian


@dataclass
class AsyncGeminiDriverConfig:
    """Configuration for AsyncGeminiDriver."""
    cli_path: str = "gemini"
    timeout: float = 300.0
    model: str = "gemini-3-pro-preview"
    workspace_path: Path = field(default_factory=Path.cwd)
    verbose: bool = False
    use_session_resume: bool = True
    approval_mode: str = "yolo"
    allowed_tools: str = "read_file,list_directory,grep,glob,read_many_files,google_web_search,web_fetch,write_file,edit_file"


class AsyncGeminiDriver:
    """
    TRUE Async Gemini CLI Driver.

    Key differences from sync GeminiDriverV7:
    - Uses asyncio.create_subprocess_exec (NOT subprocess.Popen)
    - Uses async for line in proc.stdout (NOT iter(readline))
    - Tracks processes by session_uuid via AsyncProcessHandle
    - Properly handles asyncio.CancelledError with re-raise

    Session Management:
    - When session_uuid is provided: uses --resume {uuid} for isolation
    - Without session_uuid: uses --resume latest for continuity
    - First invocation creates new session (no --resume)
    """

    def __init__(self, config: AsyncGeminiDriverConfig):
        """
        Initialize async Gemini driver.

        Args:
            config: Driver configuration
        """
        self.config = config
        self.workspace_path = Path(config.workspace_path)
        self.io_buffer = self.workspace_path / "_IO_BUFFER"
        self.io_buffer.mkdir(exist_ok=True)

        # Track active processes by UUID
        self._active_handles: Dict[str, AsyncProcessHandle] = {}

        # Session state for --resume latest
        self._session_active = False

        # Global registry
        self._registry = get_process_registry()

        # SECURITY: Initialize path guardian for validation
        self.path_guardian = PathGuardian(
            workspace_path=self.workspace_path,
            parent_path=self.workspace_path.parent
        )

    async def invoke(
        self,
        context: str,
        *,
        session_uuid: Optional[str] = None,
        token: Optional[CancellationToken] = None,
        task_id: Optional[str] = None,
        isolated_env: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Non-blocking invoke that collects full response.

        Args:
            context: Markdown context with system prompt
            session_uuid: Unique ID for session isolation (from SwarmSessionManager)
            token: CancellationToken for graceful cancellation
            task_id: Optional task ID for tracking
            isolated_env: V9.7.1 - Isolated environment dict with HOME/USERPROFILE.
                         When provided, subprocess uses this env and --resume latest.
                         CWD stays at project root (no ghost files).
                         Different HOME = Different session storage = Isolation.

        Returns:
            Dict structured NEXUS response (JSON parsed)
        """
        chunks = []
        async for chunk in self.invoke_stream(
            context,
            session_uuid=session_uuid,
            token=token,
            task_id=task_id,
            isolated_env=isolated_env,
        ):
            chunks.append(chunk)

        full_response = "".join(chunks)
        return self._extract_and_parse_json(full_response)

    async def invoke_stream(
        self,
        context: str,
        *,
        session_uuid: Optional[str] = None,
        token: Optional[CancellationToken] = None,
        task_id: Optional[str] = None,
        on_token: Optional[Callable[[str], None]] = None,
        isolated_env: Optional[Dict[str, str]] = None,
    ) -> AsyncIterator[str]:
        """
        TRUE Non-blocking streaming invoke.

        Args:
            context: Markdown context with system prompt
            session_uuid: Unique ID for session isolation
            token: CancellationToken for graceful cancellation
            task_id: Optional task ID for tracking
            on_token: Optional callback for each token
            isolated_env: V9.7.1 - Isolated environment dict with HOME/USERPROFILE.
                         When provided, subprocess uses this env and --resume latest.
                         CWD stays at project root (no ghost files).

        Yields:
            Text chunks as they arrive from Gemini CLI

        V9.7.1 Session Isolation (HOME Spoofing):
            - CWD stays at project root (file operations work correctly)
            - HOME is isolated via env parameter (session storage is isolated)
            - isolated_env provided: Use --resume latest (SAFE with isolated HOME)
            - No isolated_env: Start fresh session (no context leakage)
        """
        token = token or CancellationToken()
        unique_id = session_uuid or str(uuid_module.uuid4())[:8]

        # V9.7.1: CWD always at project root (no ghost files)
        effective_io_buffer = self.workspace_path / "_IO_BUFFER"
        effective_io_buffer.mkdir(parents=True, exist_ok=True)

        # SECURITY FIX #2: Sanitize unique_id to prevent path traversal
        sanitized_id = self._sanitize_unique_id(unique_id)

        # SECURITY FIX #3: Sanitize context content
        sanitized_context = self._sanitize_context(context)

        # Write context to file in main workspace's IO buffer
        context_file = effective_io_buffer / f"gemini_context_{sanitized_id}.md"
        context_file.write_text(sanitized_context, encoding="utf-8")

        # V9.7.1: Path relative to workspace (CWD is always workspace root)
        context_file_relative = Path("_IO_BUFFER") / f"gemini_context_{sanitized_id}.md"

        # Find CLI executable
        cli_executable = shutil.which(str(self.config.cli_path))
        if not cli_executable:
            cli_executable = str(self.config.cli_path)

        # SECURITY FIX #1: Validate CLI executable
        if not self._validate_cli_path(cli_executable):
            raise SecurityError(f"Invalid or unsafe CLI path: {cli_executable}")

        # Calculate NEXUS root for --include-directories
        nexus_root = self._get_nexus_root()

        # SECURITY FIX #1: Validate configuration parameters before command construction
        is_valid, error_msg = self._validate_config_params()
        if not is_valid:
            raise SecurityError(f"Invalid configuration: {error_msg}")

        # Build command parts
        cmd = [
            cli_executable,
            "-m", self.config.model,
            "--approval-mode", self.config.approval_mode,
            "--allowed-tools", self.config.allowed_tools,
            "--include-directories", str(nexus_root),
        ]

        # V9.7.1: HOME spoofing replaces V9.7 CWD isolation (which caused ghost files)
        # Gemini CLI stores sessions in ~/.gemini/tmp/<hash(cwd)>/chats/
        # Different HOME = Different session storage = Isolation
        # CWD stays at project root = No ghost files
        if isolated_env:
            # Isolated HOME: --resume latest is SAFE (no context bleeding)
            cmd.extend(["--resume", "latest"])
            if self.config.verbose:
                print(f"[AsyncGeminiDriver] V9.7.1: Isolated HOME, using --resume latest", file=sys.stderr)
        else:
            # Shared HOME: start fresh (no --resume to prevent context leakage)
            if self.config.verbose:
                print(f"[AsyncGeminiDriver] V9.7.1: Shared HOME, starting fresh session", file=sys.stderr)

        # Add prompt file and output format
        cmd.extend(["-p", f"@{context_file_relative}", "-o", "json"])

        handle: Optional[AsyncProcessHandle] = None

        try:
            # TRUE ASYNC: create_subprocess_exec
            # V9.7.1: CWD always at workspace root, env may be isolated
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(self.workspace_path),  # V9.7.1: Always at project root (no ghost files)
                env=isolated_env,  # V9.7.1: Isolated HOME for session separation (None = inherit)
            )

            # Track by UUID
            handle = AsyncProcessHandle(
                proc=proc,
                session_uuid=unique_id,
                task_id=task_id,
                agent_id="gemini",
                created_at=datetime.now()
            )
            self._active_handles[unique_id] = handle
            await self._registry.register(handle)

            # Register cancellation callback
            async def cancel_process():
                if handle and handle.is_running:
                    await handle.terminate_gracefully()

            # V9.5: Use SafeTaskManager for error tracking
            token.on_cancel(lambda: create_safe_task(cancel_process(), name="gemini_cancel"))

            if self.config.verbose:
                print(f"[AsyncGeminiDriver] Started process pid={proc.pid}, uuid={unique_id[:8]}", file=sys.stderr)

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

            # TRUE ASYNC STREAMING
            start_time = datetime.now()
            try:
                async for line_bytes in proc.stdout:
                    token.check()

                    # Check timeout
                    elapsed = (datetime.now() - start_time).total_seconds()
                    if elapsed > self.config.timeout:
                        stderr_task.cancel()
                        await handle.terminate_gracefully()
                        raise TimeoutError(f"Gemini CLI timed out after {self.config.timeout}s")

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
                    raise RuntimeError(f"Gemini CLI failed (code {proc.returncode}): {stderr_content}")

            except asyncio.CancelledError:
                stderr_task.cancel()
                raise

            # Mark session as active for future --resume latest
            if self.config.use_session_resume:
                self._session_active = True

            if self.config.verbose:
                print(f"[AsyncGeminiDriver] Process completed, code={proc.returncode}", file=sys.stderr)

        except asyncio.CancelledError:
            if self.config.verbose:
                print(f"[AsyncGeminiDriver] Cancelled, cleaning up...", file=sys.stderr)
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

    @property
    def active_process_count(self) -> int:
        """Get count of active processes."""
        return sum(1 for h in self._active_handles.values() if h.is_running)

    def list_active_processes(self) -> list[Dict[str, Any]]:
        """List all active processes."""
        return [h.to_dict() for h in self._active_handles.values() if h.is_running]

    def _get_nexus_root(self) -> Path:
        """Calculate NEXUS root directory for --include-directories."""
        resolved_workspace = self.workspace_path.resolve()
        parent_dir = resolved_workspace.parent
        grandparent = parent_dir.parent

        # Handle child workspaces in GENERATION_ACTIVE
        if grandparent.name == "GENERATION_ACTIVE":
            return grandparent.parent
        return grandparent

    def _extract_and_parse_json(self, output_text: str) -> Dict[str, Any]:
        """
        Extract and parse JSON from Gemini output.

        Gemini CLI returns JSON wrapped in {"response": "...", "stats": {...}}
        The actual NEXUS JSON is inside response["response"] as string.
        """
        try:
            gemini_output = json.loads(output_text)

            # Handle wrapper format
            if "response" in gemini_output and isinstance(gemini_output["response"], str):
                result, error = robust_extract_json(gemini_output["response"], verbose=True)
                if result is not None:
                    return self._normalize_response(result)
            else:
                return self._normalize_response(gemini_output)

        except json.JSONDecodeError:
            # Try to extract JSON from text
            result, error = robust_extract_json(output_text, verbose=True)
            if result is not None:
                return self._normalize_response(result)

        # Fallback for extraction failure
        registry = get_registry()
        return {
            "sender": registry.get_display_name("gemini"),
            "action_type": "TALK",
            "content": f"[JSON extraction failed - raw response]\n{output_text[:1000]}",
            "status": "CONTINUE",
            "next_agent": registry.get_alternate("gemini"),
            "_json_extraction_failed": True,
        }

    def _normalize_response(self, data: Any) -> Dict[str, Any]:
        """Normalize response to standard NEXUS format."""
        registry = get_registry()

        # Handle list response (Evolution Mutations)
        if isinstance(data, list):
            return {
                "sender": registry.get_display_name("gemini"),
                "action_type": "TALK",
                "content": json.dumps(data),
                "status": "FINISHED",
                "next_agent": registry.get_alternate("gemini"),
            }

        # Ensure required fields
        if isinstance(data, dict):
            if "sender" not in data:
                data["sender"] = registry.get_display_name("gemini")
            if "action_type" not in data:
                data["action_type"] = "TALK"
            if "status" not in data:
                data["status"] = "CONTINUE"
            if "next_agent" not in data:
                data["next_agent"] = registry.get_alternate("gemini")
            return data

        # Fallback for unexpected format
        return {
            "sender": registry.get_display_name("gemini"),
            "action_type": "TALK",
            "content": str(data),
            "status": "CONTINUE",
            "next_agent": registry.get_alternate("gemini"),
        }

    # SECURITY FIXES: Helper methods for input validation

    def _sanitize_unique_id(self, unique_id: str) -> str:
        """
        SECURITY FIX #2: Sanitize unique_id to prevent path traversal.

        Only allows alphanumeric characters, hyphens, and underscores.
        Replaces any other characters with safe alternatives.

        Args:
            unique_id: The ID to sanitize

        Returns:
            Sanitized ID safe for use in filenames
        """
        if not unique_id:
            return "default"

        # Only allow alphanumeric, hyphens, underscores, and dots (for UUIDs)
        sanitized = re.sub(r'[^a-zA-Z0-9._-]', '_', str(unique_id))

        # Limit length to prevent buffer overflow issues
        max_length = 128
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length]

        # Ensure it doesn't start with a dot (hidden files)
        if sanitized.startswith('.'):
            sanitized = 'x' + sanitized

        return sanitized

    def _validate_cli_path(self, cli_path: str) -> bool:
        """
        SECURITY FIX #1: Validate CLI executable path.

        Checks that:
        1. Path is not empty
        2. Path contains no shell metacharacters
        3. Binary exists and is executable
        4. The command name is valid (with or without Windows extensions)

        Args:
            cli_path: Path to CLI executable

        Returns:
            True if valid, False otherwise
        """
        if not cli_path:
            return False

        # Check for shell metacharacters
        dangerous_chars = [';', '|', '&', '$', '`', '>', '<', '(', ')']
        if any(char in cli_path for char in dangerous_chars):
            return False

        # Get the basename to check the actual command name
        cli_name = Path(cli_path).name

        # Only allow expected CLI commands (with or without Windows extensions)
        base_commands = {'gemini', 'gemini-cli', 'npx', 'node'}
        
        # Check if the base name matches (strip Windows extensions if present)
        # Windows extensions: .cmd, .exe, .bat, .com, .ps1
        cli_name_base = cli_name
        for ext in ['.cmd', '.exe', '.bat', '.com', '.ps1']:
            if cli_name.lower().endswith(ext):
                cli_name_base = cli_name[:-len(ext)]
                break
        
        if cli_name_base not in base_commands:
            # Check if it's in PATH and resolves to an allowed command
            resolved = shutil.which(cli_path)
            if not resolved:
                return False
            resolved_name = Path(resolved).name
            
            # Strip Windows extensions from resolved name too
            resolved_name_base = resolved_name
            for ext in ['.cmd', '.exe', '.bat', '.com', '.ps1']:
                if resolved_name.lower().endswith(ext):
                    resolved_name_base = resolved_name[:-len(ext)]
                    break
            
            if resolved_name_base not in base_commands:
                return False

        return True

    def _validate_config_params(self) -> Tuple[bool, str]:
        """
        SECURITY FIX #1: Validate configuration parameters before command construction.

        Checks that model, approval_mode, and allowed_tools contain safe values.

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Validate model format (alphanumeric, hyphens, dots, slashes)
        model_pattern = r'^[a-zA-Z0-9._/-]+$'
        if not re.match(model_pattern, self.config.model):
            return False, f"Invalid model name: {self.config.model}"

        # Validate approval_mode
        allowed_modes = {'yolo', 'suggest', 'auto', 'manual'}
        if self.config.approval_mode not in allowed_modes:
            return False, f"Invalid approval_mode: {self.config.approval_mode}"

        # Validate allowed_tools (comma-separated tool names)
        tools_pattern = r'^[a-zA-Z0-9_,-]+$'
        if not re.match(tools_pattern, self.config.allowed_tools):
            return False, f"Invalid allowed_tools format: {self.config.allowed_tools}"

        return True, "OK"

    def _sanitize_context(self, context: str) -> str:
        """
        SECURITY FIX #3: Sanitize context content before writing to file.

        Prevents potential content-based attacks by:
        1. Limiting maximum size
        2. Removing null bytes
        3. Normalizing line endings

        Args:
            context: The context content to sanitize

        Returns:
            Sanitized context
        """
        if not context:
            return ""

        # Convert to string if needed
        context_str = str(context)

        # Limit maximum size (10MB)
        max_size = 10 * 1024 * 1024
        if len(context_str) > max_size:
            context_str = context_str[:max_size]

        # Remove null bytes
        context_str = context_str.replace('\x00', '')

        # Normalize line endings
        context_str = context_str.replace('\r\n', '\n').replace('\r', '\n')

        return context_str

    def invoke_sync(
        self,
        context: str,
        *,
        session_uuid: Optional[str] = None,
        task_id: Optional[str] = None,
        isolated_env: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Synchronous invoke for backward compatibility.

        DEPRECATED: Use `await invoke()` for async code.

        This method runs the async invoke in a new event loop.
        It's intended for gradual migration from sync to async.

        Args:
            context: Markdown context with system prompt
            session_uuid: Unique ID for session isolation
            task_id: Optional task ID for tracking
            isolated_env: V9.7.1 - Isolated environment for session isolation

        Returns:
            Dict structured NEXUS response (JSON parsed)

        .. deprecated:: V8.4.4
            Use `await driver.invoke()` in async code.
        """
        raise RuntimeError(
            "invoke_sync() has been removed. Use `await driver.invoke()`."
        )


class SecurityError(Exception):
    """Raised when a security validation fails."""
    pass


# Factory function
def create_async_gemini_driver(
    config: Any,
    workspace_path: Path,
    model: Optional[str] = None
) -> AsyncGeminiDriver:
    """
    Create an AsyncGeminiDriver from a NEXUS config object.

    Args:
        config: NEXUS config object
        workspace_path: Workspace path for file I/O
        model: Optional model override

    Returns:
        Configured AsyncGeminiDriver
    """
    return AsyncGeminiDriver(AsyncGeminiDriverConfig(
        cli_path=getattr(config, 'gemini_cli_path', 'gemini'),
        timeout=getattr(config, 'timeout', 300.0),
        model=model or getattr(config, 'gemini_default_model', 'gemini-3-pro-preview'),
        workspace_path=workspace_path,
        verbose=getattr(config, 'verbose', False),
        use_session_resume=getattr(config, 'gemini_persistent_mode', True),
    ))
