"""
NEXUS Research CLI - local evidence-pack generation with grounded synthesis.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.config import Config
from core.memory_pkg.memory.project_memory import ProjectMemory

STOP_WORDS = {
    "the",
    "and",
    "for",
    "with",
    "that",
    "this",
    "from",
    "into",
    "what",
    "how",
    "why",
    "when",
    "where",
    "which",
    "does",
    "doesn",
    "mode",
    "local",
    "mock",
    "using",
    "used",
}

CONTRADICTION_RULES = (
    (
        "workspace/.nexus",
        "nexus_root/.nexus",
        "Retrieved evidence disagrees on whether storage lives under workspace or NEXUS_ROOT.",
    ),
    (
        "default runtime authority",
        "historical review",
        "Retrieved evidence disagrees on whether a governance surface is active runtime authority or historical-only.",
    ),
)


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


def _clip(text: str, max_chars: int = 180) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 3].rstrip() + "..."


def _extract_query_terms(question: str) -> set[str]:
    terms = set()
    for term in re.findall(r"[a-zA-Z_][a-zA-Z0-9_./-]*", question.lower()):
        if len(term) > 2 and term not in STOP_WORDS:
            terms.add(term)
    return terms


def _confidence_label(score: float) -> str:
    if score >= 0.75:
        return "high"
    if score >= 0.45:
        return "medium"
    return "low"


def _extract_best_snippet(source: Dict[str, Any]) -> str:
    excerpt = str(source.get("excerpt", ""))
    chunk_type = str(source.get("chunk_type", ""))
    name = str(source.get("name") or "").strip()

    lines = [line.strip() for line in excerpt.splitlines() if line.strip()]
    if not lines:
        if name:
            return f"Relevant {chunk_type} `{name}` was retrieved."
        return "Relevant evidence was retrieved."

    if chunk_type == "section":
        for line in lines:
            candidate = line.lstrip("#").strip("` ").strip()
            if candidate:
                return _clip(candidate)

    for line in lines:
        if line.startswith(('"""', "'''")):
            candidate = line.strip('"\' ')
            if candidate:
                return _clip(candidate)

    for line in lines:
        if line.startswith("#"):
            candidate = line.lstrip("#").strip()
            if candidate:
                return _clip(candidate)

    for line in lines:
        if line.startswith("class "):
            return _clip(f"Defines {line}.")
        if line.startswith("def ") or line.startswith("async def "):
            return _clip(f"Defines {line}.")

    for line in lines:
        candidate = line.strip("` ").strip()
        if candidate:
            return _clip(candidate)

    if name:
        return f"Relevant {chunk_type} `{name}` was retrieved."
    return "Relevant evidence was retrieved."


