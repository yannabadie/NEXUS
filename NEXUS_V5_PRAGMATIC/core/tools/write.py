"""
NEXUS V5.0 - Write Tool
Écriture sécurisée de fichiers dans le workspace.
"""
from pathlib import Path
from datetime import datetime
from core.synapse.protocol import ToolResult


def execute(arguments: dict, workspace_path: Path) -> ToolResult:
    """
    Écrit ou crée un fichier dans le workspace.

    Args:
        arguments: {"file_path": "chemin", "content": "contenu"}
        workspace_path: Chemin du workspace (sandbox)

    Returns:
        ToolResult avec confirmation
    """
    file_path_str = arguments.get("file_path", "")
    content = arguments.get("content", "")

    if not file_path_str:
        return ToolResult(
            tool_name="write",
            status="ERROR",
            stdout="",
            stderr="Missing 'file_path' argument",
            returncode=-1,
            timestamp=datetime.utcnow().isoformat()
        )

    try:
        # Construire le chemin complet
        full_path = (workspace_path / file_path_str).resolve()

        # Sécurité
        if not str(full_path).startswith(str(workspace_path.resolve())):
            return ToolResult(
                tool_name="write",
                status="ERROR",
                stdout="",
                stderr=f"Access denied: file outside workspace: {file_path_str}",
                returncode=-1,
                timestamp=datetime.utcnow().isoformat()
            )

        # Créer les répertoires parents si nécessaire
        full_path.parent.mkdir(parents=True, exist_ok=True)

        # Écrire le fichier
        full_path.write_text(content, encoding="utf-8")

        return ToolResult(
            tool_name="write",
            status="SUCCESS",
            stdout=f"File written: {file_path_str} ({len(content)} bytes)",
            stderr="",
            returncode=0,
            files_changed=[file_path_str],
            timestamp=datetime.utcnow().isoformat()
        )

    except Exception as e:
        return ToolResult(
            tool_name="write",
            status="ERROR",
            stdout="",
            stderr=str(e),
            returncode=-1,
            timestamp=datetime.utcnow().isoformat()
        )
