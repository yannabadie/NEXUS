"""
NEXUS V13.x META GRAPHRAG - GraphRAG Query + Briefing API

Provides standardized HTTP access to the Meta GraphRAG index so agents can:
- query top-k chunks with optional graph expansion
- fetch status metrics
- generate and retrieve briefing reports (top-down, bottom-up, module catalog)
"""

from __future__ import annotations

import hashlib
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from ..deps import AuthenticatedUser
from ..rbac import Permission, require_permission

logger = logging.getLogger(__name__)

router = APIRouter()

_META_GRAPHRAG_INDEXER = None


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _iso_now() -> str:
    return _utc_now().isoformat()


def _get_meta_graphrag_indexer():
    """Lazy load Meta GraphRAG indexer for HTTP queries."""
    global _META_GRAPHRAG_INDEXER
    if _META_GRAPHRAG_INDEXER is not None:
        return _META_GRAPHRAG_INDEXER
    from tools.meta_graph_rag.config import load_config
    from tools.meta_graph_rag.indexer import MetaGraphIndexer

    config = load_config()
    _META_GRAPHRAG_INDEXER = MetaGraphIndexer(config)
    return _META_GRAPHRAG_INDEXER


def _hash_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _safe_excerpt(value: Optional[str], limit: int = 200) -> Optional[str]:
    if not value:
        return None
    value = value.strip()
    if len(value) <= limit:
        return value
    return value[:limit]


async def _audit_meta_graphrag(
    user: AuthenticatedUser,
    action: str,
    resource_id: str,
    success: bool,
    request: Optional[Request],
    details: Optional[Dict[str, Any]] = None,
) -> None:
    try:
        from core.audit import AuditLogger, AuditStatus

        await AuditLogger.log(
            tenant_id=UUID(user.tenant_id),
            user_id=UUID(user.user_id),
            action=action,
            resource_type="meta_graphrag",
            resource_id=resource_id,
            status=AuditStatus.SUCCESS if success else AuditStatus.ERROR,
            details=details,
            request=request,
        )
    except Exception as exc:
        logger.warning(f"[META_GRAPHRAG] Audit log failed: {exc}")


def _format_meta_chunk(chunk, include_text: bool = False) -> Dict[str, Any]:
    payload = {
        "path": chunk.path,
        "start_line": chunk.start_line,
        "end_line": chunk.end_line,
        "kind": chunk.kind,
        "node_id": chunk.node_id,
        "security_tags": chunk.metadata.get("security_tags", ""),
        "source_type": chunk.metadata.get("source_type", ""),
    }
    if include_text:
        payload["text"] = chunk.text
    else:
        payload["excerpt"] = chunk.text[:400]
    return payload


def _build_meta_graphrag_query(
    query: str,
    seed_limit: Optional[int],
    expansion_depth: Optional[int],
    expansion_limit: Optional[int],
    include_text: bool,
) -> Dict[str, Any]:
    if not query or not query.strip():
        raise ValueError("Query cannot be empty.")

    indexer = _get_meta_graphrag_indexer()
    seed_limit = seed_limit if seed_limit is not None else indexer.config.query_seed_limit
    expansion_depth = (
        expansion_depth if expansion_depth is not None else indexer.config.query_expansion_depth
    )
    expansion_limit = (
        expansion_limit if expansion_limit is not None else indexer.config.query_expansion_limit
    )

    if seed_limit < 0:
        seed_limit = 0
    if expansion_depth < 0:
        expansion_depth = 0
    if expansion_limit < 0:
        expansion_limit = 0

    seed_records = indexer.vector_index.query(query, limit=seed_limit)
    seed_chunks = []
    for record in seed_records:
        chunk = indexer.chunks.chunks.get(record.chunk_id)
        if chunk:
            seed_chunks.append(chunk)

    expanded_chunks = []
    if expansion_depth > 0 and expansion_limit > 0 and seed_chunks:
        from tools.meta_graph_rag.indexer import _expand_nodes

        adjacency = indexer.graph.build_adjacency()
        expanded_nodes: List[str] = []
        for chunk in seed_chunks:
            expanded_nodes.extend(_expand_nodes(adjacency, chunk.node_id, expansion_depth))
        expanded_nodes = list(dict.fromkeys(expanded_nodes))
        seed_chunk_ids = {chunk.chunk_id for chunk in seed_chunks}
        for node_id in expanded_nodes:
            for chunk in indexer.chunks.get_by_node(node_id):
                if chunk.chunk_id in seed_chunk_ids:
                    continue
                expanded_chunks.append(chunk)
                if len(expanded_chunks) >= expansion_limit:
                    break
            if len(expanded_chunks) >= expansion_limit:
                break

    return {
        "query": query,
        "generated_at": _iso_now(),
        "seed_limit": seed_limit,
        "expansion_depth": expansion_depth,
        "expansion_limit": expansion_limit,
        "seed_count": len(seed_chunks),
        "expanded_count": len(expanded_chunks),
        "seed_chunks": [_format_meta_chunk(chunk, include_text) for chunk in seed_chunks],
        "expanded_chunks": [_format_meta_chunk(chunk, include_text) for chunk in expanded_chunks],
    }


