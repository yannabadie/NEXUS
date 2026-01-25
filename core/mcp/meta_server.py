"""
NEXUS Meta GraphRAG MCP Server - exposes Meta GraphRAG tools only.

Usage:
    python -m core.mcp.meta_server
"""

from __future__ import annotations

import sys
import os
import logging
from typing import Optional, List

# Configure logging to stderr (stdout is reserved for MCP JSON-RPC)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stderr
)
logger = logging.getLogger("nexus.mcp.meta")

# Check for MCP SDK availability
try:
    from mcp.server.fastmcp import FastMCP
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    logger.warning("MCP SDK not installed. Install with: pip install mcp")

from core.mcp.server import (  # reuse shared helpers
    build_meta_graphrag_query,
    build_meta_graphrag_status,
    build_meta_graphrag_reports,
    reset_meta_graphrag_indexer,
    _run_blocking,
    MCPNotAvailableError,
)


if MCP_AVAILABLE:
    mcp = FastMCP("nexus-meta-graphrag")

    @mcp.tool()
    async def nexus_meta_graphrag_query(
        query: str,
        seed_limit: Optional[int] = None,
        expansion_depth: Optional[int] = None,
        expansion_limit: Optional[int] = None,
        include_text: bool = False,
    ) -> str:
        """
        Query the Meta GraphRAG index (vector search + graph expansion).
        """
        try:
            payload = await _run_blocking(
                build_meta_graphrag_query,
                query=query,
                seed_limit=seed_limit,
                expansion_depth=expansion_depth,
                expansion_limit=expansion_limit,
                include_text=include_text,
            )
            import json
            return json.dumps(payload, indent=2, ensure_ascii=True)
        except Exception as exc:
            logger.error("nexus_meta_graphrag_query error: %s", exc)
            return f"Error querying meta GraphRAG: {exc}"

    @mcp.tool()
    async def nexus_meta_graphrag_status(fast: bool = True) -> str:
        """
        Return Meta GraphRAG index status.
        """
        try:
            payload = await _run_blocking(build_meta_graphrag_status, fast=fast)
            import json
            return json.dumps(payload, indent=2, ensure_ascii=True)
        except Exception as exc:
            logger.error("nexus_meta_graphrag_status error: %s", exc)
            return f"Error fetching meta GraphRAG status: {exc}"

    @mcp.tool()
    async def nexus_meta_graphrag_reports(
        entrypoints: Optional[List[str]] = None,
        include_content: bool = False,
        fast: bool = True,
    ) -> str:
        """
        Generate and return Meta GraphRAG reports (overview/top-down/bottom-up).
        """
        try:
            payload = await _run_blocking(
                build_meta_graphrag_reports,
                entrypoints=entrypoints,
                include_content=include_content,
                fast=fast,
            )
            import json
            return json.dumps(payload, indent=2, ensure_ascii=True)
        except Exception as exc:
            logger.error("nexus_meta_graphrag_reports error: %s", exc)
            return f"Error generating meta GraphRAG reports: {exc}"

    @mcp.tool()
    async def nexus_meta_graphrag_reload() -> str:
        """
        Reset cached Meta GraphRAG indexer (use after reindex).
        """
        try:
            await _run_blocking(reset_meta_graphrag_indexer)
            return "Meta GraphRAG cache reset."
        except Exception as exc:
            logger.error("nexus_meta_graphrag_reload error: %s", exc)
            return f"Error resetting meta GraphRAG cache: {exc}"


def main() -> None:
    """
    Run Meta GraphRAG MCP server (stdio).
    """
    if not MCP_AVAILABLE:
        raise MCPNotAvailableError(
            "MCP SDK not installed. Install with: pip install mcp"
        )

    if os.name == "nt":
        try:
            import asyncio
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        except Exception as exc:
            logger.debug("MCP stdio event loop policy setup failed: %s", exc)

    logger.info("Starting NEXUS Meta GraphRAG MCP Server...")
    logger.info(
        "Tools: nexus_meta_graphrag_query, nexus_meta_graphrag_status, "
        "nexus_meta_graphrag_reports, nexus_meta_graphrag_reload"
    )

    mcp.run(transport="stdio")


if __name__ == "__main__":
    try:
        main()
    except MCPNotAvailableError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
