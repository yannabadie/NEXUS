from pathlib import Path

from core.mcp import server as mcp_server


def _write_sample_doc(root: Path) -> Path:
    docs_dir = root / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)
    content = (
        "# Sample Guide\n"
        "This guide explains how evidence packs are generated from local files.\n"
        "Use MCP to search project memory and export structured artifacts.\n"
    )
    file_path = docs_dir / "guide.md"
    file_path.write_text(content, encoding="utf-8")
    return file_path


def test_build_memory_search_returns_sources(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    sample_file = _write_sample_doc(root)

    payload = mcp_server.build_memory_search(
        query="evidence packs",
        root_path=root,
        mode="mock",
        backend="tfidf",
        limit=3,
        min_score=0.0,
        paths=[str(sample_file)],
    )

    assert payload["sources"]
    first_path = Path(payload["sources"][0]["file_path"]).as_posix()
    assert first_path == "docs/guide.md"
    assert payload["indexed_chunks"] >= 1


def test_build_evidence_pack_outputs_artifacts(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    sample_file = _write_sample_doc(root)
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    output_dir = workspace / "evidence_pack"

    outputs = mcp_server.build_evidence_pack(
        question="What does the guide describe?",
        root_path=root,
        workspace_path=workspace,
        output_dir=str(output_dir),
        mode="mock",
        backend="tfidf",
        limit=3,
        min_score=0.0,
        paths=[str(sample_file)],
    )

    report_path = Path(outputs["report"])
    sources_path = Path(outputs["sources"])
    trace_path = Path(outputs["trace"])
    graph_path = Path(outputs["graph"])
    manifest_path = Path(outputs["manifest"])

    assert report_path.exists()
    assert sources_path.exists()
    assert trace_path.exists()
    assert graph_path.exists()
    assert manifest_path.exists()

    report_text = report_path.read_text(encoding="utf-8")
    assert "What does the guide describe?" in report_text
