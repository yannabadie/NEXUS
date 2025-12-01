"""
Workspace Models - Data structures for workspace management.

Defines:
- WorkspaceStatus: Enum for workspace states
- WorkspaceMetrics: Usage statistics
- WorkspaceInfo: Complete workspace information
"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional, List


class WorkspaceStatus(Enum):
    """Workspace lifecycle states."""
    ACTIVE = "active"
    ARCHIVED = "archived"
    CORRUPTED = "corrupted"


@dataclass
class WorkspaceMetrics:
    """Usage statistics for a workspace."""
    iterations: int = 0
    files_count: int = 0
    size_bytes: int = 0
    gemini_calls: int = 0
    claude_calls: int = 0
    tokens_used: int = 0

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "iterations": self.iterations,
            "files_count": self.files_count,
            "size_bytes": self.size_bytes,
            "gemini_calls": self.gemini_calls,
            "claude_calls": self.claude_calls,
            "tokens_used": self.tokens_used
        }

    @classmethod
    def from_dict(cls, data: dict) -> "WorkspaceMetrics":
        """Create from dictionary."""
        return cls(
            iterations=data.get("iterations", 0),
            files_count=data.get("files_count", 0),
            size_bytes=data.get("size_bytes", 0),
            gemini_calls=data.get("gemini_calls", 0),
            claude_calls=data.get("claude_calls", 0),
            tokens_used=data.get("tokens_used", 0)
        )


@dataclass
class WorkspaceInfo:
    """Complete workspace information."""
    name: str
    path: Path
    status: WorkspaceStatus
    created_at: datetime
    last_accessed: Optional[datetime] = None
    last_task: str = ""
    description: str = ""
    metrics: WorkspaceMetrics = field(default_factory=WorkspaceMetrics)
    is_current: bool = False

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "name": self.name,
            "path": str(self.path),
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "last_accessed": self.last_accessed.isoformat() if self.last_accessed else None,
            "last_task": self.last_task,
            "description": self.description,
            "metrics": self.metrics.to_dict(),
            "is_current": self.is_current
        }

    @classmethod
    def from_dict(cls, data: dict, base_path: Optional[Path] = None) -> "WorkspaceInfo":
        """Create from dictionary."""
        path = Path(data["path"])
        if base_path and not path.is_absolute():
            path = base_path / path

        return cls(
            name=data["name"],
            path=path,
            status=WorkspaceStatus(data.get("status", "active")),
            created_at=datetime.fromisoformat(data["created_at"]),
            last_accessed=datetime.fromisoformat(data["last_accessed"]) if data.get("last_accessed") else None,
            last_task=data.get("last_task", ""),
            description=data.get("description", ""),
            metrics=WorkspaceMetrics.from_dict(data.get("metrics", {})),
            is_current=data.get("is_current", False)
        )

    def get_relative_time(self) -> str:
        """Get human-readable relative time since last access."""
        if not self.last_accessed:
            return "never"

        delta = datetime.now() - self.last_accessed
        seconds = delta.total_seconds()

        if seconds < 60:
            return "just now"
        elif seconds < 3600:
            minutes = int(seconds / 60)
            return f"{minutes} min ago"
        elif seconds < 86400:
            hours = int(seconds / 3600)
            return f"{hours}h ago"
        else:
            days = int(seconds / 86400)
            return f"{days} days ago"

    def get_size_human(self) -> str:
        """Get human-readable size."""
        size = self.metrics.size_bytes
        if size < 1024:
            return f"{size} B"
        elif size < 1024 * 1024:
            return f"{size / 1024:.1f} KB"
        else:
            return f"{size / (1024 * 1024):.1f} MB"
