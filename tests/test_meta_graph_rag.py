"""Tests for Meta GraphRAG indexing and querying."""

from __future__ import annotations

from pathlib import Path

from tools.meta_graph_rag import MetaGraphIndexer, load_config


def test_meta_graph_rag_index_and_query(tmp_path, monkeypatch):
    root = tmp_path / "repo"
    workspace = tmp_path / "workspace"
    root.mkdir()
    workspace.mkdir()

    sample = root / "sample.py"
    sample.write_text(
        """

def add(a, b):
    return a + b

class Greeter:
    def greet(self, name):
        return f"Hello {name}"
""",
        encoding="utf-8",
    )

    monkeypatch.setenv("META_RAG_EMBEDDINGS", "hash")
    config = load_config(root_path=root, workspace_path=workspace)
    indexer = MetaGraphIndexer(config)
    indexer.index(full=True)

    status = indexer.status()
    assert status["nodes"] >= 2
    assert status["chunks"] >= 1

    result = indexer.query("add function")
    assert result.seed_chunks


def test_meta_graph_rag_reports(tmp_path, monkeypatch):
    root = tmp_path / "repo"
    workspace = tmp_path / "workspace"
    root.mkdir()
    workspace.mkdir()

    sample = root / "module.md"
    sample.write_text("# Title\n\nSome content\n", encoding="utf-8")

    monkeypatch.setenv("META_RAG_EMBEDDINGS", "hash")
    config = load_config(root_path=root, workspace_path=workspace)
    indexer = MetaGraphIndexer(config)
    indexer.index(full=True)

    from tools.meta_graph_rag.reports import generate_reports

    status = indexer.status()
    paths = generate_reports(
        graph=indexer.graph,
        chunks_count=status["chunks"],
        vector_count=status["vector_entries"],
        output_dir=config.reports_path,
    )

    assert paths.overview.exists()
    assert paths.top_down.exists()
    assert paths.bottom_up.exists()
    assert paths.security.exists()
    assert paths.module_catalog.exists()
