"""
Spawned Agent Loader - NEXUS V12.4 REFAC
Discovers and loads spawned agents from workspace/agents/ at startup.
Supports both V7 AgentPool (Legacy) and V12 UnifiedAgentRegistry (Modern).

Usage:
    from core.bootstrap.agent_loader import SpawnedAgentLoader

    loader = SpawnedAgentLoader(workspace_path)
    descriptors = loader.discover_spawned_agents()

    # Polyglot Registration
    loader.register_agents(agent_pool)       # Adapt to AgentProfile
    loader.register_agents(agent_registry)   # Use AgentDescriptor
"""

import json
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any, Union

from dataclasses import dataclass

# V7 Legacy Metrics
from core.swarm.agent_metrics import AgentProfile

# V12.4 Unified Registry
from core.agents.unified_registry import (
    AgentDescriptor,
    AgentProvider,
    AgentCapability,
    UnifiedAgentRegistry
)

logger = logging.getLogger(__name__)


@dataclass
class InferenceConfig:
    """V8.1.8-B: Model inference configuration for spawned agent."""
    provider: str  # "gemini" or "claude"
    model: str     # e.g., "gemini-2.5-flash", "claude-sonnet-4-5-20250929"
    reasoning: Optional[str] = None


@dataclass
class SpawnedAgentConfig:
    """Configuration loaded from BIRTH_CERTIFICATE.json"""
    agent_id: str
    role: str
    created_at: str
    parent: str
    mission: str
    domains: List[str]
    tools_priority: List[str]
    workspace_path: Path
    system_prompt_path: Optional[Path] = None
    uuid: Optional[str] = None
    inference: Optional[InferenceConfig] = None


