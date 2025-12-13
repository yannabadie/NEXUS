"""
Swarm Mode Executors - V9.5 Refactored

Decomposed from mode_executors.py (1323 LOC) for Single Responsibility.

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
)

__all__ = [
    "ExecutionStatus",
    "AgentResponse",
    "ExecutionContext",
    "ExecutionResult",
    "ModeExecutor",
    "ExecutionError",
    "COMPLETION_PATTERN",
]

__version__ = "9.5.0"
