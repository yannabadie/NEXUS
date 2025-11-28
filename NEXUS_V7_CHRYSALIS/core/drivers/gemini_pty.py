"""
Gemini Persistent PTY Driver - NEXUS V7

EXPERIMENTAL: PTY-based driver for Gemini CLI interaction.

## What Works
- Initial prompt processing via --prompt-interactive flag
- Startup time reduced to ~25-30s (includes first prompt response)
- Screen reader mode provides cleaner output parsing

## Known Limitations
- Follow-up prompts via PTY write do NOT submit properly to TUI
  - Text is received and displayed in input field
  - Text appears as "Queued (press up to edit)"
  - But Enter/newline doesn't trigger submission
- Gemini's TUI uses special input handling that PTY stdin doesn't fully emulate

## Recommended Usage
1. Use PTY for INITIAL prompt only (via --prompt-interactive)
2. For multi-turn conversations, use subprocess mode with --resume

## Architecture
- Uses winpty.PtyProcess for Windows TTY emulation
- Screen reader mode (--screen-reader) for cleaner output
- ANSI escape codes stripped via ANSIParser
- Response detection via "Model:" and "Type your message" markers

## Security
- --approval-mode yolo with --allowed-tools whitelist
- Write operations restricted to workspace

## Future Work
- Investigate conpty or native Windows PTY for better TUI input
- Consider Gemini API integration as alternative to CLI
"""

import re
import sys
import time
import json
import threading
import atexit
from pathlib import Path
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, field

# Conditional import for Windows PTY
try:
    import winpty
    WINPTY_AVAILABLE = True
except ImportError:
    WINPTY_AVAILABLE = False
    winpty = None


@dataclass
class PTYMetrics:
    """Metrics for monitoring PTY performance."""
    start_time: float = 0.0
    invocation_count: int = 0
    total_response_time: float = 0.0
    restart_count: int = 0
    last_response_time: float = 0.0
    errors: List[str] = field(default_factory=list)

    @property
    def avg_response_time(self) -> float:
        if self.invocation_count == 0:
            return 0.0
        return self.total_response_time / self.invocation_count

    @property
    def uptime(self) -> float:
        if self.start_time == 0:
            return 0.0
        return time.time() - self.start_time


class ANSIParser:
    """Parser for stripping ANSI escape codes from terminal output."""

    # Comprehensive ANSI escape patterns
    PATTERNS = [
        r'\x1b\[[0-9;]*[a-zA-Z]',           # CSI sequences (colors, cursor, etc.)
        r'\x1b\][^\x07\x1b]*(?:\x07|\x1b\\)', # OSC sequences (title, etc.)
        r'\x1b[PX^_][^\x1b]*\x1b\\',         # DCS/PM/APC/SOS sequences
        r'\x1b\([A-Z0-9]',                   # Character set selection
        r'\x1b[78DEHM]',                     # Single-char sequences
        r'\x1b=|\x1b>',                      # Keypad mode
        r'\x1b\[[\?]?[0-9;]*[hlsr]',         # Mode set/reset
        r'\r',                               # Carriage return
    ]

    _compiled_pattern = None

    @classmethod
    def get_pattern(cls) -> re.Pattern:
        """Get compiled regex pattern (cached)."""
        if cls._compiled_pattern is None:
            cls._compiled_pattern = re.compile('|'.join(cls.PATTERNS))
        return cls._compiled_pattern

    @classmethod
    def strip(cls, text: str) -> str:
        """Remove all ANSI escape sequences from text."""
        return cls.get_pattern().sub('', text)

    @classmethod
    def extract_visible_text(cls, text: str) -> str:
        """Extract only visible text, removing control chars."""
        stripped = cls.strip(text)
        # Remove other control characters except newline/tab
        return ''.join(c for c in stripped if c >= ' ' or c in '\n\t')


