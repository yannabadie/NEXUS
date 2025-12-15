"""
NEXUS V11.6 KEYMAKER - Authentication Endpoints

Provides JWT authentication for CEREBRO UI:
- POST /api/auth/login : Authenticate and get JWT token
- GET /api/auth/me : Verify token and get user info
- POST /api/auth/refresh : Refresh token (future)

Security Notes (MVP):
- Single admin password via NEXUS_ADMIN_PASSWORD env var
- 24h token expiration (consider shorter for production)
- No refresh token (TODO V11.7)

Author: Claude (NEXUS V11.6 KEYMAKER)
Date: 2025-12-15
"""

import logging
import os
from typing import Optional

from fastapi import APIRouter, HTTPException, Header, status
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter()

# =============================================================================
# Configuration
# =============================================================================

# MVP: Single admin password from environment
# Production: Replace with user database
ADMIN_PASSWORD = os.environ.get("NEXUS_ADMIN_PASSWORD", "nexus")
TOKEN_EXPIRE_HOURS = 24

# Warn if using default password
if ADMIN_PASSWORD == "nexus":
    logger.warning(
        "NEXUS_ADMIN_PASSWORD not set! Using default 'nexus'. "
        "Set NEXUS_ADMIN_PASSWORD environment variable for security."
    )


# =============================================================================
# Request/Response Models
# =============================================================================

class LoginRequest(BaseModel):
    """Login request body."""
    username: str
    password: str


class TokenResponse(BaseModel):
    """Login response with JWT token."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds
    tenant_id: str
    user_id: str


class UserInfo(BaseModel):
    """Current user info response."""
    user_id: str
    tenant_id: str
    workspace_id: str
    authenticated: bool = True


# =============================================================================
# Endpoints
# =============================================================================

@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest) -> TokenResponse:
    """
    Authenticate user and return JWT token.

    MVP Implementation:
    - Single admin password (NEXUS_ADMIN_PASSWORD env var)
    - Username becomes user_id in token
    - Default tenant_id = "default"

    Args:
        body: LoginRequest with username and password

    Returns:
        TokenResponse with access_token, expires_in, etc.

    Raises:
        401: Invalid credentials
    """
    # Validate password (MVP: single admin password)
    if body.password != ADMIN_PASSWORD:
        logger.warning(f"[KEYMAKER] Failed login attempt for user: {body.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Generate JWT token
    try:
        from ..middleware import create_jwt_token

        expires_seconds = TOKEN_EXPIRE_HOURS * 3600
        token = create_jwt_token(
            tenant_id="default",  # MVP: single tenant
            user_id=body.username,
            workspace_id="default",
            expires_in_seconds=expires_seconds,
        )

        logger.info(f"[KEYMAKER] Login successful for user: {body.username}")

        return TokenResponse(
            access_token=token,
            expires_in=expires_seconds,
            tenant_id="default",
            user_id=body.username,
        )

    except ImportError as e:
        logger.error(f"[KEYMAKER] JWT library not available: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication service unavailable (python-jose not installed)",
        )
    except Exception as e:
        logger.error(f"[KEYMAKER] Token generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token generation failed",
        )


@router.get("/me", response_model=UserInfo)
async def get_current_user(
    authorization: Optional[str] = Header(None, description="Bearer token")
) -> UserInfo:
    """
    Verify token and return current user info.

    Used by UI to:
    - Check if stored token is still valid on page load
    - Get user info for display

    Args:
        authorization: Bearer token in Authorization header

    Returns:
        UserInfo with user_id, tenant_id, workspace_id

    Raises:
        401: Not authenticated or invalid token
    """
    # Check Authorization header
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format. Use: Bearer <token>",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Extract and decode token
    token = authorization[7:]

    try:
        from ..middleware import decode_jwt

        claims = decode_jwt(token)

        if not claims:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return UserInfo(
            user_id=claims.get("sub", "anonymous"),
            tenant_id=claims.get("tenant_id", "default"),
            workspace_id=claims.get("workspace_id", "default"),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[KEYMAKER] Token verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token verification failed",
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.post("/logout")
async def logout() -> dict:
    """
    Logout endpoint (client-side token invalidation).

    Note: JWT tokens are stateless, so logout is handled client-side
    by removing the token from storage. This endpoint exists for
    API completeness and potential future server-side invalidation.

    Returns:
        {"status": "logged_out"}
    """
    # MVP: No server-side token invalidation
    # Future: Add token to blacklist in Redis
    return {"status": "logged_out", "message": "Remove token from client storage"}
