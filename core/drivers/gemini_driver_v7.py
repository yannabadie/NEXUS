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

V7 Sprint 13: PTY Mode (DEPRECATED)
- PTY mode disabled by default - Gemini TUI doesn't accept PTY stdin input
- The --prompt-interactive flag only works for initial prompt
- For multi-turn: use subprocess mode with --resume latest
"""
import subprocess
import json
import sys
import time
import atexit
from pathlib import Path
from typing import Dict, Optional


# Global reference for cleanup at exit
_active_processes = []
_persistent_process = None  # Singleton persistent process

# PTY mode removed in V7 cleanup (was never used, gemini_pty_mode=False by default)
# Session persistence now uses --resume latest instead
PTY_AVAILABLE = False
PersistentGeminiPTY = None


def _cleanup_processes():
    """Kill any remaining Gemini processes at exit."""
    global _persistent_process

    # Cleanup persistent process first
    if _persistent_process:
        try:
            _persistent_process.close()
        except Exception:
            pass
        _persistent_process = None

    # Cleanup any one-shot processes
    for proc in _active_processes:
        try:
            if proc.poll() is None:  # Still running
                proc.terminate()
                proc.wait(timeout=2)
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass
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
        config,
        workspace_path: Path,
        model: Optional[str] = None,
        agent_id: Optional[str] = None,
        persistent: Optional[bool] = None,
        pty_mode: Optional[bool] = None
    ):
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

        # V7 Sprint 13: PTY PERSISTENT mode
        # Uses winpty to maintain a persistent Gemini session (~2s latency vs ~15s subprocess)
        # The PTY is kept alive between invocations for maximum performance
        self.pty_mode = pty_mode if pty_mode is not None else getattr(config, 'gemini_pty_mode', False)
        self.pty_available = PTY_AVAILABLE
        self._pty_instance: Optional[Any] = None  # Persistent PTY instance

    def _init_persistent(self):
        """Legacy method - persistent mode removed in V7 cleanup.

        Session persistence now uses --resume latest instead of persistent process.
        This method is kept for API compatibility but does nothing.
        """
        # Persistent process mode was removed - use session resume instead
        self._persistent_process = None

    def invoke(self, context: str, use_pty: Optional[bool] = None) -> Dict:
        """
        Invoke Gemini CLI avec contexte markdown.

        V7 Sprint 12: Uses persistent mode if available, with automatic fallback.
        V7 Sprint 13: PTY single-shot mode for one-off operations.

        Args:
            context: Contexte markdown avec system prompt
            use_pty: Override PTY mode for this invocation (None = use default)

        Returns:
            Dict structuré NEXUS (JSON parsé)

        Raises:
            RuntimeError: Si Gemini CLI échoue
            TimeoutError: Si timeout dépassé
        """
        # Determine if we should try PTY mode
        try_pty = use_pty if use_pty is not None else self.pty_mode

        # V7 Sprint 13: Try PTY PERSISTENT mode if enabled and available
        if try_pty and self.pty_available:
            try:
                return self._invoke_pty_persistent(context)
            except Exception as e:
                print(f"[WARNING] PTY mode failed: {e}, falling back to subprocess", file=sys.stderr)
                # Kill failed PTY and fall through to subprocess
                self._close_pty()

        # V7 Sprint 12: Try persistent mode if available (legacy)
        if self.persistent and self._persistent_process and self._persistent_process.is_alive():
            try:
                return self._invoke_persistent(context)
            except Exception as e:
                print(f"[WARNING] Persistent mode failed: {e}, falling back to subprocess", file=sys.stderr)
                # Fall through to subprocess mode

        return self._invoke_subprocess(context)

    def _ensure_pty_started(self) -> bool:
        """
        Ensure the persistent PTY is started and alive.

        Returns:
            True if PTY is ready for use
        """
        # Check if PTY is already running
        if self._pty_instance and self._pty_instance.is_alive():
            return True

        # Calculate nexus_root for include_directories
        resolved_workspace = self.workspace_path.resolve()
        parent_dir = resolved_workspace.parent
        grandparent = parent_dir.parent
        if grandparent.name == "GENERATION_ACTIVE":
            nexus_root = grandparent.parent
        else:
            nexus_root = grandparent

        # Create new PTY instance
        print(f"[DEBUG] Starting persistent PTY for Gemini: {self.model}", file=sys.stderr)
        self._pty_instance = PersistentGeminiPTY(
            config=self.config,
            workspace_path=self.workspace_path,
            model=self.model,
            include_directories=[nexus_root]
        )

        # Start with a simple prompt that generates a direct response (not tool use)
        initial = "Say OK"
        if not self._pty_instance.start(initial_prompt=initial):
            print(f"[ERROR] Failed to start PTY process", file=sys.stderr)
            self._pty_instance = None
            return False

        print(f"[DEBUG] Persistent PTY started (PID: {self._pty_instance.process.pid})", file=sys.stderr)
        return True

    def _close_pty(self):
        """Close the persistent PTY if running."""
        if self._pty_instance:
            try:
                self._pty_instance.close()
            except Exception:
                pass
            self._pty_instance = None

    def _invoke_pty_persistent(self, context: str) -> Dict:
        """
        Invoke Gemini using persistent PTY mode.

        Maintains a single PTY session across multiple invocations.
        ~2s latency vs ~15-20s for subprocess mode.

        Args:
            context: Context markdown

        Returns:
            Dict structured NEXUS response
        """
        # Ensure PTY is started
        if not self._ensure_pty_started():
            raise RuntimeError("Failed to start persistent PTY")

        start_time = time.time()
        print(f"[DEBUG] Invoking Gemini (PTY persistent): {self.model}", file=sys.stderr)

        try:
            # Send prompt via PTY and wait for response
            raw_response = self._pty_instance.send_prompt(context, timeout=self.timeout)

            elapsed = time.time() - start_time
            print(f"[DEBUG] PTY response received in {elapsed:.1f}s", file=sys.stderr)

            # Extract JSON from response
            return self._extract_json(raw_response)

        except Exception as e:
            # PTY might have died, close it for next retry
            print(f"[WARNING] PTY invocation failed: {e}", file=sys.stderr)
            self._close_pty()
            raise

    def _invoke_persistent(self, context: str) -> Dict:
        """
        Invoke Gemini using persistent process (legacy).

        Args:
            context: Context markdown

        Returns:
            Dict structured NEXUS response
        """
        print(f"[DEBUG] Invoking Gemini (persistent): {self.model}", file=sys.stderr)

        # Send prompt and get response (with retry)
        raw_response = self._persistent_process.send_prompt_safe(context)

        # Extract JSON from response
        return self._extract_json(raw_response)

    def _invoke_subprocess(self, context: str) -> Dict:
        """
        Invoke Gemini using subprocess (original method).

        Args:
            context: Context markdown

        Returns:
            Dict structured NEXUS response
        """
        import sys
        import shutil

        # Write context to file
        context_file = self.io_buffer / "gemini_context_in.md"
        context_file.write_text(context, encoding="utf-8")

        # FIX: Use path relative to cwd (workspace) to avoid double-path issue
        # The subprocess runs with cwd=workspace_path, so the path should be relative to that
        context_file_relative = Path("_IO_BUFFER") / "gemini_context_in.md"

        output_file = self.io_buffer / "gemini_output.json"

        # Clear previous output file
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

        # V7 Sprint 12: Session resume for context persistence + YOLO mode for auto-approval
        # --resume latest: Restores previous session context (~14k cached tokens)
        # --approval-mode yolo: Auto-approve with --allowed-tools restriction (read-only safe)
        resume_flag = "--resume latest" if self.use_session_resume and self._session_active else ""
        approval_mode = "--approval-mode yolo"  # Safe: write ops sandboxed to workspace

        if use_shell:
            # Shell command string for Windows
            # --allowed-tools: Only auto-approve read tools (write/shell require confirmation)
            # --include-directories: Give Gemini READ access to parent NEXUS code
            # FIX: Use context_file_relative to avoid double-path issue (cwd is already workspace)
            command = f'"{cli_executable}" -m {self.model} {approval_mode} --allowed-tools {allowed_tools} --include-directories "{nexus_root}" {resume_flag} -p @"{context_file_relative}" -o json'
        else:
            # List format for Unix
            cmd_parts = [cli_executable, "-m", self.model, "--approval-mode", "yolo", "--allowed-tools", allowed_tools, "--include-directories", str(nexus_root)]
            if self.use_session_resume and self._session_active:
                cmd_parts.extend(["--resume", "latest"])
            # FIX: Use context_file_relative to avoid double-path issue
            cmd_parts.extend(["-p", f"@{context_file_relative}", "-o", "json"])
            command = cmd_parts

        try:
            print(f"[DEBUG] Invoking Gemini: {self.model} (timeout: {self.timeout}s)", file=sys.stderr)
            if use_shell:
                print(f"[DEBUG] Command: {command}", file=sys.stderr)

            # Use Popen with polling loop to allow CTRL+C interruption
            proc = subprocess.Popen(
                command,
                cwd=str(self.workspace_path),
                shell=use_shell,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                errors='replace'
            )

            # Track for cleanup at exit
            _active_processes.append(proc)

            try:
                import threading
                import queue

                start_time = time.time()
                stdout_data = []
                stderr_data = []
                output_queue = queue.Queue()

                def read_stream(stream, stream_name, data_list):
                    """Read stream in thread and queue lines for display."""
                    try:
                        for line in iter(stream.readline, ''):
                            if line:
                                data_list.append(line)
                                output_queue.put((stream_name, line.strip()))
                    except Exception:
                        pass

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
                # Remove from tracking once done
                if proc in _active_processes:
                    _active_processes.remove(proc)

            # Create result-like object for compatibility
            class Result:
                pass
            result = Result()
            result.returncode = proc.returncode
            result.stdout = stdout
            result.stderr = stderr

            print(f"[DEBUG] Gemini returned: code={result.returncode}, stdout_len={len(result.stdout)}", file=sys.stderr)

            if result.returncode != 0:
                error_msg = result.stderr or result.stdout or "Unknown error"
                print(f"[DEBUG] Gemini error: {error_msg[:500]}", file=sys.stderr)
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
                return {
                    "sender": "Gemini",
                    "action_type": "TALK",
                    "content": json.dumps(extracted_data), # Pass the list as a string content
                    "status": "FINISHED"
                }

            return extracted_data

        except TimeoutError:
            # Re-raise timeout from the inner try block
            raise

    def _extract_json(self, text: str, fallback_to_error: bool = True) -> Dict:
        """
        Extract JSON from text (robust fallback)

        Args:
            text: Raw text that might contain JSON
            fallback_to_error: If True, return error dict instead of raising

        Returns:
            Dict (extracted JSON or error fallback)

        Raises:
            ValueError: If no JSON found and fallback_to_error is False
        """
        import re

        # 1. Try to find JSON in markdown code blocks first (most reliable)
        json_block_pattern = r'```json\s*(.*?)\s*```'
        matches = re.findall(json_block_pattern, text, re.DOTALL)

        if matches:
            # Try the last block first (often the final answer)
            for match in reversed(matches):
                try:
                    return json.loads(match)
                except json.JSONDecodeError:
                    continue

        # 2. Try to find a raw JSON object structure
        # Look for { at start of line or after newline, followed by "sender" key
        # This helps filter out example JSONs in the prompt

        # Robust pattern to find the outermost JSON object
        # We look for the largest block starting with { and ending with }
        try:
            # Find start of potential JSON (heuristic: looks for {"sender":)
            start_indices = [m.start() for m in re.finditer(r'\{\s*"sender"', text)]

            for start in reversed(start_indices): # Try last occurrence first
                # Simple bracket counting to find the end
                brackets = 0
                for i, char in enumerate(text[start:], start):
                    if char == '{':
                        brackets += 1
                    elif char == '}':
                        brackets -= 1
                        if brackets == 0:
                            candidate = text[start:i+1]
                            try:
                                return json.loads(candidate)
                            except json.JSONDecodeError:
                                break # Try next start index
        except Exception:
            pass

        # 3. Last resort: regex for generic JSON object
        json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
        matches = re.findall(json_pattern, text, re.DOTALL)

        if matches:
            for match in reversed(matches):
                try:
                    data = json.loads(match)
                    if "sender" in data: # Validation check
                        return data
                except json.JSONDecodeError:
                    continue

        # No JSON found - provide fallback or raise
        if fallback_to_error:
            # Return a structured error response that won't crash the system
            # Extract any useful content from the raw text
            content_preview = text[:1000] if text else "[Empty response]"
            return {
                "sender": "Gemini",
                "action_type": "TALK",
                "content": f"[JSON extraction failed - raw response]\n{content_preview}",
                "status": "CONTINUE",
                "next_agent": "Claude",
                "_json_extraction_failed": True,
                "_raw_response_preview": text[:500] if text else ""
            }
        else:
            raise ValueError(f"Could not extract JSON from Gemini response: {text[:500]}...")
