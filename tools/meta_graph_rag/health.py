"""Health checks for Meta GraphRAG indexing."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import json
import os
import sqlite3

from .config import MetaGraphRagConfig
from .coverage import build_coverage_report
from .graph import GraphStore
from .indexer import IndexManifest


@dataclass(frozen=True)
class HealthIssue:
    level: str
    message: str
    details: Optional[Dict[str, object]] = None


@dataclass(frozen=True)
class HealthReport:
    ok: bool
    issues: List[HealthIssue]
    summary: Dict[str, object]


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_iso(ts: str) -> Optional[datetime]:
    if not ts:
        return None
    try:
        return datetime.fromisoformat(ts)
    except ValueError:
        return None


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.lower() in {"1", "true", "yes", "on"}


def _env_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _find_git_paths_in_db(db_path: Path, limit: int = 5) -> List[str]:
    if not db_path.exists():
        return []
    rows: List[str] = []
    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.execute(
            """
            SELECT path FROM nodes
            WHERE path LIKE '.git/%'
               OR path LIKE '%.git/%'
               OR path LIKE '%.git\\%'
               OR path LIKE '.git\\%'
            LIMIT ?
            """,
            (limit,),
        )
        for row in cursor.fetchall():
            rows.append(row[0])
    finally:
        conn.close()
    return rows


def _find_git_paths_in_graph(graph_path: Path, limit: int = 5) -> List[str]:
    if not graph_path.exists():
        return []
    graph = GraphStore.load(graph_path)
    matches: List[str] = []
    for node in graph.nodes.values():
        path = node.path.replace("\\", "/")
        if "/.git/" in path or path.startswith(".git/"):
            matches.append(node.path)
            if len(matches) >= limit:
                break
    return matches


def _load_vector_index_summary(path: Path, max_mb: float) -> Tuple[Optional[int], Dict[str, object], Optional[str]]:
    if not path.exists():
        return None, {}, None
    size_mb = path.stat().st_size / (1024 * 1024)
    if size_mb > max_mb:
        return None, {}, f"vector_index.json size {size_mb:.1f} MB exceeds limit"
    payload = json.loads(path.read_text(encoding="utf-8"))
    backend = payload.get("backend", {}) if isinstance(payload, dict) else {}
    entries = payload.get("entries", []) if isinstance(payload, dict) else []
    return len(entries) if isinstance(entries, list) else None, backend, None


def _latest_source_mtime(sources_path: Path) -> Optional[datetime]:
    latest: Optional[datetime] = None
    if not sources_path.exists():
        return None
    for path in sources_path.glob("*.txt"):
        try:
            ts = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
        except OSError:
            continue
        if latest is None or ts > latest:
            latest = ts
    return latest


def run_health_check(
    config: MetaGraphRagConfig,
    *,
    strict: bool = False,
    require_index: bool = True,
    max_missing_ratio: float = 0.0,
    max_missing_count: int = 0,
    max_stale_seconds: float = 0.0,
    max_sources_stale_seconds: float = 0.0,
    vector_max_mb: float = 128.0,
    allow_git: bool = False,
) -> HealthReport:
    issues: List[HealthIssue] = []
    summary: Dict[str, object] = {
        "generated_at": _utc_now(),
        "root_path": str(config.root_path),
        "require_index": require_index,
        "strict": strict,
    }

    manifest = IndexManifest.load(config.manifest_path)
    if not manifest.files:
        message = "Index manifest is empty; run meta_graph_rag index first."
        issues.append(HealthIssue("error" if require_index else "warning", message))
        summary["index_present"] = False
        return HealthReport(ok=not (strict or require_index), issues=issues, summary=summary)

    summary["index_present"] = True
    summary["manifest_files"] = len(manifest.files)

    coverage = build_coverage_report(config, manifest)
    coverage_summary = coverage.get("summary", {})
    summary["coverage"] = coverage_summary
    missing_count = int(coverage_summary.get("missing_files", 0))
    included_count = int(coverage_summary.get("included_files", 0)) or 1
    missing_ratio = missing_count / included_count

    if missing_count > max_missing_count or missing_ratio > max_missing_ratio:
        issues.append(HealthIssue(
            "error",
            "Meta GraphRAG coverage below threshold",
            {
                "missing_count": missing_count,
                "missing_ratio": round(missing_ratio, 4),
                "max_missing_count": max_missing_count,
                "max_missing_ratio": max_missing_ratio,
            },
        ))

    chunks_count = 0
    for entry in manifest.files.values():
        chunks = entry.get("chunks", [])
        if isinstance(chunks, list):
            chunks_count += len(chunks)
    summary["chunk_count"] = chunks_count
    if chunks_count and chunks_count < len(manifest.files):
        issues.append(HealthIssue(
            "warning",
            "Chunk count is lower than manifest file count.",
            {"chunks": chunks_count, "files": len(manifest.files)},
        ))

    vector_entries, vector_backend, vector_warning = _load_vector_index_summary(
        config.vector_path,
        vector_max_mb,
    )
    summary["vector_entries"] = vector_entries
    summary["vector_backend"] = vector_backend
    if vector_warning:
        issues.append(HealthIssue("warning", vector_warning))

    if vector_backend:
        backend = vector_backend.get("backend")
        config_backend = config.embedding_backend
        if backend:
            fallback_backend = (config.embedding_fallback_backend or "").lower()
            if backend == "fallback":
                expected_primary = config_backend == "gemini"
                expected_fallback = fallback_backend == vector_backend.get("fallback_backend")
                if not (expected_primary and expected_fallback):
                    issues.append(HealthIssue(
                        "error",
                        "Embedding backend mismatch between config and vector index.",
                        {"config": config_backend, "index": backend, "fallback": fallback_backend},
                    ))
            elif backend != config_backend:
                issues.append(HealthIssue(
                    "error",
                    "Embedding backend mismatch between config and vector index.",
                    {"config": config_backend, "index": backend},
                ))
        if backend == "gemini":
            model = vector_backend.get("model")
            if model and model != config.gemini_embedding_model:
                issues.append(HealthIssue(
                    "warning",
                    "Gemini embedding model mismatch between config and vector index.",
                    {"config": config.gemini_embedding_model, "index": model},
                ))
    else:
        if not config.skip_embeddings and config.embedding_backend not in {"none", "noop"}:
            issues.append(HealthIssue(
                "warning",
                "Vector index backend missing; embeddings may be skipped.",
            ))

    git_paths = _find_git_paths_in_db(config.graph_db_path)
    if not git_paths:
        git_paths = _find_git_paths_in_graph(config.graph_path)
    summary["git_paths_sample"] = git_paths
    if git_paths and not allow_git:
        issues.append(HealthIssue(
            "error",
            "Detected .git paths in graph index.",
            {"sample": git_paths},
        ))

    manifest_ts = _parse_iso(manifest.generated_at)
    latest_mtime_raw = coverage_summary.get("latest_included_mtime")
    latest_mtime = _parse_iso(latest_mtime_raw) if isinstance(latest_mtime_raw, str) else None
    if manifest_ts and latest_mtime:
        delta = (latest_mtime - manifest_ts).total_seconds()
        summary["manifest_stale_seconds"] = delta
        if delta > max_stale_seconds:
            issues.append(HealthIssue(
                "warning",
                "Index manifest older than newest indexed file.",
                {"manifest": manifest.generated_at, "latest_file": latest_mtime_raw},
            ))

    sources_manifest = config.sources_path / "sources.json"
    latest_source = _latest_source_mtime(config.sources_path)
    if sources_manifest.exists() and latest_source:
        sources_ts = datetime.fromtimestamp(sources_manifest.stat().st_mtime, tz=timezone.utc)
        delta = (latest_source - sources_ts).total_seconds()
        summary["sources_stale_seconds"] = delta
        if delta > max_sources_stale_seconds:
            issues.append(HealthIssue(
                "warning",
                "sources.json older than latest source file.",
                {"sources_manifest": sources_manifest.name, "latest_source": latest_source.isoformat()},
            ))

    ok = not any(issue.level == "error" for issue in issues)
    if strict and issues:
        ok = False

    return HealthReport(ok=ok, issues=issues, summary=summary)


def write_health_report(report: HealthReport, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "health_report.json"
    payload = {
        "ok": report.ok,
        "summary": report.summary,
        "issues": [
            {
                "level": issue.level,
                "message": issue.message,
                "details": issue.details or {},
            }
            for issue in report.issues
        ],
    }
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True), encoding="utf-8")
    return path
