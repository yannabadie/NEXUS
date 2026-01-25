"""MCP smoke test for Meta GraphRAG tools."""

from __future__ import annotations

import os
from pathlib import Path

from core.mcp.client import MCPClient


def main() -> int:
    require_mcp = os.getenv("NEXUS_MCP_SMOKE_REQUIRE", "1").lower() in {"1", "true", "yes", "on"}
    try:
        import mcp  # noqa: F401
    except ImportError:
        message = "MCP SDK not installed; install with: pip install mcp"
        if require_mcp:
            print(message)
            return 1
        print(f"{message} (skipping)")
        return 0

    client = MCPClient(command=["python", "-m", "core.mcp.server"], cwd=Path(os.getcwd()))
    client.start()
    client.initialize()
    try:
        client.call_tool("nexus_meta_graphrag_status", {"fast": True})
        client.call_tool("nexus_meta_graphrag_reports", {"fast": True})
    finally:
        client.close()
    print("MCP smoke OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
