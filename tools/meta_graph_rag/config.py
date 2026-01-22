"""Configuration for the Meta GraphRAG system."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional
import os

from core.config import Config


DEFAULT_INCLUDE_DIRS = [
    "core",
    "interface",
    "tests",
    "scripts",
    "tools",
    "prompts",
    "audit",
    "PRODUCTS",
    "memory-bank",
    "docs",
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

DEFAULT_RESEARCH_QUERIES = [
    "Deep GraphRAG",
    "GraphRAG hierarchical retrieval",
    "GraphRAG security poisoning",
    "GraphRAG benchmark",
    "Agentic deep search GraphRAG",
    "Model Context Protocol MCP",
    "LLM evaluation harness",
]

DEFAULT_SOURCE_WEIGHTS = {
    "code": 1.0,
    "test": 0.9,
    "config": 0.85,
    "audit": 0.75,
    "product": 0.7,
    "doc": 0.6,
    "prompt": 0.55,
    "external": 0.6,
    "data": 0.7,
}


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
    graph_backend: str = "sqlite"
    graph_db_path: Path = Path("graph_db.sqlite")
    ssl_mode: str = "strict"
    ca_bundle_path: Optional[Path] = None
    include_dirs: List[str] = field(default_factory=lambda: DEFAULT_INCLUDE_DIRS.copy())
    exclude_dirs: List[str] = field(default_factory=lambda: DEFAULT_EXCLUDE_DIRS.copy())
    extensions: List[str] = field(default_factory=lambda: DEFAULT_EXTENSIONS.copy())
    max_file_size_kb: int = 512
    chunk_lines: int = 50
    chunk_overlap: int = 10
    embedding_backend: str = "gemini"
    embedding_model: str = "all-MiniLM-L6-v2"
    gemini_embedding_model: str = "gemini-embedding-001"
    gemini_embedding_dim: int = 3072
    gemini_task_type_document: str = "RETRIEVAL_DOCUMENT"
    gemini_task_type_query: str = "RETRIEVAL_QUERY"
    gemini_batch_size: int = 8
    gemini_generation_model: str = "gemini-3-pro-preview"
    gemini_api_key: Optional[str] = None
    query_seed_limit: int = 8
    query_expansion_depth: int = 1
    query_expansion_limit: int = 20
    research_limit: int = 5
    research_queries: List[str] = field(default_factory=lambda: DEFAULT_RESEARCH_QUERIES.copy())
    persist_every_files: int = 25
    source_weights: Dict[str, float] = field(default_factory=lambda: DEFAULT_SOURCE_WEIGHTS.copy())


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
    graph_backend = os.getenv("META_RAG_GRAPH_BACKEND", "sqlite").lower()
    graph_db_path = Path(os.getenv("META_RAG_GRAPH_PATH", data_path / "graph_db.sqlite"))
    ssl_mode = os.getenv("META_RAG_SSL_MODE", "strict").lower()
    ca_bundle = (
        os.getenv("META_RAG_CA_BUNDLE")
        or os.getenv("SSL_CERT_FILE")
        or os.getenv("REQUESTS_CA_BUNDLE")
        or os.getenv("CURL_CA_BUNDLE")
    )
    ca_bundle_path = Path(ca_bundle) if ca_bundle else None

    embedding_backend = os.getenv("META_RAG_EMBEDDINGS", "gemini").lower()
    embedding_model = os.getenv("META_RAG_EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    gemini_embedding_model = os.getenv("META_RAG_GEMINI_EMBED_MODEL", "gemini-embedding-001")
    gemini_embedding_dim = int(os.getenv("META_RAG_GEMINI_EMBED_DIM", "3072"))
    gemini_task_type_document = os.getenv("META_RAG_GEMINI_TASK_DOC", "RETRIEVAL_DOCUMENT")
    gemini_task_type_query = os.getenv("META_RAG_GEMINI_TASK_QUERY", "RETRIEVAL_QUERY")
    gemini_generation_model = os.getenv("META_RAG_GEMINI_MODEL", "gemini-3-pro-preview")
    gemini_api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    gemini_batch_size = int(os.getenv("META_RAG_GEMINI_BATCH", "8"))

    max_file_size_kb = int(os.getenv("META_RAG_MAX_FILE_KB", "512"))
    chunk_lines = int(os.getenv("META_RAG_CHUNK_LINES", "50"))
    chunk_overlap = int(os.getenv("META_RAG_CHUNK_OVERLAP", "10"))

    query_seed_limit = int(os.getenv("META_RAG_QUERY_SEEDS", "8"))
    query_expansion_depth = int(os.getenv("META_RAG_QUERY_DEPTH", "1"))
    query_expansion_limit = int(os.getenv("META_RAG_QUERY_EXPANSION", "20"))
    research_limit = int(os.getenv("META_RAG_RESEARCH_LIMIT", "5"))
    research_queries = _parse_env_list("META_RAG_RESEARCH_QUERIES", DEFAULT_RESEARCH_QUERIES)
    persist_every_files = int(os.getenv("META_RAG_PERSIST_EVERY", "25"))
    source_weights = _parse_source_weights("META_RAG_SOURCE_WEIGHTS", DEFAULT_SOURCE_WEIGHTS)

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
        graph_backend=graph_backend,
        graph_db_path=graph_db_path,
        ssl_mode=ssl_mode,
        ca_bundle_path=ca_bundle_path,
        include_dirs=include_dirs,
        exclude_dirs=exclude_dirs,
        extensions=extensions,
        max_file_size_kb=max_file_size_kb,
        chunk_lines=chunk_lines,
        chunk_overlap=chunk_overlap,
        embedding_backend=embedding_backend,
        embedding_model=embedding_model,
        gemini_embedding_model=gemini_embedding_model,
        gemini_embedding_dim=gemini_embedding_dim,
        gemini_task_type_document=gemini_task_type_document,
        gemini_task_type_query=gemini_task_type_query,
        gemini_batch_size=gemini_batch_size,
        gemini_generation_model=gemini_generation_model,
        gemini_api_key=gemini_api_key,
        query_seed_limit=query_seed_limit,
        query_expansion_depth=query_expansion_depth,
        query_expansion_limit=query_expansion_limit,
        research_limit=research_limit,
        research_queries=research_queries,
        persist_every_files=persist_every_files,
        source_weights=source_weights,
    )


def _parse_env_list(key: str, default: List[str]) -> List[str]:
    raw = os.getenv(key)
    if not raw:
        return default.copy()
    parts = [part.strip() for part in raw.split(",")]
    return [part for part in parts if part]


def _parse_source_weights(key: str, default: Dict[str, float]) -> Dict[str, float]:
    raw = os.getenv(key)
    if not raw:
        return default.copy()
    mapping: Dict[str, float] = {}
    for item in raw.split(","):
        item = item.strip()
        if not item or ":" not in item:
            continue
        label, value = item.split(":", 1)
        label = label.strip()
        try:
            mapping[label] = float(value.strip())
        except ValueError:
            continue
    return mapping or default.copy()
