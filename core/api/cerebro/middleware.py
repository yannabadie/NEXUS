"""
NEXUS V10 CEREBRO - Tenant Context Middleware

Hydrates PRISM SessionContext from JWT for HTTP requests.
WebSocket connections use dependency injection instead (see deps.py).

JWT Payload Expected:
{
    "sub": "user_id",
    "tenant_id": "tenant_abc",
    "workspace_id": "default",
    "exp": 1234567890
}
"""

import logging
from typing import Optional

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger(__name__)

# JWT secret (should come from config in production)
JWT_SECRET = "nexus-cerebro-dev-secret"  # TODO: Load from env
JWT_ALGORITHM = "HS256"


def decode_jwt(token: str) -> Optional[dict]:
    """
    Decode and validate JWT token.

    Args:
        token: JWT token string

    Returns:
        Decoded claims dict or None if invalid
    """
    try:
        from jose import jwt, JWTError

        claims = jwt.decode(
            token,
            JWT_SECRET,
            algorithms=[JWT_ALGORITHM],
            options={"verify_exp": True}
        )
        return claims
    except ImportError:
        logger.warning("python-jose not installed, JWT auth disabled")
        return None
    except Exception as e:
        logger.debug(f"JWT decode failed: {e}")
        return None


class TenantContextMiddleware(BaseHTTPMiddleware):
    """
    Middleware to hydrate PRISM SessionContext from JWT.

    Only applies to HTTP requests, not WebSocket (websocket scope type).
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        """
        Process request and hydrate tenant context.

        Args:
            request: Starlette Request
            call_next: Next middleware/handler

        Returns:
            Response
        """
        # Skip WebSocket connections - they use dependency injection
        if request.scope.get("type") == "websocket":
            return await call_next(request)

        # Try to extract JWT from Authorization header
        auth_header = request.headers.get("Authorization", "")

        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
            claims = decode_jwt(token)

            if claims:
                # Hydrate PRISM context
                try:
                    from core.context import use_context_async

                    async with use_context_async(
                        tenant_id=claims.get("tenant_id", "anonymous"),
                        user_id=claims.get("sub", "anonymous"),
                        workspace_id=claims.get("workspace_id", "default"),
                    ):
                        return await call_next(request)

                except ImportError:
                    # context module not available
                    pass

        # No auth or auth failed - continue without context
        return await call_next(request)


def create_jwt_token(
    tenant_id: str,
    user_id: str = "anonymous",
    workspace_id: str = "default",
    expires_in_seconds: int = 3600,
) -> str:
    """
    Create a JWT token for testing.

    Args:
        tenant_id: Tenant identifier
        user_id: User identifier
        workspace_id: Workspace identifier
        expires_in_seconds: Token expiration time

    Returns:
        JWT token string
    """
    from datetime import datetime, timezone, timedelta
    from jose import jwt

    now = datetime.now(timezone.utc)
    claims = {
        "sub": user_id,
        "tenant_id": tenant_id,
        "workspace_id": workspace_id,
        "iat": now,
        "exp": now + timedelta(seconds=expires_in_seconds),
    }

    return jwt.encode(claims, JWT_SECRET, algorithm=JWT_ALGORITHM)
