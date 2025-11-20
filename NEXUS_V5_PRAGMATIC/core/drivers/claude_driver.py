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
            Réponse parsée
        """
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

            # Lire la réponse JSON
            return self.read_response()

        except subprocess.TimeoutExpired:
            raise Exception(f"Claude CLI timeout après {self.timeout}s")
