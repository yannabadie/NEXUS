"""
NEXUS Research CLI - Evidence Pack Generator (Mock/Local).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from core.config import Config
from core.memory.project_memory import ProjectMemory


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _iso_now() -> str:
    return _utc_now().isoformat()


def _hash_file(path: Path) -> str:
    sha = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8192), b""):
            sha.update(chunk)
    return sha.hexdigest()


def _resolve_path(root: Path, raw_path: str) -> Path:
    path = Path(raw_path)
    return path if path.is_absolute() else root / path


def _default_index_paths(root: Path) -> List[Path]:
    candidates = []
    for name in ("core", "docs"):
        candidate = root / name
        if candidate.exists():
            candidates.append(candidate)
    return candidates or [root]


def _init_memory(root: Path, backend: str) -> ProjectMemory:
    previous_backend = os.environ.get("PROJECT_MEMORY_BACKEND")
    os.environ["PROJECT_MEMORY_BACKEND"] = backend
    try:
        return ProjectMemory(root)
    finally:
        if previous_backend is None:
            os.environ.pop("PROJECT_MEMORY_BACKEND", None)
        else:
            os.environ["PROJECT_MEMORY_BACKEND"] = previous_backend


def _write_report(
    path: Path,
    question: str,
    mode: str,
    backend: str,
    source_summaries: List[str],
    generated_at: str,
) -> None:
    lines = [
        "# Research Report",
        "",
        f"Question: {question}",
        f"Mode: {mode}",
        f"Backend: {backend}",
        f"Generated: {generated_at}",
        "",
        "Summary:",
    ]

    if source_summaries:
        for summary in source_summaries:
            lines.append(f"- {summary}")
    else:
        lines.append("- No sources matched the query at the current threshold.")

    lines.extend([
        "",
        "Notes:",
        "- This report was generated in mock/local mode using on-disk project data.",
        "- No external network calls or API keys were required.",
    ])

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_sources(path: Path, payload: Dict[str, object]) -> None:
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=True),
        encoding="utf-8",
    )


def _write_metrics(path: Path, payload: Dict[str, object]) -> None:
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=True),
        encoding="utf-8",
    )


def _write_trace(path: Path, events: List[Dict[str, object]]) -> None:
    lines = [json.dumps(event, ensure_ascii=True) for event in events]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_reasoning_graph(path: Path, question: str, sources: List[Dict[str, object]]) -> None:
    lines = ["graph TD", '  Q["Question"]']
    for idx, source in enumerate(sources, start=1):
        label = str(source.get("file_path", "source")).replace('"', "'")
        lines.append(f'  Q --> S{idx}["{label}"]')
        lines.append(f'  S{idx} --> R["Report"]')
    if not sources:
        lines.append('  Q --> R["Report"]')
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_manifest(path: Path, files: List[Path]) -> None:
    lines = []
    for file_path in files:
        digest = _hash_file(file_path)
        lines.append(f"{digest}  {file_path.name}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_research(
    question: str,
    root_path: Optional[Path] = None,
    output_dir: Optional[Path] = None,
    mode: str = "mock",
    backend: Optional[str] = None,
    limit: int = 5,
    min_score: float = 0.2,
    paths: Optional[List[str]] = None,
) -> Dict[str, Path]:
    if not question or not question.strip():
        raise ValueError("Question cannot be empty.")

    start_time = time.perf_counter()

    config = Config()
    root = Path(root_path) if root_path else config.nexus_root
    root = root.resolve()

    output_dir = Path(output_dir) if output_dir else (
        config.workspace_path / "research" / _utc_now().strftime("%Y%m%d_%H%M%S")
    )
    output_dir.mkdir(parents=True, exist_ok=True)

    mode = mode.lower()
    if mode not in {"mock", "local"}:
        raise ValueError(f"Unsupported mode: {mode}. Use 'mock' or 'local'.")

    backend = backend or ("tfidf" if mode == "mock" else "auto")
    memory = _init_memory(root, backend)

    index_paths = [_resolve_path(root, p) for p in paths] if paths else _default_index_paths(root)

    indexed_chunks = 0
    for path in index_paths:
        if path.is_dir():
            indexed_chunks += memory.index_directory(path)
        elif path.is_file():
            indexed_chunks += memory.index_file(path)

    results = memory.retrieve(question, limit=limit, min_score=min_score)

    sources = []
    for chunk in results:
        sources.append({
            "file_path": chunk.file_path,
            "start_line": chunk.start_line,
            "end_line": chunk.end_line,
            "chunk_type": chunk.chunk_type,
            "name": chunk.name,
            "terms": sorted(chunk.terms),
            "excerpt": chunk.content.strip()[:400],
        })

    backend_info = memory.get_backend_info()
    backend_name = backend_info.get("backend", backend)
    generated_at = _iso_now()

    report_path = output_dir / "report.md"
    sources_path = output_dir / "sources.json"
    trace_path = output_dir / "trace.jsonl"
    graph_path = output_dir / "reasoning_graph.mmd"
    metrics_path = output_dir / "metrics.json"
    manifest_path = output_dir / "manifest.sha256"

    source_summaries = [
        f"{source['file_path']} (L{source['start_line']}-{source['end_line']})"
        for source in sources
    ]

    _write_report(
        report_path,
        question=question,
        mode=mode,
        backend=backend_name,
        source_summaries=source_summaries,
        generated_at=generated_at,
    )

    _write_sources(
        sources_path,
        {
            "question": question,
            "mode": mode,
            "backend": backend_name,
            "generated_at": generated_at,
            "root_path": str(root),
            "index_paths": [str(p) for p in index_paths],
            "indexed_chunks": indexed_chunks,
            "sources": sources,
        },
    )

    duration_ms = int((time.perf_counter() - start_time) * 1000)
    _write_metrics(
        metrics_path,
        {
            "question": question,
            "mode": mode,
            "backend": backend_name,
            "generated_at": generated_at,
            "indexed_chunks": indexed_chunks,
            "source_count": len(sources),
            "duration_ms": duration_ms,
        },
    )

    trace_events = [
        {
            "ts": generated_at,
            "event": "start",
            "detail": {"mode": mode, "backend": backend_name},
        },
        {
            "ts": _iso_now(),
            "event": "index",
            "detail": {"paths": [str(p) for p in index_paths], "chunks": indexed_chunks},
        },
        {
            "ts": _iso_now(),
            "event": "retrieve",
            "detail": {"limit": limit, "min_score": min_score, "results": len(results)},
        },
        {
            "ts": _iso_now(),
            "event": "write_outputs",
            "detail": {"output_dir": str(output_dir)},
        },
    ]
    _write_trace(trace_path, trace_events)
    _write_reasoning_graph(graph_path, question, sources)
    _write_manifest(manifest_path, [report_path, sources_path, trace_path, graph_path, metrics_path])

    return {
        "output_dir": output_dir,
        "report": report_path,
        "sources": sources_path,
        "trace": trace_path,
        "graph": graph_path,
        "metrics": metrics_path,
        "manifest": manifest_path,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate a NEXUS research evidence pack (mock/local mode)."
    )
    parser.add_argument("question", help="Research question to answer.")
    parser.add_argument("--mode", default="mock", help="Mode: mock or local.")
    parser.add_argument("--root", help="Root path to index (default: NEXUS_ROOT).")
    parser.add_argument("--output", help="Output directory for evidence pack.")
    parser.add_argument("--backend", help="Memory backend (tfidf, bm25, dense, auto).")
    parser.add_argument("--limit", type=int, default=5, help="Max chunks to return.")
    parser.add_argument("--min-score", type=float, default=0.2, help="Minimum score threshold.")
    parser.add_argument(
        "--path",
        action="append",
        dest="paths",
        help="Optional paths to index (repeatable).",
    )

    args = parser.parse_args()

    outputs = run_research(
        question=args.question,
        root_path=Path(args.root).resolve() if args.root else None,
        output_dir=Path(args.output).resolve() if args.output else None,
        mode=args.mode,
        backend=args.backend,
        limit=args.limit,
        min_score=args.min_score,
        paths=args.paths,
    )

    print(f"Evidence pack written to: {outputs['output_dir']}")
    print(f"Report: {outputs['report']}")
    print(f"Sources: {outputs['sources']}")
    print(f"Trace: {outputs['trace']}")
    print(f"Graph: {outputs['graph']}")
    print(f"Metrics: {outputs['metrics']}")
    print(f"Manifest: {outputs['manifest']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
