"""
NEXUS V10 CEREBRO - WebSocket Streaming Endpoint

Streams NEXUS events to connected UI clients via WebSocket.

Usage:
    # Connect with tenant_id (dev mode)
    ws://localhost:8080/ws/stream?tenant_id=tenant_1&workspace_id=default

    # Connect with JWT token
    ws://localhost:8080/ws/stream?token=<jwt>

Events are streamed as JSON:
    {
        "event_type": "interaction.ask",
        "payload": {"prompt": "Continue?"},
        "timestamp": "2025-12-15T10:30:00Z",
        "event_id": "abc123"
    }
"""

import asyncio
import logging
from typing import List, Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query

from core.events.redis_bus import get_redis_bus
from core.events.types import CerebroEvent, CerebroEventType
from ..deps import WebSocketContext

logger = logging.getLogger(__name__)

router = APIRouter()


async def _get_context_from_params(
    websocket: WebSocket,
    tenant_id: Optional[str],
    workspace_id: str,
    token: Optional[str],
) -> Optional[WebSocketContext]:
    """Extract context from query params."""
    # Try JWT token first
    if token:
        try:
            from ..deps import _decode_token
            claims = _decode_token(token)
            if claims:
                return WebSocketContext(
                    tenant_id=claims.get("tenant_id", "anonymous"),
                    user_id=claims.get("sub", "anonymous"),
                    workspace_id=claims.get("workspace_id", workspace_id),
                )
        except Exception:
            pass

    # Fall back to simple tenant_id
    if tenant_id:
        return WebSocketContext(
            tenant_id=tenant_id,
            user_id="anonymous",
            workspace_id=workspace_id,
        )

    return None


@router.websocket("/stream")
async def websocket_stream(
    websocket: WebSocket,
    tenant_id: Optional[str] = Query(None, description="Tenant identifier"),
    workspace_id: str = Query("default", description="Workspace identifier"),
    token: Optional[str] = Query(None, description="JWT auth token"),
    event_types: Optional[str] = Query(None, description="Comma-separated event types to filter"),
):
    """
    Stream events to connected WebSocket clients.

    Query Parameters:
        tenant_id: Tenant identifier (required unless token provided)
        workspace_id: Workspace identifier (default: "default")
        token: JWT authentication token
        event_types: Comma-separated list of event types to subscribe to

    Events are sent as JSON objects with event_type, payload, timestamp, event_id.
    """
    # Extract context
    ctx = await _get_context_from_params(websocket, tenant_id, workspace_id, token)

    if not ctx:
        await websocket.close(code=4001, reason="Authentication required")
        return

    # Accept connection
    await websocket.accept()
    logger.info(f"CEREBRO: WebSocket connected for {ctx}")

    # Parse event type filter
    filter_types: Optional[List[CerebroEventType]] = None
    if event_types:
        try:
            filter_types = [
                CerebroEventType(et.strip())
                for et in event_types.split(",")
            ]
        except ValueError as e:
            await websocket.send_json({"error": f"Invalid event_type: {e}"})

    # Get Redis bus
    bus = get_redis_bus()

    if not bus.is_connected():
        await websocket.send_json({
            "event_type": "system.warning",
            "payload": {"message": "Redis not connected, streaming unavailable"},
        })
        # Keep connection open for potential reconnect
        try:
            while True:
                # Wait for client messages (e.g., ping/pong)
                data = await websocket.receive_text()
                if data == "ping":
                    await websocket.send_text("pong")
        except WebSocketDisconnect:
            logger.info(f"CEREBRO: WebSocket disconnected (no Redis): {ctx}")
            return

    # Stream events from Redis
    try:
        # Send initial connected message
        await websocket.send_json({
            "event_type": "system.connected",
            "payload": {
                "tenant_id": ctx.tenant_id,
                "workspace_id": ctx.workspace_id,
                "filter": [et.value for et in filter_types] if filter_types else "all",
            },
        })

        # Subscribe and stream events
        async for event in bus.subscribe(
            tenant_id=ctx.tenant_id,
            workspace_id=ctx.workspace_id,
            event_types=filter_types,
        ):
            await websocket.send_json({
                "event_type": event.event_type.value,
                "payload": event.payload,
                "timestamp": event.timestamp,
                "event_id": event.event_id,
            })

    except WebSocketDisconnect:
        logger.info(f"CEREBRO: WebSocket disconnected: {ctx}")
    except asyncio.CancelledError:
        logger.debug(f"CEREBRO: WebSocket cancelled: {ctx}")
    except Exception as e:
        logger.error(f"CEREBRO: WebSocket error: {e}")
        try:
            await websocket.send_json({
                "event_type": "system.error",
                "payload": {"message": str(e)},
            })
        except Exception:
            pass


@router.websocket("/echo")
async def websocket_echo(websocket: WebSocket):
    """
    Echo WebSocket for testing.

    Echoes back any message received.
    """
    await websocket.accept()
    logger.debug("CEREBRO: Echo WebSocket connected")

    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"echo: {data}")
    except WebSocketDisconnect:
        logger.debug("CEREBRO: Echo WebSocket disconnected")
