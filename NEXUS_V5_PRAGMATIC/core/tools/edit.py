"""
NEXUS V5.0 - Edit Tool
Édition sécurisée de fichiers (remplacement de texte).
"""
from pathlib import Path
from datetime import datetime
from core.synapse.protocol import ToolResult


def execute(arguments: dict, workspace_path: Path) -> ToolResult:
    """
    Édite un fichier en remplaçant old_string par new_string.

    Args:
        arguments: {
            "file_path": "chemin",
            "old_string": "texte à remplacer",
            "new_string": "nouveau texte"
        }
        workspace_path: Chemin du workspace

    Returns:
        ToolResult avec confirmation
    """
    file_path_str = arguments.get("file_path", "")
    old_string = arguments.get("old_string", "")
    new_string = arguments.get("new_string", "")

    if not all([file_path_str, old_string]):
        return ToolResult(
            tool_name="edit",
            status="ERROR",
            stdout="",
            stderr="Missing required arguments: file_path, old_string",
            returncode=-1,
            timestamp=datetime.utcnow().isoformat()
        )

    try:
        full_path = (workspace_path / file_path_str).resolve()

        # Sécurité
        if not str(full_path).startswith(str(workspace_path.resolve())):
            return ToolResult(
                tool_name="edit",
                status="ERROR",
                stdout="",
                stderr=f"Access denied: file outside workspace: {file_path_str}",
                returncode=-1,
                timestamp=datetime.utcnow().isoformat()
            )

        # Lire le fichier
        content = full_path.read_text(encoding="utf-8")

        # Vérifier que old_string existe
        if old_string not in content:
            return ToolResult(
                tool_name="edit",
                status="FAILURE",
                stdout="",
                stderr=f"String not found in file: '{old_string[:50]}...'",
                returncode=1,
                timestamp=datetime.utcnow().isoformat()
            )

        # Compter les occurrences
        count = content.count(old_string)

        # Remplacer
        new_content = content.replace(old_string, new_string)

        # Écrire
        full_path.write_text(new_content, encoding="utf-8")

        return ToolResult(
            tool_name="edit",
            status="SUCCESS",
            stdout=f"Replaced {count} occurrence(s) in {file_path_str}",
            stderr="",
            returncode=0,
            files_changed=[file_path_str],
            timestamp=datetime.utcnow().isoformat()
        )

    except FileNotFoundError:
        return ToolResult(
            tool_name="edit",
            status="FAILURE",
            stdout="",
            stderr=f"File not found: {file_path_str}",
            returncode=1,
            timestamp=datetime.utcnow().isoformat()
        )

    except Exception as e:
        return ToolResult(
            tool_name="edit",
            status="ERROR",
            stdout="",
            stderr=str(e),
            returncode=-1,
            timestamp=datetime.utcnow().isoformat()
        )
