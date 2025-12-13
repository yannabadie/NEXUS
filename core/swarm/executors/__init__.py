"""
Swarm Mode Executors - V9.6 Complete Extraction

Decomposed from mode_executors.py (1187 LOC) for Single Responsibility.

Each executor implements one collaboration mode:
- ParallelExecutor: Simultaneous work with result merging
- SequentialExecutor: Ordered execution (first → second)
- LeadSupportExecutor: Lead drives, support reviews
- PingPongExecutor: Rapid alternation until convergence
- SpecialistExecutor: Single expert handles all
- RedBlueExecutor: Adversarial propose/attack/defend
"""

from .base import (
    ExecutionStatus,
    AgentResponse,
    ExecutionContext,
    ExecutionResult,
    ModeExecutor,
    ExecutionError,
    COMPLETION_PATTERN,
    _blackboard_lock,
)

# V9.6: Import all extracted executors
from .parallel_executor import ParallelExecutor
from .sequential_executor import SequentialExecutor
from .specialist_executor import SpecialistExecutor
from .lead_support_executor import LeadSupportExecutor
from .ping_pong_executor import PingPongExecutor
from .red_blue_executor import RedBlueExecutor

# V9.6: Import registry
from .registry import get_executor, get_executor_registry

__all__ = [
    # Base classes
    "ExecutionStatus",
    "AgentResponse",
    "ExecutionContext",
    "ExecutionResult",
    "ModeExecutor",
    "ExecutionError",
    "COMPLETION_PATTERN",
    "_blackboard_lock",
    # Executors
    "ParallelExecutor",
    "SequentialExecutor",
    "SpecialistExecutor",
    "LeadSupportExecutor",
    "PingPongExecutor",
    "RedBlueExecutor",
    # Registry
    "get_executor",
    "get_executor_registry",
]

__version__ = "9.6.0"
