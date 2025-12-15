"""
NEXUS V10 CEREBRO: SYNAPSE - TelemetryBridge

Singleton facade for emitting telemetry events to Redis.
Uses contextvars for async-safe correlation ID tracking.

Features:
- Correlation IDs for tracing related events
- Sequence numbers for ordering within a trace
- Payload truncation (> 1KB) to prevent Redis congestion
- Fire-and-forget: never blocks main execution
- emit() for async code, emit_sync() for sync code

Usage:
    from core.events.telemetry_bridge import get_telemetry_bridge

    # In async code
    bridge = get_telemetry_bridge()
    trace_id = bridge.start_trace()
    await bridge.emit(CerebroEventType.HIVE_STATE_CHANGE, {"state": "ANALYZING"})
    bridge.end_trace()

    # In sync code (e.g., callbacks)
    bridge.emit_sync(CerebroEventType.HIVE_STATE_CHANGE, {"state": "EXECUTING"})

Author: Claude (NEXUS V10 CEREBRO SYNAPSE)
Date: 2025-12-15
"""

import asyncio
import json
import logging
import secrets
import threading
from contextvars import ContextVar
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger("nexus.telemetry.bridge")

# =============================================================================
# Async-safe Correlation Context (NOT dict - required for async)
# =============================================================================

_correlation_id: ContextVar[Optional[str]] = ContextVar("correlation_id", default=None)
_sequence_counter: ContextVar[int] = ContextVar("sequence_counter", default=0)

# =============================================================================
# Constants
# =============================================================================

MAX_PAYLOAD_SIZE = 1024  # 1KB limit for payload
EMIT_SYNC_TIMEOUT = 0.1  # 100ms max for sync emit
STATE_TTL = 86400  # 24 hours - V11.5 CORTEX state persistence (F5 recovery)


# =============================================================================
# TelemetryBridge Singleton
# =============================================================================

