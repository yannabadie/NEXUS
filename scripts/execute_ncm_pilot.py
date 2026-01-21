"""
NCM Phase 1 Pilot Executor

Executes pilot stories from workspace/ncm/pilot/pilot_queue.json
Integrates with OrchestratorV7 for actual story execution.

Usage:
    python scripts/execute_ncm_pilot.py --interactive    # Story-by-story with approval
    python scripts/execute_ncm_pilot.py --batch=10       # Execute 10 stories at once
    python scripts/execute_ncm_pilot.py --dry-run        # Simulate execution
"""

import json
import sys
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
import subprocess


class NCMPilotExecutor:
    """Execute NCM pilot stories with validation and metrics tracking."""

    def __init__(self, workspace_path: Path, dry_run: bool = False):
        self.workspace_path = workspace_path
        self.ncm_path = workspace_path / "ncm"
        self.dry_run = dry_run

        # Load pilot queue
        pilot_queue_path = self.ncm_path / "pilot" / "pilot_queue.json"
        with open(pilot_queue_path, "r", encoding="utf-8") as f:
            self.pilot_data = json.load(f)

        self.stories = self.pilot_data["stories"]
        self.total_stories = len(self.stories)

        # Metrics
        self.stories_completed = []
        self.stories_failed = []
        self.total_tokens_used = 0

        # Directories
        self.logs_dir = self.ncm_path / "logs"
        self.metrics_dir = self.ncm_path / "metrics"
        self.snapshots_dir = self.ncm_path / "snapshots"
        self.stories_dir = self.ncm_path / "stories"

        # Ensure directories exist
        for dir_path in [self.logs_dir, self.metrics_dir, self.snapshots_dir, self.stories_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)

        # Log file
        today = datetime.now().strftime("%Y%m%d")
        self.log_file = self.logs_dir / f"ncm_{today}.jsonl"
        self.failures_file = self.logs_dir / "ncm_failures.jsonl"
        self.successes_file = self.logs_dir / "ncm_successes.jsonl"

    def log_event(self, event_type: str, data: Dict[str, Any]):
        """Log event to JSONL file."""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            **data
        }

        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry) + "\n")

        print(f"[{event_type}] {data.get('story_id', 'N/A')}")

    async def execute_story(self, story: Dict[str, Any], story_index: int) -> Dict[str, Any]:
        """
        Execute a single story.

        Args:
            story: Story object from pilot queue
            story_index: Index in pilot queue (0-99)

        Returns:
            Execution result with status, tokens, duration, etc.
        """
        story_id = story["story_id"]
        start_time = datetime.now()

        self.log_event("story_start", {
            "story_id": story_id,
            "index": story_index,
            "category": story["category"],
            "priority": story["priority"]
        })

        try:
            if self.dry_run:
                # Dry run: simulate execution
                result = await self._simulate_story_execution(story)
            else:
                # Real execution: delegate to NCM Orchestrator
                result = await self._execute_story_real(story)

            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            # Build execution record
            execution_record = {
                "story_id": story_id,
                "index": story_index,
                "category": story["category"],
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "duration_seconds": duration,
                "status": result["status"],
                "tokens_used": result["tokens_used"],
                "files_modified": result.get("files_modified", []),
                "tests_passed": result.get("tests_passed", False),
                "validation": result.get("validation", {}),
                "error": result.get("error")
            }

            # Log result
            if result["status"] == "SUCCESS":
                self.stories_completed.append(execution_record)
                with open(self.successes_file, "a", encoding="utf-8") as f:
                    f.write(json.dumps(execution_record) + "\n")
                self.log_event("story_success", {"story_id": story_id, "tokens": result["tokens_used"]})
            else:
                self.stories_failed.append(execution_record)
                with open(self.failures_file, "a", encoding="utf-8") as f:
                    f.write(json.dumps(execution_record) + "\n")
                self.log_event("story_failure", {"story_id": story_id, "error": result.get("error")})

            # Update token usage
            self.total_tokens_used += result["tokens_used"]

            # Save story execution record
            story_file = self.stories_dir / f"{story_id}.json"
            with open(story_file, "w", encoding="utf-8") as f:
                json.dump(execution_record, f, indent=2)

            return execution_record

        except Exception as e:
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            error_record = {
                "story_id": story_id,
                "index": story_index,
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "duration_seconds": duration,
                "status": "ERROR",
                "error": str(e),
                "tokens_used": 0
            }

            self.stories_failed.append(error_record)
            self.log_event("story_error", {"story_id": story_id, "error": str(e)})

            return error_record

    async def _simulate_story_execution(self, story: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate story execution for dry-run mode."""
        # Simulate processing time
        await asyncio.sleep(1)

        # Simulate token usage (random between 30k-60k)
        import random
        tokens = random.randint(30000, 60000)

        return {
            "status": "SUCCESS",
            "tokens_used": tokens,
            "files_modified": story["target_files"],
            "tests_passed": True,
            "validation": {
                "syntax_ok": True,
                "imports_ok": True,
                "tests_ok": True
            }
        }

    async def _execute_story_real(self, story: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute story via NCM Orchestrator.

        This would delegate to:
        - NCMOrchestrator.execute_story(story)
        - Which calls OrchestratorV7.process_turn(story.description)

        For now, this is a placeholder for actual integration.
        """
        # TODO: Integrate with NCMOrchestrator
        # from core.ncm.orchestrator import NCMOrchestrator
        # orchestrator = NCMOrchestrator(...)
        # result = await orchestrator.execute_story(story)

        raise NotImplementedError(
            "Real execution requires NCMOrchestrator integration. Use --dry-run for testing."
        )

    async def validate_story_result(self, story: Dict[str, Any], result: Dict[str, Any]) -> bool:
        """
        Validate story execution result.

        Checks:
        1. Target files were modified
        2. Tests pass (if test files specified)
        3. No syntax errors
        4. No import errors
        """
        story_id = story["story_id"]

        # Check files modified
        if not result.get("files_modified"):
            print(f"WARNING: No files modified for {story_id}")
            return False

        # Run tests if specified
        if story["test_files"] and not self.dry_run:
            for test_file in story["test_files"]:
                test_path = Path(test_file)
                if test_path.exists():
                    print(f"Running tests: pytest {test_file} -v")
                    test_result = subprocess.run(
                        ["pytest", str(test_file), "-v", "--tb=short"],
                        capture_output=True,
                        text=True
                    )

                    if test_result.returncode != 0:
                        print(f"FAILED: Tests failed for {story_id}")
                        print(test_result.stdout)
                        return False

        # Check syntax (if Python files)
        for file_path in story["target_files"]:
            if file_path.endswith(".py") and not self.dry_run:
                try:
                    import ast
                    with open(file_path, "r", encoding="utf-8") as f:
                        ast.parse(f.read())
                except SyntaxError as e:
                    print(f"FAILED: Syntax error in {file_path}: {e}")
                    return False

        return True

    async def take_snapshot(self, stories_completed: int):
        """Take state snapshot."""
        snapshot_id = f"snapshot_{stories_completed}"
        snapshot_path = self.snapshots_dir / f"{snapshot_id}.json"

        snapshot_data = {
            "snapshot_id": snapshot_id,
            "timestamp": datetime.now().isoformat(),
            "stories_completed": stories_completed,
            "stories_failed": len(self.stories_failed),
            "total_tokens_used": self.total_tokens_used,
            "success_rate": stories_completed / (stories_completed + len(self.stories_failed)) if stories_completed else 0,
            "completed_story_ids": [s["story_id"] for s in self.stories_completed],
            "failed_story_ids": [s["story_id"] for s in self.stories_failed]
        }

        with open(snapshot_path, "w", encoding="utf-8") as f:
            json.dump(snapshot_data, f, indent=2)

        self.log_event("snapshot_taken", {"snapshot_id": snapshot_id, "stories_completed": stories_completed})
        print(f"Snapshot saved: {snapshot_path}")

    async def execute_batch(self, start_index: int, batch_size: int, interactive: bool = False):
        """
        Execute a batch of stories.

        Args:
            start_index: Starting index in pilot queue
            batch_size: Number of stories to execute
            interactive: Pause after each story for approval
        """
        end_index = min(start_index + batch_size, self.total_stories)

        print(f"\n{'='*60}")
        print(f"Executing stories {start_index+1} to {end_index} ({end_index - start_index} stories)")
        print(f"{'='*60}\n")

        for i in range(start_index, end_index):
            story = self.stories[i]
            story_id = story["story_id"]

            print(f"\n--- Story {i+1}/{self.total_stories}: {story_id} ---")
            print(f"Category: {story['category']}")
            print(f"Priority: {story['priority']}")
            print(f"Target: {', '.join(story['target_files'])}")
            print(f"\nDescription:\n{story['description'][:200]}...\n")

            if interactive:
                response = input(f"Execute {story_id}? [Y/n/q]: ").strip().lower()
                if response == 'q':
                    print("Execution stopped by user.")
                    break
                elif response == 'n':
                    print(f"Skipping {story_id}.")
                    continue

            # Execute story
            result = await self.execute_story(story, i)

            print(f"Status: {result['status']}")
            print(f"Tokens: {result['tokens_used']:,}")
            print(f"Duration: {result['duration_seconds']:.1f}s")

            # Checkpoint every 10 stories
            if (i + 1) % 10 == 0:
                await self.checkpoint(i + 1, interactive=interactive)

        print(f"\n{'='*60}")
        print(f"Batch complete: {start_index+1} to {end_index}")
        print(f"{'='*60}\n")

    async def checkpoint(self, stories_completed: int, interactive: bool = True):
        """Human checkpoint with summary and decision point."""
        print(f"\n{'='*60}")
        print(f"CHECKPOINT: {stories_completed} stories completed")
        print(f"{'='*60}")

        success_count = len(self.stories_completed)
        fail_count = len(self.stories_failed)
        success_rate = (success_count / stories_completed * 100) if stories_completed else 0

        print(f"\nMetrics:")
        print(f"  Success: {success_count}/{stories_completed} ({success_rate:.1f}%)")
        print(f"  Failed:  {fail_count}")
        print(f"  Tokens:  {self.total_tokens_used:,} / 100,000,000")
        print(f"  Budget:  {self.total_tokens_used / 100_000_000 * 100:.2f}%")

        # Take snapshot
        await self.take_snapshot(stories_completed)

        # Show recent failures
        if self.stories_failed:
            print(f"\nRecent failures:")
            for failure in self.stories_failed[-3:]:
                print(f"  - {failure['story_id']}: {failure.get('error', 'Unknown error')}")

        print(f"\n{'='*60}\n")

        # Decision point (only in interactive mode)
        if interactive and stories_completed in [10, 50, 100]:
            response = input("Continue to next batch? [Y/n]: ").strip().lower()
            if response == 'n':
                print("Execution paused. Resume with --resume flag.")
                sys.exit(0)

    async def generate_summary(self):
        """Generate daily summary."""
        today = datetime.now().strftime("%Y%m%d")
        summary_path = self.metrics_dir / f"daily_summary_{today}.json"

        total_attempted = len(self.stories_completed) + len(self.stories_failed)
        success_rate = (len(self.stories_completed) / total_attempted * 100) if total_attempted else 0

        summary = {
            "date": today,
            "stories_attempted": total_attempted,
            "stories_completed": len(self.stories_completed),
            "stories_failed": len(self.stories_failed),
            "success_rate": success_rate,
            "total_tokens_used": self.total_tokens_used,
            "avg_tokens_per_story": self.total_tokens_used / len(self.stories_completed) if self.stories_completed else 0,
            "completed_story_ids": [s["story_id"] for s in self.stories_completed],
            "failed_story_ids": [s["story_id"] for s in self.stories_failed]
        }

        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)

        print(f"\nSummary saved: {summary_path}")
        return summary


