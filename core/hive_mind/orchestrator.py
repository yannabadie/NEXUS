"""
NEXUS V8.0 - TRUE HIVE MIND Orchestrator

Main coordinator for the 7-phase Hive Mind pipeline.
Entry point called by FSMHandlers when complexity >= MODERATE.

Usage:
    hive_mind = TrueHiveMind(
        workspace_path=workspace_path,
        config=config,
        gemini_driver=gemini_driver,
        claude_driver=claude_driver,
        agent_pool=agent_pool,  # Existing V7 AgentPool
        budget_tracker=budget_tracker,  # Existing V7 BudgetTracker
        project_memory=project_memory  # Existing V7 ProjectMemory
    )

    result = await hive_mind.process_task("Complex task here")
"""

import asyncio
import logging
import time
import uuid
from pathlib import Path
from typing import Dict, Any, Optional, TYPE_CHECKING
from dataclasses import dataclass

from .types import HiveMindState, UserBreakpoint
from .agent_registry import AgentRegistry
from .cost_estimator import CostEstimator
from .context_manager import HiveMindContextManager
from .strategy_blacklist import StrategyBlacklist
from .user_interaction import UserInteractionHandler
from .adaptive_debate import AdaptiveDebateConfig, TaskComplexity

from .phases import (
    IndependentAnalysisPhase,
    StrategicDebatePhase,
    ArchitectureGenerationPhase,
    MonitoredExecutionPhase,
    FailureDiagnosisPhase,
    AdaptiveRetryPhase,
    KnowledgeConsolidationPhase,
)

# V8.0.1: Hot-Swap Lead Agent
from core.fsm.stagnation_detector import StagnationDetector

if TYPE_CHECKING:
    from core.drivers.gemini_driver_v7 import GeminiDriverV7
    from core.drivers.claude_driver_v7 import ClaudeDriverV7
    from core.swarm import AgentPool
    from core.telemetry import BudgetTracker
    from core.memory import ProjectMemory

logger = logging.getLogger(__name__)


@dataclass
class HiveMindResult:
    """Result of a Hive Mind task execution."""
    success: bool
    output: str
    state: HiveMindState
    phases_completed: list
    total_duration: float
    total_tokens: int
    agents_used: list
    agents_spawned: list
    artifacts_created: list
    knowledge_archived: int
    error: Optional[str] = None


