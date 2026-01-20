"""
NEXUS V12.2 CEREBRO - FastAPI Application Factory

Creates the CEREBRO API application with:
- Redis connection lifecycle management
- Tenant context middleware (HTTP only)
- WebSocket streaming endpoint
- Health check endpoints
- V11.5 CORTEX: State snapshot, interactions, workflow, files endpoints
- V11.6 KEYMAKER: JWT authentication endpoints
- V12.1 RETINA: HTTP rate limiting (Conseiller 1 feedback)
- V12.2 IRONCLAD: User management API, RBAC enforcement

V11.3 HARDENING: CORS origins from environment variable.
V11.5 CORTEX: API control & state persistence for CEREBRO UI.
V11.6 KEYMAKER: Authentication endpoints (login, me, logout, refresh).
V12.1 RETINA: Rate limiting on sensitive endpoints.
V12.2 IRONCLAD: User management (invite, remove, change role).

Usage:
    uvicorn core.api.cerebro.app:create_cerebro_app --factory --port 8080
"""

import logging
import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator, List

# V13.0: Passlib 1.7.4 + bcrypt 4.x compatibility
# passlib logs "error reading bcrypt version" at WARNING level due to bcrypt 4.x API change
# This is a known issue: https://github.com/pyca/bcrypt/issues/684
# Fix: Set logger level to ERROR to suppress this specific warning
logging.getLogger("passlib.handlers.bcrypt").setLevel(logging.ERROR)

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
    - V12.0: Register main event loop for in-memory pub/sub

    Shutdown:
    - Disconnect from Redis
    """
    import asyncio

    # Startup
    logger.info("CEREBRO API: Starting up...")
    bus = get_redis_bus()

    # V12.0: Register main event loop for thread-safe in-memory pub/sub
    main_loop = asyncio.get_running_loop()
    bus.set_main_loop(main_loop)

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

    # V12.1 RETINA: Rate limiting middleware (Conseiller 1 feedback)
    from .rate_limit import setup_rate_limiting
    setup_rate_limiting(app)

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

    # V12.2 IRONCLAD routers
    from .routes import users
    app.include_router(users.router, prefix="/api/users", tags=["users"])

    # V13.0 MEMORIA UNIVERSALIS routers
    from .routes import memory
    app.include_router(memory.router, prefix="/api/memory", tags=["memory"])

    # Root endpoint
    @app.get("/", tags=["root"])
    async def root():
        """Root endpoint with API info."""
        return {
            "service": "NEXUS CEREBRO API",
            "version": "13.0.0",  # V13.0 MEMORIA UNIVERSALIS
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
            "auth_refresh": "/api/auth/refresh",
            # V12.2 IRONCLAD endpoints
            "users": "/api/users",
            "users_invite": "/api/users/invite",
            # V13.0 MEMORIA UNIVERSALIS endpoints
            "memory": "/api/memory/stats",
            "memory_namespaces": "/api/memory/namespaces",
            "memory_ingest": "/api/memory/ingest",
        }

    return app


# For uvicorn direct usage
app = create_cerebro_app()
