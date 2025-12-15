"""
NEXUS V10 CEREBRO - Redis Event Bus

Async Redis pub/sub bus for external UI observation.
Fire-and-forget publishing with graceful degradation.

Architecture:
- Singleton via __new__ + RLock (thread-safe)
- Connection pool with Redis.from_url()
- Graceful degradation: if Redis unavailable, continue without blocking

Channel Format: nexus:{tenant_id}:{workspace_id}:{event_type}

Usage:
    bus = get_redis_bus()
    await bus.connect()

    # Publish (fire-and-forget)
    event = CerebroEvent(...)
    await bus.publish(event)

    # Subscribe (async iterator)
    async for event in bus.subscribe("tenant_1", "ws_1"):
        print(event)

    await bus.disconnect()
"""

import asyncio
import logging
from threading import RLock
from typing import Any, AsyncIterator, Dict, List, Optional, Set

from .types import CerebroEvent, CerebroEventType

logger = logging.getLogger(__name__)


class RedisEventBus:
    """
    Async Redis pub/sub event bus for CEREBRO.

    Thread-safe singleton with graceful degradation.
    """

    _instance: Optional["RedisEventBus"] = None
    _lock = RLock()

    def __new__(cls) -> "RedisEventBus":
        """Singleton pattern with double-checked locking."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    instance = super().__new__(cls)
                    instance._initialized = False
                    cls._instance = instance
        return cls._instance

    def __init__(self):
        """Initialize bus (only runs once due to singleton)."""
        if self._initialized:
            return

        self._redis: Optional[Any] = None  # redis.asyncio.Redis
        self._pubsub: Optional[Any] = None  # redis.asyncio.PubSub
        self._url: str = "redis://localhost:6379"
        self._connected: bool = False
        self._subscriptions: Set[str] = set()
        self._initialized = True

    async def connect(self, url: str = "redis://localhost:6379") -> bool:
        """
        Connect to Redis server.

        Args:
            url: Redis connection URL

        Returns:
            True if connected successfully, False otherwise
        """
        if self._connected:
            return True

        self._url = url

        try:
            import redis.asyncio as aioredis

            self._redis = aioredis.from_url(
                url,
                encoding="utf-8",
                decode_responses=True,
                health_check_interval=30,
                socket_connect_timeout=5.0,
                socket_timeout=5.0,
            )

            # Test connection
            await self._redis.ping()
            self._connected = True
            logger.info(f"CEREBRO: Connected to Redis at {url}")
            return True

        except ImportError:
            logger.warning("CEREBRO: redis package not installed, running in degraded mode")
            return False
        except Exception as e:
            logger.warning(f"CEREBRO: Failed to connect to Redis: {e}")
            self._connected = False
            return False

    async def disconnect(self) -> None:
        """Disconnect from Redis server."""
        if self._pubsub:
            try:
                await self._pubsub.close()
            except Exception:
                pass
            self._pubsub = None

        if self._redis:
            try:
                await self._redis.aclose()
            except Exception:
                pass
            self._redis = None

        self._connected = False
        self._subscriptions.clear()
        logger.info("CEREBRO: Disconnected from Redis")

    async def publish(self, event: CerebroEvent) -> bool:
        """
        Publish event to Redis (fire-and-forget).

        Args:
            event: CerebroEvent to publish

        Returns:
            True if published successfully, False otherwise (graceful degradation)
        """
        if not self._connected or self._redis is None:
            logger.debug(f"CEREBRO: Redis unavailable, dropping event: {event.event_type.value}")
            return False

        try:
            channel = event.channel_name()
            await self._redis.publish(channel, event.to_json())
            logger.debug(f"CEREBRO: Published {event.event_type.value} to {channel}")
            return True

        except Exception as e:
            logger.warning(f"CEREBRO: Failed to publish event: {e}")
            return False

    async def subscribe(
        self,
        tenant_id: str,
        workspace_id: str,
        event_types: Optional[List[CerebroEventType]] = None
    ) -> AsyncIterator[CerebroEvent]:
        """
        Subscribe to events for a tenant/workspace.

        Args:
            tenant_id: Tenant identifier
            workspace_id: Workspace identifier
            event_types: List of event types to subscribe to (None = all)

        Yields:
            CerebroEvent instances as they arrive

        Example:
            async for event in bus.subscribe("t1", "ws1"):
                print(event.payload)
        """
        if not self._connected or self._redis is None:
            logger.warning("CEREBRO: Cannot subscribe - Redis not connected")
            return

        try:
            import redis.asyncio as aioredis

            pubsub = self._redis.pubsub()

            # Build patterns
            if event_types:
                patterns = [
                    CerebroEvent.wildcard_channel(tenant_id, workspace_id, et)
                    for et in event_types
                ]
            else:
                patterns = [CerebroEvent.wildcard_channel(tenant_id, workspace_id)]

            # Subscribe to patterns
            for pattern in patterns:
                await pubsub.psubscribe(pattern)
                self._subscriptions.add(pattern)
                logger.debug(f"CEREBRO: Subscribed to pattern: {pattern}")

            # Yield events
            async for message in pubsub.listen():
                if message["type"] == "pmessage":
                    try:
                        event = CerebroEvent.from_json(message["data"])
                        yield event
                    except Exception as e:
                        logger.warning(f"CEREBRO: Failed to parse event: {e}")

        except asyncio.CancelledError:
            logger.debug("CEREBRO: Subscription cancelled")
            raise
        except Exception as e:
            logger.error(f"CEREBRO: Subscription error: {e}")
        finally:
            if pubsub:
                try:
                    await pubsub.close()
                except Exception:
                    pass

    def is_connected(self) -> bool:
        """Check if connected to Redis."""
        return self._connected

    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on Redis connection.

        Returns:
            Health status dict with connected, latency_ms, etc.
        """
        result = {
            "connected": self._connected,
            "url": self._url,
            "subscriptions": len(self._subscriptions),
        }

        if self._connected and self._redis:
            try:
                import time
                start = time.perf_counter()
                await self._redis.ping()
                latency = (time.perf_counter() - start) * 1000
                result["latency_ms"] = round(latency, 2)
                result["status"] = "healthy"
            except Exception as e:
                result["status"] = "unhealthy"
                result["error"] = str(e)
        else:
            result["status"] = "disconnected"

        return result

    async def get_info(self) -> Dict[str, Any]:
        """
        Get Redis server info.

        Returns:
            Redis INFO dict or empty dict if not connected
        """
        if not self._connected or self._redis is None:
            return {}

        try:
            info = await self._redis.info()
            return {
                "redis_version": info.get("redis_version"),
                "connected_clients": info.get("connected_clients"),
                "used_memory_human": info.get("used_memory_human"),
                "pubsub_channels": info.get("pubsub_channels"),
                "pubsub_patterns": info.get("pubsub_patterns"),
            }
        except Exception:
            return {}


