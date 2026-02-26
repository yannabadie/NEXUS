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

import logging
import os
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

try:
    from core.memory_pkg.memory.project_memory import ProjectMemory as _ProjectMemory
except Exception:
    _ProjectMemory = None

# Configure logging to stderr (stdout is reserved for MCP JSON-RPC)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s", stream=sys.stderr)
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

_TOOL_MANAGER = None
_ORCHESTRATOR = None


def get_tool_manager():
    """Lazy load ToolManager to avoid circular imports."""
    global _TOOL_MANAGER
    if _TOOL_MANAGER is not None:
        return _TOOL_MANAGER
    from core.config import Config
    from core.execution_pkg.execution.tool_manager import ToolManager

    config = Config()
    # V8.5.0: ToolManager expects workspace_path, not config
    _TOOL_MANAGER = ToolManager(config.workspace_path)
    return _TOOL_MANAGER


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
    global _ORCHESTRATOR
    if _ORCHESTRATOR is not None:
        return _ORCHESTRATOR
    from core.config import Config
    from core.orchestration_v7 import OrchestratorV7

    config = Config()
    # V8.5.0: OrchestratorV7 requires workspace_path, config, and model info
    gemini_info = {"model": config.gemini_pro_model, "provider": "gemini"}
    claude_info = {"model": config.claude_opus_model, "provider": "claude"}
    _ORCHESTRATOR = OrchestratorV7(config.workspace_path, config, gemini_info, claude_info)
    return _ORCHESTRATOR


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _iso_now() -> str:
    return _utc_now().isoformat()


def _resolve_root(root_path: Path | None) -> Path:
    from core.config import Config

    config = Config()
    root = Path(root_path) if root_path else config.nexus_root
    return root.resolve()


def _resolve_workspace(workspace_path: Path | None) -> Path:
    from core.config import Config

    config = Config()
    workspace = Path(workspace_path) if workspace_path else config.workspace_path
    return workspace.resolve()


def _default_index_paths(root: Path) -> list[Path]:
    candidates = []
    for name in ("core", "docs"):
        candidate = root / name
        if candidate.exists():
            candidates.append(candidate)
    return candidates or [root]


def _resolve_index_paths(root: Path, paths: list[str] | None) -> list[Path]:
    if not paths:
        return _default_index_paths(root)

    resolved = []
    for raw_path in paths:
        candidate = Path(raw_path)
        if not candidate.is_absolute():
            candidate = root / candidate
        candidate = candidate.resolve()
        if not candidate.is_relative_to(root):
            raise ValueError(f"Index path must be under NEXUS root: {candidate}")
        resolved.append(candidate)
    return resolved


def _resolve_output_dir(workspace: Path, output_dir: str | None) -> Path | None:
    if output_dir is None:
        return None
    candidate = Path(output_dir)
    if not candidate.is_absolute():
        candidate = workspace / candidate
    candidate = candidate.resolve()
    if not candidate.is_relative_to(workspace):
        raise ValueError(f"Output directory must be under workspace: {candidate}")
    return candidate


def _init_memory(root: Path, backend: str):
    if _ProjectMemory is None:
        raise RuntimeError("ProjectMemory is unavailable in this environment.")
    previous_backend = os.environ.get("PROJECT_MEMORY_BACKEND")
    os.environ["PROJECT_MEMORY_BACKEND"] = backend
    try:
        return _ProjectMemory(root)
    finally:
        if previous_backend is None:
            os.environ.pop("PROJECT_MEMORY_BACKEND", None)
        else:
            os.environ["PROJECT_MEMORY_BACKEND"] = previous_backend


async def _run_blocking(func, *args, **kwargs):
    import anyio

    if kwargs:
        import functools

        func = functools.partial(func, **kwargs)
    return await anyio.to_thread.run_sync(func, *args)


