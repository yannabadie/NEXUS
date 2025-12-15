"""
NEXUS V10 CEREBRO - Events Package

Redis-based event bus for external UI observation.
Coexists with internal EventBus (core/async_primitives/event_bus.py).

Usage:
    from core.events import CerebroEvent, CerebroEventType, get_redis_bus

    # Publish event
    event = CerebroEvent(
        event_type=CerebroEventType.INTERACTION_ASK,
        tenant_id="tenant_123",
        workspace_id="default",
        payload={"prompt": "Continue?"}
    )
    await get_redis_bus().publish(event)
"""

from .types import CerebroEvent, CerebroEventType
from .redis_bus import RedisEventBus, get_redis_bus, reset_redis_bus

__all__ = [
    "CerebroEvent",
    "CerebroEventType",
    "RedisEventBus",
    "get_redis_bus",
    "reset_redis_bus",
]
