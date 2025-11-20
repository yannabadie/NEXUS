"""
NEXUS V5.0 - Memory Module
Gestion du blackboard, compression mémorielle, state rollback, plan health.
"""
import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional


class MemoryManager:
    """Gestionnaire de mémoire avec rollback et compression."""

    def __init__(self, workspace_path: Path, compression_threshold: int = 100000):
        self.workspace_path = workspace_path
        self.compression_threshold = compression_threshold
        self.blackboard_path = workspace_path / ".nexus" / "blackboard.json"
        self.blackboard = self._load_state_with_recovery()

    def _load_state_with_recovery(self) -> Dict:
        """Charge l'état avec récupération automatique depuis backup."""
        try:
            return json.loads(self.blackboard_path.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"[NEXUS] État corrompu: {e}. Tentative restauration...")

            # Essayer .bak1
            backup1 = self.blackboard_path.with_suffix(".json.bak1")
            if backup1.exists():
                try:
                    print("[NEXUS] Restauration depuis .bak1")
                    return json.loads(backup1.read_text(encoding="utf-8"))
                except json.JSONDecodeError:
                    pass

            # Essayer .bak2
            backup2 = self.blackboard_path.with_suffix(".json.bak2")
            if backup2.exists():
                try:
                    print("[NEXUS] Restauration depuis .bak2")
                    return json.loads(backup2.read_text(encoding="utf-8"))
                except json.JSONDecodeError:
                    pass

            # Créer état vide par défaut
            print("[NEXUS] Aucun backup valide. Initialisation état vide.")
            return self._create_empty_state()

    def _create_empty_state(self) -> Dict:
        """Crée un état vide initial."""
        return {
            "objective": "",
            "mode": "Normal",
            "strategic_plan": [],
            "plan_health": {
                "steps_pending_more_than_20_turns": 0,
                "longest_pending_step_id": None,
                "last_progress_turn": 0,
                "drift_score": "LOW"
            },
            "recent_history": [],
            "compressed_history_summary": "",
            "current_state": {
                "active_agent": "Gemini",
                "iteration": 0,
                "token_count_estimate": 0,
                "stalemate_counter": 0,
                "last_action_signature": "",
                "pending_tool_validation": False
            }
        }

    def save_state_with_backup(self):
        """Sauvegarde l'état avec rotation des backups."""
        backup1 = self.blackboard_path.with_suffix(".json.bak1")
        backup2 = self.blackboard_path.with_suffix(".json.bak2")

        # Rotation : .bak1 → .bak2
        if backup1.exists():
            if backup2.exists():
                backup2.unlink()
            shutil.copy(backup1, backup2)

        # Sauvegarde : current → .bak1
        if self.blackboard_path.exists():
            shutil.copy(self.blackboard_path, backup1)

        # Écriture nouvel état
        self.blackboard_path.parent.mkdir(parents=True, exist_ok=True)
        self.blackboard_path.write_text(
            json.dumps(self.blackboard, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )

    def get_blackboard(self) -> Dict:
        """Retourne le blackboard actuel."""
        return self.blackboard

    def add_to_history(self, message: Dict):
        """Ajoute un message à l'historique."""
        self.blackboard["recent_history"].append({
            "agent": message.get("sender"),
            "timestamp": datetime.utcnow().isoformat(),
            "summary": message.get("action_summary", "")
        })

        # Limiter l'historique récent à 50 entrées
        if len(self.blackboard["recent_history"]) > 50:
            self.blackboard["recent_history"] = self.blackboard["recent_history"][-50:]

    def update_strategic_plan(self, plan_update: List[Dict]):
        """Met à jour le plan stratégique."""
        # Fusionner les mises à jour
        existing_ids = {step["step_id"] for step in self.blackboard["strategic_plan"]}

        for step in plan_update:
            if step["step_id"] in existing_ids:
                # Mettre à jour l'étape existante
                for i, existing in enumerate(self.blackboard["strategic_plan"]):
                    if existing["step_id"] == step["step_id"]:
                        self.blackboard["strategic_plan"][i] = step
                        break
            else:
                # Ajouter nouvelle étape
                self.blackboard["strategic_plan"].append(step)

    def calculate_plan_health(self) -> Dict:
        """Calcule la santé du plan stratégique."""
        current_turn = self.blackboard["current_state"]["iteration"]
        strategic_plan = self.blackboard["strategic_plan"]

        if not strategic_plan:
            return {
                "steps_pending_more_than_20_turns": 0,
                "longest_pending_step_id": None,
                "last_progress_turn": current_turn,
                "drift_score": "LOW"
            }

        # Étapes en attente
        pending_steps = [s for s in strategic_plan if s["status"] == "PENDING"]

        # Compter étapes bloquées > 20 tours
        long_pending = 0
        longest_id = None
        max_pending_turns = 0

        for step in pending_steps:
            created_turn = step.get("created_turn", 0)
            pending_turns = current_turn - created_turn
            if pending_turns > 20:
                long_pending += 1
            if pending_turns > max_pending_turns:
                max_pending_turns = pending_turns
                longest_id = step["step_id"]

        # Dernière progression
        completed = [s for s in strategic_plan if s["status"] == "COMPLETED"]
        last_progress = max([s.get("completed_turn", 0) for s in completed], default=0)

        # Score de drift
        turns_since_progress = current_turn - last_progress

        if turns_since_progress > 40:
            drift = "CRITICAL"
        elif turns_since_progress > 20:
            drift = "HIGH"
        elif long_pending > 2:
            drift = "MEDIUM"
        else:
            drift = "LOW"

        health = {
            "steps_pending_more_than_20_turns": long_pending,
            "longest_pending_step_id": longest_id,
            "last_progress_turn": last_progress,
            "drift_score": drift
        }

        # Sauvegarder dans le blackboard
        self.blackboard["plan_health"] = health
        return health

    def should_compress(self) -> bool:
        """Vérifie si la compression est nécessaire."""
        token_estimate = self.blackboard["current_state"]["token_count_estimate"]
        return token_estimate > self.compression_threshold

    def compress_history(self):
        """Compression mémorielle (placeholder - à implémenter avec un modèle)."""
        # TODO: Implémenter avec un appel à Opus/Gemini-Pro
        # Pour l'instant, simple troncature
        if len(self.blackboard["recent_history"]) > 50:
            # Résumer les 30 premiers
            old_history = self.blackboard["recent_history"][:30]
            summary = f"Résumé des {len(old_history)} premiers tours (placeholder)"

            self.blackboard["compressed_history_summary"] = summary
            self.blackboard["recent_history"] = self.blackboard["recent_history"][30:]

            print(f"[NEXUS] Compression effectuée: {len(old_history)} tours résumés")
