"""CLI for Meta GraphRAG."""

from __future__ import annotations

import argparse
from dataclasses import replace
from pathlib import Path
import subprocess

from .config import load_config
from .indexer import MetaGraphIndexer
from .deep_research import run_deep_research
from .reports import generate_reports
from .research import fetch_sources
from .http_client import HttpConfig


def _run_git(args: list[str], cwd: Path) -> str:
    result = subprocess.run(
        args,
        cwd=str(cwd),
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "git command failed")
    return result.stdout


def _git_changed_paths(base: str, root: Path) -> tuple[list[Path], list[Path]]:
    changed: set[str] = set()
    removed: set[str] = set()

    diff_output = _run_git(
        ["git", "diff", "--name-status", "--no-renames", f"{base}...HEAD"],
        cwd=root,
    )
    for line in diff_output.splitlines():
        if not line.strip():
            continue
        parts = line.split("\t", 1)
        if len(parts) != 2:
            continue
        status, path = parts
        if status.startswith("D"):
            removed.add(path)
        else:
            changed.add(path)

    status_output = _run_git(["git", "status", "--porcelain"], cwd=root)
    for line in status_output.splitlines():
        if not line.strip():
            continue
        status = line[:2]
        path = line[3:].strip()
        if "->" in path:
            path = path.split("->", 1)[1].strip()
        if "D" in status:
            removed.add(path)
        elif status.strip():
            changed.add(path)

    changed -= removed

    changed_paths = [root / Path(path) for path in sorted(changed)]
    removed_paths = [root / Path(path) for path in sorted(removed)]
    return changed_paths, removed_paths


