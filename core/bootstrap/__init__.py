"""
NEXUS V7.5 - Bootstrap Module

Components:
- AutoBootstrap: Generates NEXUS.md when deployed to a new project
- SpawnedAgentLoader: Discovers spawned agents from workspace/agents/
"""

from .auto_bootstrap import AutoBootstrap, ProjectAnalysis
from .agent_loader import (
    SpawnedAgentLoader,
    SpawnedAgentConfig,
    discover_and_register_spawned_agents
)

__all__ = [
    'AutoBootstrap',
    'ProjectAnalysis',
    'SpawnedAgentLoader',
    'SpawnedAgentConfig',
    'discover_and_register_spawned_agents'
]
