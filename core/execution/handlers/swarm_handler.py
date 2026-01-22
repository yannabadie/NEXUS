"""
Swarm Handler - Delegate subtasks to Swarm Engine.

NEXUS V9.6 Sprint 5.2b - Extracted from tool_manager.py

Provides:
- SwarmDelegateHandler: Delegate tasks to Swarm collaboration modes
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, Any, Optional

from .base import BaseHandler, ToolResult


class SwarmDelegateHandler(BaseHandler):
    """
    Handler for delegating subtasks to the Swarm Engine.

    V8.3.1 SwarmTool - Allows agents to invoke Swarm collaboration modes
    at any HiveMind phase, not just Phase 4 (Execution). Enables debates,
    parallel analysis, etc.

    Includes anti-recursion protection (max depth = 2) to prevent
    "Inception Trap" infinite loops.
    """

    # Maximum Swarm recursion depth (prevents infinite loops)
    MAX_SWARM_DEPTH = 2

    def __init__(
        self,
        workspace_path: Path,
        validation_service: Any = None,
        swarm_bridge: Optional[Any] = None
    ):
        """Initializes the SwarmDelegateHandler.

        Args:
            workspace_path: The absolute path to the workspace root.
            validation_service: Optional service for validating operations.
            swarm_bridge: Optional bridge interface for Swarm interactions.

        Raises:
            None: This method does not explicitly raise exceptions.
        """
        super().__init__(workspace_path, validation_service)
        self._swarm_bridge = swarm_bridge
        self._logger = logging.getLogger(__name__)

    @property
    def tool_name(self) -> str:
        """Returns the name of the tool.

        Returns:
            str: The tool name string identifier "swarm_delegate".
        """
        return "swarm_delegate"

    @property
    def swarm_bridge(self) -> Optional[Any]:
        """Get the configured SwarmBridge."""
        return self._swarm_bridge

    @swarm_bridge.setter
    def swarm_bridge(self, bridge: Any) -> None:
        """Set the SwarmBridge (for lazy initialization)."""
        self._swarm_bridge = bridge

    def execute(self, args: Dict[str, Any]) -> ToolResult:
        """Delegates a subtask to the Swarm Engine for collaborative execution.

        Args:
            args: A dictionary containing the arguments for the task delegation:
                task (str): The subtask description to delegate.
                mode (str, optional): The collaboration mode (e.g., "parallel",
                    "sequential", "lead_support", "ping_pong", "specialist",
                    "red_blue"). Defaults to "specialist".
                phase (str, optional): The hive phase (e.g., "analysis", "debate",
                    "architecture", "execution").
                context_categories (List[str], optional): Categories of context
                    to include (e.g., ["task", "architecture"]).
                _swarm_depth (int, optional): Internal recursion depth tracking.

        Returns:
            ToolResult: The result of the swarm execution, containing status,
                output, and error information.

        Raises:
            None: Exceptions are caught and returned as error ToolResults.
        """
        # V8.3.1-hotfix: Anti-recursion depth guard ("Inception Trap" prevention)
        current_depth = args.get("_swarm_depth", 0)

        if current_depth >= self.MAX_SWARM_DEPTH:
            self._logger.warning(
                f"swarm_delegate blocked: depth {current_depth} >= max {self.MAX_SWARM_DEPTH}"
            )
            return ToolResult(
                tool_name=self.tool_name,
                status="ERROR",
                output="",
                error=(
                    f"Max swarm recursion depth ({self.MAX_SWARM_DEPTH}) reached. "
                    f"Nested Swarm calls are limited to prevent infinite loops."
                )
            )

        # Guard: SwarmBridge must be configured
        if self._swarm_bridge is None:
            return ToolResult(
                tool_name=self.tool_name,
                status="ERROR",
                output="",
                error="SwarmBridge not configured. Cannot delegate to Swarm."
            )

        task = args.get("task")
        mode_str = args.get("mode", "specialist")
        phase_str = args.get("phase")
        context_categories = args.get("context_categories")

        # V8.3.1-hotfix: Propagate depth to nested calls
        next_depth = current_depth + 1

        # Validate task
        if not task:
            return ToolResult(
                tool_name=self.tool_name,
                status="ERROR",
                output="",
                error="Missing 'task' argument. Provide the subtask to delegate."
            )

        try:
            # Import locally to avoid circular imports
            from core.swarm.collaboration_modes import CollaborationMode
            from core.hive_mind.swarm_bridge import HivePhase

            # Parse mode
            mode = self._parse_mode(mode_str, CollaborationMode)
            if isinstance(mode, ToolResult):
                return mode  # Error result

            # Parse phase (optional)
            phase = self._parse_phase(phase_str, HivePhase)
            if isinstance(phase, ToolResult):
                return phase  # Error result

            # Execute delegation (async -> sync wrapper)
            from core.utils.async_utils import run_sync

            result = run_sync(
                self._swarm_bridge.delegate(
                    task=task,
                    mode=mode,
                    phase=phase,
                    context_categories=context_categories,
                    config={"_swarm_depth": next_depth}
                )
            )

            # FEEDBACK LOOP: Inject results into HiveMind context
            if result.success and hasattr(self._swarm_bridge, 'inject_results_into_context'):
                self._swarm_bridge.inject_results_into_context(result)

            # Build output with metadata
            output_parts = [result.summary] if result.summary else []
            if result.fallback_chain and len(result.fallback_chain) > 1:
                chain_str = " -> ".join(m.value for m in result.fallback_chain)
                output_parts.append(f"[Fallback chain: {chain_str}]")
            output_parts.append(
                f"[Mode: {result.mode_used.value}, Time: {result.execution_time:.2f}s]"
            )

            return ToolResult(
                tool_name=self.tool_name,
                status="SUCCESS" if result.success else "FAILURE",
                output="\n".join(output_parts),
                error="; ".join(result.failure_diagnostics) if not result.success else ""
            )

        except Exception as e:
            self._logger.error(f"swarm_delegate failed: {e}")
            return ToolResult(
                tool_name=self.tool_name,
                status="ERROR",
                output="",
                error=f"Swarm delegation error: {str(e)}"
            )

    def _parse_mode(self, mode_str: str, CollaborationMode: Any) -> Any:
        """Parses the collaboration mode string into a CollaborationMode enum member.

        Args:
            mode_str: The string representation of the collaboration mode.
            CollaborationMode: The enum class containing valid collaboration modes.

        Returns:
            The matching CollaborationMode enum member if found, otherwise a
            ToolResult object containing an error message.

        Raises:
            None: Exceptions (ValueError, AttributeError) are caught and converted
                to error results.
        """
        try:
            return CollaborationMode.from_string(mode_str)
        except (ValueError, AttributeError):
            # Fallback: try direct enum access
            mode_upper = mode_str.upper()
            if hasattr(CollaborationMode, mode_upper):
                return CollaborationMode[mode_upper]
            else:
                valid_modes = [m.value for m in CollaborationMode]
                return ToolResult(
                    tool_name=self.tool_name,
                    status="ERROR",
                    output="",
                    error=f"Invalid mode: '{mode_str}'. Valid modes: {valid_modes}"
                )

    def _parse_phase(self, phase_str: Optional[str], HivePhase: Any) -> Any:
        """Parses the hive phase string into a HivePhase enum member.

        Args:
            phase_str: The string representation of the hive phase.
            HivePhase: The enum class containing valid hive phases.

        Returns:
            The matching HivePhase enum member if found, None if phase_str is
            empty, or a ToolResult object containing an error message if the
            phase is invalid.

        Raises:
            None: ValueError is caught and converted to an error result.
        """
        if not phase_str:
            return None

        try:
            return HivePhase(phase_str.lower())
        except ValueError:
            valid_phases = [p.value for p in HivePhase]
            return ToolResult(
                tool_name=self.tool_name,
                status="ERROR",
                output="",
                error=f"Invalid phase: '{phase_str}'. Valid phases: {valid_phases}"
            )


def create_swarm_handler(
    workspace_path: Path,
    validation_service: Any = None,
    swarm_bridge: Any = None
) -> SwarmDelegateHandler:
    """Factory function to create a SwarmDelegateHandler instance.

    Args:
        workspace_path: The absolute path to the workspace root.
        validation_service: Optional service for validating operations.
        swarm_bridge: Optional SwarmBridge instance (can be set later).

    Returns:
        SwarmDelegateHandler: A configured instance of the handler.

    Raises:
        None: This function does not explicitly raise exceptions.
    """
    return SwarmDelegateHandler(workspace_path, validation_service, swarm_bridge)
