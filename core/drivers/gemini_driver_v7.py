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

V7.5 Phase 7: Session Isolation via session_uuid
- SwarmSessionManager generates unique session UUIDs per task+role
- When session_uuid is provided, uses --resume {uuid} for isolation
- Enables parallel task execution without context bleeding

Note: PTY mode was removed in V7.6 cleanup (never worked, gemini_pty_mode=False).
      Archived to: docs/archive/pty_mode_v7_archived.py
"""
import subprocess
import json
import sys
import time
import atexit
import uuid as uuid_module
from pathlib import Path
from typing import Dict, Optional, Callable

# V7.5 HIVE MIND: Centralized JSON extraction
from core.utils.json_extractor import extract_json_safe as robust_extract_json
# V7.7 Phase 15: Stream parser for real-time response display
from core.utils.stream_parser import parse_stream_chunk, is_result_message, extract_stats
# V8.4.0: Unified agent registry
from core.agents.unified_registry import get_registry


# Global reference for cleanup at exit
_active_processes = []
_persistent_process = None  # Singleton persistent process

# PTY mode removed in V7.6 cleanup - see docs/archive/pty_mode_v7_archived.py


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
        persistent: Optional[bool] = None
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

    def _init_persistent(self):
        """Legacy method - persistent mode removed in V7 cleanup.

        Session persistence now uses --resume latest instead of persistent process.
        This method is kept for API compatibility but does nothing.
        """
        # Persistent process mode was removed - use session resume instead
        self._persistent_process = None

    def invoke(
        self,
        context: str,
        session_uuid: Optional[str] = None
    ) -> Dict:
        """
        Invoke Gemini CLI avec contexte markdown.

        V7 Sprint 12: Uses session resume for context persistence.
        V7.5 Phase 7: Session isolation via session_uuid parameter.

        Args:
            context: Contexte markdown avec system prompt
            session_uuid: Optional session UUID for isolation (Phase 7).
                         When provided, uses --resume {uuid} instead of --resume latest.
                         This enables parallel task execution without context bleeding.

        Returns:
            Dict structuré NEXUS (JSON parsé)

        Raises:
            RuntimeError: Si Gemini CLI échoue
            TimeoutError: Si timeout dépassé
            ValueError: Si session_uuid invalide (resume failed)
        """
        return self._invoke_subprocess(context, session_uuid=session_uuid)

    def invoke_stream(
        self,
        context: str,
        on_token: Callable[[str], None],
        session_uuid: Optional[str] = None
    ) -> Dict:
        """
        Invoke Gemini CLI with streaming output (V7.7 Phase 15).

        Streams text tokens in real-time via callback, then returns
        the full parsed JSON response.

        Args:
            context: Contexte markdown avec system prompt
            on_token: Callback called with each text chunk
            session_uuid: Optional session UUID for isolation (Phase 7)

        Returns:
            Dict structuré NEXUS (JSON parsé)

        Raises:
            RuntimeError: Si Gemini CLI échoue
            TimeoutError: Si timeout dépassé
        """
        return self._invoke_subprocess_stream(context, on_token, session_uuid=session_uuid)

    # NOTE: PTY and legacy persistent methods removed in V7.6 cleanup
    # See: docs/archive/pty_mode_v7_archived.py

    def _invoke_subprocess(
        self,
        context: str,
        session_uuid: Optional[str] = None
    ) -> Dict:
        """
        Invoke Gemini using subprocess (original method).

        V7.5 Phase 7: Session isolation support via session_uuid.

        Args:
            context: Context markdown
            session_uuid: Optional session UUID for isolation.
                         When provided, uses --resume {uuid} for session isolation.

        Returns:
            Dict structured NEXUS response
        """
        import sys
        import shutil

        # V8.1.6: Generate unique ID for thread-safe file access
        unique_id = session_uuid or str(uuid_module.uuid4())[:8]

        # Write context to file with unique ID
        context_file = self.io_buffer / f"gemini_context_{unique_id}.md"
        context_file.write_text(context, encoding="utf-8")

        # FIX: Use path relative to cwd (workspace) to avoid double-path issue
        # The subprocess runs with cwd=workspace_path, so the path should be relative to that
        context_file_relative = Path("_IO_BUFFER") / f"gemini_context_{unique_id}.md"

        output_file = self.io_buffer / f"gemini_output_{unique_id}.json"

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

        # V7.5 Phase 7: Session isolation via explicit session_uuid
        # V7 Sprint 12: Session resume for context persistence + YOLO mode for auto-approval
        # --resume {uuid}: Isolates this task from other parallel tasks
        # --resume latest: Restores previous session context (~14k cached tokens)
        # --approval-mode yolo: Auto-approve with --allowed-tools restriction (read-only safe)
        if session_uuid:
            # Phase 7: Explicit session UUID for isolation (Swarm parallel tasks)
            resume_flag = f"--resume {session_uuid}"
            print(f"[DEBUG] Using session isolation: {session_uuid[:8]}...", file=sys.stderr)
        elif self.use_session_resume and self._session_active:
            # Default: Resume latest session for single-agent mode
            resume_flag = "--resume latest"
        else:
            # New session (first invocation or session resume disabled)
            resume_flag = ""
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
            # V7.5 Phase 7: Session isolation support
            if session_uuid:
                cmd_parts.extend(["--resume", session_uuid])
            elif self.use_session_resume and self._session_active:
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
                # V8.4.0: Use registry for display name
                registry = get_registry()
                return {
                    "sender": registry.get_display_name("gemini"),
                    "action_type": "TALK",
                    "content": json.dumps(extracted_data), # Pass the list as a string content
                    "status": "FINISHED"
                }

            return extracted_data

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
        session_uuid: Optional[str] = None
    ) -> Dict:
        """
        Invoke Gemini with streaming output (V7.7 Phase 15).

        Uses -o stream-json for JSONL streaming, parses each line,
        and calls on_token for text deltas.

        Args:
            context: Context markdown
            on_token: Callback for each text chunk
            session_uuid: Optional session UUID for isolation

        Returns:
            Dict structured NEXUS response
        """
        import shutil
        import platform

        # V8.1.6: Generate unique ID for thread-safe file access
        unique_id = session_uuid or str(uuid_module.uuid4())[:8]

        # Write context to file with unique ID
        context_file = self.io_buffer / f"gemini_context_{unique_id}.md"
        context_file.write_text(context, encoding="utf-8")
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

        # Build resume flag
        if session_uuid:
            resume_flag = f"--resume {session_uuid}"
        elif self.use_session_resume and self._session_active:
            resume_flag = "--resume latest"
        else:
            resume_flag = ""

        approval_mode = "--approval-mode yolo"

        # Build command with -o stream-json (CRITICAL: different from -o json)
        if use_shell:
            command = f'"{cli_executable}" -m {self.model} {approval_mode} --allowed-tools {allowed_tools} --include-directories "{nexus_root}" {resume_flag} -p @"{context_file_relative}" -o stream-json'
        else:
            cmd_parts = [cli_executable, "-m", self.model, "--approval-mode", "yolo", "--allowed-tools", allowed_tools, "--include-directories", str(nexus_root)]
            if session_uuid:
                cmd_parts.extend(["--resume", session_uuid])
            elif self.use_session_resume and self._session_active:
                cmd_parts.extend(["--resume", "latest"])
            cmd_parts.extend(["-p", f"@{context_file_relative}", "-o", "stream-json"])
            command = cmd_parts

        try:
            print(f"[DEBUG] Invoking Gemini (streaming): {self.model}", file=sys.stderr)

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

                return extracted_data

            except KeyboardInterrupt:
                print("\n[DEBUG] Interrupt received, killing Gemini process...", file=sys.stderr)
                proc.kill()
                proc.wait()
                raise
            finally:
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
