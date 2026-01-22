#!/usr/bin/env python3
"""
NCM Pilot Script - Phase 1 Mini Pilot (10 stories)

Execute 10 simple P2 stories with real NEXUS to validate NCM workflow.

Stories:
- 5x Remove dead imports
- 5x Add missing docstrings

Usage:
    python scripts/ncm_pilot.py
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime
from typing import List

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.ncm.models import (
    Story,
    StoryPriority,
    IssueDomain,
    StoryStatus,
    NCMConfig,
)
from core.ncm.orchestrator import NCMOrchestrator
from core.orchestration_v7 import OrchestratorV7
from core.config import Settings
from core.logging import get_logger

logger = get_logger()


def create_pilot_stories() -> List[Story]:
    """
    Create 10 simple P2 stories for pilot test.

    Returns:
        List of Story objects (5 dead imports + 5 docstrings)
    """
    stories = []

    # Story 1-5: Remove dead imports (easy wins)
    dead_import_targets = [
        ("core/drivers/gemini_driver_v7.py", "Remove unused 're' import", 15),
        ("core/hive_mind/orchestrator.py", "Remove unused 'time' import", 12),
        ("core/swarm/hybrid_swarm_engine.py", "Remove unused 'os' import", 8),
        ("core/memory/backends/hybrid.py", "Remove unused 'sys' import", 10),
        ("core/execution/tool_manager.py", "Remove unused 'json' import", 14),
    ]

    for i, (file_path, description, line) in enumerate(dead_import_targets, 1):
        story = Story(
            story_id=f"PILOT-{i:03d}",
            priority=StoryPriority.P2,
            domains={IssueDomain.CLEANUP},
            description=f"{description} from {file_path} (line ~{line})",
            target_files=[Path(file_path)],
            test_files=[],  # No tests needed for dead import removal
        )
        stories.append(story)

    # Story 6-10: Add missing docstrings (documentation)
    docstring_targets = [
        ("core/drivers/protocol.py", "DriverProtocol class"),
        ("core/ncm/locks.py", "LockManager.__init__ method"),
        ("core/swarm/negotiation_protocol.py", "negotiate_mode function"),
        ("core/memory/backends/bm25.py", "BM25Backend.query method"),
        ("core/execution/handlers/base.py", "BaseHandler class"),
    ]

    for i, (file_path, target) in enumerate(docstring_targets, 6):
        story = Story(
            story_id=f"PILOT-{i:03d}",
            priority=StoryPriority.P2,
            domains={IssueDomain.DOCUMENTATION},
            description=f"Add docstring to {target} in {file_path}",
            target_files=[Path(file_path)],
            test_files=[],  # Documentation changes don't need tests
        )
        stories.append(story)

    return stories


async def run_pilot():
    """
    Execute NCM pilot with 10 real stories.

    Process:
        1. Initialize OrchestratorV7 (get existing instance or create new)
        2. Create NCMOrchestrator
        3. Load 10 pilot stories
        4. Execute stories sequentially
        5. Report results
    """
    print("\n" + "="*70)
    print("  NCM PILOT - Phase 1 Mini (10 Stories)")
    print("  Testing NCM + NEXUS Real Integration")
    print("="*70 + "\n")

    # Step 1: Initialize workspace
    workspace_path = project_root / "workspace"
    if not workspace_path.exists():
        print(f"ERROR: Workspace not found at {workspace_path}")
        return

    print("[1/5] Loading NEXUS configuration...")

    # Initialize settings
    settings = Settings()

    print(f"      Workspace: {workspace_path}")
    print(f"      Branch: NX-BM")
    print()

    # Step 2: Initialize OrchestratorV7
    print("[2/5] Initializing OrchestratorV7...")

    # Try to get existing orchestrator instance (singleton pattern)
    try:
        from core.factory import get_orchestrator
        orchestrator = get_orchestrator()
        print("      [OK] Using existing OrchestratorV7 instance")
    except Exception as e:
        print(f"      [INFO] No existing orchestrator, creating new one")
        # For pilot, we'll use a simplified orchestrator initialization
        # In production, this would be handled by the main NEXUS entry point
        print(f"      [SKIP] Full initialization requires gemini/claude CLI setup")
        print(f"      [INFO] This pilot would need to be run from within NEXUS session")
        print()
        print("="*70)
        print("  PILOT SETUP NOTE")
        print("="*70)
        print()
        print("To run this pilot, execute from within a NEXUS session:")
        print()
        print("  1. Start NEXUS: python nexus7.py")
        print("  2. Run: /exec python scripts/ncm_pilot.py")
        print()
        print("Or alternatively, use the NCM command (when implemented):")
        print("  nexus7> /ncm pilot --stories=10")
        print()
        return

    # Step 3: Create NCMOrchestrator
    print("[3/5] Creating NCMOrchestrator...")

    config = NCMConfig(
        story_batch_size=10,
        token_limit=10_000_000,  # 10M tokens for pilot
        parallel_execution=False,  # Sequential for pilot
    )

    ncm = NCMOrchestrator(
        orchestrator=orchestrator,
        workspace_path=workspace_path,
        config=config,
    )

    print(f"      [OK] NCM initialized")
    print(f"      Token limit: {config.token_limit:,}")
    print()

    # Step 4: Generate pilot stories
    print("[4/5] Loading pilot stories...")
    stories = create_pilot_stories()

    print(f"      [OK] Created {len(stories)} stories")
    print(f"        - Dead imports: {sum(1 for s in stories if IssueDomain.CLEANUP in s.domains)}")
    print(f"        - Docstrings: {sum(1 for s in stories if IssueDomain.DOCUMENTATION in s.domains)}")
    print()

    # Load stories into NCM
    await ncm.load_story_queue(stories)

    # Step 5: Execute pilot
    print("[5/5] Executing pilot stories...\n")

    start_time = datetime.now()

    for i, story in enumerate(stories, 1):
        print(f"  Story {i}/10: {story.story_id} - {story.description[:60]}...")

        try:
            status = await ncm.execute_story(story)

            if status == StoryStatus.SUCCESS:
                print(f"    [OK] SUCCESS")
            elif status == StoryStatus.FAILED:
                print(f"    [FAIL] FAILED - {story.error_message}")
            elif status == StoryStatus.PARTIAL:
                print(f"    [PARTIAL] Some changes applied")

        except Exception as e:
            print(f"    [ERROR] {str(e)}")
            story.status = StoryStatus.FAILED
            story.error_message = str(e)

        print()

    # Report results
    duration = (datetime.now() - start_time).total_seconds()

    completed = sum(1 for s in stories if s.status == StoryStatus.SUCCESS)
    failed = sum(1 for s in stories if s.status == StoryStatus.FAILED)
    partial = sum(1 for s in stories if s.status == StoryStatus.PARTIAL)

    print("\n" + "="*70)
    print("  PILOT RESULTS")
    print("="*70)
    print()
    print(f"  Total Stories:    {len(stories)}")
    print(f"  Completed:        {completed} ({completed/len(stories)*100:.1f}%)")
    print(f"  Failed:           {failed} ({failed/len(stories)*100:.1f}%)")
    print(f"  Partial:          {partial}")
    print()
    print(f"  Duration:         {duration:.1f}s")
    print(f"  Avg per Story:    {duration/len(stories):.1f}s")
    print()

    # Success criteria
    success_rate = completed / len(stories)

    if success_rate >= 0.80:
        print("  [PASS] Pilot PASSED - Success rate >= 80%")
        print("  Ready to proceed to full Phase 1 Pilot (100 stories)")
    elif success_rate >= 0.50:
        print("  [PARTIAL] Pilot PARTIAL - Need investigation")
    else:
        print("  [FAIL] Pilot FAILED - Review errors")

    print("\n" + "="*70 + "\n")


if __name__ == "__main__":
    try:
        asyncio.run(run_pilot())
    except KeyboardInterrupt:
        print("\n\nPilot interrupted by user.")
        sys.exit(1)
    except Exception as e:
        logger.error("pilot_crashed", {"error": str(e)})
        print(f"\nERROR: {e}")
        sys.exit(1)