def build_memory_search(
    query: str,
    root_path: Path | None = None,
    mode: str = "mock",
    backend: str | None = None,
    limit: int = 5,
    min_score: float = 0.2,
    paths: list[str] | None = None,
) -> dict[str, Any]:
    if not query or not query.strip():
        raise ValueError("Query cannot be empty.")

    mode = mode.lower()
    if mode not in {"mock", "local"}:
        raise ValueError(f"Unsupported mode: {mode}. Use 'mock' or 'local'.")

    root = _resolve_root(root_path)
    backend = backend or ("tfidf" if mode == "mock" else "auto")
    index_paths = _resolve_index_paths(root, paths)
    logger.info("build_memory_search init root=%s backend=%s", root, backend)

    memory = _init_memory(root, backend)
    indexed_chunks = 0
    for path in index_paths:
        if path.is_dir():
            indexed_chunks += memory.index_directory(path)
        elif path.is_file():
            indexed_chunks += memory.index_file(path)
    logger.info("build_memory_search indexed_chunks=%s", indexed_chunks)

    results = memory.retrieve(query, limit=limit, min_score=min_score)
    logger.info("build_memory_search results=%s", len(results))
    sources = []
    for chunk in results:
        sources.append(
            {
                "file_path": chunk.file_path,
                "start_line": chunk.start_line,
                "end_line": chunk.end_line,
                "chunk_type": chunk.chunk_type,
                "name": chunk.name,
                "terms": sorted(chunk.terms),
                "excerpt": chunk.content.strip()[:400],
            }
        )

    backend_info = memory.get_backend_info()
    backend_name = backend_info.get("backend", backend)

    return {
        "query": query,
        "mode": mode,
        "backend": backend_name,
        "generated_at": _iso_now(),
        "root_path": str(root),
        "index_paths": [str(p) for p in index_paths],
        "indexed_chunks": indexed_chunks,
        "sources": sources,
    }


