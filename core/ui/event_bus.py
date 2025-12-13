"""
Event Bus for NEXUS V9.1 Reality Injection.

This module provides a global singleton EventBus to broadcast real-time events
from the Core (Orchestrator, Swarm, Architect) to the UI (Dashboard Server).

Since Core and Dashboard run in separate processes, this EventBus acts as a 
BRIDGE, sending events via HTTP POST to the Dashboard's /api/telemetry endpoint.

Usage:
    from core.ui.event_bus import EventBus

    # Async context:
    await EventBus.publish("AGENT_THINK", {"agent": "Gemini", "thought": "..."})
    
    # Sync context (e.g., from drivers):
    EventBus.publish_sync("AGENT_RESPONSE", {"agent": "Gemini", "content": "..."})
"""

import asyncio
import logging
import json
import os
import threading
from datetime import datetime
from typing import Dict, Any

logger = logging.getLogger("nexus.event_bus")

DASHBOARD_URL = os.getenv("NEXUS_DASHBOARD_URL", "http://localhost:8000/api/telemetry")

class EventBus:
    """
    Async Event Bus Bridge.
    Sends events to the Dashboard Server via HTTP.
    """
    _session = None

    @classmethod
    async def get_session(cls):
        import aiohttp
        if cls._session is None or cls._session.closed:
            cls._session = aiohttp.ClientSession()
        return cls._session

    @classmethod
    async def publish(cls, event_type: str, data: Dict[str, Any]):
        """
        Publish an event to the Dashboard via HTTP POST (async).
        
        Args:
            event_type: Type of event (e.g., "STATE_CHANGE", "LOG")
            data: Event payload
        """
        import aiohttp
        event = {
            "type": event_type,
            "timestamp": datetime.now().isoformat(),
            "data": data
        }
        
        try:
            session = await cls.get_session()
            async with session.post(DASHBOARD_URL, json=event) as resp:
                pass
        except Exception as e:
            pass  # Silently fail if dashboard is down

    @classmethod
    def publish_sync(cls, event_type: str, data: Dict[str, Any]):
        """
        Publish an event to the Dashboard via HTTP POST (synchronous).
        
        Uses a background thread for fire-and-forget semantics.
        Safe to call from synchronous driver code.
        
        Args:
            event_type: Type of event (e.g., "AGENT_RESPONSE")
            data: Event payload
        """
        event = {
            "type": event_type,
            "timestamp": datetime.now().isoformat(),
            "data": data
        }
        
        def _send():
            try:
                import requests
                requests.post(DASHBOARD_URL, json=event, timeout=2)
            except Exception:
                pass  # Silently fail
        
        # Fire-and-forget in background thread
        thread = threading.Thread(target=_send, daemon=True)
        thread.start()

    @classmethod
    async def close(cls):
        if cls._session:
            await cls._session.close()

