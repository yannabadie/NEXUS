"""
NEXUS V10 CEREBRO - FastAPI Application Factory

Creates the CEREBRO API application with:
- Redis connection lifecycle management
- Tenant context middleware (HTTP only)
- WebSocket streaming endpoint
- Health check endpoints
- V11.5 CORTEX: State snapshot, interactions, workflow, files endpoints
- V11.6 KEYMAKER: JWT authentication endpoints

V11.3 HARDENING: CORS origins from environment variable.
V11.5 CORTEX: API control & state persistence for CEREBRO UI.
V11.6 KEYMAKER: Authentication endpoints (login, me, logout).

Usage:
    uvicorn core.api.cerebro.app:create_cerebro_app --factory --port 8080
"""

import logging
import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator, List

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.events.redis_bus import get_redis_bus

logger = logging.getLogger(__name__)

# V11.3 HARDENING: CORS origins from environment (comma-separated)
# Example: NEXUS_CORS_ORIGINS=http://localhost:3000,https://nexus.example.com
_cors_env = os.environ.get("NEXUS_CORS_ORIGINS", "http://localhost:3000")
CORS_ORIGINS: List[str] = [origin.strip() for origin in _cors_env.split(",") if origin.strip()]

if not CORS_ORIGINS:
    CORS_ORIGINS = ["http://localhost:3000"]
    logger.warning("NEXUS_CORS_ORIGINS not set, defaulting to localhost:3000")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan: startup and shutdown events.

    Startup:
    - Connect to Redis

    Shutdown:
    - Disconnect from Redis
    """
    # Startup
    logger.info("CEREBRO API: Starting up...")
    bus = get_redis_bus()
    connected = await bus.connect()
    if connected:
        logger.info("CEREBRO API: Redis connected")
    else:
        logger.warning("CEREBRO API: Redis not available, running in degraded mode")

    yield  # Application runs here

    # Shutdown
    logger.info("CEREBRO API: Shutting down...")
    await bus.disconnect()
    logger.info("CEREBRO API: Redis disconnected")


def create_cerebro_app() -> FastAPI:
    """
    Create the CEREBRO FastAPI application.

    Returns:
        Configured FastAPI application instance
    """
    app = FastAPI(
        title="NEXUS CEREBRO API",
        description="Real-time event streaming API for NEXUS V10",
        version="10.0.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    # V11.3 HARDENING: CORS with explicit origins (not wildcard)
    # Note: allow_credentials=True requires explicit origins, not ["*"]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Tenant-ID"],
    )

    # Tenant context middleware (HTTP only, not WebSocket)
    from .middleware import TenantContextMiddleware
    app.add_middleware(TenantContextMiddleware)

    # Include routers
    from .routes import health, stream

    # Core routers (V10)
    app.include_router(health.router, prefix="/health", tags=["health"])
    app.include_router(stream.router, prefix="/ws", tags=["websocket"])

    # V11.5 CORTEX routers
    from .routes import state, interactions, workflow, files
    app.include_router(state.router, prefix="/api/state", tags=["state"])
    app.include_router(interactions.router, prefix="/api/interactions", tags=["interactions"])
    app.include_router(workflow.router, prefix="/api/workflow", tags=["workflow"])
    app.include_router(files.router, prefix="/api/files", tags=["files"])

    # V11.6 KEYMAKER routers
    from .routes import auth
    app.include_router(auth.router, prefix="/api/auth", tags=["auth"])

    # Root endpoint
    @app.get("/", tags=["root"])
    async def root():
        """Root endpoint with API info."""
        return {
            "service": "NEXUS CEREBRO API",
            "version": "11.6.0",  # V11.6 KEYMAKER
            "docs": "/docs",
            "health": "/health",
            "websocket": "/ws/stream",
            # V11.5 CORTEX endpoints
            "state": "/api/state/snapshot",
            "interactions": "/api/interactions/pending",
            "workflow": "/api/workflow/start",
            "files": "/api/files/content",
            # V11.6 KEYMAKER endpoints
            "auth": "/api/auth/login",
        }

    return app


# For uvicorn direct usage
app = create_cerebro_app()
