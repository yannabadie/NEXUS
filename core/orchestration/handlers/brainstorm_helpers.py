"""
NEXUS V10.2 - Brainstorming State Helpers

Extracted helper functions for handle_brainstorming and handle_validating_cfl states.
These are pure functions that take explicit parameters.

Usage:
    from core.orchestration.handlers.brainstorm_helpers import (
        process_agent_message,
        extract_tool_request
    )
"""

from typing import Dict, Optional, Any, Tuple
import json
import logging

logger = logging.getLogger("nexus.handlers.brainstorm")


def extract_tool_request(message: Dict) -> Optional[Dict]:
    """
    Extract tool_use from agent message if present.
    
    Args:
        message: Agent response dict
        
    Returns:
        Tool use dict or None
    """
    if not message:
        return None
    
    # Check for tool_use in different formats
    tool_use = message.get("tool_use")
    if tool_use:
        return tool_use
    
    # Check for nested in content
    content = message.get("content", "")
    if isinstance(content, dict) and "tool_use" in content:
        return content["tool_use"]
    
    return None


def is_action_type(message: Dict, action_type: str) -> bool:
    """
    Check if message has specific action type.
    
    Args:
        message: Agent message
        action_type: Expected action type (TALK, TOOL_USE, etc.)
        
    Returns:
        True if message has matching action type
    """
    return message.get("action_type", "").upper() == action_type.upper()


def get_message_content(message: Dict) -> str:
    """
    Extract content from agent message safely.
    
    Args:
        message: Agent message dict
        
    Returns:
        Content string
    """
    content = message.get("content", "")
    if isinstance(content, dict):
        return json.dumps(content, ensure_ascii=False)
    return str(content)


def should_validate_tool(tool_use: Dict) -> Tuple[bool, str]:
    """
    Check if tool execution requires CFL validation.
    
    Args:
        tool_use: Tool use request
        
    Returns:
        Tuple of (needs_validation, reason)
    """
    if not tool_use:
        return False, "No tool use"
    
    tool_name = tool_use.get("tool_name", "")
    
    # High-risk tools always need validation
    HIGH_RISK_TOOLS = ["bash", "edit", "write", "glob", "grep"]
    if tool_name in HIGH_RISK_TOOLS:
        return True, f"High-risk tool: {tool_name}"
    
    # Read operations can skip
    READ_ONLY = ["read", "list_dir"]
    if tool_name in READ_ONLY:
        return False, f"Read-only tool: {tool_name}"
    
    return True, "Default validation"


def format_tool_result(
    tool_name: str,
    success: bool,
    output: str,
    truncate_at: int = 500
) -> str:
    """
    Format tool execution result for display.
    
    Args:
        tool_name: Name of executed tool
        success: Whether execution succeeded
        output: Tool output
        truncate_at: Max chars before truncation
        
    Returns:
        Formatted result string
    """
    status = "✓" if success else "✗"
    truncated = output[:truncate_at] + "..." if len(output) > truncate_at else output
    return f"[{status} {tool_name}] {truncated}"
