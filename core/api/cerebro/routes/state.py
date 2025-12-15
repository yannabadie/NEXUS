"""
NEXUS V11.5 CORTEX - State Snapshot Endpoint
V11.6 KEYMAKER - Optional authentication support

Enables F5 Recovery for CEREBRO UI:
- GET /api/state/snapshot : Get state snapshot for UI hydration
- DELETE /api/state/snapshot : Clear state (for testing)

The snapshot includes:
- Phase state (current HiveMind phase)
- Graph nodes (agents in the swarm)
- Recent logs (last 100 entries)
- Pending interactions (CRITICAL: for Fantôme fix)

Authentication:
- V11.6: Optional auth - uses token tenant_id if provided, falls back to query param
- Production: Change to require_auth for mandatory authentication

Author: Claude (NEXUS V11.5 CORTEX)
Date: 2025-12-15
"""

import json
import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from ..deps import AuthenticatedUser, get_current_user_optional

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/snapshot")
async def get_state_snapshot(
    user: Optional[AuthenticatedUser] = Depends(get_current_user_optional),
    tenant_id: Optional[str] = Query(None, description="Tenant identifier (fallback if no auth)"),
    workspace_id: str = Query("default", description="Workspace identifier"),
) -> Dict[str, Any]:
    """
    Get state snapshot for UI hydration (F5 recovery).

    Called by CEREBRO UI on page load/refresh to restore state.

    Args:
        tenant_id: Tenant identifier (required)
        workspace_id: Workspace identifier (default: "default")

    Returns:
        Dict with:
        - phase: Current HiveMind phase state (or None)
        - nodes: Dict of graph nodes by node_id
        - logs: List of recent log entries (max 100)
        - pending_interactions: List of pending human-in-the-loop requests (CRITICAL)
        - tenant_id: Tenant identifier
        - workspace_id: Workspace identifier

    Raises:
        503: Redis not available
        500: Snapshot failed
    """
    # V11.6: Resolve tenant_id from auth token or query param
    actual_tenant_id = user.tenant_id if user else tenant_id
    if not actual_tenant_id:
        raise HTTPException(400, "tenant_id required (via auth token or query param)")

    actual_workspace_id = user.workspace_id if user else workspace_id

    try:
        from core.events.redis_bus import get_redis_bus
        bus = get_redis_bus()
    except Exception as e:
        logger.error(f"Failed to get Redis bus: {e}")
        raise HTTPException(503, "Redis bus unavailable")

    if not bus.is_connected():
        raise HTTPException(503, "Redis not connected")

    redis = bus._redis
    if not redis:
        raise HTTPException(503, "Redis client unavailable")

    base_key = f"nexus:{actual_tenant_id}:{actual_workspace_id}:state"

    try:
        # Get phase state
        phase_raw = await redis.get(f"{base_key}:phase")
        phase = json.loads(phase_raw) if phase_raw else None

        # Get graph nodes (hash)
        nodes_raw = await redis.hgetall(f"{base_key}:nodes")
        nodes = {}
        if nodes_raw:
            for k, v in nodes_raw.items():
                key = k.decode() if isinstance(k, bytes) else k
                val = v.decode() if isinstance(v, bytes) else v
                nodes[key] = json.loads(val)

        # Get logs (list, most recent first)
        logs_raw = await redis.lrange(f"{base_key}:logs", 0, 99)
        logs = []
        if logs_raw:
            for log_entry in logs_raw:
                entry = log_entry.decode() if isinstance(log_entry, bytes) else log_entry
                logs.append(json.loads(entry))

        # CRITICAL: Get pending interactions from HeadlessProvider
        # This fixes the "Fantôme de la Question" bug
        pending_interactions = []
        try:
            from core.interaction import get_interaction_provider
            provider = get_interaction_provider()
            if hasattr(provider, 'get_pending_requests'):
                pending_interactions = provider.get_pending_requests()
        except Exception as e:
            logger.debug(f"Could not get pending interactions: {e}")

        logger.info(
            f"[CORTEX] Snapshot retrieved: tenant={actual_tenant_id}, "
            f"workspace={actual_workspace_id}, nodes={len(nodes)}, "
            f"logs={len(logs)}, pending={len(pending_interactions)}"
        )

        return {
            "phase": phase,
            "nodes": nodes,
            "logs": logs,
            "pending_interactions": pending_interactions,
            "tenant_id": actual_tenant_id,
            "workspace_id": actual_workspace_id,
        }

    except Exception as e:
        logger.error(f"Snapshot failed: {e}")
        raise HTTPException(500, f"Snapshot failed: {e}")


@router.delete("/snapshot")
async def clear_state_snapshot(
    user: Optional[AuthenticatedUser] = Depends(get_current_user_optional),
    tenant_id: Optional[str] = Query(None, description="Tenant identifier (fallback if no auth)"),
    workspace_id: str = Query("default", description="Workspace identifier"),
) -> Dict[str, str]:
    """
    Clear state snapshot (for testing/debugging).

    Removes all persisted state for a tenant/workspace.

    Args:
        tenant_id: Tenant identifier (required)
        workspace_id: Workspace identifier (default: "default")

    Returns:
        {"status": "cleared"}

    Raises:
        503: Redis not available
    """
    # V11.6: Resolve tenant_id from auth token or query param
    actual_tenant_id = user.tenant_id if user else tenant_id
    if not actual_tenant_id:
        raise HTTPException(400, "tenant_id required (via auth token or query param)")

    actual_workspace_id = user.workspace_id if user else workspace_id

    try:
        from core.events.redis_bus import get_redis_bus
        bus = get_redis_bus()
    except Exception as e:
        logger.error(f"Failed to get Redis bus: {e}")
        raise HTTPException(503, "Redis bus unavailable")

    if not bus.is_connected():
        raise HTTPException(503, "Redis not connected")

    redis = bus._redis
    if not redis:
        raise HTTPException(503, "Redis client unavailable")

    base_key = f"nexus:{actual_tenant_id}:{actual_workspace_id}:state"

    try:
        await redis.delete(
            f"{base_key}:phase",
            f"{base_key}:nodes",
            f"{base_key}:logs"
        )
        logger.info(f"[CORTEX] State cleared: tenant={actual_tenant_id}, workspace={actual_workspace_id}")
        return {"status": "cleared"}
    except Exception as e:
        logger.error(f"Clear failed: {e}")
        raise HTTPException(500, f"Clear failed: {e}")
