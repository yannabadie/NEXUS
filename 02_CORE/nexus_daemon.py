#!/usr/bin/env python
"""
NEXUS DAEMON - Robust Windows-Compatible Bridge
Handles bidirectional communication between Claude CLI and Gemini
"""

import subprocess
import sys
import json
import time
import os
import threading
import queue
from pathlib import Path
from datetime import datetime
import traceback
import signal

# ============= CONFIGURATION =============
BASE_DIR = Path(__file__).parent.parent  # 20_NEXUS
IPC_DIR = BASE_DIR / "02_CORE" / "ipc"
INPUT_FILE = IPC_DIR / "input.json"
OUTPUT_FILE = IPC_DIR / "output.json"
LOG_FILE = IPC_DIR / "daemon.log"
PID_FILE = IPC_DIR / "daemon.pid"
STATE_FILE = IPC_DIR / "state.json"

# Claude CLI configuration
CLAUDE_MODEL = "claude-opus-4-1-20250805"
MCP_CONFIG = BASE_DIR / "mcp_config.json"

# Timeouts and intervals
POLL_INTERVAL = 0.1  # 100ms
WRITE_RETRY = 3
READ_TIMEOUT = 30  # seconds
HEARTBEAT_INTERVAL = 5  # seconds

# ============= UTILITIES =============

class Logger:
    """Thread-safe logger with file and console output"""
    def __init__(self, log_file):
        self.log_file = log_file
        self.lock = threading.Lock()

    def log(self, level, msg, error=None):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        with self.lock:
            log_entry = f"[{timestamp}] [{level}] {msg}"
            if error:
                log_entry += f"\n  ERROR: {str(error)}"
                if level == "ERROR":
                    log_entry += f"\n  TRACE: {traceback.format_exc()}"

            # Console output
            print(log_entry)

            # File output
            try:
                with open(self.log_file, "a", encoding="utf-8") as f:
                    f.write(log_entry + "\n")
            except Exception as e:
                print(f"LOGGER WRITE ERROR: {e}")

logger = Logger(LOG_FILE)

def ensure_directories():
    """Create necessary directories"""
    IPC_DIR.mkdir(parents=True, exist_ok=True)
    logger.log("INFO", f"IPC directory ready: {IPC_DIR}")

def save_state(state):
    """Save daemon state for recovery"""
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
    except Exception as e:
        logger.log("ERROR", f"Failed to save state", e)

def load_state():
    """Load previous daemon state"""
    try:
        if STATE_FILE.exists():
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        logger.log("WARN", f"Could not load state", e)
    return {"sessions": 0, "last_start": None}

def write_pid():
    """Write daemon PID for external monitoring"""
    try:
        with open(PID_FILE, "w") as f:
            f.write(str(os.getpid()))
    except Exception as e:
        logger.log("ERROR", f"Failed to write PID", e)

# ============= CLAUDE PROCESS MANAGER =============