class ResponseDetector:
    """
    Detects when Gemini has finished responding.

    Strategies (in order of reliability):
    1. Screen reader mode: Look for "Model:" followed by "Type your message"
    2. Prompt marker detection (❯ or similar)
    3. JSON structure completion (for -o json mode)
    4. Idle timeout (no new data for N seconds)
    """

    # Possible prompt markers (Gemini CLI uses various Unicode chars)
    PROMPT_MARKERS = [
        '❯',                    # Main prompt
        '>',                    # Fallback
        '>>> ',                 # Alternative
        'Type your message',    # Input prompt text
    ]

    # Regex for detecting prompt line
    PROMPT_REGEX = re.compile(r'[\r\n].*[❯>]\s*$')

    # Regex for screen reader mode completion
    # After "Model: <response>" we should see "Type your message" again
    SCREEN_READER_COMPLETE = re.compile(
        r'Model:\s+.+?Type your message',
        re.DOTALL | re.IGNORECASE
    )

    # Regex for JSON completion
    JSON_END_REGEX = re.compile(r'\}\s*$')

    def __init__(self, idle_timeout: float = 2.0):
        self.idle_timeout = idle_timeout
        self.last_data_time = time.time()
        self.buffer = ""
        self._saw_model_response = False

    def reset(self):
        """Reset detector state for new response."""
        self.buffer = ""
        self.last_data_time = time.time()
        self._saw_model_response = False

    def add_data(self, data: str):
        """Add new data to buffer."""
        self.buffer += data
        self.last_data_time = time.time()
        # Track if we've seen a model response
        if 'Model:' in data:
            self._saw_model_response = True

    def is_complete(self, json_mode: bool = False) -> bool:
        """
        Check if response appears complete.

        Args:
            json_mode: If True, also check for JSON completion

        Returns:
            True if response seems complete
        """
        clean = ANSIParser.extract_visible_text(self.buffer)

        # Strategy 1: Screen reader mode - Model response followed by input prompt
        if self._saw_model_response and 'Type your message' in clean:
            # Verify we have actual content after "Model:"
            if self.SCREEN_READER_COMPLETE.search(clean):
                return True

        # Strategy 2: Prompt marker at end (non-screen-reader mode)
        if self.PROMPT_REGEX.search(clean):
            return True

        # Strategy 3: JSON completion (if in JSON mode)
        if json_mode:
            # Look for complete JSON object
            if self._has_complete_json(clean):
                return True

        return False

    def is_idle(self) -> bool:
        """Check if idle timeout has passed."""
        return (time.time() - self.last_data_time) > self.idle_timeout

    def _has_complete_json(self, text: str) -> bool:
        """Check if text contains a complete JSON object."""
        # Find potential JSON start
        start = text.find('{')
        if start == -1:
            return False

        # Try to find matching end
        depth = 0
        in_string = False
        escape_next = False

        for i, char in enumerate(text[start:], start):
            if escape_next:
                escape_next = False
                continue

            if char == '\\' and in_string:
                escape_next = True
                continue

            if char == '"' and not escape_next:
                in_string = not in_string
                continue

            if in_string:
                continue

            if char == '{':
                depth += 1
            elif char == '}':
                depth -= 1
                if depth == 0:
                    return True

        return False


