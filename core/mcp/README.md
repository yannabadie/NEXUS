# NEXUS MCP Module

## Synopsis

The **mcp** module implements the Model Context Protocol (MCP) for bidirectional agent communication. It provides both client capabilities (consuming external MCP servers) and server capabilities (exposing NEXUS as an MCP server for tools like Claude Desktop).

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        MCP ARCHITECTURE                                  │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                    NEXUS (Client Mode)                           │    │
│  │              Consumes external MCP servers                       │    │
│  └────────────────────────────┬────────────────────────────────────┘    │
│                               │                                          │
│                          MCPClient                                       │
│                               │                                          │
│  ┌────────────────────────────┴────────────────────────────────────┐    │
│  │  External MCP Servers (via MCPRegistry config)                   │    │
│  │  • @modelcontextprotocol/server-filesystem                       │    │
│  │  • @modelcontextprotocol/server-github                           │    │
│  │  • Custom servers...                                              │    │
│  └──────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  ═══════════════════════════════════════════════════════════════════════ │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                    NEXUS (Server Mode) - V9.0                    │    │
│  │              Exposes NEXUS to external clients                   │    │
│  └────────────────────────────┬────────────────────────────────────┘    │
│                               │                                          │
│                          server.py                                       │
│                               │                                          │
│  ┌────────────────────────────┴────────────────────────────────────┐    │
│  │  External Clients                                                │    │
│  │  • Claude Desktop                                                 │    │
│  │  • Other MCP-compatible tools                                     │    │
│  └──────────────────────────────────────────────────────────────────┘    │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

## Component Map

| File | Purpose | Key Exports |
|------|---------|-------------|
| `protocol.py` | JSON-RPC 2.0 types | `MCPRequest`, `MCPResponse`, `MCPTool` |
| `client.py` | Consume external servers | `MCPClient` |
| `registry.py` | Server configuration | `MCPRegistry` |
| `server.py` | Expose NEXUS as server | MCP server implementation |

## Protocol Types

```python
@dataclass
class MCPRequest:
    jsonrpc: str = "2.0"
    method: str
    params: Optional[Dict] = None
    id: Optional[str] = None

@dataclass
class MCPResponse:
    jsonrpc: str = "2.0"
    result: Optional[Any] = None
    error: Optional[MCPError] = None
    id: Optional[str] = None

@dataclass
class MCPTool:
    name: str
    description: str
    inputSchema: Dict  # JSON Schema
```

## Key Interfaces

### MCPClient
```python
class MCPClient:
    """Client for consuming external MCP servers."""

    def __init__(self, command: List[str], env: Optional[Dict] = None)
    def initialize(self) -> MCPCapabilities
    def call_tool(self, name: str, arguments: Dict) -> MCPToolResult
    def list_tools(self) -> List[MCPTool]
    def close(self) -> None
```

### MCPRegistry
```python
class MCPRegistry:
    """Loads server configurations from mcp_servers.json."""

    def __init__(self, workspace_path: Path)
    def get_server(self, name: str) -> MCPServerConfig
    def list_servers(self) -> List[str]
```

## Client Usage

```python
from core.mcp import MCPClient, MCPRegistry

# Via registry (recommended)
registry = MCPRegistry(workspace_path)
config = registry.get_server("filesystem")
client = MCPClient(**config)

# Direct usage
client = MCPClient(
    command=["npx", "-y", "@modelcontextprotocol/server-filesystem"],
    env={"MCP_ROOT": "/tmp"}
)
client.initialize()

# Call tool
result = client.call_tool("read_file", {"path": "/tmp/test.txt"})
print(result.content)

# Cleanup
client.close()
```

## Server Mode (V9.0)

Run NEXUS as an MCP server:

```bash
python -m core.mcp.server
```

Configure in Claude Desktop (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "nexus": {
      "command": "python",
      "args": ["-m", "core.mcp.server"],
      "cwd": "/path/to/nexus"
    }
  }
}
```

## Registry Configuration

`workspace/mcp_servers.json`:

```json
{
  "servers": {
    "filesystem": {
      "command": ["npx", "-y", "@modelcontextprotocol/server-filesystem"],
      "env": {"MCP_ROOT": "/workspace"}
    },
    "github": {
      "command": ["npx", "-y", "@modelcontextprotocol/server-github"],
      "env": {"GITHUB_TOKEN": "${GITHUB_TOKEN}"}
    }
  }
}
```

## Dependencies

### External
- `mcp` - MCP SDK (optional, for server mode)
- Standard library (subprocess, json)

## Version History

- **V8.0** - MCPClient for external server consumption
- **V9.0** - MCPServer for exposing NEXUS
- **V12.4** - Enhanced registry, tool schema validation
