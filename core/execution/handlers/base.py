"""
Base Handler - Foundation for all tool handlers.

NEXUS V9.5 Refactoring - Sprint 2

Defines:
- ToolResult: Standard result object
- BaseHandler: Protocol for handler implementations
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any, Protocol, runtime_checkable
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class ToolResult:
    """
    Result from tool execution.

    Attributes:
        tool_name: Name of the executed tool
        status: Execution status (SUCCESS, FAILURE, ERROR)
        output: Output from the tool
        error: Error message if any
    """
    tool_name: str
    status: str  # SUCCESS, FAILURE, ERROR
    output: str
    error: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "tool_name": self.tool_name,
            "status": self.status,
            "output": self.output,
            "error": self.error,
        }

    @property
    def success(self) -> bool:
        """Check if execution was successful."""
        return self.status == "SUCCESS"

    @property
    def failed(self) -> bool:
        """Check if execution failed."""
        return self.status in ("FAILURE", "ERROR")

    @classmethod
    def ok(cls, tool_name: str, output: str) -> "ToolResult":
        """Create success result."""
        return cls(tool_name=tool_name, status="SUCCESS", output=output)

    @classmethod
    def fail(cls, tool_name: str, error: str, output: str = "") -> "ToolResult":
        """Create failure result."""
        return cls(tool_name=tool_name, status="FAILURE", output=output, error=error)

    @classmethod
    def error(cls, tool_name: str, error: str) -> "ToolResult":
        """Create error result."""
        return cls(tool_name=tool_name, status="ERROR", output="", error=error)


@runtime_checkable
class HandlerProtocol(Protocol):
    """Protocol for tool handlers."""

    def execute(self, args: Dict[str, Any]) -> ToolResult:
        """Execute the tool with given arguments."""
        ...


class BaseHandler(ABC):
    """
    Abstract base class for tool handlers.

    Provides common functionality and enforces interface.
    """

    def __init__(
        self,
        workspace_path: Path,
        validation_service: Any = None,
    ):
        """
        Initialize handler.

        Args:
            workspace_path: Workspace root path
            validation_service: Optional ValidationService instance
        """
        self.workspace_path = Path(workspace_path)
        self.validation_service = validation_service
        self._logger = logging.getLogger(f"nexus.tools.{self.tool_name}")

    @property
    @abstractmethod
    def tool_name(self) -> str:
        """Tool name for this handler."""
        ...

    @abstractmethod
    def execute(self, args: Dict[str, Any]) -> ToolResult:
        """
        Execute the tool.

        Args:
            args: Tool arguments

        Returns:
            ToolResult with status and output
        """
        ...

    def _resolve_path(self, path_str: str) -> Path:
        """
        Resolve path relative to workspace.

        Args:
            path_str: Path string (absolute or relative)

        Returns:
            Resolved absolute Path
        """
        path = Path(path_str)
        if path.is_absolute():
            return path.resolve()
        return (self.workspace_path / path).resolve()

    def _validate_path(self, path: Path, operation: str = "read") -> bool:
        """
        Validate path using ValidationService.

        Args:
            path: Path to validate
            operation: Operation type (read, write, edit, list)

        Returns:
            True if path is valid
        """
        if self.validation_service is None:
            return True
        return self.validation_service.validate_path(path, operation)

    def _ok(self, output: str) -> ToolResult:
        """Create success result."""
        return ToolResult.ok(self.tool_name, output)

    def _fail(self, error: str, output: str = "") -> ToolResult:
        """Create failure result."""
        return ToolResult.fail(self.tool_name, error, output)

    def _error(self, error: str) -> ToolResult:
        """Create error result."""
        return ToolResult.error(self.tool_name, error)
