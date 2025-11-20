"""
NEXUS V5.0 - Synapse Package
Protocole de communication et gestion d'état.
"""
from core.synapse.protocol import (
    ThoughtChain,
    StrategicPlanStep,
    ToolUse,
    ToolResult,
    PostActionReview,
    NewCapability,
    SubAgentRequest,
    LightMessage,
    HeavyMessage,
    SynapseMessage
)
from core.synapse.memory import MemoryManager
from core.synapse.state import StateManager

__all__ = [
    "ThoughtChain", "StrategicPlanStep", "ToolUse", "ToolResult",
    "PostActionReview", "NewCapability", "SubAgentRequest",
    "LightMessage", "HeavyMessage", "SynapseMessage",
    "MemoryManager", "StateManager"
]
