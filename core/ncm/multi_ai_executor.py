"""
Multi-AI Executor for NCM Phase 2B Acceleration.

Routes NCM stories to optimal AI providers and enables parallel execution
for 3-4x performance improvement.

Providers:
- SimpleExecutor: Trivial tasks (dead_import) - ~6s/story
- OpenCode/GLM: Simple tasks (missing_doc) - ~45s/story
- Codex: Moderate tasks (type_error) - ~90s/story
- NEXUS: Complex tasks (dead_code, refactoring) - ~5min/story

Usage:
    executor = MultiAIExecutor(config)
    results = await executor.execute_phase2b(stories)

Author: Claude (NEXUS V12.4)
Date: 2026-01-21
"""

from __future__ import annotations

import asyncio
import json
import os
import signal
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import logging

# Use standard logging instead of structlog for compatibility
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# =============================================================================
# Routing Configuration
# =============================================================================

ROUTING_MATRIX = {
    # Category → (Provider, Estimated Time in seconds)
    # Providers: simple (no AI), opencode (CLI), kimi (K2 Thinking), claude (headless), nexus (full orchestration)
    "dead_import": ("simple", 6),
    "missing_doc": ("opencode", 45),      # OpenCode CLI via Zen subscription
    "type_error": ("kimi", 60),           # Kimi K2 Thinking CLI
    "dead_code": ("claude", 120),         # Claude Code CLI for complex analysis
    "refactoring": ("nexus", 300),        # Full NEXUS for major refactoring
    "security": ("kimi", 90),             # Kimi for security analysis
    "deprecation": ("opencode", 30),      # Simple deprecation fixes
}


