"""
NEXUS V5.0 - Gemini Driver
Driver pour Gemini CLI.
"""
import subprocess
import time
import json
import re
from pathlib import Path
from typing import Dict, Any
from core.drivers.base_driver import BaseDriver
from core.config import Config


class GeminiDriver(BaseDriver):
    """Driver pour Gemini CLI."""

    def __init__(self, config: Config, workspace_path: Path):
        super().__init__(workspace_path, config.cli_timeout_seconds)
        self.cli_path = config.gemini_cli_path

    def invoke(self, context: str) -> Dict[str, Any]:
        """
        Invoque Gemini via CLI avec syntaxe correcte (Nov 2025).

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

        # SYNTAXE CORRECTE GEMINI CLI (Nov 2025) :
        # IMPORTANT: Cannot use both @file (positional) and -p flag together
        # CRITICAL: Must specify model with -m flag to use Gemini 3 Pro!
        # VERIFIED: Correct model name is "gemini-3-pro-preview"
        #
        # Using positional syntax: gemini -m model @file "prompt" -o json
        command = (
            f'"{self.cli_path}" '
            f'-m gemini-3-pro-preview '  # FORCE Gemini 3 Pro Preview (VERIFIED)
            f'@"{context_file.absolute()}" '
            f'"Réponds STRICTEMENT en JSON (Protocole Synapse V5.0)." '
            f'-o json '
            f'> "{output_file.absolute()}"'
        )

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
                raise Exception(f"Gemini CLI error: {result.stderr}")

            # Attendre que le fichier soit écrit (Windows I/O lag)
            time.sleep(0.5)

            # Lire la réponse JSON de Gemini CLI
            # Format: {"response": "```json\n{...}\n```", "stats": {...}}
            raw_response = self.read_response()

            # Extraire le vrai JSON depuis le wrapper Gemini CLI
            if "response" in raw_response:
                response_text = raw_response["response"]

                # Extraire JSON du markdown code block
                json_match = re.search(r'```json\s*\n(.*?)\n```', response_text, re.DOTALL)
                if json_match:
                    json_str = json_match.group(1)
                    return json.loads(json_str)
                else:
                    # Fallback: essayer de parser directement
                    return json.loads(response_text)
            else:
                # Format inattendu, retourner tel quel
                return raw_response

        except subprocess.TimeoutExpired:
            raise Exception(f"Gemini CLI timeout après {self.timeout}s")
