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
- create_tool: Create a dynamic Python tool (V7.8 Phase 12.5)
- delete_tool: Delete a dynamic tool (V7.8 Phase 12.5)
- list_dynamic_tools: List all dynamic tools (V7.8 Phase 12.5)
- run_dynamic_tool: Execute a dynamic tool (V7.8 Phase 12.5)
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

# V7.8 Phase 12.5: Dynamic Tool Generation imports
try:
    from core.execution.dynamic_tools import DynamicToolManager
    _DYNAMIC_TOOLS_AVAILABLE = True
except ImportError:
    _DYNAMIC_TOOLS_AVAILABLE = False
    DynamicToolManager = None


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

        # V8.3.1: SwarmBridge for swarm_delegate tool (set externally)
        self.swarm_bridge: Optional[Any] = None

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
            "todo_write": self._execute_todo_write,
            # V7.8 Phase 12.5: Dynamic Tool Generation
            "create_tool": self._execute_create_tool,
            "delete_tool": self._execute_delete_tool,
            "list_dynamic_tools": self._execute_list_dynamic_tools,
            "run_dynamic_tool": self._execute_run_dynamic_tool,
            # V8.3.1: SwarmTool - Swarm as invocable tool
            "swarm_delegate": self._execute_swarm_delegate,
        }

        # V7.6 Phase 12.3: MCP Registry and dynamic tools
        self._mcp_registry: Optional["MCPRegistry"] = None
        self._mcp_tools: Dict[str, Tuple[str, str]] = {}  # tool_name -> (server_name, mcp_tool_name)
        self._logger = logging.getLogger("nexus.tools")

        if _MCP_AVAILABLE:
            self._init_mcp_tools()

        # V7.8 Phase 12.5: Dynamic Tool Manager
        self._dynamic_tool_manager: Optional["DynamicToolManager"] = None
        if _DYNAMIC_TOOLS_AVAILABLE:
            self._init_dynamic_tools()

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

    # =========================================================================
    # V7.8 Phase 12.5: Dynamic Tool Generation
    # =========================================================================

    def _init_dynamic_tools(self) -> None:
        """
        Initialize the Dynamic Tool Manager.

        Called during __init__ if dynamic tools module is available.
        """
        try:
            self._dynamic_tool_manager = DynamicToolManager(self.workspace_path)
            tools_count = len(self._dynamic_tool_manager.list_tools())
            if tools_count > 0:
                self._logger.info(f"Loaded {tools_count} existing dynamic tool(s)")
        except Exception as e:
            self._logger.error(f"Failed to initialize Dynamic Tool Manager: {e}")
            self._dynamic_tool_manager = None

    def _execute_create_tool(self, args: Dict) -> ToolResult:
        """
        Create a new dynamic Python tool.

        Args:
            args: {
                "name": "tool_name",
                "code": "def run(x): return x * 2",
                "description": "Optional description"
            }

        Returns:
            ToolResult with creation status

        Example:
            {
                "name": "fibonacci",
                "code": "def run(n):\\n    if n <= 1: return n\\n    return run(n-1) + run(n-2)",
                "description": "Calculate fibonacci number"
            }
        """
        if self._dynamic_tool_manager is None:
            return ToolResult(
                tool_name="create_tool",
                status="ERROR",
                output="",
                error="Dynamic Tool Manager not available"
            )

        name = args.get("name", "")
        code = args.get("code", "")
        description = args.get("description", "")

        if not name:
            return ToolResult(
                tool_name="create_tool",
                status="ERROR",
                output="",
                error="Tool name is required"
            )

        if not code:
            return ToolResult(
                tool_name="create_tool",
                status="ERROR",
                output="",
                error="Tool code is required"
            )

        result = self._dynamic_tool_manager.create_tool(name, code, description)

        if result.success:
            return ToolResult(
                tool_name="create_tool",
                status="SUCCESS",
                output=f"Tool '{name}' created successfully at {result.tool_path}\n\n"
                       f"Use 'run_dynamic_tool' with name='{name}' to execute it."
            )
        else:
            error_msg = result.error or "Unknown error"
            if result.validation_violations:
                error_msg += "\n\nValidation violations:\n"
                error_msg += "\n".join(f"  - {v}" for v in result.validation_violations)

            return ToolResult(
                tool_name="create_tool",
                status="FAILURE",
                output="",
                error=error_msg
            )

    def _execute_delete_tool(self, args: Dict) -> ToolResult:
        """
        Delete a dynamic tool.

        Args:
            args: {
                "name": "tool_name"
            }

        Returns:
            ToolResult with deletion status
        """
        if self._dynamic_tool_manager is None:
            return ToolResult(
                tool_name="delete_tool",
                status="ERROR",
                output="",
                error="Dynamic Tool Manager not available"
            )

        name = args.get("name", "")

        if not name:
            return ToolResult(
                tool_name="delete_tool",
                status="ERROR",
                output="",
                error="Tool name is required"
            )

        success, message = self._dynamic_tool_manager.delete_tool(name)

        return ToolResult(
            tool_name="delete_tool",
            status="SUCCESS" if success else "FAILURE",
            output=message if success else "",
            error="" if success else message
        )

    def _execute_list_dynamic_tools(self, args: Dict) -> ToolResult:
        """
        List all available dynamic tools.

        Args:
            args: {} (no arguments required)

        Returns:
            ToolResult with list of tools
        """
        if self._dynamic_tool_manager is None:
            return ToolResult(
                tool_name="list_dynamic_tools",
                status="ERROR",
                output="",
                error="Dynamic Tool Manager not available"
            )

        tools = self._dynamic_tool_manager.list_tools()

        if not tools:
            return ToolResult(
                tool_name="list_dynamic_tools",
                status="SUCCESS",
                output="No dynamic tools found.\n\n"
                       "Use 'create_tool' to create a new tool."
            )

        output = f"Found {len(tools)} dynamic tool(s):\n\n"
        for tool in tools:
            output += f"  - {tool.name}: {tool.description}\n"
            output += f"    Created: {tool.created_at}\n"

        return ToolResult(
            tool_name="list_dynamic_tools",
            status="SUCCESS",
            output=output
        )

    def _execute_run_dynamic_tool(self, args: Dict) -> ToolResult:
        """
        Execute a dynamic tool.

        Args:
            args: {
                "name": "tool_name",
                "args": {"arg1": value1, ...}  # Arguments for the tool
            }

        Returns:
            ToolResult with execution output

        Example:
            {
                "name": "fibonacci",
                "args": {"n": 10}
            }
        """
        if self._dynamic_tool_manager is None:
            return ToolResult(
                tool_name="run_dynamic_tool",
                status="ERROR",
                output="",
                error="Dynamic Tool Manager not available"
            )

        name = args.get("name", "")
        tool_args = args.get("args", {})

        if not name:
            return ToolResult(
                tool_name="run_dynamic_tool",
                status="ERROR",
                output="",
                error="Tool name is required"
            )

        result = self._dynamic_tool_manager.execute_tool(name, tool_args)

        if result.timed_out:
            return ToolResult(
                tool_name="run_dynamic_tool",
                status="TIMEOUT",
                output="",
                error=result.error
            )

        return ToolResult(
            tool_name="run_dynamic_tool",
            status="SUCCESS" if result.success else "FAILURE",
            output=result.output,
            error=result.error
        )

    # =========================================================================
    # V8.3.1: SwarmTool - Swarm as Invocable Tool
    # =========================================================================

    def _execute_swarm_delegate(self, args: Dict) -> ToolResult:
        """
        V8.3.1 SwarmTool - Delegate subtask to Swarm Engine.

        Allows agents to invoke Swarm collaboration modes at any HiveMind phase,
        not just Phase 4 (Execution). Enables debates, parallel analysis, etc.

        Args:
            args: {
                "task": "The subtask to delegate",
                "mode": "parallel|sequential|lead_support|ping_pong|specialist|red_blue",
                "phase": "analysis|debate|architecture|execution|diagnosis|consolidation" (optional),
                "context_categories": ["task", "architecture", ...] (optional)
            }

        Returns:
            ToolResult with swarm execution output

        Examples:
            {"task": "Run security review", "mode": "red_blue", "phase": "debate"}
            {"task": "Analyze files in parallel", "mode": "parallel"}
            {"task": "Iterative refinement", "mode": "ping_pong", "phase": "architecture"}
        """
        # V8.3.1-hotfix: Anti-recursion depth guard ("Inception Trap" prevention)
        # Prevents: Swarm → swarm_delegate → Swarm → swarm_delegate → ... (infinite)
        MAX_SWARM_DEPTH = 2
        current_depth = args.get("_swarm_depth", 0)

        if current_depth >= MAX_SWARM_DEPTH:
            self._logger.warning(
                f"swarm_delegate blocked: depth {current_depth} >= max {MAX_SWARM_DEPTH}"
            )
            return ToolResult(
                tool_name="swarm_delegate",
                status="ERROR",
                output="",
                error=f"Max swarm recursion depth ({MAX_SWARM_DEPTH}) reached. "
                      f"Nested Swarm calls are limited to prevent infinite loops."
            )

        # Guard: SwarmBridge must be configured
        if self.swarm_bridge is None:
            return ToolResult(
                tool_name="swarm_delegate",
                status="ERROR",
                output="",
                error="SwarmBridge not configured. Cannot delegate to Swarm."
            )

        task = args.get("task")
        mode_str = args.get("mode", "specialist")
        phase_str = args.get("phase")
        context_categories = args.get("context_categories")

        # V8.3.1-hotfix: Propagate depth to nested calls
        next_depth = current_depth + 1

        # Validate task
        if not task:
            return ToolResult(
                tool_name="swarm_delegate",
                status="ERROR",
                output="",
                error="Missing 'task' argument. Provide the subtask to delegate."
            )

        try:
            # Import locally to avoid circular imports
            from core.swarm.collaboration_modes import CollaborationMode
            from core.hive_mind.swarm_bridge import HivePhase

            # Parse mode
            try:
                mode = CollaborationMode.from_string(mode_str)
            except (ValueError, AttributeError):
                # Fallback: try direct enum access
                mode_upper = mode_str.upper()
                if hasattr(CollaborationMode, mode_upper):
                    mode = CollaborationMode[mode_upper]
                else:
                    valid_modes = [m.value for m in CollaborationMode]
                    return ToolResult(
                        tool_name="swarm_delegate",
                        status="ERROR",
                        output="",
                        error=f"Invalid mode: '{mode_str}'. Valid modes: {valid_modes}"
                    )

            # Parse phase (optional)
            phase = None
            if phase_str:
                try:
                    phase = HivePhase(phase_str.lower())
                except ValueError:
                    valid_phases = [p.value for p in HivePhase]
                    return ToolResult(
                        tool_name="swarm_delegate",
                        status="ERROR",
                        output="",
                        error=f"Invalid phase: '{phase_str}'. Valid phases: {valid_phases}"
                    )

            # Execute delegation (async → sync wrapper)
            import asyncio

            # Get or create event loop
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            result = loop.run_until_complete(
                self.swarm_bridge.delegate(
                    task=task,
                    mode=mode,
                    phase=phase,
                    context_categories=context_categories,
                    # V8.3.1-hotfix: Pass depth for recursion tracking
                    config={"_swarm_depth": next_depth}
                )
            )

            # FEEDBACK LOOP: Inject results into HiveMind context
            if result.success and hasattr(self.swarm_bridge, 'inject_results_into_context'):
                self.swarm_bridge.inject_results_into_context(result)

            # Build output with metadata
            output_parts = [result.summary] if result.summary else []
            if result.fallback_chain and len(result.fallback_chain) > 1:
                chain_str = " -> ".join(m.value for m in result.fallback_chain)
                output_parts.append(f"[Fallback chain: {chain_str}]")
            output_parts.append(f"[Mode: {result.mode_used.value}, Time: {result.execution_time:.2f}s]")

            return ToolResult(
                tool_name="swarm_delegate",
                status="SUCCESS" if result.success else "FAILURE",
                output="\n".join(output_parts),
                error="; ".join(result.failure_diagnostics) if not result.success else ""
            )

        except Exception as e:
            self._logger.error(f"swarm_delegate failed: {e}")
            return ToolResult(
                tool_name="swarm_delegate",
                status="ERROR",
                output="",
                error=f"Swarm delegation error: {str(e)}"
            )

    def get_dynamic_tools(self) -> List[str]:
        """
        Get list of available dynamic tools.

        Returns:
            List of dynamic tool names
        """
        if self._dynamic_tool_manager is None:
            return []
        return [t.name for t in self._dynamic_tool_manager.list_tools()]