class ClaudeProcess:
    """Manages Claude CLI subprocess with robust I/O handling"""

    def __init__(self):
        self.process = None
        self.stdout_reader = None
        self.stderr_reader = None
        self.output_queue = queue.Queue()
        self.error_queue = queue.Queue()
        self.running = False
        self.lock = threading.Lock()

    def start(self):
        """Start Claude CLI process"""
        # Check MCP config
        if MCP_CONFIG.exists():
            logger.log("INFO", f"Using MCP config: {MCP_CONFIG}")
            mcp_args = ["--mcp-config", str(MCP_CONFIG.absolute())]
        else:
            logger.log("WARN", "MCP config not found, proceeding without it")
            mcp_args = []

        # Build command
        cmd = [
            "claude",
            "-p",  # Persistent mode
            "--model", CLAUDE_MODEL
        ] + mcp_args

        logger.log("INFO", f"Starting Claude: {' '.join(cmd)}")

        try:
            # Start process with proper Windows settings
            startupinfo = None
            if sys.platform == "win32":
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE

            self.process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=False,  # Use bytes for better control
                bufsize=0,  # Unbuffered
                startupinfo=startupinfo,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            )

            self.running = True

            # Start reader threads
            self.stdout_reader = threading.Thread(
                target=self._read_stream,
                args=(self.process.stdout, self.output_queue, "STDOUT"),
                daemon=True
            )
            self.stderr_reader = threading.Thread(
                target=self._read_stream,
                args=(self.process.stderr, self.error_queue, "STDERR"),
                daemon=True
            )

            self.stdout_reader.start()
            self.stderr_reader.start()

            logger.log("INFO", f"Claude started with PID {self.process.pid}")
            return True

        except Exception as e:
            logger.log("ERROR", "Failed to start Claude", e)
            self.running = False
            return False

    def _read_stream(self, stream, output_queue, stream_name):
        """Read from stream continuously"""
        buffer = b""
        while self.running:
            try:
                chunk = stream.read(1024)
                if not chunk:
                    break

                buffer += chunk

                # Try to decode and extract complete lines
                try:
                    text = buffer.decode('utf-8', errors='ignore')
                    lines = text.split('\n')

                    # Keep incomplete line in buffer
                    if not text.endswith('\n'):
                        buffer = lines[-1].encode('utf-8')
                        lines = lines[:-1]
                    else:
                        buffer = b""

                    for line in lines:
                        if line.strip():
                            output_queue.put({
                                'type': stream_name,
                                'data': line,
                                'timestamp': time.time()
                            })

                except Exception as e:
                    logger.log("WARN", f"Decode error in {stream_name}: {e}")

            except Exception as e:
                if self.running:
                    logger.log("ERROR", f"Read error in {stream_name}", e)
                break

    def send_message(self, message):
        """Send message to Claude"""
        with self.lock:
            if not self.process or self.process.poll() is not None:
                logger.log("ERROR", "Claude process not running")
                return False

            try:
                # Format message for Claude CLI
                # Try simple text first, then JSON if needed
                if isinstance(message, str):
                    # Direct text input
                    data = message + "\n"
                else:
                    # JSON formatted
                    data = json.dumps(message) + "\n"

                # Write to stdin
                self.process.stdin.write(data.encode('utf-8'))
                self.process.stdin.flush()

                logger.log("DEBUG", f"Sent to Claude: {data[:100]}...")
                return True

            except Exception as e:
                logger.log("ERROR", "Failed to send message", e)
                return False

    def get_output(self, timeout=0.1):
        """Get output from Claude (non-blocking)"""
        outputs = []
        deadline = time.time() + timeout

        while time.time() < deadline:
            # Check stdout
            try:
                while not self.output_queue.empty():
                    outputs.append(self.output_queue.get_nowait())
            except queue.Empty:
                pass

            # Check stderr
            try:
                while not self.error_queue.empty():
                    error = self.error_queue.get_nowait()
                    logger.log("STDERR", error['data'])
            except queue.Empty:
                pass

            if outputs:
                break
            time.sleep(0.01)

        return outputs

    def is_alive(self):
        """Check if process is still running"""
        return self.process and self.process.poll() is None

    def terminate(self):
        """Gracefully terminate Claude process"""
        self.running = False
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
            except:
                self.process.kill()
            logger.log("INFO", "Claude process terminated")

# ============= COMMUNICATION BRIDGE =============

