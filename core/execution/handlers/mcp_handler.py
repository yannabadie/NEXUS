"""
MCP Handler - Execute Model Context Protocol tools.

NEXUS V9.6 Sprint 5.2b - Extracted from tool_manager.py

Provides:
- MCPToolHandler: Execute tools from MCP servers
- MCP_AVAILABLE: Flag indicating MCP module availability
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Any, Optional, Callable

from .base import BaseHandler, ToolResult

# Optional import - MCP module may not be available
try:
    from core.mcp import MCPRegistry
    from core.mcp.client import MCPClientError, MCPServerError
    MCP_AVAILABLE = True
except ImportError:
    MCPRegistry = None  # type: ignore
    MCPClientError = Exception  # type: ignore
    MCPServerError = Exception  # type: ignore
    MCP_AVAILABLE = False


class MCPToolHandler(BaseHandler):
    """
    Handler for executing MCP (Model Context Protocol) tools.

    Delegates tool calls to registered MCP servers.
    """

    def __init__(
        self,
        workspace_path: Path,
        validation_service: Any = None,
        mcp_registry: Optional[Any] = None,
        server_name: str = "",
        mcp_tool_name: str = ""
    ):
        """
        Initialize the MCP tool handler.

        Args:
            workspace_path: Path to the workspace root.
            validation_service: Service for validating tool execution.
            mcp_registry: Registry containing MCP clients.
            server_name: Name of the target MCP server.
            mcp_tool_name: Name of the tool to execute on the server.

        Returns:
            None

        Raises:
            None
        """
        super().__init__(workspace_path, validation_service)
        self._mcp_registry = mcp_registry
        self._server_name = server_name
        self._mcp_tool_name = mcp_tool_name

    @property
    def tool_name(self) -> str:
        """Return full MCP tool name (mcp_{server}_{tool})."""
        if self._server_name and self._mcp_tool_name:
            return f"mcp_{self._server_name}_{self._mcp_tool_name}"
        return "mcp_tool"

    def execute(self, args: Dict[str, Any]) -> ToolResult:
        """
        Execute an MCP tool via the configured server client.

        Args:
            args: A dictionary of arguments to pass to the MCP tool.

        Returns:
            ToolResult: The result of the tool execution. Contains the output
                text on success, or an error message on failure.

        Raises:
            None: Exceptions during execution are caught and returned as
                failed ToolResult objects.
        """
        nexus_tool_name = self.tool_name

        if self._mcp_registry is None:
            return ToolResult(
                tool_name=nexus_tool_name,
                status="ERROR",
                output="",
                error="MCP registry not initialized"
            )

        try:
            client = self._mcp_registry.get_client(self._server_name)
            if client is None:
                return ToolResult(
                    tool_name=nexus_tool_name,
                    status="ERROR",
                    output="",
                    error=f"Failed to connect to MCP server: {self._server_name}"
                )

            # Call the tool
            result = client.call_tool(self._mcp_tool_name, args)

            if result.isError:
                return ToolResult(
                    tool_name=nexus_tool_name,
                    status="FAILURE",
                    output="",
                    error=result.text
                )

            return ToolResult(
                tool_name=nexus_tool_name,
                status="SUCCESS",
                output=result.text
            )

        except MCPServerError as e:
            return ToolResult(
                tool_name=nexus_tool_name,
                status="FAILURE",
                output="",
                error=f"MCP server error: {str(e)}"
            )
        except MCPClientError as e:
            return ToolResult(
                tool_name=nexus_tool_name,
                status="ERROR",
                output="",
                error=f"MCP client error: {str(e)}"
            )
        except Exception as e:
            return ToolResult(
                tool_name=nexus_tool_name,
                status="ERROR",
                output="",
                error=f"Unexpected error: {str(e)}"
            )


def create_mcp_tool_handler(
    workspace_path: Path,
    mcp_registry: Any,
    server_name: str,
    tool_name: str,
    validation_service: Any = None
) -> MCPToolHandler:
    """
    Factory function to create an MCP tool handler.

    Args:
        workspace_path: The absolute path to the workspace root.
        mcp_registry: The registry instance managing MCP clients.
        server_name: The name of the target MCP server.
        tool_name: The name of the tool to execute.
        validation_service: Optional service for tool validation.

    Returns:
        MCPToolHandler: A configured handler instance for the specified tool.

    Raises:
        None: This factory function does not raise exceptions.
    """
    return MCPToolHandler(
        workspace_path=workspace_path,
        validation_service=validation_service,
        mcp_registry=mcp_registry,
        server_name=server_name,
        mcp_tool_name=tool_name
    )


def create_mcp_tool_executor(
    handler: MCPToolHandler
) -> Callable[[Dict], ToolResult]:
    """
    Create a callable executor for legacy ToolManager integration.

    This wraps the handler's execute method for compatibility with
    the ToolManager.tools dict pattern.

    Args:
        handler: MCPToolHandler instance to be wrapped.

    Returns:
        Callable[[Dict], ToolResult]: A callable that executes the handler.

    Raises:
        None
    """
    def executor(args: Dict) -> ToolResult:
        """
        Execute the wrapped MCP tool handler.

        Args:
            args: Dictionary of arguments for the tool.

        Returns:
            ToolResult containing the execution status and output.
        """
        return handler.execute(args)
    return executor
