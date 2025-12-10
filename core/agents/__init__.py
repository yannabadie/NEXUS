"""
NEXUS V8.4.0 - Agents Module

Centralized agent management and registry.
"""

from .unified_registry import (
    UnifiedAgentRegistry,
    AgentDescriptor,
    AgentProvider,
    AgentCapability,
    DriverProtocol,
    get_registry,
)

__all__ = [
    "UnifiedAgentRegistry",
    "AgentDescriptor",
    "AgentProvider",
    "AgentCapability",
    "DriverProtocol",
    "get_registry",
]
