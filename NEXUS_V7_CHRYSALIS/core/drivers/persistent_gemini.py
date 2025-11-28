"""
Persistent Gemini Process - NEXUS V7

Manages a persistent Gemini CLI process using interactive mode (-i)
to eliminate ~7-10s subprocess startup latency per turn.

Security:
- --approval-mode yolo combined with --allowed-tools (read-only only)
- Gemini cannot write/execute, only read and search

Architecture:
- Single process started at driver init
- stdin/stdout communication for prompts
- Automatic restart on failure with fallback to subprocess mode
"""
import subprocess
import json
import time
import threading
import queue
import atexit
import sys
from pathlib import Path
from typing import Optional, List, Dict


class PersistentGeminiProcess:
    """
    Persistent Gemini CLI process for reduced latency.

    Uses -i (interactive) mode with restricted tools (read-only).
    Provides ~7-10s latency reduction after initial startup.
    """

    # Retry configuration
    MAX_RETRIES = 2
    BACKOFF_SECONDS = [1, 3]

    # Read-only tools (safe for yolo mode)
    DEFAULT_ALLOWED_TOOLS = [
        "read_file",
        "list_directory",
        "grep",
        "glob",
        "read_many_files",
        "google_web_search",
        "web_fetch"
    ]

    def __init__(
        self,
        cli_path: str,
        model: str,
        workspace_path: Path,
        include_directories: List[Path],
        allowed_tools: Optional[List[str]] = None,
        timeout: float = 300.0
    ):
        """
        Initialize persistent Gemini process manager.

        Args:
            cli_path: Path to gemini CLI executable
            model: Gemini model to use (e.g., gemini-3-pro-preview)
            workspace_path: Working directory for Gemini
            include_directories: Directories Gemini can read from
            allowed_tools: Tools to enable (default: read-only tools)
            timeout: Response timeout in seconds
        """
        self.cli_path = cli_path
        self.model = model
        self.workspace_path = workspace_path
        self.include_directories = include_directories
        self.allowed_tools = allowed_tools or self.DEFAULT_ALLOWED_TOOLS
        self.timeout = timeout

        # Process state
        self.process: Optional[subprocess.Popen] = None
        self._lock = threading.Lock()

        # Metrics
        self.start_time: Optional[float] = None
        self.invocation_count = 0
        self.restart_count = 0

        # Register cleanup at exit
        atexit.register(self.close)

    def start(self) -> bool:
        """
        Start the persistent Gemini process.

        Returns:
            True if process started successfully
        """
        with self._lock:
            if self.process and self.process.poll() is None:
                return True  # Already running

            try:
                # Build command with security flags
                import platform
                use_shell = platform.system() == "Windows"

                # Format include directories
                include_dirs_str = ",".join(str(d) for d in self.include_directories)
                allowed_tools_str = ",".join(self.allowed_tools)

                if use_shell:
                    # Windows: shell command string
                    cmd = (
                        f'"{self.cli_path}" '
                        f'-m {self.model} '
                        f'--approval-mode yolo '  # Auto-approve (safe with restricted tools)
                        f'--allowed-tools {allowed_tools_str} '  # Read-only only
                        f'--include-directories "{include_dirs_str}" '
                        f'-o stream-json '  # Stream JSON for response detection
                        f'-i'  # Interactive mode (persistent)
                    )
                else:
                    # Unix: list format
                    cmd = [
                        self.cli_path,
                        "-m", self.model,
                        "--approval-mode", "yolo",
                        "--allowed-tools", allowed_tools_str,
                        "--include-directories", include_dirs_str,
                        "-o", "stream-json",
                        "-i"
                    ]

                print(f"[DEBUG] Starting persistent Gemini: {self.model}", file=sys.stderr)

                self.process = subprocess.Popen(
                    cmd,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    encoding='utf-8',
                    errors='replace',
                    cwd=str(self.workspace_path),
                    shell=use_shell,
                    bufsize=1  # Line buffered
                )

                self.start_time = time.time()
                print(f"[DEBUG] Persistent Gemini started (PID: {self.process.pid})", file=sys.stderr)

                # Wait briefly for process to initialize
                time.sleep(0.5)

                return self.is_alive()

            except Exception as e:
                print(f"[ERROR] Failed to start persistent Gemini: {e}", file=sys.stderr)
                return False

    def is_alive(self) -> bool:
        """Check if the process is still running."""
        if not self.process:
            return False
        return self.process.poll() is None

    def send_prompt(self, prompt: str, timeout: Optional[float] = None) -> str:
        """
        Send a prompt and receive the complete response.

        Args:
            prompt: The prompt to send
            timeout: Optional timeout override

        Returns:
            The complete response text

        Raises:
            TimeoutError: If response takes too long
            RuntimeError: If process is not running
            BrokenPipeError: If process died during communication
        """
        if not self.is_alive():
            raise RuntimeError("Persistent Gemini process is not running")

        timeout = timeout or self.timeout
        response_parts = []

        with self._lock:
            try:
                # Send prompt (add newline to submit)
                self.process.stdin.write(prompt + "\n")
                self.process.stdin.flush()

                start_time = time.time()
                self.invocation_count += 1

                # Read stream-json events until message_stop
                while True:
                    if time.time() - start_time > timeout:
                        raise TimeoutError(f"Gemini response timeout after {timeout}s")

                    # Non-blocking read with timeout
                    line = self._read_line_with_timeout(timeout - (time.time() - start_time))

                    if not line:
                        if not self.is_alive():
                            raise BrokenPipeError("Gemini process died during response")
                        continue

                    # Parse stream-json events
                    try:
                        event = json.loads(line.strip())
                        event_type = event.get("type", "")

                        if event_type == "content_block_delta":
                            delta = event.get("delta", {})
                            text = delta.get("text", "")
                            if text:
                                response_parts.append(text)

                        elif event_type == "message_stop":
                            # Response complete
                            break

                        elif event_type == "error":
                            error_msg = event.get("error", {}).get("message", "Unknown error")
                            raise RuntimeError(f"Gemini error: {error_msg}")

                    except json.JSONDecodeError:
                        # Non-JSON line (logs, prompts, etc.) - skip
                        continue

                return "".join(response_parts)

            except (BrokenPipeError, OSError) as e:
                # Process communication failed
                raise BrokenPipeError(f"Lost connection to Gemini process: {e}")

    def _read_line_with_timeout(self, timeout: float) -> Optional[str]:
        """
        Read a line from stdout with timeout.

        Uses a separate thread to avoid blocking indefinitely.
        """
        result_queue = queue.Queue()

        def reader():
            try:
                line = self.process.stdout.readline()
                result_queue.put(line)
            except Exception as e:
                result_queue.put(None)

        thread = threading.Thread(target=reader, daemon=True)
        thread.start()
        thread.join(timeout=min(timeout, 1.0))  # Check every second

        try:
            return result_queue.get_nowait()
        except queue.Empty:
            return None

    def send_prompt_safe(self, prompt: str) -> str:
        """
        Send prompt with automatic retry on failure.

        Args:
            prompt: The prompt to send

        Returns:
            The response text

        Raises:
            RuntimeError: If all retries failed
        """
        last_error = None

        for attempt in range(self.MAX_RETRIES + 1):
            try:
                if not self.is_alive():
                    self.restart()

                return self.send_prompt(prompt)

            except (TimeoutError, BrokenPipeError, RuntimeError) as e:
                last_error = e
                print(f"[WARNING] Persistent Gemini failed (attempt {attempt + 1}): {e}", file=sys.stderr)

                if attempt < self.MAX_RETRIES:
                    backoff = self.BACKOFF_SECONDS[min(attempt, len(self.BACKOFF_SECONDS) - 1)]
                    time.sleep(backoff)
                    self.restart()

        raise RuntimeError(f"Persistent Gemini failed after {self.MAX_RETRIES + 1} attempts: {last_error}")

    def restart(self) -> bool:
        """
        Restart the persistent process.

        Returns:
            True if restart successful
        """
        print("[DEBUG] Restarting persistent Gemini process...", file=sys.stderr)
        self.close()
        self.restart_count += 1
        return self.start()

    def close(self):
        """Gracefully shutdown the persistent process."""
        with self._lock:
            if self.process:
                try:
                    if self.process.poll() is None:
                        # Send exit command
                        try:
                            self.process.stdin.write("/exit\n")
                            self.process.stdin.flush()
                            self.process.wait(timeout=2)
                        except Exception:
                            pass

                        # Force kill if still running
                        if self.process.poll() is None:
                            self.process.terminate()
                            self.process.wait(timeout=2)

                        if self.process.poll() is None:
                            self.process.kill()

                except Exception as e:
                    print(f"[WARNING] Error closing Gemini process: {e}", file=sys.stderr)
                finally:
                    self.process = None
                    print("[DEBUG] Persistent Gemini process closed", file=sys.stderr)

    def get_stats(self) -> Dict:
        """Get process statistics."""
        uptime = time.time() - self.start_time if self.start_time else 0
        return {
            "alive": self.is_alive(),
            "pid": self.process.pid if self.process else None,
            "model": self.model,
            "uptime_seconds": round(uptime, 1),
            "invocations": self.invocation_count,
            "restarts": self.restart_count
        }
