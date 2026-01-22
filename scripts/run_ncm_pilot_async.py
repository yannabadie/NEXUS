#!/usr/bin/env python3
"""
NCM Pilot - Direct Async Execution

Uses async drivers directly (async_gemini_driver, async_claude_driver)
to execute NCM pilot without going through REPL.

This bypasses the V9 command system which is synchronous.
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Suppress warnings
import warnings
warnings.filterwarnings("ignore")


async def execute_pilot_story(story_id: str, description: str, target_file: Path):
    """
    Execute a single pilot story using async drivers.

    Args:
        story_id: Story ID (e.g., "PILOT-001")
        description: Task description
        target_file: File to modify

    Returns:
        tuple: (success: bool, message: str)
    """
    from core.drivers.async_gemini_driver import AsyncGeminiDriver
    from core.drivers.async_claude_driver import AsyncClaudeDriver
    from core.drivers.protocol import DriverConfig

    print(f"\n{'='*70}")
    print(f"  {story_id}: {description}")
    print(f"  Target: {target_file}")
    print(f"{'='*70}\n")

    try:
        # Initialize drivers
        gemini_config = DriverConfig(
            model="gemini-3-pro-preview",
            temperature=0.7,
            max_tokens=8000,
        )

        claude_config = DriverConfig(
            model="claude-sonnet-4-5-20250929",
            temperature=0.7,
            max_tokens=8000,
        )

        gemini = AsyncGeminiDriver(config=gemini_config)
        claude = AsyncClaudeDriver(config=claude_config)

        # Read target file
        if not target_file.exists():
            return False, f"File not found: {target_file}"

        file_content = target_file.read_text(encoding='utf-8')

        # Create prompt for task
        prompt = f"""Task: {description}

Target file: {target_file}

Current file content:
```python
{file_content}
```

Instructions:
1. Analyze the current code
2. {description}
3. Return the complete modified file content

Respond with the full updated file content only, no explanations."""

        # Execute with Gemini
        print("[1/3] Sending task to Gemini...")
        gemini_response = await gemini.invoke(prompt)

        if gemini_response.status.name != "SUCCESS":
            return False, f"Gemini failed: {gemini_response.error}"

        modified_content = gemini_response.content

        # Validate with Claude
        print("[2/3] Validating with Claude...")
        validation_prompt = f"""Review this code modification for a Python file.

Original task: {description}

Modified code:
```python
{modified_content}
```

Questions:
1. Does this fulfill the task requirements?
2. Is the code syntactically correct?
3. Are there any issues?

Respond with: APPROVED or REJECTED (with reason)"""

        claude_response = await claude.invoke(validation_prompt)

        if "APPROVED" not in claude_response.content:
            return False, f"Claude rejected: {claude_response.content}"

        # Write modified file
        print("[3/3] Writing modified file...")
        target_file.write_text(modified_content, encoding='utf-8')

        return True, "SUCCESS"

    except Exception as e:
        return False, f"Error: {str(e)}"

    finally:
        # Cleanup
        await gemini.cleanup()
        await claude.cleanup()


async def run_pilot(story_count: int = 2):
    """
    Run NCM pilot with N stories.

    Args:
        story_count: Number of stories to execute (default: 2)
    """
    print("\n" + "="*70)
    print(f"  NCM PILOT - Direct Async Execution ({story_count} stories)")
    print("  Date:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("="*70)

    # Define pilot stories
    stories = [
        ("PILOT-001", "Add comprehensive module docstring to file", Path("core/ncm/models.py")),
        ("PILOT-002", "Add docstring to Story class with description of all fields", Path("core/ncm/models.py")),
        ("PILOT-003", "Add docstring to NCMConfig class", Path("core/ncm/models.py")),
        ("PILOT-004", "Add docstring to StoryShardEngine class", Path("core/ncm/story_shard.py")),
        ("PILOT-005", "Add docstring to CrewManager class", Path("core/ncm/crew_manager.py")),
        ("PILOT-006", "Add docstring to TokenBudgetMonitor class", Path("core/ncm/token_monitor.py")),
        ("PILOT-007", "Add docstring to PromptRefreshSystem class", Path("core/ncm/prompt_refresh.py")),
        ("PILOT-008", "Add docstring to StateSnapshotSystem class", Path("core/ncm/snapshot.py")),
        ("PILOT-009", "Add docstring to SimpleExecutor class", Path("core/ncm/simple_executor.py")),
        ("PILOT-010", "Add docstring to MultiAIExecutor class", Path("core/ncm/multi_ai_executor.py")),
    ]

    # Execute stories
    results = []
    start_time = datetime.now()

    for i, (story_id, description, target_file) in enumerate(stories[:story_count], 1):
        print(f"\n[Story {i}/{story_count}]")

        success, message = await execute_pilot_story(story_id, description, target_file)

        results.append((story_id, success, message))

        if success:
            print(f"✓ {story_id}: SUCCESS")
        else:
            print(f"✗ {story_id}: FAILED - {message}")

    duration = (datetime.now() - start_time).total_seconds()

    # Report results
    print("\n" + "="*70)
    print("  PILOT RESULTS")
    print("="*70 + "\n")

    completed = sum(1 for _, success, _ in results if success)
    failed = sum(1 for _, success, _ in results if not success)

    print(f"  Total Stories:    {len(results)}")
    print(f"  Completed:        {completed} ({completed/len(results)*100:.1f}%)")
    print(f"  Failed:           {failed}")
    print(f"  Duration:         {duration:.1f}s")
    print(f"  Avg per Story:    {duration/len(results):.1f}s")
    print()

    # Success criteria
    success_rate = completed / len(results)

    if success_rate >= 0.80:
        print("  ✓ PILOT PASSED (≥80% success)")
        return True
    else:
        print("  ✗ PILOT FAILED (<80% success)")
        return False


if __name__ == "__main__":
    import argparse

    parser = argparse.parser(description="NCM Pilot - Direct Async Execution")
    parser.add_argument("--count", type=int, default=2, help="Number of stories to execute")
    args = parser.parse_args()

    try:
        result = asyncio.run(run_pilot(args.count))
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n\nPilot interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\nFATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
