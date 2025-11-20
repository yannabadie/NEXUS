# MCP Server Skeleton

A production-ready Model Context Protocol (MCP) server implementation using stdio transport.

## Features

- ✅ Standard MCP protocol implementation
- ✅ Stdio transport for cross-platform compatibility
- ✅ Modular tool architecture
- ✅ Comprehensive logging
- ✅ Error handling and recovery
- ✅ Sample calculator tool with 6 operations

## Installation

1. **Install dependencies**:
```bash
pip install -r requirements.txt
```

2. **Verify installation**:
```bash
python -c "import mcp; print(f'MCP version: {mcp.__version__}')"
```

## Running the Server

### Standalone Mode (for testing)
```bash
python server.py
```

### With Claude Desktop

1. **Add to Claude configuration** (`%APPDATA%\Claude\claude_desktop_config.json` on Windows):
```json
{
  "mcpServers": {
    "nexus-calculator": {
      "command": "python",
      "args": ["C:/Users/yann.abadie/OneDrive - GIE AD BRIVE/Documents/Projets/MES/20_NEXUS/03_AGENTS/mcp_skeleton/server.py"],
      "cwd": "C:/Users/yann.abadie/OneDrive - GIE AD BRIVE/Documents/Projets/MES/20_NEXUS/03_AGENTS/mcp_skeleton"
    }
  }
}
```

2. **Restart Claude Desktop**

3. **Verify connection** - In Claude, you should see the calculator tools available

## Architecture

```
mcp_skeleton/
├── server.py           # Main server implementation
├── tools/              # Tool modules
│   ├── __init__.py    # (optional) Package init
│   └── calculator.py   # Sample calculator tool
├── requirements.txt    # Dependencies
├── README.md          # This file
└── mcp_server.log     # Runtime logs (generated)
```

## License

This skeleton is provided as-is for the NEXUS project.

---

*MCP Server Skeleton v1.0*
*Part of NEXUS 2.0 Architecture*
