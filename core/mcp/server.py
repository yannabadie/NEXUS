"""
NEXUS V9.0 MCP Server - Expose NEXUS as a Tool for External Agents

This module implements NEXUS as an MCP (Model Context Protocol) server,
allowing Claude Desktop, VSCode, and other MCP clients to invoke NEXUS
capabilities.

Usage:
    # As a standalone server (stdio transport):
    python -m core.mcp.server

    # In Claude Desktop config:
    {
        "mcpServers": {
            "nexus": {
                "command": "python",
                "args": ["-m", "core.mcp.server"],
                "cwd": "/path/to/nexus"
            }
        }
    }

Reference: https://modelcontextprotocol.io/quickstart/server
"""

import sys
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List

# Configure logging to stderr (stdout is reserved for MCP JSON-RPC)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stderr
)
logger = logging.getLogger("nexus.mcp.server")

# Check for MCP SDK availability
try:
    from mcp.server.fastmcp import FastMCP
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    logger.warning("MCP SDK not installed. Install with: pip install mcp")


# =============================================================================
# NEXUS Tool Imports (lazy loading to avoid circular imports)
# =============================================================================

def get_tool_manager():
    """Lazy load ToolManager to avoid circular imports."""
    from core.execution.tool_manager import ToolManager
    from core.config import Config
    config = Config()
    # V8.5.0: ToolManager expects workspace_path, not config
    return ToolManager(config.workspace_path)


def execute_tool(tool_name: str, params: dict):
    """
    Helper to execute a tool via ToolManager.

    V8.5.0: Wraps ToolManager.execute() with ToolUse object creation.
    """
    from core.synapse.protocol_v7 import ToolUse
    tm = get_tool_manager()
    tool_request = ToolUse(tool_name=tool_name, arguments=params)
    return tm.execute(tool_request)


def get_orchestrator():
    """Lazy load Orchestrator for complex tasks."""
    from core.orchestration_v7 import OrchestratorV7
    from core.config import Config
    config = Config()
    # V8.5.0: OrchestratorV7 requires workspace_path, config, and model info
    gemini_info = {"model": config.gemini_pro_model, "provider": "gemini"}
    claude_info = {"model": config.claude_opus_model, "provider": "claude"}
    return OrchestratorV7(config.workspace_path, config, gemini_info, claude_info)


# =============================================================================
# MCP Server Definition
# =============================================================================

