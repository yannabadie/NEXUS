"""
NEXUS V7.9 - Project Memory RAG (Phase 10c + 10e + 10f + 10g)

Persistent project knowledge base with pluggable retrieval backends.
Stores indexed code and documentation for context-aware responses.

Architecture:
- Storage: .nexus/project_knowledge.json (at NEXUS_ROOT, NOT in workspace/)
- Persistence: Survives /workspace new (workspace is session, memory is project)
- Sharing: All agents (Gemini, Claude, spawned) share the same factual knowledge

Chunking Strategy:
- .py files: Split by function/class definitions
- .md files: Split by sections (headers)
- Other files: Split by lines (50 lines, 10 overlap)

Backend Architecture (V7.9 Phase 10f + 10g):
- SEMANTIC: Dense embeddings (LanceDB + Sentence-Transformers) - ~+10% recall
- LEXICAL: BM25S sparse retrieval (if installed) - ~15% better than TF-IDF
- FALLBACK: TF-IDF weighted Jaccard similarity (built-in, no dependencies)
- Pluggable: MemoryBackend ABC allows future backends (Hybrid, etc.)

Environment: PROJECT_MEMORY_BACKEND = "auto" | "dense" | "bm25" | "tfidf"

Usage:
    memory = ProjectMemory(nexus_root)
    memory.index_file(Path("core/orchestration_v7.py"))
    chunks = memory.retrieve("FSM state handling", limit=5)

    # Check which backend is active
    print(memory.get_backend_info())  # {"backend": "dense", ...}
"""

import json
import re
import logging
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Set, Optional, Any

# V7.9 Phase 10f/10g: Import from modular types and backends
from .types import Chunk, IndexStats
from .backends import (
    MemoryBackend, TfidfBackend, Bm25Backend, DenseBackend,
    BM25S_AVAILABLE, STEMMER_AVAILABLE, LANCEDB_AVAILABLE, SENTENCE_TRANSFORMERS_AVAILABLE
)


# =============================================================================
# Configuration
# =============================================================================

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
# ProjectMemory Class (Facade)
# =============================================================================

