"""Lightweight status snapshot helpers for Meta GraphRAG."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Tuple

from .config import MetaGraphRagConfig
from .graph import GraphStore
from .graph_db import GraphDatabase
from .indexer import IndexManifest


@dataclass(frozen=True)
class GraphRagSnapshot:
    graph: GraphStore
    chunks: int
    vector_entries: int
    manifest_generated_at: str
    embedding_backend: Dict[str, str]
    graph_db: Dict[str, object]


def load_snapshot(config: MetaGraphRagConfig) -> GraphRagSnapshot:
    graph = GraphStore.load(config.graph_path)
    manifest = IndexManifest.load(config.manifest_path)
    chunks = _count_chunks(manifest, config.chunks_path)
    vector_entries = chunks
    graph_db = GraphDatabase(config.graph_db_path, backend=config.graph_backend).status()
    return GraphRagSnapshot(
        graph=graph,
        chunks=chunks,
        vector_entries=vector_entries,
        manifest_generated_at=manifest.generated_at,
        embedding_backend=_embedding_info_from_config(config),
        graph_db=graph_db,
    )


def _count_chunks(manifest: IndexManifest, chunks_path: Path) -> int:
    count = 0
    for entry in manifest.files.values():
        chunks = entry.get("chunks", [])
        if isinstance(chunks, list):
            count += len(chunks)
    if count:
        return count
    if not chunks_path.exists():
        return 0
    with chunks_path.open("r", encoding="utf-8") as handle:
        return sum(1 for line in handle if line.strip())


def _embedding_info_from_config(config: MetaGraphRagConfig) -> Dict[str, str]:
    backend = config.embedding_backend
    info: Dict[str, str] = {"backend": backend}
    if backend == "gemini":
        info["model"] = config.gemini_embedding_model
        info["dim"] = str(config.gemini_embedding_dim)
    elif backend in {"sentence", "sentence-transformers", "auto"}:
        info["model"] = config.embedding_model
    return info
