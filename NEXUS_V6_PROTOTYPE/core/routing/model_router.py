"""
Model Router - Intelligent Model Selection for NEXUS V7

Routes tasks to the most appropriate model based on task type and complexity.
Implements the Opus vs Sonnet routing strategy for Claude models.

Usage:
    from core.routing import ModelRouter

    router = ModelRouter(config)
    model = router.select_claude_model(TaskType.BRAINSTORM)
    # Returns: "claude-opus-4-5-20251101"
"""

from enum import Enum
from typing import Optional, List, TYPE_CHECKING
from dataclasses import dataclass

if TYPE_CHECKING:
    from core.config import Config
    from core.swarm import AgentPool, AgentProfile


class TaskType(Enum):
    """
    Task types for model routing.

    Complex tasks route to Opus, simpler tasks route to Sonnet.
    """
    # Opus-routed (complex, creative, security-critical)
    BRAINSTORM = "brainstorm"      # Evolution brainstorming
    REDTEAM = "redteam"            # Security/alignment testing
    ARCHITECT = "architect"        # Architecture decisions
    EVOLUTION = "evolution"        # Child mutation design

    # Sonnet-routed (simpler, faster)
    TOOL = "tool"                  # Tool execution
    VALIDATION = "validation"      # Code validation
    SIMPLE = "simple"              # Simple queries
    FORMAT = "format"              # Formatting tasks

    # Default
    DEFAULT = "default"


@dataclass
class RoutingDecision:
    """Result of model routing decision"""
    model_id: str
    task_type: TaskType
    reason: str
    is_opus: bool = False


