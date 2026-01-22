"""
Gemini Driver V7 Chrysalis - JSON Strict Mode

Gemini reste en mode JSON strict (contrairement à Claude qui est hybride).

V7 Features:
- Gemini 3 Pro Preview for all tasks (unified model)
- Model routing via ModelRouter.select_gemini_model()

V7 Sprint 12: Session Resume Mode (DEFAULT)
- Uses --resume latest for context persistence between invocations
- Automatic session management (no manual session ID tracking)
- First invocation creates session, subsequent invocations resume it
- Benefits: ~5s latency (vs ~15s without resume), cached context tokens
- IMPORTANT: First call does NOT use --resume (creates new session)

V9.7.1: Session Isolation via HOME Spoofing (replaces V9.7 CWD Isolation)
- V9.7 CWD Isolation caused "ghost files" (writes to wrong directory)
- V9.7.1 uses HOME spoofing: CWD stays at project root, HOME is isolated
- Gemini CLI stores sessions in ~/.gemini/tmp/<hash(cwd)>/chats/
- Different HOME = Different session storage = Isolation without ghost files

Note: PTY mode was removed in V7.6 cleanup (never worked, gemini_pty_mode=False).
      Archived to: docs/archive/pty_mode_v7_archived.py
"""
import asyncio
import subprocess
import json
import sys
import time
import atexit
import logging
import threading

# V9 Cyborg Hardening: Logger for exception tracking
_logger = logging.getLogger(__name__)
import uuid as uuid_module
from pathlib import Path
from typing import Dict, Optional, Callable, List, Any

# V7.5 HIVE MIND: Centralized JSON extraction
from core.utils.json_extractor import extract_json_safe as robust_extract_json

# V8.8: Output Guard - System prompt leak prevention (OWASP LLM01:2025)
from core.security import get_output_guard
# V7.7 Phase 15: Stream parser for real-time response display
from core.utils.stream_parser import parse_stream_chunk, is_result_message, extract_stats
# V8.4.0: Unified agent registry
from core.agents.unified_registry import get_registry
# V8.4.5: Structured driver logging
from core.logging.driver_logger import get_driver_logger

# Initialize driver logger
_logger = get_driver_logger("gemini")


# Global reference for cleanup at exit
# V9.8 DETOX: Thread-safe with lock (for multi-tenant/concurrent use)
_active_processes: List[subprocess.Popen] = []
_active_processes_lock = threading.Lock()
_persistent_process: Optional[subprocess.Popen] = None  # Singleton persistent process

# PTY mode removed in V7.6 cleanup - see docs/archive/pty_mode_v7_archived.py


def _cleanup_processes():
    """Kill any remaining Gemini processes at exit.

    Iterates through registered active processes and terminates them.
    Also handles cleanup of the singleton persistent process if it exists.
    Uses thread-safe locking to ensure safe access to the process list.

    Args:
        None

    Returns:
        None

    Raises:
        None
    """
    global _persistent_process

    # Cleanup persistent process first
    if _persistent_process:
        try:
            _persistent_process.close()
        except Exception as e:
            _logger.debug(f"[GeminiDriver] Persistent process cleanup warning: {e}")
        _persistent_process = None

    # V9.8 DETOX: Thread-safe cleanup of one-shot processes
    with _active_processes_lock:
        for proc in _active_processes:
            try:
                if proc.poll() is None:  # Still running
                    proc.terminate()
                    proc.wait(timeout=2)
            except Exception as e:
                _logger.debug(f"[GeminiDriver] Process terminate failed: {e}")
                try:
                    proc.kill()
                except Exception as e2:
                    _logger.warning(f"[GeminiDriver] Process kill also failed: {e2}")
        _active_processes.clear()


# Register cleanup handler
atexit.register(_cleanup_processes)


