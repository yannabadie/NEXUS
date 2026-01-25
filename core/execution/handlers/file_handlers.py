"""
File Handlers - read, write, edit, list_dir.

NEXUS V9.5 Refactoring - Sprint 2

Extracted from tool_manager.py for Single Responsibility.
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Dict, Any, Optional

from .base import BaseHandler, ToolResult


def _validate_python_syntax(content: str, path: Path) -> Optional[str]:
    if path.suffix.lower() != ".py":
        return None
    try:
        ast.parse(content, filename=str(path))
    except SyntaxError as exc:
        location = f"{exc.lineno}:{exc.offset}" if exc.lineno else "unknown"
        detail = exc.msg or "invalid syntax"
        return f"Syntax error in {path} at {location}: {detail}"
    return None


class ReadHandler(BaseHandler):
    """Handler for reading file contents.

    Executes read operations on files within the workspace. Ensures strict
    security validation via PathGuardian before accessing the file system.

    Args:
        workspace_path (Path): The root directory of the workspace.
        validation_service (Optional[Any]): The security validation service.

    Returns:
        ReadHandler: A new instance of ReadHandler.

    Raises:
        None
    """

    @property
    def tool_name(self) -> str:
        """Gets the tool identifier.

        Args:
            None

        Returns:
            str: The tool name 'read'.

        Raises:
            None
        """
        return "read"

    def execute(self, args: Dict[str, Any]) -> ToolResult:
        """Executes the file reading operation.

        Args:
            args (Dict[str, Any]): A dictionary containing the arguments:
                file_path (str): The path to the file to read.

        Returns:
            ToolResult: The result of the operation containing:
                status (str): 'SUCCESS', 'FAILURE', or 'ERROR'.
                output (str): The file content.
                error (str): Error message if applicable.

        Raises:
            None: All exceptions are handled and returned as ToolResult.
        """
        file_path_str = args.get("file_path", "")

        if not file_path_str:
            return self._error("Missing required argument: file_path")

        # Resolve and validate path
        path = self._resolve_path(file_path_str)

        # Security validation
        if not self._validate_path(path, "read"):
            return ToolResult(
                tool_name=self.tool_name,
                status="BLOCKED",
                output="",
                error=f"[SECURITY] Path blocked: {path}",
            )

        try:
            content = path.read_text(encoding="utf-8")
            return self._ok(content)
        except FileNotFoundError:
            return self._fail(f"File not found: {path}")
        except PermissionError:
            return self._fail(f"Permission denied: {path}")
        except UnicodeDecodeError:
            # Try binary read for non-text files
            try:
                content = path.read_bytes()
                return self._ok(f"[Binary file, {len(content)} bytes]")
            except Exception as e:
                return self._error(f"Read error: {e}")
        except Exception as e:
            return self._error(f"Read error: {e}")


class WriteHandler(BaseHandler):
    """Handler for writing files (create or overwrite).

    Executes write operations to create or overwrite files within the workspace.
    Ensures security validation prevents unauthorized file modification.

    Args:
        workspace_path (Path): The root directory of the workspace.
        validation_service (Optional[Any]): The security validation service.

    Returns:
        WriteHandler: A new instance of WriteHandler.

    Raises:
        None
    """

    @property
    def tool_name(self) -> str:
        """Gets the tool identifier.

        Args:
            None

        Returns:
            str: The tool name 'write'.

        Raises:
            None
        """
        return "write"

    def execute(self, args: Dict[str, Any]) -> ToolResult:
        """Executes the file writing operation.

        Args:
            args (Dict[str, Any]): A dictionary containing the arguments:
                file_path (str): The path to the file to write.
                content (str): The content to write to the file.

        Returns:
            ToolResult: The result of the operation containing:
                status (str): 'SUCCESS', 'FAILURE', or 'ERROR'.
                output (str): Success message.
                error (str): Error message if applicable.

        Raises:
            None: All exceptions are handled and returned as ToolResult.
        """
        file_path_str = args.get("file_path", "")
        content = args.get("content", "")

        if not file_path_str:
            return self._error("Missing required argument: file_path")

        # Resolve path
        path = self._resolve_path(file_path_str)

        # Security validation (use original relative path for PathGuardian)
        if not self._validate_path_str(file_path_str, "write"):
            return ToolResult(
                tool_name=self.tool_name,
                status="BLOCKED",
                output="",
                error=f"[SECURITY] Write blocked: {path}",
            )

        syntax_error = _validate_python_syntax(content, path)
        if syntax_error:
            return self._fail(syntax_error)

        try:
            # Create parent directories
            path.parent.mkdir(parents=True, exist_ok=True)

            # Write file
            path.write_text(content, encoding="utf-8")

            return self._ok(f"File written: {path}")
        except PermissionError:
            return self._fail(f"Permission denied: {path}")
        except Exception as e:
            return self._error(str(e))


class EditHandler(BaseHandler):
    """Handler for editing files (search and replace).

    Performs search and replace operations on file content. Validates paths
    and ensures the string to be replaced exists to prevent errors.

    Args:
        workspace_path (Path): The root directory of the workspace.
        validation_service (Optional[Any]): The security validation service.

    Returns:
        EditHandler: A new instance of EditHandler.

    Raises:
        None
    """

    @property
    def tool_name(self) -> str:
        """Gets the tool identifier.

        Args:
            None

        Returns:
            str: The tool name 'edit'.

        Raises:
            None
        """
        return "edit"

    def execute(self, args: Dict[str, Any]) -> ToolResult:
        """Executes the file editing operation (search and replace).

        Args:
            args (Dict[str, Any]): A dictionary containing the arguments:
                file_path (str): The path to the file to edit.
                old_string (str): The exact string to search for.
                new_string (str): The replacement string.

        Returns:
            ToolResult: The result of the operation containing:
                status (str): 'SUCCESS', 'FAILURE', or 'ERROR'.
                output (str): Success message.
                error (str): Error message if applicable.

        Raises:
            None: All exceptions are handled and returned as ToolResult.
        """
        file_path_str = args.get("file_path", "")
        old_string = args.get("old_string", "")
        new_string = args.get("new_string", "")

        if not file_path_str:
            return self._error("Missing required argument: file_path")
        if not old_string:
            return self._error("Missing required argument: old_string")

        # Resolve path
        path = self._resolve_path(file_path_str)

        # Security validation (use original relative path for PathGuardian)
        if not self._validate_path_str(file_path_str, "edit"):
            return ToolResult(
                tool_name=self.tool_name,
                status="BLOCKED",
                output="",
                error=f"[SECURITY] Edit blocked: {path}",
            )

        try:
            # Read file
            content = path.read_text(encoding="utf-8")

            # Check if old_string exists
            if old_string not in content:
                return self._fail(f"String not found in file: {old_string[:50]}...")

            # Replace (only first occurrence)
            new_content = content.replace(old_string, new_string, 1)

            syntax_error = _validate_python_syntax(new_content, path)
            if syntax_error:
                return self._fail(syntax_error)

            # Write back
            path.write_text(new_content, encoding="utf-8")

            return self._ok(f"File edited: {path}")

        except FileNotFoundError:
            return self._fail(f"File not found: {path}")
        except PermissionError:
            return self._fail(f"Permission denied: {path}")
        except Exception as e:
            return self._error(str(e))


class ListDirHandler(BaseHandler):
    """Handler for listing directory contents.

    Retrieves the list of files and subdirectories within a specified path.
    Results are sorted and formatted to distinguish directories from files.

    Args:
        workspace_path (Path): The root directory of the workspace.
        validation_service (Optional[Any]): The security validation service.

    Returns:
        ListDirHandler: A new instance of ListDirHandler.

    Raises:
        None
    """

    @property
    def tool_name(self) -> str:
        """Gets the tool identifier.

        Args:
            None

        Returns:
            str: The tool name 'list_dir'.

        Raises:
            None
        """
        return "list_dir"

    def execute(self, args: Dict[str, Any]) -> ToolResult:
        """Executes the list directory operation.

        Args:
            args (Dict[str, Any]): A dictionary containing the arguments:
                path (str, optional): The directory path to list. Defaults to ".".

        Returns:
            ToolResult: The result of the operation containing:
                status (str): 'SUCCESS', 'FAILURE', or 'ERROR'.
                output (str): The formatted list of files and directories.
                error (str): Error message if applicable.

        Raises:
            None: All exceptions are handled and returned as ToolResult.
        """
        dir_path_str = args.get("path", ".")

        # Resolve and validate path
        path = self._resolve_path(dir_path_str)

        # Security validation
        if not self._validate_path(path, "list"):
            return ToolResult(
                tool_name=self.tool_name,
                status="BLOCKED",
                output="",
                error=f"[SECURITY] List blocked: {path}",
            )

        try:
            if not path.exists():
                return self._fail(f"Directory not found: {path}")

            if not path.is_dir():
                return self._fail(f"Not a directory: {path}")

            # List directory contents
            items = sorted(
                path.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())
            )

            # Format output
            lines = []
            for item in items:
                if item.is_dir():
                    lines.append(f"[DIR]  {item.name}/")
                else:
                    size = item.stat().st_size
                    lines.append(f"[FILE] {item.name} ({size} bytes)")

            if not lines:
                return self._ok("(empty directory)")

            return self._ok("\n".join(lines))

        except PermissionError:
            return self._fail(f"Permission denied: {path}")
        except Exception as e:
            return self._error(str(e))


# Factory function
def create_file_handlers(
    workspace_path: Path,
    validation_service: Optional[Any] = None,
) -> Dict[str, BaseHandler]:
    """Create all file handlers.

    Args:
        workspace_path (Path): Workspace root path.
        validation_service (Optional[Any], optional): Validation service. Defaults to None.

    Returns:
        Dict[str, BaseHandler]: Dict mapping tool names to handlers.

    Raises:
        None
    """
    return {
        "read": ReadHandler(workspace_path, validation_service),
        "write": WriteHandler(workspace_path, validation_service),
        "edit": EditHandler(workspace_path, validation_service),
        "list_dir": ListDirHandler(workspace_path, validation_service),
    }