if MCP_AVAILABLE:
    # Initialize FastMCP server
    mcp = FastMCP("nexus")

    # =========================================================================
    # File Operations
    # =========================================================================

    @mcp.tool()
    async def nexus_read(file_path: str, offset: int = 0, limit: int = 500) -> str:
        """
        Read file contents from the NEXUS workspace.

        Args:
            file_path: Path to the file (relative to workspace or absolute)
            offset: Line number to start reading from (0-based)
            limit: Maximum number of lines to read

        Returns:
            File contents as a string with line numbers
        """
        try:
            result = execute_tool("read", {
                "file_path": file_path,
                "offset": offset,
                "limit": limit
            })
            return result.output if result.status == "SUCCESS" else f"Error: {result.error}"
        except Exception as e:
            logger.error(f"nexus_read error: {e}")
            return f"Error reading file: {e}"

    @mcp.tool()
    async def nexus_glob(pattern: str, path: str = ".") -> str:
        """
        Find files matching a glob pattern.

        Args:
            pattern: Glob pattern (e.g., "**/*.py", "src/**/*.ts")
            path: Directory to search in (default: current directory)

        Returns:
            List of matching file paths
        """
        try:
            result = execute_tool("glob", {
                "pattern": pattern,
                "path": path
            })
            return result.output if result.status == "SUCCESS" else f"Error: {result.error}"
        except Exception as e:
            logger.error(f"nexus_glob error: {e}")
            return f"Error searching files: {e}"

    @mcp.tool()
    async def nexus_grep(
        pattern: str,
        path: str = ".",
        file_type: Optional[str] = None,
        context_lines: int = 0
    ) -> str:
        """
        Search for patterns in files using ripgrep-style regex.

        Args:
            pattern: Regex pattern to search for
            path: Directory or file to search in
            file_type: Filter by file type (e.g., "py", "js", "ts")
            context_lines: Number of context lines before/after match

        Returns:
            Matching lines with file paths and line numbers
        """
        try:
            params = {
                "pattern": pattern,
                "path": path
            }
            if file_type:
                params["type"] = file_type
            if context_lines > 0:
                params["-C"] = context_lines

            result = execute_tool("grep", params)
            return result.output if result.status == "SUCCESS" else f"Error: {result.error}"
        except Exception as e:
            logger.error(f"nexus_grep error: {e}")
            return f"Error searching: {e}"

    # =========================================================================
    # Code Analysis
    # =========================================================================

    @mcp.tool()
    async def nexus_analyze(task: str) -> str:
        """
        Analyze a coding task using NEXUS multi-agent collaboration.

        This invokes NEXUS's brainstorming mode where Gemini and Claude
        collaborate to analyze and solve the task.

        Args:
            task: Description of the task or question to analyze

        Returns:
            Analysis result from the collaborative agents
        """
        try:
            orch = get_orchestrator()
            result = orch.process_turn(task)
            return result.get("response", "No response generated")
        except Exception as e:
            logger.error(f"nexus_analyze error: {e}")
            return f"Error analyzing task: {e}"

    @mcp.tool()
    async def nexus_status() -> str:
        """
        Get current NEXUS system status.

        Returns:
            JSON string with FSM state, active agent, memory stats
        """
        try:
            orch = get_orchestrator()
            status = orch.get_system_status()
            import json
            return json.dumps(status, indent=2, default=str)
        except Exception as e:
            logger.error(f"nexus_status error: {e}")
            return f"Error getting status: {e}"

    # =========================================================================
    # Shell Execution (sandboxed)
    # =========================================================================

    @mcp.tool()
    async def nexus_bash(command: str, timeout: int = 30) -> str:
        """
        Execute a shell command in the NEXUS workspace (sandboxed).

        Security: Commands are validated by ExecutionPolicy before execution.
        Dangerous commands (rm -rf, etc.) are blocked.

        Args:
            command: Shell command to execute
            timeout: Timeout in seconds (default 30, max 120)

        Returns:
            Command output (stdout + stderr)
        """
        try:
            result = execute_tool("bash", {
                "command": command,
                "timeout": min(timeout, 120) * 1000  # Convert to ms, cap at 120s
            })
            return result.output if result.status == "SUCCESS" else f"Error: {result.error}"
        except Exception as e:
            logger.error(f"nexus_bash error: {e}")
            return f"Error executing command: {e}"

    # =========================================================================
    # Resources (optional - for exposing project context)
    # =========================================================================

    @mcp.resource("nexus://config")
    async def get_nexus_config() -> str:
        """Get NEXUS configuration summary."""
        try:
            from core.config import Config
            config = Config()
            return config.to_string()
        except Exception as e:
            return f"Error loading config: {e}"

    @mcp.resource("nexus://agents")
    async def get_nexus_agents() -> str:
        """Get registered agent information."""
        try:
            from core.agents.unified_registry import get_registry
            registry = get_registry()
            agents = registry.list_agents()
            import json
            return json.dumps(agents, indent=2, default=str)
        except Exception as e:
            return f"Error loading agents: {e}"


# =============================================================================
# Server Entry Point
# =============================================================================

class MCPNotAvailableError(RuntimeError):
    """Raised when MCP SDK is not installed."""
    pass


def main():
    """
    Run NEXUS MCP server.

    V9.8 DETOX: Raises MCPNotAvailableError instead of sys.exit()
    for proper exception handling when imported as a module.
    """
    if not MCP_AVAILABLE:
        raise MCPNotAvailableError(
            "MCP SDK not installed. Install with: pip install mcp"
        )

    logger.info("Starting NEXUS MCP Server...")
    logger.info("Tools: nexus_read, nexus_glob, nexus_grep, nexus_analyze, nexus_status, nexus_bash")
    logger.info("Resources: nexus://config, nexus://agents")

    # Run server with stdio transport
    mcp.run(transport='stdio')


if __name__ == "__main__":
    try:
        main()
    except MCPNotAvailableError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
