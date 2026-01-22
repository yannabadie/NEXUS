"""Graph database persistence for Meta GraphRAG."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, Optional
import json
import sqlite3

from .graph import GraphEdge, GraphNode, GraphStore


class GraphDatabase:
    """SQLite-backed property graph store."""

    def __init__(self, path: Path, backend: str = "sqlite") -> None:
        self.backend = backend
        self.path = Path(path)
        self._conn: Optional[sqlite3.Connection] = None
        if backend != "sqlite":
            raise RuntimeError(f"Unsupported graph backend: {backend}")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self.path)
        self._conn.execute("PRAGMA foreign_keys = ON")
        self._init_schema()

    def close(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None

    def status(self) -> dict:
        conn = self._require_conn()
        node_count = conn.execute("SELECT COUNT(*) FROM nodes").fetchone()[0]
        edge_count = conn.execute("SELECT COUNT(*) FROM edges").fetchone()[0]
        return {"nodes": node_count, "edges": edge_count, "backend": self.backend}

    def reset(self) -> None:
        conn = self._require_conn()
        conn.execute("DELETE FROM edges")
        conn.execute("DELETE FROM nodes")
        conn.commit()

    def upsert_nodes(self, nodes: Iterable[GraphNode]) -> None:
        conn = self._require_conn()
        payload = [
            (
                node.node_id,
                node.node_type,
                node.name,
                node.path,
                node.start_line,
                node.end_line,
                node.content_hash,
                json.dumps(node.metadata, ensure_ascii=True),
            )
            for node in nodes
        ]
        if not payload:
            return
        conn.executemany(
            """
            INSERT INTO nodes (
                node_id, node_type, name, path, start_line, end_line, content_hash, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(node_id) DO UPDATE SET
                node_type=excluded.node_type,
                name=excluded.name,
                path=excluded.path,
                start_line=excluded.start_line,
                end_line=excluded.end_line,
                content_hash=excluded.content_hash,
                metadata=excluded.metadata
            """,
            payload,
        )
        conn.commit()

    def upsert_edges(self, edges: Iterable[GraphEdge]) -> None:
        conn = self._require_conn()
        payload = [
            (
                edge.source,
                edge.target,
                edge.edge_type,
                json.dumps(edge.metadata, ensure_ascii=True),
            )
            for edge in edges
        ]
        if not payload:
            return
        conn.executemany(
            """
            INSERT INTO edges (source, target, edge_type, metadata)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(source, target, edge_type) DO UPDATE SET
                metadata=excluded.metadata
            """,
            payload,
        )
        conn.commit()

    def remove_nodes(self, node_ids: Iterable[str]) -> None:
        ids = list(node_ids)
        if not ids:
            return
        conn = self._require_conn()
        placeholders = ", ".join("?" for _ in ids)
        conn.execute(f"DELETE FROM nodes WHERE node_id IN ({placeholders})", ids)
        conn.commit()

    def load_graph(self) -> GraphStore:
        conn = self._require_conn()
        graph = GraphStore()
        rows = conn.execute(
            "SELECT node_id, node_type, name, path, start_line, end_line, content_hash, metadata FROM nodes"
        ).fetchall()
        for row in rows:
            metadata = json.loads(row[7]) if row[7] else {}
            graph.add_node(GraphNode(
                node_id=row[0],
                node_type=row[1],
                name=row[2],
                path=row[3],
                start_line=row[4],
                end_line=row[5],
                content_hash=row[6],
                metadata=metadata,
            ))
        rows = conn.execute(
            "SELECT source, target, edge_type, metadata FROM edges"
        ).fetchall()
        for row in rows:
            metadata = json.loads(row[3]) if row[3] else {}
            graph.add_edge(GraphEdge(
                source=row[0],
                target=row[1],
                edge_type=row[2],
                metadata=metadata,
            ))
        return graph

    def _init_schema(self) -> None:
        conn = self._require_conn()
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS nodes (
                node_id TEXT PRIMARY KEY,
                node_type TEXT,
                name TEXT,
                path TEXT,
                start_line INTEGER,
                end_line INTEGER,
                content_hash TEXT,
                metadata TEXT
            )
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_nodes_path ON nodes(path)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_nodes_type ON nodes(node_type)")
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS edges (
                source TEXT,
                target TEXT,
                edge_type TEXT,
                metadata TEXT,
                PRIMARY KEY (source, target, edge_type),
                FOREIGN KEY (source) REFERENCES nodes(node_id) ON DELETE CASCADE,
                FOREIGN KEY (target) REFERENCES nodes(node_id) ON DELETE CASCADE
            )
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_edges_source ON edges(source)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_edges_target ON edges(target)")
        conn.commit()

    def _require_conn(self) -> sqlite3.Connection:
        if not self._conn:
            raise RuntimeError("Graph database connection is not available")
        return self._conn
