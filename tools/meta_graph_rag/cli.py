"""CLI for Meta GraphRAG."""

from __future__ import annotations

import argparse
from dataclasses import replace

from .config import load_config
from .indexer import MetaGraphIndexer
from .reports import generate_reports
from .research import fetch_sources


def main() -> int:
    parser = argparse.ArgumentParser(description="Meta GraphRAG for NEXUS development")
    subparsers = parser.add_subparsers(dest="command")

    index_parser = subparsers.add_parser("index", help="Index the codebase and sources")
    index_parser.add_argument("--full", action="store_true", help="Rebuild the index from scratch")
    index_parser.add_argument("--backend", help="Embedding backend override (auto|sentence|gemini|hash|none)")

    query_parser = subparsers.add_parser("query", help="Query the GraphRAG index")
    query_parser.add_argument("query", help="Query text")
    query_parser.add_argument("--limit", type=int, default=None, help="Override seed limit")

    subparsers.add_parser("status", help="Show index status")

    report_parser = subparsers.add_parser("report", help="Generate analysis reports")
    report_parser.add_argument("--entrypoints", help="Comma-separated entrypoint paths")

    research_parser = subparsers.add_parser("research", help="Fetch web sources")
    research_parser.add_argument("--url", action="append", help="Specific URL to fetch")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return 1

    config = load_config()
    if getattr(args, "backend", None):
        config = replace(config, embedding_backend=args.backend)

    if args.command == "research":
        fetch_sources(config.sources_path, urls=args.url)
        print(f"Saved sources to {config.sources_path}")
        return 0

    indexer = MetaGraphIndexer(config)

    if args.command == "index":
        indexer.index(full=args.full)
        status = indexer.status()
        print(f"Indexed nodes: {status['nodes']}, chunks: {status['chunks']}")
        return 0

    if args.command == "status":
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

    if args.command == "report":
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

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
