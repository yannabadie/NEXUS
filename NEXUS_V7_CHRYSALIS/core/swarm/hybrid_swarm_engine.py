"""
Hybrid Swarm Engine - Sprint 9 Main Orchestration

The central engine that coordinates:
1. Task analysis
2. Mode selection (DyLAN-based)
3. Agent negotiation (optional)
4. Mode execution
5. Result merging and metrics update

Entry point for dynamic multi-agent collaboration where
agents negotiate the optimal mode for each task.

Usage:
    from core.swarm import HybridSwarmEngine

    engine = HybridSwarmEngine(agent_pool, model_router, config)
    result = engine.process_task("Fix the auth bug", blackboard)
"""

from dataclasses import dataclass, field
from typing import Dict, Optional, Callable, Any, List
from datetime import datetime
from enum import Enum

from .agent_metrics import AgentPool, AgentInvocationResult, create_default_pool
from .collaboration_modes import CollaborationMode
from .task_analyzer import TaskAnalyzer, TaskAnalysis
from .mode_selector import ModeSelector, ModeProposal
from .negotiation_protocol import (
    NegotiationProtocol,
    NegotiationResult,
    NegotiationStatus
)
from .mode_executors import (
    ExecutionContext,
    ExecutionResult,
    ExecutionStatus,
    AgentResponse,
    get_executor
)


class SwarmPhase(Enum):
    """Current phase of swarm processing"""
    IDLE = "idle"
    ANALYZING = "analyzing"
    SELECTING = "selecting"
    NEGOTIATING = "negotiating"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class SwarmResult:
    """
    Final result from Hybrid Swarm processing.

    Contains the output, metrics, and full processing history.
    """
    status: SwarmPhase
    final_output: str
    selected_mode: CollaborationMode
    task_analysis: TaskAnalysis
    mode_proposal: ModeProposal
    negotiation_result: Optional[NegotiationResult]
    execution_result: ExecutionResult
    total_time_seconds: float
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict:
        return {
            "status": self.status.value,
            "final_output": self.final_output[:2000],
            "selected_mode": self.selected_mode.value,
            "task_analysis": self.task_analysis.to_dict(),
            "mode_proposal": self.mode_proposal.to_dict(),
            "negotiation_result": (
                self.negotiation_result.to_dict()
                if self.negotiation_result else None
            ),
            "execution_result": self.execution_result.to_dict(),
            "total_time_seconds": round(self.total_time_seconds, 2),
            "timestamp": self.timestamp.isoformat()
        }


