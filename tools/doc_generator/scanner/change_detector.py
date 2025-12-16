# NEXUS Documentation Generator - Change Detector
"""
Detects changes in the repository since last run or commit.
"""

import json
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

from ..config import DocGeneratorConfig


@dataclass
class ChangeInfo:
    """Information about a file change."""
    path: Path
    change_type: str  # 'added', 'modified', 'deleted', 'renamed'
    old_path: Optional[Path] = None  # For renames
    lines_added: int = 0
    lines_deleted: int = 0


@dataclass
class ChangeReport:
    """Report of all changes detected."""
    since: str
    until: str
    timestamp: datetime = field(default_factory=datetime.now)
    changes: list[ChangeInfo] = field(default_factory=list)
    new_folders: list[Path] = field(default_factory=list)
    deleted_folders: list[Path] = field(default_factory=list)

    @property
    def total_changes(self) -> int:
        return len(self.changes)

    @property
    def files_added(self) -> int:
        return len([c for c in self.changes if c.change_type == "added"])

    @property
    def files_modified(self) -> int:
        return len([c for c in self.changes if c.change_type == "modified"])

    @property
    def files_deleted(self) -> int:
        return len([c for c in self.changes if c.change_type == "deleted"])


class ChangeDetector:
    """Detects changes in the repository."""

    STATE_FILE = ".doc_generator_state.json"

    def __init__(self, config: DocGeneratorConfig):
        self.config = config
        self.repo_root = config.repo_root
        self.state_file = self.repo_root / self.STATE_FILE

    def detect_changes(self, since: str = "HEAD~1") -> ChangeReport:
        """
        Detect all changes since a specific reference.

        Args:
            since: Git reference (commit, branch, tag)

        Returns:
            ChangeReport with all detected changes
        """
        changes = []

        # Get diff with stats
        try:
            result = subprocess.run(
                ["git", "diff", "--name-status", "--find-renames", since],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                check=True,
            )

            for line in result.stdout.strip().split("\n"):
                if not line:
                    continue

                parts = line.split("\t")
                if len(parts) < 2:
                    continue

                status = parts[0]
                file_path = Path(parts[1])

                change_type = self._parse_status(status)
                old_path = None

                # Handle renames (R100, R095, etc.)
                if status.startswith("R") and len(parts) >= 3:
                    old_path = Path(parts[1])
                    file_path = Path(parts[2])

                changes.append(ChangeInfo(
                    path=file_path,
                    change_type=change_type,
                    old_path=old_path,
                ))

        except (subprocess.CalledProcessError, FileNotFoundError):
            pass

        # Detect new/deleted folders
        new_folders = self._detect_new_folders(since)
        deleted_folders = self._detect_deleted_folders(since)

        # Get current commit
        until = self._get_current_commit()

        return ChangeReport(
            since=since,
            until=until,
            changes=changes,
            new_folders=new_folders,
            deleted_folders=deleted_folders,
        )

    def _parse_status(self, status: str) -> str:
        """Parse git status code to change type."""
        code = status[0]
        mapping = {
            "A": "added",
            "M": "modified",
            "D": "deleted",
            "R": "renamed",
            "C": "copied",
        }
        return mapping.get(code, "modified")

    def _detect_new_folders(self, since: str) -> list[Path]:
        """Detect folders that were added."""
        try:
            result = subprocess.run(
                ["git", "diff", "--name-only", "--diff-filter=A", since],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                check=True,
            )

            folders = set()
            for line in result.stdout.strip().split("\n"):
                if line:
                    parent = Path(line).parent
                    if parent != Path("."):
                        folders.add(parent)

            return sorted(folders)

        except (subprocess.CalledProcessError, FileNotFoundError):
            return []

    def _detect_deleted_folders(self, since: str) -> list[Path]:
        """Detect folders that were deleted."""
        try:
            result = subprocess.run(
                ["git", "diff", "--name-only", "--diff-filter=D", since],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                check=True,
            )

            folders = set()
            for line in result.stdout.strip().split("\n"):
                if line:
                    parent = Path(line).parent
                    if parent != Path("."):
                        folders.add(parent)

            # Only include folders that no longer exist
            deleted = [f for f in folders if not (self.repo_root / f).exists()]
            return sorted(deleted)

        except (subprocess.CalledProcessError, FileNotFoundError):
            return []

    def _get_current_commit(self) -> str:
        """Get current commit hash."""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout.strip()[:8]
        except (subprocess.CalledProcessError, FileNotFoundError):
            return "unknown"

    def save_state(self) -> None:
        """Save current state for future comparisons."""
        commit = self._get_current_commit()
        state = {
            "last_commit": commit,
            "timestamp": datetime.now().isoformat(),
        }

        with open(self.state_file, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)

    def load_state(self) -> Optional[dict]:
        """Load saved state."""
        if not self.state_file.exists():
            return None

        try:
            with open(self.state_file, encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return None

    def detect_since_last_run(self) -> ChangeReport:
        """Detect changes since last documentation generation."""
        state = self.load_state()

        if state and "last_commit" in state:
            return self.detect_changes(since=state["last_commit"])

        # Default to last commit
        return self.detect_changes(since="HEAD~1")
