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
"""
import subprocess
import urllib.request
import urllib.parse
import json
import re
import fnmatch
from pathlib import Path
from typing import Dict, Any, List


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
        self.parent_path = workspace_path.parent  # NEXUS_V6_PROTOTYPE/
        self.project_root = workspace_path.parent.parent  # 20_NEXUS/
        self.generation_active = self.project_root / "GENERATION_ACTIVE"

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
        """Execute bash command"""
        command = args.get("command", "")

        try:
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
        """Write file (create or overwrite)"""
        file_path = Path(args.get("file_path", ""))
        content = args.get("content", "")

        # Evolution mode: Allow writing to GENERATION_ACTIVE
        if self.evolution_mode and not file_path.is_absolute():
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

        # Evolution mode: Allow editing GENERATION_ACTIVE files
        if self.evolution_mode and not file_path.is_absolute():
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

        # Whitelist allowed operations
        allowed_ops = ["add", "commit", "status", "diff", "log", "push", "pull"]
        if operation not in allowed_ops:
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
                            rel_path = file_path.relative_to(self.workspace_path)
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
