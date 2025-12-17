"""
NEXUS V10 CEREBRO - FastAPI Application Package

WebSocket API for external UI observation of NEXUS events.

Usage:
    # Start server
    uvicorn core.api.cerebro.app:create_cerebro_app --factory --port 8080

    # Or import app factory
    from core.api.cerebro import create_cerebro_app
    app = create_cerebro_app()
"""

from .app import create_cerebro_app

__all__ = ["create_cerebro_app"]
