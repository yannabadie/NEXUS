"""
NEXUS V5.0 - Tool Executor
Exécution centralisée et sécurisée de tous les outils.
"""
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any
from core.synapse.protocol import ToolUse, ToolResult
from core.tools import bash, edit, git, read, write


class ToolExecutor:
    """Exécuteur centralisé d'outils avec capture objective des résultats."""

    def __init__(self, workspace_path: Path):
        self.workspace_path = workspace_path
        self.tools = {
            "bash": bash.execute,
            "edit": edit.execute,
            "git": git.execute,
            "read": read.execute,
            "write": write.execute,
            "list_dir": read.list_directory,
        }

    def execute(self, tool_request: ToolUse) -> ToolResult:
        """
        Exécute un outil et retourne le résultat structuré.

        Args:
            tool_request: Requête d'outil validée

        Returns:
            ToolResult avec stdout, stderr, returncode, etc.
        """
        tool_name = tool_request.tool_name
        arguments = tool_request.arguments

        if tool_name not in self.tools:
            return ToolResult(
                tool_name=tool_name,
                status="ERROR",
                stdout="",
                stderr=f"Tool '{tool_name}' not found",
                returncode=-1,
                timestamp=datetime.utcnow().isoformat()
            )

        try:
            # Exécuter l'outil avec les arguments
            result = self.tools[tool_name](arguments, self.workspace_path)

            # Sauvegarder dans last_tool_result.json
            self._save_last_result(result)

            return result

        except Exception as e:
            return ToolResult(
                tool_name=tool_name,
                status="ERROR",
                stdout="",
                stderr=str(e),
                returncode=-1,
                timestamp=datetime.utcnow().isoformat()
            )

    def _save_last_result(self, result: ToolResult):
        """Sauvegarde le dernier résultat pour injection dans le contexte."""
        result_path = self.workspace_path / "_IO_BUFFER" / "last_tool_result.json"
        with open(result_path, "w", encoding="utf-8") as f:
            json.dump(result.model_dump(), f, indent=2, ensure_ascii=False)
