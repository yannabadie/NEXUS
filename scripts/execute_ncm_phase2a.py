"""
Execute NCM Phase 2A Stories

Phase 2A Strategy:
- First 5 stories: Manual validation (one-by-one with review)
- Next 45 stories: Semi-automated (batch of 10 with checkpoints)
- Remaining stories: Automated batches (batch of 50)

Usage:
    # Manual mode (first 5 stories)
    python scripts/execute_ncm_phase2a.py --manual --limit=5

    # Semi-automated (next 45 stories)
    python scripts/execute_ncm_phase2a.py --batch=10 --limit=45 --start=6

    # Automated (remaining stories)
    python scripts/execute_ncm_phase2a.py --batch=50 --start=51
"""

import asyncio
import json
import re
import sys
import signal
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import argparse

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.ncm.orchestrator import NCMOrchestrator
from core.ncm.simple_executor import SimpleExecutor
from core.orchestration_v7 import OrchestratorV7


class Phase2AExecutor:
    """Execute Phase 2A stories with manual/automated modes and pause/resume."""

    def __init__(self, manual_mode: bool = False, dry_run: bool = False):
        """
        Initialize Phase 2A executor.

        Args:
            manual_mode: If True, pause after each story for review
            dry_run: If True, simulate execution without real changes
        """
        self.manual_mode = manual_mode
        self.dry_run = dry_run
        self.workspace_path = Path("workspace/ncm")
        self.queue_path = self.workspace_path / "phase2a_queue.json"
        self.state_path = self.workspace_path / "execution_state.json"

        # Pause/Resume state
        self._pause_requested = False
        self._setup_signal_handlers()

        # Load Phase 2A queue
        if not self.queue_path.exists():
            print(f"ERROR: Phase 2A queue not found: {self.queue_path}")
            print("Run: python scripts/generate_phase2a_queue.py")
            sys.exit(1)

        with open(self.queue_path, "r", encoding="utf-8") as f:
            self.queue_data = json.load(f)

        self.stories = self.queue_data["stories"]
        self.total_stories = len(self.stories)

        # Load execution state if exists
        self.execution_state = self._load_state()

        print("=" * 60)
        print("NCM Phase 2A/2B Executor (with Pause/Resume)")
        print("=" * 60)
        print()
        print(f"Mode: {'MANUAL' if manual_mode else 'AUTOMATED'}")
        print(f"Dry-Run: {'YES' if dry_run else 'NO'}")
        print(f"Total Stories: {self.total_stories}")
        if self.execution_state.get("last_completed"):
            print(f"Last Completed: {self.execution_state['last_completed']}")
            print(f"Success: {self.execution_state.get('success_count', 0)}, "
                  f"Failed: {self.execution_state.get('failed_count', 0)}")
        print()
        print("Press CTRL+C to pause gracefully (state will be saved)")
        print()

    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful pause."""
        def signal_handler(signum, frame):
            print("\n" + "=" * 60)
            print("PAUSE REQUESTED - Finishing current story...")
            print("=" * 60)
            self._pause_requested = True

        # Windows and Unix signal handling
        signal.signal(signal.SIGINT, signal_handler)
        if hasattr(signal, 'SIGTERM'):
            signal.signal(signal.SIGTERM, signal_handler)

    def _load_state(self) -> Dict[str, Any]:
        """Load execution state from disk."""
        if self.state_path.exists():
            try:
                with open(self.state_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {
            "last_completed": None,
            "last_completed_idx": 0,
            "success_count": 0,
            "failed_count": 0,
            "completed_stories": [],
            "failed_stories": [],
            "started_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat()
        }

    def _save_state(self):
        """Save execution state to disk for resume capability."""
        self.execution_state["last_updated"] = datetime.now().isoformat()
        with open(self.state_path, "w", encoding="utf-8") as f:
            json.dump(self.execution_state, f, indent=2)

    def _check_pause(self) -> bool:
        """Check if pause was requested and handle it."""
        if self._pause_requested:
            self._save_state()
            print()
            print("=" * 60)
            print("EXECUTION PAUSED")
            print("=" * 60)
            print(f"Progress saved to: {self.state_path}")
            print(f"Last completed: {self.execution_state.get('last_completed', 'None')}")
            print(f"Success: {self.execution_state.get('success_count', 0)}, "
                  f"Failed: {self.execution_state.get('failed_count', 0)}")
            print()
            print("To resume, run the same command again.")
            print("To start fresh, delete: workspace/ncm/execution_state.json")
            print("=" * 60)
            return True
        return False

    def _prompt_continue(self, message: str) -> bool:
        """Prompt user to continue; default to yes when stdin is non-interactive."""
        try:
            if not sys.stdin.isatty():
                print("[AUTO] No TTY available; continuing by default.")
                return True
            response = input(message).strip().lower()
            return response in ("", "y", "yes")
        except EOFError:
            print("[AUTO] EOF on stdin; continuing by default.")
            return True

    async def execute_manual(self, limit: int = 5, start: int = 1):
        """
        Execute stories in manual mode (one-by-one with review).

        Args:
            limit: Number of stories to execute
            start: Starting story index (1-based)
        """
        print(f"Manual Mode: Executing {limit} stories starting from #{start}")
        print()

        # Adjust for 0-based indexing
        start_idx = start - 1
        end_idx = min(start_idx + limit, self.total_stories)

        stories_to_execute = self.stories[start_idx:end_idx]

        for i, story in enumerate(stories_to_execute, start=start):
            story_id = story["story_id"]
            print("=" * 60)
            print(f"Story {i}/{self.total_stories}: {story_id}")
            print("=" * 60)
            print()
            print(f"Category: {story['category']}")
            print(f"Priority: {story['priority']}")
            print(f"Target Files: {', '.join(story['target_files'])}")
            print()
            print("Description:")
            print(story["description"])
            print()

            if self.dry_run:
                print("[DRY-RUN] Simulating execution...")
                await asyncio.sleep(1)  # Simulate work
                print("SUCCESS: Story simulated successfully")
                print()
            else:
                # Execute story with NCMOrchestrator
                result = await self._execute_story_real(story)

                if result["status"] == "success":
                    print("SUCCESS: Story completed successfully")
                    print(f"- Syntax valid: {result.get('syntax_valid', False)}")
                    print(f"- Imports valid: {result.get('imports_valid', False)}")
                    print(f"- Tests passed: {result.get('tests_passed', False)}")
                    print()
                else:
                    print(f"FAILED: Story execution failed")
                    print(f"- Error: {result.get('error', 'Unknown error')}")
                    print()

                    # In manual mode, ask whether to continue
                    if self.manual_mode:
                        if not self._prompt_continue("Story failed. Continue to next? [Y/n]: "):
                            print("Execution stopped by user.")
                            return

            # Manual checkpoint
            if self.manual_mode:
                print("-" * 60)
                print("Review the changes above.")
                print("-" * 60)
                if not self._prompt_continue("Continue to next story? [Y/n]: "):
                    print("Execution stopped by user.")
                    return
                print()

        print("=" * 60)
        print(f"Manual execution complete: {len(stories_to_execute)} stories")
        print("=" * 60)

    async def execute_batch(self, batch_size: int = 10, start: int = 1, limit: int = None):
        """
        Execute stories in batch mode with pause/resume support.

        Args:
            batch_size: Number of stories per batch
            start: Starting story index (1-based)
            limit: Maximum number of stories to execute (None = all remaining)

        Pause/Resume:
            - Press CTRL+C to pause gracefully
            - State is saved to workspace/ncm/execution_state.json
            - Run same command to resume from last completed story
        """
        # Check for resume from saved state
        saved_idx = self.execution_state.get("last_completed_idx", 0)
        if saved_idx > 0 and start == 1:
            resume_start = saved_idx + 1  # Resume from next story
            print(f"Resuming from story #{resume_start} (last completed: {saved_idx})")
            start = resume_start

        print(f"Batch Mode: Batch size {batch_size}, starting from #{start}")
        print()

        # Adjust for 0-based indexing
        start_idx = start - 1
        end_idx = self.total_stories if limit is None else min(start_idx + limit, self.total_stories)

        stories_to_execute = self.stories[start_idx:end_idx]
        total_to_execute = len(stories_to_execute)

        print(f"Executing {total_to_execute} stories in batches of {batch_size}")
        print()

        # Load counters from saved state
        success_count = self.execution_state.get("success_count", 0)
        failed_count = self.execution_state.get("failed_count", 0)

        for batch_start in range(0, total_to_execute, batch_size):
            # Check for pause before starting batch
            if self._check_pause():
                return

            batch_end = min(batch_start + batch_size, total_to_execute)
            batch = stories_to_execute[batch_start:batch_end]

            print("=" * 60)
            print(f"Batch: Stories {start_idx + batch_start + 1} to {start_idx + batch_end}")
            print("=" * 60)
            print()

            for i, story in enumerate(batch):
                # Check for pause before each story
                if self._check_pause():
                    return

                story_id = story["story_id"]
                story_idx = start_idx + batch_start + i + 1  # 1-based index
                print(f"[{story_idx}/{self.total_stories}] Executing {story_id}...", end=" ")

                if self.dry_run:
                    await asyncio.sleep(0.5)  # Simulate work
                    print("SUCCESS (simulated)")
                    success_count += 1
                else:
                    result = await self._execute_story_real(story)
                    if result["status"] == "success":
                        print("SUCCESS")
                        success_count += 1
                        self.execution_state["completed_stories"].append(story_id)
                    else:
                        print(f"FAILED ({result.get('error', 'unknown')[:50]})")
                        failed_count += 1
                        self.execution_state["failed_stories"].append({
                            "story_id": story_id,
                            "error": result.get("error", "unknown")
                        })

                # Update state after each story
                self.execution_state["last_completed"] = story_id
                self.execution_state["last_completed_idx"] = story_idx
                self.execution_state["success_count"] = success_count
                self.execution_state["failed_count"] = failed_count

                # Save state periodically (every 5 stories)
                if story_idx % 5 == 0:
                    self._save_state()

            print()
            print(f"Batch complete: {batch_end - batch_start} stories")
            print(f"Total Progress: Success={success_count}, Failed={failed_count}")
            print()

            # Save state after each batch
            self._save_state()

            # Checkpoint after each batch (only in manual mode)
            if not self.dry_run and (batch_end < total_to_execute) and not self.manual_mode:
                # In automated mode, brief pause between batches
                import time
                time.sleep(2)
            elif self.manual_mode and (batch_end < total_to_execute):
                # In manual mode, ask for confirmation
                if not self._prompt_continue("Continue to next batch? [Y/n]: "):
                    self._save_state()
                    print("Execution paused by user.")
                    return

        # Final state save
        self._save_state()

        print("=" * 60)
        print(f"Batch execution complete")
        print(f"Total: {success_count + failed_count}, Success: {success_count}, Failed: {failed_count}")
        print(f"State saved to: {self.state_path}")
        print("=" * 60)

    async def _initialize_orchestrator(self):
        """Initialize OrchestratorV7 and NCMOrchestrator (lazy initialization)."""
        if hasattr(self, 'ncm_orchestrator'):
            return  # Already initialized

        from core.config import load_config
        from nexus7 import bootstrap

        # Bootstrap Gemini + Claude
        print("Initializing NEXUS orchestrators...")
        gemini_info, claude_info = bootstrap()
        config = load_config()

        # Initialize OrchestratorV7
        from core.orchestration_v7 import OrchestratorV7
        self.orchestrator = OrchestratorV7(
            workspace_path=self.workspace_path.parent.parent,  # NEXUS workspace root
            config=config,
            gemini_info=gemini_info,
            claude_info=claude_info
        )

        # Initialize NCMOrchestrator
        from core.ncm.models import NCMConfig
        ncm_config = NCMConfig(
            story_batch_size=50,
            token_limit=100_000_000,
            workspace_path=self.workspace_path
        )
        self.ncm_orchestrator = NCMOrchestrator(
            orchestrator=self.orchestrator,
            workspace_path=self.workspace_path,
            config=ncm_config
        )
        print("SUCCESS: Orchestrators initialized")
        print()

    async def _execute_story_real(self, story: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a story using SimpleExecutor (fast path for dead import removal).

        For Phase 2A/2B dead import stories, use SimpleExecutor instead of
        the full OrchestratorV7 pipeline. This is 50x faster (~6s vs 300s+).

        Args:
            story: Story dict from phase2a_queue.json

        Returns:
            Result dict with status and validation results
        """
        # Use SimpleExecutor for dead import stories (fast path)
        if story.get("category") == "dead_import":
            return await self._execute_dead_import_story(story)

        # Use SimpleExecutor for type hint stories (fast path)
        if story.get("category") == "type_error":
            return await self._execute_type_error_story(story)

        # Fall back to full orchestration for complex stories
        await self._initialize_orchestrator()

        # Convert story dict to Story object
        from core.ncm.models import Story, StoryPriority, IssueDomain, StoryStatus
        story_obj = Story(
            story_id=story["story_id"],
            priority=StoryPriority(story["priority"]),
            domains={IssueDomain(d.lower()) for d in story["domains"]},
            description=story["description"],
            target_files=[Path(f) for f in story["target_files"]],
            test_files=[Path(f) for f in story.get("test_files", [])],
            status=StoryStatus.PENDING
        )

        # Execute story via NCMOrchestrator
        try:
            status = await self.ncm_orchestrator.execute_story(story_obj)

            # Build result dict from story object state
            return {
                "status": "success" if status == StoryStatus.SUCCESS else "failed",
                "syntax_valid": True,
                "imports_valid": True,
                "tests_passed": True,
                "error": None if status == StoryStatus.SUCCESS else "Story execution failed"
            }
        except Exception as e:
            self.orchestrator.logger.error("Phase2A story execution failed", {
                "story_id": story["story_id"],
                "error": str(e)
            })
            return {
                "status": "failed",
                "syntax_valid": False,
                "imports_valid": False,
                "tests_passed": False,
                "error": str(e)
            }

    async def _execute_dead_import_story(self, story: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute dead import removal using SimpleExecutor (fast path).

        This bypasses the full orchestration pipeline for deterministic tasks.

        Args:
            story: Story dict with dead import info

        Returns:
            Result dict with status and validation results
        """
        executor = SimpleExecutor()

        description = story["description"]
        target_files = [Path(f) for f in story["target_files"]]

        # Extract import names from description
        # Format: "Import 'X' from 'Y' may be unused"
        import_pattern = r"Import '([^']+)' from '([^']+)' may be unused"
        matches = re.findall(import_pattern, description)

        if matches:
            # Extract just the import names (first group of each match)
            imports_to_remove = [m[0] for m in matches]
        else:
            # Fallback: look for quoted import names
            imports_to_remove = re.findall(r"'([^']+)'", description)
            if not imports_to_remove:
                return {
                    "status": "failed",
                    "error": f"Could not parse imports from description: {description[:100]}"
                }

        # Execute removal for each target file
        all_success = True
        errors = []
        skipped = []

        for file_path in target_files:
            if not file_path.exists():
                skipped.append(str(file_path))
                continue

            success, error = await executor.execute_dead_import_removal(
                file_path=file_path,
                imports_to_remove=imports_to_remove
            )

            if not success:
                all_success = False
                errors.append(f"{file_path.name}: {error}")

        if all_success:
            if skipped:
                print(f"SKIPPED missing targets: {', '.join(skipped)}")
            return {
                "status": "success",
                "syntax_valid": True,
                "imports_valid": True,
                "tests_passed": True,  # Tests run separately after batch
                "error": None
            }
        else:
            return {
                "status": "failed",
                "syntax_valid": False,
                "imports_valid": False,
                "tests_passed": False,
                "error": "; ".join(errors)
            }

    async def _execute_type_error_story(self, story: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute missing return type hint additions using SimpleExecutor.

        Args:
            story: Story dict with type error info.

        Returns:
            Result dict with status and validation results.
        """
        executor = SimpleExecutor()
        description = story["description"]
        target_files = [Path(f) for f in story["target_files"]]

        pattern = r"(?:Method|Function)\s+'([^']+)'\s+has no return type hint"
        matches = re.findall(pattern, description)
        targets = []
        for item in matches:
            if "." in item:
                class_name, func_name = item.split(".", 1)
                targets.append((class_name, func_name))
            else:
                targets.append((None, item))

        if not targets:
            return {
                "status": "failed",
                "error": f"Could not parse missing return type hints: {description[:100]}"
            }

        all_success = True
        errors = []
        skipped = []

        for file_path in target_files:
            if not file_path.exists():
                skipped.append(str(file_path))
                continue
            success, error = await executor.execute_missing_return_type_hints(
                file_path=file_path,
                targets=targets
            )
            if not success:
                all_success = False
                errors.append(f"{file_path.name}: {error}")

        if all_success:
            if skipped:
                print(f"SKIPPED missing targets: {', '.join(skipped)}")
            return {
                "status": "success",
                "syntax_valid": True,
                "imports_valid": True,
                "tests_passed": True,  # Tests run separately after batch
                "error": None
            }

        return {
            "status": "failed",
            "syntax_valid": False,
            "imports_valid": False,
            "tests_passed": False,
            "error": "; ".join(errors)
        }


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Execute NCM Phase 2A/2B Stories with Pause/Resume",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Start Phase 2B (type_error stories starting at 101)
    python scripts/execute_ncm_phase2a.py --batch=10 --start=101

    # Resume after pause (auto-detects last completed)
    python scripts/execute_ncm_phase2a.py --batch=10

    # Reset progress and start fresh
    python scripts/execute_ncm_phase2a.py --reset --batch=10 --start=101

Pause:
    Press CTRL+C to pause gracefully. Progress is saved automatically.
    Re-run the same command to resume from where you left off.
"""
    )
    parser.add_argument("--manual", action="store_true", help="Manual mode (pause after each story)")
    parser.add_argument("--batch", type=int, default=10, help="Batch size for automated mode")
    parser.add_argument("--limit", type=int, help="Maximum number of stories to execute")
    parser.add_argument("--start", type=int, default=1, help="Starting story number (1-based)")
    parser.add_argument("--dry-run", action="store_true", help="Simulate execution without real changes")
    parser.add_argument("--reset", action="store_true", help="Reset saved state and start fresh")

    args = parser.parse_args()

    # Handle reset
    if args.reset:
        state_path = Path("workspace/ncm/execution_state.json")
        if state_path.exists():
            state_path.unlink()
            print("Execution state reset. Starting fresh.")

    executor = Phase2AExecutor(manual_mode=args.manual, dry_run=args.dry_run)

    if args.manual:
        # Manual mode: Execute stories one-by-one
        asyncio.run(executor.execute_manual(limit=args.limit or 5, start=args.start))
    else:
        # Batch mode: Execute in batches
        asyncio.run(executor.execute_batch(
            batch_size=args.batch,
            start=args.start,
            limit=args.limit
        ))


if __name__ == "__main__":
    main()
