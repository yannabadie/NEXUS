"""
NEXUS V12.4 - FSM State Handlers

Modular state handlers for the FSM orchestrator.

Usage:
    from core.fsm.handlers import FSMHandlers
    handlers = FSMHandlers(orchestrator)
    result = handlers.handle_idle(user_input)
"""

from core.fsm.handlers.base import BaseHandler
from core.fsm.handlers.error import ErrorHandler
from core.fsm.handlers.brainstorming import BrainstormingHandler
from core.fsm.handlers.executing_tool import ExecutingToolHandler
from core.fsm.handlers.validating_cfl import ValidatingCFLHandler
from core.fsm.handlers.evolution import EvolutionHandler
from core.fsm.handlers.swarm import SwarmHandler
from core.fsm.handlers.idle_waiting import IdleWaitingHandler

# Import legacy handlers temporarily for simple execution helpers
from core.orchestration.fsm_handlers import FSMHandlers as LegacyFSMHandlers

from typing import TYPE_CHECKING, Dict, Optional

if TYPE_CHECKING:
    from core.orchestration_v7 import OrchestratorV7


class FSMHandlers:
    """
    Facade for all FSM state handlers.

    Delegates to specialized handler classes for each state.
    """

    def __init__(self, orchestrator: 'OrchestratorV7'):
        """
        Initialize all handler modules.

        Args:
            orchestrator: Parent OrchestratorV7 instance
        """
        self._orch = orchestrator

        # Initialize modular handlers
        self.error_handler = ErrorHandler(orchestrator)
        self.brainstorming_handler = BrainstormingHandler(orchestrator)
        self.executing_tool_handler = ExecutingToolHandler(orchestrator)
        self.validating_cfl_handler = ValidatingCFLHandler(orchestrator)
        self.evolution_handler = EvolutionHandler(orchestrator)
        self.swarm_handler = SwarmHandler(orchestrator)
        self.idle_waiting_handler = IdleWaitingHandler(orchestrator)

        # Temporary: Use legacy handler for simple execution helpers
        self._legacy_handler = LegacyFSMHandlers(orchestrator)

    # =========================================================================
    # Public Handler Methods (FSM State Dispatch Interface)
    # =========================================================================

    def handle_idle(self, user_input: Optional[str]) -> Dict:
        """Handle IDLE state."""
        return self.idle_waiting_handler.handle_idle(user_input)

    def handle_waiting_user(self, user_input: Optional[str]) -> Dict:
        """Handle WAITING_USER state."""
        return self.idle_waiting_handler.handle_waiting_user(user_input)

    def handle_brainstorming(self) -> Dict:
        """Handle BRAINSTORMING state."""
        return self.brainstorming_handler.handle_brainstorming()

    def handle_executing_tool(self) -> Dict:
        """Handle EXECUTING_TOOL state."""
        return self.executing_tool_handler.handle_executing_tool()

    def handle_validating_cfl(self) -> Dict:
        """Handle VALIDATING_CFL state."""
        return self.validating_cfl_handler.handle_validating_cfl()

    def handle_error(self) -> Dict:
        """Handle ERROR state."""
        return self.error_handler.handle_error()

    def handle_panic(self) -> Dict:
        """Handle PANIC state."""
        return self.error_handler.handle_panic()

    def handle_evolution_brainstorm(self, user_input: Optional[str] = None) -> Dict:
        """Handle EVOLUTION_BRAINSTORM state."""
        return self.evolution_handler.handle_evolution_brainstorm(user_input)

    def handle_swarm_analyzing(self) -> Dict:
        """Handle SWARM_ANALYZING state."""
        return self.swarm_handler.handle_swarm_analyzing()

    def handle_swarm_negotiating(self) -> Dict:
        """Handle SWARM_NEGOTIATING state."""
        return self.swarm_handler.handle_swarm_negotiating()

    def handle_swarm_executing(self) -> Dict:
        """Handle SWARM_EXECUTING state."""
        return self.swarm_handler.handle_swarm_executing()

    # V8.4.4: Async handlers - delegated to orchestrator for now
    @property
    def has_async_handlers(self) -> bool:
        """Check if async handlers are available."""
        return self._legacy_handler.has_async_handlers


__all__ = [
    'FSMHandlers',
    'BaseHandler',
    'ErrorHandler',
    'BrainstormingHandler',
    'ExecutingToolHandler',
    'ValidatingCFLHandler',
    'EvolutionHandler',
    'SwarmHandler',
]
