"""
Tool Manager - Exécution centralisée des outils

Outils disponibles:
- bash: Execute shell commands
- read: Read file contents
- write: Create/overwrite file
- edit: Search and replace in file
- list_dir: List directory contents
"""
import subprocess
from pathlib import Path
from typing import Dict, Any


class ToolResult:
    """Result from tool execution"""

    def __init__(self, tool_name: str, status: str, output: str, error: str = ""):
        self.tool_name = tool_name
        self.status = status  # SUCCESS, FAILURE, ERROR
        self.output = output
        self.error = error

    def to_dict(self) -> Dict:
        return {
            "tool_name": self.tool_name,
            "status": self.status,
            "output": self.output,
            "error": self.error
        }


class ToolManager:
    """
    Centralized tool execution (OMTE - Orchestrated Multi-Tool Executor)
    """

    def __init__(self, workspace_path: Path):
        self.workspace_path = workspace_path

    def execute(self, tool_request) -> ToolResult:
        """
        Execute tool request

        Args:
            tool_request: ToolUse object with tool_name and arguments

        Returns:
            ToolResult

        Example:
            tool_request = ToolUse(
                tool_name="read",
                arguments={"file_path": "auth.py"}
            )
            result = manager.execute(tool_request)
        """
        tool_name = tool_request.tool_name
        arguments = tool_request.arguments

        # Dispatch to appropriate handler
        handlers = {
            "bash": self._execute_bash,
            "read": self._execute_read,
            "write": self._execute_write,
            "edit": self._execute_edit,
            "list_dir": self._execute_list_dir
        }

        if tool_name not in handlers:
            return ToolResult(
                tool_name=tool_name,
                status="ERROR",
                output="",
                error=f"Unknown tool: {tool_name}"
            )

        try:
            return handlers[tool_name](arguments)
        except Exception as e:
            return ToolResult(
                tool_name=tool_name,
                status="ERROR",
                output="",
                error=str(e)
            )

    def _execute_bash(self, args: Dict) -> ToolResult:
        """Execute bash command"""
        command = args.get("command", "")

        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=str(self.workspace_path),
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode == 0:
                return ToolResult(
                    tool_name="bash",
                    status="SUCCESS",
                    output=result.stdout,
                    error=result.stderr
                )
            else:
                return ToolResult(
                    tool_name="bash",
                    status="FAILURE",
                    output=result.stdout,
                    error=result.stderr
                )

        except subprocess.TimeoutExpired:
            return ToolResult(
                tool_name="bash",
                status="ERROR",
                output="",
                error="Command timed out (60s)"
            )

    def _execute_read(self, args: Dict) -> ToolResult:
        """Read file contents"""
        file_path = Path(args.get("file_path", ""))

        # Resolve relative to workspace
        if not file_path.is_absolute():
            file_path = self.workspace_path / file_path

        try:
            content = file_path.read_text(encoding="utf-8")
            return ToolResult(
                tool_name="read",
                status="SUCCESS",
                output=content
            )
        except FileNotFoundError:
            return ToolResult(
                tool_name="read",
                status="FAILURE",
                output="",
                error=f"File not found: {file_path}"
            )

    def _execute_write(self, args: Dict) -> ToolResult:
        """Write file (create or overwrite)"""
        file_path = Path(args.get("file_path", ""))
        content = args.get("content", "")

        if not file_path.is_absolute():
            file_path = self.workspace_path / file_path

        try:
            # Create parent directories
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # Write file
            file_path.write_text(content, encoding="utf-8")

            return ToolResult(
                tool_name="write",
                status="SUCCESS",
                output=f"File written: {file_path}"
            )
        except Exception as e:
            return ToolResult(
                tool_name="write",
                status="ERROR",
                output="",
                error=str(e)
            )

    def _execute_edit(self, args: Dict) -> ToolResult:
        """Edit file (search and replace)"""
        file_path = Path(args.get("file_path", ""))
        old_string = args.get("old_string", "")
        new_string = args.get("new_string", "")

        if not file_path.is_absolute():
            file_path = self.workspace_path / file_path

        try:
            # Read file
            content = file_path.read_text(encoding="utf-8")

            # Check if old_string exists
            if old_string not in content:
                return ToolResult(
                    tool_name="edit",
                    status="FAILURE",
                    output="",
                    error=f"String not found in file: {old_string[:50]}..."
                )

            # Replace
            new_content = content.replace(old_string, new_string, 1)

            # Write back
            file_path.write_text(new_content, encoding="utf-8")

            return ToolResult(
                tool_name="edit",
                status="SUCCESS",
                output=f"File edited: {file_path}"
            )

        except FileNotFoundError:
            return ToolResult(
                tool_name="edit",
                status="FAILURE",
                output="",
                error=f"File not found: {file_path}"
            )

    def _execute_list_dir(self, args: Dict) -> ToolResult:
        """List directory contents"""
        dir_path = Path(args.get("path", "."))

        if not dir_path.is_absolute():
            dir_path = self.workspace_path / dir_path

        try:
            items = []
            for item in dir_path.iterdir():
                item_type = "dir" if item.is_dir() else "file"
                items.append(f"{item_type}: {item.name}")

            output = "\n".join(sorted(items))

            return ToolResult(
                tool_name="list_dir",
                status="SUCCESS",
                output=output
            )

        except FileNotFoundError:
            return ToolResult(
                tool_name="list_dir",
                status="FAILURE",
                output="",
                error=f"Directory not found: {dir_path}"
            )
