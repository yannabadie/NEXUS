"""Graph structures for Meta GraphRAG."""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, List
import json


@dataclass
class GraphNode:
    node_id: str
    node_type: str
    name: str
    path: str
    start_line: int
    end_line: int
    content_hash: str
    metadata: Dict[str, str] = field(default_factory=dict)


@dataclass
class GraphEdge:
    source: str
    target: str
    edge_type: str
    metadata: Dict[str, str] = field(default_factory=dict)


class GraphStore:
    """In-memory graph store with JSON persistence."""

    def __init__(self) -> None:
        self.nodes: Dict[str, GraphNode] = {}
        self.edges: List[GraphEdge] = []

    def add_node(self, node: GraphNode) -> None:
        self.nodes[node.node_id] = node

    def add_edge(self, edge: GraphEdge) -> None:
        self.edges.append(edge)

    def remove_nodes(self, node_ids: List[str]) -> None:
        for node_id in node_ids:
            self.nodes.pop(node_id, None)
        if node_ids:
            self.edges = [
                edge for edge in self.edges
                if edge.source not in node_ids and edge.target not in node_ids
            ]

    def to_dict(self) -> Dict[str, object]:
        return {
            "nodes": [asdict(node) for node in self.nodes.values()],
            "edges": [asdict(edge) for edge in self.edges],
        }

    @classmethod
    def from_dict(cls, payload: Dict[str, object]) -> "GraphStore":
        graph = cls()
        for node in payload.get("nodes", []):
            graph.add_node(GraphNode(**node))
        for edge in payload.get("edges", []):
            graph.add_edge(GraphEdge(**edge))
        return graph

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        data = self.to_dict()
        path.write_text(
            json.dumps(data, indent=2, ensure_ascii=True),
            encoding="utf-8",
        )

    @classmethod
    def load(cls, path: Path) -> "GraphStore":
        if not path.exists():
            return cls()
        payload = json.loads(path.read_text(encoding="utf-8"))
        return cls.from_dict(payload)

    def build_adjacency(self) -> Dict[str, List[GraphEdge]]:
        adjacency: Dict[str, List[GraphEdge]] = {}
        for edge in self.edges:
            adjacency.setdefault(edge.source, []).append(edge)
        return adjacency

    def build_reverse_adjacency(self) -> Dict[str, List[GraphEdge]]:
        adjacency: Dict[str, List[GraphEdge]] = {}
        for edge in self.edges:
            adjacency.setdefault(edge.target, []).append(edge)
        return adjacency
