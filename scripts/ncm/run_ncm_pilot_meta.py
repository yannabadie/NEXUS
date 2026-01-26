#!/usr/bin/env python
"""
Run NCM Pilot with Meta GraphRAG stories - Direct execution.

This bypasses the REPL and runs NCM directly with Meta GraphRAG stories.

Usage:
    python scripts/ncm/run_ncm_pilot_meta.py
"""

import asyncio
import sys
import json
from pathlib import Path

# Add NEXUS root to path
NEXUS_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(NEXUS_ROOT))

from core.ncm.models import Story, StoryPriority, IssueDomain, StoryStatus
from core.ncm.orchestrator import NCMOrchestrator
from core.config import Config
from core.orchestration_v7 import OrchestratorV7


def load_stories_from_json(json_file: Path) -> list[Story]:
    """Load Story objects from JSON file."""
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    stories = []
    for story_data in data['stories']:
        story = Story(
            story_id=story_data['story_id'],
            priority=StoryPriority(story_data['priority']),
            domains={IssueDomain(d) for d in story_data['domains']},
            description=story_data['description'],
            target_files=[Path(f) for f in story_data['target_files']],
            test_files=[Path(f) for f in story_data.get('test_files', [])],
        )
        stories.append(story)

    return stories


async def run_pilot():
    """Run NCM pilot with Meta GraphRAG stories."""
    print("\n" + "=" * 80)
    print("NCM PILOT - Meta GraphRAG Stories (Direct Execution)")
    print("=" * 80 + "\n")

    # Load config
    config = Config()

    # Load stories
    stories_file = NEXUS_ROOT / 'workspace' / 'ncm_analysis' / 'ncm_pilot_stories.json'

    if not stories_file.exists():
        print(f"[ERROR] Stories file not found: {stories_file}")
        print("Run: python scripts/ncm/ncm_pilot_meta_graphrag.py --priority=p2 --count=10")
        return 1

    print(f"[LOAD] Loading stories from {stories_file.name}...")
    stories = load_stories_from_json(stories_file)
    print(f"  Loaded {len(stories)} stories\n")

    # Create Orchestrator
    print("[INIT] Initializing OrchestratorV7...")
    gemini_info = {"model": config.gemini_pro_model, "provider": "gemini"}
    claude_info = {"model": config.claude_opus_model, "provider": "claude"}

    orchestrator = OrchestratorV7(
        workspace_path=config.workspace_path,
        config=config,
        gemini_info=gemini_info,
        claude_info=claude_info,
    )

    # Create NCM config
    from core.ncm.models import NCMConfig
    ncm_config = NCMConfig(
        story_batch_size=50,
        token_limit=100_000_000,
        parallel_execution=False,
    )

    # Create NCM orchestrator
    print("[INIT] Initializing NCMOrchestrator...")
    ncm = NCMOrchestrator(
        orchestrator=orchestrator,
        workspace_path=config.workspace_path,
        config=ncm_config,
    )

    # Load story queue
    print(f"[QUEUE] Loading {len(stories)} stories into queue...\n")
    await ncm.load_story_queue(stories)

    # Execute stories one by one
    print("=" * 80)
    print("EXECUTION START")
    print("=" * 80 + "\n")

    for i, story in enumerate(stories, 1):
        print(f"\n[{i}/{len(stories)}] {story.story_id}: {story.description[:60]}...")
        print(f"  Priority: {story.priority.value} | File: {story.target_files[0] if story.target_files else 'N/A'}")

        try:
            status = await ncm.execute_story(story)

            if status == StoryStatus.SUCCESS:
                print(f"  [SUCCESS] Story completed successfully")
            elif status == StoryStatus.FAILED:
                print(f"  [FAILED] {story.error_message or 'Unknown error'}")
            elif status == StoryStatus.PARTIAL:
                print(f"  [PARTIAL] Some changes applied")

        except Exception as e:
            print(f"  [ERROR] Exception: {str(e)}")
            story.status = StoryStatus.FAILED
            story.error_message = str(e)

    # Summary
    print("\n" + "=" * 80)
    print("EXECUTION COMPLETE")
    print("=" * 80 + "\n")

    completed = sum(1 for s in stories if s.status == StoryStatus.SUCCESS)
    failed = sum(1 for s in stories if s.status == StoryStatus.FAILED)
    partial = sum(1 for s in stories if s.status == StoryStatus.PARTIAL)

    print(f"Results:")
    print(f"  SUCCESS:  {completed}/{len(stories)} ({completed/len(stories)*100:.1f}%)")
    print(f"  FAILED:   {failed}/{len(stories)}")
    print(f"  PARTIAL:  {partial}/{len(stories)}")
    print()

    if completed / len(stories) >= 0.80:
        print("[PASS] Pilot passed (>=80% success)")
    else:
        print("[REVIEW] Pilot needs review (<80% success)")

    print()
    return 0 if completed / len(stories) >= 0.80 else 1


def main():
    """Main entry point."""
    try:
        result = asyncio.run(run_pilot())
        return result
    except KeyboardInterrupt:
        print("\n\n[INTERRUPTED] Pilot interrupted by user")
        return 130
    except Exception as e:
        print(f"\n[ERROR] Fatal error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
