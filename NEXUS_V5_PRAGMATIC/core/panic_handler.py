"""
NEXUS V5.0 - Panic Handler
Système d'arrêt d'urgence.
"""
from pathlib import Path
from typing import Optional


class PanicHandler:
    """Gestionnaire d'arrêt d'urgence."""

    def __init__(self, workspace_path: Path):
        self.workspace_path = workspace_path
        self.panic_file = workspace_path / "_IO_BUFFER" / "STOP_NOW"
        self.panic_msg_file = workspace_path / "_IO_BUFFER" / "PANIC_MSG.txt"

    def check_panic(self) -> Optional[str]:
        """
        Vérifie si un arrêt d'urgence a été demandé.

        Returns:
            Message de panic si le fichier STOP_NOW existe, None sinon
        """
        if self.panic_file.exists():
            if self.panic_msg_file.exists():
                return self.panic_msg_file.read_text(encoding="utf-8").strip()
            return "Emergency stop requested (no message)"
        return None

    def trigger_panic(self, reason: str):
        """
        Déclenche un arrêt d'urgence.

        Args:
            reason: Raison de l'arrêt
        """
        self.panic_file.touch()
        self.panic_msg_file.write_text(reason, encoding="utf-8")

    def clear_panic(self):
        """Efface les fichiers de panic."""
        if self.panic_file.exists():
            self.panic_file.unlink()
        if self.panic_msg_file.exists():
            self.panic_msg_file.unlink()
