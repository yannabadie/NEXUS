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

        # SYNTAXE RÉELLE CLAUDE CODE CLI (Nov 2025) :
        # VERIFIED: Claude CLI only supports basic flags
        # - -p for print mode (non-interactive)
        # - @file to read file
        # - --resume <session-id> for session continuity (optional)
        # NO FLAGS FOR: --output-format, --max-turns, --append-system-prompt (these don't exist!)
        #
        # The prompt system file MUST enforce JSON output format.

        command_parts = [
            f'"{self.cli_path}"',
            '-p'  # Print mode (non-interactive)
        ]

        # Resume session if available
        if self.session_id:
            command_parts.append(f'--resume "{self.session_id}"')

        # Read context file using @syntax
        command_parts.append(f'@"{context_file.absolute()}"')

        # Redirect to output file
        command_parts.append(f'> "{output_file.absolute()}"')

        # Join command
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
        Parse la réponse de Claude CLI.

        Avec -p mode, Claude CLI retourne le texte brut (pas de wrapper JSON).
        Le texte doit être du JSON Synapse V5.0 directement.

        Args:
            output_file: Fichier action_out.json

        Returns:
            Protocole Synapse V5.0 parsé
        """
        import json
        import re

        with self.lock:
            raw_content = output_file.read_text(encoding="utf-8").strip()

            # Claude peut enrober le JSON dans des markdown code blocks
            # Extraire le JSON s'il est dans ```json ... ```
            json_match = re.search(r'```json\s*\n(.*?)\n```', raw_content, re.DOTALL)
            if json_match:
                json_content = json_match.group(1)
            else:
                # Pas de code block, assume JSON direct
                json_content = raw_content

            # Tentative de parsing JSON
            try:
                synapse_message = json.loads(json_content)

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
                    f"Contenu reçu (premiers 500 chars): {raw_content[:500]}"
                )
