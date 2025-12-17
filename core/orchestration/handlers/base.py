"""
NEXUS V10.2 - FSM Handlers Base Module

Contains shared imports, helpers, and the base mixin class that all
handler mixins inherit from.

Extracted from fsm_handlers.py during monolithic file split.
"""

import sys
import time
import logging
import asyncio
from typing import TYPE_CHECKING, Dict, Optional

from core.agents.unified_registry import get_registry
from core.fsm.states import OrchestratorState
from core.routing.model_router import TaskType
from core.synapse.protocol_v7 import ToolUse
from core.swarm import TaskComplexity
from core.governance.sandbox_policy import SandboxPolicy

# V8.0 TRUE HIVE MIND
try:
    from core.hive_mind import TrueHiveMind, TaskComplexity as HiveComplexity
    HIVE_MIND_AVAILABLE = True
except ImportError:
    HIVE_MIND_AVAILABLE = False
    TrueHiveMind = None
    HiveComplexity = None

if TYPE_CHECKING:
    from core.orchestration_v7 import OrchestratorV7

logger = logging.getLogger("nexus.fsm_handlers")


class FSMHandlersMixin:
    """
    Base mixin for FSM handlers.
    
    Provides common attributes and helper methods used by all handler mixins.
    Must be mixed with a class that has self._orch attribute.
    """
    _orch: "OrchestratorV7"
    _logger: logging.Logger
    _registry: any
    _telemetry: any
    _event_bus: any
    _asyncio: any
    
    def _emit(self, event_type: str, data: Dict):
        """Helper to emit events from sync context using fire-and-forget."""
        if self._event_bus:
            try:
                self._event_bus.publish_sync(event_type, data)
            except Exception:
                pass
    
    def _make_result(self, state: str, output, agent, finished: bool, **kwargs) -> Dict:
        """Delegate to orchestrator."""
        return self._orch._make_result(state, output, agent, finished, **kwargs)
    
    def _build_context(self) -> str:
        """Build context - delegate to context_builder or orchestrator."""
        if hasattr(self._orch, '_context_builder') and self._orch._context_builder:
            return self._orch._context_builder.build_context()
        return self._orch._build_context()
    
    def _build_context_with_tool_result(self) -> str:
        """Build CFL context - delegate to context_builder or orchestrator."""
        if hasattr(self._orch, '_context_builder') and self._orch._context_builder:
            return self._orch._context_builder.build_context_with_tool_result()
        return self._orch._build_context_with_tool_result()
    
    def _invoke_agent(self, task_type: TaskType, context: str) -> Dict:
        """Invoke agent - delegate to agent_invoker or orchestrator."""
        if hasattr(self._orch, '_agent_invoker') and self._orch._agent_invoker:
            return self._orch._agent_invoker.invoke_agent(task_type, context)
        return self._orch._invoke_agent(task_type, context)
    
    def _get_claude_driver(self, task_type: TaskType, timeout_override: int = None):
        """Get Claude driver - delegate to agent_invoker or orchestrator."""
        if hasattr(self._orch, '_agent_invoker') and self._orch._agent_invoker:
            return self._orch._agent_invoker.get_claude_driver(task_type, timeout_override)
        return self._orch._get_claude_driver(task_type, timeout_override)
    
    def _validate_message(self, response: Dict, expect_heavy: bool = False) -> bool:
        """Validate message - delegate to orchestrator."""
        return self._orch._validate_message(response, expect_heavy)
    
    def _calculate_quality_score(self, message: dict, validation_ok: bool, is_stagnant: bool) -> float:
        """Calculate quality - delegate to agent_invoker or orchestrator."""
        if hasattr(self._orch, '_agent_invoker') and self._orch._agent_invoker:
            return self._orch._agent_invoker.calculate_quality_score(message, validation_ok, is_stagnant)
        return self._orch._calculate_quality_score(message, validation_ok, is_stagnant)
    
    def _record_invocation(self, agent_name: str, task_type: str, success: bool, duration: float, quality: float):
        """Record invocation - delegate to agent_invoker or orchestrator."""
        if hasattr(self._orch, '_agent_invoker') and self._orch._agent_invoker:
            return self._orch._agent_invoker.record_invocation(agent_name, task_type, success, duration, quality)
        return self._orch._record_invocation(agent_name, task_type, success, duration, quality)
    
    def _detect_mutation_complete(self, content: str) -> bool:
        """Detect mutation - delegate to detectors or orchestrator."""
        if hasattr(self._orch, '_detectors') and self._orch._detectors:
            return self._orch._detectors.detect_mutation_complete(content)
        return self._orch._detect_mutation_complete(content)
