"""
NEXUS V9.0 - MCP Module (Client + Server)

Model Context Protocol support for bidirectional agent communication.

Components:
- protocol.py: JSON-RPC 2.0 types (Request, Response, Tool, etc.)
- client.py: MCPClient class for consuming external MCP servers
- registry.py: Server configuration loader
- server.py: V9.0 - NEXUS as MCP Server (for Claude Desktop, etc.)

Usage (Client - consume external servers):
    from core.mcp import MCPClient, MCPRegistry

    registry = MCPRegistry(workspace_path)
    client = MCPClient(command=["npx", "-y", "@modelcontextprotocol/server-filesystem"])
    client.initialize()
    result = client.call_tool("read_file", {"path": "/tmp/test.txt"})

Usage (Server - expose NEXUS to external clients):
    # Run NEXUS as MCP server:
    python -m core.mcp.server

    # Configure in Claude Desktop (claude_desktop_config.json):
    {
        "mcpServers": {
            "nexus": {
                "command": "python",
                "args": ["-m", "core.mcp.server"],
                "cwd": "/path/to/nexus"
            }
        }
    }
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

# V9.0: Server exports (optional - only if MCP SDK installed)
try:
    from .server import MCP_AVAILABLE as MCP_SERVER_AVAILABLE
except ImportError:
    MCP_SERVER_AVAILABLE = False

__all__ = [
    # Protocol types
    "MCPRequest",
    "MCPResponse",
    "MCPTool",
    "MCPToolResult",
    "MCPError",
    "MCPCapabilities",
    # Client
    "MCPClient",
    "MCPRegistry",
    # Server (V9.0)
    "MCP_SERVER_AVAILABLE",
]
