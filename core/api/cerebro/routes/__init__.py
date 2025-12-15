"""
NEXUS V10 CEREBRO - API Routes Package
V11.5 CORTEX: Extended with state, interactions, workflow, files endpoints
V11.6 KEYMAKER: Authentication endpoints

Routes:
- health: Health check endpoints (/health, /health/ready)
- stream: WebSocket streaming endpoint (/ws/stream)
- state: State snapshot for F5 recovery (/api/state/snapshot)
- interactions: Human-in-the-loop (/api/interactions/{id}/reply)
- workflow: Task execution control (/api/workflow/start)
- files: Secure file access (/api/files/content)
- auth: Authentication (V11.6) (/api/auth/login, /api/auth/me)
"""

from . import health, stream, state, interactions, workflow, files, auth

__all__ = ["health", "stream", "state", "interactions", "workflow", "files", "auth"]
