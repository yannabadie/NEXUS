"""
NEXUS V10 CEREBRO - Health Check Endpoints

Endpoints:
- GET /health     : Basic liveness check
- GET /health/ready : Readiness check with Redis status
- GET /health/info  : Detailed system info
"""

import logging
from typing import Any, Dict

from fastapi import APIRouter

from core.events.redis_bus import get_redis_bus

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/")
async def health() -> Dict[str, str]:
    """
    Basic liveness check.

    Returns:
        {"status": "healthy", "service": "cerebro"}
    """
    return {
        "status": "healthy",
        "service": "cerebro",
    }


@router.get("/ready")
async def readiness() -> Dict[str, Any]:
    """
    Readiness check with Redis status.

    Returns:
        Status dict with Redis connection info
    """
    bus = get_redis_bus()
    redis_health = await bus.health_check()

    # Determine overall status
    if redis_health.get("status") == "healthy":
        status = "ready"
    elif redis_health.get("connected"):
        status = "ready"  # Connected but maybe slow
    else:
        status = "degraded"  # Running without Redis

    return {
        "status": status,
        "service": "cerebro",
        "version": "10.0.0",
        "redis": redis_health,
    }


@router.get("/info")
async def info() -> Dict[str, Any]:
    """
    Detailed system information.

    Returns:
        System info including Redis server details
    """
    bus = get_redis_bus()
    redis_info = await bus.get_info()
    redis_health = await bus.health_check()

    return {
        "service": "cerebro",
        "version": "10.0.0",
        "redis": {
            "connected": bus.is_connected(),
            "health": redis_health,
            "server": redis_info,
        },
    }


@router.get("/ping")
async def ping() -> Dict[str, str]:
    """
    Simple ping endpoint for monitoring.

    Returns:
        {"pong": "ok"}
    """
    return {"pong": "ok"}
