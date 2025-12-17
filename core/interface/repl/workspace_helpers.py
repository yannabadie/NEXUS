"""
NEXUS V10.2 - Workspace Command Helpers

Extracted helper functions for /workspace commands.

Usage:
    from core.interface.repl.workspace_helpers import (
        list_workspaces,
        get_workspace_info
    )
"""

from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
import logging

logger = logging.getLogger("nexus.repl.workspace")


def list_workspaces(workspace_root: Path) -> List[Dict]:
    """
    List all workspaces in the workspace root directory.
    
    Args:
        workspace_root: Root directory containing workspaces
        
    Returns:
        List of workspace info dicts
    """
    workspaces = []
    
    if not workspace_root.exists():
        return workspaces
    
    for item in workspace_root.iterdir():
        if item.is_dir() and not item.name.startswith('.'):
            info = get_workspace_info(item)
            if info:
                workspaces.append(info)
    
    return sorted(workspaces, key=lambda w: w.get("modified", 0), reverse=True)


def get_workspace_info(workspace_path: Path) -> Optional[Dict]:
    """
    Get info about a specific workspace.
    
    Args:
        workspace_path: Path to workspace directory
        
    Returns:
        Workspace info dict or None
    """
    if not workspace_path.exists() or not workspace_path.is_dir():
        return None
    
    # Count files
    file_count = sum(1 for _ in workspace_path.rglob("*") if _.is_file())
    
    # Get modification time
    try:
        mtime = workspace_path.stat().st_mtime
        modified = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M")
    except Exception:
        mtime = 0
        modified = "unknown"
    
    return {
        "name": workspace_path.name,
        "path": str(workspace_path),
        "files": file_count,
        "modified": mtime,
        "modified_str": modified
    }


def validate_workspace_name(name: str) -> bool:
    """
    Validate workspace name for creation.
    
    Args:
        name: Proposed workspace name
        
    Returns:
        True if valid
    """
    if not name:
        return False
    
    # No special characters
    invalid_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
    for char in invalid_chars:
        if char in name:
            return False
    
    # Not reserved names
    reserved = ['.', '..', 'CON', 'PRN', 'AUX', 'NUL']
    if name.upper() in reserved:
        return False
    
    return True


def format_workspace_table(workspaces: List[Dict], current_name: str = None) -> str:
    """
    Format workspaces as a table string.
    
    Args:
        workspaces: List of workspace info dicts
        current_name: Name of current workspace for highlighting
        
    Returns:
        Formatted table string
    """
    if not workspaces:
        return "No workspaces found."
    
    lines = [
        "| Name | Files | Modified |",
        "|------|-------|----------|"
    ]
    
    for ws in workspaces:
        marker = " *" if ws["name"] == current_name else ""
        lines.append(
            f"| {ws['name']}{marker} | {ws['files']} | {ws['modified_str']} |"
        )
    
    return "\n".join(lines)
