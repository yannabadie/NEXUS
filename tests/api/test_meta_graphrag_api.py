"""
Meta GraphRAG API validation and caching tests.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from pydantic import ValidationError

import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


def test_query_validation_rejects_oversized_query():
    """Query length should be capped."""
    from core.api.cerebro.routes import meta_graphrag

    query = "x" * (meta_graphrag.MAX_QUERY_LENGTH + 1)
    with pytest.raises(ValidationError):
        meta_graphrag.GraphRagQueryRequest(query=query)


def test_entrypoints_validation_rejects_too_many():
    """Entrypoints list should be capped."""
    from core.api.cerebro.routes import meta_graphrag

    entrypoints = [f"module_{i}" for i in range(meta_graphrag.MAX_ENTRYPOINTS + 1)]
    with pytest.raises(ValidationError):
        meta_graphrag.ReportsRequest(entrypoints=entrypoints)


def test_reports_cache_hits(monkeypatch, tmp_path):
    """Reports should be cached between identical calls."""
    from core.api.cerebro.routes import meta_graphrag
    import tools.meta_graph_rag.config as config_module
    import tools.meta_graph_rag.snapshot as snapshot_module
    import tools.meta_graph_rag.reports as reports_module

    meta_graphrag._REPORT_CACHE.clear()

    @dataclass
    class DummyConfig:
        reports_path: Path

    @dataclass
    class DummySnapshot:
        graph: object
        chunks: int
        vector_entries: int

    class DummyPaths:
        def __init__(self, base: Path) -> None:
            self.overview = base / "overview.md"
            self.top_down = base / "top_down.md"
            self.bottom_up = base / "bottom_up.md"
            self.security = base / "security.md"
            self.module_catalog = base / "module_catalog.md"

    def fake_load_config():
        return DummyConfig(reports_path=tmp_path)

    def fake_load_snapshot(config):
        return DummySnapshot(graph=MagicMock(), chunks=1, vector_entries=1)

    calls = {"count": 0}

    def fake_generate_reports(graph, chunks_count, vector_count, output_dir, entrypoints=None):
        calls["count"] += 1
        paths = DummyPaths(output_dir)
        for path in [
            paths.overview,
            paths.top_down,
            paths.bottom_up,
            paths.security,
            paths.module_catalog,
        ]:
            path.write_text("content", encoding="utf-8")
        return paths

    monkeypatch.setattr(config_module, "load_config", fake_load_config)
    monkeypatch.setattr(snapshot_module, "load_snapshot", fake_load_snapshot)
    monkeypatch.setattr(reports_module, "generate_reports", fake_generate_reports)

    payload1 = meta_graphrag._build_meta_graphrag_reports(
        entrypoints=["core"],
        include_content=True,
        fast=True,
    )
    payload2 = meta_graphrag._build_meta_graphrag_reports(
        entrypoints=["core"],
        include_content=True,
        fast=True,
    )

    assert calls["count"] == 1
    assert payload1["cache"]["hit"] is False
    assert payload2["cache"]["hit"] is True
