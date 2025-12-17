"""
NEXUS V10.2 - Tool Manager Package

Split from monolithic tool_manager.py for better maintainability.

Usage:
    from core.execution.tools import ToolManager, ToolResult
"""

from core.execution.tool_manager import ToolManager, ToolResult

__all__ = ["ToolManager", "ToolResult"]
