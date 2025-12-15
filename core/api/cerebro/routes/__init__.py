"""
NEXUS V10 CEREBRO - API Routes Package
V11.5 CORTEX: Extended with state, interactions, workflow, files endpoints

Routes:
- health: Health check endpoints (/health, /health/ready)
- stream: WebSocket streaming endpoint (/ws/stream)
- state: State snapshot for F5 recovery (/api/state/snapshot)
- interactions: Human-in-the-loop (/api/interactions/{id}/reply)
- workflow: Task execution control (/api/workflow/start)
- files: Secure file access (/api/files/content)
"""

from . import health, stream, state, interactions, workflow, files

__all__ = ["health", "stream", "state", "interactions", "workflow", "files"]
