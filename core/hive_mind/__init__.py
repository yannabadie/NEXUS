"""
NEXUS V8.0 - TRUE HIVE MIND Module

Transforms NEXUS from a sequential orchestrator into a true collaborative intelligence.

Architecture:
- 7 Phases: Analysis → Debate → Architecture → Execution → Diagnosis → Retry → Consolidation
- 4 User Breakpoints: After debate, before spawn, after diagnosis, consolidation
- Adaptive debate turns based on complexity and errors
- Knowledge consolidation post-task

Components:
- types.py: Core dataclasses and enums
- agent_registry.py: Anti-duplication with similarity search
- cost_estimator.py: Budget control before decisions
- context_manager.py: Sliding window to avoid token explosion
- strategy_blacklist.py: Anti-circular retry
- user_interaction.py: Breakpoint handling
- fsm_states.py: FSM states extension for V8.0

Usage:
    from core.hive_mind import TrueHiveMind

    hive = TrueHiveMind(workspace_path, config)
    result = await hive.process_task("Complex task here")
"""

from .types import (
    # Enums
    HiveMindState,
    UserBreakpoint,
    RetentionDecision,

    # Analysis
    IndependentAnalysis,
    AnalysisComparison,
    Disagreement,

    # Debate
    DebateArgument,
    DebateResult,

    # Architecture
    AgentSpec,
    AgentArchitecture,

    # Execution
    ExecutionIssue,
    MonitoredStepResult,

    # Diagnosis
    FailureDiagnosis,

    # Retry
    RetryDecision,

    # Consolidation
    KnowledgeConsolidation,
    AgentRetention,

    # Breakpoints
    BreakpointOption,
    BreakpointRequest,
    BreakpointResponse,
)

from .agent_registry import AgentRegistry
from .cost_estimator import CostEstimator
from .context_manager import HiveMindContextManager
from .strategy_blacklist import StrategyBlacklist
from .user_interaction import UserInteractionHandler
from .adaptive_debate import AdaptiveDebateConfig, DebateParams, TaskComplexity
from .orchestrator import TrueHiveMind, HiveMindResult
from .swarm_bridge import (
    SwarmBridge,
    SwarmDelegationResult,
    HivePhase,
    suggest_mode_for_subtask,
    create_bridge_for_phase,
)
from .saga_manager import (
    SagaManager,
    PhaseCheckpoint,
    SagaContext,
    PHASE_ORDER,
    PHASE_GUARDS,
)

# V12.4: Phase Coordinator
from .phase_coordinator import (
    PhaseCoordinator,
    PhaseState,
    PhaseTransition,
    TransitionResult,
    get_phase_coordinator,
    reset_phase_coordinator,
)

# V12.4: Consensus Tracker
from .consensus_tracker import (
    ConsensusTracker,
    TopicConsensus,
    ConsensusReport,
    get_consensus_tracker,
    reset_consensus_tracker,
)

# V12.4 COGNITIVE BOOST: Phase Audit Logger
from .phase_audit_logger import (
    PhaseAuditLogger,
    DecisionAudit,
    PhaseAuditReport,
    AuditPattern,
    AuditStats,
    get_phase_audit_logger,
    reset_phase_audit_logger,
)

__all__ = [
    # Enums
    "HiveMindState",
    "UserBreakpoint",
    "RetentionDecision",

    # Types
    "IndependentAnalysis",
    "AnalysisComparison",
    "Disagreement",
    "DebateArgument",
    "DebateResult",
    "AgentSpec",
    "AgentArchitecture",
    "ExecutionIssue",
    "MonitoredStepResult",
    "FailureDiagnosis",
    "RetryDecision",
    "KnowledgeConsolidation",
    "AgentRetention",
    "BreakpointOption",
    "BreakpointRequest",
    "BreakpointResponse",

    # Components
    "AgentRegistry",
    "CostEstimator",
    "HiveMindContextManager",
    "StrategyBlacklist",
    "UserInteractionHandler",
    "AdaptiveDebateConfig",
    "DebateParams",
    "TaskComplexity",

    # Orchestrator
    "TrueHiveMind",
    "HiveMindResult",

    # V8.3 SwarmBridge - Hive Mind → Swarm Delegation
    "SwarmBridge",
    "SwarmDelegationResult",
    "HivePhase",
    "suggest_mode_for_subtask",
    "create_bridge_for_phase",

    # V8.4.4 SagaManager - Checkpoint/Recovery
    "SagaManager",
    "PhaseCheckpoint",
    "SagaContext",
    "PHASE_ORDER",
    "PHASE_GUARDS",

    # V12.4: Phase Coordinator
    "PhaseCoordinator",
    "PhaseState",
    "PhaseTransition",
    "TransitionResult",
    "get_phase_coordinator",
    "reset_phase_coordinator",

    # V12.4: Consensus Tracker
    "ConsensusTracker",
    "TopicConsensus",
    "ConsensusReport",
    "get_consensus_tracker",
    "reset_consensus_tracker",

    # V12.4 COGNITIVE BOOST: Phase Audit Logger
    "PhaseAuditLogger",
    "DecisionAudit",
    "PhaseAuditReport",
    "AuditPattern",
    "AuditStats",
    "get_phase_audit_logger",
    "reset_phase_audit_logger",
]
