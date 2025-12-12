"""
NEXUS V9.1 - Agents Module

Centralized agent management, registry, and services.
"""

from .unified_registry import (
    UnifiedAgentRegistry,
    AgentDescriptor,
    AgentProvider,
    AgentCapability,
    DriverProtocol,
    get_registry,
)

from .service import (
    AgentService,
    SpawnResult,
    AgentInfo,
    PoolStats,
)

__all__ = [
    # Registry
    "UnifiedAgentRegistry",
    "AgentDescriptor",
    "AgentProvider",
    "AgentCapability",
    "DriverProtocol",
    "get_registry",
    # Service (V9.1)
    "AgentService",
    "SpawnResult",
    "AgentInfo",
    "PoolStats",
]
