"""
Model Router - Intelligent Model Selection for NEXUS V7 Chrysalis

Routes tasks to the most appropriate model based on task type and complexity.
Implements routing strategies for both Claude (Opus/Sonnet) and Gemini (Pro/Flash).

Usage:
    from core.routing import ModelRouter

    router = ModelRouter(config)

    # Claude routing
    model = router.select_claude_model(TaskType.BRAINSTORM)
    # Returns: "claude-opus-4-5-20251101"

    # Gemini routing (V7 Sprint 6)
    model = router.select_gemini_model(TaskType.REASONING)
    # Returns: "gemini-3-pro-preview"
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

    Claude: Complex tasks → Opus, simpler tasks → Sonnet
    Gemini: Complex tasks → 3-Pro, simpler tasks → Flash
    """
    # Opus/3-Pro routed (complex, creative, security-critical)
    BRAINSTORM = "brainstorm"      # Evolution brainstorming
    REDTEAM = "redteam"            # Security/alignment testing
    ARCHITECT = "architect"        # Architecture decisions
    EVOLUTION = "evolution"        # Child mutation design
    REASONING = "reasoning"        # Complex reasoning (Gemini 3 Pro)
    RESEARCH = "research"          # Web research (Gemini 3 Pro)
    ANALYSIS = "analysis"          # Deep analysis (Gemini 3 Pro)

    # Sonnet/Flash routed (simpler, faster)
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

    Claude:
        Opus (claude-opus-4-5): Complex reasoning, creativity, security
        Sonnet (claude-sonnet-4-5): Speed, tools, simple tasks

    Gemini (V7 Sprint 6):
        3-Pro (gemini-3-pro-preview): Complex reasoning, research, analysis
        Flash (gemini-2.5-flash): Simple tasks, validation, formatting
    """

    def __init__(self, config: Optional["Config"] = None):
        """
        Initialize router with config.

        Args:
            config: NEXUS config with model IDs and task type mappings
        """
        # Default Claude model IDs
        self.opus_model = "claude-opus-4-5-20251101"
        self.sonnet_model = "claude-sonnet-4-5-20250929"

        # Default Gemini model IDs (V7 Sprint 6)
        self.gemini_model = "gemini-3-pro-preview"
        self.gemini_pro_model = "gemini-3-pro-preview"
        self.gemini_flash_model = "gemini-3-flash-preview"

        # Default Claude task type mappings
        self.opus_tasks = {TaskType.BRAINSTORM, TaskType.REDTEAM,
                          TaskType.ARCHITECT, TaskType.EVOLUTION}
        self.sonnet_tasks = {TaskType.TOOL, TaskType.VALIDATION,
                            TaskType.SIMPLE, TaskType.FORMAT}

        # Default Gemini task type mappings (V7 Sprint 6)
        self.gemini_pro_tasks = {TaskType.REASONING, TaskType.RESEARCH,
                                 TaskType.ANALYSIS, TaskType.BRAINSTORM, TaskType.EVOLUTION}
        self.gemini_flash_tasks = {TaskType.SIMPLE, TaskType.FORMAT,
                                   TaskType.VALIDATION, TaskType.TOOL}

        # Override with config if provided
        if config:
            # Claude models
            self.opus_model = getattr(config, 'claude_opus_model', self.opus_model)
            self.sonnet_model = getattr(config, 'claude_sonnet_model', self.sonnet_model)

            # Gemini models (V7 Sprint 6)
            self.gemini_model = getattr(config, 'gemini_default_model', self.gemini_model)
            self.gemini_pro_model = getattr(config, 'gemini_pro_model', self.gemini_pro_model)
            self.gemini_flash_model = getattr(config, 'gemini_flash_model', self.gemini_flash_model)

            # Update Claude task mappings from config lists
            opus_list = getattr(config, 'opus_task_types', [])
            sonnet_list = getattr(config, 'sonnet_task_types', [])

            if opus_list:
                self.opus_tasks = {TaskType(t) for t in opus_list if t in [e.value for e in TaskType]}
            if sonnet_list:
                self.sonnet_tasks = {TaskType(t) for t in sonnet_list if t in [e.value for e in TaskType]}

            # Update Gemini task mappings from config lists (V7 Sprint 6)
            gemini_pro_list = getattr(config, 'gemini_pro_tasks', [])
            gemini_flash_list = getattr(config, 'gemini_flash_tasks', [])

            if gemini_pro_list:
                self.gemini_pro_tasks = {TaskType(t) for t in gemini_pro_list if t in [e.value for e in TaskType]}
            if gemini_flash_list:
                self.gemini_flash_tasks = {TaskType(t) for t in gemini_flash_list if t in [e.value for e in TaskType]}

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
        """Get the default configured Gemini model"""
        return self.gemini_model

    def select_gemini_model(self, task_type: TaskType) -> str:
        """
        Select appropriate Gemini model for task type (V7 Sprint 6).

        Complex tasks (reasoning, research, analysis) → Gemini 3 Pro
        Simple tasks (tool, validation, format) → Gemini Flash

        Args:
            task_type: Type of task to perform

        Returns:
            Model ID string (gemini-3-pro-preview or gemini-2.5-flash)
        """
        if task_type in self.gemini_pro_tasks:
            return self.gemini_pro_model
        return self.gemini_flash_model

    def select_gemini_model_str(self, task_type_str: str) -> str:
        """
        Select Gemini model from string task type.

        Args:
            task_type_str: String like "reasoning", "research", "tool", etc.

        Returns:
            Model ID string
        """
        try:
            task_type = TaskType(task_type_str.lower())
        except ValueError:
            task_type = TaskType.DEFAULT
        return self.select_gemini_model(task_type)

    def should_use_gemini_pro(self, task_type: TaskType) -> bool:
        """Check if task should use Gemini 3 Pro (V7 Sprint 6)"""
        return task_type in self.gemini_pro_tasks

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
