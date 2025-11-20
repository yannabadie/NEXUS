"""
NEXUS V5.0 - Read Tool
Lecture sécurisée de fichiers dans le workspace.
"""
from pathlib import Path
from datetime import datetime
from core.synapse.protocol import ToolResult


def execute(arguments: dict, workspace_path: Path) -> ToolResult:
    """
    Lit un fichier dans le workspace.

    Args:
        arguments: {"file_path": "chemin relatif au workspace"}
        workspace_path: Chemin du workspace (sandbox)

    Returns:
        ToolResult avec contenu du fichier
    """
    file_path_str = arguments.get("file_path", "")

    if not file_path_str:
        return ToolResult(
            tool_name="read",
            status="ERROR",
            stdout="",
            stderr="Missing 'file_path' argument",
            returncode=-1,
            timestamp=datetime.utcnow().isoformat()
        )

    try:
        # Construire le chemin complet et vérifier qu'il est dans le workspace
        full_path = (workspace_path / file_path_str).resolve()

        # Sécurité : vérifier que le fichier est bien dans le workspace
        if not str(full_path).startswith(str(workspace_path.resolve())):
            return ToolResult(
                tool_name="read",
                status="ERROR",
                stdout="",
                stderr=f"Access denied: file outside workspace: {file_path_str}",
                returncode=-1,
                timestamp=datetime.utcnow().isoformat()
            )

        # Lire le fichier
        content = full_path.read_text(encoding="utf-8")

        return ToolResult(
            tool_name="read",
            status="SUCCESS",
            stdout=content,
            stderr="",
            returncode=0,
            timestamp=datetime.utcnow().isoformat()
        )

    except FileNotFoundError:
        return ToolResult(
            tool_name="read",
            status="FAILURE",
            stdout="",
            stderr=f"File not found: {file_path_str}",
            returncode=1,
            timestamp=datetime.utcnow().isoformat()
        )

    except Exception as e:
        return ToolResult(
            tool_name="read",
            status="ERROR",
            stdout="",
            stderr=str(e),
            returncode=-1,
            timestamp=datetime.utcnow().isoformat()
        )


def list_directory(arguments: dict, workspace_path: Path) -> ToolResult:
    """
    Liste les fichiers d'un répertoire.

    Args:
        arguments: {"directory": "chemin relatif", "pattern": "*.py" (optionnel)}
        workspace_path: Chemin du workspace

    Returns:
        ToolResult avec liste des fichiers
    """
    directory = arguments.get("directory", ".")
    pattern = arguments.get("pattern", "*")

    try:
        full_path = (workspace_path / directory).resolve()

        # Sécurité
        if not str(full_path).startswith(str(workspace_path.resolve())):
            return ToolResult(
                tool_name="list_dir",
                status="ERROR",
                stdout="",
                stderr=f"Access denied: directory outside workspace: {directory}",
                returncode=-1,
                timestamp=datetime.utcnow().isoformat()
            )

        # Lister les fichiers
        files = sorted([str(p.relative_to(workspace_path)) for p in full_path.glob(pattern)])
        output = "\n".join(files) if files else "(empty)"

        return ToolResult(
            tool_name="list_dir",
            status="SUCCESS",
            stdout=output,
            stderr="",
            returncode=0,
            timestamp=datetime.utcnow().isoformat()
        )

    except Exception as e:
        return ToolResult(
            tool_name="list_dir",
            status="ERROR",
            stdout="",
            stderr=str(e),
            returncode=-1,
            timestamp=datetime.utcnow().isoformat()
        )
