"""
Prompt Refresh System - Blind Spot #3 Mitigation

Prevents prompt drift/decay during long-running execution by reloading
system prompts from disk every N tool calls.

Blind Spot #3: Prompt Decay
    - Long-running execution → prompt drift/decay
    - Stale context → hallucinations
    - Solution: Reload system prompts from disk periodically

Architecture:
    - Track tool calls count
    - Trigger refresh at configurable interval (default: 500 calls)
    - Reload prompts from prompts/ directory
    - Update orchestrator's prompt cache

Usage:
    from core.ncm.prompt_refresh import PromptRefreshSystem

    refresh_system = PromptRefreshSystem(
        prompts_dir=Path("prompts"),
        refresh_interval=500
    )

    # Track tool calls
    refresh_system.increment_tool_calls()

    # Check and refresh if needed
    if await refresh_system.check_and_refresh():
        print("Prompts refreshed!")
"""

from pathlib import Path
from typing import Dict, Optional, List
from datetime import datetime

from core.logging import get_logger


class PromptRefreshSystem:
    """
    Refresh agent prompts every N tool calls.

    Blind Spot #3 Mitigation:
        - Long-running execution → prompt drift/decay
        - Stale context → hallucinations
        - Solution: Reload system prompts from disk every 500 tool calls

    Process:
        1. Track tool calls count
        2. When count >= refresh_interval:
           a. Reload all prompts from prompts/ directory
           b. Update prompt cache (in-memory)
           c. Log refresh event
           d. Reset counter
        3. Return to normal execution

    NOTE: For Phase 0, this reloads prompts from disk into memory.
          Full orchestrator integration will be added in Phase 0.4.

    Usage:
        refresh_system = PromptRefreshSystem(
            prompts_dir=Path("prompts"),
            refresh_interval=500
        )

        # In main execution loop
        for tool_call in tool_calls:
            refresh_system.increment_tool_calls()
            if await refresh_system.check_and_refresh():
                # Prompts refreshed, continue
                pass
    """

    def __init__(
        self,
        prompts_dir: Path,
        refresh_interval: int = 500,
    ):
        """
        Initialize prompt refresh system.

        Args:
            prompts_dir: Path to prompts directory (e.g., Path("prompts"))
            refresh_interval: Tool calls before refresh (default: 500)

        Raises:
            ValueError: If prompts_dir doesn't exist or refresh_interval <= 0
        """
        if not prompts_dir.exists():
            raise ValueError(f"prompts_dir does not exist: {prompts_dir}")
        if refresh_interval <= 0:
            raise ValueError(f"refresh_interval must be positive, got {refresh_interval}")

        self.prompts_dir = prompts_dir
        self.refresh_interval = refresh_interval
        self.logger = get_logger()

        # Tool calls counter
        self.tool_calls_count = 0

        # Prompt cache (file_name → prompt_content)
        self.prompt_cache: Dict[str, str] = {}

        # Refresh history (for monitoring)
        self.refresh_history: List[Dict] = []

        # Initial load
        self._load_prompts()

        self.logger.info("prompt_refresh_system_initialized", {
            "prompts_dir": str(prompts_dir),
            "refresh_interval": refresh_interval,
            "prompts_loaded": len(self.prompt_cache)
        })

    def _load_prompts(self):
        """
        Load all prompts from prompts_dir into cache.

        Scans for .md files and loads their content.

        NOTE: For Phase 0, we load all .md files directly.
              Phase 0.4 will add support for templated prompts.
        """
        self.logger.debug("prompt_load_start", {
            "prompts_dir": str(self.prompts_dir)
        })

        loaded_count = 0

        for prompt_file in self.prompts_dir.glob("*.md"):
            try:
                prompt_name = prompt_file.stem  # e.g., "system_gemini_v7"
                prompt_content = prompt_file.read_text(encoding='utf-8')

                self.prompt_cache[prompt_name] = prompt_content
                loaded_count += 1

                self.logger.debug("prompt_loaded", {
                    "prompt_name": prompt_name,
                    "size_bytes": len(prompt_content)
                })

            except Exception as e:
                self.logger.warning("prompt_load_failed", {
                    "prompt_file": str(prompt_file),
                    "error": str(e)
                })

        self.logger.debug("prompt_load_complete", {
            "loaded_count": loaded_count
        })

    def increment_tool_calls(self, count: int = 1):
        """
        Increment tool calls counter.

        Args:
            count: Number of tool calls to add (default: 1)

        Usage:
            # After each tool execution
            refresh_system.increment_tool_calls()

            # After batch execution
            refresh_system.increment_tool_calls(count=10)
        """
        self.tool_calls_count += count

    def should_refresh(self) -> bool:
        """
        Check if refresh is needed based on tool calls count.

        Returns:
            True if tool_calls_count >= refresh_interval, False otherwise

        Usage:
            if refresh_system.should_refresh():
                await refresh_system.refresh()
        """
        return self.tool_calls_count >= self.refresh_interval

    async def check_and_refresh(self) -> bool:
        """
        Check if refresh needed and perform refresh if so.

        Convenience method that combines should_refresh() and refresh().

        Returns:
            True if refresh occurred, False otherwise

        Usage:
            if await refresh_system.check_and_refresh():
                # Prompts were refreshed
                pass
        """
        if self.should_refresh():
            await self.refresh()
            return True
        return False

    async def refresh(self):
        """
        Reload all prompts from disk.

        Process:
            1. Clear current prompt cache
            2. Reload all prompts from prompts_dir
            3. Log refresh event
            4. Reset tool calls counter
            5. Add to refresh history

        NOTE: This method is async for future integration with
              OrchestratorV7 (which may need async prompt updates).
        """
        self.logger.info("prompt_refresh_start", {
            "tool_calls": self.tool_calls_count,
            "refresh_interval": self.refresh_interval
        })

        start_time = datetime.now()

        # Reload prompts
        old_count = len(self.prompt_cache)
        self._load_prompts()
        new_count = len(self.prompt_cache)

        # Reset counter
        old_tool_calls = self.tool_calls_count
        self.tool_calls_count = 0

        # Record refresh event
        refresh_event = {
            "timestamp": start_time.isoformat(),
            "tool_calls": old_tool_calls,
            "prompts_reloaded": new_count,
            "prompts_added": max(0, new_count - old_count),
            "prompts_removed": max(0, old_count - new_count)
        }
        self.refresh_history.append(refresh_event)

        self.logger.info("prompt_refresh_complete", refresh_event)

    def get_prompt(self, prompt_name: str) -> Optional[str]:
        """
        Get prompt content from cache.

        Args:
            prompt_name: Prompt file name without extension (e.g., "system_gemini_v7")

        Returns:
            Prompt content string or None if not found

        Usage:
            gemini_prompt = refresh_system.get_prompt("system_gemini_v7")
            if gemini_prompt:
                # Use prompt
                pass
        """
        return self.prompt_cache.get(prompt_name)

    def get_all_prompts(self) -> Dict[str, str]:
        """
        Get all cached prompts.

        Returns:
            Dict of prompt_name → prompt_content

        Usage:
            all_prompts = refresh_system.get_all_prompts()
            for name, content in all_prompts.items():
                print(f"{name}: {len(content)} characters")
        """
        return dict(self.prompt_cache)

    def get_status(self) -> Dict:
        """
        Get current refresh system status.

        Returns:
            Dict with status information:
                - tool_calls_count: Current tool calls count
                - refresh_interval: Configured refresh interval
                - prompts_cached: Number of prompts in cache
                - refreshes_performed: Total refreshes performed
                - next_refresh_in: Tool calls until next refresh

        Usage:
            status = refresh_system.get_status()
            print(f"Next refresh in {status['next_refresh_in']} tool calls")
        """
        return {
            "tool_calls_count": self.tool_calls_count,
            "refresh_interval": self.refresh_interval,
            "prompts_cached": len(self.prompt_cache),
            "refreshes_performed": len(self.refresh_history),
            "next_refresh_in": max(0, self.refresh_interval - self.tool_calls_count),
            "last_refresh": self.refresh_history[-1] if self.refresh_history else None
        }

    def get_refresh_history(self) -> List[Dict]:
        """
        Get refresh event history.

        Returns:
            List of refresh events with timestamps and stats

        Usage:
            history = refresh_system.get_refresh_history()
            for event in history:
                print(f"Refresh at {event['timestamp']}: {event['prompts_reloaded']} prompts")
        """
        return list(self.refresh_history)
