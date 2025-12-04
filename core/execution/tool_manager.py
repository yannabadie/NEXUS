"""
Tool Manager - Exécution centralisée des outils

Outils disponibles (TOUS accessibles par Gemini ET Claude):
- bash: Execute shell commands
- read: Read file contents
- write: Create/overwrite file
- edit: Search and replace in file
- list_dir: List directory contents
- git: Git operations (add, commit, status, diff, log, push, pull)
- web_search: Search the web (via Gemini CLI)
- web_fetch: Fetch URL content
- glob: File pattern matching (find files by pattern)
- grep: Search code for keywords/patterns
- todo_write: Task/plan management
- mcp_*: Dynamic MCP tools from configured servers (V7.6 CORTEX)
"""
import subprocess
import urllib.request
import urllib.parse
import json
import re
import fnmatch
import logging
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional, Callable

# Security imports
from core.security import PathGuardian
from core.security.execution_policy import ExecutionPolicy, CommandType

# V7.6 Phase 12.3: MCP Client imports (optional)
try:
    from core.mcp import MCPRegistry, MCPClient, MCPTool
    from core.mcp.client import MCPClientError, MCPServerError
    _MCP_AVAILABLE = True
except ImportError:
    _MCP_AVAILABLE = False
    MCPRegistry = None
    MCPClient = None


