"""
NEXUS V10 CEREBRO - FastAPI Dependencies

Dependency injection for WebSocket authentication and context extraction.

WebSocket Auth Methods:
1. Query params: ?tenant_id=xxx&token=yyy
2. First message: {"type": "auth", "tenant_id": "xxx", "token": "yyy"}

Note: HTTP requests use TenantContextMiddleware instead.
"""

import logging
from dataclasses import dataclass
from typing import Optional

from fastapi import WebSocket, HTTPException, status

logger = logging.getLogger(__name__)


@dataclass
class WebSocketContext:
    """
    Context extracted from WebSocket connection.

    Provides tenant isolation info for event filtering.
    """

    tenant_id: str
    user_id: str
    workspace_id: str

    def __str__(self) -> str:
        return f"WebSocketContext(tenant={self.tenant_id}, user={self.user_id}, ws={self.workspace_id})"


def _decode_token(token: str) -> Optional[dict]:
    """Decode JWT token and return claims."""
    try:
        from jose import jwt
        from .middleware import JWT_SECRET, JWT_ALGORITHM

        return jwt.decode(
            token,
            JWT_SECRET,
            algorithms=[JWT_ALGORITHM],
            options={"verify_exp": True}
        )
    except Exception as e:
        logger.debug(f"Token decode failed: {e}")
        return None


async def get_ws_context(websocket: WebSocket) -> WebSocketContext:
    """
    Extract context from WebSocket connection.

    Auth Methods (in order):
    1. Query param 'token' (JWT)
    2. Query param 'tenant_id' (simple auth for dev)

    Args:
        websocket: FastAPI WebSocket connection

    Returns:
        WebSocketContext with tenant/user/workspace info

    Raises:
        HTTPException: If no valid auth provided
    """
    # Method 1: JWT token in query params
    token = websocket.query_params.get("token")
    if token:
        claims = _decode_token(token)
        if claims:
            return WebSocketContext(
                tenant_id=claims.get("tenant_id", "anonymous"),
                user_id=claims.get("sub", "anonymous"),
                workspace_id=claims.get("workspace_id", "default"),
            )

    # Method 2: Simple tenant_id in query params (dev mode)
    tenant_id = websocket.query_params.get("tenant_id")
    if tenant_id:
        return WebSocketContext(
            tenant_id=tenant_id,
            user_id=websocket.query_params.get("user_id", "anonymous"),
            workspace_id=websocket.query_params.get("workspace_id", "default"),
        )

    # No auth - reject
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="WebSocket requires authentication. Use ?token=<jwt> or ?tenant_id=<id>",
    )


async def get_ws_context_optional(websocket: WebSocket) -> Optional[WebSocketContext]:
    """
    Extract context from WebSocket connection (optional).

    Same as get_ws_context but returns None instead of raising exception.

    Args:
        websocket: FastAPI WebSocket connection

    Returns:
        WebSocketContext or None if no valid auth
    """
    try:
        return await get_ws_context(websocket)
    except HTTPException:
        return None


def create_ws_url(
    base_url: str,
    tenant_id: str,
    workspace_id: str = "default",
    token: Optional[str] = None,
) -> str:
    """
    Create WebSocket URL with auth params.

    Args:
        base_url: Base WebSocket URL (e.g., "ws://localhost:8080/ws/stream")
        tenant_id: Tenant identifier
        workspace_id: Workspace identifier
        token: Optional JWT token

    Returns:
        Complete WebSocket URL with query params

    Example:
        url = create_ws_url("ws://localhost:8080/ws/stream", "tenant_1")
        # -> "ws://localhost:8080/ws/stream?tenant_id=tenant_1&workspace_id=default"
    """
    params = [f"tenant_id={tenant_id}", f"workspace_id={workspace_id}"]
    if token:
        params.append(f"token={token}")
    return f"{base_url}?{'&'.join(params)}"
