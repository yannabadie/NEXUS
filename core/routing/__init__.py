"""
NEXUS V7 Model Routing Module

Routes tasks to appropriate models based on complexity and task type.
Supports Opus/Sonnet selection for Claude and model variants for Gemini.
"""

from .model_router import ModelRouter, TaskType

__all__ = ["ModelRouter", "TaskType"]
