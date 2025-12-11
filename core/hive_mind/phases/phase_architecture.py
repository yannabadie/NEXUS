"""
NEXUS V8.0 - Phase 3: Architecture Generation

Generates the agent architecture for task execution:
- Which existing agents to use
- Which new agents to spawn
- Execution plan (sequential/parallel/pipeline)
- RAG configuration

Flow:
1. Check Agent Registry for existing agents
2. Generate architecture based on debate outcome
3. User Breakpoint: BEFORE_SPAWN (if spawning agents)
4. Spawn new agents if approved
5. Return execution-ready architecture

Key Innovation:
- Auto-detects when specialized agents are needed
- Prevents duplicate spawning via Registry
- User can intervene before spawning
"""

import asyncio
import json
import logging
import re
from typing import List, Optional, Dict, Any, TYPE_CHECKING
from dataclasses import dataclass
from pathlib import Path

from ..types import (
    AgentSpec,
    AgentArchitecture,
    RAGConfig,
    ExecutionPlan,
    ExecutionStep,
    DebateResult,
    UserBreakpoint,
    BreakpointOption,
)
from ..cost_estimator import CostEstimator
from ..context_manager import HiveMindContextManager
from ..agent_registry import AgentRegistry
from ..user_interaction import UserInteractionHandler

if TYPE_CHECKING:
    from core.drivers.gemini_driver_v7 import GeminiDriverV7
    from core.drivers.claude_driver_v7 import ClaudeDriverV7

logger = logging.getLogger(__name__)


# Architecture generation prompt
ARCHITECTURE_PROMPT = """You are designing an agent architecture for NEXUS Hive Mind.

TASK: {task}

AGREED APPROACH: {approach}

REQUIRED CAPABILITIES: {capabilities}

AVAILABLE AGENTS:
{available_agents}

Design the optimal architecture. Consider:
1. Can existing agents handle this? (prefer reuse)
2. What specialized agents are needed?
3. How should agents collaborate (parallel, sequential, pipeline)?
4. What RAG context is needed?

Respond in JSON format:
{{
    "agents_to_use": ["agent_id1", "agent_id2", ...],
    "agents_to_spawn": [
        {{
            "role": "specialist_name",
            "mission": "What this agent does",
            "capabilities": ["cap1", "cap2"],
            "tools_priority": ["tool1", "tool2"],
            "estimated_cost": 500
        }}
    ],
    "execution_strategy": "parallel" or "sequential" or "pipeline",
    "execution_steps": [
        {{
            "name": "step_name",
            "agent_id": "agent_to_use",
            "action": "What to do",
            "expected_duration": 30,
            "depends_on": ["previous_step_name"],
            "verification_required": true
        }}
    ],
    "rag_config": {{
        "enabled": true,
        "depth": "shallow" or "standard" or "deep",
        "sources": ["codebase", "docs", "memory"],
        "max_chunks": 10
    }},
    "reasoning": "Why this architecture"
}}
"""


@dataclass
class ArchitecturePhaseResult:
    """Result of Phase 3."""
    architecture: AgentArchitecture
    agents_spawned: List[str]
    user_approved_spawn: bool
    spawn_skipped_reason: Optional[str] = None


