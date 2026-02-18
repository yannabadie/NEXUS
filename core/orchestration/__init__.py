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
# P5.1 Phase 1: GuardPipeline extraction
from core.orchestration.guard_pipeline import GuardPipeline, GuardValidationResult
# P5.1 Phase 2: TaskRouter extraction
from core.orchestration.task_router import TaskRouter, RouteDecision, RouteType

# V9.4 ISSUE-003: Sync bridge for HiveMind/Swarm state synchronization
from core.orchestration.sync_bridge import (
    OrchestratorSyncBridge,
    SyncEvent,
    SyncEventType,
    get_sync_bridge,
    reset_sync_bridge,
)

# V12.4: Dependency Injector
from core.orchestration.dependency_injector import (
    DependencyInjector,
    Capability,
    AgentRequirements,
    ValidationResult as DependencyValidationResult,
    Conflict,
    DependencyManifest,
    get_injector,
    reset_injector,
)

# V12.4: Call Graph Tracer
from core.orchestration.call_graph_tracer import (
    CallGraphTracer,
    CallRecord,
    EdgeMetrics,
    TracerStats,
    get_call_tracer,
    reset_call_tracer,
)

__all__ = [
    # Extracted modules (new in V7.8)
    'ContextBuilder',
    'MutationDetector',
    'ResponseDetector',
    'get_mutation_detector',
    'AgentInvoker',
    'SwarmBridge',
    'FSMHandlers',
    # P5.1 Phase 1: GuardPipeline
    'GuardPipeline',
    'GuardValidationResult',
    # P5.1 Phase 2: TaskRouter
    'TaskRouter',
    'RouteDecision',
    'RouteType',
    # V9.4: Sync bridge
    'OrchestratorSyncBridge',
    'SyncEvent',
    'SyncEventType',
    'get_sync_bridge',
    'reset_sync_bridge',
    # V12.4: Dependency Injector
    'DependencyInjector',
    'Capability',
    'AgentRequirements',
    'DependencyValidationResult',
    'Conflict',
    'DependencyManifest',
    'get_injector',
    'reset_injector',
    # V12.4: Call Graph Tracer
    'CallGraphTracer',
    'CallRecord',
    'EdgeMetrics',
    'TracerStats',
    'get_call_tracer',
    'reset_call_tracer',
]
