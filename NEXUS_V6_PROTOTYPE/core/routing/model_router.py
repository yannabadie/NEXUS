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
from typing import Optional, TYPE_CHECKING
from dataclasses import dataclass

if TYPE_CHECKING:
    from core.config import Config


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
