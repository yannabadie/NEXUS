"""
NEXUS V5.0 - Claude Driver
Driver pour Claude CLI.
"""
import subprocess
import time
from pathlib import Path
from typing import Dict, Any
from core.drivers.base_driver import BaseDriver
from core.config import Config


class ClaudeDriver(BaseDriver):
    """Driver pour Claude CLI."""

    def __init__(self, config: Config, workspace_path: Path):
        super().__init__(workspace_path, config.cli_timeout_seconds)
        self.cli_path = config.claude_cli_path
        self.session_id = config.claude_session_id

    def invoke(self, context: str) -> Dict[str, Any]:
        """
        Invoque Claude via CLI avec syntaxe optimale (Nov 2025).

        Args:
            context: Contexte markdown

        Returns:
            Réponse parsée (protocole Synapse V5.0)
        """
        import json

        # Écrire le contexte
        self.write_context(context)

        # Chemins absolus
        context_file = self.workspace_path / "_IO_BUFFER" / "context_in.md"
        output_file = self.workspace_path / "_IO_BUFFER" / "action_out.json"

        # SYNTAXE OPTIMALE CLAUDE CODE CLI (Nov 2025) :
        # - Flag -p pour print mode (non-interactif)
        # - @syntax pour lire fichier automatiquement
        # - --output-format json pour sortie JSON structurée
        # - --max-turns 1 pour limiter à un tour (non-interactif)
        # - --append-system-prompt pour renforcer CFL sans casser outils
        # - --resume <session-id> pour continuité (optionnel)

        command_parts = [
            f'"{self.cli_path}"'
        ]

        # Reprendre session si disponible
        if self.session_id:
            command_parts.append(f'--resume "{self.session_id}"')

        # Lire contexte via @syntax + prompt + flags
        command_parts.extend([
            f'@"{context_file.absolute()}"',
            '-p "Réponds STRICTEMENT en JSON (Protocole Synapse V5.0)."',
            '--output-format json',
            '--max-turns 1',
            '--append-system-prompt "CRITICAL: After TOOL_USE, always provide post_action_review. Use last_tool_result.json as truth."'
        ])

        # Redirection vers fichier de sortie
        command_parts.append(f'> "{output_file.absolute()}"')

        # Joindre la commande complète
        command = ' '.join(command_parts)

        # Exécuter
        try:
            result = subprocess.run(
                command,
                cwd=str(self.workspace_path),
                shell=True,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                encoding="utf-8",
                errors="replace"
            )

            if result.returncode != 0:
                raise Exception(f"Claude CLI error: {result.stderr}")

            # Attendre que le fichier soit écrit (Windows I/O lag)
            time.sleep(0.5)

            # Lire et parser le wrapper Claude Code
            return self._parse_claude_wrapper(output_file)

        except subprocess.TimeoutExpired:
            raise Exception(f"Claude CLI timeout après {self.timeout}s")

    def _parse_claude_wrapper(self, output_file: Path) -> Dict[str, Any]:
        """
        Parse le wrapper JSON retourné par Claude Code CLI.

        Claude Code avec --output-format json retourne:
        {
          "type": "result",
          "result": "contenu réel ici (peut être JSON string)",
          "cost_usd": 0.042,
          "duration_ms": 5558,
          ...
        }

        Args:
            output_file: Fichier action_out.json

        Returns:
            Protocole Synapse V5.0 parsé
        """
        import json

        with self.lock:
            wrapper = json.loads(output_file.read_text(encoding="utf-8"))

            # Vérifier le wrapper Claude Code
            if wrapper.get('type') != 'result':
                raise Exception(f"Format inattendu: type={wrapper.get('type')}")

            # Vérifier erreurs
            if wrapper.get('is_error', False):
                raise Exception(f"Claude Code error: {wrapper.get('result', 'Unknown error')}")

            # Extraire le contenu réel
            result_content = wrapper.get('result', '')

            # Le result peut être:
            # 1. Une string JSON (protocole Synapse) -> parser
            # 2. Du texte simple -> erreur de protocole

            # Tentative de parsing JSON
            try:
                synapse_message = json.loads(result_content)

                # Valider que c'est bien le protocole Synapse
                if not isinstance(synapse_message, dict):
                    raise ValueError("Result n'est pas un objet JSON")

                # Vérifier présence champs obligatoires
                required_fields = ['sender', 'action_type', 'status']
                missing = [f for f in required_fields if f not in synapse_message]

                if missing:
                    raise ValueError(f"Champs Synapse manquants: {missing}")

                return synapse_message

            except (json.JSONDecodeError, ValueError) as e:
                # Le result n'est pas du JSON valide ou n'est pas du protocole Synapse
                raise Exception(
                    f"Claude n'a pas répondu en protocole Synapse V5.0. "
                    f"Erreur: {e}. "
                    f"Contenu reçu (premiers 500 chars): {result_content[:500]}"
                )
