"""
Agent Metrics - DyLAN-inspired Performance Tracking

Implements importance scoring for intelligent agent selection.
Designed to scale from 2 agents (V7) to N agents (Phase 6 Swarm).

DyLAN Formula: importance_score = quality / cost
- quality: Task success rate and output quality (0.0-1.0)
- cost: tokens_used / 1000 + time_seconds

Usage:
    from core.swarm import AgentPool, AgentProfile, AgentInvocationResult

    pool = AgentPool()
    pool.register(AgentProfile(
        agent_id="claude_opus",
        provider="claude",
        model="claude-opus-4-5-20251101"
    ))

    # After invocation, record result
    result = AgentInvocationResult(
        agent_id="claude_opus",
        task_type="brainstorm",
        success=True,
        quality_score=0.85,
        tokens_used=1500,
        time_seconds=12.5
    )
    pool.agents["claude_opus"].record_invocation(result)

    # Select best agent for task
    best = pool.select_best_for_task("brainstorm")
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import datetime
from enum import Enum
import json


class AgentProvider(Enum):
    """Agent providers - extensible for future integrations"""
    GEMINI = "gemini"
    CLAUDE = "claude"
    # Future: OPENAI = "openai", LOCAL = "local"


@dataclass
class AgentInvocationResult:
    """
    Metrics for a single agent invocation.

    Used to calculate DyLAN importance score for agent selection.
    """
    agent_id: str
    task_type: str
    timestamp: datetime = field(default_factory=datetime.now)
    success: bool = True
    quality_score: float = 0.5  # 0.0-1.0
    tokens_used: int = 0
    time_seconds: float = 0.0
    error: Optional[str] = None

    @property
    def importance_score(self) -> float:
        """
        DyLAN-style importance: quality / cost

        Higher is better. Rewards quality while penalizing resource usage.
        """
        if not self.success:
            return 0.0
        cost = (self.tokens_used / 1000) + self.time_seconds
        return self.quality_score / max(cost, 0.1)

    def to_dict(self) -> Dict:
        return {
            "agent_id": self.agent_id,
            "task_type": self.task_type,
            "timestamp": self.timestamp.isoformat(),
            "success": self.success,
            "quality_score": self.quality_score,
            "tokens_used": self.tokens_used,
            "time_seconds": self.time_seconds,
            "importance_score": round(self.importance_score, 4),
            "error": self.error
        }


@dataclass
class AgentProfile:
    """
    Profile for a single agent with performance history.

    Tracks invocation history for importance scoring.
    Scales to N agents in Phase 6 Swarm.
    """
    agent_id: str
    provider: str  # "gemini", "claude"
    model: str
    capabilities: List[str] = field(default_factory=list)
    is_active: bool = True
    invocation_history: List[AgentInvocationResult] = field(default_factory=list)
    history_window: int = 100  # Keep last N invocations

    @property
    def average_importance(self) -> float:
        """Average importance score across all invocations"""
        if not self.invocation_history:
            return 0.5  # Neutral score for new agents
        scores = [r.importance_score for r in self.invocation_history]
        return sum(scores) / len(scores)

    @property
    def success_rate(self) -> float:
        """Success rate across invocations"""
        if not self.invocation_history:
            return 1.0
        successes = sum(1 for r in self.invocation_history if r.success)
        return successes / len(self.invocation_history)

    def get_task_importance(self, task_type: str) -> float:
        """Get importance score for specific task type"""
        relevant = [r for r in self.invocation_history if r.task_type == task_type]
        if not relevant:
            return self.average_importance
        return sum(r.importance_score for r in relevant) / len(relevant)

    def record_invocation(self, result: AgentInvocationResult):
        """Record an invocation result, maintaining window size"""
        self.invocation_history.append(result)
        # Trim to window size
        if len(self.invocation_history) > self.history_window:
            self.invocation_history = self.invocation_history[-self.history_window:]

    def to_dict(self) -> Dict:
        return {
            "agent_id": self.agent_id,
            "provider": self.provider,
            "model": self.model,
            "capabilities": self.capabilities,
            "is_active": self.is_active,
            "average_importance": round(self.average_importance, 4),
            "success_rate": round(self.success_rate, 4),
            "invocation_count": len(self.invocation_history)
        }


@dataclass
class AgentPool:
    """
    Pool of agents for multi-agent coordination.

    Foundation for Phase 6 Hybrid Swarm:
    - V7: 2 fixed agents (Gemini + Claude)
    - Phase 6: Dynamic N agents with spawning

    Selection uses DyLAN importance scoring.
    """
    agents: Dict[str, AgentProfile] = field(default_factory=dict)

    def register(self, profile: AgentProfile):
        """Register an agent in the pool"""
        self.agents[profile.agent_id] = profile

    def unregister(self, agent_id: str):
        """Remove an agent from the pool"""
        if agent_id in self.agents:
            del self.agents[agent_id]

    def get_active_agents(self) -> List[AgentProfile]:
        """Get all active agents"""
        return [a for a in self.agents.values() if a.is_active]

    def select_best_for_task(
        self,
        task_type: str,
        top_k: int = 1,
        min_importance: float = 0.0
    ) -> List[AgentProfile]:
        """
        Select best agent(s) for a task using importance scoring.

        Args:
            task_type: Type of task (brainstorm, validation, etc.)
            top_k: Number of agents to return (1 for V7, N for Phase 6)
            min_importance: Minimum importance threshold

        Returns:
            List of top-k agents sorted by task-specific importance
        """
        active = self.get_active_agents()
        if not active:
            return []

        # Score by task-specific importance
        scored = [
            (agent, agent.get_task_importance(task_type))
            for agent in active
        ]

        # Filter by minimum threshold
        scored = [(a, s) for a, s in scored if s >= min_importance]

        # Sort by score descending
        scored.sort(key=lambda x: x[1], reverse=True)

        return [agent for agent, _ in scored[:top_k]]

    def record_invocation(self, result: AgentInvocationResult):
        """Record invocation result to appropriate agent"""
        if result.agent_id in self.agents:
            self.agents[result.agent_id].record_invocation(result)

    def get_pool_stats(self) -> Dict:
        """Get aggregate statistics for the pool"""
        active = self.get_active_agents()
        if not active:
            return {"agents": 0, "total_invocations": 0}

        total_invocations = sum(
            len(a.invocation_history) for a in active
        )
        avg_importance = sum(
            a.average_importance for a in active
        ) / len(active)

        return {
            "agents": len(active),
            "total_invocations": total_invocations,
            "average_pool_importance": round(avg_importance, 4),
            "agents_detail": {a.agent_id: a.to_dict() for a in active}
        }

    def to_dict(self) -> Dict:
        return {
            "agents": {
                agent_id: profile.to_dict()
                for agent_id, profile in self.agents.items()
            },
            "stats": self.get_pool_stats()
        }

    def save_to_file(self, path: str):
        """Persist pool state to JSON file"""
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load_from_file(cls, path: str) -> "AgentPool":
        """Load pool state from JSON file"""
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        pool = cls()
        for agent_id, agent_data in data.get("agents", {}).items():
            profile = AgentProfile(
                agent_id=agent_data["agent_id"],
                provider=agent_data["provider"],
                model=agent_data["model"],
                capabilities=agent_data.get("capabilities", []),
                is_active=agent_data.get("is_active", True)
            )
            pool.register(profile)

        return pool


def create_default_pool(config=None) -> AgentPool:
    """
    Create default 2-agent pool for V7.

    Args:
        config: Optional config with model names

    Returns:
        AgentPool with Gemini and Claude profiles
    """
    pool = AgentPool()

    # Gemini agent
    gemini_model = "gemini-2.5-pro"
    if config:
        gemini_model = getattr(config, 'gemini_default_model', gemini_model)

    pool.register(AgentProfile(
        agent_id="gemini_primary",
        provider="gemini",
        model=gemini_model,
        capabilities=["reasoning", "coding", "research"]
    ))

    # Claude agent
    claude_model = "claude-opus-4-5-20251101"
    if config:
        claude_model = getattr(config, 'claude_opus_model', claude_model)

    pool.register(AgentProfile(
        agent_id="claude_opus",
        provider="claude",
        model=claude_model,
        capabilities=["brainstorm", "creativity", "architecture"]
    ))

    return pool
