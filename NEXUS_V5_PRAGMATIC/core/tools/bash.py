"""
NEXUS V5.0 - Bash Tool
Exécution sécurisée de commandes shell dans le workspace.
"""
import subprocess
from pathlib import Path
from datetime import datetime
from core.synapse.protocol import ToolResult


def execute(arguments: dict, workspace_path: Path) -> ToolResult:
    """
    Exécute une commande bash dans le workspace.

    Args:
        arguments: {"command": "commande shell"}
        workspace_path: Chemin du workspace (sandbox)

    Returns:
        ToolResult avec sortie capturée
    """
    command = arguments.get("command", "")

    if not command:
        return ToolResult(
            tool_name="bash",
            status="ERROR",
            stdout="",
            stderr="Missing 'command' argument",
            returncode=-1,
            timestamp=datetime.utcnow().isoformat()
        )

    try:
        # Exécution dans le workspace avec timeout
        result = subprocess.run(
            command,
            shell=True,
            cwd=str(workspace_path),
            capture_output=True,
            text=True,
            timeout=120,
            encoding="utf-8",
            errors="replace"
        )

        status = "SUCCESS" if result.returncode == 0 else "FAILURE"

        return ToolResult(
            tool_name="bash",
            status=status,
            stdout=result.stdout or "",
            stderr=result.stderr or "",
            returncode=result.returncode,
            timestamp=datetime.utcnow().isoformat()
        )

    except subprocess.TimeoutExpired:
        return ToolResult(
            tool_name="bash",
            status="TIMEOUT",
            stdout="",
            stderr=f"Command timed out after 120s: {command}",
            returncode=-1,
            timestamp=datetime.utcnow().isoformat()
        )

    except Exception as e:
        return ToolResult(
            tool_name="bash",
            status="ERROR",
            stdout="",
            stderr=str(e),
            returncode=-1,
            timestamp=datetime.utcnow().isoformat()
        )
