# Companion: NEXUS MCP Server

## Overview
The companion product exposes NEXUS capabilities via the Model Context Protocol (MCP), enabling external tools to call research, memory search, and evidence pack export without direct access to the codebase. It targets dev teams integrating NEXUS into IDEs or CI workflows.

## Quickstart
Install the MCP SDK (server mode only):
```bash
python -m pip install mcp
```

Run the server (stdio transport):
```bash
python -m core.mcp.server
```

Demo script (spawns server and calls tools via MCP client):
```bash
powershell -ExecutionPolicy Bypass -File scripts/demo_companion.ps1
```

## Tools Exposed
- `nexus_research`: markdown summary from project memory.
- `nexus_memory_search`: JSON payload with matched chunks and metadata.
- `nexus_export_evidence_pack`: writes `report.md`, `sources.json`, `trace.jsonl`, `reasoning_graph.mmd`, `manifest.sha256`.
- Existing tools: `nexus_status`, `nexus_read`, `nexus_glob`, `nexus_grep`, `nexus_analyze`, `nexus_bash`.

## Configuration Example
Claude Desktop config:
```json
{
  "mcpServers": {
    "nexus": {
      "command": "python",
      "args": ["-m", "core.mcp.server"],
      "cwd": "/path/to/NEXUS"
    }
  }
}
```

## Notes
- Evidence pack outputs are restricted to `WORKSPACE_PATH` for safety.
- Index paths must live under `NEXUS_ROOT`.

## Tests
```bash
python -m pytest tests/test_mcp_companion.py -v
```
