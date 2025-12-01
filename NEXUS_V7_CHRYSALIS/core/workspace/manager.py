"""
Workspace Manager - Main facade for workspace operations.

Provides:
- create_workspace: Create new workspace, archive current
- list_workspaces: List all workspaces with metadata
- switch_workspace: Switch to another workspace
- get_current: Get current workspace info
"""
import re
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

from .models import WorkspaceInfo, WorkspaceMetrics, WorkspaceStatus
from .repository import WorkspaceRepository


class WorkspaceError(Exception):
    """Base exception for workspace operations."""
    pass


class WorkspaceNotFoundError(WorkspaceError):
    """Workspace does not exist."""
    pass


class WorkspaceExistsError(WorkspaceError):
    """Workspace already exists."""
    pass


class WorkspaceManager:
    """
    Manages NEXUS workspaces - creation, switching, archiving, listing.

    Storage layout:
    NEXUS_V7_CHRYSALIS/
    ├── workspace/                    # Active workspace
    ├── workspace_archive/            # Archived workspaces
    │   ├── project-x-20251201/
    │   └── ...
    └── workspace_registry.json       # Global registry
    """

    # Stop words for auto-naming (French + English)
    STOP_WORDS = {
        'le', 'la', 'les', 'un', 'une', 'des', 'de', 'du', 'et', 'ou', 'a', 'au',
        'the', 'a', 'an', 'of', 'to', 'and', 'or', 'for', 'in', 'on', 'with',
        'all', 'new', 'this', 'that', 'is', 'are', 'was', 'be', 'been', 'being',
        'avoir', 'être', 'faire', 'pour', 'dans', 'sur', 'avec', 'tout', 'tous'
    }

    def __init__(self, nexus_root: Path):
        """
        Initialize WorkspaceManager.

        Args:
            nexus_root: Path to NEXUS_V7_CHRYSALIS directory
        """
        self.nexus_root = nexus_root
        self.repo = WorkspaceRepository(nexus_root)
        self._ensure_registry()

    def _ensure_registry(self):
        """Ensure registry exists and has current workspace."""
        registry = self.repo.load_registry()

        # Check if current workspace exists in registry
        if not registry.get("active_workspace"):
            # Initialize with current workspace
            current = self._build_workspace_info(
                name="default",
                path=self.repo.workspace_dir,
                status=WorkspaceStatus.ACTIVE
            )

            registry["active_workspace"] = current.name
            registry["workspaces"][current.name] = current.to_dict()
            registry["metadata"]["total_workspaces"] = 1

            self.repo.save_registry(registry)

    def _build_workspace_info(
        self,
        name: str,
        path: Path,
        status: WorkspaceStatus,
        registry_data: Optional[dict] = None
    ) -> WorkspaceInfo:
        """
        Build WorkspaceInfo from path and optional registry data.

        Args:
            name: Workspace name
            path: Path to workspace
            status: Workspace status
            registry_data: Optional existing registry data

        Returns:
            WorkspaceInfo instance
        """
        if registry_data:
            info = WorkspaceInfo.from_dict(registry_data, self.nexus_root)
            info.path = path
            info.status = status
        else:
            # Build from scratch
            created_at = datetime.now()
            if path.exists():
                try:
                    created_at = datetime.fromtimestamp(path.stat().st_ctime)
                except Exception:
                    pass

            info = WorkspaceInfo(
                name=name,
                path=path,
                status=status,
                created_at=created_at,
                last_accessed=datetime.now() if status == WorkspaceStatus.ACTIVE else None,
                last_task=self.repo.get_blackboard_objective(path),
                metrics=WorkspaceMetrics(
                    size_bytes=self.repo.calculate_workspace_size(path),
                    files_count=self.repo.count_workspace_files(path)
                )
            )

        return info

    def get_current(self) -> Optional[WorkspaceInfo]:
        """
        Get the currently active workspace.

        Returns:
            WorkspaceInfo for current workspace or None
        """
        registry = self.repo.load_registry()
        active_name = registry.get("active_workspace")

        if not active_name:
            return None

        ws_data = registry.get("workspaces", {}).get(active_name)
        if ws_data:
            info = WorkspaceInfo.from_dict(ws_data, self.nexus_root)
            info.is_current = True
            info.path = self.repo.workspace_dir  # Always at workspace/
            return info

        # Fallback: build from directory
        return self._build_workspace_info(
            name=active_name,
            path=self.repo.workspace_dir,
            status=WorkspaceStatus.ACTIVE
        )

    def list_workspaces(self, include_archives: bool = True) -> List[WorkspaceInfo]:
        """
        List all workspaces.

        Args:
            include_archives: Include archived workspaces

        Returns:
            List of WorkspaceInfo sorted by last_accessed (recent first)
        """
        registry = self.repo.load_registry()
        active_name = registry.get("active_workspace")
        workspaces = []

        for name, data in registry.get("workspaces", {}).items():
            status = WorkspaceStatus(data.get("status", "active"))

            if status == WorkspaceStatus.ARCHIVED and not include_archives:
                continue

            # Determine path
            if status == WorkspaceStatus.ACTIVE or name == active_name:
                path = self.repo.workspace_dir
            else:
                path = self.repo.archive_dir / name

            info = WorkspaceInfo.from_dict(data, self.nexus_root)
            info.path = path
            info.is_current = (name == active_name)

            # Update metrics if active
            if info.is_current and path.exists():
                info.metrics.size_bytes = self.repo.calculate_workspace_size(path)
                info.metrics.files_count = self.repo.count_workspace_files(path)

            workspaces.append(info)

        # Sort by last_accessed (recent first), then by created_at
        workspaces.sort(
            key=lambda w: (w.last_accessed or w.created_at),
            reverse=True
        )

        return workspaces

    def create_workspace(
        self,
        name: Optional[str] = None,
        archive_current: bool = True,
        description: str = ""
    ) -> WorkspaceInfo:
        """
        Create a new workspace, optionally archiving the current one.

        Args:
            name: Workspace name (auto-generated if None)
            archive_current: Whether to archive current workspace first
            description: Optional description

        Returns:
            WorkspaceInfo for new workspace

        Raises:
            WorkspaceExistsError: If name already exists
        """
        registry = self.repo.load_registry()

        # Get current workspace info before changes
        current = self.get_current()

        # Generate name if not provided
        if not name:
            objective = self.repo.get_blackboard_objective(self.repo.workspace_dir)
            name = self._generate_workspace_name(objective, list(registry.get("workspaces", {}).keys()))

        # Validate name doesn't exist
        if name in registry.get("workspaces", {}):
            raise WorkspaceExistsError(f"Workspace '{name}' already exists")

        # Archive current workspace if requested
        archive_name = None
        if archive_current and current:
            archive_name = current.name

            # Update current workspace metrics before archiving
            current.metrics.size_bytes = self.repo.calculate_workspace_size(self.repo.workspace_dir)
            current.metrics.files_count = self.repo.count_workspace_files(self.repo.workspace_dir)
            current.last_task = self.repo.get_blackboard_objective(self.repo.workspace_dir)
            current.last_accessed = datetime.now()

            # Archive
            self.repo.archive_workspace(
                self.repo.workspace_dir,
                archive_name,
                metadata=current.to_dict()
            )

            # Update registry for archived workspace
            current.status = WorkspaceStatus.ARCHIVED
            registry["workspaces"][archive_name] = current.to_dict()
            registry["metadata"]["total_archived"] = registry["metadata"].get("total_archived", 0) + 1

        # Clear current workspace for fresh start
        self.repo.clear_workspace(self.repo.workspace_dir)

        # Create new workspace info
        new_workspace = WorkspaceInfo(
            name=name,
            path=self.repo.workspace_dir,
            status=WorkspaceStatus.ACTIVE,
            created_at=datetime.now(),
            last_accessed=datetime.now(),
            description=description,
            metrics=WorkspaceMetrics(),
            is_current=True
        )

        # Save metadata to workspace
        self.repo.save_workspace_meta(self.repo.workspace_dir, new_workspace.to_dict())

        # Update registry
        registry["active_workspace"] = name
        registry["workspaces"][name] = new_workspace.to_dict()
        registry["metadata"]["total_workspaces"] = len(registry["workspaces"])
        self.repo.save_registry(registry)

        return new_workspace

    def switch_workspace(
        self,
        name: str,
        archive_current: bool = True
    ) -> Tuple[Optional[WorkspaceInfo], WorkspaceInfo]:
        """
        Switch to a different workspace.

        Args:
            name: Name of workspace to switch to
            archive_current: Whether to archive current workspace state

        Returns:
            Tuple (old_workspace, new_workspace)

        Raises:
            WorkspaceNotFoundError: If target workspace doesn't exist
        """
        registry = self.repo.load_registry()

        # Check target exists
        if name not in registry.get("workspaces", {}):
            # Try partial match
            matches = [n for n in registry.get("workspaces", {}).keys() if name.lower() in n.lower()]
            if len(matches) == 1:
                name = matches[0]
            elif len(matches) > 1:
                raise WorkspaceNotFoundError(
                    f"Multiple workspaces match '{name}': {', '.join(matches)}"
                )
            else:
                raise WorkspaceNotFoundError(f"Workspace '{name}' not found")

        target_data = registry["workspaces"][name]

        # Check if already active
        if name == registry.get("active_workspace"):
            current = self.get_current()
            return current, current

        # Get current workspace
        current = self.get_current()

        # Archive current workspace state if requested
        if archive_current and current:
            # Update metrics
            current.metrics.size_bytes = self.repo.calculate_workspace_size(self.repo.workspace_dir)
            current.metrics.files_count = self.repo.count_workspace_files(self.repo.workspace_dir)
            current.last_task = self.repo.get_blackboard_objective(self.repo.workspace_dir)
            current.last_accessed = datetime.now()

            # Archive current
            self.repo.archive_workspace(
                self.repo.workspace_dir,
                current.name,
                metadata=current.to_dict()
            )

            # Mark as archived
            current.status = WorkspaceStatus.ARCHIVED
            registry["workspaces"][current.name] = current.to_dict()

        # Restore target workspace
        archive_path = self.repo.archive_dir / name
        if archive_path.exists():
            self.repo.copy_archive_to_workspace(name, self.repo.workspace_dir)
        else:
            # Target might be the current active workspace (edge case)
            self.repo.clear_workspace(self.repo.workspace_dir)

        # Build new workspace info
        new_workspace = WorkspaceInfo.from_dict(target_data, self.nexus_root)
        new_workspace.path = self.repo.workspace_dir
        new_workspace.status = WorkspaceStatus.ACTIVE
        new_workspace.last_accessed = datetime.now()
        new_workspace.is_current = True

        # Update registry
        registry["active_workspace"] = name
        registry["workspaces"][name] = new_workspace.to_dict()
        self.repo.save_registry(registry)

        # Save workspace metadata
        self.repo.save_workspace_meta(self.repo.workspace_dir, new_workspace.to_dict())

        return current, new_workspace

    def update_metrics(
        self,
        iterations: int = 0,
        gemini_calls: int = 0,
        claude_calls: int = 0,
        tokens_used: int = 0
    ):
        """
        Update metrics for current workspace.

        Args:
            iterations: Iterations to add
            gemini_calls: Gemini API calls to add
            claude_calls: Claude API calls to add
            tokens_used: Tokens to add
        """
        registry = self.repo.load_registry()
        active_name = registry.get("active_workspace")

        if not active_name or active_name not in registry.get("workspaces", {}):
            return

        ws_data = registry["workspaces"][active_name]
        metrics = ws_data.get("metrics", {})

        metrics["iterations"] = metrics.get("iterations", 0) + iterations
        metrics["gemini_calls"] = metrics.get("gemini_calls", 0) + gemini_calls
        metrics["claude_calls"] = metrics.get("claude_calls", 0) + claude_calls
        metrics["tokens_used"] = metrics.get("tokens_used", 0) + tokens_used
        metrics["size_bytes"] = self.repo.calculate_workspace_size(self.repo.workspace_dir)
        metrics["files_count"] = self.repo.count_workspace_files(self.repo.workspace_dir)

        ws_data["metrics"] = metrics
        ws_data["last_accessed"] = datetime.now().isoformat()
        ws_data["last_task"] = self.repo.get_blackboard_objective(self.repo.workspace_dir)

        registry["workspaces"][active_name] = ws_data
        self.repo.save_registry(registry)

    def _generate_workspace_name(self, objective: str, existing_names: List[str]) -> str:
        """
        Generate workspace name from objective.

        Args:
            objective: Current task objective
            existing_names: List of existing workspace names

        Returns:
            Generated name (slug-format with date)
        """
        if objective:
            # Extract keywords (remove stop words, take first 3)
            words = re.findall(r'\b[a-zA-ZÀ-ÿ]+\b', objective.lower())
            keywords = [w for w in words if w not in self.STOP_WORDS and len(w) > 2][:3]
            base = "-".join(keywords) if keywords else "workspace"
            # Clean: keep alphanumeric + hyphens
            base = re.sub(r'[^a-z0-9-]', '', base)
        else:
            base = "workspace"

        date_suffix = datetime.now().strftime("%Y%m%d")
        name = f"{base}-{date_suffix}"

        # Handle duplicates
        if name in existing_names:
            counter = 2
            while f"{name}-{counter}" in existing_names:
                counter += 1
            name = f"{name}-{counter}"

        return name

    def find_workspace(self, query: str) -> Optional[WorkspaceInfo]:
        """
        Find a workspace by name or partial match.

        Args:
            query: Name or partial name to search

        Returns:
            WorkspaceInfo if found, None otherwise
        """
        registry = self.repo.load_registry()
        workspaces = registry.get("workspaces", {})

        # Exact match
        if query in workspaces:
            return WorkspaceInfo.from_dict(workspaces[query], self.nexus_root)

        # Partial match
        matches = [name for name in workspaces if query.lower() in name.lower()]
        if len(matches) == 1:
            return WorkspaceInfo.from_dict(workspaces[matches[0]], self.nexus_root)

        return None

    def get_suggestions(self, query: str, limit: int = 5) -> List[str]:
        """
        Get workspace name suggestions for partial query.

        Args:
            query: Partial name to match
            limit: Maximum suggestions

        Returns:
            List of matching workspace names
        """
        registry = self.repo.load_registry()
        workspaces = registry.get("workspaces", {})

        matches = [
            name for name in workspaces
            if query.lower() in name.lower()
        ]

        return sorted(matches)[:limit]
