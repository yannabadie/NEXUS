"""
NEXUS V10.2 - FSM Handlers (Modular Entry Point)

This module re-exports FSMHandlers from the original fsm_handlers.py
while providing a hook point for gradual migration to split handlers.

The monolithic file split is in progress. This wrapper ensures:
1. Backward compatibility with existing imports
2. Future flexibility to switch to mixin-based handlers

Usage:
    from core.orchestration.handlers import FSMHandlers
    # Works exactly as before
"""

# Re-export from original monolithic file
# Future: This will compose from individual handler mixins
from core.orchestration.fsm_handlers import FSMHandlers

__all__ = ["FSMHandlers"]
