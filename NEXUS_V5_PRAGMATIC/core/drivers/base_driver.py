"""
NEXUS V5.0 - Base Driver
Classe abstraite pour les drivers d'agents.
"""
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any
import threading

try:
    from filelock import FileLock
    FILELOCK_AVAILABLE = True
except ImportError:
    FILELOCK_AVAILABLE = False
    # Fallback to threading lock
    class FileLock:
        """Fallback lock when filelock unavailable."""
        def __init__(self, lock_file):
            self._lock = threading.Lock()

        def __enter__(self):
            self._lock.acquire()
            return self

        def __exit__(self, *args):
            self._lock.release()


class BaseDriver(ABC):
    """Classe de base pour les drivers d'agents."""

    def __init__(self, workspace_path: Path, timeout: int = 120):
        self.workspace_path = workspace_path
        self.timeout = timeout
        self.lock = FileLock(workspace_path / "_IO_BUFFER" / "nexus.lock")

    @abstractmethod
    def invoke(self, context: str) -> Dict[str, Any]:
        """
        Invoque l'agent avec le contexte donné.

        Args:
            context: Contexte markdown à injecter

        Returns:
            Dict parsé depuis action_out.json
        """
        pass

    def write_context(self, context: str):
        """Écrit le contexte dans context_in.md avec verrouillage."""
        with self.lock:
            context_file = self.workspace_path / "_IO_BUFFER" / "context_in.md"
            context_file.write_text(context, encoding="utf-8")

    def read_response(self) -> Dict[str, Any]:
        """Lit la réponse depuis action_out.json avec verrouillage."""
        import json

        with self.lock:
            response_file = self.workspace_path / "_IO_BUFFER" / "action_out.json"
            return json.loads(response_file.read_text(encoding="utf-8"))
