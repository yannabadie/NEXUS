"""
Workspace Repository - File system operations for workspace management.

Handles:
- Directory creation/deletion
- Archiving workspaces
- Loading/saving registry and metadata
- Size calculation
"""
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any

from .models import WorkspaceInfo, WorkspaceMetrics, WorkspaceStatus


class WorkspaceRepository:
    """File system operations for workspaces."""

    # Required directories in a workspace
    REQUIRED_DIRS = ["_IO_BUFFER", ".nexus", "logs", "external_sources"]

    # Files to ignore when copying/archiving
    # Includes Windows reserved names (nul, con, prn, aux, etc.)
    IGNORE_PATTERNS = [
        "__pycache__", "*.pyc", ".git",
        "nul", "con", "prn", "aux",  # Windows reserved device names
        "com1", "com2", "com3", "com4", "lpt1", "lpt2", "lpt3"
    ]

    def __init__(self, nexus_root: Path):
        """
        Initialize repository.

        Args:
            nexus_root: Path to NEXUS_V7_CHRYSALIS directory
        """
        self.nexus_root = nexus_root
        self.workspace_dir = nexus_root / "workspace"
        self.archive_dir = nexus_root / "workspace_archive"
        self.registry_path = nexus_root / "workspace_registry.json"

    def ensure_directories(self):
        """Ensure archive directory exists."""
        self.archive_dir.mkdir(parents=True, exist_ok=True)

    def create_workspace_structure(self, path: Path) -> bool:
        """
        Create required workspace directory structure.

        Args:
            path: Path where to create workspace

        Returns:
            True if created successfully
        """
        try:
            path.mkdir(parents=True, exist_ok=True)
            for dirname in self.REQUIRED_DIRS:
                (path / dirname).mkdir(exist_ok=True)

            # Create panic subdirectory
            (path / ".nexus" / "panic").mkdir(exist_ok=True)
            (path / ".nexus" / "backups").mkdir(exist_ok=True)

            return True
        except Exception:
            return False

    def archive_workspace(
        self,
        source_path: Path,
        archive_name: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Path:
        """
        Archive a workspace to workspace_archive/.

        Args:
            source_path: Path to workspace to archive
            archive_name: Name for the archive
            metadata: Optional metadata to save with archive

        Returns:
            Path to archived workspace
        """
        self.ensure_directories()
        archive_path = self.archive_dir / archive_name

        def ignore_and_errors(directory, files):
            """Ignore patterns + skip files that would cause errors."""
            ignored = set()
            for f in files:
                # Check ignore patterns
                for pattern in self.IGNORE_PATTERNS:
                    if pattern.startswith("*"):
                        if f.endswith(pattern[1:]):
                            ignored.add(f)
                    elif f.lower() == pattern.lower():
                        ignored.add(f)
            return ignored

        # Copy workspace to archive with error handling
        try:
            shutil.copytree(
                source_path,
                archive_path,
                ignore=ignore_and_errors,
                dirs_exist_ok=True
            )
        except shutil.Error as e:
            # Some files failed to copy - continue anyway
            # Extract successfully copied files
            pass

        # Save archive metadata
        if metadata:
            meta_path = archive_path / ".nexus" / "workspace_meta.json"
            meta_path.parent.mkdir(parents=True, exist_ok=True)
            meta_path.write_text(
                json.dumps(metadata, indent=2, ensure_ascii=False),
                encoding='utf-8'
            )

        return archive_path

    def clear_workspace(self, path: Path) -> bool:
        """
        Clear workspace contents while preserving structure.

        Args:
            path: Path to workspace to clear

        Returns:
            True if cleared successfully
        """
        # Windows reserved names to skip
        reserved_names = {'nul', 'con', 'prn', 'aux', 'com1', 'com2', 'com3', 'com4', 'lpt1', 'lpt2', 'lpt3'}

        def safe_delete(item: Path):
            """Safely delete item, skipping Windows reserved names."""
            if item.name.lower() in reserved_names:
                return  # Skip reserved names
            try:
                if item.is_dir():
                    shutil.rmtree(item)
                else:
                    item.unlink()
            except (PermissionError, OSError):
                pass  # Skip files that can't be deleted

        try:
            # Remove all contents except .nexus structure
            for item in path.iterdir():
                if item.name == ".nexus":
                    # Clear .nexus contents except structure
                    for nexus_item in item.iterdir():
                        if nexus_item.name in ["panic", "backups"]:
                            continue  # Keep empty dirs
                        safe_delete(nexus_item)
                else:
                    safe_delete(item)

            # Recreate required structure
            self.create_workspace_structure(path)
            return True
        except Exception:
            return False

    def copy_archive_to_workspace(self, archive_name: str, workspace_path: Path) -> bool:
        """
        Restore an archived workspace to the active workspace location.

        Args:
            archive_name: Name of the archive to restore
            workspace_path: Destination path

        Returns:
            True if restored successfully
        """
        archive_path = self.archive_dir / archive_name
        if not archive_path.exists():
            return False

        try:
            # Clear current workspace
            self.clear_workspace(workspace_path)

            # Copy archive to workspace
            for item in archive_path.iterdir():
                dest = workspace_path / item.name
                if item.is_dir():
                    shutil.copytree(item, dest, dirs_exist_ok=True)
                else:
                    shutil.copy2(item, dest)

            return True
        except Exception:
            return False

    def calculate_workspace_size(self, path: Path) -> int:
        """
        Calculate total size of workspace in bytes.

        Args:
            path: Path to workspace

        Returns:
            Size in bytes
        """
        total = 0
        try:
            for item in path.rglob("*"):
                if item.is_file():
                    total += item.stat().st_size
        except Exception:
            pass
        return total

    def count_workspace_files(self, path: Path) -> int:
        """
        Count files in workspace.

        Args:
            path: Path to workspace

        Returns:
            Number of files
        """
        count = 0
        try:
            for item in path.rglob("*"):
                if item.is_file():
                    count += 1
        except Exception:
            pass
        return count

    def load_registry(self) -> Dict[str, Any]:
        """
        Load workspace registry from JSON file.

        Returns:
            Registry dictionary or default structure
        """
        if self.registry_path.exists():
            try:
                return json.loads(self.registry_path.read_text(encoding='utf-8'))
            except Exception:
                pass

        # Return default structure
        return {
            "version": "1.0",
            "active_workspace": None,
            "workspaces": {},
            "metadata": {
                "total_workspaces": 0,
                "total_archived": 0,
                "registry_created": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat()
            }
        }

    def save_registry(self, registry: Dict[str, Any]):
        """
        Save workspace registry to JSON file.

        Args:
            registry: Registry dictionary to save
        """
        registry["metadata"]["last_updated"] = datetime.now().isoformat()
        self.registry_path.write_text(
            json.dumps(registry, indent=2, ensure_ascii=False),
            encoding='utf-8'
        )

    def load_workspace_meta(self, workspace_path: Path) -> Optional[Dict[str, Any]]:
        """
        Load workspace metadata from .nexus/workspace_meta.json.

        Args:
            workspace_path: Path to workspace

        Returns:
            Metadata dictionary or None
        """
        meta_path = workspace_path / ".nexus" / "workspace_meta.json"
        if meta_path.exists():
            try:
                return json.loads(meta_path.read_text(encoding='utf-8'))
            except Exception:
                pass
        return None

    def save_workspace_meta(self, workspace_path: Path, metadata: Dict[str, Any]):
        """
        Save workspace metadata to .nexus/workspace_meta.json.

        Args:
            workspace_path: Path to workspace
            metadata: Metadata to save
        """
        meta_path = workspace_path / ".nexus" / "workspace_meta.json"
        meta_path.parent.mkdir(parents=True, exist_ok=True)
        meta_path.write_text(
            json.dumps(metadata, indent=2, ensure_ascii=False),
            encoding='utf-8'
        )

    def list_archives(self) -> List[str]:
        """
        List all archived workspace names.

        Returns:
            List of archive directory names
        """
        if not self.archive_dir.exists():
            return []

        return sorted([
            d.name for d in self.archive_dir.iterdir()
            if d.is_dir()
        ])

    def workspace_exists(self, name: str) -> bool:
        """
        Check if a workspace with given name exists (active or archived).

        Args:
            name: Workspace name to check

        Returns:
            True if exists
        """
        registry = self.load_registry()
        return name in registry.get("workspaces", {})

    def validate_workspace(self, path: Path) -> tuple:
        """
        Validate workspace integrity.

        Args:
            path: Path to workspace

        Returns:
            Tuple (is_valid, missing_items)
        """
        missing = []

        if not path.exists():
            return False, ["workspace directory"]

        for dirname in self.REQUIRED_DIRS:
            if not (path / dirname).exists():
                missing.append(dirname)

        return len(missing) == 0, missing

    def repair_workspace(self, path: Path) -> bool:
        """
        Repair a corrupted workspace by recreating missing structures.

        Args:
            path: Path to workspace

        Returns:
            True if repaired successfully
        """
        try:
            return self.create_workspace_structure(path)
        except Exception:
            return False

    def get_blackboard_objective(self, workspace_path: Path) -> str:
        """
        Extract objective from workspace blackboard.

        Args:
            workspace_path: Path to workspace

        Returns:
            Objective string or empty string
        """
        blackboard_path = workspace_path / ".nexus" / "blackboard.json"
        if blackboard_path.exists():
            try:
                data = json.loads(blackboard_path.read_text(encoding='utf-8'))
                return data.get("objective", "")
            except Exception:
                pass
        return ""
