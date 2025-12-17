"""
Workspace Models

Data classes for workspace information and metrics.
"""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional
import json


@dataclass
class WorkspaceMetrics:
    """
    Metrics for a workspace.

    Tracks usage statistics for the workspace.
    """
    iterations: int = 0
    files_count: int = 0
    total_tokens: int = 0
    tasks_completed: int = 0

    def to_dict(self) -> dict:
        """Serialize to dict."""
        return {
            "iterations": self.iterations,
            "files_count": self.files_count,
            "total_tokens": self.total_tokens,
            "tasks_completed": self.tasks_completed,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "WorkspaceMetrics":
        """Deserialize from dict."""
        return cls(
            iterations=data.get("iterations", 0),
            files_count=data.get("files_count", 0),
            total_tokens=data.get("total_tokens", 0),
            tasks_completed=data.get("tasks_completed", 0),
        )


@dataclass
class WorkspaceInfo:
    """
    Information about a workspace.

    Contains metadata, path, and metrics for a workspace.
    """
    name: str
    path: Path
    created_at: datetime = field(default_factory=datetime.now)
    last_used: datetime = field(default_factory=datetime.now)
    last_task: str = ""
    is_current: bool = False
    metrics: WorkspaceMetrics = field(default_factory=WorkspaceMetrics)

    def get_relative_time(self) -> str:
        """Get human-readable relative time since last use."""
        now = datetime.now()
        delta = now - self.last_used

        if delta.days > 365:
            years = delta.days // 365
            return f"{years}y ago"
        elif delta.days > 30:
            months = delta.days // 30
            return f"{months}mo ago"
        elif delta.days > 0:
            return f"{delta.days}d ago"
        elif delta.seconds > 3600:
            hours = delta.seconds // 3600
            return f"{hours}h ago"
        elif delta.seconds > 60:
            mins = delta.seconds // 60
            return f"{mins}m ago"
        else:
            return "just now"

    def get_size_human(self) -> str:
        """Get human-readable size of workspace."""
        try:
            total_size = sum(
                f.stat().st_size
                for f in self.path.rglob("*")
                if f.is_file()
            )

            if total_size < 1024:
                return f"{total_size}B"
            elif total_size < 1024 * 1024:
                return f"{total_size // 1024}KB"
            elif total_size < 1024 * 1024 * 1024:
                return f"{total_size // (1024 * 1024)}MB"
            else:
                return f"{total_size // (1024 * 1024 * 1024)}GB"
        except Exception:
            return "?"

    def update_files_count(self) -> int:
        """Update and return files count."""
        try:
            count = sum(1 for f in self.path.rglob("*") if f.is_file())
            self.metrics.files_count = count
            return count
        except Exception:
            return 0

    def to_dict(self) -> dict:
        """Serialize to dict for JSON storage."""
        return {
            "name": self.name,
            "path": str(self.path),
            "created_at": self.created_at.isoformat(),
            "last_used": self.last_used.isoformat(),
            "last_task": self.last_task,
            "is_current": self.is_current,
            "metrics": self.metrics.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "WorkspaceInfo":
        """Deserialize from dict."""
        return cls(
            name=data.get("name", "unknown"),
            path=Path(data.get("path", ".")),
            created_at=datetime.fromisoformat(data.get("created_at", datetime.now().isoformat())),
            last_used=datetime.fromisoformat(data.get("last_used", datetime.now().isoformat())),
            last_task=data.get("last_task", ""),
            is_current=data.get("is_current", False),
            metrics=WorkspaceMetrics.from_dict(data.get("metrics", {})),
        )

    def save_metadata(self) -> None:
        """Save workspace metadata to .nexus/workspace.json."""
        meta_dir = self.path / ".nexus"
        meta_dir.mkdir(parents=True, exist_ok=True)

        meta_file = meta_dir / "workspace.json"
        with open(meta_file, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load_from_path(cls, path: Path) -> Optional["WorkspaceInfo"]:
        """Load workspace info from path."""
        meta_file = path / ".nexus" / "workspace.json"

        if not meta_file.exists():
            # Create minimal info from path
            return cls(
                name=path.name,
                path=path,
            )

        try:
            with open(meta_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            info = cls.from_dict(data)
            info.path = path  # Ensure path is correct
            return info
        except Exception:
            return cls(
                name=path.name,
                path=path,
            )
