"""
Panic System - Gestion des erreurs critiques et panic states

Inspiré de NEXUS V5 mais amélioré pour V6.
"""
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional
import json


class PanicSystem:
    """
    Système de panic pour gérer les états critiques

    Features:
    - Détection de panic (stalemate, erreurs critiques, loops infinis)
    - Enregistrement de panic dans fichier
    - Auto-recovery ou escalade vers user
    - Panic history pour debugging
    """

    def __init__(self, workspace_path: Path, max_stalemate: int = 5):
        """
        Args:
            workspace_path: Workspace NEXUS
            max_stalemate: Nombre max de stalemates avant panic
        """
        self.workspace_path = workspace_path
        self.max_stalemate = max_stalemate

        # Panic file location
        self.panic_dir = workspace_path / ".nexus" / "panic"
        self.panic_dir.mkdir(parents=True, exist_ok=True)

        self.panic_file = self.panic_dir / "panic.json"
        self.panic_history = self.panic_dir / "panic_history.jsonl"

        # State tracking
        self.stalemate_counter = 0
        self.consecutive_errors = 0
        self.is_in_panic = False
        self.panic_reason: Optional[str] = None

    def check_stalemate(self) -> bool:
        """
        Incrémente le compteur de stalemate et vérifie si panic

        Returns:
            True si panic atteint
        """
        self.stalemate_counter += 1

        if self.stalemate_counter >= self.max_stalemate:
            self._trigger_panic(
                reason="STALEMATE",
                details=f"Stalemate counter reached maximum ({self.stalemate_counter}/{self.max_stalemate})"
            )
            return True

        return False

    def reset_stalemate(self):
        """Reset stalemate counter (appelé après progrès)"""
        self.stalemate_counter = 0

    def record_error(self, error_type: str, error_message: str) -> bool:
        """
        Enregistre une erreur et vérifie si panic

        Args:
            error_type: Type d'erreur (TOOL_FAILURE, PARSING_ERROR, etc.)
            error_message: Message d'erreur

        Returns:
            True si panic atteint
        """
        self.consecutive_errors += 1

        # Log error to panic history
        self._log_to_history({
            "type": "ERROR",
            "error_type": error_type,
            "message": error_message,
            "consecutive_errors": self.consecutive_errors,
            "timestamp": datetime.utcnow().isoformat()
        })

        # Trigger panic après 3 erreurs consécutives
        if self.consecutive_errors >= 3:
            self._trigger_panic(
                reason="CONSECUTIVE_ERRORS",
                details=f"3+ consecutive errors: {error_type} - {error_message}"
            )
            return True

        return False

    def reset_errors(self):
        """Reset error counter (appelé après succès)"""
        self.consecutive_errors = 0

    def trigger_panic_explicit(self, reason: str, details: str):
        """
        Trigger panic explicitement (appelé par orchestrator)

        Args:
            reason: Raison du panic (INFINITE_LOOP, ZOMBIE_PLAN, etc.)
            details: Détails additionnels
        """
        self._trigger_panic(reason, details)

    def _trigger_panic(self, reason: str, details: str):
        """Déclenche le panic state"""
        if self.is_in_panic:
            return  # Already in panic

        self.is_in_panic = True
        self.panic_reason = reason

        panic_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "reason": reason,
            "details": details,
            "stalemate_counter": self.stalemate_counter,
            "consecutive_errors": self.consecutive_errors
        }

        # Write panic file
        self.panic_file.write_text(json.dumps(panic_data, indent=2), encoding='utf-8')

        # Log to history
        self._log_to_history({
            "type": "PANIC",
            **panic_data
        })

    def is_panicked(self) -> bool:
        """Check if system is in panic"""
        return self.is_in_panic

    def get_panic_info(self) -> Optional[Dict]:
        """
        Récupère les infos de panic

        Returns:
            Panic data dict ou None
        """
        if not self.panic_file.exists():
            return None

        try:
            return json.loads(self.panic_file.read_text(encoding='utf-8'))
        except:
            return None

    def clear_panic(self):
        """
        Clear panic state (appelé par /reset ou auto-recovery)
        """
        self.is_in_panic = False
        self.panic_reason = None
        self.stalemate_counter = 0
        self.consecutive_errors = 0

        # Remove panic file
        if self.panic_file.exists():
            self.panic_file.unlink()

        # Log recovery
        self._log_to_history({
            "type": "RECOVERY",
            "timestamp": datetime.utcnow().isoformat(),
            "message": "Panic cleared, system recovered"
        })

    def _log_to_history(self, event: Dict):
        """Log event to panic history (JSONL)"""
        try:
            with open(self.panic_history, 'a', encoding='utf-8') as f:
                f.write(json.dumps(event) + '\n')
        except:
            pass  # Don't crash on logging failure

    def get_status(self) -> Dict:
        """
        Get current panic system status

        Returns:
            Status dict avec tous les compteurs
        """
        return {
            "is_panicked": self.is_in_panic,
            "panic_reason": self.panic_reason,
            "stalemate_counter": self.stalemate_counter,
            "consecutive_errors": self.consecutive_errors,
            "max_stalemate": self.max_stalemate,
            "panic_file_exists": self.panic_file.exists()
        }