class PersistentGeminiPTY:
    """
    Persistent Gemini CLI process via Windows PTY.

    Provides low-latency interaction with Gemini CLI by maintaining
    a single running process and sending prompts via PTY.

    Usage:
        pty = PersistentGeminiPTY(config, workspace, model)
        if pty.start():
            response = pty.send_prompt("Your question here")
            print(response)
        pty.close()
    """

    # Configuration defaults
    DEFAULT_STARTUP_TIMEOUT = 30.0
    DEFAULT_RESPONSE_TIMEOUT = 300.0
    DEFAULT_IDLE_TIMEOUT = 3.0
    DEFAULT_MAX_RESTARTS = 3
    DEFAULT_READ_CHUNK_SIZE = 4096

    # Allowed tools (safe for yolo mode)
    ALLOWED_TOOLS = [
        "read_file",
        "list_directory",
        "grep",
        "glob",
        "read_many_files",
        "google_web_search",
        "web_fetch",
        "write_file",
        "edit_file",
    ]

    def __init__(
        self,
        config,
        workspace_path: Path,
        model: str = "gemini-3-pro-preview",
        include_directories: Optional[List[Path]] = None
    ):
        """
        Initialize the persistent PTY manager.

        Args:
            config: NEXUS configuration object
            workspace_path: Working directory for Gemini
            model: Gemini model to use
            include_directories: Additional directories Gemini can read
        """
        self.config = config
        self.workspace_path = Path(workspace_path)
        self.model = model
        self.include_directories = include_directories or []

        # Get CLI path from config
        self.cli_path = getattr(config, 'gemini_cli_path',
                                r'C:\Users\yann.abadie\AppData\Roaming\npm\gemini.CMD')

        # Timeouts from config
        self.startup_timeout = getattr(config, 'gemini_pty_startup_timeout',
                                       self.DEFAULT_STARTUP_TIMEOUT)
        self.response_timeout = getattr(config, 'gemini_pty_timeout',
                                        self.DEFAULT_RESPONSE_TIMEOUT)
        self.idle_timeout = getattr(config, 'gemini_pty_idle_timeout',
                                    self.DEFAULT_IDLE_TIMEOUT)
        self.max_restarts = getattr(config, 'gemini_pty_max_restarts',
                                    self.DEFAULT_MAX_RESTARTS)

        # JSON output mode
        self.json_mode = getattr(config, 'gemini_stream_json', True)

        # Process state
        self.process: Optional[Any] = None  # winpty.PtyProcess
        self._lock = threading.Lock()
        self._started = False
        self._restart_count = 0

        # Metrics
        self.metrics = PTYMetrics()

        # Response detector
        self.detector = ResponseDetector(idle_timeout=self.idle_timeout)

        # V7 Sprint 13: Capture initial response for single-shot mode
        self._initial_response: Optional[str] = None
        self._startup_raw_output: str = ""

        # Register cleanup
        atexit.register(self.close)

    @property
    def is_available(self) -> bool:
        """Check if PTY mode is available on this system."""
        return WINPTY_AVAILABLE

    def is_alive(self) -> bool:
        """Check if the PTY process is running."""
        if not self.process:
            return False
        return self.process.isalive()

    def _build_command(self, initial_prompt: str = "") -> str:
        """
        Build the Gemini CLI command string.

        Args:
            initial_prompt: Initial prompt for --prompt-interactive

        Returns:
            Complete command string (wrapped with cmd.exe for .CMD files)
        """
        # Build gemini command parts
        # Note: No quotes around cli_path - cmd.exe handles paths with spaces
        gemini_parts = [self.cli_path]

        # Model
        gemini_parts.append(f'-m {self.model}')

        # CRITICAL: Screen reader mode disables rich TUI, allows PTY input
        gemini_parts.append('--screen-reader')

        # Approval mode (safe with restricted tools)
        gemini_parts.append('--approval-mode yolo')

        # Allowed tools
        tools_str = ','.join(self.ALLOWED_TOOLS)
        gemini_parts.append(f'--allowed-tools {tools_str}')

        # Include directories for reading parent code
        if self.include_directories:
            dirs_str = ','.join(f'"{d}"' for d in self.include_directories)
            gemini_parts.append(f'--include-directories {dirs_str}')

        # Output format - NOTE: json mode may interfere with screen reader
        # Only enable if specifically needed
        if self.json_mode:
            gemini_parts.append('-o json')

        # Interactive mode with initial prompt
        if initial_prompt:
            # Escape quotes in prompt (double escape for cmd.exe)
            escaped = initial_prompt.replace('"', '""')
            gemini_parts.append(f'--prompt-interactive "{escaped}"')

        gemini_cmd = ' '.join(gemini_parts)

        # Wrap with cmd.exe for .CMD files on Windows (required for winpty)
        return f'cmd.exe /c {gemini_cmd}'

    def start(self, initial_prompt: str = "You are NEXUS Gemini agent. Respond in JSON.") -> bool:
        """
        Start the persistent PTY process.

        Args:
            initial_prompt: Initial system prompt for the session

        Returns:
            True if started successfully
        """
        if not WINPTY_AVAILABLE:
            self._log("ERROR", "winpty not available - PTY mode disabled")
            return False

        with self._lock:
            if self.process and self.process.isalive():
                return True  # Already running

            try:
                # Build command
                cmd = self._build_command(initial_prompt)
                self._log("DEBUG", f"Starting PTY: {cmd[:100]}...")

                # Spawn PTY process
                self.process = winpty.PtyProcess.spawn(
                    cmd,
                    cwd=str(self.workspace_path)
                )

                self._log("DEBUG", f"PTY spawned, PID: {self.process.pid}")

                # Wait for startup (detect first prompt)
                if not self._wait_for_startup():
                    self._log("ERROR", "PTY startup timeout - process may have failed")
                    self.close()
                    return False

                self._started = True
                self.metrics.start_time = time.time()
                self._log("INFO", f"PTY started successfully (PID: {self.process.pid})")
                return True

            except Exception as e:
                self._log("ERROR", f"Failed to start PTY: {e}")
                self.metrics.errors.append(f"Start failed: {e}")
                return False

    def _wait_for_startup(self) -> bool:
        """
        Wait for Gemini to finish starting up and process initial prompt.

        In screen reader mode with --prompt-interactive, we need to wait for:
        1. Gemini to start
        2. Initial prompt to be processed (look for "Model:" response)
        3. Next input prompt to appear (ready for follow-up)

        V7 Sprint 13: Also captures the initial response for single-shot mode.

        Returns:
            True if startup detected, False on timeout
        """
        self.detector.reset()
        start_time = time.time()
        saw_model_response = False
        all_output = ""

        while time.time() - start_time < self.startup_timeout:
            if not self.is_alive():
                self._log("ERROR", "PTY died during startup")
                return False

            try:
                chunk = self.process.read(self.DEFAULT_READ_CHUNK_SIZE)
                if chunk:
                    all_output += chunk
                    self.detector.add_data(chunk)

                    # In screen reader mode, wait for "Model:" which indicates
                    # Gemini has responded to our initial prompt
                    if not saw_model_response and 'Model:' in all_output:
                        saw_model_response = True
                        self._log("DEBUG", f"Initial response detected at {time.time()-start_time:.1f}s")

                    # After seeing Model response, wait for next input prompt
                    # Check in full buffer since they might be in different chunks
                    if saw_model_response:
                        # Find "Type your message" AFTER the Model response
                        model_pos = all_output.rfind('Model:')
                        type_msg_pos = all_output.find('Type your message', model_pos)
                        if type_msg_pos > model_pos:
                            self._log("DEBUG", f"Ready for input at {time.time()-start_time:.1f}s")

                            # V7 Sprint 13: Capture and extract initial response
                            self._startup_raw_output = all_output
                            self._initial_response = self._extract_response(all_output)

                            return True

            except Exception as e:
                self._log("WARNING", f"Read error during startup: {e}")
                pass

            time.sleep(0.1)

        # Timeout - log what we got
        self._log("WARNING", f"Startup timeout. Got {len(all_output)} bytes, saw_model={saw_model_response}")
        # Still save what we got in case it's useful
        self._startup_raw_output = all_output
        return False

    def get_initial_response(self) -> Optional[str]:
        """
        Get the response from the initial prompt (for single-shot mode).

        Returns:
            The extracted initial response, or None if not available
        """
        return self._initial_response

    def get_startup_raw_output(self) -> str:
        """
        Get the raw output captured during startup (for debugging).

        Returns:
            Raw PTY output from startup phase
        """
        return self._startup_raw_output

    def send_prompt(self, prompt: str, timeout: Optional[float] = None) -> str:
        """
        Send a prompt and wait for the complete response.

        Args:
            prompt: The prompt to send
            timeout: Optional timeout override

        Returns:
            The response text (ANSI stripped)

        Raises:
            RuntimeError: If PTY not running and restart failed
            TimeoutError: If response timeout exceeded
        """
        timeout = timeout or self.response_timeout

        # Longer stabilization delay (matches test_pty_simple.py timing)
        time.sleep(1.0)

        # Ensure process is running
        is_running = self.is_alive()
        self._log("DEBUG", f"Pre-send is_alive: {is_running}, process: {self.process}")
        if not is_running:
            if not self._try_restart():
                raise RuntimeError("PTY process not running and restart failed")

        with self._lock:
            start_time = time.time()
            self.detector.reset()

            try:
                # Send prompt - CRITICAL: Use \n only (not \r\n) for TUI submission
                # Send all at once with newline
                self.process.write(prompt + '\n')
                self._log("DEBUG", f"Sent prompt ({len(prompt)} chars)")

                # Read response immediately (no delay - detection handles the flow)
                response = self._read_until_complete(timeout)

                # Update metrics
                elapsed = time.time() - start_time
                self.metrics.invocation_count += 1
                self.metrics.total_response_time += elapsed
                self.metrics.last_response_time = elapsed
                self._log("DEBUG", f"Response received in {elapsed:.1f}s")

                return response

            except TimeoutError:
                self.metrics.errors.append(f"Timeout after {timeout}s")
                raise

            except Exception as e:
                self.metrics.errors.append(f"Send error: {e}")
                raise RuntimeError(f"Failed to send prompt: {e}")

    def _read_until_complete(self, timeout: float) -> str:
        """
        Read from PTY until response is complete.

        Simplified detection that matches the working test_pty_simple.py pattern:
        - Wait until we see content being generated (User:, responding, etc.)
        - Then wait for the next "Type your message" prompt (ready for next input)
        - Use idle detection as backup

        Args:
            timeout: Maximum time to wait

        Returns:
            Complete response text (ANSI stripped)
        """
        start_time = time.time()
        raw_output = ""
        saw_user_echo = False
        saw_activity = False  # Any sign that our prompt is being processed

        while time.time() - start_time < timeout:
            if not self.is_alive():
                raise RuntimeError("PTY process died during response")

            try:
                chunk = self.process.read(self.DEFAULT_READ_CHUNK_SIZE)
                if chunk:
                    raw_output += chunk
                    self.detector.add_data(chunk)
                    # Log content sample for first few chunks
                    if len(raw_output) < 3000:
                        clean = ANSIParser.extract_visible_text(chunk)[:80]
                        self._log("DEBUG", f"Got {len(chunk)} bytes: {clean}")

                    # Track any processing activity
                    if 'User:' in chunk or 'Queued' in chunk:
                        saw_user_echo = True
                        self._log("DEBUG", f"User prompt queued at {time.time()-start_time:.1f}s")
                    if 'responding' in chunk.lower() or 'Model:' in chunk:
                        saw_activity = True
                        self._log("DEBUG", f"Response activity at {time.time()-start_time:.1f}s")

                    # Completion: After seeing activity, wait for next input prompt
                    if saw_activity and 'Type your message' in chunk:
                        self._log("DEBUG", f"Response complete at {time.time()-start_time:.1f}s")
                        break

                    # Alternative completion: Model response followed by input prompt anywhere in buffer
                    if saw_activity and 'Type your message' in raw_output:
                        # Check if Type your message comes after our activity
                        if raw_output.rfind('Type your message') > raw_output.find('responding'):
                            self._log("DEBUG", f"Response complete (buffer check) at {time.time()-start_time:.1f}s")
                            break

                else:
                    # No data - check idle timeout (only after seeing some activity)
                    if saw_activity and self.detector.is_idle():
                        self._log("DEBUG", f"Response idle at {time.time()-start_time:.1f}s")
                        break
                    # Log periodic no-data status
                    elapsed = time.time() - start_time
                    if int(elapsed) % 5 == 0 and int(elapsed) > 0:
                        self._log("DEBUG", f"No data at {elapsed:.0f}s, total bytes={len(raw_output)}, alive={self.is_alive()}")
                    time.sleep(0.05)

            except Exception as e:
                # Read error - might be temporary
                time.sleep(0.1)
                if not self.is_alive():
                    raise RuntimeError(f"PTY died: {e}")

        # Check for timeout
        if time.time() - start_time >= timeout:
            clean_sample = ANSIParser.extract_visible_text(raw_output[-500:]) if raw_output else "(empty)"
            self._log("WARNING", f"Timeout: user_echo={saw_user_echo}, activity={saw_activity}, sample={clean_sample[:100]}")
            raise TimeoutError(f"Response timeout after {timeout}s")

        # Clean and return response
        return self._extract_response(raw_output)

    def _extract_response(self, raw_output: str) -> str:
        """
        Extract the actual response from raw PTY output.

        Handles:
        - ANSI escape codes
        - Spinner/progress indicators
        - Screen reader mode UI elements
        - JSON extraction if in JSON mode
        """
        # Strip ANSI codes
        clean = ANSIParser.extract_visible_text(raw_output)

        # In screen reader mode, look for "Model: " prefix which indicates Gemini's response
        # Format: "Model:  <response text>"
        model_match = re.search(r'Model:\s+(.+?)(?=\s*(?:User:|Type your message|$))',
                                clean, re.DOTALL | re.IGNORECASE)
        if model_match:
            response_text = model_match.group(1).strip()
            # If JSON mode, try to extract JSON
            if self.json_mode and '{' in response_text:
                json_result = self._extract_json(response_text)
                if json_result:
                    return json_result
            return response_text

        # Fallback: Remove common Gemini UI patterns
        lines = clean.split('\n')
        response_lines = []

        skip_patterns = [
            r'^\s*$',                               # Empty lines
            r'^.*gemini-\d.*preview.*$',            # Model name in status bar
            r'^.*\d+\.\d+ [KMG]?B\s*$',             # Memory usage
            r'^.*no sandbox.*$',                    # Sandbox warning
            r'^.*N7C\*?\).*$',                      # Branch indicator
            r'^.*C:\\.*workspace.*$',               # Path display
            r'^.*❯\s*$',                            # Prompt marker alone
            r'^.*screen reader.*$',                 # Screen reader notice
            r'^.*settings\.json.*$',                # Settings notice
            r'^.*YOLO mode.*$',                     # YOLO mode indicator
            r'^.*Using:.*GEMINI\.md.*$',            # GEMINI.md notice
            r'^.*Type your message.*$',             # Input prompt
            r'^.*Waiting for auth.*$',              # Auth spinner
            r'^.*responding.*$',                    # Responding status
            r'^.*ctrl \+ y.*$',                     # Toggle hint
            r'^User:.*$',                           # User message echo
            r'^Queued.*$',                          # Queue notice
            r'^[⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏].*$',                  # Spinner characters
        ]

        skip_regex = re.compile('|'.join(skip_patterns), re.IGNORECASE)

        for line in lines:
            if not skip_regex.match(line):
                response_lines.append(line)

        result = '\n'.join(response_lines).strip()

        # If JSON mode, try to extract JSON
        if self.json_mode and '{' in result:
            json_result = self._extract_json(result)
            if json_result:
                return json_result

        return result

    def _extract_json(self, text: str) -> Optional[str]:
        """
        Extract JSON object from text.

        Returns:
            JSON string if found and valid, None otherwise
        """
        # Find JSON boundaries
        start = text.find('{')
        if start == -1:
            return None

        # Find matching closing brace
        depth = 0
        in_string = False
        escape_next = False

        for i, char in enumerate(text[start:], start):
            if escape_next:
                escape_next = False
                continue

            if char == '\\' and in_string:
                escape_next = True
                continue

            if char == '"' and not escape_next:
                in_string = not in_string
                continue

            if in_string:
                continue

            if char == '{':
                depth += 1
            elif char == '}':
                depth -= 1
                if depth == 0:
                    json_str = text[start:i+1]
                    # Validate it's parseable
                    try:
                        json.loads(json_str)
                        return json_str
                    except json.JSONDecodeError:
                        return None

        return None

    def _try_restart(self) -> bool:
        """
        Try to restart the PTY process.

        Returns:
            True if restart successful
        """
        if self._restart_count >= self.max_restarts:
            self._log("ERROR", f"Max restarts ({self.max_restarts}) exceeded")
            return False

        self._restart_count += 1
        self.metrics.restart_count += 1
        self._log("WARNING", f"Restarting PTY (attempt {self._restart_count}/{self.max_restarts})")

        self.close()
        time.sleep(1.0)  # Brief pause before restart

        return self.start()

    def close(self):
        """Gracefully close the PTY process."""
        with self._lock:
            if self.process:
                try:
                    if self.process.isalive():
                        # Try graceful exit first
                        try:
                            self.process.write('/exit\r\n')
                            time.sleep(0.5)
                        except Exception:
                            pass

                        # Terminate if still running
                        if self.process.isalive():
                            self.process.terminate()

                    self._log("DEBUG", "PTY process closed")

                except Exception as e:
                    self._log("WARNING", f"Error closing PTY: {e}")

                finally:
                    self.process = None
                    self._started = False

    def get_stats(self) -> Dict[str, Any]:
        """Get PTY statistics."""
        return {
            "available": self.is_available,
            "alive": self.is_alive(),
            "pid": self.process.pid if self.process else None,
            "model": self.model,
            "uptime_seconds": round(self.metrics.uptime, 1),
            "invocations": self.metrics.invocation_count,
            "avg_response_time": round(self.metrics.avg_response_time, 2),
            "last_response_time": round(self.metrics.last_response_time, 2),
            "restarts": self.metrics.restart_count,
            "errors": self.metrics.errors[-5:],  # Last 5 errors
        }

    def _log(self, level: str, message: str):
        """Log a message to stderr."""
        print(f"[PTY:{level}] {message}", file=sys.stderr)


