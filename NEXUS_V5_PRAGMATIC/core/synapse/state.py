"""
NEXUS V5.0 - State Module
Gestion des capabilities, stalemate counter, état CFL.
"""
import json
from pathlib import Path
from typing import Dict, List, Any


class StateManager:
    """Gestionnaire d'état pour les capabilities et la détection de stagnation."""

    def __init__(self, workspace_path: Path, max_stalemate: int = 5):
        self.workspace_path = workspace_path
        self.max_stalemate = max_stalemate
        self.capabilities_path = workspace_path / ".nexus" / "capabilities.json"
        self.capabilities = self._load_capabilities()
        self.stalemate_counter = 0
        self.last_action_signature = ""

    def _load_capabilities(self) -> Dict:
        """Charge le registre des capabilities."""
        if self.capabilities_path.exists():
            return json.loads(self.capabilities_path.read_text(encoding="utf-8"))
        return self._create_default_capabilities()

    def _create_default_capabilities(self) -> Dict:
        """Crée le registre initial des capabilities."""
        return {
            "Gemini": [
                {
                    "name": "Strategic Planning",
                    "description": "Élaboration de plans stratégiques multi-étapes",
                    "invocation_method": "Utilise strategic_plan_update dans ton message"
                }
            ],
            "Claude": [
                {
                    "name": "bash",
                    "description": "Exécuter commandes shell via Nexus Tool Executor",
                    "invocation_method": "tool_use avec tool_name='bash' et expected_outcome obligatoire"
                },
                {
                    "name": "edit",
                    "description": "Éditer fichiers (remplacement de texte)",
                    "invocation_method": "tool_use avec tool_name='edit'"
                },
                {
                    "name": "git",
                    "description": "Opérations git (add, commit, status, diff, log)",
                    "invocation_method": "tool_use avec tool_name='git'"
                },
                {
                    "name": "read",
                    "description": "Lire fichiers",
                    "invocation_method": "tool_use avec tool_name='read'"
                },
                {
                    "name": "write",
                    "description": "Créer/écraser fichiers",
                    "invocation_method": "tool_use avec tool_name='write'"
                },
                {
                    "name": "list_dir",
                    "description": "Lister répertoire",
                    "invocation_method": "tool_use avec tool_name='list_dir'"
                }
            ]
        }

    def save_capabilities(self):
        """Sauvegarde le registre des capabilities."""
        self.capabilities_path.parent.mkdir(parents=True, exist_ok=True)
        self.capabilities_path.write_text(
            json.dumps(self.capabilities, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )

    def get_capabilities(self) -> Dict:
        """Retourne les capabilities actuelles."""
        return self.capabilities

    def register_capability(self, new_cap: Dict):
        """Enregistre une nouvelle capability."""
        agent_owner = new_cap.get("agent_owner", "Claude")

        if agent_owner not in self.capabilities:
            self.capabilities[agent_owner] = []

        # Vérifier si la capability existe déjà
        for cap in self.capabilities[agent_owner]:
            if cap["name"] == new_cap["name"]:
                # Mettre à jour
                cap.update(new_cap)
                self.save_capabilities()
                return

        # Ajouter nouvelle
        self.capabilities[agent_owner].append({
            "name": new_cap["name"],
            "description": new_cap["description"],
            "invocation_method": new_cap["invocation_method"]
        })
        self.save_capabilities()

    def increment_stalemate_counter(self):
        """Incrémente le compteur de stagnation."""
        self.stalemate_counter += 1

    def reset_stalemate_counter(self):
        """Réinitialise le compteur de stagnation."""
        self.stalemate_counter = 0

    def get_stalemate_counter(self) -> int:
        """Retourne le compteur actuel."""
        return self.stalemate_counter

    def is_stalemate(self) -> bool:
        """Vérifie si le seuil de stagnation est atteint."""
        return self.stalemate_counter >= self.max_stalemate

    def update_action_signature(self, message: Dict) -> bool:
        """
        Met à jour la signature d'action et détecte les répétitions.

        Returns:
            True si l'action est identique à la précédente
        """
        action_type = message.get("action_type", "")

        if action_type == "TOOL_USE" and "tool_use" in message:
            tool = message["tool_use"]
            tool_name = tool.get("tool_name", "")
            # Prendre le premier argument comme signature
            args = tool.get("arguments", {})
            primary_arg = next(iter(args.values()), "") if args else ""
            signature = f"tool_use:{tool_name}:{str(primary_arg)[:50]}"
        else:
            signature = f"{action_type}:generic"

        is_repeat = (signature == self.last_action_signature)
        self.last_action_signature = signature

        return is_repeat
