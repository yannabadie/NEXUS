import json
from pathlib import Path

import pytest

from nexus_research import run_research


def _write_sample_doc(root: Path) -> Path:
    docs_dir = root / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)
    content = (
        "# Sample Guide\n"
        "This guide explains how the memory index builds evidence packs for NEXUS.\n"
        "Use the research CLI to search local files and produce a report.\n"
        "Evidence pack outputs include report, sources, trace, and graph artifacts.\n"
    )
    file_path = docs_dir / "guide.md"
    file_path.write_text(content, encoding="utf-8")
    return file_path


def test_run_research_writes_evidence_pack(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    sample_file = _write_sample_doc(root)
    output_dir = tmp_path / "out"

    outputs = run_research(
        question="How does the evidence pack get generated?",
        root_path=root,
        output_dir=output_dir,
        mode="mock",
        backend="tfidf",
        paths=[str(sample_file)],
        limit=3,
        min_score=0.0,
    )

    assert outputs["output_dir"] == output_dir
    for key in ("report", "sources", "trace", "graph", "manifest"):
        assert outputs[key].exists()

    report_text = outputs["report"].read_text(encoding="utf-8")
    assert "How does the evidence pack get generated?" in report_text
    assert "Mode: mock" in report_text

    sources_payload = json.loads(outputs["sources"].read_text(encoding="utf-8"))
    assert sources_payload["question"] == "How does the evidence pack get generated?"
    assert sources_payload["mode"] == "mock"
    assert str(sample_file) in sources_payload["index_paths"]
    assert sources_payload["indexed_chunks"] >= 1
    assert sources_payload["sources"]
    first_source_path = Path(sources_payload["sources"][0]["file_path"]).as_posix()
    assert first_source_path == "docs/guide.md"

    trace_lines = outputs["trace"].read_text(encoding="utf-8").splitlines()
    assert len(trace_lines) >= 3

    graph_text = outputs["graph"].read_text(encoding="utf-8").replace("\\", "/")
    assert "graph TD" in graph_text
    assert "docs/guide.md" in graph_text

    manifest_lines = outputs["manifest"].read_text(encoding="utf-8").splitlines()
    assert len(manifest_lines) == 4


def test_run_research_rejects_empty_question(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="Question cannot be empty"):
        run_research("   ", root_path=tmp_path, output_dir=tmp_path / "out")


def test_run_research_rejects_invalid_mode(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="Unsupported mode"):
        run_research(
            "What is indexed?",
            root_path=tmp_path,
            output_dir=tmp_path / "out",
            mode="cloud",
        )
