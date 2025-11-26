"""
NEXUS V7 Swarm Module - Agent Metrics and Pool Management

Foundation for Phase 6 Hybrid Swarm architecture.
Provides DyLAN-inspired importance scoring for agent selection.

Classes:
- AgentInvocationResult: Single invocation metrics
- AgentProfile: Per-agent performance tracking
- AgentPool: Multi-agent management (scales 2 → N)
"""

from .agent_metrics import (
    AgentInvocationResult,
    AgentProfile,
    AgentPool,
    create_default_pool
)

__all__ = [
    "AgentInvocationResult",
    "AgentProfile",
    "AgentPool",
    "create_default_pool"
]
