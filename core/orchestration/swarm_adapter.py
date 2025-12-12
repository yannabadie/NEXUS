"""
NEXUS V7.8 - Swarm Bridge Module (Phase 14c)

Extracted from orchestration_v7.py to follow Single Responsibility Principle.

This module bridges the orchestrator with the HybridSwarmEngine:
- start_swarm_mode(): Initialize swarm for a task
- process_with_swarm(): Full swarm pipeline execution

Usage:
    bridge = SwarmBridge(orchestrator)
    result = bridge.process_with_swarm(task_input, force_mode=CollaborationMode.PARALLEL)
"""

import logging
from typing import TYPE_CHECKING, Dict, Optional, Callable

from core.fsm.states import OrchestratorState
from core.swarm import CollaborationMode, SwarmPhase
from core.ui.event_bus import EventBus
import asyncio

if TYPE_CHECKING:
    from core.orchestration_v7 import OrchestratorV7


class SwarmBridge:
    """
    Bridge between orchestrator and HybridSwarmEngine.

    Handles all swarm-related operations:
    - Mode initialization
    - Task processing
    - Result integration

    Phase 14c: Extracted from OrchestratorV7 for better maintainability.
    """

    def __init__(self, orchestrator: 'OrchestratorV7'):
        """
        Initialize swarm bridge with orchestrator reference.

        Uses composition pattern - bridge accesses orchestrator state
        but doesn't own it.

        Args:
            orchestrator: Parent OrchestratorV7 instance
        """
        self._orch = orchestrator
        self._logger = logging.getLogger("nexus.swarm_bridge")

    @property
    def is_enabled(self) -> bool:
        """Check if swarm engine is enabled."""
        return self._orch.swarm_engine is not None

    def start_swarm_mode(
        self,
        objective: str,
        force_mode: Optional[CollaborationMode] = None
    ) -> Dict:
        """
        Start Hybrid Swarm mode for a task (V7 Sprint 9).

        This bypasses the normal IDLE→BRAINSTORMING flow and uses
        the HybridSwarmEngine for dynamic mode negotiation.

        Args:
            objective: Task description
            force_mode: Optional mode to force (skip negotiation)

        Returns:
            Initial swarm result dict
        """
        if not self.is_enabled:
            return self._make_result("ERROR", "Swarm engine not enabled", None, False, error="SWARM_DISABLED")

        # Set objective
        self._orch.blackboard["objective"] = objective
        self._orch.blackboard["mode"] = "SWARM"

        # Transition to swarm analyzing
        self._orch._transition_to(OrchestratorState.SWARM_ANALYZING)

        return self._make_result(
            "SWARM_ANALYZING",
            f"[Swarm Mode Started]\nObjective: {objective}\nForce mode: {force_mode.value if force_mode else 'auto'}",
            None,
            False
        )

    def process_with_swarm(
        self,
        task_input: str,
        force_mode: Optional[CollaborationMode] = None,
        skip_negotiation: bool = False,
        on_negotiation_turn: Optional[Callable] = None,
        on_execution_round: Optional[Callable] = None
    ) -> Dict:
        """
        Process a task using HybridSwarmEngine directly (V7 Sprint 9).

        Runs the full swarm pipeline synchronously and returns the result.
        This is a convenience method for when you want to use swarm
        without going through the FSM states.

        Args:
            task_input: Task description
            force_mode: Force a specific collaboration mode
            skip_negotiation: Skip negotiation phase
            on_negotiation_turn: V7.5 callback for real-time negotiation display
            on_execution_round: V7.5 callback for real-time execution display

        Returns:
            Result dict with swarm output
        """
        if not self.is_enabled:
            return self._make_result("ERROR", "Swarm engine not enabled", None, False, error="SWARM_DISABLED")

        try:
            # V9.1: Real-time Telemetry Callbacks
            async def _on_negotiation_turn(turn_data: Dict):
                await EventBus.publish("SWARM_NEGOTIATION", turn_data)
                if on_negotiation_turn:
                    on_negotiation_turn(turn_data)

            async def _on_execution_round(round_data: Dict):
                await EventBus.publish("SWARM_EXECUTION", round_data)
                if on_execution_round:
                    on_execution_round(round_data)

            # Bridge sync callbacks to async EventBus
            def sync_negotiation_callback(data):
                try:
                    loop = asyncio.get_running_loop()
                    loop.create_task(_on_negotiation_turn(data))
                except RuntimeError:
                    pass

            def sync_execution_callback(data):
                try:
                    loop = asyncio.get_running_loop()
                    loop.create_task(_on_execution_round(data))
                except RuntimeError:
                    pass

            result = self._orch.swarm_engine.process_task(
                task_input=task_input,
                blackboard=self._orch.blackboard,
                force_mode=force_mode,
                skip_negotiation=skip_negotiation,
                on_negotiation_turn=sync_negotiation_callback,
                on_execution_round=sync_execution_callback
            )

            # Update history with swarm result
            self._orch.memory.add_to_history({
                "sender": "Swarm",
                "action_type": "SWARM_RESULT",
                "content": result.final_output[:2000]
            })

            return {
                "state": result.status.value,
                "output": result.final_output,
                "agent": "Swarm",  # V7 FIX: Add agent key for display_result
                "mode": result.selected_mode.value,
                "finished": result.status == SwarmPhase.COMPLETED,
                "analysis": result.task_analysis.to_dict(),
                "execution": result.execution_result.to_dict()
            }

        except Exception as e:
            self._logger.error(f"Swarm processing failed: {e}")
            return self._make_result("ERROR", f"Swarm failed: {e}", None, False, error=str(e))

    def get_swarm_stats(self) -> Optional[Dict]:
        """
        Get current swarm engine statistics.

        Returns:
            Stats dict or None if swarm not enabled
        """
        if not self.is_enabled:
            return None
        return self._orch.swarm_engine.get_stats()

    def _make_result(
        self,
        state: str,
        output: Optional[str],
        agent: Optional[str],
        finished: bool,
        **kwargs
    ) -> Dict:
        """
        Create standardized result dictionary.

        Helper method matching OrchestratorV7._make_result signature.

        Args:
            state: Current state name
            output: Output content
            agent: Active agent name
            finished: Whether task is finished
            **kwargs: Additional fields (error, etc.)

        Returns:
            Result dict
        """
        result = {
            "state": state,
            "output": output,
            "agent": agent,
            "finished": finished
        }
        result.update(kwargs)
        return result