async def main():
    """Main execution entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="NCM Phase 1 Pilot Executor")
    parser.add_argument("--interactive", action="store_true", help="Story-by-story with approval")
    parser.add_argument("--batch", type=int, default=10, help="Batch size (default: 10)")
    parser.add_argument("--start", type=int, default=0, help="Starting story index (default: 0)")
    parser.add_argument("--dry-run", action="store_true", help="Simulate execution without real changes")

    args = parser.parse_args()

    # Initialize executor
    workspace_path = Path("workspace")
    executor = NCMPilotExecutor(workspace_path, dry_run=args.dry_run)

    if args.dry_run:
        print("=" * 60)
        print("DRY RUN MODE: Simulating execution")
        print("=" * 60)
        print()

    # Execute batch
    await executor.execute_batch(
        start_index=args.start,
        batch_size=args.batch,
        interactive=args.interactive
    )

    # Generate summary
    summary = await executor.generate_summary()

    print("\n" + "=" * 60)
    print("EXECUTION COMPLETE")
    print("=" * 60)
    print(f"\nStories completed: {summary['stories_completed']}/{summary['stories_attempted']}")
    print(f"Success rate: {summary['success_rate']:.1f}%")
    print(f"Tokens used: {summary['total_tokens_used']:,}")
    print(f"\nLogs: {executor.log_file}")
    print(f"Metrics: {executor.metrics_dir}")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