def _build_findings(question: str, sources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    query_terms = _extract_query_terms(question)
    findings: List[Dict[str, Any]] = []

    for idx, source in enumerate(sources, start=1):
        snippet = _extract_best_snippet(source)
        source_terms = set(str(term).lower() for term in source.get("terms", []))
        overlap = len(query_terms & source_terms)
        overlap_score = overlap / max(len(query_terms), 1) if query_terms else 0.5
        structure_bonus = 0.15 if source.get("chunk_type") in {"function", "class", "section"} else 0.0
        evidence_score = min(round(overlap_score + structure_bonus, 2), 1.0)
        label = _confidence_label(evidence_score)
        target = f"`{source['name']}`" if source.get("name") else f"`{source['file_path']}`"

        if str(source.get("chunk_type")) == "section":
            statement = f"Documentation in {target} indicates: {snippet}"
        elif source.get("name"):
            statement = f"Implementation evidence around {target} indicates: {snippet}"
        else:
            statement = f"Evidence from `{source['file_path']}` indicates: {snippet}"

        findings.append(
            {
                "finding_id": f"F{idx}",
                "statement": statement,
                "source_ids": [source["source_id"]],
                "confidence": {"label": label, "score": evidence_score},
            }
        )

    return findings


def _build_contradictions(sources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    contradictions: List[Dict[str, Any]] = []
    lowered = [
        {
            "source_id": source["source_id"],
            "file_path": source["file_path"],
            "excerpt": str(source.get("excerpt", "")).lower(),
        }
        for source in sources
    ]

    for left, right, description in CONTRADICTION_RULES:
        left_hits = [source for source in lowered if left in source["excerpt"]]
        right_hits = [source for source in lowered if right in source["excerpt"]]
        if left_hits and right_hits:
            contradiction_id = f"C{len(contradictions) + 1}"
            contradiction_sources = sorted({hit["source_id"] for hit in left_hits + right_hits})
            contradictions.append(
                {
                    "contradiction_id": contradiction_id,
                    "description": description,
                    "source_ids": contradiction_sources,
                }
            )

    return contradictions


def _build_synthesis(question: str, sources: List[Dict[str, Any]]) -> Dict[str, Any]:
    findings = _build_findings(question, sources)
    contradictions = _build_contradictions(sources)
    unique_files = len({source["file_path"] for source in sources})
    average_confidence = (
        round(sum(finding["confidence"]["score"] for finding in findings) / len(findings), 2) if findings else 0.0
    )
    coverage_score = min(len(sources) / 4.0, 1.0)
    diversity_score = min(unique_files / 3.0, 1.0)
    contradiction_penalty = 0.15 * len(contradictions)
    score = max(round((0.45 * average_confidence) + (0.35 * coverage_score) + (0.20 * diversity_score) - contradiction_penalty, 2), 0.0)
    confidence = {"label": _confidence_label(score), "score": score}

    if findings:
        answer_bullets = [
            f"{finding['statement']} [{', '.join(finding['source_ids'])}]"
            for finding in findings[: min(3, len(findings))]
        ]
    else:
        answer_bullets = ["No grounded answer could be synthesized from the retrieved sources."]

    return {
        "question": question,
        "answer_bullets": answer_bullets,
        "findings": findings,
        "contradictions": contradictions,
        "overall_confidence": confidence,
    }


def _write_report(
    path: Path,
    question: str,
    mode: str,
    backend: str,
    generated_at: str,
    synthesis: Dict[str, Any],
    sources: List[Dict[str, Any]],
) -> None:
    confidence = synthesis["overall_confidence"]
    lines = [
        "# Research Report",
        "",
        f"Question: {question}",
        f"Mode: {mode}",
        f"Backend: {backend}",
        f"Generated: {generated_at}",
        f"Confidence: {confidence['label']} ({confidence['score']:.2f})",
        "",
        "## Answer",
    ]

    for bullet in synthesis["answer_bullets"]:
        lines.append(f"- {bullet}")

    lines.extend(["", "## Findings"])
    if synthesis["findings"]:
        for finding in synthesis["findings"]:
            conf = finding["confidence"]
            lines.append(
                f"- [{finding['finding_id']}] ({conf['label']} {conf['score']:.2f}) "
                f"{finding['statement']} [{', '.join(finding['source_ids'])}]"
            )
    else:
        lines.append("- No findings were synthesized from the retrieved evidence.")

    lines.extend(["", "## Contradictions"])
    if synthesis["contradictions"]:
        for contradiction in synthesis["contradictions"]:
            lines.append(
                f"- [{contradiction['contradiction_id']}] {contradiction['description']} "
                f"[{', '.join(contradiction['source_ids'])}]"
            )
    else:
        lines.append("- No heuristic contradictions detected among the retrieved sources.")

    lines.extend(["", "## Sources"])
    if sources:
        for source in sources:
            lines.append(
                f"- [{source['source_id']}] {source['file_path']} "
                f"(L{source['start_line']}-{source['end_line']})"
            )
    else:
        lines.append("- No sources matched the query at the current threshold.")

    lines.extend(
        [
            "",
            "## Notes",
            "- This report was generated in mock/local mode using on-disk project data.",
            "- No external network calls or API keys were required.",
            "- Confidence and contradiction handling are deterministic heuristics over retrieved evidence.",
        ]
    )

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_sources(path: Path, payload: Dict[str, object]) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True), encoding="utf-8")


def _write_metrics(path: Path, payload: Dict[str, object]) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True), encoding="utf-8")


def _write_trace(path: Path, events: List[Dict[str, object]]) -> None:
    lines = [json.dumps(event, ensure_ascii=True) for event in events]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _escape_mermaid(text: str) -> str:
    return _clip(str(text).replace('"', "'"), max_chars=110)