class SpawnedAgentLoader:
    """
    Discovers and loads spawned agents from workspace/agents/.
    """

    def __init__(self, workspace_path: Path):
        self.workspace_path = Path(workspace_path)
        self.agents_dir = self.workspace_path / "agents"

    def discover_spawned_agents(self) -> List[AgentDescriptor]:
        """
        Scan workspace/agents/ and create AgentDescriptors.
        
        Returns:
            List of V12.4 AgentDescriptor objects.
        """
        agents = []

        if not self.agents_dir.exists():
            logger.debug(f"No agents directory at {self.agents_dir}")
            return agents

        for agent_dir in self.agents_dir.iterdir():
            if not agent_dir.is_dir():
                continue

            try:
                descriptor = self._load_agent_from_dir(agent_dir)
                if descriptor:
                    agents.append(descriptor)
                    logger.info(f"Discovered spawned agent: {descriptor.id}")
            except Exception as e:
                logger.warning(f"Failed to load agent from {agent_dir}: {e}")

        logger.info(f"Discovered {len(agents)} spawned agents")
        return agents

    def _load_agent_from_dir(self, agent_dir: Path) -> Optional[AgentDescriptor]:
        """Load a single agent descriptor from directory."""
        cert_file = agent_dir / "BIRTH_CERTIFICATE.json"

        if not cert_file.exists():
            return None

        try:
            cert_data = json.loads(cert_file.read_text(encoding='utf-8'))
        except json.JSONDecodeError as e:
            logger.warning(f"Invalid JSON in {cert_file}: {e}")
            return None

        config = self._parse_birth_certificate(cert_data, agent_dir)
        if not config:
            return None

        # Map capabilities string -> Enum
        capabilities = self._map_capabilities(config.domains)

        # Create AgentDescriptor (V12.4)
        return AgentDescriptor(
            id=config.agent_id,
            provider=AgentProvider.SPAWNED,
            display_name=config.role,
            capabilities=capabilities,
            config_path=cert_file,
            is_available=True
        )

    def _map_capabilities(self, domains: List[str]) -> List[AgentCapability]:
        """Map string domains to AgentCapability Enum."""
        caps = []
        for d in domains:
            d_lower = d.lower()
            if "coding" in d_lower or "dev" in d_lower:
                caps.append(AgentCapability.CODING)
            elif "research" in d_lower or "search" in d_lower:
                caps.append(AgentCapability.RESEARCH)
            elif "analy" in d_lower or "data" in d_lower:
                caps.append(AgentCapability.ANALYSIS)
            elif "creative" in d_lower:
                caps.append(AgentCapability.CREATIVE)
            else:
                caps.append(AgentCapability.GENERAL)
        # Ensure at least GENERAL
        if not caps:
            caps.append(AgentCapability.GENERAL)
        return list(set(caps))

    def _parse_birth_certificate(
        self,
        cert_data: Dict[str, Any],
        agent_dir: Path
    ) -> Optional[SpawnedAgentConfig]:
        """Parse BIRTH_CERTIFICATE.json into SpawnedAgentConfig."""
        if "birth_certificate" in cert_data:
            cert_data = cert_data["birth_certificate"]

        agent_id = cert_data.get("agent_id")
        if not agent_id:
            return None

        specialization = cert_data.get("specialization", {})
        
        system_prompt_path = agent_dir / "system_prompt.md"
        if not system_prompt_path.exists():
            system_prompt_path = None

        inference_data = cert_data.get("inference")
        inference_config = None
        if inference_data and isinstance(inference_data, dict):
            inference_config = InferenceConfig(
                provider=inference_data.get("provider", "claude"),
                model=inference_data.get("model", "claude-sonnet-4-5-20250929"),
                reasoning=inference_data.get("reasoning")
            )

        return SpawnedAgentConfig(
            agent_id=agent_id,
            role=cert_data.get("role", agent_id),
            created_at=cert_data.get("created_at", ""),
            parent=cert_data.get("parent", "NEXUS"),
            mission=specialization.get("mission", f"Specialized agent: {agent_id}"),
            domains=specialization.get("domains", []),
            tools_priority=specialization.get("tools_priority", []),
            workspace_path=agent_dir,
            system_prompt_path=system_prompt_path,
            uuid=cert_data.get("uuid"),
            inference=inference_config,
        )
    
    def load_system_prompt(self, agent_id: str) -> Optional[str]:
        """Legacy helper: Load system prompt by ID."""
        prompt_file = self.agents_dir / agent_id / "system_prompt.md"
        if prompt_file.exists():
            return prompt_file.read_text(encoding='utf-8')
        return None

    def register_agents(self, registry_or_pool: Any) -> int:
        """
        Polyglot registration: Handles both UnifiedAgentRegistry and AgentPool.
        """
        descriptors = self.discover_spawned_agents()
        count = 0

        # Case 1: V12 UnifiedAgentRegistry
        if isinstance(registry_or_pool, UnifiedAgentRegistry) or hasattr(registry_or_pool, 'is_gemini'):
            for desc in descriptors:
                registry_or_pool.register(desc)
                count += 1
            return count

        # Case 2: V7 AgentPool (Legacy Bridge)
        # Check for 'get_active_agents' which applies to AgentPool
        if hasattr(registry_or_pool, 'get_active_agents'):
            for desc in descriptors:
                # Convert Descriptor -> Profile
                profile = AgentProfile(
                    agent_id=desc.id,
                    provider="spawned",  # String literal for legacy
                    model=f"spawned_{desc.id}",
                    capabilities=[c.value for c in desc.capabilities],
                    is_active=desc.is_available,
                    uuid=None  # Can be fetched from birth cert re-read if needed, or added to Descriptor
                )
                registry_or_pool.register(profile)
                count += 1
            return count
        
        logger.warning(f"Unknown registry type: {type(registry_or_pool)}")
        return 0


def discover_and_register_spawned_agents(
    workspace_path: Path,
    agent_pool: Any  # Can be AgentPool or UnifiedAgentRegistry
) -> int:
    """
    Convenience function to discover and register all spawned agents.
    Now supports both legacy AgentPool and UnifiedAgentRegistry.
    """
    loader = SpawnedAgentLoader(workspace_path)
    return loader.register_agents(agent_pool)
