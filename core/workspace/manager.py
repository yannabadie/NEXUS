"""
WorkspaceManager - Multi-workspace management for NEXUS

Provides functionality to create, archive, list, and switch between
workspaces. Each workspace is an isolated environment with its own
logs, memory, and configuration.

Directory structure:
    nexus_root/
    ├── workspace/           # Current active workspace
    │   ├── .nexus/
    │   │   ├── workspace.json   # Workspace metadata
    │   │   ├── blackboard.json  # Agent memory
    │   │   └── ...
    │   ├── logs/
    │   └── memory/
    └── workspace_archive/   # Archived workspaces
        ├── project-alpha/
        ├── project-beta/
        └── ...
"""

import shutil
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from difflib import get_close_matches

from .models import WorkspaceInfo, WorkspaceMetrics
from .exceptions import (
    WorkspaceError,
    WorkspaceNotFoundError,
    WorkspaceExistsError,
)


class WorkspaceManager:
    """
    Manager for NEXUS workspaces.

    Handles creation, archiving, listing, and switching between workspaces.
    """

    WORKSPACE_DIR = "workspace"
    ARCHIVE_DIR = "workspace_archive"
    METADATA_FILE = ".nexus/workspace.json"

    def __init__(self, nexus_root: Path):
        """
        Initialize WorkspaceManager.

        Args:
            nexus_root: Root directory of NEXUS installation
        """
        self.nexus_root = Path(nexus_root)
        self.workspace_path = self.nexus_root / self.WORKSPACE_DIR
        self.archive_path = self.nexus_root / self.ARCHIVE_DIR

        self._logger = logging.getLogger("nexus.workspace")

        # Ensure directories exist
        self.workspace_path.mkdir(parents=True, exist_ok=True)
        self.archive_path.mkdir(parents=True, exist_ok=True)

    # =========================================================================
    # Current Workspace
    # =========================================================================

    def get_current(self) -> Optional[WorkspaceInfo]:
        """
        Get current active workspace info.

        Returns:
            WorkspaceInfo or None if no active workspace
        """
        if not self.workspace_path.exists():
            return None

        # Check if workspace has any content
        if not any(self.workspace_path.iterdir()):
            return None

        info = WorkspaceInfo.load_from_path(self.workspace_path)
        if info:
            info.is_current = True
            info.update_files_count()
        return info

    def has_current(self) -> bool:
        """Check if there's an active workspace."""
        return self.get_current() is not None

    # =========================================================================
    # List Workspaces
    # =========================================================================

    def list_workspaces(self) -> List[WorkspaceInfo]:
        """
        List all workspaces (current + archived).

        Returns:
            List of WorkspaceInfo sorted by last_used (most recent first)
        """
        workspaces = []

        # Current workspace
        current = self.get_current()
        if current:
            workspaces.append(current)

        # Archived workspaces
        if self.archive_path.exists():
            for ws_dir in self.archive_path.iterdir():
                if ws_dir.is_dir():
                    info = WorkspaceInfo.load_from_path(ws_dir)
                    if info:
                        info.is_current = False
                        workspaces.append(info)

        # Sort by last_used (most recent first)
        workspaces.sort(key=lambda x: x.last_used, reverse=True)

        return workspaces

    def find_workspace(self, name: str) -> Optional[WorkspaceInfo]:
        """
        Find a workspace by name.

        Args:
            name: Workspace name to find

        Returns:
            WorkspaceInfo or None
        """
        # Check current
        current = self.get_current()
        if current and current.name == name:
            return current

        # Check archives
        archive_path = self.archive_path / name
        if archive_path.exists() and archive_path.is_dir():
            return WorkspaceInfo.load_from_path(archive_path)

        return None

    def get_suggestions(self, name: str, n: int = 3) -> List[str]:
        """
        Get workspace name suggestions for typo correction.

        Args:
            name: Attempted workspace name
            n: Number of suggestions

        Returns:
            List of similar workspace names
        """
        all_names = [ws.name for ws in self.list_workspaces()]
        return get_close_matches(name, all_names, n=n, cutoff=0.4)

    # =========================================================================
    # Create Workspace
    # =========================================================================

    def create_workspace(
        self,
        name: Optional[str] = None,
        archive_current: bool = True,
    ) -> WorkspaceInfo:
        """
        Create a new workspace.

        Args:
            name: Workspace name (auto-generated if None)
            archive_current: Archive current workspace before creating

        Returns:
            WorkspaceInfo for new workspace

        Raises:
            WorkspaceExistsError: If workspace with name exists in archive
        """
        # Generate name if not provided
        if not name:
            name = self._generate_workspace_name()

        # Clean name
        name = self._sanitize_name(name)

        # Check if already exists in archive
        if (self.archive_path / name).exists():
            raise WorkspaceExistsError(name)

        # Archive current if requested
        if archive_current and self.has_current():
            current = self.get_current()
            if current:
                self.archive_current(current.name or name)

        # Clear workspace directory
        if self.workspace_path.exists():
            shutil.rmtree(self.workspace_path)

        # Create fresh workspace
        self.workspace_path.mkdir(parents=True)

        # Create workspace structure
        (self.workspace_path / ".nexus").mkdir()
        (self.workspace_path / "logs").mkdir()
        (self.workspace_path / "memory").mkdir()

        # Create workspace info
        info = WorkspaceInfo(
            name=name,
            path=self.workspace_path,
            created_at=datetime.now(),
            last_used=datetime.now(),
            is_current=True,
        )

        # Save metadata
        info.save_metadata()

        self._logger.info(f"Created workspace: {name}")
        return info

    def _generate_workspace_name(self) -> str:
        """Generate a unique workspace name."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"session_{timestamp}"

    def _sanitize_name(self, name: str) -> str:
        """Sanitize workspace name for filesystem."""
        # Replace spaces and special chars
        import re
        name = re.sub(r'[^\w\-]', '_', name)
        name = re.sub(r'_+', '_', name)  # Collapse multiple underscores
        name = name.strip('_')
        return name[:50]  # Limit length

    # =========================================================================
    # Archive Workspace
    # =========================================================================

    def archive_current(self, name: Optional[str] = None) -> Path:
        """
        Archive the current workspace.

        Args:
            name: Archive name (uses current name if None)

        Returns:
            Path to archived workspace

        Raises:
            WorkspaceError: If no current workspace
            WorkspaceExistsError: If archive name exists
        """
        current = self.get_current()
        if not current:
            raise WorkspaceError("No current workspace to archive")

        # Use provided name or current name
        archive_name = name or current.name or self._generate_workspace_name()
        archive_name = self._sanitize_name(archive_name)

        # Check if already exists
        target_path = self.archive_path / archive_name
        if target_path.exists():
            # Add timestamp suffix
            timestamp = datetime.now().strftime("%H%M%S")
            archive_name = f"{archive_name}_{timestamp}"
            target_path = self.archive_path / archive_name

        # Update metadata before archiving
        current.last_used = datetime.now()
        current.is_current = False
        current.save_metadata()

        # Move to archive
        shutil.move(str(self.workspace_path), str(target_path))

        self._logger.info(f"Archived workspace to: {archive_name}")
        return target_path

    # =========================================================================
    # Switch Workspace
    # =========================================================================

    def switch_workspace(self, name: str, save_current: bool = True) -> WorkspaceInfo:
        """
        Switch to another workspace.

        Args:
            name: Name of workspace to switch to
            save_current: Save current workspace state before switching

        Returns:
            WorkspaceInfo for the switched-to workspace

        Raises:
            WorkspaceNotFoundError: If target workspace not found
        """
        # Find target workspace
        target = self.find_workspace(name)
        if not target:
            raise WorkspaceNotFoundError(name)

        # Already current?
        if target.is_current:
            return target

        # Archive current if it has content
        if save_current and self.has_current():
            current = self.get_current()
            if current:
                self.archive_current(current.name)

        # Restore target
        target_archive_path = self.archive_path / name

        # Clear workspace and restore from archive
        if self.workspace_path.exists():
            shutil.rmtree(self.workspace_path)

        shutil.move(str(target_archive_path), str(self.workspace_path))

        # Update metadata
        info = WorkspaceInfo.load_from_path(self.workspace_path)
        if info:
            info.last_used = datetime.now()
            info.is_current = True
            info.save_metadata()

        self._logger.info(f"Switched to workspace: {name}")
        return info or target

    # =========================================================================
    # Utility Methods
    # =========================================================================

    def update_current_task(self, task: str) -> None:
        """Update the last task for current workspace."""
        current = self.get_current()
        if current:
            current.last_task = task[:200]  # Limit length
            current.last_used = datetime.now()
            current.metrics.iterations += 1
            current.save_metadata()

    def delete_archive(self, name: str) -> bool:
        """
        Delete an archived workspace.

        Args:
            name: Archive name to delete

        Returns:
            True if deleted, False if not found
        """
        archive_path = self.archive_path / name
        if archive_path.exists():
            shutil.rmtree(archive_path)
            self._logger.info(f"Deleted archive: {name}")
            return True
        return False

    def get_archive_size(self) -> str:
        """Get total size of all archives."""
        total = 0
        try:
            for f in self.archive_path.rglob("*"):
                if f.is_file():
                    total += f.stat().st_size
        except Exception:
            return "?"

        if total < 1024 * 1024:
            return f"{total // 1024}KB"
        elif total < 1024 * 1024 * 1024:
            return f"{total // (1024 * 1024)}MB"
        else:
            return f"{total // (1024 * 1024 * 1024)}GB"