class ProjectMemory:
    """
    Persistent project knowledge base for NEXUS.

    Indexes code and documentation with pluggable retrieval backends:
    - PRIMARY: BM25S sparse retrieval (if installed) - better recall
    - FALLBACK: TF-IDF weighted Jaccard similarity (built-in)

    Key Design Decisions:
    - Stored at NEXUS_ROOT/.nexus/project_knowledge.json (not in workspace/)
    - Shared by all agents (factual knowledge is universal)
    - Survives /workspace new (memory persists across sessions)

    Phase 10c: V7.8 HIVE MIND (TF-IDF)
    Phase 10e: V7.8.2 (BM25S upgrade)
    Phase 10f: V7.9 (Backend abstraction)
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
        self.indexed_files: Set[str] = set()

        # V7.9 Phase 10f: Backend abstraction
        self._backend: MemoryBackend = self._select_backend()
        self._backend_dirty: bool = True  # Backend index needs rebuild

        # Legacy: Keep idf for backward compatibility with saved data
        self.idf: Dict[str, float] = {}

        # Ensure storage directory exists
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        # Load existing index
        self._load()

    def _select_backend(self) -> MemoryBackend:
        """
        Select the best available backend.

        V7.9 Phase 10g: Supports Dense embeddings backend.

        Environment variable PROJECT_MEMORY_BACKEND controls selection:
        - "auto" (default): Best available (Dense > BM25S > TF-IDF)
        - "dense": Force dense embeddings (fallback if unavailable)
        - "bm25": Force BM25S (fallback if unavailable)
        - "tfidf": Force TF-IDF (always available)

        Returns:
            MemoryBackend instance
        """
        backend_pref = os.getenv("PROJECT_MEMORY_BACKEND", "auto").lower()
        lancedb_path = self.storage_dir / "lancedb"

        # Explicit preference
        if backend_pref == "dense":
            # V9.0: Check UniversalIO availability too
            from ..io.universal_io import UniversalIO
            if DenseBackend.is_available() or UniversalIO.is_available():
                self._logger.info("Using Dense backend (semantic search)")
                return DenseBackend(lancedb_path)
            else:
                self._logger.warning("Dense backend requested but unavailable (needs lancedb + litellm/sentence-transformers), falling back")

        elif backend_pref == "bm25":
            if Bm25Backend.is_available():
                self._logger.info("Using BM25S backend (requested)")
                return Bm25Backend()
            else:
                self._logger.warning("BM25S backend requested but unavailable, falling back")

        elif backend_pref == "tfidf":
            self._logger.info("Using TF-IDF backend (requested)")
            return TfidfBackend()

        # Auto selection: Dense > BM25S > TF-IDF
        from ..io.universal_io import UniversalIO
        if DenseBackend.is_available() or (LANCEDB_AVAILABLE and UniversalIO.is_available()):
            self._logger.info("Using Dense backend (semantic search, best recall)")
            return DenseBackend(lancedb_path)
        elif Bm25Backend.is_available():
            self._logger.info("Using BM25S backend (lexical, +15% vs TF-IDF)")
            return Bm25Backend()
        else:
            self._logger.info("Using TF-IDF backend (fallback, stdlib only)")
            return TfidfBackend()

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
        self._backend_dirty = True  # Mark backend index for rebuild

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

        # Rebuild backend index after batch indexing
        self._rebuild_backend_index()
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

        # Extract terms for retrieval
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
    # Retrieval (V7.9 Phase 10f: Backend Abstraction)
    # =========================================================================

    def _rebuild_backend_index(self):
        """Rebuild the backend's retrieval index."""
        if not self.chunks:
            self._backend.clear()
            self._backend_dirty = False
            return

        try:
            self._backend.build_index(self.chunks)
            self._backend_dirty = False
            self._logger.debug(f"Backend index rebuilt: {len(self.chunks)} chunks")
        except Exception as e:
            self._logger.warning(f"Backend index build failed: {e}")
            self._backend_dirty = False

    def retrieve(
        self,
        query: str,
        limit: int = 5,
        min_score: float = 0.05
    ) -> List[Chunk]:
        """
        Retrieve relevant chunks using the active backend.

        V7.9 Phase 10f/10g: Uses pluggable backend architecture.
        Priority: Dense (semantic) > BM25S (lexical) > TF-IDF (fallback)

        Args:
            query: Search query (raw string)
            limit: Maximum chunks to return
            min_score: Minimum similarity score threshold

        Returns:
            List of relevant chunks, sorted by score descending
        """
        if not self.chunks:
            return []

        # Lazy rebuild backend index if needed
        if self._backend_dirty:
            self._rebuild_backend_index()

        # Extract query terms (for sparse backends)
        query_terms = self._extract_terms(query)

        # Dense backend can work with raw_query even if no terms extracted
        # Sparse backends need terms
        if not query_terms and not isinstance(self._backend, DenseBackend):
            return []

        # Use backend for retrieval
        # V7.9 Phase 10g: Pass raw_query for dense backends
        try:
            results = self._backend.retrieve(
                list(query_terms) if query_terms else [],
                self.chunks,
                limit,
                min_score,
                raw_query=query  # For dense/semantic backends
            )

            # If primary backend returns empty, try fallback
            if not results and not isinstance(self._backend, TfidfBackend):
                # Fallback to TF-IDF
                if query_terms:  # Only if we have terms for sparse search
                    fallback = TfidfBackend()
                    fallback.build_index(self.chunks)
                    results = fallback.retrieve(
                        list(query_terms), self.chunks, limit, min_score, raw_query=query
                    )

            return results

        except Exception as e:
            self._logger.warning(f"Retrieve failed: {e}")
            return []

    def get_backend_info(self) -> Dict[str, Any]:
        """
        Get information about the active retrieval backend.

        Returns:
            Dict with backend name and status
        """
        info = self._backend.get_info()
        info["chunks_indexed"] = len(self.chunks)
        info["bm25s_available"] = BM25S_AVAILABLE
        info["stemmer_available"] = STEMMER_AVAILABLE
        return info

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

        # Mark backend for rebuild
        self._backend_dirty = True
        self.save()

        self._logger.info(f"Forgot {rel_path}: {removed} chunks removed")
        return removed

    def clear(self):
        """Clear all indexed data."""
        self.chunks = []
        self.idf = {}  # Legacy
        self.indexed_files = set()
        self._backend.clear()
        self._backend_dirty = False
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

    def get_all_vectors(self) -> List[Dict[str, Any]]:
        """
        Get all vectors from the backend (if supported).
        """
        if hasattr(self._backend, "get_all_vectors"):
            return self._backend.get_all_vectors()
        return []

    # =========================================================================
    # Persistence
    # =========================================================================

    def save(self):
        """Save index to disk."""
        data = {
            "version": "1.1",  # V7.9: Bump version for backend abstraction
            "indexed_at": datetime.now().isoformat(),
            "indexed_files": list(self.indexed_files),
            "chunks": [c.to_dict() for c in self.chunks],
            "idf": self.idf  # Legacy: keep for backward compatibility
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
            self.idf = data.get("idf", {})  # Legacy

            # Mark backend for rebuild after load
            self._backend_dirty = True

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
