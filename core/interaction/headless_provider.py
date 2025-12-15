"""
HeadlessProvider - Non-blocking Interaction Provider for Servers.

NEXUS V9.8 DETOX - Headless Refactoring
NEXUS V10 CEREBRO - Redis Event Publishing

This provider never blocks:
- Always returns defaults immediately
- Logs all prompts for audit trail
- Publishes events to Redis for external UI observation (V10)
- Raises InteractionRequiredError for critical questions without defaults

Use cases:
- Web API server
- Background daemon
- CI/CD pipelines
- Automated testing
- External UI observation via CEREBRO API (V10)

Author: Claude (NEXUS DETOX)
Date: 2025-12-13
V10: 2025-12-15 (CEREBRO integration)
"""

import logging
from typing import Optional, List, Any, Dict

from .base import (
    InteractionProvider,
    InteractionLevel,
    InteractionRequiredError,
    Choice
)


logger = logging.getLogger("nexus.interaction.headless")


class HeadlessProvider(InteractionProvider):
    """
    Non-blocking provider for server/daemon mode.

    This provider:
    - Never calls input() or any blocking I/O
    - Always returns default values immediately
    - Logs all prompts and responses for audit
    - Publishes events to Redis for external observation (V10 CEREBRO)
    - Can operate in strict mode (raise on missing defaults)

    Usage:
        # Lenient mode (default) - returns empty/False for missing defaults
        provider = HeadlessProvider(strict=False)

        # Strict mode - raises InteractionRequiredError for missing defaults
        provider = HeadlessProvider(strict=True)

        # With custom logger
        provider = HeadlessProvider(logger_name="myapp.interaction")

        # Disable Redis publishing (V10)
        provider = HeadlessProvider(publish_events=False)
    """

    def __init__(
        self,
        strict: bool = False,
        logger_name: Optional[str] = None,
        publish_events: bool = True
    ):
        """
        Initialize headless provider.

        Args:
            strict: If True, raise error when required input has no default
            logger_name: Custom logger name (default: nexus.interaction.headless)
            publish_events: If True, publish events to Redis (V10 CEREBRO)
        """
        self.strict = strict
        self._logger = logging.getLogger(logger_name) if logger_name else logger
        self._publish_events = publish_events

    async def _publish_event(
        self,
        event_type_name: str,
        payload: Dict[str, Any]
    ) -> None:
        """
        Publish interaction event to Redis (fire-and-forget).

        V10 CEREBRO: Enables external UI observation of NEXUS interactions.
        Never blocks, silently ignores errors.

        Args:
            event_type_name: Event type value (e.g., "interaction.ask")
            payload: Event payload data
        """
        if not self._publish_events:
            return

        try:
            # Lazy import to avoid circular dependencies
            from core.events.redis_bus import get_redis_bus
            from core.events.types import CerebroEvent, CerebroEventType

            # Get current tenant context
            try:
                from core.context import get_current_session_or_none
                ctx = get_current_session_or_none()
                if ctx:
                    tenant_id = ctx.tenant_id
                    workspace_id = ctx.workspace_id
                else:
                    tenant_id = "anonymous"
                    workspace_id = "default"
            except ImportError:
                tenant_id = "anonymous"
                workspace_id = "default"

            # Create and publish event
            event = CerebroEvent(
                event_type=CerebroEventType(event_type_name),
                tenant_id=tenant_id,
                workspace_id=workspace_id,
                payload=payload
            )

            bus = get_redis_bus()
            await bus.publish(event)

        except Exception:
            # Fire-and-forget: never block, never raise
            pass

    async def ask(
        self,
        prompt: str,
        default: Optional[str] = None,
        timeout: Optional[float] = None,
        required: bool = False
    ) -> str:
        """Return default immediately, never block."""
        self._logger.info(f"[HEADLESS] Prompt: {prompt}")

        # V10 CEREBRO: Publish event
        await self._publish_event("interaction.ask", {
            "prompt": prompt,
            "default": default,
            "required": required,
        })

        if default is not None:
            self._logger.info(f"[HEADLESS] Using default: {default}")
            return default

        if required or self.strict:
            self._logger.warning(f"[HEADLESS] Required input has no default: {prompt}")
            raise InteractionRequiredError(
                prompt=prompt,
                context="Headless mode cannot provide user input"
            )

        self._logger.debug(f"[HEADLESS] No default, returning empty string")
        return ""

    async def confirm(
        self,
        prompt: str,
        default: bool = False,
        timeout: Optional[float] = None
    ) -> bool:
        """Return default confirmation immediately."""
        self._logger.info(f"[HEADLESS] Confirm: {prompt} -> {default}")

        # V10 CEREBRO: Publish event
        await self._publish_event("interaction.confirm", {
            "prompt": prompt,
            "default": default,
            "response": default,
        })

        return default

    async def choose(
        self,
        prompt: str,
        choices: List[Choice],
        default: Optional[str] = None,
        timeout: Optional[float] = None
    ) -> str:
        """Return default choice immediately."""
        self._logger.info(f"[HEADLESS] Choice: {prompt}")
        self._logger.debug(f"[HEADLESS] Options: {[c.key for c in choices]}")

        choice_keys = [c.key for c in choices]

        # V10 CEREBRO: Publish event
        await self._publish_event("interaction.choose", {
            "prompt": prompt,
            "choices": choice_keys,
            "default": default,
        })

        if default is not None:
            if any(c.key == default for c in choices):
                self._logger.info(f"[HEADLESS] Using default choice: {default}")
                return default

        # No valid default - use first choice or raise
        if choices:
            first_key = choices[0].key
            if self.strict and default is None:
                raise InteractionRequiredError(
                    prompt=prompt,
                    context=f"Choice required, options: {choice_keys}"
                )
            self._logger.info(f"[HEADLESS] Using first choice: {first_key}")
            return first_key

        raise InteractionRequiredError(
            prompt=prompt,
            context="No choices available"
        )

    async def announce(
        self,
        message: str,
        level: InteractionLevel = InteractionLevel.INFO
    ) -> None:
        """Log announcement instead of printing."""
        log_method = {
            InteractionLevel.DEBUG: self._logger.debug,
            InteractionLevel.INFO: self._logger.info,
            InteractionLevel.WARNING: self._logger.warning,
            InteractionLevel.ERROR: self._logger.error,
            InteractionLevel.CRITICAL: self._logger.critical
        }.get(level, self._logger.info)

        log_method(f"[ANNOUNCE] {message}")

        # V10 CEREBRO: Publish event
        await self._publish_event("interaction.announce", {
            "message": message,
            "level": level.value if hasattr(level, 'value') else str(level),
        })

    async def progress(
        self,
        message: str,
        current: int,
        total: int
    ) -> None:
        """Log progress at intervals (every 10% or completion)."""
        if total <= 0:
            return

        pct = current / total * 100

        # Log at 0%, every 25%, and 100%
        should_log = (
            current == 0 or
            current >= total or
            (current % max(1, total // 4)) == 0
        )

        if should_log:
            self._logger.debug(f"[PROGRESS] {pct:.0f}% ({current}/{total}) - {message}")

            # V10 CEREBRO: Publish event (only at log intervals to reduce noise)
            await self._publish_event("interaction.progress", {
                "message": message,
                "current": current,
                "total": total,
                "percent": round(pct, 1),
            })

    @property
    def is_interactive(self) -> bool:
        """Headless provider is not interactive."""
        return False
