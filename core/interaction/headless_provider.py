"""
HeadlessProvider - Non-blocking Interaction Provider for Servers.

NEXUS V9.8 DETOX - Headless Refactoring

This provider never blocks:
- Always returns defaults immediately
- Logs all prompts for audit trail
- Raises InteractionRequiredError for critical questions without defaults

Use cases:
- Web API server
- Background daemon
- CI/CD pipelines
- Automated testing

Author: Claude (NEXUS DETOX)
Date: 2025-12-13
"""

import logging
from typing import Optional, List

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
    - Can operate in strict mode (raise on missing defaults)

    Usage:
        # Lenient mode (default) - returns empty/False for missing defaults
        provider = HeadlessProvider(strict=False)

        # Strict mode - raises InteractionRequiredError for missing defaults
        provider = HeadlessProvider(strict=True)

        # With custom logger
        provider = HeadlessProvider(logger_name="myapp.interaction")
    """

    def __init__(
        self,
        strict: bool = False,
        logger_name: Optional[str] = None
    ):
        """
        Initialize headless provider.

        Args:
            strict: If True, raise error when required input has no default
            logger_name: Custom logger name (default: nexus.interaction.headless)
        """
        self.strict = strict
        self._logger = logging.getLogger(logger_name) if logger_name else logger

    async def ask(
        self,
        prompt: str,
        default: Optional[str] = None,
        timeout: Optional[float] = None,
        required: bool = False
    ) -> str:
        """Return default immediately, never block."""
        self._logger.info(f"[HEADLESS] Prompt: {prompt}")

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
                    context=f"Choice required, options: {[c.key for c in choices]}"
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

    @property
    def is_interactive(self) -> bool:
        """Headless provider is not interactive."""
        return False
