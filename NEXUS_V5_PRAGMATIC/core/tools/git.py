"""
NEXUS V5.0 - Git Tool
Opérations git sécurisées dans le workspace.
"""
import subprocess
from pathlib import Path
from datetime import datetime
from core.synapse.protocol import ToolResult


def execute(arguments: dict, workspace_path: Path) -> ToolResult:
    """
    Exécute une commande git dans le workspace.

    Args:
        arguments: {
            "operation": "add|commit|status|diff|log",
            "args": "arguments additionnels"
        }
        workspace_path: Chemin du workspace

    Returns:
        ToolResult avec sortie git
    """
    operation = arguments.get("operation", "")
    args = arguments.get("args", "")

    if operation not in ["add", "commit", "status", "diff", "log", "push", "pull"]:
        return ToolResult(
            tool_name="git",
            status="ERROR",
            stdout="",
            stderr=f"Invalid git operation: {operation}. Allowed: add, commit, status, diff, log, push, pull",
            returncode=-1,
            timestamp=datetime.utcnow().isoformat()
        )

    try:
        # Construire la commande git
        command = ["git", operation]
        if args:
            command.extend(args.split())

        # Exécuter git
        result = subprocess.run(
            command,
            cwd=str(workspace_path),
            capture_output=True,
            text=True,
            timeout=60,
            encoding="utf-8",
            errors="replace"
        )

        status = "SUCCESS" if result.returncode == 0 else "FAILURE"

        return ToolResult(
            tool_name="git",
            status=status,
            stdout=result.stdout or "",
            stderr=result.stderr or "",
            returncode=result.returncode,
            timestamp=datetime.utcnow().isoformat()
        )

    except subprocess.TimeoutExpired:
        return ToolResult(
            tool_name="git",
            status="TIMEOUT",
            stdout="",
            stderr=f"Git command timed out after 60s: git {operation} {args}",
            returncode=-1,
            timestamp=datetime.utcnow().isoformat()
        )

    except Exception as e:
        return ToolResult(
            tool_name="git",
            status="ERROR",
            stdout="",
            stderr=str(e),
            returncode=-1,
            timestamp=datetime.utcnow().isoformat()
        )
