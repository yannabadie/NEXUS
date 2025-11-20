#!/usr/bin/env python3
"""
MCP Server - Production Skeleton
Model Context Protocol server implementation with stdio transport
"""

import asyncio
import json
import sys
import logging
from typing import Any, Dict, List, Optional
from pathlib import Path

# Add local tools to path
sys.path.insert(0, str(Path(__file__).parent))

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent, CallToolResult

# Import custom tools
from tools.calculator import CalculatorTool

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler('mcp_server.log')]
)
logger = logging.getLogger(__name__)


class MCPServer:
    """Production MCP Server with tool management"""

    def __init__(self):
        self.server = Server("nexus-mcp-server")
        self.tools: Dict[str, Any] = {}
        self._initialize_tools()
        self._register_handlers()

    def _initialize_tools(self):
        """Initialize and register available tools"""
        # Register calculator tool
        calc_tool = CalculatorTool()
        self.tools["calculator"] = calc_tool

        logger.info(f"Initialized {len(self.tools)} tools")

    def _register_handlers(self):
        """Register MCP protocol handlers"""

        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            """List all available tools"""
            tools = []
            for name, tool_instance in self.tools.items():
                tools.extend(tool_instance.get_tools())
            logger.info(f"Listed {len(tools)} tools")
            return tools

        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> CallToolResult:
            """Execute a tool with given arguments"""
            logger.info(f"Calling tool: {name} with args: {arguments}")

            # Find the tool
            tool_name = name.split(".")[0] if "." in name else name
            if tool_name not in self.tools:
                error_msg = f"Tool '{tool_name}' not found"
                logger.error(error_msg)
                return CallToolResult(
                    content=[TextContent(type="text", text=error_msg)],
                    isError=True
                )

            try:
                # Execute the tool
                tool_instance = self.tools[tool_name]
                result = await tool_instance.execute(name, arguments)
                logger.info(f"Tool {name} executed successfully")
                return CallToolResult(content=[TextContent(type="text", text=str(result))])

            except Exception as e:
                error_msg = f"Error executing tool {name}: {str(e)}"
                logger.error(error_msg, exc_info=True)
                return CallToolResult(
                    content=[TextContent(type="text", text=error_msg)],
                    isError=True
                )

    async def run(self):
        """Run the MCP server with stdio transport"""
        logger.info("Starting MCP server with stdio transport")

        # Use stdio_server context manager
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(read_stream, write_stream)

        logger.info("MCP server stopped")


async def main():
    """Main entry point"""
    try:
        server = MCPServer()
        await server.run()
    except KeyboardInterrupt:
        logger.info("Server interrupted by user")
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
