#!/usr/bin/env python3
"""
MCP Server - SSE Transport Version
Stable Windows implementation using HTTP/SSE instead of stdio pipes
"""

import asyncio
import logging
from pathlib import Path
from typing import Any, Dict, List
import sys
import uvicorn
from starlette.applications import Starlette
from starlette.routing import Route
from starlette.responses import JSONResponse, Response

# Add local tools to path
sys.path.insert(0, str(Path(__file__).parent))

# MCP imports
from mcp.server import Server
from mcp.server.sse import SseServerTransport
from mcp.types import Tool, TextContent, CallToolResult

# Import custom tools
from tools.calculator import CalculatorTool

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('mcp_server_sse.log')
    ]
)
logger = logging.getLogger(__name__)

class MCPSSEHandler(Response):
    """
    Custom Starlette Response that delegates to the MCP SSE transport.
    This bridges the gap between Starlette's Response object and MCP's ASGI implementation.
    """
    def __init__(self, server: Server, transport: SseServerTransport):
        # Properly initialize the parent Response
        super().__init__(content=b"", status_code=200)
        self.server = server
        self.transport = transport

    async def __call__(self, scope, receive, send):
        # Delegate to mcp.server.sse.connect_sse context manager
        async with self.transport.connect_sse(scope, receive, send) as streams:
            read_stream, write_stream = streams
            logger.info("SSE connection established")
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options()
            )

class MCPMessageHandler(Response):
    """
    Custom Starlette Response for handling POST messages.
    Delegates to transport.handle_post_message.
    """
    def __init__(self, transport: SseServerTransport):
        super().__init__(content=b"", status_code=200)
        self.transport = transport

    async def __call__(self, scope, receive, send):
        await self.transport.handle_post_message(scope, receive, send)


class MCPServerSSE:
    """MCP Server with SSE transport for Windows stability"""

    def __init__(self):
        self.server = Server("nexus-mcp-server-sse")
        self.tools: Dict[str, Any] = {}
        
        # Initialize the transport ONCE so it retains session state
        self.transport = SseServerTransport("/mcp/v1/sse")
        
        self._initialize_tools()
        self._register_handlers()
        logger.info("MCP SSE Server initialized")

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
                logger.info(f"Tool {name} executed successfully: {result}")
                return CallToolResult(
                    content=[TextContent(type="text", text=str(result))]
                )

            except Exception as e:
                error_msg = f"Error executing tool {name}: {str(e)}"
                logger.error(error_msg, exc_info=True)
                return CallToolResult(
                    content=[TextContent(type="text", text=error_msg)],
                    isError=True
                )

    async def handle_sse(self, request):
        """Handle SSE connection and messages for MCP protocol"""
        if request.method == "GET":
            logger.info("Handling SSE Connection (GET)")
            return MCPSSEHandler(self.server, self.transport)
        
        elif request.method == "POST":
            logger.info("Handling SSE Message (POST)")
            return MCPMessageHandler(self.transport)
        
        else:
            return JSONResponse({"error": "Method not allowed"}, status_code=405)


# Global server instance
mcp_server = MCPServerSSE()


# Create Starlette app
app = Starlette(
    debug=True,
    routes=[
        # Health check endpoint
        Route("/health",
              endpoint=lambda request: JSONResponse({"status": "ok", "service": "MCP SSE Server"}),
              methods=["GET"]),

        # MCP SSE endpoint (Handles both GET and POST)
        Route("/mcp/v1/sse",
              endpoint=mcp_server.handle_sse,
              methods=["GET", "POST"]),
    ]
)


@app.on_event("startup")
async def startup_event():
    """Server startup event"""
    logger.info("=" * 60)
    logger.info("MCP SSE Server Starting")
    logger.info(f"Tools available: {list(mcp_server.tools.keys())}")
    logger.info("Server ready at http://localhost:8000")
    logger.info("MCP endpoint: http://localhost:8000/mcp/v1/sse")
    logger.info("=" * 60)


@app.on_event("shutdown")
async def shutdown_event():
    """Server shutdown event"""
    logger.info("MCP SSE Server shutting down")


if __name__ == "__main__":
    # Run with uvicorn
    config = uvicorn.Config(
        app,
        host="127.0.0.1",
        port=8000,
        log_level="info",
        access_log=True,
        use_colors=True,
        # Important for Windows
        reload=False,
        workers=1
    )

    server = uvicorn.Server(config)

    try:
        asyncio.run(server.serve())
    except KeyboardInterrupt:
        logger.info("Server interrupted by user")
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