class GeminiDriverV7:
    """
    Driver pour Gemini CLI - Mode JSON strict

    V7: Supports model selection and agent tracking
    V7 Sprint 12: Persistent mode with automatic fallback
    """

    def __init__(
        self,
        config: Any,
        workspace_path: Path,
        model: Optional[str] = None,
        agent_id: Optional[str] = None,
        persistent: Optional[bool] = None
    ):
        """Initializes the GeminiDriverV7.

        Sets up the driver with configuration, workspace path, and session management settings.
        Configures the model, timeout, and session persistence behavior based on the provided config.

        Args:
            config: Configuration object containing settings like gemini_cli_path, timeout, etc.
            workspace_path: Path object pointing to the current workspace directory.
            model: Optional string specifying the Gemini model to use.
            agent_id: Optional string identifier for the agent using this driver.
            persistent: Optional boolean to enable legacy persistent mode.

        Returns:
            None

        Raises:
            None
        """
        self.cli_path = config.gemini_cli_path
        self.workspace_path = workspace_path
        self.io_buffer = workspace_path / "_IO_BUFFER"
        # V7: Increase default timeout to 300s for reasoning models
        self.timeout = config.timeout if hasattr(config, 'timeout') else 300

        # V7: Model and agent tracking (default: Gemini 3 Pro Preview)
        self.model = model or getattr(config, 'gemini_default_model', 'gemini-3-pro-preview')
        self.agent_id = agent_id or "gemini_primary"

        # V7 Sprint 12: Session management (DEFAULT: enabled)
        # Sessions are automatically saved by Gemini CLI, --resume latest restores context
        # First call creates session, subsequent calls use --resume latest
        self.use_session_resume = getattr(config, 'gemini_persistent_mode', True)
        self._session_active = False  # Track if we have a session to resume
        self.config = config

        # Legacy persistent process (disabled - use session resume instead)
        self.persistent = False  # Disabled: -i with stdin doesn't work
        self._persistent_process = None

    def _init_persistent(self):
        """Legacy method - persistent mode removed in V7 cleanup.

        Session persistence now uses --resume latest instead of persistent process.
        This method is kept for API compatibility but does nothing.
        """
        # Persistent process mode was removed - use session resume instead
        self._persistent_process = None

    def _validate_output(self, response: Dict) -> Dict:
        """
        V8.8: Validate LLM output for system prompt leaks (OWASP LLM01:2025).

        Checks response content for potential information leakage and logs warnings.
        Does not block responses by default (block_on_leak=False), but provides
        visibility into potential security issues.

        Args:
            response: Parsed LLM response dict

        Returns:
            Response dict (unchanged, or with sanitized content if leak detected)
        """
        output_guard = get_output_guard()

        # Extract content to validate
        content = response.get("content", "")
        if not content or not isinstance(content, str):
            return response

        validation = output_guard.validate(content)

        if validation.leak_type.value != "none":
            _logger.warning(
                f"[OUTPUT GUARD] Potential leak detected: {validation.leak_type.value} "
                f"(severity: {validation.leak_severity.value}) - {validation.reason}"
            )
            # Use sanitized output if available
            if validation.sanitized_output:
                response = response.copy()
                response["content"] = validation.sanitized_output
                response["_output_sanitized"] = True
                response["_leak_type"] = validation.leak_type.value

        return response

    def _enforce_json_format(self, context: str) -> str:
        """
        V9.1.1: Add JSON enforcement suffix to context.

        Since Gemini CLI doesn't support --response-mime-type application/json,
        we enforce structured JSON output via strong prompt engineering.

        Args:
            context: Original context markdown

        Returns:
            Context with JSON enforcement suffix
        """
        json_enforcement = """

---
**CRITICAL: YOUR RESPONSE MUST BE VALID JSON**

You MUST respond with a single JSON object. Example format:
{"sender": "Gemini", "action_type": "TALK", "content": "your message", "status": "CONTINUE"}

Rules:
- Start with `{`, end with `}`
- Use double quotes " for all strings (NOT single quotes ')
- NO text before or after the JSON
- NO markdown code blocks (```) around the JSON
- Use true/false (lowercase), not True/False
"""
        return context + json_enforcement

    def invoke(
        self,
        context: str,
        session_uuid: Optional[str] = None,
        isolated_env: Optional[Dict[str, str]] = None
    ) -> Dict:
        """Invokes the Gemini CLI with the provided markdown context.

        V7 Sprint 12: Uses session resume for context persistence.
        V9.7.1: Session isolation via HOME spoofing (replaces V9.7 CWD isolation).

        Args:
            context: Markdown context string containing the system prompt and message history.
            session_uuid: Optional session UUID used for NEXUS tracking and file naming.
            isolated_env: V9.7.1 - Isolated environment dictionary containing HOME/USERPROFILE.
                When provided, the subprocess uses this environment and `--resume latest`.
                The CWD remains at the project root to prevent ghost files.
                Different HOME paths result in different session storage, providing isolation.

        Returns:
            A dictionary containing the structured NEXUS response (parsed JSON).

        Raises:
            RuntimeError: If the Gemini CLI fails to execute or returns an error code.
            TimeoutError: If the execution time exceeds the configured timeout.
        """
        return self._invoke_subprocess(context, session_uuid=session_uuid, isolated_env=isolated_env)

    def invoke_stream(
        self,
        context: str,
        on_token: Callable[[str], None],
        session_uuid: Optional[str] = None,
        isolated_env: Optional[Dict[str, str]] = None
    ) -> Dict:
        """Invokes the Gemini CLI with streaming output (V7.7 Phase 15).

        Streams text tokens in real-time via the provided callback, then returns
        the full parsed JSON response.

        V9.7.1: Session isolation via HOME spoofing.

        Args:
            context: Markdown context string containing the system prompt and message history.
            on_token: Callback function that receives each text chunk as it is streamed.
            session_uuid: Optional session UUID used for NEXUS tracking.
            isolated_env: V9.7.1 - Isolated environment dictionary for session isolation.

        Returns:
            A dictionary containing the structured NEXUS response (parsed JSON).

        Raises:
            RuntimeError: If the Gemini CLI fails to execute or returns an error code.
            TimeoutError: If the execution time exceeds the configured timeout.
        """
        return self._invoke_subprocess_stream(context, on_token, session_uuid=session_uuid, isolated_env=isolated_env)

    async def send_message_async(
        self,
        prompt: str,
        session_uuid: Optional[str] = None,
        isolated_env: Optional[Dict[str, str]] = None
    ) -> Dict:
        """
        Async bridge method for HiveMind phases compatibility (V8.4.5).

        Wraps sync invoke() in asyncio.to_thread() for non-blocking execution.
        This allows HiveMind phases to call driver methods without blocking
        the event loop, enabling true concurrent execution.

        V9.7.1: Session isolation via HOME spoofing.

        Args:
            prompt: Context markdown with system prompt
            session_uuid: Optional session UUID for NEXUS tracking
            isolated_env: V9.7.1 - Isolated environment for session isolation

        Returns:
            Dict structured NEXUS response (same as invoke())

        Note:
            This is a bridge method for backward compatibility with async HiveMind
            phases. New code should use AsyncGeminiDriver for full async support.
        """
        return await asyncio.to_thread(self.invoke, prompt, session_uuid, isolated_env)

    def invoke_with_retry(
        self,
        context: str,
        max_retries: int = 3,
        session_uuid: Optional[str] = None,
        isolated_env: Optional[Dict[str, str]] = None
    ) -> Dict:
        """
        Invoke with exponential backoff and jitter (V8.4.5).

        Retries on transient failures (timeout, rate limit, server errors)
        with increasing delays and randomized jitter to prevent thundering herd.

        V9.7.1: Session isolation via HOME spoofing.

        Args:
            context: Context markdown with system prompt
            max_retries: Maximum number of retry attempts (default: 3)
            session_uuid: Optional session UUID for NEXUS tracking
            isolated_env: V9.7.1 - Isolated environment for session isolation

        Returns:
            Dict structured NEXUS response

        Raises:
            RuntimeError: If all retries fail

        Algorithm:
            wait_time = (2 ** attempt) + random.uniform(0, 1)
            - Attempt 0: 1s + jitter (0-1s)
            - Attempt 1: 2s + jitter
            - Attempt 2: 4s + jitter
        """
        import random

        last_error = None

        for attempt in range(max_retries):
            try:
                return self.invoke(context, session_uuid=session_uuid, isolated_env=isolated_env)

            except (TimeoutError, RuntimeError) as e:
                last_error = e
                error_str = str(e).lower()

                # Don't retry on auth errors or invalid requests
                if any(x in error_str for x in ["auth", "invalid", "denied", "permission"]):
                    raise

                if attempt < max_retries - 1:
                    # Exponential backoff with jitter
                    base_wait = 2 ** attempt
                    jitter = random.uniform(0, 1)
                    wait_time = base_wait + jitter

                    _logger.warning(
                        f"Retry {attempt + 1}/{max_retries} after {wait_time:.1f}s",
                        error=str(e)[:100]
                    )
                    time.sleep(wait_time)

            except Exception as e:
                # Unknown error - don't retry
                raise

        # All retries failed
        raise RuntimeError(
            f"Gemini invocation failed after {max_retries} attempts: {last_error}"
        )

    # NOTE: PTY and legacy persistent methods removed in V7.6 cleanup
    # See: docs/archive/pty_mode_v7_archived.py

    def _invoke_subprocess(
        self,
        context: str,
        session_uuid: Optional[str] = None,
        isolated_env: Optional[Dict[str, str]] = None
    ) -> Dict:
        """
        Invoke Gemini using subprocess (original method).

        V9.7.1: HOME spoofing replaces V9.7 CWD isolation (which caused ghost files).
        - CWD stays at project root (file operations work correctly)
        - HOME is isolated via env parameter (session storage is isolated)

        Args:
            context: Context markdown
            session_uuid: Optional session UUID for NEXUS tracking (file naming)
            isolated_env: V9.7.1 - Isolated environment dict with HOME/USERPROFILE.
                         When provided, uses this env and --resume latest.
                         CWD stays at project root (no ghost files).

        Returns:
            Dict structured NEXUS response

        Raises:
            RuntimeError: If the Gemini CLI fails to execute or returns an error code.
            TimeoutError: If the execution time exceeds the configured timeout.
        """
        import sys
        import shutil

        # V8.1.6: Generate unique ID for thread-safe file access
        unique_id = session_uuid or str(uuid_module.uuid4())[:8]

        # V9.7.1: CWD always at project root (no ghost files)
        # IO buffer in main workspace, not isolated
        effective_io_buffer = self.workspace_path / "_IO_BUFFER"
        effective_io_buffer.mkdir(parents=True, exist_ok=True)

        # V9.1.1: Enforce JSON format via prompt suffix
        enforced_context = self._enforce_json_format(context)

        # Write context to file with unique ID (in main workspace's IO buffer)
        context_file = effective_io_buffer / f"gemini_context_{unique_id}.md"
        context_file.write_text(enforced_context, encoding="utf-8")

        # V9.7.1: Path relative to workspace (CWD is always workspace root now)
        context_file_relative = Path("_IO_BUFFER") / f"gemini_context_{unique_id}.md"

        output_file = effective_io_buffer / f"gemini_output_{unique_id}.json"

        # Clear previous output file (now unique, so less likely to exist)
        if output_file.exists():
            output_file.unlink()

        # Find the actual CLI path (handles PATH lookup)
        cli_executable = shutil.which(str(self.cli_path))
        if not cli_executable:
            # Fallback to original path if shutil.which fails
            cli_executable = str(self.cli_path)

        # Build command - use shell=True on Windows for proper PATH resolution
        # and handling of .cmd/.bat files (common for npm global installs)
        import platform
        use_shell = platform.system() == "Windows"

        # Include project root (20_NEXUS) for READ access to foundation files
        # For parent (NEXUS_V7_CHRYSALIS): workspace.parent.parent = 20_NEXUS
        # For children (GENERATION_ACTIVE/child_id): workspace.parent.parent.parent = 20_NEXUS
        # NOTE: Must resolve() first to handle relative paths correctly
        resolved_workspace = self.workspace_path.resolve()
        parent_dir = resolved_workspace.parent  # NEXUS_V7_CHRYSALIS or child_id
        grandparent = parent_dir.parent  # 20_NEXUS or GENERATION_ACTIVE

        # FIX: If grandparent is GENERATION_ACTIVE, we're in a child - go up one more level
        if grandparent.name == "GENERATION_ACTIVE":
            nexus_root = grandparent.parent  # 20_NEXUS
        else:
            nexus_root = grandparent  # Already at 20_NEXUS

        # Allowed tools for YOLO mode (auto-approved)
        # - Read tools: Can read anywhere (parent code via --include-directories)
        # - Write tools: SANDBOXED to workspace (cwd) by Gemini CLI design
        # - NO run_shell_command: Too dangerous for auto-approval
        allowed_tools = "read_file,list_directory,grep,glob,read_many_files,google_web_search,web_fetch,write_file,edit_file"

        # V9.7.1: HOME spoofing replaces V9.7 CWD isolation
        # Gemini CLI stores sessions in ~/.gemini/tmp/<hash(cwd)>/chats/
        # Different HOME = Different session storage = Isolation
        # CWD stays at project root = No ghost files
        #
        # If isolated_env: isolated HOME → --resume latest is safe
        # Else: shared HOME → start fresh (no context leakage)
        if isolated_env:
            # V9.7.1: Isolated HOME - --resume latest is SAFE
            # Different HOME = different Gemini CLI session storage
            resume_flag = "--resume latest"
            _logger.debug(
                "V9.7.1 HOME spoofing: --resume latest with isolated HOME"
            )
        else:
            # Shared HOME - start fresh to prevent context leakage
            resume_flag = ""
            if self._session_active:
                _logger.debug(
                    "Starting FRESH session (no isolated_env). "
                    "Pass isolated_env for session persistence in parallel tasks."
                )
        approval_mode = "--approval-mode yolo"  # Safe: write ops sandboxed to workspace

        if use_shell:
            # Shell command string for Windows
            # --allowed-tools: Only auto-approve read tools (write/shell require confirmation)
            # --include-directories: Give Gemini READ access to parent NEXUS code
            command = f'"{cli_executable}" -m {self.model} {approval_mode} --allowed-tools {allowed_tools} --include-directories "{nexus_root}" {resume_flag} -p @"{context_file_relative}" -o json'
        else:
            # List format for Unix
            cmd_parts = [cli_executable, "-m", self.model, "--approval-mode", "yolo", "--allowed-tools", allowed_tools, "--include-directories", str(nexus_root)]
            # V9.7.1: Add --resume latest only when using isolated HOME
            if isolated_env:
                cmd_parts.extend(["--resume", "latest"])
            cmd_parts.extend(["-p", f"@{context_file_relative}", "-o", "json"])
            command = cmd_parts

        try:
            _logger.debug("Invoking Gemini", model=self.model, timeout=self.timeout)
            if use_shell:
                _logger.debug("Command", cmd=command[:200] if len(str(command)) > 200 else command)

            # Use Popen with polling loop to allow CTRL+C interruption
            # V9.7.1: CWD always at workspace root, env may be isolated
            proc = subprocess.Popen(
                command,
                cwd=str(self.workspace_path),  # V9.7.1: Always at project root (no ghost files)
                env=isolated_env,  # V9.7.1: Isolated HOME for session separation (None = inherit)
                shell=use_shell,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                errors='replace'
            )

            # V9.8 DETOX: Thread-safe process tracking
            with _active_processes_lock:
                _active_processes.append(proc)

            try:
                import threading
                import queue

                start_time = time.time()
                stdout_data = []
                stderr_data = []
                output_queue = queue.Queue()

                def read_stream(stream: Any, stream_name: str, data_list: List[str]) -> None:
                    """Read stream in thread and queue lines for display."""
                    try:
                        for line in iter(stream.readline, ''):
                            if line:
                                data_list.append(line)
                                output_queue.put((stream_name, line.strip()))
                    except Exception as e:
                        _logger.debug(f"[GeminiDriver] Stream reader ({stream_name}) ended: {e}")

                # Start reader threads
                stdout_thread = threading.Thread(target=read_stream, args=(proc.stdout, 'stdout', stdout_data))
                stderr_thread = threading.Thread(target=read_stream, args=(proc.stderr, 'stderr', stderr_data))
                stdout_thread.daemon = True
                stderr_thread.daemon = True
                stdout_thread.start()
                stderr_thread.start()

                # Poll loop - shows real activity
                last_activity = ""
                while proc.poll() is None:
                    elapsed = time.time() - start_time
                    if elapsed > self.timeout:
                        print("\r" + " " * 80 + "\r", end="", file=sys.stderr)
                        proc.kill()
                        proc.wait()
                        raise TimeoutError(f"Gemini CLI timed out after {self.timeout}s")

                    # Check for new output
                    try:
                        while True:
                            stream_name, line = output_queue.get_nowait()
                            if line and len(line) > 3:
                                # Show real activity from Gemini
                                last_activity = line[:60] + "..." if len(line) > 60 else line
                    except queue.Empty:
                        pass

                    # Show status with real activity or waiting message
                    status = f"🤖 Gemini [{int(elapsed)}s]"
                    if last_activity:
                        print(f"\r{status}: {last_activity[:50]}", end="", file=sys.stderr)
                    else:
                        print(f"\r{status}: Processing...", end="", file=sys.stderr)

                    time.sleep(0.2)

                # Wait for threads to finish
                stdout_thread.join(timeout=1)
                stderr_thread.join(timeout=1)

                # Clear status line
                print("\r" + " " * 80 + "\r", end="", file=sys.stderr)

                # Combine outputs
                stdout = ''.join(stdout_data)
                stderr = ''.join(stderr_data)

            except KeyboardInterrupt:
                print("\n[DEBUG] Interrupt received, killing Gemini process...", file=sys.stderr)
                proc.kill()
                proc.wait()
                raise
            finally:
                # V9.8 DETOX: Thread-safe process removal
                with _active_processes_lock:
                    if proc in _active_processes:
                        _active_processes.remove(proc)

            # Create result-like object for compatibility
            class Result:
                pass
            result = Result()
            result.returncode = proc.returncode
            result.stdout = stdout
            result.stderr = stderr

            _logger.debug("Gemini returned", code=result.returncode, stdout_len=len(result.stdout))

            if result.returncode != 0:
                error_msg = result.stderr or result.stdout or "Unknown error"
                _logger.error("Gemini error", error=error_msg[:500])
                raise RuntimeError(f"Gemini CLI failed (code {result.returncode}): {error_msg}")

            # Get output from stdout
            output_text = result.stdout

            # Also save to file for debugging
            output_file.write_text(output_text, encoding="utf-8")

            try:
                gemini_output = json.loads(output_text)

                # Gemini CLI wraps response in {"response": "...", "stats": {...}}
                # The actual NEXUS JSON is inside response["response"] as markdown string
                if "response" in gemini_output and isinstance(gemini_output["response"], str):
                    # Extract JSON from markdown code block
                    extracted_data = self._extract_json(gemini_output["response"])
                else:
                    # Direct JSON (shouldn't happen with gemini CLI -o json)
                    extracted_data = gemini_output

            except json.JSONDecodeError as e:
                # Try to extract JSON from text
                extracted_data = self._extract_json(output_text)

            # V7 Sprint 12: Mark session as active for future --resume latest
            if self.use_session_resume:
                self._session_active = True

            # CRITICAL FIX: Handle list response (Evolution Mutations)
            if isinstance(extracted_data, list):
                # Wrap list in a standard message structure to satisfy Orchestrator
                # V8.4.0: Use registry for display name
                registry = get_registry()
                list_response = {
                    "sender": registry.get_display_name("gemini"),
                    "action_type": "TALK",
                    "content": json.dumps(extracted_data), # Pass the list as a string content
                    "status": "FINISHED"
                }
                # V8.8: Validate output for leaks
                return self._validate_output(list_response)

            # V8.8: Validate output for system prompt leaks before returning
            return self._validate_output(extracted_data)

        except TimeoutError:
            # Re-raise timeout from the inner try block
            raise
        finally:
            # V8.1.6: Cleanup unique files
            for f in [context_file, output_file]:
                try:
                    if f.exists():
                        f.unlink()
                except Exception:
                    pass  # Best effort cleanup

    def _extract_json(self, text: str, fallback_to_error: bool = True) -> Dict:
        """
        Extract JSON from text using centralized robust extractor.

        V7.5 HIVE MIND: Uses core.utils.json_extractor for consistent parsing
        across all modules. Supports START_JSON/END_JSON markers.

        Args:
            text: Raw text that might contain JSON
            fallback_to_error: If True, return error dict instead of raising

        Returns:
            Dict (extracted JSON or error fallback)

        Raises:
            ValueError: If no JSON found and fallback_to_error is False
        """
        # Use centralized extractor with required NEXUS keys
        result, error = robust_extract_json(
            text,
            verbose=True
        )

        if result is not None:
            return result

        # No JSON found - provide fallback or raise
        if fallback_to_error:
            # V8.4.0: Use registry for display names and alternation
            registry = get_registry()
            content_preview = text[:1000] if text else "[Empty response]"
            return {
                "sender": registry.get_display_name("gemini"),
                "action_type": "TALK",
                "content": f"[JSON extraction failed: {error} - raw response]\n{content_preview}",
                "status": "CONTINUE",
                "next_agent": registry.get_alternate("gemini"),
                "_json_extraction_failed": True,
                "_raw_response_preview": text[:500] if text else ""
            }
        else:
            raise ValueError(f"Could not extract JSON from Gemini response: {text[:500]}...")

    def _invoke_subprocess_stream(
        self,
        context: str,
        on_token: Callable[[str], None],
        session_uuid: Optional[str] = None,
        isolated_env: Optional[Dict[str, str]] = None
    ) -> Dict:
        """
        Invoke Gemini with streaming output (V7.7 Phase 15).

        Uses -o stream-json for JSONL streaming, parses each line,
        and calls on_token for text deltas.

        V9.7.1: HOME spoofing replaces CWD isolation (which caused ghost files).

        Args:
            context: Context markdown
            on_token: Callback for each text chunk
            session_uuid: Optional session UUID for NEXUS tracking
            isolated_env: V9.7.1 - Isolated environment for session isolation

        Returns:
            Dict structured NEXUS response

        Raises:
            RuntimeError: If the Gemini CLI fails to execute or returns an error code.
            TimeoutError: If the execution time exceeds the configured timeout.
        """
        import shutil
        import platform

        # V8.1.6: Generate unique ID for thread-safe file access
        unique_id = session_uuid or str(uuid_module.uuid4())[:8]

        # V9.7.1: CWD always at project root (no ghost files)
        effective_io_buffer = self.workspace_path / "_IO_BUFFER"
        effective_io_buffer.mkdir(parents=True, exist_ok=True)

        # V9.1.1: Enforce JSON format via prompt suffix
        enforced_context = self._enforce_json_format(context)

        # Write context to file with unique ID (in main workspace's IO buffer)
        context_file = effective_io_buffer / f"gemini_context_{unique_id}.md"
        context_file.write_text(enforced_context, encoding="utf-8")
        context_file_relative = Path("_IO_BUFFER") / f"gemini_context_{unique_id}.md"

        # Find CLI executable
        cli_executable = shutil.which(str(self.cli_path))
        if not cli_executable:
            cli_executable = str(self.cli_path)

        use_shell = platform.system() == "Windows"

        # Calculate nexus_root for --include-directories
        resolved_workspace = self.workspace_path.resolve()
        parent_dir = resolved_workspace.parent
        grandparent = parent_dir.parent
        if grandparent.name == "GENERATION_ACTIVE":
            nexus_root = grandparent.parent
        else:
            nexus_root = grandparent

        allowed_tools = "read_file,list_directory,grep,glob,read_many_files,google_web_search,web_fetch,write_file,edit_file"

        # V9.7.1: HOME spoofing replaces CWD isolation
        if isolated_env:
            # Isolated HOME - --resume latest is SAFE
            resume_flag = "--resume latest"
            _logger.debug(
                "V9.7.1 HOME spoofing (stream): --resume latest with isolated HOME"
            )
        else:
            # Shared HOME - start fresh to prevent context leakage
            resume_flag = ""
            if self._session_active:
                _logger.debug("invoke_stream: No isolated_env. Starting FRESH.")

        approval_mode = "--approval-mode yolo"

        # Build command with -o stream-json (CRITICAL: different from -o json)
        if use_shell:
            command = f'"{cli_executable}" -m {self.model} {approval_mode} --allowed-tools {allowed_tools} --include-directories "{nexus_root}" {resume_flag} -p @"{context_file_relative}" -o stream-json'
        else:
            cmd_parts = [cli_executable, "-m", self.model, "--approval-mode", "yolo", "--allowed-tools", allowed_tools, "--include-directories", str(nexus_root)]
            # V9.7.1: Add --resume latest only when using isolated HOME
            if isolated_env:
                cmd_parts.extend(["--resume", "latest"])
            cmd_parts.extend(["-p", f"@{context_file_relative}", "-o", "stream-json"])
            command = cmd_parts

        try:
            print(f"[DEBUG] Invoking Gemini (streaming): {self.model}", file=sys.stderr)

            # V9.7.1: CWD always at workspace root, env may be isolated
            proc = subprocess.Popen(
                command,
                cwd=str(self.workspace_path),  # V9.7.1: Always at project root (no ghost files)
                env=isolated_env,  # V9.7.1: Isolated HOME for session separation (None = inherit)
                shell=use_shell,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                errors='replace'
            )

            # V9.8 DETOX: Thread-safe process tracking
            with _active_processes_lock:
                _active_processes.append(proc)

            try:
                accumulated_text = []
                final_stats = {}
                start_time = time.time()

                # Read JSONL lines from stdout in real-time
                for line in iter(proc.stdout.readline, ''):
                    if not line:
                        break

                    # Check timeout
                    elapsed = time.time() - start_time
                    if elapsed > self.timeout:
                        proc.kill()
                        proc.wait()
                        raise TimeoutError(f"Gemini CLI timed out after {self.timeout}s")

                    # Parse stream chunk
                    text_chunk, data = parse_stream_chunk(line, "gemini")

                    if text_chunk is not None:
                        accumulated_text.append(text_chunk)
                        on_token(text_chunk)  # Stream to UI

                    if data and is_result_message(data, "gemini"):
                        final_stats = extract_stats(data, "gemini")

                # Wait for process to complete
                proc.wait(timeout=5)

                # Read any remaining stderr
                stderr = proc.stderr.read()

                if proc.returncode != 0:
                    error_msg = stderr or "Unknown error"
                    raise RuntimeError(f"Gemini CLI failed (code {proc.returncode}): {error_msg}")

                # Mark session active for future resume
                if self.use_session_resume:
                    self._session_active = True

                # Final newline after streaming
                on_token("\n")

                # Build NEXUS response from accumulated text
                full_response = "".join(accumulated_text)

                # Try to extract JSON from accumulated response
                extracted_data = self._extract_json(full_response, fallback_to_error=True)

                # Attach streaming stats if available
                if final_stats:
                    extracted_data["_stream_stats"] = final_stats

                # V8.8: Validate output for system prompt leaks
                return self._validate_output(extracted_data)

            except KeyboardInterrupt:
                print("\n[DEBUG] Interrupt received, killing Gemini process...", file=sys.stderr)
                proc.kill()
                proc.wait()
                raise
            finally:
                # V9.8 DETOX: Thread-safe process removal
                with _active_processes_lock:
                    if proc in _active_processes:
                        _active_processes.remove(proc)

        except TimeoutError:
            raise
        finally:
            # V8.1.6: Cleanup unique context file
            try:
                if context_file.exists():
                    context_file.unlink()
            except Exception:
                pass  # Best effort cleanup