def _build_meta_graphrag_reports(
    entrypoints: Optional[List[str]],
    include_content: bool,
    fast: bool,
) -> Dict[str, Any]:
    from tools.meta_graph_rag.reports import generate_reports
    if fast:
        from tools.meta_graph_rag.config import load_config
        from tools.meta_graph_rag.snapshot import load_snapshot
        config = load_config()
        snapshot = load_snapshot(config)
        paths = generate_reports(
            graph=snapshot.graph,
            chunks_count=snapshot.chunks,
            vector_count=snapshot.vector_entries,
            output_dir=config.reports_path,
            entrypoints=entrypoints,
        )
    else:
        indexer = _get_meta_graphrag_indexer()
        status = indexer.status()
        paths = generate_reports(
            graph=indexer.graph,
            chunks_count=status["chunks"],
            vector_count=status["vector_entries"],
            output_dir=indexer.config.reports_path,
            entrypoints=entrypoints,
        )
    payload: Dict[str, Any] = {
        "generated_at": _iso_now(),
        "paths": {
            "overview": str(paths.overview),
            "top_down": str(paths.top_down),
            "bottom_up": str(paths.bottom_up),
            "security": str(paths.security),
            "module_catalog": str(paths.module_catalog),
        },
    }
    if include_content:
        payload["reports"] = {
            "overview": paths.overview.read_text(encoding="utf-8", errors="ignore"),
            "top_down": paths.top_down.read_text(encoding="utf-8", errors="ignore"),
            "bottom_up": paths.bottom_up.read_text(encoding="utf-8", errors="ignore"),
            "security": paths.security.read_text(encoding="utf-8", errors="ignore"),
            "module_catalog": paths.module_catalog.read_text(encoding="utf-8", errors="ignore"),
        }
    return payload


class GraphRagQueryRequest(BaseModel):
    """Request body for Meta GraphRAG query."""

    query: str = Field(..., min_length=1, description="Query text")
    seed_limit: Optional[int] = Field(default=None, ge=0, description="Seed top-k limit")
    expansion_depth: Optional[int] = Field(default=None, ge=0, description="Graph expansion depth")
    expansion_limit: Optional[int] = Field(default=None, ge=0, description="Expanded chunk limit")
    include_text: bool = Field(default=False, description="Include full chunk text")


class ReportsRequest(BaseModel):
    """Request body for report generation."""

    entrypoints: Optional[List[str]] = Field(default=None, description="Top-down entrypoints")
    include_content: bool = Field(default=False, description="Include report contents")
    fast: bool = Field(default=True, description="Use snapshot status (avoid loading vector index)")


class BriefingRequest(BaseModel):
    """Request body for briefing pack."""

    entrypoints: Optional[List[str]] = Field(default=None, description="Top-down entrypoints")
    include_content: bool = Field(default=True, description="Include report contents")
    fast: bool = Field(default=True, description="Use snapshot status (avoid loading vector index)")


@router.get("/status")
async def meta_graphrag_status(
    request: Request,
    fast: bool = True,
    user: AuthenticatedUser = Depends(require_permission(Permission.FILE_READ, "meta_graphrag")),
) -> Dict[str, Any]:
    """Return Meta GraphRAG index status."""
    if fast:
        from tools.meta_graph_rag.config import load_config
        from tools.meta_graph_rag.snapshot import load_snapshot
        config = load_config()
        snapshot = load_snapshot(config)
        payload = {
            "nodes": len(snapshot.graph.nodes),
            "edges": len(snapshot.graph.edges),
            "chunks": snapshot.chunks,
            "vector_entries": snapshot.vector_entries,
            "embedding_backend": snapshot.embedding_backend,
            "graph_db": snapshot.graph_db,
            "manifest_generated_at": snapshot.manifest_generated_at,
            "status_source": "snapshot",
        }
        await _audit_meta_graphrag(
            user=user,
            action="meta_graphrag:status",
            resource_id="status:snapshot",
            success=True,
            request=request,
            details={"fast": True},
        )
        return payload

    payload = _get_meta_graphrag_indexer().status()
    await _audit_meta_graphrag(
        user=user,
        action="meta_graphrag:status",
        resource_id="status:live",
        success=True,
        request=request,
        details={"fast": False},
    )
    return payload