def main() -> int:
    parser = argparse.ArgumentParser(description="Meta GraphRAG for NEXUS development")
    subparsers = parser.add_subparsers(dest="command")

    index_parser = subparsers.add_parser("index", help="Index the codebase and sources")
    index_parser.add_argument("--full", action="store_true", help="Rebuild the index from scratch")
    index_parser.add_argument("--backend", help="Embedding backend override (auto|sentence|gemini|hash|none)")
    index_parser.add_argument(
        "--git-diff",
        action="store_true",
        help="Index only files changed since --git-base (plus working tree)",
    )
    index_parser.add_argument(
        "--git-base",
        default="HEAD",
        help="Git base ref for --git-diff (default: HEAD)",
    )

    query_parser = subparsers.add_parser("query", help="Query the GraphRAG index")
    query_parser.add_argument("query", help="Query text")
    query_parser.add_argument("--limit", type=int, default=None, help="Override seed limit")

    subparsers.add_parser("status", help="Show index status")

    report_parser = subparsers.add_parser("report", help="Generate analysis reports")
    report_parser.add_argument("--entrypoints", help="Comma-separated entrypoint paths")

    subparsers.add_parser("coverage", help="Generate coverage audit report")

    eval_parser = subparsers.add_parser("eval", help="Evaluate retrieval quality")
    eval_parser.add_argument("--queries", help="Path to eval queries JSON")
    eval_parser.add_argument("--seed-limit", type=int, default=None, help="Override seed limit")
    eval_parser.add_argument("--expansion-depth", type=int, default=None, help="Override expansion depth")
    eval_parser.add_argument("--expansion-limit", type=int, default=None, help="Override expansion limit")
    eval_parser.add_argument("--output", help="Output report path")

    embed_parser = subparsers.add_parser("embed", help="Embed missing chunks")
    embed_parser.add_argument("--limit", type=int, help="Limit number of chunks to embed")

    research_parser = subparsers.add_parser("research", help="Fetch web sources")
    research_parser.add_argument("--url", action="append", help="Specific URL to fetch")

    deep_parser = subparsers.add_parser("deep-research", help="Run Gemini-assisted deep research")
    deep_parser.add_argument("--query", action="append", help="Override research query (repeatable)")
    deep_parser.add_argument("--limit", type=int, help="Override results per query")

    health_parser = subparsers.add_parser("health", help="Run health checks against the index")
    health_parser.add_argument("--strict", action="store_true", help="Treat warnings as failures")
    health_parser.add_argument("--require-index", action="store_true", help="Fail if index data is missing")
    health_parser.add_argument("--max-missing-ratio", type=float, default=None)
    health_parser.add_argument("--max-missing-count", type=int, default=None)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return 1

    config = load_config()
    if getattr(args, "backend", None):
        config = replace(config, embedding_backend=args.backend)

    if args.command == "research":
        http_config = HttpConfig(ssl_mode=config.ssl_mode, ca_bundle_path=config.ca_bundle_path)
        fetch_sources(config.sources_path, urls=args.url, http_config=http_config)
        print(f"Saved sources to {config.sources_path}")
        return 0

    if args.command == "deep-research":
        if args.limit:
            config = replace(config, research_limit=args.limit)
        if args.query:
            config = replace(config, research_queries=args.query)
        paths = run_deep_research(config)
        print(f"Deep research saved to {config.sources_path} ({len(paths)} files)")
        return 0

    if args.command == "index":
        indexer = MetaGraphIndexer(config)
        if args.git_diff and args.full:
            print("WARNING: --full ignores --git-diff")
        if args.git_diff and not args.full:
            try:
                changed_paths, removed_paths = _git_changed_paths(args.git_base, config.root_path)
            except Exception as exc:
                print(f"WARNING: git diff failed ({exc}); falling back to full scan")
                indexer.index(full=args.full)
            else:
                if not changed_paths and not removed_paths:
                    print("No git changes detected. Index unchanged.")
                    status = indexer.status()
                    print(f"Indexed nodes: {status['nodes']}, chunks: {status['chunks']}")
                    return 0
                indexer.index(full=False, only_paths=changed_paths, removed_paths=removed_paths)
        else:
            indexer.index(full=args.full)
        status = indexer.status()
        print(f"Indexed nodes: {status['nodes']}, chunks: {status['chunks']}")
        return 0

    if args.command == "status":
        indexer = MetaGraphIndexer(config)
        status = indexer.status()
        print(status)
        return 0

    if args.command == "query":
        if args.limit:
            config = replace(config, query_seed_limit=args.limit)
        indexer = MetaGraphIndexer(config)
        result = indexer.query(args.query)
        print(f"Seed results: {len(result.seed_chunks)}")
        for chunk in result.seed_chunks:
            tags = chunk.metadata.get("security_tags", "")
            print(f"- {chunk.path}:{chunk.start_line}-{chunk.end_line} {chunk.kind} {tags}")
        if result.expanded_chunks:
            print(f"Expanded results: {len(result.expanded_chunks)}")
        return 0

    if args.command == "embed":
        indexer = MetaGraphIndexer(config)
        embedded = indexer.embed_missing(limit=args.limit)
        print(f"Embedded {embedded} chunks")
        return 0

    if args.command == "report":
        indexer = MetaGraphIndexer(config)
        entrypoints = None
        if args.entrypoints:
            entrypoints = [entry.strip() for entry in args.entrypoints.split(",") if entry.strip()]
        status = indexer.status()
        paths = generate_reports(
            graph=indexer.graph,
            chunks_count=status["chunks"],
            vector_count=status["vector_entries"],
            output_dir=config.reports_path,
            entrypoints=entrypoints,
        )
        print(f"Reports written to {paths.overview.parent}")
        return 0

    if args.command == "coverage":
        from .coverage import build_coverage_report, write_coverage_report
        from .indexer import IndexManifest
        manifest = IndexManifest.load(config.manifest_path)
        report = build_coverage_report(config, manifest)
        paths = write_coverage_report(report, config.reports_path)
        print(f"Coverage report written to {paths.summary}")
        return 0

    if args.command == "health":
        from .health import run_health_check, write_health_report, _env_bool, _env_float, _env_int

        strict = args.strict or _env_bool("META_RAG_HEALTH_STRICT", False)
        require_index = args.require_index or _env_bool("META_RAG_HEALTH_REQUIRE_INDEX", True)
        max_missing_ratio = (
            args.max_missing_ratio
            if args.max_missing_ratio is not None
            else _env_float("META_RAG_HEALTH_MAX_MISSING_RATIO", 0.0)
        )
        max_missing_count = (
            args.max_missing_count
            if args.max_missing_count is not None
            else _env_int("META_RAG_HEALTH_MAX_MISSING_COUNT", 0)
        )
        max_stale_seconds = _env_float("META_RAG_HEALTH_MAX_STALE_SECONDS", 0.0)
        max_sources_stale_seconds = _env_float("META_RAG_HEALTH_MAX_SOURCES_STALE_SECONDS", 0.0)
        vector_max_mb = _env_float("META_RAG_HEALTH_VECTOR_MAX_MB", 128.0)
        allow_git = _env_bool("META_RAG_HEALTH_ALLOW_GIT", False)

        report = run_health_check(
            config,
            strict=strict,
            require_index=require_index,
            max_missing_ratio=max_missing_ratio,
            max_missing_count=max_missing_count,
            max_stale_seconds=max_stale_seconds,
            max_sources_stale_seconds=max_sources_stale_seconds,
            vector_max_mb=vector_max_mb,
            allow_git=allow_git,
        )
        output = write_health_report(report, config.reports_path)
        print(f"Health report written to {output}")
        if not report.ok:
            return 2
        return 0

    if args.command == "eval":
        indexer = MetaGraphIndexer(config)
        from .eval import DEFAULT_EVAL_QUERIES, load_queries, run_eval, write_report

        queries_path = Path(args.queries) if args.queries else (config.data_path / DEFAULT_EVAL_QUERIES)
        queries = load_queries(queries_path)
        seed_limit = args.seed_limit if args.seed_limit is not None else config.query_seed_limit
        expansion_depth = (
            args.expansion_depth if args.expansion_depth is not None else config.query_expansion_depth
        )
        expansion_limit = (
            args.expansion_limit if args.expansion_limit is not None else config.query_expansion_limit
        )
        report = run_eval(
            indexer,
            queries,
            seed_limit=seed_limit,
            expansion_depth=expansion_depth,
            expansion_limit=expansion_limit,
        )
        output_path = Path(args.output) if args.output else (config.reports_path / "eval_report.json")
        write_report(report, output_path)
        summary = report.get("summary", {})
        print(f"Eval report written to {output_path}")
        if summary:
            print(f"Seed recall: {summary.get('seed_avg_recall')} | Expanded recall: {summary.get('expanded_avg_recall')}")
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
