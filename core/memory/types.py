"""
NEXUS V7.9 - Memory Types (Phase 10f)

Shared type definitions for the memory subsystem.
Extracted from project_memory.py for backend abstraction.
"""

from dataclasses import dataclass, asdict, field
from typing import Dict, Set, Optional


@dataclass
class Chunk:
    """A single indexed chunk of code or documentation."""
    file_path: str
    start_line: int
    end_line: int
    content: str
    terms: Set[str] = field(default_factory=set)
    chunk_type: str = "lines"  # "function", "class", "section", "lines"
    name: Optional[str] = None  # Function/class/section name if applicable

    def to_dict(self) -> Dict:
        """Convert to JSON-serializable dict."""
        return {
            "file_path": self.file_path,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "content": self.content,
            "terms": list(self.terms),
            "chunk_type": self.chunk_type,
            "name": self.name
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'Chunk':
        """Create from JSON dict."""
        return cls(
            file_path=data["file_path"],
            start_line=data["start_line"],
            end_line=data["end_line"],
            content=data["content"],
            terms=set(data.get("terms", [])),
            chunk_type=data.get("chunk_type", "lines"),
            name=data.get("name")
        )


@dataclass
class IndexStats:
    """Statistics about the indexed project."""
    total_files: int = 0
    total_chunks: int = 0
    total_terms: int = 0
    indexed_at: str = ""
    storage_path: str = ""

    def to_dict(self) -> Dict:
        return asdict(self)
