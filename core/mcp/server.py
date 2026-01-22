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
import os
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, Any, List, Callable, TypeVar

T = TypeVar('T')

try:
    from core.memory.project_memory import ProjectMemory as _ProjectMemory
except Exception:
    _ProjectMemory = None

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

_TOOL_MANAGER = None
_ORCHESTRATOR = None
_META_GRAPHRAG_INDEXER = None


def get_tool_manager():
    """Lazy load ToolManager to avoid circular imports."""
    global _TOOL_MANAGER
    if _TOOL_MANAGER is not None:
        return _TOOL_MANAGER
    from core.execution.tool_manager import ToolManager
    from core.config import Config
    config = Config()
    # V8.5.0: ToolManager expects workspace_path, not config
    _TOOL_MANAGER = ToolManager(config.workspace_path)
    return _TOOL_MANAGER


def execute_tool(tool_name: str, params: Dict[str, Any]) -> Any:
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
    from core.orchestration_v7 import OrchestratorV7
    from core.config import Config
    config = Config()
    # V8.5.0: OrchestratorV7 requires workspace_path, config, and model info
    gemini_info = {"model": config.gemini_pro_model, "provider": "gemini"}
    claude_info = {"model": config.claude_opus_model, "provider": "claude"}
    _ORCHESTRATOR = OrchestratorV7(config.workspace_path, config, gemini_info, claude_info)
    return _ORCHESTRATOR


def get_meta_graphrag_indexer():
    """Lazy load Meta GraphRAG indexer for MCP queries."""
    global _META_GRAPHRAG_INDEXER
    if _META_GRAPHRAG_INDEXER is not None:
        return _META_GRAPHRAG_INDEXER
    from tools.meta_graph_rag.config import load_config
    from tools.meta_graph_rag.indexer import MetaGraphIndexer
    config = load_config()
    _META_GRAPHRAG_INDEXER = MetaGraphIndexer(config)
    return _META_GRAPHRAG_INDEXER


def reset_meta_graphrag_indexer() -> None:
    """Reset cached Meta GraphRAG indexer (for refresh after reindex)."""
    global _META_GRAPHRAG_INDEXER
    _META_GRAPHRAG_INDEXER = None


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _iso_now() -> str:
    return _utc_now().isoformat()


def _resolve_root(root_path: Optional[Path]) -> Path:
    from core.config import Config
    config = Config()
    root = Path(root_path) if root_path else config.nexus_root
    return root.resolve()


def _resolve_workspace(workspace_path: Optional[Path]) -> Path:
    from core.config import Config
    config = Config()
    workspace = Path(workspace_path) if workspace_path else config.workspace_path
    return workspace.resolve()


def _format_meta_chunk(chunk, include_text: bool = False) -> Dict[str, Any]:
    payload = {
        "path": chunk.path,
        "start_line": chunk.start_line,
        "end_line": chunk.end_line,
        "kind": chunk.kind,
        "node_id": chunk.node_id,
        "security_tags": chunk.metadata.get("security_tags", ""),
        "source_type": chunk.metadata.get("source_type", ""),
    }
    if include_text:
        payload["text"] = chunk.text
    else:
        payload["excerpt"] = chunk.text[:400]
    return payload


def build_meta_graphrag_query(
    query: str,
    seed_limit: Optional[int] = None,
    expansion_depth: Optional[int] = None,
    expansion_limit: Optional[int] = None,
    include_text: bool = False,
) -> Dict[str, Any]:
    """Run a Meta GraphRAG query with optional graph expansion."""
    if not query or not query.strip():
        raise ValueError("Query cannot be empty.")

    indexer = get_meta_graphrag_indexer()
    seed_limit = seed_limit if seed_limit is not None else indexer.config.query_seed_limit
    expansion_depth = (
        expansion_depth if expansion_depth is not None else indexer.config.query_expansion_depth
    )
    expansion_limit = (
        expansion_limit if expansion_limit is not None else indexer.config.query_expansion_limit
    )

    if seed_limit < 0:
        seed_limit = 0
    if expansion_depth < 0:
        expansion_depth = 0
    if expansion_limit < 0:
        expansion_limit = 0

    seed_records = indexer.vector_index.query(query, limit=seed_limit)
    seed_chunks = []
    for record in seed_records:
        chunk = indexer.chunks.chunks.get(record.chunk_id)
        if chunk:
            seed_chunks.append(chunk)

    expanded_chunks = []
    if expansion_depth > 0 and expansion_limit > 0 and seed_chunks:
        from tools.meta_graph_rag.indexer import _expand_nodes

        adjacency = indexer.graph.build_adjacency()
        expanded_nodes = []
        for chunk in seed_chunks:
            expanded_nodes.extend(_expand_nodes(adjacency, chunk.node_id, expansion_depth))
        expanded_nodes = list(dict.fromkeys(expanded_nodes))
        seed_chunk_ids = {chunk.chunk_id for chunk in seed_chunks}
        for node_id in expanded_nodes:
            for chunk in indexer.chunks.get_by_node(node_id):
                if chunk.chunk_id in seed_chunk_ids:
                    continue
                expanded_chunks.append(chunk)
                if len(expanded_chunks) >= expansion_limit:
                    break
            if len(expanded_chunks) >= expansion_limit:
                break

    return {
        "query": query,
        "generated_at": _iso_now(),
        "seed_limit": seed_limit,
        "expansion_depth": expansion_depth,
        "expansion_limit": expansion_limit,
        "seed_count": len(seed_chunks),
        "expanded_count": len(expanded_chunks),
        "seed_chunks": [_format_meta_chunk(chunk, include_text) for chunk in seed_chunks],
        "expanded_chunks": [_format_meta_chunk(chunk, include_text) for chunk in expanded_chunks],
    }


