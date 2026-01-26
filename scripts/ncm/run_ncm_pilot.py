#!/usr/bin/env python3
"""
NCM Pilot Execution Script

Executes NCM Phase 1 pilot with 2 stories (test), then 10 stories (full).
Bypasses interactive REPL for automated execution.
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
NEXUS_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(NEXUS_ROOT))

# Suppress warnings
import warnings
warnings.filterwarnings("ignore")


async def run_ncm_pilot():
    """Execute NCM pilot programmatically."""

    print("\n" + "="*70)
    print("  NCM PHASE 1 PILOT - Automated Execution")
    print("  Date:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("="*70 + "\n")

    try:
        # Import required modules
        print("[1/8] Importing NEXUS modules...")
        from core.orchestration_v7 import OrchestratorV7
        from core.config import Settings
        from core.ncm.orchestrator import NCMOrchestrator
        from core.ncm.models import NCMConfig, StoryStatus
        from core.interface.commands.ncm import generate_pilot_stories
        from rich.console import Console

        console = Console()
        print("[OK] Imports successful\n")

        # Initialize settings
        print("[2/8] Loading NEXUS configuration...")
        settings = Settings()
        workspace_path = NEXUS_ROOT / "workspace"

        if not workspace_path.exists():
            print(f"[ERROR] Workspace not found at {workspace_path}")
            return False

        print(f"[OK] Workspace: {workspace_path}\n")

        # Initialize OrchestratorV7
        print("[3/8] Initializing OrchestratorV7...")
        print("[INFO] This requires Gemini CLI and Claude Code to be available")
        print("[INFO] Checking for cached credentials...\n")

        # Check if Gemini CLI is available
        import subprocess
        try:
            result = subprocess.run(
                ["gemini", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                print("[OK] Gemini CLI available")
            else:
                print("[WARN] Gemini CLI check failed, but continuing...")
        except Exception as e:
            print(f"[WARN] Could not check Gemini CLI: {e}")
            print("[INFO] NCM will proceed, but may need manual intervention\n")

        # For automated execution, we need to initialize OrchestratorV7
        # This is normally done by nexus7.py REPL
        try:
            gemini_info = {
                "model": "gemini-3-pro-preview",
                "cli_path": "gemini"
            }

            claude_info = {
                "model": "claude-sonnet-4-5-20250929",
                "cli_path": "claude"
            }

            orchestrator = OrchestratorV7(
                workspace_path,
                settings,
                gemini_info,
                claude_info
            )

            print("[OK] OrchestratorV7 initialized\n")

        except Exception as e:
            print(f"[ERROR] Failed to initialize OrchestratorV7: {e}")
            print("\n" + "="*70)
            print("  PILOT CANNOT RUN AUTOMATICALLY")
            print("="*70)
            print("\nThis pilot requires running from within NEXUS REPL:")
            print("  1. python nexus7.py")
            print("  2. nexus7> /ncm pilot --count=2\n")
            return False

        # Create NCM orchestrator
        print("[4/8] Creating NCMOrchestrator...")
        config = NCMConfig(
            story_batch_size=50,
            token_limit=100_000_000,
            parallel_execution=False,
        )

        ncm = NCMOrchestrator(
            orchestrator=orchestrator,
            workspace_path=workspace_path,
            config=config,
        )

        print("[OK] NCM orchestrator created\n")

        # Generate pilot stories
        print("[5/8] Generating pilot stories...")
        stories = generate_pilot_stories(count=2)  # Start with 2

        console.print(f"[green][OK][/green] Generated {len(stories)} stories:")
        for story in stories:
            console.print(f"  - {story.story_id}: {story.description}")
        print()

        # Load stories into NCM
        print("[6/8] Loading stories into NCM queue...")
        await ncm.load_story_queue(stories)
        print(f"[OK] {len(stories)} stories loaded\n")

        # Execute pilot
        print("[7/8] Executing pilot stories...")
        print("-" * 70 + "\n")

        start_time = datetime.now()

        for i, story in enumerate(stories, 1):
            console.print(f"[bold cyan]Story {i}/{len(stories)}:[/bold cyan] {story.story_id}")
            console.print(f"  Description: {story.description}")
            console.print(f"  Target: {story.target_files[0]}")
            console.print()

            try:
                # Execute story
                status = await ncm.execute_story(story)

                if status == StoryStatus.SUCCESS:
                    console.print(f"  [green]✓ SUCCESS[/green]\n")
                elif status == StoryStatus.FAILED:
                    console.print(f"  [red]✗ FAILED[/red]")
                    console.print(f"    Error: {story.error_message}\n")
                elif status == StoryStatus.PARTIAL:
                    console.print(f"  [yellow]⚠ PARTIAL[/yellow]\n")

            except Exception as e:
                console.print(f"  [red]✗ ERROR: {str(e)}[/red]\n")
                story.status = StoryStatus.FAILED
                story.error_message = str(e)

        duration = (datetime.now() - start_time).total_seconds()

        # Report results
        print("-" * 70)
        print("[8/8] Pilot Results\n")

        completed = sum(1 for s in stories if s.status == StoryStatus.SUCCESS)
        failed = sum(1 for s in stories if s.status == StoryStatus.FAILED)
        partial = sum(1 for s in stories if s.status == StoryStatus.PARTIAL)

        console.print(f"  Total Stories:    {len(stories)}")
        console.print(f"  Completed:        {completed} ({completed/len(stories)*100:.1f}%)")
        console.print(f"  Failed:           {failed}")
        console.print(f"  Partial:          {partial}")
        console.print(f"  Duration:         {duration:.1f}s")
        console.print(f"  Avg per Story:    {duration/len(stories):.1f}s")
        print()

        # Success criteria
        success_rate = completed / len(stories)

        if success_rate >= 0.80:
            console.print("[green]✓ PILOT PASSED (≥80% success)[/green]")
            print("\nReady to run full pilot (10 stories)")
            return True
        else:
            console.print("[yellow]⚠ PILOT NEEDS REVIEW (<80% success)[/yellow]")
            return False

    except Exception as e:
        print(f"\n[ERROR] Pilot execution failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    try:
        result = asyncio.run(run_ncm_pilot())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n\nPilot interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\nFATAL ERROR: {e}")
        sys.exit(1)
