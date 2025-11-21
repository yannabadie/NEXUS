"""
Gemini Driver V6 - JSON Strict Mode

Gemini reste en mode JSON strict (contrairement à Claude qui est hybride)
"""
import subprocess
import json
from pathlib import Path
from typing import Dict


class GeminiDriverV6:
    """
    Driver pour Gemini CLI - Mode JSON strict
    """

    def __init__(self, config, workspace_path: Path):
        self.cli_path = config.gemini_cli_path
        self.workspace_path = workspace_path
        self.io_buffer = workspace_path / "_IO_BUFFER"
        self.timeout = config.timeout if hasattr(config, 'timeout') else 120

    def invoke(self, context: str) -> Dict:
        """
        Invoke Gemini CLI avec contexte markdown

        Args:
            context: Contexte markdown avec system prompt

        Returns:
            Dict structuré NEXUS (JSON parsé)

        Raises:
            RuntimeError: Si Gemini CLI échoue
            TimeoutError: Si timeout dépassé
        """
        # Write context to file
        context_file = self.io_buffer / "gemini_context_in.md"
        context_file.write_text(context, encoding="utf-8")

        output_file = self.io_buffer / "gemini_output.json"

        # Invoke Gemini with JSON output
        command = f'"{self.cli_path}" -p @"{context_file}" -o json > "{output_file}"'

        try:
            result = subprocess.run(
                command,
                cwd=str(self.workspace_path),
                shell=True,
                capture_output=True,
                text=True,
                timeout=self.timeout
            )

            if result.returncode != 0:
                raise RuntimeError(f"Gemini CLI failed: {result.stderr}")

            # Read and parse JSON output
            output_text = output_file.read_text(encoding="utf-8")

            try:
                return json.loads(output_text)
            except json.JSONDecodeError as e:
                # Try to extract JSON from text
                return self._extract_json(output_text)

        except subprocess.TimeoutExpired:
            raise TimeoutError(f"Gemini CLI timed out after {self.timeout}s")

    def _extract_json(self, text: str) -> Dict:
        """
        Extract JSON from text (fallback if direct parse fails)

        Args:
            text: Raw text that might contain JSON

        Returns:
            Dict

        Raises:
            ValueError: If no JSON found
        """
        import re

        # Try to find JSON in code blocks
        json_block_pattern = r'```json\s*(.*?)\s*```'
        matches = re.findall(json_block_pattern, text, re.DOTALL)

        if matches:
            try:
                return json.loads(matches[0])
            except json.JSONDecodeError:
                pass

        # Try to find JSON object directly
        json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
        matches = re.findall(json_pattern, text, re.DOTALL)

        if matches:
            # Try each match
            for match in matches:
                try:
                    return json.loads(match)
                except json.JSONDecodeError:
                    continue

        # No JSON found
        raise ValueError(f"Could not extract JSON from Gemini response: {text[:200]}")