# ============================================================================
# LEGACY: Bash blacklist patterns moved to SandboxPolicy (Phase 14a)
# See: core/security/sandbox_policy.py for centralized security policy
# ============================================================================


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

        # Evolution mode flag (enabled only during /evolve)
        self.evolution_mode = False

        # Compute paths for evolution permissions
        self.parent_path = workspace_path.parent  # NEXUS_V7_CHRYSALIS/
        self.project_root = workspace_path.parent.parent  # 20_NEXUS/
        self.generation_active = self.project_root / "GENERATION_ACTIVE"

        # Initialize PathGuardian (security layer 2)
        self.path_guardian = PathGuardian(
            workspace_path=workspace_path,
            parent_path=self.parent_path,
            generation_active=self.generation_active
        )

        # Initialize ExecutionPolicy (security layer 1 - Phase 14a)
        self.execution_policy = ExecutionPolicy(workspace_path)

        # Dispatch to appropriate handler
        self.tools = {
            "bash": self._execute_bash,
            "read": self._execute_read,
            "write": self._execute_write,
            "edit": self._execute_edit,
            "list_dir": self._execute_list_dir,
            "git": self._execute_git,
            "web_search": self._execute_web_search,
            "web_fetch": self._execute_web_fetch,
            "glob": self._execute_glob,
            "grep": self._execute_grep,
            "todo_write": self._execute_todo_write
        }

        # V7.6 Phase 12.3: MCP Registry and dynamic tools
        self._mcp_registry: Optional["MCPRegistry"] = None
        self._mcp_tools: Dict[str, Tuple[str, str]] = {}  # tool_name -> (server_name, mcp_tool_name)
        self._logger = logging.getLogger("nexus.tools")

        if _MCP_AVAILABLE:
            self._init_mcp_tools()

    # Tool name aliases (Gemini CLI names -> NEXUS names)
    TOOL_ALIASES = {
        'read_file': 'read',
        'write_file': 'write',
        'edit_file': 'edit',
        'list_directory': 'list_dir',
        'run_shell_command': 'bash',
        'google_web_search': 'web_search',
        'read_many_files': 'read',  # Fallback to single read
    }

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

        # Normalize tool name using alias if needed (Gemini CLI compatibility)
        tool_name = self.TOOL_ALIASES.get(tool_name, tool_name)

        if tool_name not in self.tools:
            return ToolResult(
                tool_name=tool_name,
                status="ERROR",
                output="",
                error=f"Unknown tool: {tool_name}"
            )

        try:
            return self.tools[tool_name](arguments)
        except Exception as e:
            return ToolResult(
                tool_name=tool_name,
                status="ERROR",
                output="",
                error=str(e)
            )

    def _execute_bash(self, args: Dict) -> ToolResult:
        """
        Execute bash command with security hardening (Phase 14a).

        Security layers:
        1. SandboxPolicy validation (patterns, executables)
        2. Command analysis (SIMPLE vs COMPLEX)
        3. Prefer shell=False for simple commands
        4. Strict validation for complex commands
        """
        command = args.get("command", "")

        if not command or not command.strip():
            return ToolResult(
                tool_name="bash",
                status="ERROR",
                output="",
                error="Empty command"
            )

        # SECURITY LAYER 1: ExecutionPolicy validation
        is_valid, error = self.execution_policy.validate_command(command)
        if not is_valid:
            return ToolResult(
                tool_name="bash",
                status="BLOCKED",
                output="",
                error=f"{error}. Command: {command[:80]}..."
            )

        # SECURITY LAYER 2: Analyze command for safe execution
        analysis = self.execution_policy.analyze_command(command)

        if analysis.command_type == CommandType.BLOCKED:
            return ToolResult(
                tool_name="bash",
                status="BLOCKED",
                output="",
                error=f"[SECURITY] {analysis.blocked_reason}. Command: {command[:80]}..."
            )

        try:
            if analysis.command_type == CommandType.SIMPLE:
                # SAFE: Use shell=False with parsed arguments
                exec_args = [analysis.executable] + analysis.arguments
                result = subprocess.run(
                    exec_args,
                    shell=False,  # Phase 14a: Secure execution
                    cwd=str(self.workspace_path),
                    capture_output=True,
                    text=True,
                    timeout=60,
                    encoding='utf-8',
                    errors='replace'
                )
            else:
                # COMPLEX: Requires shell=True but was validated
                result = subprocess.run(
                    command,
                    shell=True,
                    cwd=str(self.workspace_path),
                    capture_output=True,
                    text=True,
                    timeout=60,
                    encoding='utf-8',
                    errors='replace'
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

        except FileNotFoundError:
            return ToolResult(
                tool_name="bash",
                status="ERROR",
                output="",
                error=f"Command not found: {analysis.executable}"
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

        # Evolution mode: Allow reading parent code
        if self.evolution_mode and not file_path.is_absolute():
            path_str = str(file_path)
            if path_str.startswith("../"):
                # Resolve relative to workspace
                resolved = (self.workspace_path / file_path).resolve()

                # Check whitelist
                if self._is_evolution_safe_read(resolved):
                    file_path = resolved
                else:
                    return ToolResult(
                        tool_name="read",
                        status="FAILURE",
                        output="",
                        error=f"Evolution mode: Read not allowed for {resolved} (not in whitelist)"
                    )

        # Normal mode: Resolve relative to workspace
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
        """Write file (create or overwrite) - with PathGuardian security."""
        file_path_str = args.get("file_path", "")
        file_content = args.get("content", "")

        # SECURITY LAYER 2: PathGuardian validation
        valid, resolved_path, msg = self.path_guardian.validate_write(
            file_path_str, is_evolution_mode=self.evolution_mode
        )
        if not valid:
            return ToolResult(tool_name="write", status="BLOCKED", output="", error=msg)

        file_path = resolved_path

        # Evolution mode: Allow writing to GENERATION_ACTIVE (additional check)
        if self.evolution_mode and not Path(file_path_str).is_absolute():
            path_str = str(file_path)
            if path_str.startswith("../../GENERATION_ACTIVE/"):
                # Resolve relative to workspace
                resolved = (self.workspace_path / file_path).resolve()

                # Check whitelist
                if self._is_evolution_safe_write(resolved):
                    file_path = resolved
                else:
                    return ToolResult(
                        tool_name="write",
                        status="FAILURE",
                        output="",
                        error=f"Evolution mode: Write not allowed for {resolved} (must be under GENERATION_ACTIVE)"
                    )

        # Normal mode: Resolve relative to workspace
        if not file_path.is_absolute():
            file_path = self.workspace_path / file_path

        try:
            # Create parent directories
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # Write file
            file_path.write_text(file_content, encoding="utf-8")

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
        """Edit file (search and replace) - with PathGuardian security."""
        file_path_str = args.get("file_path", "")
        old_string = args.get("old_string", "")
        new_string = args.get("new_string", "")

        # SECURITY LAYER 2: PathGuardian validation
        valid, resolved_path, msg = self.path_guardian.validate_write(
            file_path_str, is_evolution_mode=self.evolution_mode
        )
        if not valid:
            return ToolResult(tool_name="edit", status="BLOCKED", output="", error=msg)

        file_path = resolved_path

        # Evolution mode: Allow editing GENERATION_ACTIVE files (additional check)
        if self.evolution_mode and not Path(file_path_str).is_absolute():
            path_str = str(file_path)
            if path_str.startswith("../../GENERATION_ACTIVE/"):
                # Resolve relative to workspace
                resolved = (self.workspace_path / file_path).resolve()

                # Check whitelist
                if self._is_evolution_safe_write(resolved):
                    file_path = resolved
                else:
                    return ToolResult(
                        tool_name="edit",
                        status="FAILURE",
                        output="",
                        error=f"Evolution mode: Edit not allowed for {resolved} (must be under GENERATION_ACTIVE)"
                    )

        # Normal mode: Resolve relative to workspace
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

        # Evolution mode: Allow listing parent directories
        if self.evolution_mode and not dir_path.is_absolute():
            path_str = str(dir_path)
            if path_str.startswith("../"):
                # Resolve relative to workspace
                resolved = (self.workspace_path / dir_path).resolve()

                # Check whitelist (reuse read whitelist logic)
                if self._is_evolution_safe_list(resolved):
                    dir_path = resolved
                else:
                    return ToolResult(
                        tool_name="list_dir",
                        status="FAILURE",
                        output="",
                        error=f"Evolution mode: List not allowed for {resolved} (not in whitelist)"
                    )

        # Normal mode: Resolve relative to workspace
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

    def _execute_git(self, args: Dict) -> ToolResult:
        """
        Execute git operations (ported from V5)

        Args:
            args: {
                "operation": "add|commit|status|diff|log|push|pull",
                "args": "additional arguments (optional)"
            }

        Returns:
            ToolResult with git output

        Examples:
            {"operation": "status"}
            {"operation": "add", "args": "src/auth.py"}
            {"operation": "commit", "args": "-m 'Fix auth bug'"}
            {"operation": "diff", "args": "HEAD~1"}
        """
        operation = args.get("operation", "")
        additional_args = args.get("args", "")

        # SECURITY: Read-only operations allowed
        SAFE_OPS = {"status", "diff", "log", "show", "branch"}
        BLOCKED_OPS = {"push", "commit", "add", "reset", "checkout", "merge", "rebase"}

        if operation.lower() in BLOCKED_OPS:
            return ToolResult(
                tool_name="git",
                status="BLOCKED",
                output="",
                error=f"[SECURITY] Git '{operation}' BLOCKED. Parent repo is READ-ONLY."
            )

        allowed_ops = list(SAFE_OPS) + ["pull"]
        if operation.lower() not in allowed_ops:
            return ToolResult(
                tool_name="git",
                status="ERROR",
                output="",
                error=f"Invalid git operation: {operation}. Allowed: {', '.join(allowed_ops)}"
            )

        try:
            # Build git command
            command = ["git", operation]
            if additional_args:
                # Split args respecting quotes
                import shlex
                command.extend(shlex.split(additional_args))

            # Execute git command
            result = subprocess.run(
                command,
                cwd=str(self.workspace_path),
                capture_output=True,
                text=True,
                timeout=60,
                encoding="utf-8",
                errors="replace"
            )

            if result.returncode == 0:
                return ToolResult(
                    tool_name="git",
                    status="SUCCESS",
                    output=result.stdout or "(no output)",
                    error=result.stderr
                )
            else:
                return ToolResult(
                    tool_name="git",
                    status="FAILURE",
                    output=result.stdout,
                    error=result.stderr or f"Git command failed with return code {result.returncode}"
                )

        except subprocess.TimeoutExpired:
            return ToolResult(
                tool_name="git",
                status="ERROR",
                output="",
                error=f"Git command timed out after 60s: git {operation} {additional_args}"
            )
        except Exception as e:
            return ToolResult(
                tool_name="git",
                status="ERROR",
                output="",
                error=f"Git execution error: {str(e)}"
            )

    def _execute_web_search(self, args: Dict) -> ToolResult:
        """
        Execute web search via Gemini CLI (google_web_search)

        This delegates to Gemini CLI's built-in google_web_search tool
        which provides grounding with Google Search.

        Args:
            args: {
                "query": "search query string",
                "num_results": 5 (optional, default: 5)
            }

        Returns:
            ToolResult with search results
        """
        query = args.get("query", "")
        num_results = args.get("num_results", 5)

        if not query:
            return ToolResult(
                tool_name="web_search",
                status="ERROR",
                output="",
                error="Query parameter is required"
            )

        try:
            # Use Gemini CLI for web search
            # Fix: Force a model capable of grounding (gemini-3-pro-preview)
            # Fix: Explicitly prompt to use the tool
            command = [
                "gemini",
                "-m", "gemini-3-pro-preview",
                "-p",
                f"You have access to Google Search. Search for: '{query}'. Provide a detailed summary of the top {num_results} results including titles and URLs."
            ]

            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=90,  # Fix: Increased timeout for grounding latency
                encoding="utf-8",
                errors="replace"
            )

            if result.returncode == 0:
                return ToolResult(
                    tool_name="web_search",
                    status="SUCCESS",
                    output=result.stdout or "(no results)",
                    error=result.stderr
                )
            else:
                # Fix: Capture stdout too, as CLI might print errors there
                error_msg = f"Stderr: {result.stderr}\nStdout: {result.stdout}"
                return ToolResult(
                    tool_name="web_search",
                    status="FAILURE",
                    output=result.stdout,
                    error=error_msg
                )

        except subprocess.TimeoutExpired:
            return ToolResult(
                tool_name="web_search",
                status="ERROR",
                output="",
                error="Web search timed out after 90s"
            )
        except FileNotFoundError:
            return ToolResult(
                tool_name="web_search",
                status="ERROR",
                output="",
                error="Gemini CLI not found. Web search requires Gemini CLI."
            )
        except Exception as e:
            return ToolResult(
                tool_name="web_search",
                status="ERROR",
                output="",
                error=f"Web search error: {str(e)}"
            )

    def _execute_web_fetch(self, args: Dict) -> ToolResult:
        """
        Fetch content from a URL

        Args:
            args: {
                "url": "https://example.com",
                "max_length": 10000 (optional, default: 10000 chars)
            }

        Returns:
            ToolResult with URL content

        Examples:
            {"url": "https://docs.python.org/3/library/asyncio.html"}
            {"url": "https://api.github.com/repos/python/cpython", "max_length": 5000}
        """
        url = args.get("url", "")
        max_length = args.get("max_length", 10000)

        if not url:
            return ToolResult(
                tool_name="web_fetch",
                status="ERROR",
                output="",
                error="URL parameter is required"
            )

        # Basic URL validation
        if not url.startswith(("http://", "https://")):
            return ToolResult(
                tool_name="web_fetch",
                status="ERROR",
                output="",
                error="URL must start with http:// or https://"
            )

        try:
            # Create request with REAL browser user agent (Fix 403 blocks)
            req = urllib.request.Request(
                url,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                }
            )

            # Fetch URL
            with urllib.request.urlopen(req, timeout=30) as response:
                content_type = response.headers.get('Content-Type', '')

                # Read content
                content_bytes = response.read()

                # Decode based on content type
                if 'charset=' in content_type:
                    encoding = content_type.split('charset=')[1].split(';')[0].strip()
                else:
                    encoding = 'utf-8'

                try:
                    content = content_bytes.decode(encoding, errors='replace')
                except:
                    content = content_bytes.decode('utf-8', errors='replace')

                # Truncate if too long
                if len(content) > max_length:
                    content = content[:max_length] + f"\n\n[Content truncated at {max_length} characters]"

                return ToolResult(
                    tool_name="web_fetch",
                    status="SUCCESS",
                    output=f"URL: {url}\nContent-Type: {content_type}\n\n{content}"
                )

        except urllib.error.HTTPError as e:
            return ToolResult(
                tool_name="web_fetch",
                status="FAILURE",
                output="",
                error=f"HTTP Error {e.code}: {e.reason}"
            )
        except urllib.error.URLError as e:
            return ToolResult(
                tool_name="web_fetch",
                status="ERROR",
                output="",
                error=f"URL Error: {e.reason}"
            )
        except Exception as e:
            return ToolResult(
                tool_name="web_fetch",
                status="ERROR",
                output="",
                error=f"Web fetch error: {str(e)}"
            )

    def _execute_glob(self, args: Dict) -> ToolResult:
        """
        Find files matching a pattern (like Claude Code's Glob tool)

        Args:
            args: {
                "pattern": "**/*.py" (glob pattern),
                "path": "./src" (optional, default: workspace root),
                "max_results": 100 (optional, default: 100)
            }

        Returns:
            ToolResult with matching file paths

        Examples:
            {"pattern": "**/*.py"}
            {"pattern": "src/**/*.tsx", "max_results": 50}
            {"pattern": "*.json", "path": "./config"}

        Patterns:
            * - matches any characters except /
            ** - matches any characters including /
            ? - matches single character
            [abc] - matches one of a, b, c
        """
        pattern = args.get("pattern", "")
        search_path = args.get("path", ".")
        max_results = args.get("max_results", 100)

        if not pattern:
            return ToolResult(
                tool_name="glob",
                status="ERROR",
                output="",
                error="Pattern parameter is required"
            )

        try:
            # Evolution mode: Allow searching parent code
            if self.evolution_mode and not Path(search_path).is_absolute():
                path_str = str(search_path)
                if path_str.startswith("../"):
                    # Resolve relative to workspace
                    resolved = (self.workspace_path / search_path).resolve()

                    # Check whitelist (reuse list whitelist logic)
                    if self._is_evolution_safe_list(resolved):
                        search_path = resolved
                    else:
                        return ToolResult(
                            tool_name="glob",
                            status="FAILURE",
                            output="",
                            error=f"Evolution mode: Search not allowed for {resolved} (not in whitelist)"
                        )

            # Resolve search path relative to workspace
            if not Path(search_path).is_absolute():
                search_path = self.workspace_path / search_path

            search_path = Path(search_path)

            if not search_path.exists():
                return ToolResult(
                    tool_name="glob",
                    status="FAILURE",
                    output="",
                    error=f"Search path does not exist: {search_path}"
                )

            # Find matching files
            matches = []
            for file_path in search_path.rglob("*"):
                if file_path.is_file():
                    # Get relative path from search_path
                    rel_path = file_path.relative_to(search_path)

                    # Check if matches pattern
                    if file_path.match(pattern):
                        matches.append(str(rel_path))

                    if len(matches) >= max_results:
                        break

            # Sort matches
            matches.sort()

            if matches:
                output = f"Found {len(matches)} files matching '{pattern}':\n\n"
                output += "\n".join(matches)

                if len(matches) >= max_results:
                    output += f"\n\n[Limited to {max_results} results]"

                return ToolResult(
                    tool_name="glob",
                    status="SUCCESS",
                    output=output
                )
            else:
                return ToolResult(
                    tool_name="glob",
                    status="SUCCESS",
                    output=f"No files found matching '{pattern}'"
                )

        except Exception as e:
            return ToolResult(
                tool_name="glob",
                status="ERROR",
                output="",
                error=f"Glob error: {str(e)}"
            )

    def _execute_grep(self, args: Dict) -> ToolResult:
        """
        Search code for keywords/patterns (like Claude Code's Grep tool)

        Args:
            args: {
                "pattern": "def.*async" (regex pattern),
                "path": "./src" (optional, default: workspace root),
                "file_pattern": "*.py" (optional, filter files),
                "case_sensitive": true (optional, default: true),
                "max_results": 100 (optional, default: 100)
            }

        Returns:
            ToolResult with matching lines

        Examples:
            {"pattern": "async def", "file_pattern": "*.py"}
            {"pattern": "TODO", "case_sensitive": false}
            {"pattern": "import.*asyncio", "path": "./src"}
        """
        pattern = args.get("pattern", "")
        search_path = args.get("path", ".")
        file_pattern = args.get("file_pattern", "*")
        case_sensitive = args.get("case_sensitive", True)
        max_results = args.get("max_results", 100)

        if not pattern:
            return ToolResult(
                tool_name="grep",
                status="ERROR",
                output="",
                error="Pattern parameter is required"
            )

        try:
            # Evolution mode: Allow searching parent code
            if self.evolution_mode and not Path(search_path).is_absolute():
                path_str = str(search_path)
                if path_str.startswith("../"):
                    # Resolve relative to workspace
                    resolved = (self.workspace_path / search_path).resolve()

                    # Check whitelist (reuse list whitelist logic)
                    if self._is_evolution_safe_list(resolved):
                        search_path = resolved
                    else:
                        return ToolResult(
                            tool_name="grep",
                            status="FAILURE",
                            output="",
                            error=f"Evolution mode: Search not allowed for {resolved} (not in whitelist)"
                        )

            # Resolve search path
            if not Path(search_path).is_absolute():
                search_path = self.workspace_path / search_path

            search_path = Path(search_path)

            if not search_path.exists():
                return ToolResult(
                    tool_name="grep",
                    status="FAILURE",
                    output="",
                    error=f"Search path does not exist: {search_path}"
                )

            # Compile regex pattern
            flags = 0 if case_sensitive else re.IGNORECASE
            try:
                regex = re.compile(pattern, flags)
            except re.error as e:
                return ToolResult(
                    tool_name="grep",
                    status="ERROR",
                    output="",
                    error=f"Invalid regex pattern: {e}"
                )

            # Search files
            matches = []
            files_searched = 0

            for file_path in search_path.rglob(file_pattern):
                if not file_path.is_file():
                    continue

                files_searched += 1

                try:
                    content = file_path.read_text(encoding='utf-8', errors='replace')
                    lines = content.split('\n')

                    for line_num, line in enumerate(lines, start=1):
                        if regex.search(line):
                            try:
                                rel_path = file_path.relative_to(self.workspace_path)
                            except ValueError:
                                # Evolution mode: path might be outside workspace
                                rel_path = file_path
                            matches.append(f"{rel_path}:{line_num}: {line.strip()}")

                            if len(matches) >= max_results:
                                break

                except (UnicodeDecodeError, PermissionError):
                    # Skip files we can't read
                    continue

                if len(matches) >= max_results:
                    break

            # Format output
            if matches:
                output = f"Found {len(matches)} matches for '{pattern}' in {files_searched} files:\n\n"
                output += "\n".join(matches)

                if len(matches) >= max_results:
                    output += f"\n\n[Limited to {max_results} results]"

                return ToolResult(
                    tool_name="grep",
                    status="SUCCESS",
                    output=output
                )
            else:
                return ToolResult(
                    tool_name="grep",
                    status="SUCCESS",
                    output=f"No matches found for '{pattern}' in {files_searched} files"
                )

        except Exception as e:
            return ToolResult(
                tool_name="grep",
                status="ERROR",
                output="",
                error=f"Grep error: {str(e)}"
            )

    def _execute_todo_write(self, args: Dict) -> ToolResult:
        """
        Task/plan management (like Claude Code's TodoWrite)

        Args:
            args: {
                "todos": [
                    {
                        "id": 1,
                        "description": "Implement authentication",
                        "status": "pending|in_progress|completed",
                        "assigned_agent": "Claude|Gemini"
                    }
                ]
            }

        Returns:
            ToolResult with updated plan

        Examples:
            {
                "todos": [
                    {"id": 1, "description": "Read auth.py", "status": "completed", "assigned_agent": "Claude"},
                    {"id": 2, "description": "Fix bug", "status": "in_progress", "assigned_agent": "Claude"}
                ]
            }
        """
        todos = args.get("todos", [])

        if not isinstance(todos, list):
            return ToolResult(
                tool_name="todo_write",
                status="ERROR",
                output="",
                error="'todos' must be a list"
            )

        try:
            # Save to workspace
            todo_file = self.workspace_path / ".nexus" / "plan.json"
            todo_file.parent.mkdir(parents=True, exist_ok=True)

            # Format todos
            formatted_todos = []
            for todo in todos:
                if not isinstance(todo, dict):
                    continue

                formatted_todos.append({
                    "id": todo.get("id", len(formatted_todos) + 1),
                    "description": todo.get("description", ""),
                    "status": todo.get("status", "pending"),
                    "assigned_agent": todo.get("assigned_agent", "Claude")
                })

            # Save to file
            todo_file.write_text(json.dumps(formatted_todos, indent=2), encoding='utf-8')

            # Format output
            output = f"Plan updated ({len(formatted_todos)} tasks):\n\n"

            for todo in formatted_todos:
                status_icon = {
                    "pending": "⏳",
                    "in_progress": "🔄",
                    "completed": "✅",
                    "failed": "❌"
                }.get(todo["status"], "❓")

                output += f"{status_icon} #{todo['id']}: {todo['description']} [{todo['assigned_agent']}] ({todo['status']})\n"

            output += f"\nPlan saved to: {todo_file}"

            return ToolResult(
                tool_name="todo_write",
                status="SUCCESS",
                output=output
            )

        except Exception as e:
            return ToolResult(
                tool_name="todo_write",
                status="ERROR",
                output="",
                error=f"TodoWrite error: {str(e)}"
            )

    def _is_evolution_safe_read(self, path: Path) -> bool:
        """
        Check if path is allowed for evolution READ operations.

        Whitelist:
        - ../core/**/*.py (parent project code)
        - ../prompts/**/*.md (parent prompts)
        - ../README.md, ../nexus6.py (parent root files)

        Forbidden:
        - NEXUS_V5_PRAGMATIC
        - .env, .git, __pycache__
        """
        try:
            # Check path is under parent project
            relative = path.relative_to(self.parent_path)
            path_str = str(relative).replace("\\", "/")  # Normalize for Windows

            # Allowed prefixes
            allowed_prefixes = [
                "core/",
                "prompts/",
                "benchmarks/",  # Allow reading benchmark scripts
            ]

            # Allowed root files
            allowed_root_files = [
                "README.md",
                "nexus6.py",
                "LINEAGE.json",
                ".env"  # Needed for API keys during evolution
            ]

            # Forbidden patterns
            forbidden = [
                "NEXUS_V5_PRAGMATIC",
                "__pycache__",
                ".git",
                ".pyc"
            ]

            # Check forbidden first
            if any(forb in path_str for forb in forbidden):
                return False

            # Check allowed prefixes
            if any(path_str.startswith(prefix) for prefix in allowed_prefixes):
                return True

            # Check allowed root files
            if path_str in allowed_root_files:
                return True

            return False

        except ValueError:
            # Path not under parent
            return False

    def _is_evolution_safe_list(self, path: Path) -> bool:
        """
        Check if path is allowed for evolution LIST operations.

        Whitelist:
        - ../core/ (parent project code)
        - ../prompts/ (parent prompts)
        - ../benchmarks/ (benchmark scripts)

        Uses same logic as _is_evolution_safe_read but for directories.
        """
        try:
            # Check path is under parent project
            relative = path.relative_to(self.parent_path)
            path_str = str(relative).replace("\\", "/")  # Normalize for Windows

            # Allowed directory prefixes
            allowed_prefixes = [
                "core",
                "prompts",
                "benchmarks",
            ]

            # Forbidden directories
            forbidden = [
                "NEXUS_V5_PRAGMATIC",
                ".git",
                "__pycache__",
            ]

            # Check forbidden first
            if any(forb in path_str for forb in forbidden):
                return False

            # Check allowed prefixes (directory listing)
            if any(path_str.startswith(prefix) or path_str == prefix for prefix in allowed_prefixes):
                return True

            return False

        except ValueError:
            # Path not under parent
            return False

    def _is_evolution_safe_write(self, path: Path) -> bool:
        """
        Check if path is allowed for evolution WRITE/EDIT operations.

        Whitelist:
        - ../../GENERATION_ACTIVE/** (children only)

        Everything else is FORBIDDEN (including parent project).
        """
        try:
            # Check path is under GENERATION_ACTIVE
            path.relative_to(self.generation_active)
            return True
        except ValueError:
            # Path not under GENERATION_ACTIVE
            return False

    # =========================================================================
    # V7.6 Phase 12.3: MCP Tool Integration (CORTEX)
    # =========================================================================

    def _init_mcp_tools(self) -> None:
        """
        Initialize MCP registry and register dynamic tools from configured servers.

        Called during __init__ if MCP is available.
        """
        try:
            self._mcp_registry = MCPRegistry(self.workspace_path)
            servers = self._mcp_registry.get_servers()

            if not servers:
                self._logger.debug("No MCP servers configured")
                return

            self._logger.info(f"Loading tools from {len(servers)} MCP server(s)")

            for server_config in servers:
                if not server_config.enabled:
                    continue

                try:
                    self._register_mcp_server_tools(server_config.name)
                except Exception as e:
                    self._logger.warning(
                        f"Failed to load tools from MCP server '{server_config.name}': {e}"
                    )

        except Exception as e:
            self._logger.error(f"Failed to initialize MCP registry: {e}")

    def _register_mcp_server_tools(self, server_name: str) -> None:
        """
        Register tools from a specific MCP server.

        Tools are registered with prefix: mcp_{server}_{tool}

        Args:
            server_name: Name of the MCP server
        """
        if self._mcp_registry is None:
            return

        try:
            client = self._mcp_registry.get_client(server_name)
            if client is None:
                self._logger.warning(f"Could not connect to MCP server: {server_name}")
                return

            tools = client.list_tools()
            self._logger.info(f"MCP server '{server_name}' provides {len(tools)} tool(s)")

            for tool in tools:
                # Create prefixed tool name
                nexus_tool_name = f"mcp_{server_name}_{tool.name}"

                # Store mapping
                self._mcp_tools[nexus_tool_name] = (server_name, tool.name)

                # Register dynamic handler
                self.tools[nexus_tool_name] = self._create_mcp_tool_handler(
                    server_name, tool.name
                )

                self._logger.debug(f"Registered MCP tool: {nexus_tool_name}")

        except Exception as e:
            self._logger.error(f"Error registering tools from {server_name}: {e}")
            raise

    def _create_mcp_tool_handler(
        self, server_name: str, tool_name: str
    ) -> Callable[[Dict], "ToolResult"]:
        """
        Create a handler function for an MCP tool.

        Args:
            server_name: Name of the MCP server
            tool_name: Name of the tool on the server

        Returns:
            Handler function that executes the MCP tool
        """
        def handler(args: Dict) -> ToolResult:
            return self._execute_mcp_tool(server_name, tool_name, args)
        return handler

    def _execute_mcp_tool(
        self, server_name: str, tool_name: str, args: Dict
    ) -> "ToolResult":
        """
        Execute an MCP tool.

        Args:
            server_name: Name of the MCP server
            tool_name: Name of the tool
            args: Tool arguments

        Returns:
            ToolResult with execution output
        """
        nexus_tool_name = f"mcp_{server_name}_{tool_name}"

        if self._mcp_registry is None:
            return ToolResult(
                tool_name=nexus_tool_name,
                status="ERROR",
                output="",
                error="MCP registry not initialized"
            )

        try:
            client = self._mcp_registry.get_client(server_name)
            if client is None:
                return ToolResult(
                    tool_name=nexus_tool_name,
                    status="ERROR",
                    output="",
                    error=f"Failed to connect to MCP server: {server_name}"
                )

            # Call the tool
            result = client.call_tool(tool_name, args)

            if result.isError:
                return ToolResult(
                    tool_name=nexus_tool_name,
                    status="FAILURE",
                    output="",
                    error=result.text
                )

            return ToolResult(
                tool_name=nexus_tool_name,
                status="SUCCESS",
                output=result.text
            )

        except MCPServerError as e:
            return ToolResult(
                tool_name=nexus_tool_name,
                status="FAILURE",
                output="",
                error=f"MCP server error: {e.error.message}"
            )
        except MCPClientError as e:
            return ToolResult(
                tool_name=nexus_tool_name,
                status="ERROR",
                output="",
                error=f"MCP client error: {str(e)}"
            )
        except Exception as e:
            return ToolResult(
                tool_name=nexus_tool_name,
                status="ERROR",
                output="",
                error=f"Unexpected error: {str(e)}"
            )

    def get_mcp_tools(self) -> List[str]:
        """
        Get list of available MCP tools.

        Returns:
            List of MCP tool names (mcp_{server}_{tool} format)
        """
        return list(self._mcp_tools.keys())

    def reload_mcp_tools(self) -> int:
        """
        Reload MCP tools from all configured servers.

        Returns:
            Number of tools loaded
        """
        # Clear existing MCP tools
        for tool_name in list(self._mcp_tools.keys()):
            if tool_name in self.tools:
                del self.tools[tool_name]
        self._mcp_tools.clear()

        # Close all clients
        if self._mcp_registry:
            self._mcp_registry.close_all()
            self._mcp_registry.reload()

        # Reinitialize
        if _MCP_AVAILABLE:
            self._init_mcp_tools()

        return len(self._mcp_tools)

    def close_mcp(self) -> None:
        """Close all MCP connections."""
        if self._mcp_registry:
            self._mcp_registry.close_all()
