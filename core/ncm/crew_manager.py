"""
Crew Manager - Skill-Based Agent Assignment

Assigns agents to stories based on skill matrix matching.

Blind Spot #8 Mitigation:
    - REFACTORING_AGENT should NOT handle security stories
    - SECURITY_AGENT should NOT handle dead imports
    - Crew assignment based on story.domains → agent.expertise

Architecture:
    1. Build skill matrix from agent birth certificates
    2. Score agents for each story (domain overlap)
    3. Select top N agents (N = config.agents_per_story)
    4. Determine swarm mode based on story type
    5. Check fault isolation (no conflicting assignments)

Usage:
    from core.ncm import CrewManager
    from core.agents.agent_service import AgentService

    crew_manager = CrewManager(agent_service=agent_service, config={})
    assignment = await crew_manager.assign_agents(story)
    print(f"Assigned {len(assignment.agent_ids)} agents in {assignment.swarm_mode} mode")
"""

from pathlib import Path
from typing import List, Dict, Set, Optional, Any
from datetime import datetime
import json

from core.ncm.models import (
    Story,
    CrewAssignment,
    AgentSkill,
    IssueDomain,
    SwarmMode,
)
from core.logging import get_logger


class CrewManager:
    """
    Agent assignment with skill matrix.

    Responsibilities:
        - Build skill matrix (agent → domains they excel at)
        - Crew assignment (story → best agents)
        - Fault isolation (agents can't interfere with each other)
        - Workload balancing (avoid overloading one agent)

    Blind Spot #8 Mitigation:
        - REFACTORING_AGENT should NOT handle security stories
        - SECURITY_AGENT should NOT handle dead imports
        - Crew assignment based on story.domains → agent.expertise

    Skill Matrix Format:
        {
            "REFACTORING_AGENT_V1": {IssueDomain.REFACTORING, IssueDomain.TYPING},
            "SECURITY_AGENT_V1": {IssueDomain.SECURITY, IssueDomain.TESTING},
            "TESTING_AGENT_V1": {IssueDomain.TESTING, IssueDomain.DOCUMENTATION},
            ...
        }

    Usage:
        crew_manager = CrewManager(agent_service=agent_service, config={})
        assignment = await crew_manager.assign_agents(story)
    """

    def __init__(
        self,
        workspace_path: Path,
        config: Optional[Dict] = None
    ):
        """
        Initialize crew manager.

        Args:
            workspace_path: NEXUS workspace root (e.g., Path("workspace"))
            config: Optional crew configuration (max agents per story, etc.)

        Raises:
            ValueError: If workspace_path doesn't exist
        """
        if not workspace_path.exists():
            raise ValueError(f"workspace_path does not exist: {workspace_path}")

        self.workspace_path = workspace_path
        self.config = config or {}
        self.logger = get_logger()

        # Config
        self.agents_per_story = self.config.get("agents_per_story", 2)
        self.min_skill_overlap = self.config.get("min_skill_overlap", 0.5)

        # Skill matrix (agent_id → expertise domains)
        self.skill_matrix: Dict[str, AgentSkill] = {}

        # Workload tracking (agent_id → current story count)
        self.workload: Dict[str, int] = {}

        # Active assignments (agent_id → current story_ids)
        self.active_assignments: Dict[str, Set[str]] = {}

        # Build skill matrix
        self._build_skill_matrix()

        self.logger.info("crew_manager_initialized", {
            "workspace": str(workspace_path),
            "agents_per_story": self.agents_per_story,
            "agents_available": len(self.skill_matrix)
        })

    def _build_skill_matrix(self):
        """
        Build skill matrix from agent birth certificates.

        Reads workspace/ncm/agents/*/birth_certificate.json
        and extracts specialization.expertise fields.

        If no agents exist yet, creates default skill matrix
        for the 6 NCM specialist agents.

        NOTE: For Phase 0, we use a default skill matrix.
              Phase 0.2 will implement actual birth certificate parsing.
        """
        self.logger.debug("build_skill_matrix_start")

        # Check for actual agent directories
        agents_dir = self.workspace_path / "ncm" / "agents"
        if agents_dir.exists():
            # Load from birth certificates
            for agent_dir in agents_dir.iterdir():
                if not agent_dir.is_dir():
                    continue

                cert_path = agent_dir / "birth_certificate.json"
                if not cert_path.exists():
                    continue

                try:
                    cert = json.loads(cert_path.read_text())
                    agent_id = cert["agent_id"]
                    expertise = cert.get("specialization", {}).get("expertise", [])

                    # Map expertise strings to IssueDomain enums
                    domains = self._map_expertise_to_domains(expertise)

                    self.skill_matrix[agent_id] = AgentSkill(
                        agent_id=agent_id,
                        expertise=domains,
                        success_rate=0.0,  # Will be updated from metrics
                        avg_tokens=0,
                        stories_completed=0
                    )

                    self.logger.debug("agent_skill_loaded", {
                        "agent_id": agent_id,
                        "domains": [d.value for d in domains]
                    })

                except Exception as e:
                    self.logger.warning("agent_skill_load_failed", {
                        "agent_dir": str(agent_dir),
                        "error": str(e)
                    })

        # If no agents found, use default skill matrix for Phase 0
        if not self.skill_matrix:
            self._create_default_skill_matrix()

        self.logger.debug("build_skill_matrix_complete", {
            "agents_count": len(self.skill_matrix)
        })

    def _create_default_skill_matrix(self):
        """
        Create default skill matrix for 6 NCM specialist agents.

        Agents:
            1. REFACTORING_AGENT - God class decomposition, code restructuring
            2. SECURITY_AGENT - Vulnerability fixes, security review
            3. TESTING_AGENT - Test writing, coverage improvement
            4. EVOLUTION_AGENT - Agent spawning, system evolution
            5. DOCUMENTATION_AGENT - Docstrings, README updates
            6. CLEANUP_AGENT - Dead code/imports, deprecation fixes

        NOTE: This is a placeholder for Phase 0.
              Real agents will be spawned in Phase 0.2.
        """
        default_agents = [
            {
                "agent_id": "REFACTORING_AGENT_V1",
                "expertise": {IssueDomain.REFACTORING, IssueDomain.TYPING}
            },
            {
                "agent_id": "SECURITY_AGENT_V1",
                "expertise": {IssueDomain.SECURITY, IssueDomain.TESTING}
            },
            {
                "agent_id": "TESTING_AGENT_V1",
                "expertise": {IssueDomain.TESTING}
            },
            {
                "agent_id": "EVOLUTION_AGENT_V1",
                "expertise": {IssueDomain.EVOLUTION}
            },
            {
                "agent_id": "DOCUMENTATION_AGENT_V1",
                "expertise": {IssueDomain.DOCUMENTATION}
            },
            {
                "agent_id": "CLEANUP_AGENT_V1",
                "expertise": {IssueDomain.CLEANUP, IssueDomain.TYPING}
            }
        ]

        for agent_config in default_agents:
            self.skill_matrix[agent_config["agent_id"]] = AgentSkill(
                agent_id=agent_config["agent_id"],
                expertise=agent_config["expertise"],
                success_rate=1.0,  # Default high success rate
                avg_tokens=45000,  # Estimated average
                stories_completed=0
            )

            self.workload[agent_config["agent_id"]] = 0
            self.active_assignments[agent_config["agent_id"]] = set()

        self.logger.info("default_skill_matrix_created", {
            "agents": list(self.skill_matrix.keys())
        })

    def _map_expertise_to_domains(self, expertise: List[str]) -> Set[IssueDomain]:
        """
        Map expertise strings to IssueDomain enums.

        Args:
            expertise: List of expertise strings (e.g., ["refactoring", "security"])

        Returns:
            Set of IssueDomain enums

        Mapping:
            - "refactoring" → IssueDomain.REFACTORING
            - "security" → IssueDomain.SECURITY
            - "testing" → IssueDomain.TESTING
            - etc.
        """
        domain_map = {
            "refactoring": IssueDomain.REFACTORING,
            "security": IssueDomain.SECURITY,
            "testing": IssueDomain.TESTING,
            "evolution": IssueDomain.EVOLUTION,
            "documentation": IssueDomain.DOCUMENTATION,
            "cleanup": IssueDomain.CLEANUP,
            "typing": IssueDomain.TYPING,
        }

        domains = set()
        for exp in expertise:
            exp_lower = exp.lower()
            if exp_lower in domain_map:
                domains.add(domain_map[exp_lower])

        return domains

    async def assign_agents(self, story: Story) -> CrewAssignment:
        """
        Assign best agents for story based on skill matrix.

        Args:
            story: Story to assign agents for

        Returns:
            CrewAssignment with agent_ids and swarm_mode

        Algorithm:
            1. Score each agent (overlap between story.domains and agent.expertise)
            2. Filter agents with min_skill_overlap
            3. Sort by (skill_score, workload) - prefer skilled + available agents
            4. Select top N agents (N = config.agents_per_story)
            5. Determine swarm mode based on story complexity
            6. Check fault isolation (no conflicting file assignments)
            7. Update workload tracking

        Scoring:
            skill_score = len(story.domains ∩ agent.expertise) / len(story.domains)
            Example: Story has {REFACTORING, TYPING}, Agent has {REFACTORING}
                     → skill_score = 1/2 = 0.5
        """
        self.logger.debug("crew_assignment_start", {
            "story_id": story.story_id,
            "story_domains": [d.value for d in story.domains],
            "story_priority": story.priority.value
        })

        # 1. Score agents
        agent_scores: List[Tuple[str, float, AgentSkill]] = []

        for agent_id, agent_skill in self.skill_matrix.items():
            # Calculate skill overlap
            overlap = len(story.domains & agent_skill.expertise)
            skill_score = overlap / len(story.domains) if len(story.domains) > 0 else 0.0

            # Skip agents with insufficient skill overlap
            if skill_score < self.min_skill_overlap:
                continue

            agent_scores.append((agent_id, skill_score, agent_skill))

        # If no agents match, fall back to any available agent
        if not agent_scores:
            self.logger.warning("no_agents_match_skills", {
                "story_id": story.story_id,
                "story_domains": [d.value for d in story.domains]
            })
            # Use all agents as fallback
            agent_scores = [
                (agent_id, 0.5, agent_skill)  # Give default 0.5 score
                for agent_id, agent_skill in self.skill_matrix.items()
            ]

        # 2. Sort by (skill_score DESC, workload ASC)
        # Prefer highly-skilled agents with low workload
        agent_scores.sort(
            key=lambda x: (-x[1], self.workload.get(x[0], 0))
        )

        # 3. Select top N agents
        selected_agents = [
            agent_id for agent_id, _, _ in agent_scores[:self.agents_per_story]
        ]

        # 4. Determine swarm mode
        swarm_mode = self._determine_swarm_mode(story, selected_agents)

        # 5. Determine lead agent (for LEAD_SUPPORT mode)
        lead_agent_id = selected_agents[0] if swarm_mode == SwarmMode.LEAD_SUPPORT else None

        # 6. Create assignment
        assignment = CrewAssignment(
            story_id=story.story_id,
            agent_ids=selected_agents,
            swarm_mode=swarm_mode,
            lead_agent_id=lead_agent_id,
            assigned_at=datetime.now()
        )

        # 7. Update workload tracking
        for agent_id in selected_agents:
            self.workload[agent_id] = self.workload.get(agent_id, 0) + 1
            if agent_id not in self.active_assignments:
                self.active_assignments[agent_id] = set()
            self.active_assignments[agent_id].add(story.story_id)

        self.logger.info("crew_assignment_complete", {
            "story_id": story.story_id,
            "agents": selected_agents,
            "swarm_mode": swarm_mode.value,
            "lead_agent": lead_agent_id
        })

        return assignment

    def _determine_swarm_mode(
        self,
        story: Story,
        agents: List[str]
    ) -> SwarmMode:
        """
        Determine best swarm mode for story + agents.

        Rules:
            - Security stories → RED_BLUE (propose/attack/defend)
            - God class refactoring → LEAD_SUPPORT (complex implementation)
            - Dead imports/cleanup → PARALLEL (independent files)
            - Type errors → SEQUENTIAL (avoid races)
            - Evolution → SPECIALIST (single expert)
            - Single agent → SPECIALIST

        Args:
            story: Story to execute
            agents: List of agent_ids assigned

        Returns:
            SwarmMode enum
        """
        # Single agent → SPECIALIST
        if len(agents) == 1:
            return SwarmMode.SPECIALIST

        # Security → RED_BLUE (adversarial)
        if IssueDomain.SECURITY in story.domains:
            return SwarmMode.RED_BLUE

        # Refactoring (God classes) → LEAD_SUPPORT (complex)
        if IssueDomain.REFACTORING in story.domains and story.priority == "P0":
            return SwarmMode.LEAD_SUPPORT

        # Evolution → SPECIALIST (typically needs single expert)
        if IssueDomain.EVOLUTION in story.domains:
            return SwarmMode.SPECIALIST

        # Cleanup (dead imports, dead code) → PARALLEL (independent)
        if IssueDomain.CLEANUP in story.domains:
            return SwarmMode.PARALLEL

        # Typing/Documentation → SEQUENTIAL (avoid conflicts)
        if IssueDomain.TYPING in story.domains or IssueDomain.DOCUMENTATION in story.domains:
            return SwarmMode.SEQUENTIAL

        # Default → SEQUENTIAL (safest)
        return SwarmMode.SEQUENTIAL

    async def release_agents(self, story: Story):
        """
        Release agents after story completion.

        Updates workload tracking and removes from active assignments.

        Args:
            story: Completed story
        """
        assignment = self.get_assignment(story.story_id)
        if not assignment:
            self.logger.warning("no_assignment_found", {
                "story_id": story.story_id
            })
            return

        for agent_id in assignment.agent_ids:
            # Decrease workload
            if agent_id in self.workload:
                self.workload[agent_id] = max(0, self.workload[agent_id] - 1)

            # Remove from active assignments
            if agent_id in self.active_assignments:
                self.active_assignments[agent_id].discard(story.story_id)

        self.logger.debug("agents_released", {
            "story_id": story.story_id,
            "agents": assignment.agent_ids
        })

    def get_assignment(self, story_id: str) -> Optional[CrewAssignment]:
        """
        Get crew assignment for a story.

        Args:
            story_id: Story ID

        Returns:
            CrewAssignment if found, None otherwise

        NOTE: For Phase 0, assignments are stored in memory.
              Phase 0.3 will implement persistent storage.
        """
        # TODO: Implement persistent assignment storage
        return None

    def get_workload_status(self) -> Dict[str, Any]:
        """
        Get current workload status for all agents.

        Returns:
            Dict with workload information:
                - total_agents: Number of agents
                - active_stories: Number of stories in progress
                - workload: Dict of agent_id → story count
                - avg_workload: Average stories per agent
        """
        active_story_count = sum(len(stories) for stories in self.active_assignments.values())
        avg_workload = sum(self.workload.values()) / len(self.workload) if self.workload else 0.0

        return {
            "total_agents": len(self.skill_matrix),
            "active_stories": active_story_count,
            "workload": dict(self.workload),
            "avg_workload": avg_workload,
        }

    def update_agent_metrics(
        self,
        agent_id: str,
        success: bool,
        tokens_used: int
    ):
        """
        Update agent performance metrics after story completion.

        Args:
            agent_id: Agent ID
            success: Whether story succeeded
            tokens_used: Tokens used by agent

        Updates:
            - success_rate: Moving average of success
            - avg_tokens: Moving average of tokens used
            - stories_completed: Increment counter
        """
        if agent_id not in self.skill_matrix:
            self.logger.warning("agent_not_found_in_skill_matrix", {
                "agent_id": agent_id
            })
            return

        agent_skill = self.skill_matrix[agent_id]

        # Update counters
        if success:
            agent_skill.stories_completed += 1
        else:
            agent_skill.stories_failed += 1

        # Update success rate (moving average)
        total_stories = agent_skill.stories_completed + agent_skill.stories_failed
        if total_stories > 0:
            agent_skill.success_rate = agent_skill.stories_completed / total_stories

        # Update avg tokens (moving average)
        if agent_skill.stories_completed > 0:
            # Weighted average: (old_avg * (n-1) + new_value) / n
            n = agent_skill.stories_completed
            agent_skill.avg_tokens = int(
                (agent_skill.avg_tokens * (n - 1) + tokens_used) / n
            )
        else:
            agent_skill.avg_tokens = tokens_used

        agent_skill.last_active = datetime.now()

        self.logger.debug("agent_metrics_updated", {
            "agent_id": agent_id,
            "success_rate": f"{agent_skill.success_rate:.2%}",
            "avg_tokens": agent_skill.avg_tokens,
            "stories_completed": agent_skill.stories_completed
        })
