"""Configuration for the Meta GraphRAG system."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional
import os

from core.config import Config


DEFAULT_INCLUDE_DIRS = [
    "core",
    "interface",
    "docs",
    "tests",
    "scripts",
    "tools",
    "prompts",
    "audit",
    "PRODUCTS",
    "memory-bank",
]

DEFAULT_EXCLUDE_DIRS = [
    "__pycache__",
    ".git",
    ".nexus",
    ".venv",
    "venv",
    "archive",
    "archives",
    "logs",
    "workspace",
    "workspace_archive",
    ".pytest_cache",
    "node_modules",
    "dist",
    "build",
]

DEFAULT_EXTENSIONS = [
    ".py",
    ".md",
    ".txt",
    ".json",
    ".jsonl",
    ".yaml",
    ".yml",
    ".toml",
    ".ini",
    ".ps1",
    ".bat",
    ".sh",
]


@dataclass(frozen=True)
class MetaGraphRagConfig:
    """Configuration for meta GraphRAG indexing and retrieval."""

    root_path: Path
    workspace_path: Path
    data_path: Path
    graph_path: Path
    chunks_path: Path
    vector_path: Path
    manifest_path: Path
    reports_path: Path
    sources_path: Path
    include_dirs: List[str] = field(default_factory=lambda: DEFAULT_INCLUDE_DIRS.copy())
    exclude_dirs: List[str] = field(default_factory=lambda: DEFAULT_EXCLUDE_DIRS.copy())
    extensions: List[str] = field(default_factory=lambda: DEFAULT_EXTENSIONS.copy())
    max_file_size_kb: int = 512
    chunk_lines: int = 50
    chunk_overlap: int = 10
    embedding_backend: str = "auto"
    embedding_model: str = "all-MiniLM-L6-v2"
    gemini_embedding_model: str = "text-embedding-004"
    gemini_batch_size: int = 8
    gemini_api_key: Optional[str] = None
    query_seed_limit: int = 8
    query_expansion_depth: int = 1
    query_expansion_limit: int = 20


def load_config(
    root_path: Optional[Path] = None,
    workspace_path: Optional[Path] = None,
) -> MetaGraphRagConfig:
    """Load configuration using core Config and environment variables."""
    config = Config()
    root = root_path or config.nexus_root
    workspace = workspace_path or config.workspace_path

    data_path = Path(os.getenv("META_RAG_DATA_PATH", workspace / "meta_rag"))
    graph_path = data_path / "graph.json"
    chunks_path = data_path / "chunks.jsonl"
    vector_path = data_path / "vector_index.json"
    manifest_path = data_path / "index_manifest.json"
    reports_path = data_path / "reports"
    sources_path = data_path / "sources"

    embedding_backend = os.getenv("META_RAG_EMBEDDINGS", "auto").lower()
    embedding_model = os.getenv("META_RAG_EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    gemini_embedding_model = os.getenv("META_RAG_GEMINI_EMBED_MODEL", "text-embedding-004")
    gemini_api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    gemini_batch_size = int(os.getenv("META_RAG_GEMINI_BATCH", "8"))

    max_file_size_kb = int(os.getenv("META_RAG_MAX_FILE_KB", "512"))
    chunk_lines = int(os.getenv("META_RAG_CHUNK_LINES", "50"))
    chunk_overlap = int(os.getenv("META_RAG_CHUNK_OVERLAP", "10"))

    query_seed_limit = int(os.getenv("META_RAG_QUERY_SEEDS", "8"))
    query_expansion_depth = int(os.getenv("META_RAG_QUERY_DEPTH", "1"))
    query_expansion_limit = int(os.getenv("META_RAG_QUERY_EXPANSION", "20"))

    include_dirs = _parse_env_list("META_RAG_INCLUDE", DEFAULT_INCLUDE_DIRS)
    exclude_dirs = _parse_env_list("META_RAG_EXCLUDE", DEFAULT_EXCLUDE_DIRS)
    extensions = _parse_env_list("META_RAG_EXTENSIONS", DEFAULT_EXTENSIONS)

    return MetaGraphRagConfig(
        root_path=Path(root).resolve(),
        workspace_path=Path(workspace).resolve(),
        data_path=Path(data_path),
        graph_path=graph_path,
        chunks_path=chunks_path,
        vector_path=vector_path,
        manifest_path=manifest_path,
        reports_path=reports_path,
        sources_path=sources_path,
        include_dirs=include_dirs,
        exclude_dirs=exclude_dirs,
        extensions=extensions,
        max_file_size_kb=max_file_size_kb,
        chunk_lines=chunk_lines,
        chunk_overlap=chunk_overlap,
        embedding_backend=embedding_backend,
        embedding_model=embedding_model,
        gemini_embedding_model=gemini_embedding_model,
        gemini_batch_size=gemini_batch_size,
        gemini_api_key=gemini_api_key,
        query_seed_limit=query_seed_limit,
        query_expansion_depth=query_expansion_depth,
        query_expansion_limit=query_expansion_limit,
    )


def _parse_env_list(key: str, default: List[str]) -> List[str]:
    raw = os.getenv(key)
    if not raw:
        return default.copy()
    parts = [part.strip() for part in raw.split(",")]
    return [part for part in parts if part]
