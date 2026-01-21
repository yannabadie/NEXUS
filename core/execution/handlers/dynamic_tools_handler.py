"""
Dynamic Tools Handler - Create, delete, list, run dynamic Python tools.

NEXUS V9.6 Sprint 5.2b - Extracted from tool_manager.py

Provides:
- CreateToolHandler: Create new dynamic tools
- DeleteToolHandler: Delete existing tools
- ListDynamicToolsHandler: List all available tools
- RunDynamicToolHandler: Execute a dynamic tool
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Any, Optional

from .base import BaseHandler, ToolResult

# Optional import - DynamicToolManager may not be available
try:
    from core.execution.dynamic_tools import DynamicToolManager
    DYNAMIC_TOOLS_AVAILABLE = True
except ImportError:
    DynamicToolManager = None  # type: ignore
    DYNAMIC_TOOLS_AVAILABLE = False


class DynamicToolsHandlerBase(BaseHandler):
    """
    Base class for dynamic tool handlers.

    Manages lazy initialization of DynamicToolManager.
    """

    def __init__(
        self,
        workspace_path: Path,
        validation_service: Any = None,
        dynamic_tool_manager: Optional[Any] = None
    ):
        """Initializes the DynamicToolsHandlerBase.

        Args:
            workspace_path: The root path of the workspace.
            validation_service: Optional service for validating operations.
            dynamic_tool_manager: Optional instance of DynamicToolManager.
                If not provided, it will be lazily initialized.

        Raises:
            None
        """
        super().__init__(workspace_path, validation_service)
        self._dynamic_tool_manager = dynamic_tool_manager

    def _get_manager(self) -> Optional[Any]:
        """Gets or creates the DynamicToolManager instance.

        Lazily initializes the manager if it hasn't been created yet.
        Checks if dynamic tools are available in the environment.

        Returns:
            The DynamicToolManager instance if available and successfully
            initialized, otherwise None.

        Raises:
            None: Exceptions during initialization are caught and return None.
        """
        if self._dynamic_tool_manager is not None:
            return self._dynamic_tool_manager

        if not DYNAMIC_TOOLS_AVAILABLE or DynamicToolManager is None:
            return None

        try:
            self._dynamic_tool_manager = DynamicToolManager(self.workspace_path)
            return self._dynamic_tool_manager
        except Exception:
            return None

    def _manager_not_available(self) -> ToolResult:
        """Constructs a ToolResult indicating the manager is unavailable.

        Used when the DynamicToolManager cannot be imported or initialized.

        Returns:
            A ToolResult object with status="ERROR" and an error message.

        Raises:
            None
        """
        return ToolResult(
            tool_name=self.tool_name,
            status="ERROR",
            output="",
            error="Dynamic Tool Manager not available"
        )


class CreateToolHandler(DynamicToolsHandlerBase):
    """Handler for creating new dynamic Python tools.

    This handler manages the creation of sandboxed Python tools that can be
    executed dynamically. It validates the tool name and code before creation.

    Attributes:
        tool_name (str): The name of the tool ("create_tool").
    """

    @property
    def tool_name(self) -> str:
        return "create_tool"

    def execute(self, args: Dict[str, Any]) -> ToolResult:
        """Executes the tool creation process.

        Args:
            args: A dictionary containing the tool configuration.
                Expected keys:
                    name (str): The name of the tool to create.
                    code (str): The Python source code for the tool.
                    description (str, optional): A description of the tool.

        Returns:
            ToolResult: The result of the creation operation. Contains the
            tool path if successful, or error details if failed.

        Raises:
            None: Errors are captured and returned in the ToolResult.
        """
        manager = self._get_manager()
        if manager is None:
            return self._manager_not_available()

        name = args.get("name", "")
        code = args.get("code", "")
        description = args.get("description", "")

        if not name:
            return self._error("Tool name is required")

        if not code:
            return self._error("Tool code is required")

        result = manager.create_tool(name, code, description)

        if result.success:
            return ToolResult(
                tool_name=self.tool_name,
                status="SUCCESS",
                output=(
                    f"Tool '{name}' created successfully at {result.tool_path}\n\n"
                    f"Use 'run_dynamic_tool' with name='{name}' to execute it."
                )
            )
        else:
            error_msg = result.error or "Unknown error"
            if result.validation_violations:
                error_msg += "\n\nValidation violations:\n"
                error_msg += "\n".join(f"  - {v}" for v in result.validation_violations)

            return self._fail(error_msg)


class DeleteToolHandler(DynamicToolsHandlerBase):
    """Handler for deleting existing dynamic tools.

    This handler allows for the removal of dynamic tools from the workspace
    by their name.

    Attributes:
        tool_name (str): The name of the tool ("delete_tool").
    """

    @property
    def tool_name(self) -> str:
        return "delete_tool"

    def execute(self, args: Dict[str, Any]) -> ToolResult:
        """Deletes a dynamic tool.

        Args:
            args: A dictionary containing the arguments for the tool.
                Expected keys:
                    name (str): The name of the tool to delete.

        Returns:
            ToolResult: The result of the deletion operation, indicating
            success or failure.

        Raises:
            None: Errors are returned as part of the ToolResult.
        """
        manager = self._get_manager()
        if manager is None:
            return self._manager_not_available()

        name = args.get("name", "")

        if not name:
            return self._error("Tool name is required")

        success, message = manager.delete_tool(name)

        return ToolResult(
            tool_name=self.tool_name,
            status="SUCCESS" if success else "FAILURE",
            output=message if success else "",
            error="" if success else message
        )


class ListDynamicToolsHandler(DynamicToolsHandlerBase):
    """Handler for listing all dynamic tools."""

    @property
    def tool_name(self) -> str:
        return "list_dynamic_tools"

    def execute(self, args: Dict[str, Any]) -> ToolResult:
        """Lists all available dynamic tools.

        Args:
            args: A dictionary of arguments (unused for this handler).

        Returns:
            ToolResult: A result containing a formatted list of available
            dynamic tools, or a message if none are found.

        Raises:
            None: Errors are returned as part of the ToolResult.
        """
        manager = self._get_manager()
        if manager is None:
            return self._manager_not_available()

        tools = manager.list_tools()

        if not tools:
            return ToolResult(
                tool_name=self.tool_name,
                status="SUCCESS",
                output=(
                    "No dynamic tools found.\n\n"
                    "Use 'create_tool' to create a new tool."
                )
            )

        output = f"Found {len(tools)} dynamic tool(s):\n\n"
        for tool in tools:
            output += f"  - {tool.name}: {tool.description}\n"
            output += f"    Created: {tool.created_at}\n"

        return ToolResult(
            tool_name=self.tool_name,
            status="SUCCESS",
            output=output
        )


class RunDynamicToolHandler(DynamicToolsHandlerBase):
    """Handler for executing dynamic tools.

    This handler manages the execution of previously created dynamic tools,
    passing provided arguments to the tool's entry point.

    Attributes:
        tool_name (str): The name of the tool ("run_dynamic_tool").
    """

    @property
    def tool_name(self) -> str:
        return "run_dynamic_tool"

    def execute(self, args: Dict[str, Any]) -> ToolResult:
        """Executes a specified dynamic tool with provided arguments.

        Args:
            args: A dictionary containing execution parameters.
                Expected keys:
                    name (str): The name of the tool to run.
                    args (Dict[str, Any], optional): A dictionary of arguments
                        to pass to the tool's execution function.

        Returns:
            ToolResult: The result of the tool execution, containing the output
            if successful, or error details if the execution failed or timed out.

        Raises:
            None: Execution errors and timeouts are returned in the ToolResult.
        """
        manager = self._get_manager()
        if manager is None:
            return self._manager_not_available()

        name = args.get("name", "")
        tool_args = args.get("args", {})

        if not name:
            return self._error("Tool name is required")

        result = manager.execute_tool(name, tool_args)

        if result.timed_out:
            return ToolResult(
                tool_name=self.tool_name,
                status="TIMEOUT",
                output="",
                error=result.error
            )

        return ToolResult(
            tool_name=self.tool_name,
            status="SUCCESS" if result.success else "FAILURE",
            output=result.output,
            error=result.error
        )


def create_dynamic_tool_handlers(
    workspace_path: Path,
    validation_service: Any = None,
    dynamic_tool_manager: Any = None
) -> Dict[str, BaseHandler]:
    """
    Factory function to create all dynamic tool handlers.

    Args:
        workspace_path: Workspace root path
        validation_service: Optional validation service
        dynamic_tool_manager: Optional shared DynamicToolManager instance

    Returns:
        Dict mapping tool names to handlers
    """
    return {
        "create_tool": CreateToolHandler(
            workspace_path, validation_service, dynamic_tool_manager
        ),
        "delete_tool": DeleteToolHandler(
            workspace_path, validation_service, dynamic_tool_manager
        ),
        "list_dynamic_tools": ListDynamicToolsHandler(
            workspace_path, validation_service, dynamic_tool_manager
        ),
        "run_dynamic_tool": RunDynamicToolHandler(
            workspace_path, validation_service, dynamic_tool_manager
        ),
    }
