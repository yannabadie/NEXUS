"""
NEXUS V7.8 - Orchestration Package (Phase 14c)

This package contains the refactored orchestration components:
- OrchestratorV7: Main orchestrator (re-exported from parent for compatibility)
- ContextBuilder: Context construction for agents
- MutationDetector: Format detection for evolution
- AgentInvoker: Agent invocation handling
- SwarmBridge: Swarm engine integration
- FSMHandlers: State machine handlers

Phase 14c Migration Strategy:
1. Extracted modules are used via COMPOSITION by OrchestratorV7
2. Original orchestration_v7.py remains as entry point
3. New modules can be used directly for testing/extension

Usage:
    # Standard usage (unchanged):
    from core.orchestration_v7 import OrchestratorV7

    # Direct module access:
    from core.orchestration.context_builder import ContextBuilder
    from core.orchestration.detectors import MutationDetector
    from core.orchestration.agent_invoker import AgentInvoker
    from core.orchestration.swarm_bridge import SwarmBridge
    from core.orchestration.fsm_handlers import FSMHandlers
"""

# Re-export OrchestratorV7 for backwards compatibility
# Note: OrchestratorV7 remains in core/orchestration_v7.py for now
# It uses the extracted modules via composition

from core.orchestration.context_builder import ContextBuilder
from core.orchestration.detectors import MutationDetector, ResponseDetector, get_mutation_detector
from core.orchestration.agent_invoker import AgentInvoker
from core.orchestration.swarm_bridge import SwarmBridge
from core.orchestration.fsm_handlers import FSMHandlers

__all__ = [
    # Extracted modules (new in V7.8)
    'ContextBuilder',
    'MutationDetector',
    'ResponseDetector',
    'get_mutation_detector',
    'AgentInvoker',
    'SwarmBridge',
    'FSMHandlers',
]
