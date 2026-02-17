"""
NEXUS V13.0 MEMORIA UNIVERSALIS - API Routes Package
V11.5 CORTEX: Extended with state, interactions, workflow, files endpoints
V11.6 KEYMAKER: Authentication endpoints
V13.0 MEMORIA: Memory management endpoints
V12.4 P2.1: Causality Timeline (observability)

Routes:
- health: Health check endpoints (/health, /health/ready)
- stream: WebSocket streaming endpoint (/ws/stream)
- state: State snapshot for F5 recovery (/api/state/snapshot)
- interactions: Human-in-the-loop (/api/interactions/{id}/reply)
- workflow: Task execution control (/api/workflow/start)
- files: Secure file access (/api/files/content)
- auth: Authentication (V11.6) (/api/auth/login, /api/auth/me)
- memory: RAG memory management (V13.0) (/api/memory/*)
- timeline: Causality timeline (V12.4) (/api/timeline/{task_id})
"""

from . import health, stream, state, interactions, workflow, files, auth, memory, timeline

__all__ = ["health", "stream", "state", "interactions", "workflow", "files", "auth", "memory", "timeline"]