class NexusBridge:
    """Main bridge between file-based IPC and Claude process"""

    def __init__(self):
        self.claude = ClaudeProcess()
        self.running = False
        self.last_input_mtime = 0
        self.conversation_history = []
        self.state = load_state()

    def start(self):
        """Start the bridge"""
        logger.log("INFO", "=== NEXUS DAEMON STARTING ===")

        # Initialize
        ensure_directories()
        write_pid()

        # Start Claude
        if not self.claude.start():
            logger.log("ERROR", "Failed to start Claude, exiting")
            return False

        # Update state
        self.state['sessions'] = self.state.get('sessions', 0) + 1
        self.state['last_start'] = datetime.now().isoformat()
        save_state(self.state)

        # Initialize input file if needed
        if not INPUT_FILE.exists():
            self._write_input_file({"status": "ready", "timestamp": time.time()})

        # Start main loop
        self.running = True
        self._main_loop()

        return True

    def _write_input_file(self, data):
        """Safely write to input file"""
        try:
            temp_file = INPUT_FILE.with_suffix('.tmp')
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            temp_file.replace(INPUT_FILE)
        except Exception as e:
            logger.log("ERROR", "Failed to write input file", e)

    def _write_output_file(self, data):
        """Safely write to output file"""
        try:
            temp_file = OUTPUT_FILE.with_suffix('.tmp')
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            temp_file.replace(OUTPUT_FILE)
            logger.log("DEBUG", f"Wrote output: {str(data)[:200]}...")
        except Exception as e:
            logger.log("ERROR", "Failed to write output file", e)

    def _process_input(self):
        """Check and process input file"""
        try:
            if not INPUT_FILE.exists():
                return

            stat = os.stat(INPUT_FILE)
            if stat.st_mtime <= self.last_input_mtime:
                return

            self.last_input_mtime = stat.st_mtime

            # Read input with retries
            for attempt in range(3):
                try:
                    time.sleep(0.05)  # Small delay for file write completion
                    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    break
                except json.JSONDecodeError:
                    if attempt == 2:
                        logger.log("ERROR", "Invalid JSON in input file")
                        return
                    time.sleep(0.1)

            # Process different message types
            if 'prompt' in data:
                # Standard prompt
                prompt = data['prompt']
                logger.log("INFO", f"Received prompt: {prompt[:100]}...")

                # Send to Claude
                success = self.claude.send_message(prompt)

                if success:
                    # Record in history
                    self.conversation_history.append({
                        'type': 'user',
                        'content': prompt,
                        'timestamp': time.time()
                    })

                    # Collect response
                    self._collect_response()
                else:
                    self._write_output_file({
                        'status': 'error',
                        'error': 'Failed to send message to Claude',
                        'timestamp': time.time()
                    })

            elif 'command' in data:
                # System command
                self._handle_command(data['command'])

        except Exception as e:
            logger.log("ERROR", "Error processing input", e)

    def _collect_response(self):
        """Collect response from Claude"""
        response_parts = []
        start_time = time.time()
        last_output_time = start_time

        while time.time() - start_time < READ_TIMEOUT:
            outputs = self.claude.get_output(timeout=0.5)

            if outputs:
                last_output_time = time.time()
                for output in outputs:
                    if output['type'] == 'STDOUT':
                        response_parts.append(output['data'])

            # Check if response seems complete (no output for 1 second)
            if response_parts and time.time() - last_output_time > 1.0:
                break

        if response_parts:
            response = '\n'.join(response_parts)

            # Try to parse as JSON first
            try:
                response_data = json.loads(response)
            except:
                # Plain text response
                response_data = {
                    'type': 'assistant',
                    'content': response,
                    'timestamp': time.time()
                }

            # Record and output
            self.conversation_history.append(response_data)
            self._write_output_file(response_data)

            logger.log("INFO", f"Response collected: {len(response)} chars")
        else:
            logger.log("WARN", "No response received from Claude")
            self._write_output_file({
                'status': 'timeout',
                'error': 'No response within timeout',
                'timestamp': time.time()
            })

    def _handle_command(self, command):
        """Handle system commands"""
        logger.log("INFO", f"Handling command: {command}")

        if command == "status":
            self._write_output_file({
                'status': 'running',
                'claude_alive': self.claude.is_alive(),
                'sessions': self.state['sessions'],
                'history_length': len(self.conversation_history),
                'timestamp': time.time()
            })
        elif command == "history":
            self._write_output_file({
                'history': self.conversation_history,
                'timestamp': time.time()
            })
        elif command == "clear":
            self.conversation_history = []
            self._write_output_file({
                'status': 'cleared',
                'timestamp': time.time()
            })
        elif command == "restart":
            logger.log("INFO", "Restarting Claude process...")
            self.claude.terminate()
            time.sleep(1)
            if self.claude.start():
                self._write_output_file({
                    'status': 'restarted',
                    'timestamp': time.time()
                })
            else:
                self._write_output_file({
                    'status': 'error',
                    'error': 'Failed to restart Claude',
                    'timestamp': time.time()
                })
        else:
            self._write_output_file({
                'status': 'error',
                'error': f'Unknown command: {command}',
                'timestamp': time.time()
            })

    def _heartbeat(self):
        """Periodic health check"""
        if not self.claude.is_alive():
            logger.log("ERROR", "Claude process died, attempting restart...")
            if not self.claude.start():
                logger.log("CRITICAL", "Failed to restart Claude")
                self.running = False

    def _main_loop(self):
        """Main event loop"""
        logger.log("INFO", "Entering main loop")

        last_heartbeat = time.time()

        try:
            while self.running:
                # Check Claude health
                if time.time() - last_heartbeat > HEARTBEAT_INTERVAL:
                    self._heartbeat()
                    last_heartbeat = time.time()

                # Process input
                self._process_input()

                # Check for unexpected output
                outputs = self.claude.get_output(timeout=0)
                for output in outputs:
                    if output['type'] == 'STDOUT':
                        logger.log("ASYNC", f"Unexpected output: {output['data']}")

                # Brief sleep
                time.sleep(POLL_INTERVAL)

        except KeyboardInterrupt:
            logger.log("INFO", "Interrupt received, shutting down...")
        except Exception as e:
            logger.log("ERROR", "Fatal error in main loop", e)
        finally:
            self.stop()

    def stop(self):
        """Stop the bridge"""
        logger.log("INFO", "Stopping NEXUS daemon...")
        self.running = False

        # Terminate Claude
        self.claude.terminate()

        # Save final state
        self.state['last_stop'] = datetime.now().isoformat()
        save_state(self.state)

        # Clean up PID file
        try:
            PID_FILE.unlink()
        except:
            pass

        logger.log("INFO", "=== NEXUS DAEMON STOPPED ===")

# ============= SIGNAL HANDLERS =============

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.log("INFO", f"Received signal {signum}")
    if hasattr(signal_handler, 'bridge'):
        signal_handler.bridge.stop()
    sys.exit(0)

# ============= MAIN ENTRY POINT =============

def main():
    """Main entry point"""
    # Set up signal handlers
    if sys.platform != "win32":
        signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    # Create and start bridge
    bridge = NexusBridge()
    signal_handler.bridge = bridge  # Store for signal handler

    # Run
    success = bridge.start()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    # Ensure proper Windows console encoding
    if sys.platform == "win32":
        import locale
        if sys.stdout.encoding != 'utf-8':
            sys.stdout.reconfigure(encoding='utf-8')
        if sys.stderr.encoding != 'utf-8':
            sys.stderr.reconfigure(encoding='utf-8')

    main()