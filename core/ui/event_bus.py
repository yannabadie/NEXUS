"""
Event Bus for NEXUS V9.1 Reality Injection.

This module provides a global singleton EventBus to broadcast real-time events
from the Core (Orchestrator, Swarm, Architect) to the UI (Dashboard Server).

Since Core and Dashboard run in separate processes, this EventBus acts as a 
BRIDGE, sending events via HTTP POST to the Dashboard's /api/telemetry endpoint.

Usage:
    from core.ui.event_bus import EventBus

    # Publish (Fire and Forget)
    await EventBus.publish("AGENT_THINK", {"agent": "Gemini", "thought": "..."})
"""

import asyncio
import logging
import json
import aiohttp
from datetime import datetime
from typing import Dict, Any

logger = logging.getLogger("nexus.event_bus")

import os

DASHBOARD_URL = os.getenv("NEXUS_DASHBOARD_URL", "http://localhost:8000/api/telemetry")

class EventBus:
    """
    Async Event Bus Bridge.
    Sends events to the Dashboard Server via HTTP.
    """
    _session = None

    @classmethod
    async def get_session(cls):
        if cls._session is None or cls._session.closed:
            cls._session = aiohttp.ClientSession()
        return cls._session

    @classmethod
    async def publish(cls, event_type: str, data: Dict[str, Any]):
        """
        Publish an event to the Dashboard via HTTP POST.
        
        Args:
            event_type: Type of event (e.g., "STATE_CHANGE", "LOG")
            data: Event payload
        """
        event = {
            "type": event_type,
            "timestamp": datetime.now().isoformat(),
            "data": data
        }
        
        try:
            session = await cls.get_session()
            # Fire and forget - don't wait for response to avoid blocking Core
            # But we must await the request creation
            async with session.post(DASHBOARD_URL, json=event) as resp:
                pass
        except Exception as e:
            # Silently fail if dashboard is down to not disrupt Core
            # logger.debug(f"Failed to push event to dashboard: {e}")
            pass

    @classmethod
    async def close(cls):
        if cls._session:
            await cls._session.close()
