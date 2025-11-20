"""
NEXUS V5.0 - Mode Handlers
Handlers pour modes InProjectImprovement et CoreEvolution.
"""
from pathlib import Path
from typing import Dict, Any


class ModeHandler:
    """Base handler pour modes spéciaux."""

    def __init__(self, workspace_path: Path):
        self.workspace_path = workspace_path

    def get_mode_instructions(self) -> str:
        """Retourne les instructions spécifiques au mode."""
        raise NotImplementedError()

    def validate_permissions(self, tool_name: str, arguments: Dict) -> bool:
        """Valide les permissions pour l'opération demandée."""
        raise NotImplementedError()


class InProjectImprovementHandler(ModeHandler):
    """
    Mode InProjectImprovement - Auto-amélioration de NEXUS.

    Focus: Analyser session.log, proposer new_capability basé sur échecs répétés.
    Déclenchement: drift_score == CRITICAL ou demande explicite.
    """

    def get_mode_instructions(self) -> str:
        """Instructions pour mode InProjectImprovement."""
        return """
# MODE: InProjectImprovement (Auto-amélioration)

## OBJECTIF
Analyser les logs de session récents pour identifier des patterns d'échec et proposer des améliorations.

## TÂCHES
1. Lire `workspace/logs/session.log`
2. Identifier les échecs répétés, erreurs fréquentes
3. Proposer `new_capability` pour résoudre ces problèmes
4. Tester la nouvelle capability (si possible)

## PERMISSIONS
- Lecture: `workspace/logs/`
- Écriture: `workspace/` uniquement
- Interdiction: Modification code core NEXUS

## OUTPUT ATTENDU
Proposer au moins une `new_capability` dans ton message avec:
- `name`: Nom descriptif
- `description`: Problème résolu
- `invocation_method`: Comment l'invoquer
- `agent_owner`: Gemini ou Claude

## EXEMPLE
```json
{
  "new_capability": {
    "name": "retry_on_timeout",
    "description": "Réessayer automatiquement les commandes qui timeout",
    "invocation_method": "Ajouter retry_count=3 dans tool_use",
    "agent_owner": "Claude"
  }
}
```

**Important**: Ce mode est automatique. Analyse, propose, puis status=FINISHED.
"""

    def validate_permissions(self, tool_name: str, arguments: Dict) -> bool:
        """
        Valide les permissions InProjectImprovement.

        Autorisé:
        - read: workspace/logs/
        - write: workspace/ (mais pas core/)

        Interdit:
        - Modification core NEXUS
        """
        if tool_name == "read":
            file_path = arguments.get("file_path", "")
            # Autoriser lecture logs
            return "workspace/logs" in file_path or "workspace" in file_path

        elif tool_name == "write":
            file_path = arguments.get("file_path", "")
            # Interdire modification core
            if "core/" in file_path or "../" in file_path:
                return False
            # Autoriser workspace uniquement
            return "workspace/" in file_path

        elif tool_name in ["bash", "git"]:
            # Interdire commandes dangereuses
            return False

        elif tool_name in ["list_dir", "edit"]:
            # Autoriser lecture/modification limitée
            file_path = arguments.get("file_path", "")
            return "workspace/" in file_path and "core/" not in file_path

        return False


class CoreEvolutionHandler(ModeHandler):
    """
    Mode CoreEvolution - Réécriture du code NEXUS.

    Focus: Proposer modifications au code NEXUS lui-même.
    Sécurité: Modifications dans EVOLUTION_VNEXT/ seulement.
    Human-in-the-Loop: OBLIGATOIRE avant application.
    """

    def __init__(self, workspace_path: Path):
        super().__init__(workspace_path)
        self.evolution_sandbox = workspace_path / "EVOLUTION_VNEXT"
        self.evolution_sandbox.mkdir(exist_ok=True)

    def get_mode_instructions(self) -> str:
        """Instructions pour mode CoreEvolution."""
        return f"""
# MODE: CoreEvolution (Évolution du Core NEXUS)

## OBJECTIF
Proposer des modifications au code NEXUS lui-même pour améliorer architecture ou fonctionnalités.

## SANDBOX
**CRITIQUE**: Toutes les modifications DOIVENT être dans:
`{self.evolution_sandbox.absolute()}/`

## WORKFLOW
1. Analyser le code NEXUS actuel (core/, prompts/, etc.)
2. Identifier améliorations architecturales
3. Créer fichiers modifiés dans `EVOLUTION_VNEXT/`
4. Proposer `request_core_evolution = true`
5. **ATTENDRE validation humaine** avant application

## PERMISSIONS
- Lecture: Tout le projet NEXUS
- Écriture: `EVOLUTION_VNEXT/` UNIQUEMENT
- Interdiction: Modification directe de `core/`, `prompts/`, `nexus.py`

## OUTPUT ATTENDU
1. Fichiers modifiés dans `EVOLUTION_VNEXT/`
2. Fichier `EVOLUTION_VNEXT/PROPOSAL.md` avec:
   - Problème identifié
   - Solution proposée
   - Fichiers affectés
   - Plan de test
3. `request_core_evolution = true` dans message

## SÉCURITÉ
⚠️ **Human-in-the-Loop OBLIGATOIRE**
L'utilisateur devra:
1. Reviewer les modifications dans `EVOLUTION_VNEXT/`
2. Approuver explicitement
3. Appliquer manuellement (ou via script fourni)

**Important**: Ce mode nécessite expertise. Analyser avant proposer.
"""

    def validate_permissions(self, tool_name: str, arguments: Dict) -> bool:
        """
        Valide les permissions CoreEvolution.

        Autorisé:
        - read: Tout le projet
        - write: EVOLUTION_VNEXT/ uniquement

        Interdit:
        - Modification directe core NEXUS
        """
        if tool_name == "read" or tool_name == "list_dir":
            # Autoriser lecture complète
            return True

        elif tool_name == "write" or tool_name == "edit":
            file_path = arguments.get("file_path", "")
            # UNIQUEMENT dans EVOLUTION_VNEXT/
            return "EVOLUTION_VNEXT" in file_path

        elif tool_name == "bash":
            command = arguments.get("command", "")
            # Autoriser commandes de lecture uniquement
            safe_commands = ["ls", "cat", "grep", "find", "pwd", "echo"]
            return any(command.startswith(cmd) for cmd in safe_commands)

        elif tool_name == "git":
            # Interdire git operations en mode evolution
            return False

        return False


def get_mode_handler(mode: str, workspace_path: Path) -> ModeHandler:
    """Factory pour créer le handler approprié."""
    handlers = {
        "InProjectImprovement": InProjectImprovementHandler,
        "CoreEvolution": CoreEvolutionHandler
    }

    handler_class = handlers.get(mode)
    if handler_class:
        return handler_class(workspace_path)

    # Mode Normal ou inconnu = pas de handler spécial
    return None
