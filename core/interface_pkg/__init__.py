"""
NEXUS V12.4 - Interface Package

Consolidated interface components:
- workspace: Multi-workspace management
- notifications: Email and file-based notifications
- mcp: MCP (Model Context Protocol) client and registry
- interface: Command parsing and analytics

P5.6 Phase 3: Package consolidation for reduced cognitive load.
"""

# Workspace exports
from core.interface_pkg.workspace import (
    WorkspaceManager,
    WorkspaceInfo,
    WorkspaceMetrics,
    WorkspaceError,
    WorkspaceNotFoundError,
    WorkspaceExistsError,
)

# Notifications exports
from core.interface_pkg.notifications import (
    send_review_email,
    EmailNotificationError,
    create_pending_review,
    check_pending_review,
    get_repl_alert_message,
)

# MCP exports
from core.interface_pkg.mcp import (
    MCPRequest,
    MCPResponse,
    MCPTool,
    MCPToolResult,
    MCPError,
    MCPCapabilities,
    MCPClient,
    MCPRegistry,
    MCPToolDiscovery,
    DiscoveredTool,
    ToolDiscoveryResult,
    validate_input_schema,
    MCP_SERVER_AVAILABLE,
)

# Interface exports
from core.interface_pkg.interface import (
    Arg,
    ArgType,
    CommandDef,
    CommandParser,
    ParsedCommand,
    Suggestion,
    CommandAnalytics,
    CommandInvocation,
    CommandMetrics,
    UsagePattern,
    AnalyticsStats,
    get_command_analytics,
    reset_command_analytics,
)

__all__ = [
    # Workspace
    "WorkspaceManager",
    "WorkspaceInfo",
    "WorkspaceMetrics",
    "WorkspaceError",
    "WorkspaceNotFoundError",
    "WorkspaceExistsError",
    # Notifications
    "send_review_email",
    "EmailNotificationError",
    "create_pending_review",
    "check_pending_review",
    "get_repl_alert_message",
    # MCP
    "MCPRequest",
    "MCPResponse",
    "MCPTool",
    "MCPToolResult",
    "MCPError",
    "MCPCapabilities",
    "MCPClient",
    "MCPRegistry",
    "MCPToolDiscovery",
    "DiscoveredTool",
    "ToolDiscoveryResult",
    "validate_input_schema",
    "MCP_SERVER_AVAILABLE",
    # Interface
    "Arg",
    "ArgType",
    "CommandDef",
    "CommandParser",
    "ParsedCommand",
    "Suggestion",
    "CommandAnalytics",
    "CommandInvocation",
    "CommandMetrics",
    "UsagePattern",
    "AnalyticsStats",
    "get_command_analytics",
    "reset_command_analytics",
]

__version__ = "12.4.0"
