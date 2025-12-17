"""
NEXUS V7.5 HIVE MIND - Prompt Loader Module

Handles loading and assembling prompts with include directives.
"""

from .prompt_loader import load_prompt, resolve_includes

__all__ = ["load_prompt", "resolve_includes"]
