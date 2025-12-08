"""
NEXUS V7.8 - Project Memory RAG (Phase 10c)

Persistent project knowledge base using TF-IDF weighted Jaccard similarity.
Stores indexed code and documentation for context-aware responses.

Architecture:
- Storage: .nexus/project_knowledge.json (at NEXUS_ROOT, NOT in workspace/)
- Persistence: Survives /workspace new (workspace is session, memory is project)
- Sharing: All agents (Gemini, Claude, spawned) share the same factual knowledge

Chunking Strategy:
- .py files: Split by function/class definitions
- .md files: Split by sections (headers)
- Other files: Split by lines (50 lines, 10 overlap)

Scoring: TF-IDF weighted Jaccard similarity
- Precompute terms per chunk (lowercase, alphanumeric)
- Build IDF from all indexed chunks
- Score = sum(idf[term] for term in query ∩ chunk) / len(query_terms)

Usage:
    memory = ProjectMemory(nexus_root)
    memory.index_file(Path("core/orchestration_v7.py"))
    chunks = memory.retrieve("FSM state handling", limit=5)
"""

import json
import re
import math
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Set, Optional, Any
from dataclasses import dataclass, asdict, field
from collections import defaultdict


# =============================================================================
# Configuration
# =============================================================================

import os

DEFAULT_EXTENSIONS = [".py", ".md", ".txt", ".yaml", ".yml", ".json", ".toml"]
EXCLUDED_DIRS = ["__pycache__", ".git", "node_modules", ".venv", "venv",
                 "workspace", "workspace_archive", ".pytest_cache", "dist", "build"]

# V7.8.1 OV-001: MAX_CHUNKS now configurable via environment
# Default: 5000 chunks, Max allowed: 50000 (memory safety)
_max_chunks_env = int(os.getenv("PROJECT_MEMORY_MAX_CHUNKS", "5000"))
MAX_CHUNKS = min(_max_chunks_env, 50000)  # Cap at 50k to prevent OOM
MAX_CHUNK_SIZE = 2000  # Characters per chunk
MIN_CHUNK_SIZE = 50  # Minimum characters to index
LINES_PER_CHUNK = 50  # For line-based chunking
LINES_OVERLAP = 10  # Overlap between chunks


# =============================================================================
# Data Classes
# =============================================================================

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


# =============================================================================
# ProjectMemory Class
# =============================================================================