class ModelRouter:
    """
    Routes tasks to appropriate models based on complexity.

    Opus (claude-opus-4-5): Complex reasoning, creativity, security
    Sonnet (claude-sonnet-4-5): Speed, tools, simple tasks
    """

    def __init__(self, config: Optional["Config"] = None):
        """
        Initialize router with config.

        Args:
            config: NEXUS config with model IDs and task type mappings
        """
        # Default model IDs (can be overridden by config)
        self.opus_model = "claude-opus-4-5-20251101"
        self.sonnet_model = "claude-sonnet-4-5-20250929"
        self.gemini_model = "gemini-2.5-pro"

        # Default task type mappings
        self.opus_tasks = {TaskType.BRAINSTORM, TaskType.REDTEAM,
                          TaskType.ARCHITECT, TaskType.EVOLUTION}
        self.sonnet_tasks = {TaskType.TOOL, TaskType.VALIDATION,
                            TaskType.SIMPLE, TaskType.FORMAT}

        # Override with config if provided
        if config:
            self.opus_model = getattr(config, 'claude_opus_model', self.opus_model)
            self.sonnet_model = getattr(config, 'claude_sonnet_model', self.sonnet_model)
            self.gemini_model = getattr(config, 'gemini_default_model', self.gemini_model)

            # Update task mappings from config lists
            opus_list = getattr(config, 'opus_task_types', [])
            sonnet_list = getattr(config, 'sonnet_task_types', [])

            if opus_list:
                self.opus_tasks = {TaskType(t) for t in opus_list if t in [e.value for e in TaskType]}
            if sonnet_list:
                self.sonnet_tasks = {TaskType(t) for t in sonnet_list if t in [e.value for e in TaskType]}

    def select_claude_model(self, task_type: TaskType) -> str:
        """
        Select appropriate Claude model for task type.

        Args:
            task_type: Type of task to perform

        Returns:
            Model ID string (opus or sonnet)
        """
        if task_type in self.opus_tasks:
            return self.opus_model
        return self.sonnet_model

    def select_claude_model_str(self, task_type_str: str) -> str:
        """
        Select Claude model from string task type.

        Args:
            task_type_str: String like "brainstorm", "tool", etc.

        Returns:
            Model ID string
        """
        try:
            task_type = TaskType(task_type_str.lower())
        except ValueError:
            task_type = TaskType.DEFAULT
        return self.select_claude_model(task_type)

    def route(self, task_type: TaskType) -> RoutingDecision:
        """
        Make a full routing decision with explanation.

        Args:
            task_type: Type of task

        Returns:
            RoutingDecision with model and reasoning
        """
        model = self.select_claude_model(task_type)
        is_opus = model == self.opus_model

        if is_opus:
            reason = f"Task type '{task_type.value}' requires complex reasoning - routing to Opus"
        else:
            reason = f"Task type '{task_type.value}' is routine - routing to Sonnet for speed"

        return RoutingDecision(
            model_id=model,
            task_type=task_type,
            reason=reason,
            is_opus=is_opus
        )

    def get_gemini_model(self) -> str:
        """Get the configured Gemini model"""
        return self.gemini_model

    def should_use_opus(self, task_type: TaskType) -> bool:
        """Check if task should use Opus"""
        return task_type in self.opus_tasks

    def select_best_agent(
        self,
        task_type: TaskType,
        agent_pool: Optional["AgentPool"] = None,
        min_importance: float = 0.5
    ) -> RoutingDecision:
        """
        Select best agent using DyLAN metrics when available.

        Combines static task type routing with dynamic performance metrics.
        Falls back to static routing if no pool or insufficient metrics.

        Args:
            task_type: Type of task to perform
            agent_pool: Optional AgentPool with performance history
            min_importance: Minimum importance score to consider agent (default 0.5)

        Returns:
            RoutingDecision with model selection and reasoning

        Example:
            router = ModelRouter(config)
            pool = create_default_pool(config)
            decision = router.select_best_agent(TaskType.BRAINSTORM, pool)
            # Uses DyLAN metrics if available, else static routing
        """
        # Base routing decision (static)
        base_model = self.select_claude_model(task_type)
        is_opus = base_model == self.opus_model

        # No pool = use static routing
        if agent_pool is None:
            return RoutingDecision(
                model_id=base_model,
                task_type=task_type,
                reason=f"Static routing: {task_type.value} → {'Opus' if is_opus else 'Sonnet'}",
                is_opus=is_opus
            )

        # Get agents with performance for this task type
        task_type_str = task_type.value
        best_agents = agent_pool.select_best_for_task(task_type_str, top_k=2)

        if not best_agents:
            return RoutingDecision(
                model_id=base_model,
                task_type=task_type,
                reason="No agent metrics yet, using static routing",
                is_opus=is_opus
            )

        # Check if best agent meets minimum importance threshold
        best = best_agents[0]
        best_importance = best.get_task_importance(task_type_str)

        if best_importance < min_importance:
            return RoutingDecision(
                model_id=base_model,
                task_type=task_type,
                reason=f"Best agent importance ({best_importance:.2f}) below threshold ({min_importance})",
                is_opus=is_opus
            )

        # Use DyLAN-selected agent
        selected_is_opus = "opus" in best.model.lower()
        return RoutingDecision(
            model_id=best.model,
            task_type=task_type,
            reason=f"DyLAN selection: {best.agent_id} (importance={best_importance:.3f}, "
                   f"success_rate={best.success_rate:.1%})",
            is_opus=selected_is_opus
        )

    def get_routing_stats(
        self,
        agent_pool: Optional["AgentPool"] = None
    ) -> dict:
        """
        Get routing statistics for debugging.

        Args:
            agent_pool: Optional AgentPool for metrics

        Returns:
            Dict with routing configuration and pool stats
        """
        stats = {
            "opus_model": self.opus_model,
            "sonnet_model": self.sonnet_model,
            "gemini_model": self.gemini_model,
            "opus_tasks": [t.value for t in self.opus_tasks],
            "sonnet_tasks": [t.value for t in self.sonnet_tasks],
            "pool_available": agent_pool is not None
        }

        if agent_pool:
            pool_stats = agent_pool.get_pool_stats()
            stats["pool_agents"] = pool_stats.get("agents", 0)
            stats["pool_invocations"] = pool_stats.get("total_invocations", 0)
            stats["pool_avg_importance"] = pool_stats.get("average_pool_importance", 0)

        return stats