def _write_reasoning_graph(
    path: Path,
    question: str,
    synthesis: Dict[str, Any],
    sources: List[Dict[str, Any]],
) -> None:
    lines = ["graph TD", f'  Q["{_escape_mermaid(question)}"]']
    source_lookup = {source["source_id"]: source for source in sources}

    for finding in synthesis["findings"]:
        finding_id = finding["finding_id"]
        lines.append(f'  Q --> {finding_id}["{_escape_mermaid(finding["statement"])}"]')
        for source_id in finding["source_ids"]:
            source = source_lookup.get(source_id)
            if not source:
                continue
            lines.append(f'  {finding_id} --> {source_id}["{_escape_mermaid(source["file_path"])}"]')

    for contradiction in synthesis["contradictions"]:
        contradiction_id = contradiction["contradiction_id"]
        lines.append(f'  Q --> {contradiction_id}["{_escape_mermaid(contradiction["description"])}"]')
        for source_id in contradiction["source_ids"]:
            source = source_lookup.get(source_id)
            if not source:
                continue
            lines.append(f'  {contradiction_id} --> {source_id}["{_escape_mermaid(source["file_path"])}"]')

    if not synthesis["findings"] and not synthesis["contradictions"]:
        lines.append('  Q --> R["No grounded findings"]')

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_manifest(path: Path, files: List[Path]) -> None:
    lines = []
    for file_path in files:
        digest = _hash_file(file_path)
        lines.append(f"{digest}  {file_path.name}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_research_payload(
    question: str,
    root_path: Optional[Path] = None,
    mode: str = "mock",
    backend: Optional[str] = None,
    limit: int = 5,
    min_score: float = 0.2,
    paths: Optional[List[str]] = None,
) -> Dict[str, Any]:
    if not question or not question.strip():
        raise ValueError("Question cannot be empty.")

    config = Config()
    root = Path(root_path) if root_path else config.nexus_root
    root = root.resolve()

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
    sources: List[Dict[str, Any]] = []
    for idx, chunk in enumerate(results, start=1):
        sources.append(
            {
                "source_id": f"S{idx}",
                "file_path": chunk.file_path,
                "start_line": chunk.start_line,
                "end_line": chunk.end_line,
                "chunk_type": chunk.chunk_type,
                "name": chunk.name,
                "terms": sorted(chunk.terms),
                "excerpt": chunk.content.strip()[:400],
            }
        )

    backend_info = memory.get_backend_info()
    backend_name = backend_info.get("backend", backend)
    generated_at = _iso_now()
    synthesis = _build_synthesis(question, sources)

    return {
        "question": question,
        "mode": mode,
        "backend": backend_name,
        "generated_at": generated_at,
        "root_path": str(root),
        "index_paths": [str(p) for p in index_paths],
        "indexed_chunks": indexed_chunks,
        "sources": sources,
        "synthesis": synthesis,
    }


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
    start_time = time.perf_counter()
    config = Config()

    output_dir = Path(output_dir) if output_dir else (
        config.workspace_path / "research" / _utc_now().strftime("%Y%m%d_%H%M%S")
    )
    output_dir.mkdir(parents=True, exist_ok=True)

    payload = build_research_payload(
        question=question,
        root_path=root_path,
        mode=mode,
        backend=backend,
        limit=limit,
        min_score=min_score,
        paths=paths,
    )
    sources = payload["sources"]
    synthesis = payload["synthesis"]
    backend_name = payload["backend"]
    generated_at = payload["generated_at"]

    report_path = output_dir / "report.md"
    sources_path = output_dir / "sources.json"
    trace_path = output_dir / "trace.jsonl"
    graph_path = output_dir / "reasoning_graph.mmd"
    metrics_path = output_dir / "metrics.json"
    manifest_path = output_dir / "manifest.sha256"

    _write_report(
        report_path,
        question=question,
        mode=payload["mode"],
        backend=backend_name,
        generated_at=generated_at,
        synthesis=synthesis,
        sources=sources,
    )

    _write_sources(
        sources_path,
        payload,
    )

    duration_ms = int((time.perf_counter() - start_time) * 1000)
    _write_metrics(
        metrics_path,
        {
            "question": question,
            "mode": payload["mode"],
            "backend": backend_name,
            "generated_at": generated_at,
            "indexed_chunks": payload["indexed_chunks"],
            "source_count": len(sources),
            "finding_count": len(synthesis["findings"]),
            "contradiction_count": len(synthesis["contradictions"]),
            "unique_files": len({source["file_path"] for source in sources}),
            "confidence_score": synthesis["overall_confidence"]["score"],
            "confidence_label": synthesis["overall_confidence"]["label"],
            "duration_ms": duration_ms,
        },
    )

    trace_events = [
        {
            "ts": generated_at,
            "event": "start",
            "detail": {"mode": payload["mode"], "backend": backend_name},
        },
        {
            "ts": _iso_now(),
            "event": "index",
            "detail": {"paths": payload["index_paths"], "chunks": payload["indexed_chunks"]},
        },
        {
            "ts": _iso_now(),
            "event": "retrieve",
            "detail": {"limit": limit, "min_score": min_score, "results": len(results)},
        },
        {
            "ts": _iso_now(),
            "event": "synthesize",
            "detail": {
                "findings": len(synthesis["findings"]),
                "contradictions": len(synthesis["contradictions"]),
                "confidence": synthesis["overall_confidence"],
            },
        },
        {
            "ts": _iso_now(),
            "event": "write_outputs",
            "detail": {"output_dir": str(output_dir)},
        },
    ]

    _write_trace(trace_path, trace_events)
    _write_reasoning_graph(graph_path, question, synthesis, sources)
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
    parser = argparse.ArgumentParser(description="Generate a NEXUS research evidence pack (mock/local mode).")
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
