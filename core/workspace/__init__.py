"""
NEXUS V7.6 - Workspace Management Module

Provides multi-workspace support for NEXUS sessions.
Allows creating, archiving, and switching between workspaces.

Components:
- manager.py: WorkspaceManager class
- models.py: WorkspaceInfo, WorkspaceMetrics dataclasses
- exceptions.py: Workspace-related exceptions

Usage:
    from core.workspace import WorkspaceManager

    manager = WorkspaceManager(nexus_root)
    current = manager.get_current()
    workspaces = manager.list_workspaces()
    new_ws = manager.create_workspace("my-project")
    manager.switch_workspace("old-project")
"""

from .manager import WorkspaceManager
from .models import WorkspaceInfo, WorkspaceMetrics
from .exceptions import (
    WorkspaceError,
    WorkspaceNotFoundError,
    WorkspaceExistsError,
)

__all__ = [
    "WorkspaceManager",
    "WorkspaceInfo",
    "WorkspaceMetrics",
    "WorkspaceError",
    "WorkspaceNotFoundError",
    "WorkspaceExistsError",
]