def _discover_cli_path(cli_name: str) -> Optional[str]:
    """
    Auto-discover CLI path using 'where' (Windows) or 'which' (Unix).

    Args:
        cli_name: Name of the CLI to find (e.g., 'opencode', 'kimi', 'claude')

    Returns:
        Full path to CLI if found, None otherwise
    """
    import shutil
    import subprocess

    # First try shutil.which (cross-platform)
    path = shutil.which(cli_name)
    if path:
        return path

    # On Windows, try with .cmd and .exe extensions
    if os.name == 'nt':
        for ext in ['.cmd', '.exe', '.bat']:
            path = shutil.which(cli_name + ext)
            if path:
                return path

    # Fallback: try 'where' on Windows or 'which' on Unix
    try:
        cmd = 'where' if os.name == 'nt' else 'which'
        result = subprocess.run(
            [cmd, cli_name],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip().split('\n')[0]
    except Exception:
        pass

    return None


@dataclass
class MultiAIExecutorConfig:
    """Configuration for Multi-AI Executor."""

    # Workspace
    workspace_path: Path = field(default_factory=Path.cwd)
    stories_path: Optional[Path] = None

    # Execution mode
    parallel_workers: int = 3  # Number of parallel workers

    # Provider configs
    opencode_server_url: str = "http://localhost:5173"
    opencode_model: str = "glm-4.7"
    codex_model: str = "gpt-5.2-codex"
    codex_reasoning: str = "xhigh"

    # CLI Paths - Auto-discovered or configured via .env
    # Set these via env vars: OPENCODE_CLI_PATH, KIMI_CLI_PATH, CLAUDE_CLI_PATH
    # If not set, will auto-discover from PATH
    opencode_cli: Optional[str] = None
    kimi_cli: Optional[str] = None
    claude_cli: Optional[str] = None

    # Timeouts
    simple_timeout: float = 30.0
    opencode_timeout: float = 120.0
    codex_timeout: float = 300.0
    nexus_timeout: float = 600.0

    # State persistence
    state_file: str = "workspace/ncm/multi_ai_state.json"
    log_dir: str = "workspace/ncm/logs"

    # Verbose logging
    verbose: bool = True

    def __post_init__(self):
        """Auto-discover CLI paths if not provided."""
        # Check env vars first, then auto-discover
        if self.opencode_cli is None:
            self.opencode_cli = os.environ.get("OPENCODE_CLI_PATH") or _discover_cli_path("opencode")
        if self.kimi_cli is None:
            self.kimi_cli = os.environ.get("KIMI_CLI_PATH") or _discover_cli_path("kimi")
        if self.claude_cli is None:
            self.claude_cli = os.environ.get("CLAUDE_CLI_PATH") or _discover_cli_path("claude")

        # Log discovered paths
        logger.info(f"CLI paths discovered: opencode={self.opencode_cli}, kimi={self.kimi_cli}, claude={self.claude_cli}")


@dataclass
class StoryResult:
    """Result of story execution."""
    story_id: str
    category: str
    provider: str
    status: str  # SUCCESS, FAILED, SKIPPED
    duration_seconds: float
    error: Optional[str] = None
    output: Optional[str] = None
    tokens_used: int = 0


class MultiAIExecutor:
    """
    Multi-AI Executor for accelerated NCM story execution.

    Routes stories to optimal providers based on category:
    - dead_import → SimpleExecutor (fast, no AI)
    - missing_doc → OpenCode/GLM (free, simple tasks)
    - type_error → Codex (paid, moderate complexity)
    - dead_code → NEXUS (full orchestration)
    """

    def __init__(self, config: MultiAIExecutorConfig):
        """Initialize Multi-AI Executor."""
        self.config = config
        self.workspace_path = config.workspace_path

        # State
        self._state: Dict[str, Any] = {}
        self._pause_requested = False
        self._results: List[StoryResult] = []

        # Drivers (lazy init)
        self._opencode_driver: Optional[AsyncOpenCodeDriver] = None
        self._codex_driver: Optional[AsyncCodexDriver] = None

        # Setup paths
        self.state_path = self.workspace_path / config.state_file
        self.log_dir = self.workspace_path / config.log_dir
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Log file
        self.log_file = self.log_dir / f"multi_ai_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl"

        logger.info(f"multi_ai_executor_initialized: workers={config.parallel_workers}, log={self.log_file}")

    # =========================================================================
    # Driver Management
    # =========================================================================

    async def _get_opencode_driver(self) -> AsyncOpenCodeDriver:
        """Get or create OpenCode driver."""
        if self._opencode_driver is None:
            config = AsyncOpenCodeDriverConfig(
                server_url=self.config.opencode_server_url,
                model=self.config.opencode_model,
                timeout=self.config.opencode_timeout,
                workspace_path=self.workspace_path,
            )
            self._opencode_driver = AsyncOpenCodeDriver(config)
        return self._opencode_driver

    async def _get_codex_driver(self) -> AsyncCodexDriver:
        """Get or create Codex driver."""
        if self._codex_driver is None:
            config = AsyncCodexDriverConfig(
                model=self.config.codex_model,
                reasoning_effort=self.config.codex_reasoning,
                timeout=self.config.codex_timeout,
                workspace_path=self.workspace_path,
            )
            self._codex_driver = AsyncCodexDriver(config)
        return self._codex_driver

    async def close_drivers(self):
        """Close all drivers."""
        if self._opencode_driver:
            await self._opencode_driver.close()
            self._opencode_driver = None
        if self._codex_driver:
            await self._codex_driver.close()
            self._codex_driver = None

    # =========================================================================
    # Story Routing
    # =========================================================================

    def _route_story(self, story: Dict) -> Tuple[str, int]:
        """
        Route story to optimal provider.

        Args:
            story: Story dict with 'category' field

        Returns:
            Tuple of (provider_name, estimated_seconds)
        """
        category = story.get("category", "unknown")
        return ROUTING_MATRIX.get(category, ("nexus", 300))

    def _group_stories_by_provider(
        self,
        stories: List[Dict]
    ) -> Dict[str, List[Dict]]:
        """Group stories by their target provider."""
        groups: Dict[str, List[Dict]] = {
            "simple": [],
            "opencode": [],
            "kimi": [],
            "claude": [],
            "nexus": [],
        }

        for story in stories:
            provider, _ = self._route_story(story)
            # Normalize codex to kimi
            if provider == "codex":
                provider = "kimi"
            if provider in groups:
                groups[provider].append(story)
            else:
                groups["nexus"].append(story)

        return groups

    # =========================================================================
    # Story Execution
    # =========================================================================

    async def _execute_simple(self, story: Dict) -> StoryResult:
        """Execute simple story (dead import removal)."""
        import re
        start_time = time.time()
        story_id = story.get("story_id", "unknown")

        try:
            # Get file path (make absolute if relative)
            file_path_str = story.get("target_file", "")
            if not file_path_str:
                file_path_str = story.get("target_files", [""])[0]

            file_path = Path(file_path_str)
            if not file_path.is_absolute():
                file_path = self.workspace_path / file_path

            # Get import to remove
            import_text = story.get("import_text", "")
            description = story.get("description", "")

            # Parse import from description if not in metadata
            if not import_text:
                # Pattern: "Import 'X' from 'Y' may be unused"
                match = re.search(r"Import '([^']+)' from '([^']+)'", description)
                if match:
                    import_text = match.group(1)

            # Parse line number from description
            line_number = story.get("line_number")
            if not line_number:
                line_match = re.search(r"Line (\d+):", description)
                if line_match:
                    line_number = int(line_match.group(1))

            if not file_path.exists():
                duration = time.time() - start_time
                return StoryResult(
                    story_id=story_id,
                    category="dead_import",
                    provider="simple",
                    status="SKIPPED",
                    duration_seconds=duration,
                    error=f"File not found: {file_path}",
                )

            content = file_path.read_text(encoding="utf-8")
            lines = content.split("\n")
            removed_lines = []

            # Strategy 1: Remove by line number if known
            if line_number and 0 < line_number <= len(lines):
                line_content = lines[line_number - 1]
                # Verify this line contains the import
                if import_text and import_text in line_content:
                    removed_lines.append(lines.pop(line_number - 1))

            # Strategy 2: Remove by import name if line number didn't work
            if not removed_lines and import_text:
                new_lines = []
                for line in lines:
                    # Check if this line is an import containing import_text
                    is_import = (line.strip().startswith("import ") or
                                line.strip().startswith("from "))
                    if is_import and import_text in line:
                        removed_lines.append(line)
                    else:
                        new_lines.append(line)
                lines = new_lines

            if removed_lines:
                file_path.write_text("\n".join(lines), encoding="utf-8")
                duration = time.time() - start_time
                return StoryResult(
                    story_id=story_id,
                    category="dead_import",
                    provider="simple",
                    status="SUCCESS",
                    duration_seconds=duration,
                    output=f"Removed {len(removed_lines)} import(s): {removed_lines[0].strip()[:50]}",
                )

            duration = time.time() - start_time
            return StoryResult(
                story_id=story_id,
                category="dead_import",
                provider="simple",
                status="SKIPPED",
                duration_seconds=duration,
                error=f"Import '{import_text}' not found in file",
            )

        except Exception as e:
            duration = time.time() - start_time
            return StoryResult(
                story_id=story_id,
                category="dead_import",
                provider="simple",
                status="FAILED",
                duration_seconds=duration,
                error=str(e),
            )

    async def _execute_opencode(self, story: Dict) -> StoryResult:
        """
        Execute story via OpenCode CLI (authenticated via Zen subscription).

        Uses: echo prompt | opencode run --format json
        Note: Uses stdin to avoid Windows command line length limits.
        Reference: https://opencode.ai/docs/cli/
        """
        start_time = time.time()
        story_id = story.get("story_id", "unknown")
        category = story.get("category", "unknown")

        try:
            # Check if CLI is available
            opencode_path = self.config.opencode_cli
            if not opencode_path:
                return StoryResult(
                    story_id=story_id,
                    category=category,
                    provider="opencode",
                    status="SKIPPED",
                    duration_seconds=time.time() - start_time,
                    error="OpenCode CLI not found. Install with: npm install -g opencode",
                )

            # Build prompt for the task (shorter version without full file content)
            prompt = self._build_prompt(story, include_context=False)

            # Use OpenCode CLI with JSON output format
            # Pass prompt via stdin to avoid command line length limits
            proc = await asyncio.create_subprocess_exec(
                opencode_path, "run",
                "--format", "json",
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(self.workspace_path),
            )

            # Send prompt via stdin
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(input=prompt.encode("utf-8")),
                timeout=self.config.opencode_timeout,
            )

            duration = time.time() - start_time
            output = stdout.decode("utf-8", errors="replace").strip()

            if proc.returncode == 0 and output:
                # Parse JSON events from output (newline-delimited)
                result_text = self._parse_json_events(output)

                # Apply the changes if code was generated
                if result_text:
                    await self._apply_changes(story, result_text)

                return StoryResult(
                    story_id=story_id,
                    category=category,
                    provider="opencode",
                    status="SUCCESS",
                    duration_seconds=duration,
                    output=result_text[:500] if result_text else output[:500],
                )
            else:
                error_msg = stderr.decode("utf-8", errors="replace").strip() or "Empty response"
                return StoryResult(
                    story_id=story_id,
                    category=category,
                    provider="opencode",
                    status="FAILED",
                    duration_seconds=duration,
                    error=error_msg[:200],
                )

        except asyncio.TimeoutError:
            duration = time.time() - start_time
            return StoryResult(
                story_id=story_id,
                category=category,
                provider="opencode",
                status="FAILED",
                duration_seconds=duration,
                error="Timeout",
            )
        except asyncio.CancelledError:
            raise  # Re-raise for proper cancellation handling
        except Exception as e:
            duration = time.time() - start_time
            return StoryResult(
                story_id=story_id,
                category=category,
                provider="opencode",
                status="FAILED",
                duration_seconds=duration,
                error=str(e),
            )

    async def _execute_codex(self, story: Dict) -> StoryResult:
        """
        Execute story via Kimi K2 Thinking CLI (authenticated subscription).

        Uses: kimi --print -p "prompt" --yolo --output-format stream-json
        Note: Uses short prompts (CLI reads files natively) to avoid command line limits.
        Reference: https://github.com/MoonshotAI/kimi-cli

        Key flags:
        - --print: Non-interactive mode (required for automation)
        - --yolo: Auto-approve all file/shell operations
        - --output-format stream-json: Newline-delimited JSON for parsing
        """
        start_time = time.time()
        story_id = story.get("story_id", "unknown")
        category = story.get("category", "unknown")

        try:
            # Check if CLI is available
            kimi_path = self.config.kimi_cli
            if not kimi_path:
                return StoryResult(
                    story_id=story_id,
                    category=category,
                    provider="kimi",
                    status="SKIPPED",
                    duration_seconds=time.time() - start_time,
                    error="Kimi CLI not found. Install with: pip install kimi-cli",
                )

            # Build prompt WITHOUT file content (Kimi can read files natively)
            # This avoids Windows command line length limits
            prompt = self._build_prompt(story, include_context=False)

            # Use Kimi CLI with proper automation flags
            # --print: Non-interactive mode
            # --yolo: Auto-approve all actions (critical for automation)
            # --output-format stream-json: Parseable output
            proc = await asyncio.create_subprocess_exec(
                kimi_path,
                "--print",
                "-p", prompt,
                "--yolo",
                "--output-format", "stream-json",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(self.workspace_path),
            )

            stdout, stderr = await asyncio.wait_for(
                proc.communicate(),
                timeout=self.config.codex_timeout,
            )

            duration = time.time() - start_time
            output = stdout.decode("utf-8", errors="replace").strip()

            if proc.returncode == 0 and output:
                # Parse JSON events from stream-json output
                result_text = self._parse_json_events(output)

                # Apply the changes if code was generated
                if result_text:
                    await self._apply_changes(story, result_text)

                return StoryResult(
                    story_id=story_id,
                    category=category,
                    provider="kimi",
                    status="SUCCESS",
                    duration_seconds=duration,
                    output=result_text[:500] if result_text else output[:500],
                )
            else:
                error_msg = stderr.decode("utf-8", errors="replace").strip() or "Empty response"
                return StoryResult(
                    story_id=story_id,
                    category=category,
                    provider="kimi",
                    status="FAILED",
                    duration_seconds=duration,
                    error=error_msg[:200],
                )

        except asyncio.TimeoutError:
            duration = time.time() - start_time
            return StoryResult(
                story_id=story_id,
                category=category,
                provider="kimi",
                status="FAILED",
                duration_seconds=duration,
                error="Timeout",
            )
        except asyncio.CancelledError:
            raise  # Re-raise for proper cancellation handling
        except Exception as e:
            duration = time.time() - start_time
            return StoryResult(
                story_id=story_id,
                category=category,
                provider="kimi",
                status="FAILED",
                duration_seconds=duration,
                error=str(e),
            )

    async def _execute_nexus(self, story: Dict) -> StoryResult:
        """Execute story via full NEXUS orchestration."""
        start_time = time.time()
        story_id = story.get("story_id", "unknown")
        category = story.get("category", "unknown")

        try:
            # For NEXUS stories, we use subprocess to call the orchestrator
            # This is a placeholder - actual implementation would invoke OrchestratorV7
            prompt = self._build_prompt(story, include_context=True)

            # TODO: Implement actual NEXUS orchestration call
            # For now, mark as pending for manual execution
            duration = time.time() - start_time
            return StoryResult(
                story_id=story_id,
                category=category,
                provider="nexus",
                status="PENDING",
                duration_seconds=duration,
                error="NEXUS orchestration not yet integrated",
            )

        except Exception as e:
            duration = time.time() - start_time
            return StoryResult(
                story_id=story_id,
                category=category,
                provider="nexus",
                status="FAILED",
                duration_seconds=duration,
                error=str(e),
            )

    async def execute_story(self, story: Dict) -> StoryResult:
        """Execute a single story with appropriate provider."""
        provider, _ = self._route_story(story)

        if provider == "simple":
            return await self._execute_simple(story)
        elif provider == "opencode":
            return await self._execute_opencode(story)
        elif provider in ("kimi", "codex"):
            return await self._execute_codex(story)  # Uses Kimi K2 CLI
        elif provider == "claude":
            return await self._execute_claude(story)  # Uses Claude Code CLI
        else:
            return await self._execute_nexus(story)

    # =========================================================================
    # Prompt Building
    # =========================================================================

    def _build_prompt(self, story: Dict, include_context: bool = False) -> str:
        """Build prompt for AI execution."""
        category = story.get("category", "unknown")
        description = story.get("description", "")
        target_file = story.get("target_file", "")

        prompt_parts = [f"Task: {description}"]

        if target_file:
            prompt_parts.append(f"File: {target_file}")

            if include_context and Path(target_file).exists():
                try:
                    content = Path(target_file).read_text(encoding="utf-8")
                    # Limit context size
                    if len(content) > 10000:
                        content = content[:10000] + "\n... (truncated)"
                    prompt_parts.append(f"\nCurrent content:\n```python\n{content}\n```")
                except Exception:
                    pass

        if category == "type_error":
            prompt_parts.append("\nAdd appropriate type hints to fix type errors.")
        elif category == "missing_doc":
            prompt_parts.append("\nAdd Google-style docstrings with Args, Returns, Raises sections.")
        elif category == "dead_code":
            prompt_parts.append("\nRemove unused/dead code while preserving functionality.")

        return "\n".join(prompt_parts)

    async def _apply_changes(self, story: Dict, ai_output: str):
        """Apply AI-generated changes to file."""
        target_file = story.get("target_file")
        if not target_file:
            return

        # Extract code from AI output (between ```python and ```)
        import re
        code_match = re.search(r'```python\n(.*?)```', ai_output, re.DOTALL)
        if code_match:
            new_content = code_match.group(1)
            Path(target_file).write_text(new_content, encoding="utf-8")

    def _parse_json_events(self, output: str) -> str:
        """
        Parse newline-delimited JSON events from CLI output.

        Both OpenCode (--format json) and Kimi (--output-format stream-json)
        return newline-delimited JSON events. Extract the final content.

        Args:
            output: Raw CLI output (may be JSON or text)

        Returns:
            Extracted text content from JSON events, or original output if not JSON
        """
        if not output:
            return ""

        result_parts = []

        for line in output.strip().split('\n'):
            line = line.strip()
            if not line:
                continue

            # Try to parse as JSON
            try:
                event = json.loads(line)

                # Handle different JSON event formats
                if isinstance(event, dict):
                    # OpenCode format: {"type": "...", "content": "..."}
                    if "content" in event:
                        result_parts.append(event["content"])
                    # Kimi format: {"type": "text", "text": "..."}
                    elif "text" in event:
                        result_parts.append(event["text"])
                    # Claude format: {"result": "..."}
                    elif "result" in event:
                        result_parts.append(event["result"])
                    # Generic message format
                    elif "message" in event:
                        result_parts.append(event["message"])

            except json.JSONDecodeError:
                # Not JSON, treat as plain text
                result_parts.append(line)

        return "\n".join(result_parts) if result_parts else output

    async def _execute_claude(self, story: Dict) -> StoryResult:
        """
        Execute story via Claude Code CLI (headless mode with full autonomy).

        Uses: claude -p "prompt" --output-format json --dangerously-skip-permissions
        Reference: https://docs.anthropic.com/en/docs/claude-code/cli-usage

        Key flags:
        - -p: Print mode (non-interactive, outputs result and exits)
        - --output-format json: Structured JSON output for parsing
        - --dangerously-skip-permissions: CRITICAL - Skip all permission prompts
          This enables fully autonomous execution without manual approval.
          Required for NCM automation pipeline.
        """
        start_time = time.time()
        story_id = story.get("story_id", "unknown")
        category = story.get("category", "unknown")

        try:
            # Check if CLI is available
            claude_path = self.config.claude_cli
            if not claude_path:
                return StoryResult(
                    story_id=story_id,
                    category=category,
                    provider="claude",
                    status="SKIPPED",
                    duration_seconds=time.time() - start_time,
                    error="Claude CLI not found. Install with: npm install -g @anthropic-ai/claude-code",
                )

            # Build prompt WITHOUT file content (Claude can read files natively)
            # This avoids Windows command line length limits
            prompt = self._build_prompt(story, include_context=False)

            # Use Claude CLI with headless mode flags for FULL AUTONOMY
            # -p: Print mode (non-interactive)
            # --output-format json: Structured output
            # --dangerously-skip-permissions: Skip ALL permission prompts (autonomous)
            proc = await asyncio.create_subprocess_exec(
                claude_path,
                "-p", prompt,
                "--output-format", "json",
                "--dangerously-skip-permissions",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(self.workspace_path),
            )

            stdout, stderr = await asyncio.wait_for(
                proc.communicate(),
                timeout=self.config.codex_timeout,  # Reuse codex timeout
            )

            duration = time.time() - start_time
            output = stdout.decode("utf-8", errors="replace").strip()

            if proc.returncode == 0 and output:
                # Parse JSON output
                result_text = self._parse_json_events(output)

                # Apply the changes if code was generated
                if result_text:
                    await self._apply_changes(story, result_text)

                return StoryResult(
                    story_id=story_id,
                    category=category,
                    provider="claude",
                    status="SUCCESS",
                    duration_seconds=duration,
                    output=result_text[:500] if result_text else output[:500],
                )
            else:
                error_msg = stderr.decode("utf-8", errors="replace").strip() or "Empty response"
                return StoryResult(
                    story_id=story_id,
                    category=category,
                    provider="claude",
                    status="FAILED",
                    duration_seconds=duration,
                    error=error_msg[:200],
                )

        except asyncio.TimeoutError:
            duration = time.time() - start_time
            return StoryResult(
                story_id=story_id,
                category=category,
                provider="claude",
                status="FAILED",
                duration_seconds=duration,
                error="Timeout",
            )
        except asyncio.CancelledError:
            raise
        except Exception as e:
            duration = time.time() - start_time
            return StoryResult(
                story_id=story_id,
                category=category,
                provider="claude",
                status="FAILED",
                duration_seconds=duration,
                error=str(e),
            )

    # =========================================================================
    # Parallel Execution
    # =========================================================================

    async def execute_parallel(
        self,
        stories: List[Dict],
        max_concurrent: int = 3
    ) -> List[StoryResult]:
        """
        Execute stories in parallel with worker pool.

        Args:
            stories: List of stories to execute
            max_concurrent: Maximum concurrent executions

        Returns:
            List of StoryResults
        """
        results: List[StoryResult] = []
        semaphore = asyncio.Semaphore(max_concurrent)

        async def execute_with_semaphore(story: Dict) -> StoryResult:
            async with semaphore:
                if self._pause_requested:
                    return StoryResult(
                        story_id=story.get("story_id", "unknown"),
                        category=story.get("category", "unknown"),
                        provider="none",
                        status="PAUSED",
                        duration_seconds=0,
                    )
                return await self.execute_story(story)

        # Create tasks for all stories
        tasks = [execute_with_semaphore(story) for story in stories]

        # Execute with progress tracking
        total = len(tasks)
        completed = 0

        for coro in asyncio.as_completed(tasks):
            result = await coro
            results.append(result)
            completed += 1

            # Log progress
            self._log_result(result)

            if self.config.verbose:
                status_char = "OK" if result.status == "SUCCESS" else "FAIL"
                print(f"  [{completed}/{total}] {status_char} {result.story_id} "
                      f"({result.provider}) - {result.duration_seconds:.1f}s")

            if self._pause_requested:
                break

        return results

    # =========================================================================
    # State Management
    # =========================================================================

    def _load_state(self) -> Dict[str, Any]:
        """Load execution state from disk."""
        if self.state_path.exists():
            with open(self.state_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {
            "completed_stories": [],
            "failed_stories": [],
            "last_run": None,
            "total_tokens": 0,
        }

    def _save_state(self):
        """Save execution state to disk."""
        self._state["last_run"] = datetime.now().isoformat()
        self._state["completed_stories"] = [
            r.story_id for r in self._results if r.status == "SUCCESS"
        ]
        self._state["failed_stories"] = [
            r.story_id for r in self._results if r.status == "FAILED"
        ]
        self._state["total_tokens"] = sum(r.tokens_used for r in self._results)

        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.state_path, "w", encoding="utf-8") as f:
            json.dump(self._state, f, indent=2)

    def _log_result(self, result: StoryResult):
        """Log result to JSONL file."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "story_id": result.story_id,
            "category": result.category,
            "provider": result.provider,
            "status": result.status,
            "duration_seconds": result.duration_seconds,
            "tokens_used": result.tokens_used,
            "error": result.error,
        }

        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")

    # =========================================================================
    # Main Execution
    # =========================================================================

    async def execute_phase2b(
        self,
        stories_path: Optional[Path] = None,
        resume: bool = True
    ) -> Dict[str, Any]:
        """
        Execute Phase 2B stories with multi-AI acceleration.

        Args:
            stories_path: Path to stories JSON file
            resume: Whether to resume from last state

        Returns:
            Execution summary dict
        """
        print("=" * 60)
        print("NCM PHASE 2B - MULTI-AI ACCELERATED EXECUTION")
        print("=" * 60)

        # Load stories
        stories_path = stories_path or self.config.stories_path
        if not stories_path or not stories_path.exists():
            stories_path = self.workspace_path / "workspace/ncm/phase2b_stories.json"

        with open(stories_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Handle both formats: direct list or wrapped in "stories" key
        if isinstance(data, list):
            all_stories = data
        else:
            all_stories = data.get("stories", [])

        print(f"Total stories: {len(all_stories)}")

        # Load state and filter completed
        if resume:
            self._state = self._load_state()
            completed_ids = set(self._state.get("completed_stories", []))
            stories = [s for s in all_stories if s.get("story_id") not in completed_ids]
            print(f"Already completed: {len(completed_ids)}")
            print(f"Remaining: {len(stories)}")
        else:
            stories = all_stories
            self._state = {}

        if not stories:
            print("All stories already completed!")
            return {"status": "COMPLETE", "total": len(all_stories)}

        # Group by provider and show plan
        groups = self._group_stories_by_provider(stories)
        print("\nExecution Plan:")
        print("-" * 40)
        for provider, provider_stories in groups.items():
            if provider_stories:
                _, est_time = ROUTING_MATRIX.get(
                    provider_stories[0].get("category", "unknown"),
                    ("nexus", 300)
                )
                total_est = len(provider_stories) * est_time
                print(f"  {provider}: {len(provider_stories)} stories (~{total_est//60}m)")
        print("-" * 40)

        # Setup signal handler for pause
        def signal_handler(signum, frame):
            print("\n[PAUSE REQUESTED] Finishing current stories...")
            self._pause_requested = True

        signal.signal(signal.SIGINT, signal_handler)

        # Execute in optimal order
        start_time = time.time()

        try:
            # 1. Simple tasks first (fastest)
            if groups["simple"]:
                print(f"\n[1/5] Executing {len(groups['simple'])} simple tasks...")
                simple_results = await self.execute_parallel(
                    groups["simple"],
                    max_concurrent=10  # Very parallel for simple tasks
                )
                self._results.extend(simple_results)

            if self._pause_requested:
                self._save_state()
                return {"status": "PAUSED", "completed": len(self._results)}

            # 2. OpenCode tasks (free, moderate speed)
            if groups["opencode"]:
                print(f"\n[2/5] Executing {len(groups['opencode'])} OpenCode tasks...")
                opencode_results = await self.execute_parallel(
                    groups["opencode"],
                    max_concurrent=3
                )
                self._results.extend(opencode_results)

            if self._pause_requested:
                self._save_state()
                return {"status": "PAUSED", "completed": len(self._results)}

            # 3. Kimi K2 Thinking tasks (type errors, security)
            if groups["kimi"]:
                print(f"\n[3/5] Executing {len(groups['kimi'])} Kimi K2 tasks...")
                kimi_results = await self.execute_parallel(
                    groups["kimi"],
                    max_concurrent=2  # Respect rate limits
                )
                self._results.extend(kimi_results)

            if self._pause_requested:
                self._save_state()
                return {"status": "PAUSED", "completed": len(self._results)}

            # 4. Claude tasks (dead code removal, complex analysis)
            if groups["claude"]:
                print(f"\n[4/5] Executing {len(groups['claude'])} Claude tasks...")
                claude_results = await self.execute_parallel(
                    groups["claude"],
                    max_concurrent=2  # Respect rate limits
                )
                self._results.extend(claude_results)

            if self._pause_requested:
                self._save_state()
                return {"status": "PAUSED", "completed": len(self._results)}

            # 5. NEXUS tasks (complex, full orchestration)
            if groups["nexus"]:
                print(f"\n[5/5] Executing {len(groups['nexus'])} NEXUS tasks...")
                nexus_results = await self.execute_parallel(
                    groups["nexus"],
                    max_concurrent=1  # Sequential for complex tasks
                )
                self._results.extend(nexus_results)

        finally:
            # Always save state and close drivers
            self._save_state()
            await self.close_drivers()

        # Summary
        total_time = time.time() - start_time
        success_count = sum(1 for r in self._results if r.status == "SUCCESS")
        failed_count = sum(1 for r in self._results if r.status == "FAILED")
        total_tokens = sum(r.tokens_used for r in self._results)

        print("\n" + "=" * 60)
        print("EXECUTION COMPLETE")
        print("=" * 60)
        print(f"Total time: {total_time/60:.1f} minutes")
        print(f"Success: {success_count}/{len(self._results)} ({100*success_count/len(self._results):.1f}%)")
        print(f"Failed: {failed_count}")
        print(f"Total tokens: {total_tokens:,}")
        print(f"Log file: {self.log_file}")

        return {
            "status": "COMPLETE" if not self._pause_requested else "PAUSED",
            "total": len(self._results),
            "success": success_count,
            "failed": failed_count,
            "duration_minutes": total_time / 60,
            "total_tokens": total_tokens,
            "log_file": str(self.log_file),
        }


# =============================================================================
# CLI Entry Point
# =============================================================================

async def main():
    """CLI entry point for multi-AI executor."""
    import argparse

    parser = argparse.ArgumentParser(description="NCM Multi-AI Executor")
    parser.add_argument("--stories", type=str, help="Path to stories JSON file")
    parser.add_argument("--workers", type=int, default=3, help="Parallel workers")
    parser.add_argument("--reset", action="store_true", help="Reset state and start fresh")
    parser.add_argument("--verbose", action="store_true", default=True, help="Verbose output")

    args = parser.parse_args()

    config = MultiAIExecutorConfig(
        workspace_path=Path.cwd(),
        stories_path=Path(args.stories) if args.stories else None,
        parallel_workers=args.workers,
        verbose=args.verbose,
    )

    executor = MultiAIExecutor(config)
    result = await executor.execute_phase2b(resume=not args.reset)

    return result


if __name__ == "__main__":
    asyncio.run(main())