class ProjectMemory:
    """
    Persistent project knowledge base for NEXUS.

    Indexes code and documentation using TF-IDF weighted Jaccard similarity
    for intelligent context retrieval during agent execution.

    Key Design Decisions:
    - Stored at NEXUS_ROOT/.nexus/project_knowledge.json (not in workspace/)
    - Shared by all agents (factual knowledge is universal)
    - Survives /workspace new (memory persists across sessions)

    Phase 10c: V7.8 HIVE MIND
    """

    STORAGE_FILE = "project_knowledge.json"

    def __init__(self, nexus_root: Path):
        """
        Initialize ProjectMemory.

        Args:
            nexus_root: Root directory of NEXUS/project installation.
                       Storage will be at nexus_root/.nexus/project_knowledge.json
        """
        self.nexus_root = Path(nexus_root)
        self.storage_dir = self.nexus_root / ".nexus"
        self.storage_path = self.storage_dir / self.STORAGE_FILE

        self._logger = logging.getLogger("nexus.project_memory")

        # In-memory data
        self.chunks: List[Chunk] = []
        self.idf: Dict[str, float] = {}  # Inverse Document Frequency
        self.indexed_files: Set[str] = set()

        # Ensure storage directory exists
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        # Load existing index
        self._load()

    # =========================================================================
    # Indexing
    # =========================================================================

    def index_file(self, path: Path, force: bool = False) -> int:
        """
        Index a single file into project memory.

        Args:
            path: Path to file (absolute or relative to nexus_root)
            force: Re-index even if already indexed

        Returns:
            Number of chunks created
        """
        # Resolve path
        if not path.is_absolute():
            path = self.nexus_root / path

        if not path.exists():
            self._logger.warning(f"File not found: {path}")
            return 0

        if not path.is_file():
            self._logger.warning(f"Not a file: {path}")
            return 0

        # Check if already indexed
        rel_path = str(path.relative_to(self.nexus_root) if path.is_relative_to(self.nexus_root) else path)

        if rel_path in self.indexed_files and not force:
            self._logger.debug(f"Already indexed: {rel_path}")
            return 0

        # Remove old chunks for this file if re-indexing
        if force and rel_path in self.indexed_files:
            self.forget(path)

        # Read file content
        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
        except Exception as e:
            self._logger.warning(f"Failed to read {path}: {e}")
            return 0

        # Skip empty or tiny files
        if len(content.strip()) < MIN_CHUNK_SIZE:
            return 0

        # Check global chunk limit
        if len(self.chunks) >= MAX_CHUNKS:
            self._logger.warning(f"Chunk limit reached ({MAX_CHUNKS}), skipping {rel_path}")
            return 0

        # Chunk based on file type
        suffix = path.suffix.lower()
        if suffix == ".py":
            new_chunks = self._chunk_python(content, rel_path)
        elif suffix == ".md":
            new_chunks = self._chunk_markdown(content, rel_path)
        else:
            new_chunks = self._chunk_by_lines(content, rel_path)

        # Add chunks and update index
        self.chunks.extend(new_chunks)
        self.indexed_files.add(rel_path)

        self._logger.info(f"Indexed {rel_path}: {len(new_chunks)} chunks")
        return len(new_chunks)

    def index_directory(
        self,
        path: Path,
        extensions: List[str] = None,
        recursive: bool = True
    ) -> int:
        """
        Index all files in a directory.

        Args:
            path: Directory path
            extensions: File extensions to include (default: DEFAULT_EXTENSIONS)
            recursive: Include subdirectories

        Returns:
            Total number of chunks created
        """
        if not path.is_absolute():
            path = self.nexus_root / path

        if not path.exists() or not path.is_dir():
            self._logger.warning(f"Directory not found: {path}")
            return 0

        extensions = extensions or DEFAULT_EXTENSIONS
        total_chunks = 0

        # Get files
        if recursive:
            files = path.rglob("*")
        else:
            files = path.glob("*")

        for file_path in files:
            # Skip excluded directories
            if any(excluded in file_path.parts for excluded in EXCLUDED_DIRS):
                continue

            # Skip non-matching extensions
            if file_path.suffix.lower() not in extensions:
                continue

            # Skip if at chunk limit
            if len(self.chunks) >= MAX_CHUNKS:
                self._logger.warning(f"Chunk limit reached ({MAX_CHUNKS})")
                break

            total_chunks += self.index_file(file_path)

        # Rebuild IDF after batch indexing
        self._rebuild_idf()
        self.save()

        return total_chunks

    # =========================================================================
    # Chunking Strategies
    # =========================================================================

    def _chunk_python(self, content: str, file_path: str) -> List[Chunk]:
        """
        Chunk Python file by function and class definitions.

        Uses regex to find def/class boundaries.
        """
        chunks = []
        lines = content.split("\n")

        # Pattern to match function/class definitions
        pattern = re.compile(r'^(class |def |async def )')

        current_chunk_start = 0
        current_chunk_name = None
        current_chunk_type = "module"

        for i, line in enumerate(lines):
            if pattern.match(line.lstrip()):
                # Save previous chunk if substantial
                if i > current_chunk_start:
                    chunk_content = "\n".join(lines[current_chunk_start:i])
                    if len(chunk_content.strip()) >= MIN_CHUNK_SIZE:
                        chunks.append(self._create_chunk(
                            file_path, current_chunk_start + 1, i,
                            chunk_content, current_chunk_type, current_chunk_name
                        ))

                # Start new chunk
                current_chunk_start = i
                stripped = line.lstrip()
                if stripped.startswith("class "):
                    current_chunk_type = "class"
                    match = re.match(r'class (\w+)', stripped)
                    current_chunk_name = match.group(1) if match else None
                else:
                    current_chunk_type = "function"
                    match = re.match(r'(?:async )?def (\w+)', stripped)
                    current_chunk_name = match.group(1) if match else None

        # Add final chunk
        if current_chunk_start < len(lines):
            chunk_content = "\n".join(lines[current_chunk_start:])
            if len(chunk_content.strip()) >= MIN_CHUNK_SIZE:
                chunks.append(self._create_chunk(
                    file_path, current_chunk_start + 1, len(lines),
                    chunk_content, current_chunk_type, current_chunk_name
                ))

        # If no functions/classes found, fall back to line chunking
        if not chunks:
            return self._chunk_by_lines(content, file_path)

        return chunks

    def _chunk_markdown(self, content: str, file_path: str) -> List[Chunk]:
        """
        Chunk Markdown file by section headers.

        Splits on # headers.
        """
        chunks = []
        lines = content.split("\n")

        # Pattern to match headers
        pattern = re.compile(r'^#{1,4} ')

        current_chunk_start = 0
        current_section_name = "Introduction"

        for i, line in enumerate(lines):
            if pattern.match(line):
                # Save previous chunk if substantial
                if i > current_chunk_start:
                    chunk_content = "\n".join(lines[current_chunk_start:i])
                    if len(chunk_content.strip()) >= MIN_CHUNK_SIZE:
                        chunks.append(self._create_chunk(
                            file_path, current_chunk_start + 1, i,
                            chunk_content, "section", current_section_name
                        ))

                # Start new section
                current_chunk_start = i
                current_section_name = line.lstrip("#").strip()

        # Add final chunk
        if current_chunk_start < len(lines):
            chunk_content = "\n".join(lines[current_chunk_start:])
            if len(chunk_content.strip()) >= MIN_CHUNK_SIZE:
                chunks.append(self._create_chunk(
                    file_path, current_chunk_start + 1, len(lines),
                    chunk_content, "section", current_section_name
                ))

        # If no sections found, fall back to line chunking
        if not chunks:
            return self._chunk_by_lines(content, file_path)

        return chunks

    def _chunk_by_lines(self, content: str, file_path: str) -> List[Chunk]:
        """
        Chunk file by fixed line count with overlap.

        Default strategy for non-Python/Markdown files.
        """
        chunks = []
        lines = content.split("\n")

        i = 0
        while i < len(lines):
            end = min(i + LINES_PER_CHUNK, len(lines))
            chunk_content = "\n".join(lines[i:end])

            if len(chunk_content.strip()) >= MIN_CHUNK_SIZE:
                chunks.append(self._create_chunk(
                    file_path, i + 1, end,
                    chunk_content, "lines", None
                ))

            # Move forward with overlap
            i += LINES_PER_CHUNK - LINES_OVERLAP
            if i + LINES_OVERLAP >= len(lines):
                break

        return chunks

    def _create_chunk(
        self,
        file_path: str,
        start_line: int,
        end_line: int,
        content: str,
        chunk_type: str,
        name: Optional[str]
    ) -> Chunk:
        """Create a chunk with precomputed terms."""
        # Truncate if too large
        if len(content) > MAX_CHUNK_SIZE:
            content = content[:MAX_CHUNK_SIZE] + "\n... [truncated]"

        # Extract terms for TF-IDF
        terms = self._extract_terms(content)

        return Chunk(
            file_path=file_path,
            start_line=start_line,
            end_line=end_line,
            content=content,
            terms=terms,
            chunk_type=chunk_type,
            name=name
        )

    def _extract_terms(self, text: str) -> Set[str]:
        """
        Extract searchable terms from text.

        Lowercase, alphanumeric only, remove common stopwords.
        """
        # Tokenize: lowercase, split on non-alphanumeric
        words = re.findall(r'[a-z_][a-z0-9_]*', text.lower())

        # Filter short words and common stopwords
        stopwords = {
            'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
            'could', 'should', 'may', 'might', 'must', 'shall', 'can',
            'to', 'of', 'in', 'for', 'on', 'with', 'at', 'by', 'from',
            'as', 'or', 'and', 'not', 'but', 'if', 'then', 'else',
            'this', 'that', 'it', 'its', 'self', 'none', 'true', 'false',
            'def', 'class', 'return', 'import', 'from', 'pass', 'raise'
        }

        return {w for w in words if len(w) > 2 and w not in stopwords}

    # =========================================================================
    # Retrieval
    # =========================================================================

    def retrieve(
        self,
        query: str,
        limit: int = 5,
        min_score: float = 0.05
    ) -> List[Chunk]:
        """
        Retrieve relevant chunks using TF-IDF weighted Jaccard similarity.

        Args:
            query: Search query
            limit: Maximum chunks to return
            min_score: Minimum similarity score threshold

        Returns:
            List of relevant chunks, sorted by score descending
        """
        if not self.chunks:
            return []

        # Extract query terms
        query_terms = self._extract_terms(query)
        if not query_terms:
            return []

        # Ensure IDF is built
        if not self.idf:
            self._rebuild_idf()

        # Score each chunk
        scored_chunks = []
        for chunk in self.chunks:
            score = self._score_chunk(query_terms, chunk.terms)
            if score >= min_score:
                scored_chunks.append((score, chunk))

        # Sort by score descending
        scored_chunks.sort(key=lambda x: x[0], reverse=True)

        # Return top chunks
        return [chunk for _, chunk in scored_chunks[:limit]]

    def _score_chunk(self, query_terms: Set[str], chunk_terms: Set[str]) -> float:
        """
        Calculate TF-IDF weighted Jaccard similarity.

        Score = sum(idf[term] for term in intersection) / sum(idf[term] for term in query)
        """
        intersection = query_terms & chunk_terms
        if not intersection:
            return 0.0

        # TF-IDF weighted score
        intersection_weight = sum(self.idf.get(term, 1.0) for term in intersection)
        query_weight = sum(self.idf.get(term, 1.0) for term in query_terms)

        if query_weight == 0:
            return 0.0

        return intersection_weight / query_weight

    def _rebuild_idf(self):
        """
        Rebuild Inverse Document Frequency scores.

        IDF(term) = log(N / (1 + df(term)))
        where N = total chunks, df = chunks containing term
        """
        if not self.chunks:
            self.idf = {}
            return

        # Count document frequency for each term
        df: Dict[str, int] = defaultdict(int)
        for chunk in self.chunks:
            for term in chunk.terms:
                df[term] += 1

        # Calculate IDF
        n = len(self.chunks)
        self.idf = {
            term: math.log(n / (1 + count))
            for term, count in df.items()
        }

    # =========================================================================
    # Management
    # =========================================================================

    def forget(self, path: Path) -> int:
        """
        Remove a file from the index.

        Args:
            path: File path to forget

        Returns:
            Number of chunks removed
        """
        if not path.is_absolute():
            path = self.nexus_root / path

        rel_path = str(path.relative_to(self.nexus_root) if path.is_relative_to(self.nexus_root) else path)

        if rel_path not in self.indexed_files:
            return 0

        # Remove chunks for this file
        original_count = len(self.chunks)
        self.chunks = [c for c in self.chunks if c.file_path != rel_path]
        removed = original_count - len(self.chunks)

        # Update tracking
        self.indexed_files.discard(rel_path)

        # Rebuild IDF
        self._rebuild_idf()
        self.save()

        self._logger.info(f"Forgot {rel_path}: {removed} chunks removed")
        return removed

    def clear(self):
        """Clear all indexed data."""
        self.chunks = []
        self.idf = {}
        self.indexed_files = set()
        self.save()
        self._logger.info("Project memory cleared")

    def get_stats(self) -> IndexStats:
        """Get statistics about the indexed project."""
        all_terms = set()
        for chunk in self.chunks:
            all_terms.update(chunk.terms)

        return IndexStats(
            total_files=len(self.indexed_files),
            total_chunks=len(self.chunks),
            total_terms=len(all_terms),
            indexed_at=datetime.now().isoformat(),
            storage_path=str(self.storage_path)
        )

    # =========================================================================
    # Persistence
    # =========================================================================

    def save(self):
        """Save index to disk."""
        data = {
            "version": "1.0",
            "indexed_at": datetime.now().isoformat(),
            "indexed_files": list(self.indexed_files),
            "chunks": [c.to_dict() for c in self.chunks],
            "idf": self.idf
        }

        try:
            self.storage_path.write_text(
                json.dumps(data, indent=2, ensure_ascii=False),
                encoding="utf-8"
            )
            self._logger.debug(f"Saved {len(self.chunks)} chunks to {self.storage_path}")
        except Exception as e:
            self._logger.error(f"Failed to save project memory: {e}")

    def _load(self):
        """Load index from disk."""
        if not self.storage_path.exists():
            self._logger.debug("No existing project memory found")
            return

        try:
            data = json.loads(self.storage_path.read_text(encoding="utf-8"))

            self.indexed_files = set(data.get("indexed_files", []))
            self.chunks = [Chunk.from_dict(c) for c in data.get("chunks", [])]
            self.idf = data.get("idf", {})

            self._logger.info(f"Loaded {len(self.chunks)} chunks from {self.storage_path}")
        except Exception as e:
            self._logger.warning(f"Failed to load project memory: {e}")
            self.chunks = []
            self.idf = {}
            self.indexed_files = set()

    # =========================================================================
    # Utilities
    # =========================================================================

    def format_chunks_for_context(self, chunks: List[Chunk], max_chars: int = 3000) -> str:
        """
        Format retrieved chunks for injection into agent context.

        Args:
            chunks: Chunks to format
            max_chars: Maximum total characters

        Returns:
            Formatted markdown string
        """
        if not chunks:
            return ""

        lines = ["## RELEVANT PROJECT KNOWLEDGE", ""]
        current_chars = 0

        for chunk in chunks:
            # Build chunk header
            header = f"### {chunk.file_path}"
            if chunk.name:
                header += f" - {chunk.chunk_type}: {chunk.name}"
            header += f" (L{chunk.start_line}-{chunk.end_line})"

            # Check size limit
            chunk_text = f"{header}\n```\n{chunk.content}\n```\n"
            if current_chars + len(chunk_text) > max_chars:
                break

            lines.append(chunk_text)
            current_chars += len(chunk_text)

        return "\n".join(lines)
