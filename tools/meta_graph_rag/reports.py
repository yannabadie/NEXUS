"""Report generation for Meta GraphRAG."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .graph import GraphEdge, GraphNode, GraphStore


DEFAULT_ENTRYPOINTS = [
    "nexus7.py",
    "core/orchestration_v7.py",
    "core/api",
    "core/hive_mind",
    "interface/ui",
]


@dataclass
class ReportPaths:
    overview: Path
    top_down: Path
    bottom_up: Path
    security: Path


def generate_reports(
    graph: GraphStore,
    chunks_count: int,
    vector_count: int,
    output_dir: Path,
    entrypoints: Optional[List[str]] = None,
) -> ReportPaths:
    output_dir.mkdir(parents=True, exist_ok=True)

    overview_path = output_dir / "overview.md"
    top_down_path = output_dir / "top_down.md"
    bottom_up_path = output_dir / "bottom_up.md"
    security_path = output_dir / "security_hotspots.md"

    entrypoints = entrypoints or DEFAULT_ENTRYPOINTS
    _write_overview(overview_path, graph, chunks_count, vector_count)
    _write_top_down(top_down_path, graph, entrypoints)
    _write_bottom_up(bottom_up_path, graph)
    _write_security(security_path, graph)

    return ReportPaths(
        overview=overview_path,
        top_down=top_down_path,
        bottom_up=bottom_up_path,
        security=security_path,
    )


def _write_overview(path: Path, graph: GraphStore, chunks_count: int, vector_count: int) -> None:
    node_types: Dict[str, int] = {}
    edge_types: Dict[str, int] = {}
    for node in graph.nodes.values():
        node_types[node.node_type] = node_types.get(node.node_type, 0) + 1
    for edge in graph.edges:
        edge_types[edge.edge_type] = edge_types.get(edge.edge_type, 0) + 1

    lines = [
        "# Meta GraphRAG Overview",
        "",
        f"Generated: {_utc_now()}",
        "",
        "## Node Types",
    ]
    for node_type, count in sorted(node_types.items(), key=lambda item: item[0]):
        lines.append(f"- {node_type}: {count}")

    lines.extend(["", "## Edge Types"])
    for edge_type, count in sorted(edge_types.items(), key=lambda item: item[0]):
        lines.append(f"- {edge_type}: {count}")

    lines.extend([
        "",
        "## Index Volume",
        f"- chunks: {chunks_count}",
        f"- vector entries: {vector_count}",
    ])

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_top_down(path: Path, graph: GraphStore, entrypoints: List[str]) -> None:
    adjacency = graph.build_adjacency()
    entry_nodes = _find_entry_nodes(graph, entrypoints)

    lines = [
        "# Top-Down Dependency Map",
        "",
        f"Generated: {_utc_now()}",
        "",
    ]

    for label, node_ids in entry_nodes:
        lines.append(f"## {label}")
        if not node_ids:
            lines.append("- (no matching nodes)")
            lines.append("")
            continue
        for node_id in node_ids:
            lines.extend(_render_dependency_tree(node_id, graph, adjacency, depth=2))
        lines.append("")

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_bottom_up(path: Path, graph: GraphStore) -> None:
    adjacency = graph.build_adjacency()
    reverse = graph.build_reverse_adjacency()
    leaf_nodes = []
    for node_id, node in graph.nodes.items():
        if node.node_type != "file":
            continue
        outgoing = [edge for edge in adjacency.get(node_id, []) if edge.edge_type == "imports"]
        if not outgoing:
            leaf_nodes.append(node_id)

    leaf_nodes.sort()

    lines = [
        "# Bottom-Up Dependency Map",
        "",
        f"Generated: {_utc_now()}",
        "",
    ]

    for node_id in leaf_nodes[:50]:
        node = graph.nodes.get(node_id)
        if not node:
            continue
        lines.append(f"- {node.path}")
        parents = [edge.source for edge in reverse.get(node_id, []) if edge.edge_type == "imports"]
        for parent_id in parents[:5]:
            parent = graph.nodes.get(parent_id)
            if parent:
                lines.append(f"  - used by: {parent.path}")

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_security(path: Path, graph: GraphStore) -> None:
    lines = [
        "# Security Hotspots",
        "",
        f"Generated: {_utc_now()}",
        "",
    ]
    for node in graph.nodes.values():
        tags = node.metadata.get("security_tags", "")
        if not tags:
            continue
        lines.append(f"- {node.path}:{node.start_line} {node.name} [{tags}]")
    if len(lines) == 4:
        lines.append("- (no security-tagged nodes detected)")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _find_entry_nodes(graph: GraphStore, entrypoints: List[str]) -> List[Tuple[str, List[str]]]:
    results: List[Tuple[str, List[str]]] = []
    for entry in entrypoints:
        matched = []
        for node_id, node in graph.nodes.items():
            if node.node_type != "file":
                continue
            if node.path == entry or node.path.startswith(entry):
                matched.append(node_id)
        results.append((entry, sorted(matched)))
    return results


def _render_dependency_tree(
    node_id: str,
    graph: GraphStore,
    adjacency: Dict[str, List[GraphEdge]],
    depth: int = 2,
    indent: int = 0,
    visited: Optional[set[str]] = None,
) -> List[str]:
    if visited is None:
        visited = set()
    lines = []
    node = graph.nodes.get(node_id)
    if not node:
        return lines
    prefix = "  " * indent
    lines.append(f"{prefix}- {node.path}")
    if depth <= 0:
        return lines
    visited.add(node_id)
    for edge in adjacency.get(node_id, []):
        if edge.edge_type != "imports":
            continue
        if edge.target in visited:
            continue
        lines.extend(_render_dependency_tree(edge.target, graph, adjacency, depth - 1, indent + 1, visited))
    return lines


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()
