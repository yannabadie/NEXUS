import aiohttp
import asyncio
import logging
import json
from typing import Dict, Any

import os

logger = logging.getLogger("nexus.telemetry")

class TelemetryClient:
    """
    Fire-and-forget telemetry client to push events to the Dashboard.
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(TelemetryClient, cls).__new__(cls)
            cls._instance.dashboard_url = os.getenv("NEXUS_DASHBOARD_URL", "http://localhost:8000/api/telemetry")
            cls._instance.enabled = True
        return cls._instance

    async def emit(self, event_type: str, data: Dict[str, Any]):
        """
        Emit an event to the dashboard.
        """
        if not self.enabled:
            return

        payload = {
            "type": event_type,
            "data": data
        }

        try:
            async with aiohttp.ClientSession() as session:
                try:
                    await session.post(self.dashboard_url, json=payload, timeout=0.1)
                except asyncio.TimeoutError:
                    pass # Fire and forget, don't block
                except Exception as e:
                    # Don't spam logs if dashboard is down
                    pass
        except Exception:
            pass

    def emit_sync(self, event_type: str, data: Dict[str, Any]):
        """
        Sync wrapper for emit (fire-and-forget via background task if possible, 
        or just skip if no loop - but here we usually have a loop).
        For simplicity in sync contexts, we might skip or use a thread.
        """
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(self.emit(event_type, data))
        except RuntimeError:
            pass

# Global instance
telemetry = TelemetryClient()
