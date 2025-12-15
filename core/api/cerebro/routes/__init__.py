"""
NEXUS V10 CEREBRO - API Routes Package

Routes:
- health: Health check endpoints (/health, /health/ready)
- stream: WebSocket streaming endpoint (/ws/stream)
"""

from . import health, stream

__all__ = ["health", "stream"]