# Convenience function for testing
def test_pty_basic():
    """Basic PTY functionality test."""
    import os
    os.environ['PYTHONIOENCODING'] = 'utf-8'

    if not WINPTY_AVAILABLE:
        print("winpty not available")
        return False

    # Mock config
    class MockConfig:
        gemini_cli_path = r'C:\Users\yann.abadie\AppData\Roaming\npm\gemini.CMD'
        gemini_pty_startup_timeout = 60.0  # Longer timeout for startup
        gemini_pty_timeout = 60.0
        gemini_pty_idle_timeout = 5.0
        gemini_pty_max_restarts = 3
        gemini_stream_json = False  # Text mode for simple test

    workspace = Path(r'C:\Code\NEXUS\20_NEXUS\NEXUS_V7_CHRYSALIS\workspace')

    pty = PersistentGeminiPTY(
        MockConfig(),
        workspace,
        model="gemini-3-pro-preview"
    )

    print("Starting PTY with initial prompt...")
    # Use initial prompt that will get a known response
    if not pty.start("Reply with just: STARTUP_OK"):
        print("Failed to start")
        return False

    print(f"Started! PID: {pty.process.pid}")

    # Test 1: Send follow-up prompt
    print("\n[Test 1] Sending follow-up: 'Say just OK'")
    try:
        response = pty.send_prompt("Say just OK", timeout=60)
        print(f"Response ({len(response)} chars): {response[:200]}")
        test1_pass = "OK" in response.upper()
        print(f"Test 1: {'PASS' if test1_pass else 'FAIL'}")
    except Exception as e:
        print(f"Test 1 Error: {e}")
        test1_pass = False

    # Test 2: Multi-turn - another prompt
    print("\n[Test 2] Sending: 'What is 2+2? Reply with just the number.'")
    try:
        response = pty.send_prompt("What is 2+2? Reply with just the number.", timeout=60)
        print(f"Response ({len(response)} chars): {response[:200]}")
        test2_pass = "4" in response
        print(f"Test 2: {'PASS' if test2_pass else 'FAIL'}")
    except Exception as e:
        print(f"Test 2 Error: {e}")
        test2_pass = False

    print("\nClosing...")
    pty.close()

    print(f"\nStats: {pty.get_stats()}")

    success = test1_pass and test2_pass
    return success


if __name__ == "__main__":
    # Fix Windows encoding
    import sys
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

    result = test_pty_basic()
    print(f"\n{'='*40}")
    print(f"Overall Test: {'PASSED' if result else 'FAILED'}")
    print(f"{'='*40}")
    sys.exit(0 if result else 1)