def build_evidence_pack(
    question: str,
    root_path: Path | None = None,
    workspace_path: Path | None = None,
    output_dir: str | None = None,
    mode: str = "mock",
    backend: str | None = None,
    limit: int = 5,
    min_score: float = 0.2,
    paths: list[str] | None = None,
) -> dict[str, str]:
    if not question or not question.strip():
        raise ValueError("Question cannot be empty.")

    mode = mode.lower()
    if mode not in {"mock", "local"}:
        raise ValueError(f"Unsupported mode: {mode}. Use 'mock' or 'local'.")

    root = _resolve_root(root_path)
    workspace = _resolve_workspace(workspace_path)
    index_paths = _resolve_index_paths(root, paths)
    resolved_output = _resolve_output_dir(workspace, output_dir)

    from nexus_research import run_research

    outputs = run_research(
        question=question,
        root_path=root,
        output_dir=resolved_output,
        mode=mode,
        backend=backend,
        limit=limit,
        min_score=min_score,
        paths=[str(p) for p in index_paths],
    )

    return {key: str(path) for key, path in outputs.items()}


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
            logger.info("nexus_read start file_path=%s", file_path)
            result = await _run_blocking(
                execute_tool,
                "read",
                {
                    "file_path": file_path,
                    "offset": offset,
                    "limit": limit,
                },
            )
            logger.info("nexus_read done status=%s", result.status)
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
            logger.info("nexus_glob start pattern=%s path=%s", pattern, path)
            result = await _run_blocking(
                execute_tool,
                "glob",
                {
                    "pattern": pattern,
                    "path": path,
                },
            )
            logger.info("nexus_glob done status=%s", result.status)
            return result.output if result.status == "SUCCESS" else f"Error: {result.error}"
        except Exception as e:
            logger.error(f"nexus_glob error: {e}")
            return f"Error searching files: {e}"

    @mcp.tool()
    async def nexus_grep(pattern: str, path: str = ".", file_type: str | None = None, context_lines: int = 0) -> str:
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
            params = {"pattern": pattern, "path": path}
            if file_type:
                params["type"] = file_type
            if context_lines > 0:
                params["-C"] = context_lines
            result = await _run_blocking(execute_tool, "grep", params)
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
            result = await _run_blocking(orch.process_turn, task)
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
            status = await _run_blocking(orch.get_system_status)
            import json

            return json.dumps(status, indent=2, default=str)
        except Exception as e:
            logger.error(f"nexus_status error: {e}")
            return f"Error getting status: {e}"

    # =========================================================================
    # Research & Evidence Pack
    # =========================================================================

    @mcp.tool()
    async def nexus_research(
        question: str,
        mode: str = "mock",
        backend: str | None = None,
        limit: int = 5,
        min_score: float = 0.2,
        paths: list[str] | None = None,
    ) -> str:
        """
        Run a local-first research lookup over project memory.

        Returns a short summary with matched sources. Use
        nexus_export_evidence_pack to generate full artifacts.
        """
        try:
            payload = await _run_blocking(
                build_memory_search,
                query=question,
                mode=mode,
                backend=backend,
                limit=limit,
                min_score=min_score,
                paths=paths,
            )
            sources = payload.get("sources", [])
            lines = [
                "# Research Summary",
                "",
                f"Question: {payload.get('query')}",
                f"Mode: {payload.get('mode')}",
                f"Backend: {payload.get('backend')}",
                f"Generated: {payload.get('generated_at')}",
                "",
                "Sources:",
            ]
            if sources:
                for source in sources:
                    lines.append(f"- {source.get('file_path')} (L{source.get('start_line')}-{source.get('end_line')})")
            else:
                lines.append("- No sources matched the query at the current threshold.")
            return "\n".join(lines) + "\n"
        except Exception as e:
            logger.error(f"nexus_research error: {e}")
            return f"Error running research: {e}"

    @mcp.tool()
    async def nexus_memory_search(
        query: str,
        mode: str = "mock",
        backend: str | None = None,
        limit: int = 5,
        min_score: float = 0.2,
        paths: list[str] | None = None,
    ) -> str:
        """
        Search indexed project memory and return structured results.
        """
        try:
            logger.info("nexus_memory_search start query=%s", query)
            payload = await _run_blocking(
                build_memory_search,
                query=query,
                mode=mode,
                backend=backend,
                limit=limit,
                min_score=min_score,
                paths=paths,
            )
            import json

            logger.info("nexus_memory_search done sources=%s", len(payload.get("sources", [])))
            return json.dumps(payload, indent=2, ensure_ascii=True)
        except Exception as e:
            logger.error(f"nexus_memory_search error: {e}")
            return f"Error searching memory: {e}"

    @mcp.tool()
    async def nexus_export_evidence_pack(
        question: str,
        mode: str = "mock",
        backend: str | None = None,
        limit: int = 5,
        min_score: float = 0.2,
        output_dir: str | None = None,
        paths: list[str] | None = None,
    ) -> str:
        """
        Generate a full evidence pack (report, sources, trace, graph, manifest).
        """
        try:
            logger.info("nexus_export_evidence_pack start question=%s", question)
            outputs = await _run_blocking(
                build_evidence_pack,
                question=question,
                output_dir=output_dir,
                mode=mode,
                backend=backend,
                limit=limit,
                min_score=min_score,
                paths=paths,
            )
            import json

            logger.info("nexus_export_evidence_pack done output_dir=%s", outputs.get("output_dir"))
            return json.dumps(outputs, indent=2, ensure_ascii=True)
        except Exception as e:
            logger.error(f"nexus_export_evidence_pack error: {e}")
            return f"Error exporting evidence pack: {e}"

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
            result = execute_tool(
                "bash",
                {
                    "command": command,
                    "timeout": min(timeout, 120) * 1000,  # Convert to ms, cap at 120s
                },
            )
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
            from core.foundation.agents.unified_registry import get_registry

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
        raise MCPNotAvailableError("MCP SDK not installed. Install with: pip install mcp")

    logger.info("Starting NEXUS MCP Server...")
    logger.info(
        "Tools: nexus_read, nexus_glob, nexus_grep, nexus_analyze, nexus_status, "
        "nexus_research, nexus_memory_search, nexus_export_evidence_pack, nexus_bash"
    )
    logger.info("Resources: nexus://config, nexus://agents")

    # Run server with stdio transport
    mcp.run(transport="stdio")


if __name__ == "__main__":
    try:
        main()
    except MCPNotAvailableError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