class HybridSwarmEngine:
    """
    Main Hybrid Swarm Engine for dynamic multi-agent collaboration.

    Coordinates the full pipeline:
    Task → Analysis → Mode Selection → Negotiation → Execution → Result

    The engine can operate in different modes:
    - Full: Analysis + Selection + Negotiation + Execution
    - Fast: Analysis + Selection + Execution (skip negotiation)
    - Forced: User-specified mode + Execution
    """

    def __init__(
        self,
        agent_pool: Optional[AgentPool] = None,
        model_router: Optional[Any] = None,
        config: Optional[Any] = None,
        invoke_agent: Optional[Callable] = None
    ):
        """
        Initialize Hybrid Swarm Engine.

        Args:
            agent_pool: AgentPool for DyLAN metrics
            model_router: ModelRouter for agent selection
            config: Configuration object
            invoke_agent: Callable to invoke agents
        """
        self.agent_pool = agent_pool or create_default_pool()
        self.model_router = model_router
        self.config = config
        self.invoke_agent = invoke_agent

        # Components
        self.task_analyzer = TaskAnalyzer()
        self.mode_selector = ModeSelector(agent_pool=self.agent_pool)
        self.negotiation = NegotiationProtocol(
            max_turns=self._get_config("swarm_negotiation_max_turns", 4),
            skip_trivial=self._get_config("swarm_skip_trivial", True)
        )

        # State
        self.current_phase = SwarmPhase.IDLE
        self._current_analysis: Optional[TaskAnalysis] = None
        self._current_proposal: Optional[ModeProposal] = None
        self._negotiation_result: Optional[NegotiationResult] = None

        # History
        self.processing_history: List[Dict] = []

    def _get_config(self, key: str, default: Any) -> Any:
        """Get config value with fallback"""
        if self.config is None:
            return default
        return getattr(self.config, key, default)

    def process_task(
        self,
        task_input: str,
        blackboard: Optional[Dict] = None,
        force_mode: Optional[CollaborationMode] = None,
        skip_negotiation: bool = False
    ) -> SwarmResult:
        """
        Process a task through the full Hybrid Swarm pipeline.

        Args:
            task_input: User's task description
            blackboard: Shared state dictionary
            force_mode: Force a specific mode (skip selection)
            skip_negotiation: Skip negotiation even if enabled

        Returns:
            SwarmResult with complete processing details
        """
        start_time = datetime.now()
        blackboard = blackboard or {}

        try:
            # Phase 1: Analyze task
            self.current_phase = SwarmPhase.ANALYZING
            analysis = self.task_analyzer.analyze(task_input)
            self._current_analysis = analysis

            # Phase 2: Select mode (or use forced mode)
            self.current_phase = SwarmPhase.SELECTING
            if force_mode:
                proposal = self._create_forced_proposal(force_mode, analysis)
            else:
                proposal = self.mode_selector.select_mode(analysis)
            self._current_proposal = proposal

            # Phase 3: Negotiate (if enabled and not skipped)
            negotiation_enabled = self._get_config("swarm_negotiation_enabled", True)
            negotiation_result = None

            if negotiation_enabled and not skip_negotiation and not force_mode:
                self.current_phase = SwarmPhase.NEGOTIATING
                negotiation_result = self._run_negotiation(analysis, proposal)
                self._negotiation_result = negotiation_result

                # Update mode and assignments from negotiation
                if negotiation_result.status == NegotiationStatus.CONSENSUS:
                    final_mode = negotiation_result.selected_mode
                    agent_assignments = negotiation_result.agent_assignments
                else:
                    final_mode = proposal.mode
                    agent_assignments = proposal.agent_assignments
            else:
                final_mode = proposal.mode
                agent_assignments = proposal.agent_assignments

            # Phase 4: Execute
            self.current_phase = SwarmPhase.EXECUTING
            execution_context = ExecutionContext(
                task_input=task_input,
                agent_assignments=agent_assignments,
                blackboard=blackboard,
                max_rounds=self._get_config("swarm_max_rounds", 6),
                invoke_agent=self._wrap_invoke_agent()
            )

            executor = get_executor(final_mode)
            execution_result = executor.execute(execution_context)

            # Phase 5: Update metrics
            self._update_metrics(analysis, execution_result)

            # Complete
            self.current_phase = SwarmPhase.COMPLETED
            total_time = (datetime.now() - start_time).total_seconds()

            result = SwarmResult(
                status=SwarmPhase.COMPLETED,
                final_output=execution_result.final_output,
                selected_mode=final_mode,
                task_analysis=analysis,
                mode_proposal=proposal,
                negotiation_result=negotiation_result,
                execution_result=execution_result,
                total_time_seconds=total_time
            )

            # Record history
            self._record_processing(result)

            return result

        except Exception as e:
            self.current_phase = SwarmPhase.FAILED
            total_time = (datetime.now() - start_time).total_seconds()

            # Create error result
            return SwarmResult(
                status=SwarmPhase.FAILED,
                final_output=f"Swarm processing failed: {str(e)}",
                selected_mode=force_mode or CollaborationMode.PING_PONG,
                task_analysis=self._current_analysis or TaskAnalysis(
                    complexity=1,
                    domains=[],
                    primary_domain=None,
                    raw_input=task_input
                ),
                mode_proposal=self._current_proposal or ModeProposal(
                    mode=CollaborationMode.PING_PONG,
                    confidence=0.0,
                    agent_assignments=[],
                    reasoning="Error fallback"
                ),
                negotiation_result=None,
                execution_result=ExecutionResult(
                    mode=CollaborationMode.PING_PONG,
                    status=ExecutionStatus.FAILED,
                    final_output=str(e),
                    agent_outputs=[],
                    total_rounds=0,
                    total_tokens=0,
                    total_time_seconds=0.0
                ),
                total_time_seconds=total_time
            )

    def _create_forced_proposal(
        self,
        mode: CollaborationMode,
        analysis: TaskAnalysis
    ) -> ModeProposal:
        """Create a proposal for a forced mode"""
        # Use selector to get proper assignments
        proposal = self.mode_selector.select_mode(analysis)
        proposal.mode = mode
        proposal.reasoning = "User forced mode"
        proposal.confidence = 1.0
        return proposal

    def _run_negotiation(
        self,
        analysis: TaskAnalysis,
        proposal: ModeProposal
    ) -> NegotiationResult:
        """Run negotiation protocol"""
        return self.negotiation.run_negotiation(
            task_analysis=analysis,
            initial_proposal=proposal,
            invoke_agent=self._invoke_for_negotiation
        )

    def _invoke_for_negotiation(
        self,
        agent_id: str,
        task_type: str,
        context: str
    ) -> str:
        """Invoke agent for negotiation (returns string)"""
        if self.invoke_agent is None:
            return f"[Mock {agent_id} negotiation response]"

        response = self.invoke_agent(agent_id, task_type, context)

        if isinstance(response, str):
            return response
        elif hasattr(response, 'content'):
            return response.content
        return str(response)

    def _wrap_invoke_agent(self) -> Callable:
        """Wrap invoke_agent to return AgentResponse"""
        def wrapper(agent_id: str, task_type: str, context: str) -> AgentResponse:
            if self.invoke_agent is None:
                return AgentResponse(
                    agent_id=agent_id,
                    content=f"[Mock {agent_id} response]",
                    status="mock"
                )

            start = datetime.now()
            response = self.invoke_agent(agent_id, task_type, context)
            elapsed = (datetime.now() - start).total_seconds()

            if isinstance(response, AgentResponse):
                return response
            elif isinstance(response, str):
                return AgentResponse(
                    agent_id=agent_id,
                    content=response,
                    status="success",
                    time_seconds=elapsed
                )
            elif isinstance(response, dict):
                return AgentResponse(
                    agent_id=agent_id,
                    content=response.get("content", str(response)),
                    status=response.get("status", "success"),
                    tokens_used=response.get("tokens_used", 0),
                    time_seconds=elapsed
                )
            else:
                return AgentResponse(
                    agent_id=agent_id,
                    content=str(response),
                    status="success",
                    time_seconds=elapsed
                )

        return wrapper

    def _update_metrics(
        self,
        analysis: TaskAnalysis,
        result: ExecutionResult
    ):
        """Update DyLAN metrics after execution"""
        if self.agent_pool is None:
            return

        for agent_output in result.agent_outputs:
            invocation = AgentInvocationResult(
                agent_id=agent_output.agent_id,
                task_type=analysis.primary_domain.value if analysis.primary_domain else "unknown",
                success=agent_output.status != "error",
                quality_score=0.7 if agent_output.status != "error" else 0.0,
                tokens_used=agent_output.tokens_used,
                time_seconds=agent_output.time_seconds
            )
            self.agent_pool.record_invocation(invocation)

    def _record_processing(self, result: SwarmResult):
        """Record processing for history"""
        record = {
            "timestamp": result.timestamp.isoformat(),
            "mode": result.selected_mode.value,
            "complexity": result.task_analysis.complexity.name,
            "total_time": result.total_time_seconds,
            "status": result.status.value
        }
        self.processing_history.append(record)

        # Keep last 100
        if len(self.processing_history) > 100:
            self.processing_history = self.processing_history[-100:]

    # === Public API for FSM integration ===

    def start_analysis(self, task_input: str) -> TaskAnalysis:
        """Start analysis phase (for FSM integration)"""
        self.current_phase = SwarmPhase.ANALYZING
        analysis = self.task_analyzer.analyze(task_input)
        self._current_analysis = analysis
        return analysis

    def get_analysis(self) -> Optional[TaskAnalysis]:
        """Get current analysis"""
        return self._current_analysis

    def start_selection(self) -> ModeProposal:
        """Start mode selection phase"""
        self.current_phase = SwarmPhase.SELECTING
        if self._current_analysis is None:
            raise ValueError("Analysis must be run before selection")

        proposal = self.mode_selector.select_mode(self._current_analysis)
        self._current_proposal = proposal
        return proposal

    def start_negotiation(
        self,
        analysis: Optional[TaskAnalysis] = None
    ) -> Optional[NegotiationResult]:
        """Start negotiation phase"""
        self.current_phase = SwarmPhase.NEGOTIATING

        analysis = analysis or self._current_analysis
        proposal = self._current_proposal

        if analysis is None or proposal is None:
            return None

        result = self._run_negotiation(analysis, proposal)
        self._negotiation_result = result
        return result

    def process_negotiation_turn(self) -> Optional[NegotiationResult]:
        """Process a single negotiation turn (for FSM)"""
        # Negotiation is run in one shot for simplicity
        # This method returns the result if negotiation is complete
        return self._negotiation_result

    def execute_turn(
        self,
        task_input: str,
        blackboard: Optional[Dict] = None
    ) -> ExecutionResult:
        """Execute current mode (for FSM integration)"""
        self.current_phase = SwarmPhase.EXECUTING

        mode = self._current_proposal.mode if self._current_proposal else CollaborationMode.PING_PONG
        if self._negotiation_result and self._negotiation_result.status == NegotiationStatus.CONSENSUS:
            mode = self._negotiation_result.selected_mode

        assignments = (
            self._negotiation_result.agent_assignments
            if self._negotiation_result
            else (self._current_proposal.agent_assignments if self._current_proposal else [])
        )

        context = ExecutionContext(
            task_input=task_input,
            agent_assignments=assignments,
            blackboard=blackboard or {},
            max_rounds=self._get_config("swarm_max_rounds", 6),
            invoke_agent=self._wrap_invoke_agent()
        )

        executor = get_executor(mode)
        return executor.execute(context)

    def reset(self):
        """Reset engine state"""
        self.current_phase = SwarmPhase.IDLE
        self._current_analysis = None
        self._current_proposal = None
        self._negotiation_result = None

    def get_stats(self) -> Dict:
        """Get swarm engine statistics"""
        mode_counts = {}
        for record in self.processing_history:
            mode = record["mode"]
            mode_counts[mode] = mode_counts.get(mode, 0) + 1

        return {
            "current_phase": self.current_phase.value,
            "total_processed": len(self.processing_history),
            "mode_distribution": mode_counts,
            "agent_pool_stats": self.agent_pool.get_pool_stats() if self.agent_pool else {},
            "mode_selector_stats": self.mode_selector.get_selection_stats()
        }