class TelemetryBridge:
    """
    Singleton facade for telemetry emission.

    Provides centralized telemetry publishing with:
    - Correlation ID tracing (via contextvars)
    - Sequence numbering within traces
    - Payload truncation for large messages
    - Both async and sync emission methods
    """

    _instance: Optional["TelemetryBridge"] = None
    _lock = threading.RLock()

    def __new__(cls) -> "TelemetryBridge":
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        logger.debug("TelemetryBridge singleton initialized")

    # =========================================================================
    # Trace Management
    # =========================================================================

    def start_trace(self, trace_id: Optional[str] = None) -> str:
        """
        Start a new correlation trace.

        Args:
            trace_id: Optional custom trace ID. If None, generates 12-char hex.

        Returns:
            The trace ID (generated or provided)
        """
        tid = trace_id or secrets.token_hex(6)
        _correlation_id.set(tid)
        _sequence_counter.set(0)
        logger.debug(f"Started trace: {tid}")
        return tid

    def end_trace(self) -> None:
        """End the current correlation trace."""
        tid = _correlation_id.get()
        _correlation_id.set(None)
        _sequence_counter.set(0)
        if tid:
            logger.debug(f"Ended trace: {tid}")

    def get_correlation_id(self) -> Optional[str]:
        """Get current correlation ID, or None if no trace active."""
        return _correlation_id.get()

    def _next_seq(self) -> int:
        """Increment and return sequence number."""
        seq = _sequence_counter.get() + 1
        _sequence_counter.set(seq)
        return seq

    # =========================================================================
    # Context Extraction
    # =========================================================================

    def _get_tenant(self) -> str:
        """Get current tenant ID from PRISM context, or 'anonymous'."""
        try:
            from core.context import get_current_session_or_none
            ctx = get_current_session_or_none()
            return ctx.tenant_id if ctx else "anonymous"
        except ImportError:
            return "anonymous"

    def _get_workspace(self) -> str:
        """Get current workspace ID from PRISM context, or 'default'."""
        try:
            from core.context import get_current_session_or_none
            ctx = get_current_session_or_none()
            return ctx.workspace_id if ctx else "default"
        except ImportError:
            return "default"

    # =========================================================================
    # Payload Truncation
    # =========================================================================

    def _truncate_payload(self, payload: Dict[str, Any]) -> Tuple[Dict[str, Any], bool]:
        """
        Truncate payload if it exceeds MAX_PAYLOAD_SIZE.

        Args:
            payload: The payload dictionary

        Returns:
            Tuple of (possibly truncated payload, was_truncated flag)
        """
        try:
            json_str = json.dumps(payload, default=str)
        except (TypeError, ValueError):
            # If serialization fails, return simple error payload
            return {"error": "payload_serialization_failed"}, True

        if len(json_str) <= MAX_PAYLOAD_SIZE:
            return payload, False

        # Try to truncate 'content' field if it exists
        payload_copy = payload.copy()
        if "content" in payload_copy and isinstance(payload_copy["content"], str):
            excess = len(json_str) - MAX_PAYLOAD_SIZE + 50  # 50 bytes margin
            if excess > 0 and len(payload_copy["content"]) > excess:
                payload_copy["content"] = payload_copy["content"][:-excess] + "..."

        return payload_copy, True

    # =========================================================================
    # V11.5 CORTEX - State Persistence for F5 Recovery
    # =========================================================================

    async def _persist_state(
        self,
        tenant_id: str,
        workspace_id: str,
        event_type: "CerebroEventType",
        payload: Dict[str, Any]
    ) -> None:
        """
        Persist stateful events to Redis for snapshot recovery (F5 recovery).

        V11.5 CORTEX: Enables UI to recover state after browser refresh.
        Persists phase state, graph nodes, and recent logs.

        Args:
            tenant_id: Tenant identifier
            workspace_id: Workspace identifier
            event_type: Event type to determine persistence behavior
            payload: Event payload data
        """
        try:
            from core.events.redis_bus import get_redis_bus
            from core.events.types import CerebroEventType

            bus = get_redis_bus()
            if not bus.is_connected():
                return

            redis = bus._redis
            if not redis:
                return

            base_key = f"nexus:{tenant_id}:{workspace_id}:state"

            # Phase state (HIVE_PHASE_START, HIVE_STATE_CHANGE)
            if event_type in (CerebroEventType.HIVE_PHASE_START,
                              CerebroEventType.HIVE_STATE_CHANGE):
                await redis.set(
                    f"{base_key}:phase",
                    json.dumps(payload, default=str),
                    ex=STATE_TTL
                )

            # Graph nodes (spawn/update)
            elif event_type == CerebroEventType.GRAPH_NODE_SPAWN:
                node_id = payload.get("node_id", "unknown")
                await redis.hset(f"{base_key}:nodes", node_id, json.dumps(payload, default=str))
                await redis.expire(f"{base_key}:nodes", STATE_TTL)

            elif event_type == CerebroEventType.GRAPH_NODE_UPDATE:
                node_id = payload.get("node_id", "unknown")
                await redis.hset(f"{base_key}:nodes", node_id, json.dumps(payload, default=str))
                # Refresh TTL on update
                await redis.expire(f"{base_key}:nodes", STATE_TTL)

            # Logs (capped list - max 100 entries)
            elif event_type == CerebroEventType.LOG:
                await redis.lpush(f"{base_key}:logs", json.dumps(payload, default=str))
                await redis.ltrim(f"{base_key}:logs", 0, 99)  # Keep only 100 most recent
                await redis.expire(f"{base_key}:logs", STATE_TTL)

        except Exception as e:
            # Fire-and-forget: never block, log at debug level
            logger.debug(f"State persistence failed (non-blocking): {e}")

    # =========================================================================
    # Emission Methods
    # =========================================================================

    async def emit(
        self,
        event_type: "CerebroEventType",
        payload: Dict[str, Any],
        tenant_id: Optional[str] = None,
        workspace_id: Optional[str] = None
    ) -> bool:
        """
        Emit telemetry event (async). Fire-and-forget.

        Args:
            event_type: CerebroEventType enum value
            payload: Event payload dict
            tenant_id: Optional tenant override
            workspace_id: Optional workspace override

        Returns:
            True if published successfully, False otherwise
        """
        try:
            # Lazy import to avoid circular dependencies
            from core.events.redis_bus import get_redis_bus
            from core.events.types import CerebroEvent

            # Truncate if needed
            payload_final, truncated = self._truncate_payload(payload)
            if truncated:
                payload_final["content_truncated"] = True

            # Get correlation context
            corr_id = _correlation_id.get()
            seq_num = self._next_seq() if corr_id else None

            # Build event
            event = CerebroEvent(
                event_type=event_type,
                tenant_id=tenant_id or self._get_tenant(),
                workspace_id=workspace_id or self._get_workspace(),
                payload=payload_final,
                correlation_id=corr_id,
                sequence_number=seq_num,
            )

            # Publish (fire-and-forget)
            bus = get_redis_bus()
            result = await bus.publish(event)

            # V11.5 CORTEX: Persist stateful events for F5 recovery
            await self._persist_state(
                tenant_id=event.tenant_id,
                workspace_id=event.workspace_id,
                event_type=event_type,
                payload=payload_final
            )

            return result

        except Exception as e:
            logger.debug(f"Telemetry emit failed (non-blocking): {e}")
            return False

    def emit_sync(
        self,
        event_type: "CerebroEventType",
        payload: Dict[str, Any],
        tenant_id: Optional[str] = None,
        workspace_id: Optional[str] = None
    ) -> bool:
        """
        Emit telemetry event from sync code. Thread-safe.

        Uses run_coroutine_threadsafe if event loop is running,
        otherwise falls back to asyncio.run().

        Args:
            event_type: CerebroEventType enum value
            payload: Event payload dict
            tenant_id: Optional tenant override
            workspace_id: Optional workspace override

        Returns:
            True if published successfully, False otherwise
        """
        try:
            # Try to get running loop
            try:
                loop = asyncio.get_running_loop()
                # Schedule in running loop
                future = asyncio.run_coroutine_threadsafe(
                    self.emit(event_type, payload, tenant_id, workspace_id),
                    loop
                )
                return future.result(timeout=EMIT_SYNC_TIMEOUT)
            except RuntimeError:
                # No running loop - create new one (for truly sync contexts)
                return asyncio.run(
                    self.emit(event_type, payload, tenant_id, workspace_id)
                )
        except Exception as e:
            logger.debug(f"Telemetry emit_sync failed (non-blocking): {e}")
            return False


# =============================================================================
# Module-level Accessors
# =============================================================================

def get_telemetry_bridge() -> TelemetryBridge:
    """Get the TelemetryBridge singleton instance."""
    return TelemetryBridge()


def reset_telemetry_bridge() -> None:
    """Reset the singleton and contextvars (for testing only)."""
    with TelemetryBridge._lock:
        TelemetryBridge._instance = None
    # Also reset contextvars
    _correlation_id.set(None)
    _sequence_counter.set(0)


# Type hint import (deferred to avoid circular import at module load)
if False:  # TYPE_CHECKING equivalent without import
    from core.events.types import CerebroEventType
