"""
Interaction Module - User Interaction Abstraction Layer.

NEXUS V9.8 DETOX - Headless Refactoring

This module provides a clean abstraction for user interaction,
enabling NEXUS to run in both interactive CLI and headless server modes.

Configuration:
    Set NEXUS_INTERACTION_MODE environment variable:
    - "cli" (default): Interactive terminal mode
    - "headless": Non-blocking, returns defaults
    - "strict": Headless but raises on missing defaults

Usage:
    from core.interaction import get_interaction_provider

    async def my_function():
        provider = get_interaction_provider()

        # Ask for input
        name = await provider.ask("Enter name", default="Anonymous")

        # Confirm action
        if await provider.confirm("Proceed?", default=True):
            await provider.announce("Processing...")

        # Multiple choice
        choice = await provider.choose(
            "Select option",
            choices=[
                Choice("a", "Option A"),
                Choice("b", "Option B"),
            ],
            default="a"
        )

Author: Claude (NEXUS DETOX)
Date: 2025-12-13
"""

import os
import threading
from typing import Optional

from .base import (
    InteractionProvider,
    InteractionLevel,
    InteractionRequiredError,
    Choice
)
from .cli_provider import CLIProvider
from .headless_provider import HeadlessProvider


# =============================================================================
# V10 PRISM: Multi-Tenant Interaction Provider Access
# =============================================================================
_provider: Optional[InteractionProvider] = None
_provider_lock = threading.Lock()


def get_interaction_provider() -> InteractionProvider:
    """
    Get the interaction provider for the current tenant context.

    V10 PRISM: Returns tenant-scoped provider via ServiceFactory.
    Falls back to global singleton if no context is active.

    The provider type is determined by NEXUS_INTERACTION_MODE env var:
    - "cli": Interactive CLIProvider (default)
    - "headless": Non-blocking HeadlessProvider
    - "strict": HeadlessProvider with strict=True

    Returns:
        InteractionProvider instance scoped to current tenant

    Thread-safe with double-checked locking.
    """
    # V10: Try ServiceFactory first (tenant-scoped)
    try:
        from .base import InteractionProvider as _IP  # avoid shadowing
        from ..context import has_active_session
        if has_active_session():
            from ..factory import ServiceFactory
            return ServiceFactory.get_interaction_provider()
    except ImportError:
        pass  # context module not available, use legacy

    # Legacy fallback: global singleton
    global _provider

    if _provider is None:
        with _provider_lock:
            if _provider is None:
                mode = os.environ.get("NEXUS_INTERACTION_MODE", "cli").lower()

                if mode == "headless":
                    _provider = HeadlessProvider(strict=False)
                elif mode == "strict":
                    _provider = HeadlessProvider(strict=True)
                else:
                    _provider = CLIProvider()

    return _provider


def set_interaction_provider(provider: InteractionProvider) -> None:
    """
    Override the global interaction provider.

    Useful for:
    - Testing with mock providers
    - Runtime mode switching
    - Custom provider implementations

    Args:
        provider: The provider instance to use globally
    """
    global _provider
    with _provider_lock:
        _provider = provider


def reset_interaction_provider() -> None:
    """
    Reset the global provider to None.

    The next call to get_interaction_provider() will create
    a new instance based on current environment settings.

    Note: In V10, also clears ServiceFactory cache for current tenant.
    """
    global _provider
    with _provider_lock:
        _provider = None

    # V10: Also clear factory cache
    try:
        from ..context import get_current_session_or_none
        from ..factory import ServiceFactory
        ctx = get_current_session_or_none()
        if ctx:
            ServiceFactory.clear_tenant_cache(ctx.tenant_id)
    except ImportError:
        pass


__all__ = [
    # Base classes
    "InteractionProvider",
    "InteractionLevel",
    "InteractionRequiredError",
    "Choice",

    # Implementations
    "CLIProvider",
    "HeadlessProvider",

    # Factory functions
    "get_interaction_provider",
    "set_interaction_provider",
    "reset_interaction_provider",
]