def build_meta_graphrag_status() -> Dict[str, Any]:
    """Return Meta GraphRAG index status."""
    indexer = get_meta_graphrag_indexer()
    return indexer.status()


def build_meta_graphrag_reports(
    entrypoints: Optional[List[str]] = None,
    include_content: bool = False,
) -> Dict[str, Any]:
    """Generate and return Meta GraphRAG reports."""
    indexer = get_meta_graphrag_indexer()
    status = indexer.status()
    from tools.meta_graph_rag.reports import generate_reports

    paths = generate_reports(
        graph=indexer.graph,
        chunks_count=status["chunks"],
        vector_count=status["vector_entries"],
        output_dir=indexer.config.reports_path,
        entrypoints=entrypoints,
    )
    payload = {
        "generated_at": _iso_now(),
        "paths": {
            "overview": str(paths.overview),
            "top_down": str(paths.top_down),
            "bottom_up": str(paths.bottom_up),
            "security": str(paths.security),
            "module_catalog": str(paths.module_catalog),
        },
    }
    if include_content:
        payload["reports"] = {
            "overview": paths.overview.read_text(encoding="utf-8", errors="ignore"),
            "top_down": paths.top_down.read_text(encoding="utf-8", errors="ignore"),
            "bottom_up": paths.bottom_up.read_text(encoding="utf-8", errors="ignore"),
            "security": paths.security.read_text(encoding="utf-8", errors="ignore"),
            "module_catalog": paths.module_catalog.read_text(encoding="utf-8", errors="ignore"),
        }
    return payload


def _default_index_paths(root: Path) -> List[Path]:
    """
    Determines the default paths to index if none are specified.

    Checks for the existence of standard directories ('core', 'docs') within
    the root. If found, they are returned. If neither exists, the root
    directory itself is returned.

    Args:
        root: The absolute path to the project root directory.

    Returns:
        A list of Path objects representing the default directories to index.
    """
    candidates = []
    for name in ("core", "docs"):
        candidate = root / name
        if candidate.exists():
            candidates.append(candidate)
    return candidates or [root]


def _resolve_index_paths(root: Path, paths: Optional[List[str]]) -> List[Path]:
    """
    Resolves a list of index paths relative to the project root.

    If no paths are provided, defaults to standard index locations (e.g. 'core', 'docs')
    or the root itself if those don't exist.

    Args:
        root: The absolute path to the project root directory.
        paths: A list of file or directory paths to resolve. Can be absolute or
            relative to the root.

    Returns:
        A list of resolved Path objects.

    Raises:
        ValueError: If a resolved path is not located under the project root.
    """
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


def _resolve_output_dir(workspace: Path, output_dir: Optional[str]) -> Optional[Path]:
    """
    Resolves the output directory path relative to the workspace.

    Args:
        workspace: The absolute path to the workspace directory.
        output_dir: The path to the output directory. Can be absolute or
            relative to the workspace. If None, returns None.

    Returns:
        The resolved absolute Path object for the output directory, or None
        if output_dir was not provided.

    Raises:
        ValueError: If the resolved output directory is not located under the
            workspace directory.
    """
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
    """
    Initialize the ProjectMemory instance with a specific backend.

    This function temporarily sets the 'PROJECT_MEMORY_BACKEND' environment
    variable to the specified backend before initializing ProjectMemory.
    It ensures the environment variable is restored to its original state
    after initialization.

    Args:
        root: The absolute path to the project root directory.
        backend: The name of the memory backend to use (e.g., 'tfidf', 'chroma').

    Returns:
        An instance of ProjectMemory initialized with the specified root and backend.

    Raises:
        RuntimeError: If the ProjectMemory class is not available.
    """
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


async def _run_blocking(func: Callable[..., T], *args, **kwargs) -> T:
    import anyio
    if kwargs:
        import functools
        func = functools.partial(func, **kwargs)
    return await anyio.to_thread.run_sync(func, *args)


