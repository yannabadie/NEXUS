"""
Workspace Management Module for NEXUS V7.

Provides multi-workspace support with:
- Hot-swap (change workspace without restart)
- Full metrics tracking (iterations, tokens, agents)
- Rich UX (tables, confirmations)
- Auto-naming based on task objective

Usage:
    from core.workspace import WorkspaceManager

    manager = WorkspaceManager(nexus_root)
    current = manager.get_current()
    workspaces = manager.list_workspaces()
    new_ws = manager.create_workspace("my-project")
    old, new = manager.switch_workspace("other-project")
"""
from .models import WorkspaceInfo, WorkspaceMetrics, WorkspaceStatus
from .manager import (
    WorkspaceManager,
    WorkspaceError,
    WorkspaceNotFoundError,
    WorkspaceExistsError
)
from .repository import WorkspaceRepository

__all__ = [
    # Main manager
    "WorkspaceManager",

    # Models
    "WorkspaceInfo",
    "WorkspaceMetrics",
    "WorkspaceStatus",

    # Exceptions
    "WorkspaceError",
    "WorkspaceNotFoundError",
    "WorkspaceExistsError",

    # Low-level (for advanced use)
    "WorkspaceRepository",
]
