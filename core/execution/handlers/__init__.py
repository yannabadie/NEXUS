"""
Tool Handlers - NEXUS V9.5

Extracted from tool_manager.py for Single Responsibility.
Each handler focuses on one category of tools.

Modules:
- base: BaseHandler protocol and ToolResult
- file_handlers: read, write, edit, list_dir
- bash_handler: bash command execution
- git_handler: git operations
- web_handlers: web_search, web_fetch
- search_handlers: glob, grep
- todo_handler: todo_write
"""

from .base import BaseHandler, ToolResult

__all__ = [
    "BaseHandler",
    "ToolResult",
]
