"""
NEXUS V10.2 - Mode Executors Package

Split from monolithic mode_executors.py for better maintainability.

Usage:
    from core.swarm.executors import (
        ParallelExecutor,
        SequentialExecutor, 
        LeadSupportExecutor,
        PingPongExecutor,
        SpecialistExecutor,
        RedBlueExecutor
    )
"""

from core.swarm.mode_executors import (
    ParallelExecutor,
    SequentialExecutor,
    LeadSupportExecutor,
    PingPongExecutor,
    SpecialistExecutor,
    RedBlueExecutor,
    ModeExecutor,
    ExecutionContext,
    ExecutionResult,
    ExecutionStatus,
    AgentResponse
)

__all__ = [
    "ParallelExecutor",
    "SequentialExecutor",
    "LeadSupportExecutor",
    "PingPongExecutor",
    "SpecialistExecutor",
    "RedBlueExecutor",
    "ModeExecutor",
    "ExecutionContext",
    "ExecutionResult",
    "ExecutionStatus",
    "AgentResponse"
]
