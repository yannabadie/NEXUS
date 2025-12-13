"""
NEXUS V9.5 Execution Module

Refactored from monolithic tool_manager.py (1848 LOC).

Modules:
- tool_registry: Tool registration and discovery
- validation_service: Path and security validation
- execution_engine: Centralized tool execution
- handlers/: Individual tool handlers

Usage:
    from core.execution import ExecutionEngine, ToolResult
    engine = ExecutionEngine(workspace_path)
    result = engine.execute(tool_request)
"""

from .handlers.base import ToolResult, BaseHandler
from .tool_registry import ToolRegistry, get_tool_registry, reset_tool_registry
from .validation_service import ValidationService
from .execution_engine import ExecutionEngine, get_execution_engine, reset_execution_engine

__all__ = [
    # Core classes
    "ToolResult",
    "BaseHandler",
    "ToolRegistry",
    "ValidationService",
    "ExecutionEngine",
    # Factory functions
    "get_tool_registry",
    "reset_tool_registry",
    "get_execution_engine",
    "reset_execution_engine",
]

__version__ = "9.5.0"