# =============================================================================
# Module-Level Singleton Access
# =============================================================================

_redis_bus: Optional[RedisEventBus] = None


def get_redis_bus() -> RedisEventBus:
    """
    Get the global RedisEventBus singleton.

    Returns:
        RedisEventBus instance (may not be connected yet)
    """
    global _redis_bus
    if _redis_bus is None:
        _redis_bus = RedisEventBus()
    return _redis_bus


def reset_redis_bus() -> None:
    """
    Reset the global RedisEventBus singleton (for testing).

    Note: Does NOT disconnect - call disconnect() first if needed.
    """
    global _redis_bus
    RedisEventBus._instance = None
    _redis_bus = None


# =============================================================================
# Convenience Functions
# =============================================================================

async def publish_event(event: CerebroEvent) -> bool:
    """
    Quick publish function (uses global bus).

    Args:
        event: CerebroEvent to publish

    Returns:
        True if published, False otherwise
    """
    bus = get_redis_bus()
    return await bus.publish(event)


async def publish_interaction(
    event_type: CerebroEventType,
    tenant_id: str,
    workspace_id: str,
    **payload
) -> bool:
    """
    Quick publish for interaction events.

    Args:
        event_type: Must be INTERACTION_* type
        tenant_id: Tenant identifier
        workspace_id: Workspace identifier
        **payload: Event payload fields

    Returns:
        True if published, False otherwise
    """
    event = CerebroEvent(
        event_type=event_type,
        tenant_id=tenant_id,
        workspace_id=workspace_id,
        payload=payload,
    )
    return await publish_event(event)
