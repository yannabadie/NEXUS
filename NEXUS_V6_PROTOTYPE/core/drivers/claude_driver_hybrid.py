"""
Claude Hybrid Driver V6 - CORRECTIF CRITIQUE

Problème V5: Claude CLI forçé à répondre en JSON → échec 90% du temps → boucles infinies

Solution V6: Mode Hybride
- Claude répond en TEXTE NATUREL
- Utilise des balises XML pour les outils: <tool_use name="read">...</tool_use>
- Parser intelligent extrait content + tool_use
- Plus de JSON forcé = plus de boucles infinies

Example Input Prompt:
    "Lis le fichier auth.py et identifie le bug"

Example Claude Response:
    "Je vais d'abord lire le fichier pour comprendre la structure.

    <tool_use name="read">
    {
      "file_path": "src/auth.py"
    }
    </tool_use>

    Ensuite j'analyserai le code pour trouver le bug."

Parser Output:
    {
        "sender": "Claude",
        "action_type": "TOOL_USE",
        "content": "Je vais d'abord lire... Ensuite j'analyserai...",
        "tool_use": {
            "tool_name": "read",
            "arguments": {"file_path": "src/auth.py"}
        }
    }
"""
import re
import json
import subprocess
from pathlib import Path
from typing import Dict, Optional


class ClaudeDriverHybrid:
    """
    Driver hybride pour Claude CLI

    Mode: Natural Language + XML Tool Blocks
    NO JSON enforcement - Claude parle naturellement
    """

    def __init__(self, config, workspace_path: Path):
        self.cli_path = config.claude_cli_path
        self.workspace_path = workspace_path
        self.io_buffer = workspace_path / "_IO_BUFFER"
        self.timeout = config.timeout if hasattr(config, 'timeout') else 120

    def invoke(self, context: str) -> Dict:
        """
        Invoke Claude CLI avec contexte markdown

        Args:
            context: Contexte markdown avec system prompt

        Returns:
            Dict structuré NEXUS (content, action_type, tool_use, etc.)

        Raises:
            RuntimeError: Si Claude CLI échoue
            TimeoutError: Si timeout dépassé
        """
        # Write context to file
        context_file = self.io_buffer / "claude_context_in.md"
        context_file.write_text(context, encoding="utf-8")

        # Invoke Claude (mode naturel, PAS de flag JSON!)
        command = f'"{self.cli_path}" -p @"{context_file}"'

        try:
            result = subprocess.run(
                command,
                cwd=str(self.workspace_path),
                shell=True,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                encoding='utf-8',
                errors='replace'
            )

            if result.returncode != 0:
                raise RuntimeError(f"Claude CLI failed: {result.stderr}")

            raw_response = result.stdout

            # Parse hybrid response
            return self._parse_hybrid_response(raw_response)

        except subprocess.TimeoutExpired:
            raise TimeoutError(f"Claude CLI timed out after {self.timeout}s")

    def _parse_hybrid_response(self, raw_text: str) -> Dict:
        """
        Parse Claude's natural language response avec balises XML

        Extrait:
        - content: Tout le texte HORS balises XML
        - tool_use: Contenu des balises <tool_use>
        - action_type: TOOL_USE si balise trouvée, sinon TALK

        Example Input:
            "Je vais lire le fichier.

            <tool_use name="read">
            {"file_path": "auth.py"}
            </tool_use>

            Puis je chercherai le bug."

        Example Output:
            {
                "sender": "Claude",
                "action_type": "TOOL_USE",
                "content": "Je vais lire le fichier. Puis je chercherai le bug.",
                "tool_use": {
                    "tool_name": "read",
                    "arguments": {"file_path": "auth.py"},
                    "expected_outcome": "Execute read successfully"
                }
            }
        """
        # Extract tool use blocks (XML pattern)
        tool_pattern = r'<tool_use\s+name="(\w+)">(.*?)</tool_use>'
        tool_matches = list(re.finditer(tool_pattern, raw_text, re.DOTALL))

        # Extract content (everything OUTSIDE tool blocks)
        content = raw_text
        for match in tool_matches:
            content = content.replace(match.group(0), '')
        content = content.strip()

        # Parse tool use if present
        tool_use = None
        action_type = "TALK"

        if tool_matches:
            # Use first tool block found
            match = tool_matches[0]
            tool_name = match.group(1)
            tool_args_raw = match.group(2).strip()

            # Parse arguments (JSON or key=value)
            try:
                arguments = json.loads(tool_args_raw)
            except json.JSONDecodeError:
                # Fallback: parse key=value format
                arguments = self._parse_keyvalue_args(tool_args_raw)

            tool_use = {
                "tool_name": tool_name,
                "arguments": arguments,
                "expected_outcome": f"Execute {tool_name} successfully"
            }
            action_type = "TOOL_USE"

        # Detect status from content
        status = "CONTINUE"
        finish_keywords = ["task complete", "finished", "done", "terminé", "fini"]
        if any(keyword in content.lower() for keyword in finish_keywords):
            status = "FINISHED"

        # Detect next_agent from content
        next_agent = "Claude"  # By default, stay with Claude
        if "gemini" in content.lower() and action_type == "TALK":
            next_agent = "Gemini"  # Asking Gemini's opinion

        # Construct structured message
        return {
            "sender": "Claude",
            "action_type": action_type,
            "content": content,
            "tool_use": tool_use,
            "status": status,
            "next_agent": next_agent
        }

    def _parse_keyvalue_args(self, args_text: str) -> Dict:
        """
        Parse arguments au format key=value (fallback si pas JSON)

        Example:
            file_path=src/auth.py
            line_number=42

        Returns:
            {"file_path": "src/auth.py", "line_number": "42"}
        """
        args = {}
        for line in args_text.split('\n'):
            line = line.strip()
            if '=' in line:
                key, value = line.split('=', 1)
                args[key.strip()] = value.strip()
        return args

    def invoke_with_retry(self, context: str, max_retries: int = 3) -> Dict:
        """
        Invoke avec retry sur erreur

        Si Claude échoue (timeout, subprocess error), retry avec:
        - Exponential backoff
        - Context augmenté avec reminder si parse error

        Args:
            context: Contexte markdown
            max_retries: Nombre de tentatives max

        Returns:
            Dict structuré

        Raises:
            RuntimeError: Si toutes les tentatives échouent
        """
        import time

        last_error = None

        for attempt in range(max_retries):
            try:
                return self.invoke(context)

            except Exception as e:
                last_error = e

                if attempt < max_retries - 1:
                    # Wait before retry (exponential backoff)
                    wait_time = 2 ** attempt
                    time.sleep(wait_time)

                    # If parse error, inject stronger reminder
                    if "parse" in str(e).lower() or "json" in str(e).lower():
                        context += "\n\n🚨 IMPORTANT: Use <tool_use> XML tags for tools."

        # All retries failed
        raise RuntimeError(f"Claude invocation failed after {max_retries} attempts: {last_error}")
