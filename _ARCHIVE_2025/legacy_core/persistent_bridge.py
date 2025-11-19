import subprocess
import threading
import queue
import time
import sys
import os
import shutil
from typing import Optional, Dict, Any, List
from .logger import NexusLogger

class ClaudePersistentSession:
    """
    Maintient une instance Claude vivante via REPL.
    Version V2 : Renforcée avec --dangerously-skip-permissions et Session ID.
    """

    def __init__(self, model: str = "opus", session_id: str = None, logger: Optional[NexusLogger] = None):
        self.process: Optional[subprocess.Popen] = None
        self.response_queue = queue.Queue()
        self.model = model
        self.session_id = session_id or f"nexus_{int(time.time())}"
        self.delimiter = "---CLAUDE_RESPONSE_END---"
        self.logger = logger or NexusLogger()
        self.is_active = False
        self.executable_path = self._find_executable()

    def _find_executable(self) -> str:
        if sys.platform == "win32":
            npm_roaming = os.path.join(os.getenv("APPDATA"), "npm")
            claude_cmd = os.path.join(npm_roaming, "claude.cmd")
            if os.path.exists(claude_cmd):
                return claude_cmd
        return shutil.which("claude") or "claude"

    def start(self) -> bool:
        try:
            self.logger.system(f"🚀 STARTING PERSISTENT CLAUDE ({self.model}) ID={self.session_id}...")
            
            env = os.environ.copy()
            env["PYTHONIOENCODING"] = "utf-8"

            # LES FLAGS SAUVEURS
            cmd = [
                self.executable_path, 
                "--model", self.model,
                "--session-id", self.session_id,
                "--dangerously-skip-permissions", # Bypass Y/n prompts
                "--permission-mode", "bypassPermissions" # Double tap
            ]
            
            self.process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                encoding='utf-8',
                env=env,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            )

            self.is_active = True

            # Threads de lecture
            self.stdout_thread = threading.Thread(target=self._read_stream, args=(self.process.stdout, "stdout"), daemon=True)
            self.stdout_thread.start()
            
            self.stderr_thread = threading.Thread(target=self._read_stream, args=(self.process.stderr, "stderr"), daemon=True)
            self.stderr_thread.start()
            
            time.sleep(3) # Un peu plus de temps pour le boot
            
            if self.process.poll() is None:
                self.logger.system(f"✅ Claude PID: {self.process.pid} is ALIVE")
                return True
            else:
                self.logger.system(f"❌ Start failed. RC: {self.process.returncode}")
                return False

        except Exception as e:
            self.logger.log("SYSTEM", "ERROR", f"Start Exception: {e}", "🔥")
            return False

    def _read_stream(self, stream, stream_name):
        buffer = []
        while self.is_active and self.process:
            try:
                line = stream.readline()
                if not line: break
                
                line = line.strip()
                if not line: continue

                # Debug intense pour comprendre ce qui se passe
                # if stream_name == "stderr": print(f"[STDERR] {line}")
                # if stream_name == "stdout": print(f"[STDOUT] {line}")

                if self.delimiter in line:
                    full = "\n".join(buffer)
                    self.response_queue.put({"status": "complete", "content": full})
                    buffer = []
                else:
                    buffer.append(line)
            except:
                break

    def send_message(self, message: str, timeout: int = 60) -> str:
        if not self.is_active or not self.process: return "ERROR: Dead process"

        try:
            # PROTOCOLE XML + DELIMITER
            # On demande à Claude d'ignorer tout décorum et de répondre brut
            prompt = f"""
{message}

[SYSTEM: CRITICAL INSTRUCTION]
1. Perform the task.
2. Output NOTHING else after your response except exactly this line:
{self.delimiter}
"""
            self.process.stdin.write(prompt + "\n")
            self.process.stdin.flush()
            
            try:
                resp = self.response_queue.get(timeout=timeout)
                if resp["status"] == "complete":
                    return resp["content"].replace(self.delimiter, "").strip()
                return f"ERROR: {resp.get('error')}"
            except queue.Empty:
                return f"TIMEOUT ({timeout}s)"

        except Exception as e:
            return f"EXCEPTION: {e}"

    def close(self):
        self.is_active = False
        if self.process:
            self.process.terminate()
