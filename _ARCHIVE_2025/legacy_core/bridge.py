import subprocess
import shutil
from typing import Dict, Optional
from .logger import NexusLogger
from .persistent_bridge import ClaudePersistentSession

class AIBridge:
    _persistent_sessions: Dict[str, ClaudePersistentSession] = {}
    
    # Mapping 19/11/2025
    MODEL_MAP = {
        "sonnet": "claude-sonnet-4-5-20250929",
        "opus": "claude-opus-4-1-20250805", 
        "haiku": "claude-haiku-4-5-20251001"
    }

    def __init__(self, logger: NexusLogger):
        self.logger = logger
        self._check_dependencies()

    def _check_dependencies(self):
        if not shutil.which("gemini"): self.logger.system("WARNING: 'gemini' CLI not found.")
        if not shutil.which("claude"): self.logger.system("WARNING: 'claude' CLI not found.")

    def get_persistent_session(self, model: str) -> ClaudePersistentSession:
        real_model = self.MODEL_MAP.get(model, model)
        
        # Session ID stable pour garder la mémoire (ex: nexus-session-opus)
        session_key = f"nexus-session-{model}" 
        
        if real_model not in self._persistent_sessions:
            session = ClaudePersistentSession(
                model=real_model, 
                session_id=session_key, # Stable ID
                logger=self.logger
            )
            if session.start():
                self._persistent_sessions[real_model] = session
            else:
                # Retry with alias
                session = ClaudePersistentSession(model=model, session_id=session_key, logger=self.logger)
                if session.start():
                    self._persistent_sessions[real_model] = session
                else:
                    raise RuntimeError(f"Failed to start {real_model}")
        
        return self._persistent_sessions[real_model]

    def call_claude(self, prompt: str, model: str = "sonnet", persistent: bool = True) -> str:
        if persistent:
            try:
                session = self.get_persistent_session(model)
                return session.send_message(prompt)
            except Exception as e:
                self.logger.log("SYSTEM", "ERROR", f"Persistent call failed: {e}", "⚠️")
        
        # Fallback
        real_model = self.MODEL_MAP.get(model, model)
        cmd = ["claude", "--print", prompt, "--model", real_model]
        return self._execute_oneshot(cmd, f"CLAUDE-{model.upper()}")

    def call_gemini(self, prompt: str, model: str = "gemini-3-pro-preview") -> str:
        cmd = ["gemini", "--model", model, "--yolo", "--resume", "latest", prompt]
        return self._execute_oneshot(cmd, "GEMINI")

    def _execute_oneshot(self, cmd: list, source_name: str) -> str:
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace', shell=True)
            if result.returncode != 0:
                self.logger.log(source_name, "ERROR", result.stderr, "❌")
                return f"ERROR: {result.stderr}"
            return result.stdout.strip()
        except Exception as e:
            return f"EXCEPTION: {str(e)}"

    def close_all_sessions(self):
        for s in self._persistent_sessions.values(): s.close()
        self._persistent_sessions.clear()
