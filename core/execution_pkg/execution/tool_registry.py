"""
ToolRegistry - Tool Registration and Discovery.

NEXUS V9.5 Refactoring - Sprint 2

Extracted from tool_manager.py (God Class decomposition).
Handles:
- Tool name aliases (Gemini CLI -> NEXUS)
- Tool registration and lookup
- Tool metadata and schemas
- Dynamic tool discovery

Usage:
    registry = ToolRegistry()

    # Normalize tool name
    name = registry.normalize_name("read_file")  # -> "read"

    # Register a handler
    registry.register("custom_tool", handler_func, schema={...})

    # Get handler
    handler = registry.get_handler("custom_tool")
"""

from __future__ import annotations

import logging
from typing import Callable, Dict, Any, Optional, List, Set
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class ToolMetadata:
    """Metadata for a registered tool."""
    name: str
    description: str = ""
    schema: Dict[str, Any] = field(default_factory=dict)
    category: str = "core"  # core, mcp, dynamic, swarm
    enabled: bool = True
    aliases: List[str] = field(default_factory=list)


class ToolRegistry:
    """
    Centralized tool registration and discovery.

    Responsibilities:
    - Maintain tool name aliases (Gemini CLI compatibility)
    - Register and lookup tool handlers
    - Manage tool metadata and schemas
    - Track tool categories (core, mcp, dynamic)
    """

    # Tool name aliases (Gemini CLI names -> NEXUS names)
    TOOL_ALIASES: Dict[str, str] = {
        'read_file': 'read',
        'write_file': 'write',
        'edit_file': 'edit',
        'list_directory': 'list_dir',
        'run_shell_command': 'bash',
        'google_web_search': 'web_search',
        'read_many_files': 'read',  # Fallback to single read
    }

    # Core tool definitions
    CORE_TOOLS: Set[str] = {
        "bash", "read", "write", "edit", "list_dir",
        "git", "web_search", "web_fetch",
        "glob", "grep", "todo_write",
        "create_tool", "delete_tool", "list_dynamic_tools", "run_dynamic_tool",
        "swarm_delegate",
    }

    def __init__(self):
        """Initialize empty registry."""
        self._handlers: Dict[str, Callable] = {}
        self._metadata: Dict[str, ToolMetadata] = {}
        self._mcp_tools: Dict[str, str] = {}  # mcp_name -> server_name
        self._dynamic_tools: Set[str] = set()

    def normalize_name(self, tool_name: str) -> str:
        """
        Normalize tool name using aliases.

        Args:
            tool_name: Raw tool name (possibly from Gemini CLI)

        Returns:
            Normalized NEXUS tool name
        """
        return self.TOOL_ALIASES.get(tool_name, tool_name)

    def register(
        self,
        name: str,
        handler: Callable,
        *,
        description: str = "",
        schema: Optional[Dict[str, Any]] = None,
        category: str = "core",
        aliases: Optional[List[str]] = None,
    ) -> None:
        """
        Register a tool handler.

        Args:
            name: Tool name
            handler: Handler function (args: Dict) -> ToolResult
            description: Human-readable description
            schema: JSON schema for arguments
            category: Tool category (core, mcp, dynamic)
            aliases: Alternative names for this tool
        """
        self._handlers[name] = handler
        self._metadata[name] = ToolMetadata(
            name=name,
            description=description,
            schema=schema or {},
            category=category,
            aliases=aliases or [],
        )

        # Register aliases
        if aliases:
            for alias in aliases:
                if alias not in self.TOOL_ALIASES:
                    self.TOOL_ALIASES[alias] = name

        logger.debug(f"Registered tool: {name} (category={category})")

    def unregister(self, name: str) -> bool:
        """
        Unregister a tool.

        Args:
            name: Tool name to remove

        Returns:
            True if tool was removed
        """
        if name in self._handlers:
            del self._handlers[name]
            self._metadata.pop(name, None)
            self._dynamic_tools.discard(name)
            logger.debug(f"Unregistered tool: {name}")
            return True
        return False

    def get_handler(self, name: str) -> Optional[Callable]:
        """
        Get handler for a tool.

        Args:
            name: Tool name (will be normalized)

        Returns:
            Handler function or None
        """
        normalized = self.normalize_name(name)
        return self._handlers.get(normalized)

    def has_tool(self, name: str) -> bool:
        """Check if tool exists."""
        normalized = self.normalize_name(name)
        return normalized in self._handlers

    def get_metadata(self, name: str) -> Optional[ToolMetadata]:
        """Get metadata for a tool."""
        normalized = self.normalize_name(name)
        return self._metadata.get(normalized)

    def list_tools(self, category: Optional[str] = None) -> List[str]:
        """
        List all registered tools.

        Args:
            category: Filter by category (None = all)

        Returns:
            List of tool names
        """
        if category is None:
            return list(self._handlers.keys())
        return [
            name for name, meta in self._metadata.items()
            if meta.category == category
        ]

    def list_core_tools(self) -> List[str]:
        """List core (built-in) tools."""
        return self.list_tools(category="core")

    def list_mcp_tools(self) -> List[str]:
        """List MCP tools."""
        return self.list_tools(category="mcp")

    def list_dynamic_tools(self) -> List[str]:
        """List dynamic tools."""
        return self.list_tools(category="dynamic")

    # MCP tool management
    def register_mcp_tool(
        self,
        name: str,
        handler: Callable,
        server_name: str,
        description: str = "",
        schema: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Register an MCP tool with optional input schema."""
        self.register(
            name=name,
            handler=handler,
            description=description,
            schema=schema,
            category="mcp",
        )
        self._mcp_tools[name] = server_name

    def get_mcp_server(self, tool_name: str) -> Optional[str]:
        """Get MCP server name for a tool."""
        return self._mcp_tools.get(tool_name)

    # Dynamic tool management
    def register_dynamic_tool(
        self,
        name: str,
        handler: Callable,
        description: str = "",
        schema: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Register a dynamic tool."""
        self.register(
            name=name,
            handler=handler,
            description=description,
            schema=schema,
            category="dynamic",
        )
        self._dynamic_tools.add(name)

    def is_dynamic_tool(self, name: str) -> bool:
        """Check if tool is a dynamic tool."""
        return name in self._dynamic_tools

    def get_all_aliases(self) -> Dict[str, str]:
        """Get all tool aliases."""
        return dict(self.TOOL_ALIASES)

    def to_dict(self) -> Dict[str, Any]:
        """Export registry state."""
        return {
            "tools": list(self._handlers.keys()),
            "metadata": {
                name: {
                    "description": meta.description,
                    "category": meta.category,
                    "enabled": meta.enabled,
                }
                for name, meta in self._metadata.items()
            },
            "mcp_tools": dict(self._mcp_tools),
            "dynamic_tools": list(self._dynamic_tools),
        }


# =============================================================================
# V10 PRISM: Multi-Tenant Tool Registry Access
# =============================================================================
_global_registry: Optional[ToolRegistry] = None


def get_tool_registry() -> ToolRegistry:
    """
    Get the tool registry for the current tenant context.

    V10 PRISM: Returns tenant-scoped registry via ServiceFactory.
    Falls back to global singleton if no context is active.

    Returns:
        ToolRegistry instance scoped to current tenant
    """
    # V10: Try ServiceFactory first (tenant-scoped)
    try:
        from ..context import has_active_session
        if has_active_session():
            from ..factory import ServiceFactory
            return ServiceFactory.get_tool_registry()
    except ImportError:
        pass  # context module not available, use legacy

    # Legacy fallback: global singleton
    global _global_registry
    if _global_registry is None:
        _global_registry = ToolRegistry()
    return _global_registry


def reset_tool_registry() -> None:
    """
    Reset global tool registry (for testing).

    Note: In V10, also clears ServiceFactory cache for current tenant.
    """
    global _global_registry
    _global_registry = None

    # V10: Also clear factory cache
    try:
        from ..context import get_current_session_or_none
        from ..factory import ServiceFactory
        ctx = get_current_session_or_none()
        if ctx:
            ServiceFactory.clear_tenant_cache(ctx.tenant_id)
    except ImportError:
        pass
