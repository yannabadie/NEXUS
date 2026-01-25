"""Coverage audit report for Meta GraphRAG indexing."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from .config import MetaGraphRagConfig
from .indexer import IndexManifest, _is_binary_file


@dataclass
class CoverageReportPaths:
    summary: Path
    details: Path


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize_extensions(extensions: List[str]) -> List[str]:
    normalized: List[str] = []
    for ext in extensions:
        cleaned = ext.strip().lower()
        if not cleaned:
            continue
        if not cleaned.startswith("."):
            cleaned = "." + cleaned
        normalized.append(cleaned)
    return sorted(set(normalized))


def _is_excluded_dir(path: Path, exclude_dirs: List[str]) -> bool:
    exclude_set = {entry.lower() for entry in exclude_dirs}
    return any(part.lower() in exclude_set for part in path.parts)


def _classify_file(
    path: Path,
    extensions: List[str],
    max_bytes: int,
    exclude_dirs: List[str],
) -> Optional[str]:
    if _is_excluded_dir(path, exclude_dirs):
        return "excluded_dir"
    if extensions and path.suffix.lower() not in extensions:
        return "excluded_extension"
    if max_bytes and path.stat().st_size > max_bytes:
        return "excluded_size"
    return None


def _collect_files(root: Path) -> List[Path]:
    files: List[Path] = []
    for dirpath, _dirnames, filenames in os.walk(root):
        for name in filenames:
            files.append(Path(dirpath) / name)
    return files


def build_coverage_report(config: MetaGraphRagConfig, manifest: IndexManifest) -> Dict[str, object]:
    root = config.root_path
    extensions = _normalize_extensions(config.extensions)
    max_bytes = config.max_file_size_kb * 1024 if config.max_file_size_kb > 0 else 0
    files = _collect_files(root)
    manifest_files = set(manifest.files.keys())

    summary = {
        "generated_at": _utc_now(),
        "root_path": str(root),
        "total_files": 0,
        "included_files": 0,
        "indexed_files": 0,
        "missing_files": 0,
        "binary_files": 0,
        "excluded_dir": 0,
        "excluded_extension": 0,
        "excluded_size": 0,
        "latest_included_mtime": None,
        "include_dirs": list(config.include_dirs),
        "exclude_dirs": list(config.exclude_dirs),
        "extensions": extensions,
        "max_file_size_kb": config.max_file_size_kb,
        "manifest_generated_at": manifest.generated_at,
    }

    details = {
        "missing_files": [],
        "excluded_dir": [],
        "excluded_extension": [],
        "excluded_size": [],
        "binary_files": [],
    }

    limit = 100
    for path in files:
        summary["total_files"] += 1
        reason = _classify_file(path, extensions, max_bytes, config.exclude_dirs)
        if reason:
            summary[reason] += 1
            if len(details[reason]) < limit:
                details[reason].append(str(path))
            continue

        summary["included_files"] += 1
        try:
            mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
        except OSError:
            mtime = None
        if mtime:
            current = summary.get("latest_included_mtime")
            if not current or mtime > datetime.fromisoformat(current):
                summary["latest_included_mtime"] = mtime.isoformat()
        resolved = str(path.resolve())
        if resolved in manifest_files:
            summary["indexed_files"] += 1
            if _is_binary_file(path):
                summary["binary_files"] += 1
                if len(details["binary_files"]) < limit:
                    details["binary_files"].append(str(path))
        else:
            summary["missing_files"] += 1
            if len(details["missing_files"]) < limit:
                details["missing_files"].append(str(path))

    return {
        "summary": summary,
        "details": details,
    }


def write_coverage_report(
    report: Dict[str, object],
    output_dir: Path,
) -> CoverageReportPaths:
    output_dir.mkdir(parents=True, exist_ok=True)
    summary_path = output_dir / "coverage_report.md"
    details_path = output_dir / "coverage_report.json"

    details_path.write_text(json.dumps(report, indent=2, ensure_ascii=True), encoding="utf-8")

    summary = report.get("summary", {})
    lines = [
        "# Meta GraphRAG Coverage Report",
        "",
        f"Generated: {summary.get('generated_at')}",
        "",
        "## Summary",
        f"- root_path: {summary.get('root_path')}",
        f"- total_files: {summary.get('total_files')}",
        f"- included_files: {summary.get('included_files')}",
        f"- indexed_files: {summary.get('indexed_files')}",
        f"- missing_files: {summary.get('missing_files')}",
        f"- binary_files: {summary.get('binary_files')}",
        f"- excluded_dir: {summary.get('excluded_dir')}",
        f"- excluded_extension: {summary.get('excluded_extension')}",
        f"- excluded_size: {summary.get('excluded_size')}",
        "",
        "## Config",
        f"- include_dirs: {summary.get('include_dirs')}",
        f"- exclude_dirs: {summary.get('exclude_dirs')}",
        f"- extensions: {summary.get('extensions')}",
        f"- max_file_size_kb: {summary.get('max_file_size_kb')}",
        f"- manifest_generated_at: {summary.get('manifest_generated_at')}",
        "",
        "## Details",
        f"- JSON: {details_path}",
    ]
    summary_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    return CoverageReportPaths(summary=summary_path, details=details_path)