class TrueHiveMind:
    """
    TRUE HIVE MIND V8.0 Orchestrator

    Coordinates the 7-phase pipeline for complex tasks.
    Integrates with existing V7 components.
    """

    def __init__(
        self,
        workspace_path: Path,
        config: Any,
        gemini_driver: "GeminiDriverV7",
        claude_driver: "ClaudeDriverV7",
        agent_pool: "AgentPool" = None,
        budget_tracker: "BudgetTracker" = None,
        project_memory: "ProjectMemory" = None,
        success_memory: "SuccessMemory" = None,  # V8.2.0
        on_state_change: callable = None,
        auto_breakpoints: bool = True,
        swarm_engine: "HybridSwarmEngine" = None  # V8.4.5: SwarmBridge wiring fix
    ):
        """
        Initialize TRUE HIVE MIND.

        Args:
            workspace_path: NEXUS workspace path
            config: NEXUS configuration
            gemini_driver: Gemini driver instance
            claude_driver: Claude driver instance
            agent_pool: Existing V7 AgentPool (for DyLAN metrics)
            budget_tracker: Existing V7 BudgetTracker (for USD limits)
            project_memory: Existing V7 ProjectMemory (for RAG)
            success_memory: V8.2.0 SuccessMemory (for learning from successes)
            on_state_change: Callback for state changes
            auto_breakpoints: Enable user breakpoints
            swarm_engine: V8.4.5 - Optional Swarm Engine for Phase 4 delegation
        """
        self.workspace_path = Path(workspace_path)
        self.config = config
        self.gemini = gemini_driver
        self.claude = claude_driver
        self.agent_pool = agent_pool
        self.budget_tracker = budget_tracker
        self.project_memory = project_memory
        self.success_memory = success_memory  # V8.2.0
        self.on_state_change = on_state_change
        self.auto_breakpoints = auto_breakpoints
        self.swarm_engine = swarm_engine  # V8.4.5: SwarmBridge wiring

        # Current state
        self.state = HiveMindState.HIVE_GATING
        self._current_task: str = ""

        # Initialize V8 components
        self._init_components()

        logger.info("TrueHiveMind V8.0 initialized", extra={
            "workspace": str(workspace_path),
            "breakpoints_enabled": auto_breakpoints
        })

    def _init_components(self):
        """Initialize Hive Mind components."""
        # Budget: Get limit from config or default
        budget_limit = getattr(self.config, 'hive_mind_budget_limit', 50000)

        # Core components
        self.cost_estimator = CostEstimator(budget_limit=budget_limit)
        self.context_manager = HiveMindContextManager(max_tokens=budget_limit)
        self.agent_registry = AgentRegistry(self.workspace_path)
        self.strategy_blacklist = StrategyBlacklist(self.workspace_path)
        self.debate_config = AdaptiveDebateConfig()

        # V8.0.1: Hot-Swap Lead Agent support
        self.stagnation_detector = StagnationDetector(
            similarity_threshold=0.8,
            window_size=3,
            strategy_blacklist=self.strategy_blacklist
        )
        self._current_lead = "gemini"  # Default lead agent
        self._lead_swap_count = 0

        # User interaction
        self.user_handler = UserInteractionHandler(
            default_timeout=getattr(self.config, 'hive_mind_breakpoint_timeout', 60),
            enable_rich=True,
            auto_accept=not self.auto_breakpoints
        )

        # Initialize phases
        self._init_phases()

    def _init_phases(self):
        """Initialize all 7 phases."""
        # Phase 1: Independent Analysis
        self.phase_analysis = IndependentAnalysisPhase(
            gemini_driver=self.gemini,
            claude_driver=self.claude,
            cost_estimator=self.cost_estimator,
            context_manager=self.context_manager
        )

        # Phase 2: Strategic Debate
        self.phase_debate = StrategicDebatePhase(
            gemini_driver=self.gemini,
            claude_driver=self.claude,
            cost_estimator=self.cost_estimator,
            context_manager=self.context_manager,
            debate_config=self.debate_config
        )

        # Phase 3: Architecture Generation
        self.phase_architecture = ArchitectureGenerationPhase(
            gemini_driver=self.gemini,
            claude_driver=self.claude,
            cost_estimator=self.cost_estimator,
            context_manager=self.context_manager,
            agent_registry=self.agent_registry,
            user_handler=self.user_handler,
            workspace_path=self.workspace_path
        )

        # Phase 4: Monitored Execution
        # V8.4.5: Pass swarm_engine for SwarmBridge delegation (Dictator Mode)
        self.phase_execution = MonitoredExecutionPhase(
            gemini_driver=self.gemini,
            claude_driver=self.claude,
            cost_estimator=self.cost_estimator,
            context_manager=self.context_manager,
            swarm_engine=self.swarm_engine
        )

        # Phase 5: Failure Diagnosis
        self.phase_diagnosis = FailureDiagnosisPhase(
            gemini_driver=self.gemini,
            claude_driver=self.claude,
            cost_estimator=self.cost_estimator,
            context_manager=self.context_manager,
            user_handler=self.user_handler
        )

        # Phase 6: Adaptive Retry
        self.phase_retry = AdaptiveRetryPhase(
            cost_estimator=self.cost_estimator,
            context_manager=self.context_manager,
            blacklist=self.strategy_blacklist
        )

        # Phase 7: Knowledge Consolidation
        self.phase_consolidation = KnowledgeConsolidationPhase(
            gemini_driver=self.gemini,
            claude_driver=self.claude,
            cost_estimator=self.cost_estimator,
            context_manager=self.context_manager,
            agent_registry=self.agent_registry,
            user_handler=self.user_handler,
            project_memory=self.project_memory
        )

    def _set_state(self, new_state: HiveMindState):
        """Change state and notify."""
        old_state = self.state
        self.state = new_state
        logger.debug(f"State: {old_state.value} -> {new_state.value}")
        if self.on_state_change:
            self.on_state_change(old_state, new_state)

    async def process_task(
        self,
        task: str,
        complexity: TaskComplexity = TaskComplexity.MODERATE
    ) -> HiveMindResult:
        """
        Process a task through the Hive Mind pipeline.

        Args:
            task: Task description
            complexity: Task complexity level

        Returns:
            HiveMindResult with outcome
        """
        logger.info(f"Processing task: {task[:100]}...")
        self._current_task = task
        start_time = time.time()
        phases_completed = []
        agents_spawned = []
        
        # V10: Generate session_uuid for context isolation
        # Critical for: agent spawning, swarm, session persistence, context leakage prevention
        self._current_session_uuid = str(uuid.uuid4())
        logger.debug(f"HiveMind session started", session_uuid=self._current_session_uuid[:8])

        try:
            # Reset for new task
            self.cost_estimator.start_task()
            self.phase_retry.reset_retry_count()
            self.context_manager.clear(keep_critical=False)

            # Check budget before starting
            if self.budget_tracker:
                # Integration with V7 BudgetTracker
                estimated_cost = self.cost_estimator.estimate_full_hive_mind()
                # TODO: Convert tokens to USD and check with budget_tracker

            # =========================================================
            # PHASE 1: Independent Analysis
            # =========================================================
            self._set_state(HiveMindState.HIVE_ANALYZING_GEMINI)
            analysis_result = await self.phase_analysis.execute(task, session_uuid=self._current_session_uuid)
            phases_completed.append("analysis")

            # =========================================================
            # PHASE 2: Strategic Debate (if needed)
            # =========================================================
            if analysis_result.needs_debate:
                self._set_state(HiveMindState.HIVE_DEBATING)
                debate_result = await self.phase_debate.execute(
                    task=task,
                    comparison=analysis_result.comparison,
                    complexity=complexity
                )
                phases_completed.append("debate")

                # User breakpoint after debate
                if self.auto_breakpoints and not debate_result.was_skipped:
                    self._set_state(HiveMindState.HIVE_BREAKPOINT_DEBATE)
                    response = self.user_handler.after_debate(
                        debate_summary=str(debate_result.debate_result.debate_history[-3:]) if debate_result.debate_result.debate_history else "No debate history",
                        final_approach=debate_result.final_approach,
                        consensus_score=debate_result.debate_result.consensus_confidence
                    )
                    if response.chosen_option == "cancel":
                        return self._create_cancelled_result(
                            phases_completed, start_time, "User cancelled after debate"
                        )
            else:
                # Skip debate - use analysis consensus
                debate_result = self.phase_debate._create_skipped_result(
                    analysis_result.comparison
                )
                phases_completed.append("debate_skipped")

            # =========================================================
            # PHASE 3: Architecture Generation
            # =========================================================
            self._set_state(HiveMindState.HIVE_ARCHITECTING)
            arch_result = await self.phase_architecture.execute(
                task=task,
                debate_result=debate_result.debate_result
            )
            phases_completed.append("architecture")
            agents_spawned = arch_result.agents_spawned

            # =========================================================
            # PHASE 4-6: Execution Loop (with retry)
            # =========================================================
            execution_success = False
            execution_result = None
            max_attempts = 4  # 1 initial + 3 retries

            for attempt in range(max_attempts):
                # PHASE 4: Monitored Execution
                self._set_state(HiveMindState.HIVE_EXECUTING)
                execution_result = await self.phase_execution.execute(
                    task=task,
                    architecture=arch_result.architecture
                )

                if execution_result.success:
                    execution_success = True
                    phases_completed.append(f"execution_success_attempt_{attempt + 1}")
                    break

                phases_completed.append(f"execution_failed_attempt_{attempt + 1}")

                # Check if diagnosis needed
                if not execution_result.needs_diagnosis:
                    break

                # PHASE 5: Failure Diagnosis
                self._set_state(HiveMindState.HIVE_DIAGNOSING)
                diagnosis_result = await self.phase_diagnosis.execute(
                    task=task,
                    step_results=execution_result.step_results,
                    issues=execution_result.issues,
                    failure_step=execution_result.failure_step
                )
                phases_completed.append("diagnosis")

                # Check user decision
                if diagnosis_result.user_decision in ("abort", "escalate"):
                    return self._create_failed_result(
                        phases_completed=phases_completed,
                        start_time=start_time,
                        error=f"User chose to {diagnosis_result.user_decision}",
                        execution_result=execution_result
                    )

                # PHASE 6: Adaptive Retry
                self._set_state(HiveMindState.HIVE_APPLYING_CHANGES)
                retry_recommendations = self.phase_diagnosis.get_retry_recommendations(
                    diagnosis_result
                )
                retry_result = self.phase_retry.execute(
                    diagnosis=diagnosis_result.diagnosis,
                    current_architecture=arch_result.architecture,
                    recommendations=retry_recommendations,
                    user_decision=diagnosis_result.user_decision
                )

                if retry_result.decision.action != "RETRY":
                    # Can't retry - escalate
                    return self._create_failed_result(
                        phases_completed=phases_completed,
                        start_time=start_time,
                        error=retry_result.decision.reason,
                        execution_result=execution_result
                    )

                # =========================================================
                # V8.0.1: Hot-Swap Lead Agent Check
                # =========================================================
                swap_result = self._check_and_swap_lead(
                    diagnosis_result.diagnosis,
                    arch_result.architecture
                )
                if swap_result["swapped"]:
                    phases_completed.append(f"lead_swapped_{swap_result['new_lead']}")
                    logger.info(f"Hot-Swap: Lead changed to {swap_result['new_lead']}")
                    # Update architecture to use new lead
                    if hasattr(arch_result.architecture, 'lead_agent'):
                        arch_result.architecture.lead_agent = swap_result['new_lead']

                # Update architecture for retry
                if retry_result.modified_architecture:
                    arch_result.architecture = retry_result.modified_architecture

                phases_completed.append(f"retry_attempt_{attempt + 1}")

            # =========================================================
            # PHASE 7: Knowledge Consolidation
            # =========================================================
            self._set_state(HiveMindState.HIVE_REFLECTING)
            consolidation_result = await self.phase_consolidation.execute(
                task=task,
                success=execution_success,
                duration=time.time() - start_time,
                steps_completed=len(execution_result.step_results) if execution_result else 0,
                issues_count=len(execution_result.issues) if execution_result else 0,
                approach=debate_result.final_approach,
                agents_used=arch_result.architecture.agents_to_use,
                agents_spawned=agents_spawned
            )
            phases_completed.append("consolidation")

            # Mark success in retry system
            if execution_success:
                self.phase_retry.mark_success(
                    arch_result.architecture,
                    diagnosis_result.diagnosis if 'diagnosis_result' in dir() else None
                )

            # Archive context insights to RAG
            if self.project_memory:
                archived = self.context_manager.archive_to_rag(
                    self.project_memory,
                    session_id=f"hive_mind_{int(start_time)}"
                )
                logger.info(f"Archived {archived} insights to RAG")

            # =========================================================
            # SUCCESS
            # =========================================================
            self._set_state(HiveMindState.HIVE_SUCCESS)

            # V8.2.0: Record success to SuccessMemory for learning
            if self.success_memory and execution_success:
                try:
                    from .success_adapter import create_hive_mind_adapters

                    analysis_adapter, result_adapter = create_hive_mind_adapters(
                        task=task,
                        duration=time.time() - start_time,
                        success=execution_success,
                        phases_completed=len(phases_completed),
                        agents_used=arch_result.architecture.agents_to_use if arch_result else ["gemini", "claude"]
                    )

                    self.success_memory.record_success(
                        task_id=f"hive_{int(start_time)}",
                        analysis=analysis_adapter,
                        result=result_adapter,
                        quality_score=0.8 if execution_success else 0.3
                    )
                    logger.debug("Recorded HiveMind success to memory")
                except Exception as mem_err:
                    logger.warning(f"Failed to record HiveMind success: {mem_err}")

            return HiveMindResult(
                success=execution_success,
                output=self._format_output(execution_result, consolidation_result),
                state=HiveMindState.HIVE_SUCCESS,
                phases_completed=phases_completed,
                total_duration=time.time() - start_time,
                total_tokens=self.cost_estimator.spent,
                agents_used=arch_result.architecture.agents_to_use,
                agents_spawned=agents_spawned,
                artifacts_created=execution_result.artifacts_created if execution_result else [],
                knowledge_archived=consolidation_result.archived_to_rag
            )

        except Exception as e:
            logger.error(f"Hive Mind error: {e}", exc_info=True)
            self._set_state(HiveMindState.HIVE_FAILED)

            return HiveMindResult(
                success=False,
                output=f"Hive Mind failed: {e}",
                state=HiveMindState.HIVE_FAILED,
                phases_completed=phases_completed,
                total_duration=time.time() - start_time,
                total_tokens=self.cost_estimator.spent,
                agents_used=[],
                agents_spawned=agents_spawned,
                artifacts_created=[],
                knowledge_archived=0,
                error=str(e)
            )

    def _format_output(self, execution_result, consolidation_result) -> str:
        """Format the final output."""
        lines = []

        if execution_result:
            lines.append("## Execution Results")
            for step_result in execution_result.step_results:
                status = "✓" if step_result.status == "success" else "✗"
                lines.append(f"{status} {step_result.step_name}: {step_result.output[:200]}")

            if execution_result.artifacts_created:
                lines.append("\n## Artifacts Created")
                for artifact in execution_result.artifacts_created:
                    lines.append(f"- {artifact}")

        if consolidation_result and consolidation_result.consolidation.learned_patterns:
            lines.append("\n## Learned Patterns")
            for pattern in consolidation_result.consolidation.learned_patterns[:5]:
                lines.append(f"- {pattern}")

        return "\n".join(lines) if lines else "Task completed"

    def _create_cancelled_result(
        self,
        phases_completed: list,
        start_time: float,
        reason: str
    ) -> HiveMindResult:
        """Create result for user-cancelled task."""
        return HiveMindResult(
            success=False,
            output=f"Task cancelled: {reason}",
            state=HiveMindState.HIVE_ESCALATE,
            phases_completed=phases_completed,
            total_duration=time.time() - start_time,
            total_tokens=self.cost_estimator.spent,
            agents_used=[],
            agents_spawned=[],
            artifacts_created=[],
            knowledge_archived=0,
            error=reason
        )

    def _create_failed_result(
        self,
        phases_completed: list,
        start_time: float,
        error: str,
        execution_result=None
    ) -> HiveMindResult:
        """Create result for failed task."""
        return HiveMindResult(
            success=False,
            output=f"Task failed: {error}",
            state=HiveMindState.HIVE_FAILED,
            phases_completed=phases_completed,
            total_duration=time.time() - start_time,
            total_tokens=self.cost_estimator.spent,
            agents_used=[],
            agents_spawned=[],
            artifacts_created=execution_result.artifacts_created if execution_result else [],
            knowledge_archived=0,
            error=error
        )

    def get_stats(self) -> Dict[str, Any]:
        """Get Hive Mind statistics."""
        return {
            "current_state": self.state.value,
            "cost_stats": self.cost_estimator.get_stats(),
            "context_stats": self.context_manager.get_stats(),
            "registry_stats": self.agent_registry.get_stats(),
            "blacklist_stats": self.strategy_blacklist.get_stats(),
            "debate_stats": self.debate_config.get_stats(),
            "hot_swap_stats": {
                "current_lead": self._current_lead,
                "swap_count": self._lead_swap_count,
                "stagnation": self.stagnation_detector.get_stats()
            }
        }

    # =========================================================================
    # V8.0.1: Hot-Swap Lead Agent
    # =========================================================================

    def _check_and_swap_lead(
        self,
        diagnosis: str,
        architecture: Any
    ) -> Dict[str, Any]:
        """
        V8.0.1: Check if lead agent should be swapped due to repeated failures.

        Called after failure diagnosis to determine if swapping lead might help.
        Uses StagnationDetector to track failure patterns.

        Args:
            diagnosis: Diagnosis text from failure analysis
            architecture: Current task architecture

        Returns:
            Dict with swap decision:
            - swapped: bool - Whether swap occurred
            - new_lead: str - New lead agent (if swapped)
            - reason: str - Reason for decision
        """
        # Record this failure for stagnation tracking
        self.stagnation_detector.add_message(diagnosis)
        self.stagnation_detector.record_agent_failure(self._current_lead)

        # Check if swap is recommended
        recommendation = self.stagnation_detector.get_swap_recommendation(
            self._current_lead
        )

        if recommendation["should_swap"]:
            # Perform the swap
            old_lead = self._current_lead
            self._current_lead = recommendation["new_lead"]
            self._lead_swap_count += 1

            # Report to blacklist for future reference
            self.stagnation_detector.report_to_blacklist(
                task_context=f"Task failed with {old_lead} as lead"
            )

            # Reset stagnation detector for fresh start with new lead
            self.stagnation_detector.reset()

            logger.info(
                f"Hot-Swap Lead: {old_lead} -> {self._current_lead} "
                f"(reason: {recommendation['reason']})"
            )

            return {
                "swapped": True,
                "old_lead": old_lead,
                "new_lead": self._current_lead,
                "reason": recommendation["reason"],
                "swap_count": self._lead_swap_count
            }

        return {
            "swapped": False,
            "new_lead": None,
            "reason": "No swap needed - stagnation threshold not reached"
        }

    def force_lead_swap(self, new_lead: str) -> Dict[str, Any]:
        """
        V8.0.1: Manually force a lead agent swap.

        Useful for testing or when user wants to try different lead.

        Args:
            new_lead: New lead agent ("gemini" or "claude")

        Returns:
            Dict with swap result
        """
        if new_lead.lower() not in ("gemini", "claude"):
            return {
                "swapped": False,
                "error": f"Invalid lead agent: {new_lead}. Must be 'gemini' or 'claude'"
            }

        old_lead = self._current_lead
        self._current_lead = new_lead.lower()
        self._lead_swap_count += 1
        self.stagnation_detector.reset()

        logger.info(f"Manual Lead Swap: {old_lead} -> {self._current_lead}")

        return {
            "swapped": True,
            "old_lead": old_lead,
            "new_lead": self._current_lead,
            "reason": "Manual swap requested",
            "swap_count": self._lead_swap_count
        }

    def get_current_lead(self) -> str:
        """V8.0.1: Get current lead agent."""
        return self._current_lead