def build_memory_search(
    query: str,
    root_path: Optional[Path] = None,
    mode: str = "mock",
    backend: Optional[str] = None,
    limit: int = 5,
    min_score: float = 0.2,
    paths: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Builds a memory search result from the project's indexed memory.

    Args:
        query: The search query string.
        root_path: Optional root path for the project. Defaults to configured root.
        mode: Search mode, either "mock" or "local". Defaults to "mock".
        backend: Search backend (e.g., "tfidf", "chroma"). Defaults to "tfidf" for mock mode, "auto" otherwise.
        limit: Maximum number of results to return. Defaults to 5.
        min_score: Minimum relevance score for results. Defaults to 0.2.
        paths: Optional list of specific paths to search within.

    Returns:
        A dictionary containing the search results, metadata, and matched sources.
        The dictionary includes keys like 'query', 'mode', 'backend', 'generated_at',
        'root_path', 'index_paths', 'indexed_chunks', and 'sources'.

    Raises:
        ValueError: If the query is empty or if an unsupported mode is specified.
        RuntimeError: If ProjectMemory is unavailable.
    """
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
        sources.append({
            "file_path": chunk.file_path,
            "start_line": chunk.start_line,
            "end_line": chunk.end_line,
            "chunk_type": chunk.chunk_type,
            "name": chunk.name,
            "terms": sorted(chunk.terms),
            "excerpt": chunk.content.strip()[:400],
        })

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
    root_path: Optional[Path] = None,
    workspace_path: Optional[Path] = None,
    output_dir: Optional[str] = None,
    mode: str = "mock",
    backend: Optional[str] = None,
    limit: int = 5,
    min_score: float = 0.2,
    paths: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Builds a comprehensive evidence pack for a research question.

    This function orchestrates a research process, gathering evidence from the
    codebase and generating reports and artifacts.

    Args:
        question: The research question or topic.
        root_path: Optional root path for the project. Defaults to configured root.
        workspace_path: Optional workspace path. Defaults to configured workspace.
        output_dir: Directory to save the evidence pack. Defaults to a subdirectory in workspace.
        mode: Research mode, either "mock" or "local". Defaults to "mock".
        backend: Search backend to use. Defaults to "tfidf" for mock mode.
        limit: Maximum number of search results to consider. Defaults to 5.
        min_score: Minimum relevance score for search results. Defaults to 0.2.
        paths: Optional list of paths to restrict the research to.

    Returns:
        A dictionary mapping artifact keys (e.g., 'report', 'sources') to their
        absolute file paths.

    Raises:
        ValueError: If the question is empty or if an unsupported mode is specified.
    """
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
        backend: Optional[str] = None,
        limit: int = 5,
        min_score: float = 0.2,
        paths: Optional[List[str]] = None,
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
                    lines.append(
                        f"- {source.get('file_path')} (L{source.get('start_line')}-{source.get('end_line')})"
                    )
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
        backend: Optional[str] = None,
        limit: int = 5,
        min_score: float = 0.2,
        paths: Optional[List[str]] = None,
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

    # =========================================================================
    # Meta GraphRAG
    # =========================================================================

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
        except Exception as e:
            logger.error(f"nexus_meta_graphrag_query error: {e}")
            return f"Error querying meta GraphRAG: {e}"

    @mcp.tool()
    async def nexus_meta_graphrag_status() -> str:
        """
        Return Meta GraphRAG index status.
        """
        try:
            payload = await _run_blocking(build_meta_graphrag_status)
            import json
            return json.dumps(payload, indent=2, ensure_ascii=True)
        except Exception as e:
            logger.error(f"nexus_meta_graphrag_status error: {e}")
            return f"Error fetching meta GraphRAG status: {e}"

    @mcp.tool()
    async def nexus_meta_graphrag_reports(
        entrypoints: Optional[List[str]] = None,
        include_content: bool = False,
    ) -> str:
        """
        Generate and return Meta GraphRAG reports (overview/top-down/bottom-up).
        """
        try:
            payload = await _run_blocking(
                build_meta_graphrag_reports,
                entrypoints=entrypoints,
                include_content=include_content,
            )
            import json
            return json.dumps(payload, indent=2, ensure_ascii=True)
        except Exception as e:
            logger.error(f"nexus_meta_graphrag_reports error: {e}")
            return f"Error generating meta GraphRAG reports: {e}"

    @mcp.tool()
    async def nexus_meta_graphrag_reload() -> str:
        """
        Reset cached Meta GraphRAG indexer (use after reindex).
        """
        try:
            await _run_blocking(reset_meta_graphrag_indexer)
            return "Meta GraphRAG cache reset."
        except Exception as e:
            logger.error(f"nexus_meta_graphrag_reload error: {e}")
            return f"Error resetting meta GraphRAG cache: {e}"

    @mcp.tool()
    async def nexus_export_evidence_pack(
        question: str,
        mode: str = "mock",
        backend: Optional[str] = None,
        limit: int = 5,
        min_score: float = 0.2,
        output_dir: Optional[str] = None,
        paths: Optional[List[str]] = None,
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
    logger.info(
        "Tools: nexus_read, nexus_glob, nexus_grep, nexus_analyze, nexus_status, "
        "nexus_research, nexus_memory_search, "
        "nexus_meta_graphrag_query, nexus_meta_graphrag_status, nexus_meta_graphrag_reports, "
        "nexus_meta_graphrag_reload, nexus_export_evidence_pack, nexus_bash"
    )
    logger.info("Resources: nexus://config, nexus://agents")

    # Run server with stdio transport
    mcp.run(transport='stdio')


if __name__ == "__main__":
    try:
        main()
    except MCPNotAvailableError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
