"""
NEXUS V9 Command System

This module provides:
1. Legacy slash command utilities (from slash_commands.py)
2. Strategy Pattern-based command dispatch system (V9)

Usage (V9 - New):
    from core.interface.commands import CommandRegistry, CommandContext

    registry = CommandRegistry()
    registry.register(StatusCommand())

    context = CommandContext(orchestrator, console, config)
    result = registry.dispatch("/status", context)

Usage (Legacy):
    from core.interface.commands import is_slash_command, parse_command
"""

# V9: Strategy Pattern command dispatch
from .registry import (
    Command,
    CommandContext,
    CommandRegistry,
    CommandResult,
    CommandStatus,
)

# Legacy: Re-export from slash_commands.py for backward compatibility
from core.interface.slash_commands import (
    is_slash_command,
    is_exit_command,
    parse_command,
    get_help_message,
    get_category_for_command,
    SLASH_COMMANDS,
    COMMAND_CATEGORIES,
)

__all__ = [
    # V9 Strategy Pattern
    "Command",
    "CommandContext",
    "CommandRegistry",
    "CommandResult",
    "CommandStatus",
    # Legacy
    "is_slash_command",
    "is_exit_command",
    "parse_command",
    "get_help_message",
    "get_category_for_command",
    "SLASH_COMMANDS",
    "COMMAND_CATEGORIES",
]
