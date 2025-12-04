"""
NEXUS V7.6 - MCP Client Module (CORTEX)

Model Context Protocol client for interacting with external MCP servers.
Zero-dependency implementation using JSON-RPC 2.0 over stdio.

Components:
- protocol.py: JSON-RPC 2.0 types (Request, Response, Tool, etc.)
- client.py: MCPClient class for subprocess communication
- registry.py: Server configuration loader

Usage:
    from core.mcp import MCPClient, MCPRegistry

    # Load configured servers
    registry = MCPRegistry(workspace_path)
    servers = registry.get_servers()

    # Connect to a server
    client = MCPClient(command=["npx", "-y", "@modelcontextprotocol/server-filesystem"])
    client.initialize()

    # List available tools
    tools = client.list_tools()

    # Call a tool
    result = client.call_tool("read_file", {"path": "/tmp/test.txt"})

    # Cleanup
    client.close()
"""

from .protocol import (
    MCPRequest,
    MCPResponse,
    MCPTool,
    MCPToolResult,
    MCPError,
    MCPCapabilities,
)
from .client import MCPClient
from .registry import MCPRegistry

__all__ = [
    "MCPRequest",
    "MCPResponse",
    "MCPTool",
    "MCPToolResult",
    "MCPError",
    "MCPCapabilities",
    "MCPClient",
    "MCPRegistry",
]
