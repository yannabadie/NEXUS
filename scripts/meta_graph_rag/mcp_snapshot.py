"""Capture Meta GraphRAG MCP snapshots and queries."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any, Dict, List

from core.mcp.client import MCPClient


def _serialize_content(content: List[Any]) -> List[object]:
    payload: List[object] = []
    for item in content or []:
        if hasattr(item, "to_dict"):
            payload.append(item.to_dict())
        else:
            payload.append(item)
    return payload


def _content_text(content: List[Any]) -> str:
    parts: List[str] = []
    for item in content or []:
        if hasattr(item, "to_dict"):
            item = item.to_dict()
        if isinstance(item, dict) and item.get("type") == "text":
            parts.append(item.get("text", ""))
        else:
            parts.append(json.dumps(item, ensure_ascii=False))
    return "\n".join(part for part in parts if part)


def _write_payload(path: Path, content: List[Any]) -> None:
    payload = {
        "raw": _serialize_content(content),
        "text": _content_text(content),
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _default_queries() -> Dict[str, str]:
    return {
        "entrypoints": "List primary entrypoints, CLI/API/UI boot paths, and module boundaries.",
        "critical_flows": "Summarize critical execution flows, orchestration pipeline, and NCM pipeline with file references.",
        "security_hotspots": "Identify security-sensitive areas, external calls, subprocess, network IO, and auth flows with file references.",
        "known_todos": "Aggregate TODO/FIXME/XXX notes that affect runtime correctness, orchestration, or persistence.",
    }


def _extra_queries() -> Dict[str, str]:
    return {
        "cli_startup": "Trace CLI startup: nexus7.py -> core.interface.repl -> orchestrator. Provide function-level references and potential failure points.",
        "orchestrator_flow": "Summarize OrchestratorV7 lifecycle, model routing, tool execution, and swarm integration with file references.",
        "memory_subsystem": "Summarize memory subsystem (core/memory, core/synapse) and how it is wired into orchestration.",
        "execution_security": "Summarize execution handlers and security policy enforcement (ExecutionPolicy, PathGuardian, sandbox) with file references.",
        "ncm_pipeline": "Summarize NCM pipeline from /ncm command to story execution with file references.",
        "api_surface": "Summarize Cerebro API surface (auth, files, memory, stream) and notable security boundaries with file references.",
    }


def _run_queries(
    client: MCPClient,
    output_dir: Path,
    *,
    include_extra: bool,
    skip_queries: bool,
    top_k: int,
) -> None:
    if skip_queries:
        return

    queries = _default_queries()
    results: Dict[str, Dict[str, object]] = {}
    for key, query in queries.items():
        result = client.call_tool(
            "nexus_meta_graphrag_query",
            {"query": query, "top_k": top_k, "expand_hops": 1},
        ).content
        results[key] = {
            "raw": _serialize_content(result),
            "text": _content_text(result),
        }
    (output_dir / "mcp_queries.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    if include_extra:
        extra = _extra_queries()
        extra_results: Dict[str, Dict[str, object]] = {}
        for key, query in extra.items():
            result = client.call_tool(
                "nexus_meta_graphrag_query",
                {"query": query, "top_k": top_k, "expand_hops": 1},
            ).content
            extra_results[key] = {
                "raw": _serialize_content(result),
                "text": _content_text(result),
            }
        (output_dir / "mcp_queries_extra.json").write_text(
            json.dumps(extra_results, ensure_ascii=False, indent=2), encoding="utf-8"
        )


def main() -> int:
    parser = argparse.ArgumentParser(description="Capture Meta GraphRAG MCP snapshots.")
    parser.add_argument("--output-dir", default="workspace/meta_rag", help="Output directory")
    parser.add_argument("--include-extra", action="store_true", help="Include extended query set")
    parser.add_argument("--skip-queries", action="store_true", help="Skip meta GraphRAG queries")
    parser.add_argument("--top-k", type=int, default=8, help="Top-k seed results per query")
    parser.add_argument("--fast", action="store_true", help="Use snapshot mode for status/reports")
    parser.add_argument(
        "--server",
        choices=("nexus", "meta"),
        default="nexus",
        help="MCP server to query (nexus = full server, meta = meta-only server)",
    )

    args = parser.parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    command = ["python", "-m", "core.mcp.server"]
    if args.server == "meta":
        command = ["python", "-m", "core.mcp.meta_server"]

    client = MCPClient(command=command, cwd=Path(os.getcwd()))
    client.start()
    client.initialize()
    try:
        status = client.call_tool("nexus_meta_graphrag_status", {"fast": args.fast}).content
        reports = client.call_tool("nexus_meta_graphrag_reports", {"fast": args.fast}).content
        _write_payload(output_dir / "mcp_status.json", status)
        _write_payload(output_dir / "mcp_reports.json", reports)
        _run_queries(
            client,
            output_dir,
            include_extra=args.include_extra,
            skip_queries=args.skip_queries,
            top_k=args.top_k,
        )
    finally:
        client.close()

    print(f"MCP meta GraphRAG snapshot saved to {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