@router.post("/query")
async def meta_graphrag_query(
    body: GraphRagQueryRequest,
    request: Request,
    user: AuthenticatedUser = Depends(require_permission(Permission.FILE_READ, "meta_graphrag")),
) -> Dict[str, Any]:
    """Run a Meta GraphRAG query with optional graph expansion."""
    try:
        payload = _build_meta_graphrag_query(
            query=body.query,
            seed_limit=body.seed_limit,
            expansion_depth=body.expansion_depth,
            expansion_limit=body.expansion_limit,
            include_text=body.include_text,
        )
        await _audit_meta_graphrag(
            user=user,
            action="meta_graphrag:query",
            resource_id=f"query:{_hash_text(body.query)}",
            success=True,
            request=request,
            details={
                "query_len": len(body.query),
                "query_excerpt": _safe_excerpt(body.query),
                "seed_limit": payload.get("seed_limit"),
                "expansion_depth": payload.get("expansion_depth"),
                "expansion_limit": payload.get("expansion_limit"),
                "seed_count": payload.get("seed_count"),
                "expanded_count": payload.get("expanded_count"),
                "include_text": body.include_text,
            },
        )
        return payload
    except ValueError as exc:
        await _audit_meta_graphrag(
            user=user,
            action="meta_graphrag:query",
            resource_id="query:invalid",
            success=False,
            request=request,
            details={"error": str(exc)},
        )
        raise HTTPException(400, str(exc)) from exc
    except Exception as exc:
        logger.error(f"[META_GRAPHRAG] Query failed: {exc}")
        await _audit_meta_graphrag(
            user=user,
            action="meta_graphrag:query",
            resource_id="query:error",
            success=False,
            request=request,
            details={"error": str(exc)},
        )
        raise HTTPException(500, f"Meta GraphRAG query failed: {exc}") from exc


@router.post("/reports")
async def meta_graphrag_reports(
    body: ReportsRequest,
    request: Request,
    user: AuthenticatedUser = Depends(require_permission(Permission.FILE_READ, "meta_graphrag")),
) -> Dict[str, Any]:
    """Generate and return Meta GraphRAG reports."""
    try:
        payload = _build_meta_graphrag_reports(
            entrypoints=body.entrypoints,
            include_content=body.include_content,
            fast=body.fast,
        )
        await _audit_meta_graphrag(
            user=user,
            action="meta_graphrag:reports",
            resource_id="reports",
            success=True,
            request=request,
            details={
                "entrypoints_count": len(body.entrypoints or []),
                "entrypoints_sample": (body.entrypoints or [])[:5],
                "include_content": body.include_content,
                "fast": body.fast,
            },
        )
        return payload
    except Exception as exc:
        logger.error(f"[META_GRAPHRAG] Report generation failed: {exc}")
        await _audit_meta_graphrag(
            user=user,
            action="meta_graphrag:reports",
            resource_id="reports:error",
            success=False,
            request=request,
            details={"error": str(exc)},
        )
        raise HTTPException(500, f"Meta GraphRAG report generation failed: {exc}") from exc


@router.post("/briefing")
async def meta_graphrag_briefing(
    body: BriefingRequest,
    request: Request,
    user: AuthenticatedUser = Depends(require_permission(Permission.FILE_READ, "meta_graphrag")),
) -> Dict[str, Any]:
    """Return a briefing pack (top-down, bottom-up, module catalog)."""
    try:
        payload = _build_meta_graphrag_reports(
            entrypoints=body.entrypoints,
            include_content=body.include_content,
            fast=body.fast,
        )
        reports = payload.get("reports", {})
        payload["briefing"] = {
            "top_down": reports.get("top_down", ""),
            "bottom_up": reports.get("bottom_up", ""),
            "module_catalog": reports.get("module_catalog", ""),
            "overview": reports.get("overview", ""),
            "security": reports.get("security", ""),
        }
        await _audit_meta_graphrag(
            user=user,
            action="meta_graphrag:briefing",
            resource_id="briefing",
            success=True,
            request=request,
            details={
                "entrypoints_count": len(body.entrypoints or []),
                "entrypoints_sample": (body.entrypoints or [])[:5],
                "include_content": body.include_content,
                "fast": body.fast,
            },
        )
        return payload
    except Exception as exc:
        logger.error(f"[META_GRAPHRAG] Briefing failed: {exc}")
        await _audit_meta_graphrag(
            user=user,
            action="meta_graphrag:briefing",
            resource_id="briefing:error",
            success=False,
            request=request,
            details={"error": str(exc)},
        )
        raise HTTPException(500, f"Meta GraphRAG briefing failed: {exc}") from exc
