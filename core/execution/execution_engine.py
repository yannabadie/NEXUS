"""
ExecutionEngine - Centralized Tool Execution Orchestrator.

NEXUS V9.5 Refactoring - Sprint 2

Coordinates:
- ToolRegistry for handler lookup
- ValidationService for security
- Individual handlers for execution
- Error handling and logging

This is the main entry point for tool execution in NEXUS.

Usage:
    engine = ExecutionEngine(workspace_path)
    result = engine.execute(tool_request)
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, Any, Optional, Callable

from .tool_registry import ToolRegistry, get_tool_registry
from .validation_service import ValidationService
from .handlers.base import ToolResult
from .handlers.file_handlers import create_file_handlers
from .handlers.bash_handler import create_bash_handler
from .handlers.search_handlers import create_search_handlers

logger = logging.getLogger(__name__)


class ExecutionEngine:
    """
    Centralized tool execution engine.

    Responsibilities:
    - Route tool requests to appropriate handlers
    - Apply security validation
    - Handle errors gracefully
    - Track execution metrics
    """

    def __init__(
        self,
        workspace_path: Path,
        registry: Optional[ToolRegistry] = None,
        validation_service: Optional[ValidationService] = None,
    ):
        """
        Initialize execution engine.

        Args:
            workspace_path: Workspace root path
            registry: Optional ToolRegistry (uses global if None)
            validation_service: Optional ValidationService (created if None)
        """
        self.workspace_path = Path(workspace_path)
        self.registry = registry or get_tool_registry()
        self.validation_service = validation_service or ValidationService(
            workspace_path=self.workspace_path,
            parent_path=self.workspace_path.parent,
            generation_active=self.workspace_path.parent.parent / "GENERATION_ACTIVE",
        )

        # Statistics
        self._stats = {
            "total_executions": 0,
            "successful": 0,
            "failed": 0,
            "blocked": 0,
        }

        # Initialize core handlers
        self._initialize_handlers()

    def _initialize_handlers(self) -> None:
        """Initialize and register core tool handlers."""
        # File handlers
        file_handlers = create_file_handlers(
            self.workspace_path,
            self.validation_service,
        )
        for name, handler in file_handlers.items():
            self.registry.register(
                name,
                handler.execute,
                category="core",
                description=handler.__class__.__doc__ or "",
            )

        # Bash handler
        bash_handler = create_bash_handler(
            self.workspace_path,
            self.validation_service,
        )
        self.registry.register(
            "bash",
            bash_handler.execute,
            category="core",
            description="Execute shell commands",
        )

        # Search handlers
        search_handlers = create_search_handlers(
            self.workspace_path,
            self.validation_service,
        )
        for name, handler in search_handlers.items():
            self.registry.register(
                name,
                handler.execute,
                category="core",
                description=handler.__class__.__doc__ or "",
            )

        logger.debug(f"Initialized {len(self.registry.list_tools())} core handlers")

    def execute(self, tool_request: Any) -> ToolResult:
        """
        Execute a tool request.

        Args:
            tool_request: Object with tool_name and arguments attributes

        Returns:
            ToolResult with execution outcome
        """
        tool_name = getattr(tool_request, 'tool_name', '')
        arguments = getattr(tool_request, 'arguments', {})

        return self.execute_by_name(tool_name, arguments)

    def execute_by_name(
        self,
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> ToolResult:
        """
        Execute a tool by name.

        Args:
            tool_name: Tool name (will be normalized)
            arguments: Tool arguments

        Returns:
            ToolResult with execution outcome
        """
        self._stats["total_executions"] += 1

        # Normalize tool name
        normalized_name = self.registry.normalize_name(tool_name)

        # Get handler
        handler = self.registry.get_handler(normalized_name)
        if handler is None:
            self._stats["failed"] += 1
            return ToolResult.make_error(tool_name, f"Unknown tool: {tool_name}")

        try:
            result = handler(arguments)

            # Track statistics
            if result.status == "SUCCESS":
                self._stats["successful"] += 1
            elif result.status == "BLOCKED":
                self._stats["blocked"] += 1
            else:
                self._stats["failed"] += 1

            return result

        except Exception as e:
            self._stats["failed"] += 1
            logger.error(f"Tool execution error: {tool_name}: {e}")
            return ToolResult.make_error(tool_name, str(e))

    def register_handler(
        self,
        name: str,
        handler: Callable[[Dict[str, Any]], ToolResult],
        *,
        category: str = "custom",
        description: str = "",
    ) -> None:
        """
        Register a custom tool handler.

        Args:
            name: Tool name
            handler: Handler function
            category: Tool category
            description: Tool description
        """
        self.registry.register(
            name,
            handler,
            category=category,
            description=description,
        )
        logger.debug(f"Registered custom handler: {name}")

    def has_tool(self, name: str) -> bool:
        """Check if tool exists."""
        return self.registry.has_tool(name)

    def list_tools(self) -> list[str]:
        """List all available tools."""
        return self.registry.list_tools()

    def set_evolution_mode(self, enabled: bool) -> None:
        """Enable or disable evolution mode."""
        self.validation_service.set_evolution_mode(enabled)

    def get_stats(self) -> Dict[str, int]:
        """Get execution statistics."""
        return dict(self._stats)

    def reset_stats(self) -> None:
        """Reset execution statistics."""
        self._stats = {
            "total_executions": 0,
            "successful": 0,
            "failed": 0,
            "blocked": 0,
        }


# Singleton instance
_engine_instance: Optional[ExecutionEngine] = None


def get_execution_engine(workspace_path: Optional[Path] = None) -> ExecutionEngine:
    """
    Get or create the global execution engine.

    Args:
        workspace_path: Workspace path (required on first call)

    Returns:
        ExecutionEngine instance
    """
    global _engine_instance
    if _engine_instance is None:
        if workspace_path is None:
            raise ValueError("workspace_path required for first initialization")
        _engine_instance = ExecutionEngine(workspace_path)
    return _engine_instance


def reset_execution_engine() -> None:
    """Reset the global execution engine (for testing)."""
    global _engine_instance
    _engine_instance = None