class ArchitectureGenerationPhase:
    """
    Phase 3: Architecture Generation

    Generates agent topology and execution plan.
    """

    def __init__(
        self,
        gemini_driver: "GeminiDriverV7",
        claude_driver: "ClaudeDriverV7",
        cost_estimator: CostEstimator,
        context_manager: HiveMindContextManager,
        agent_registry: AgentRegistry,
        user_handler: UserInteractionHandler,
        workspace_path: Path
    ):
        """
        Initialize Phase 3.

        Args:
            gemini_driver: Gemini driver
            claude_driver: Claude driver
            cost_estimator: Cost estimator
            context_manager: Context manager
            agent_registry: Agent registry for spawn tracking
            user_handler: User interaction handler for breakpoints
            workspace_path: Workspace path for agent files
        """
        self.gemini = gemini_driver
        self.claude = claude_driver
        self.cost_estimator = cost_estimator
        self.context_manager = context_manager
        self.registry = agent_registry
        self.user_handler = user_handler
        self.workspace_path = workspace_path

    async def execute(
        self,
        task: str,
        debate_result: DebateResult
    ) -> ArchitecturePhaseResult:
        """
        Execute Phase 3: Architecture Generation.

        Args:
            task: Original task
            debate_result: Result from Phase 2

        Returns:
            ArchitecturePhaseResult with execution-ready architecture
        """
        logger.info("Phase 3: Starting Architecture Generation")

        # Check budget
        if not self.cost_estimator.can_afford_multiple({
            "generate_architecture": 1,
            "check_registry": 1
        }):
            logger.error("Cannot afford Phase 3 operations")
            raise RuntimeError("Budget exceeded for Phase 3")

        # Get available agents from registry
        available_agents = self._format_available_agents()

        # Generate architecture
        architecture = await self._generate_architecture(
            task=task,
            approach=debate_result.final_approach,
            capabilities=debate_result.final_capabilities,
            available_agents=available_agents
        )

        # Check if spawning is needed
        if architecture.agents_to_spawn:
            # Check registry for similar agents
            architecture = self._check_for_duplicates(architecture)

            # If still spawning needed, request user approval
            if architecture.agents_to_spawn:
                user_response = self.user_handler.before_spawn(
                    agents_to_spawn=[
                        {
                            "role": spec.role,
                            "mission": spec.mission,
                            "capabilities": spec.capabilities
                        }
                        for spec in architecture.agents_to_spawn
                    ],
                    estimated_cost=architecture.estimated_cost
                )

                if user_response.chosen_option == "spawn_all":
                    # Spawn all agents
                    spawned = await self._spawn_agents(architecture.agents_to_spawn)
                    return ArchitecturePhaseResult(
                        architecture=architecture,
                        agents_spawned=spawned,
                        user_approved_spawn=True
                    )

                elif user_response.chosen_option == "spawn_selective":
                    # TODO: Implement selective spawning UI
                    spawned = await self._spawn_agents(architecture.agents_to_spawn)
                    return ArchitecturePhaseResult(
                        architecture=architecture,
                        agents_spawned=spawned,
                        user_approved_spawn=True
                    )

                elif user_response.chosen_option == "skip":
                    # Skip spawning, use existing agents
                    architecture.agents_to_spawn = []
                    architecture.status = "READY"
                    return ArchitecturePhaseResult(
                        architecture=architecture,
                        agents_spawned=[],
                        user_approved_spawn=False,
                        spawn_skipped_reason="User chose to skip spawning"
                    )

                else:
                    # Cancel - but continue with existing agents
                    architecture.agents_to_spawn = []
                    return ArchitecturePhaseResult(
                        architecture=architecture,
                        agents_spawned=[],
                        user_approved_spawn=False,
                        spawn_skipped_reason="User cancelled spawning"
                    )

        # No spawning needed
        logger.info("No spawning required - using existing agents")
        return ArchitecturePhaseResult(
            architecture=architecture,
            agents_spawned=[],
            user_approved_spawn=True  # N/A but true for flow
        )

    def _format_available_agents(self) -> str:
        """Format available agents for prompt."""
        agents = self.registry.get_active_agents()
        lines = []
        for agent in agents:
            caps = ", ".join(agent.capabilities)
            lines.append(f"- {agent.agent_id} ({agent.role}): {caps}")
        return "\n".join(lines) if lines else "No specialized agents available"

    async def _generate_architecture(
        self,
        task: str,
        approach: str,
        capabilities: List[str],
        available_agents: str
    ) -> AgentArchitecture:
        """Generate architecture using Gemini."""
        prompt = ARCHITECTURE_PROMPT.format(
            task=task,
            approach=approach,
            capabilities=", ".join(capabilities),
            available_agents=available_agents
        )

        try:
            response = await self.gemini.send_message_async(prompt)

            # Extract content if response is a dict
            if isinstance(response, dict):
                content = response.get("content", response.get("text", str(response)))
            else:
                content = str(response)

            # Record cost
            tokens = len(content) // 4
            self.cost_estimator.record_cost("generate_architecture", tokens)

            # Parse response
            return self._parse_architecture_response(content, capabilities)

        except Exception as e:
            logger.error(f"Architecture generation failed: {e}")
            return self._create_fallback_architecture(capabilities)

    def _parse_architecture_response(
        self,
        response: str,
        capabilities: List[str]
    ) -> AgentArchitecture:
        """Parse architecture JSON from response."""
        json_match = re.search(r'\{[\s\S]*\}', response)
        if not json_match:
            return self._create_fallback_architecture(capabilities)

        try:
            data = json.loads(json_match.group())

            # Parse agents to spawn
            agents_to_spawn = []
            for spec_data in data.get("agents_to_spawn", []):
                agents_to_spawn.append(AgentSpec(
                    role=spec_data.get("role", "specialist"),
                    mission=spec_data.get("mission", ""),
                    capabilities=spec_data.get("capabilities", []),
                    tools_priority=spec_data.get("tools_priority", []),
                    estimated_cost=spec_data.get("estimated_cost", 500)
                ))

            # Parse execution steps
            steps = []
            for step_data in data.get("execution_steps", []):
                steps.append(ExecutionStep(
                    name=step_data.get("name", "step"),
                    agent_id=step_data.get("agent_id", "claude"),
                    action=step_data.get("action", ""),
                    expected_duration=step_data.get("expected_duration", 30),
                    depends_on=step_data.get("depends_on", []),
                    verification_required=step_data.get("verification_required", False)
                ))

            # Parse RAG config
            rag_data = data.get("rag_config", {})
            rag_config = RAGConfig(
                enabled=rag_data.get("enabled", True),
                depth=rag_data.get("depth", "standard"),
                sources=rag_data.get("sources", ["codebase"]),
                max_chunks=rag_data.get("max_chunks", 10)
            )

            # Calculate estimated cost
            total_cost = sum(spec.estimated_cost for spec in agents_to_spawn)
            total_cost += len(steps) * 500  # Estimate per step

            # Determine status
            status = "SPAWN_REQUIRED" if agents_to_spawn else "READY"

            return AgentArchitecture(
                status=status,
                collaboration_mode=data.get("execution_strategy", "sequential"),
                agents_to_use=data.get("agents_to_use", ["claude", "gemini"]),
                agents_to_spawn=agents_to_spawn,
                rag_config=rag_config,
                execution_plan=ExecutionPlan(
                    strategy=data.get("execution_strategy", "sequential"),
                    steps=steps,
                    estimated_total_duration=sum(s.expected_duration for s in steps),
                    estimated_total_tokens=total_cost
                ),
                estimated_cost=total_cost,
                reasoning=data.get("reasoning", "")
            )

        except json.JSONDecodeError as e:
            logger.warning(f"JSON parse error: {e}")
            return self._create_fallback_architecture(capabilities)

    def _create_fallback_architecture(self, capabilities: List[str]) -> AgentArchitecture:
        """Create fallback architecture when generation fails."""
        return AgentArchitecture(
            status="READY",
            collaboration_mode="sequential",
            agents_to_use=["claude", "gemini"],
            agents_to_spawn=[],
            rag_config=RAGConfig(),
            execution_plan=ExecutionPlan(
                strategy="sequential",
                steps=[
                    ExecutionStep(
                        name="main_execution",
                        agent_id="claude",
                        action="Execute task with available capabilities",
                        expected_duration=60
                    )
                ],
                estimated_total_duration=60,
                estimated_total_tokens=1000
            ),
            estimated_cost=1000,
            reasoning="Fallback architecture due to generation failure"
        )

    def _check_for_duplicates(self, architecture: AgentArchitecture) -> AgentArchitecture:
        """Check for duplicate agents and remove them."""
        self.cost_estimator.record_cost("check_registry", 100)

        remaining_spawns = []
        for spec in architecture.agents_to_spawn:
            # Check if similar agent exists
            similar = self.registry.find_similar(spec.capabilities)

            if similar:
                logger.info(
                    f"Found similar agent '{similar.agent_id}' for '{spec.role}' - "
                    f"skipping spawn"
                )
                # Add existing agent to use list
                if similar.agent_id not in architecture.agents_to_use:
                    architecture.agents_to_use.append(similar.agent_id)
            else:
                remaining_spawns.append(spec)

        architecture.agents_to_spawn = remaining_spawns

        if not remaining_spawns:
            architecture.status = "READY"
        else:
            architecture.status = "SPAWN_SUGGESTED"

        return architecture

    async def _spawn_agents(self, specs: List[AgentSpec]) -> List[str]:
        """Spawn new agents from specifications."""
        spawned = []

        for spec in specs:
            try:
                # Generate unique ID
                import hashlib
                agent_id = f"{spec.role}_{hashlib.md5(spec.mission.encode()).hexdigest()[:6]}"

                # Create agent file in workspace
                agent_path = self.workspace_path / "agents" / f"{agent_id}.json"
                agent_path.parent.mkdir(parents=True, exist_ok=True)

                agent_config = {
                    "id": agent_id,
                    "role": spec.role,
                    "mission": spec.mission,
                    "capabilities": spec.capabilities,
                    "tools_priority": spec.tools_priority,
                    "created_by": "hive_mind_v8",
                    "created_at": str(asyncio.get_event_loop().time())
                }

                agent_path.write_text(
                    json.dumps(agent_config, indent=2),
                    encoding='utf-8'
                )

                # Register in registry
                self.registry.register_spawn(
                    agent_id=agent_id,
                    role=spec.role,
                    capabilities=spec.capabilities,
                    mission=spec.mission
                )

                # Record cost
                self.cost_estimator.record_cost("spawn_agent", spec.estimated_cost)

                spawned.append(agent_id)
                logger.info(f"Spawned agent: {agent_id}")

            except Exception as e:
                logger.error(f"Failed to spawn {spec.role}: {e}")

        return spawned

    def get_execution_ready_architecture(
        self,
        result: ArchitecturePhaseResult
    ) -> Dict[str, Any]:
        """
        Get architecture in format ready for Phase 4 execution.

        Args:
            result: Phase 3 result

        Returns:
            Execution-ready configuration
        """
        arch = result.architecture

        return {
            "mode": arch.collaboration_mode,
            "agents": arch.agents_to_use + result.agents_spawned,
            "steps": [
                {
                    "name": step.name,
                    "agent": step.agent_id,
                    "action": step.action,
                    "timeout": step.expected_duration,
                    "depends_on": step.depends_on,
                    "verify": step.verification_required
                }
                for step in arch.execution_plan.steps
            ],
            "rag": {
                "enabled": arch.rag_config.enabled,
                "depth": arch.rag_config.depth,
                "sources": arch.rag_config.sources,
                "max_chunks": arch.rag_config.max_chunks
            },
            "estimated_tokens": arch.estimated_cost,
            "estimated_duration": arch.execution_plan.estimated_total_duration
        }
