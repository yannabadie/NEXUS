"""
Execute NCM Phase 2B with Multi-AI Acceleration.

Routes stories to optimal AI providers for 3-4x speedup:
- dead_import → SimpleExecutor (~6s)
- missing_doc → OpenCode/GLM (~45s)
- type_error → Codex (~90s)
- dead_code → NEXUS (~5min)

Usage:
    # Execute with default settings
    python scripts/execute_ncm_phase2b_multi_ai.py

    # Execute with more parallel workers
    python scripts/execute_ncm_phase2b_multi_ai.py --workers=4

    # Resume from last state
    python scripts/execute_ncm_phase2b_multi_ai.py

    # Reset and start fresh
    python scripts/execute_ncm_phase2b_multi_ai.py --reset

Author: Claude (NEXUS V12.4)
Date: 2026-01-21
"""

import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime
import argparse

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.ncm.multi_ai_executor import MultiAIExecutor, MultiAIExecutorConfig


def check_prerequisites():
    """Check that all prerequisites are in place."""
    workspace_path = Path.cwd()

    # Check for stories file
    stories_path = workspace_path / "workspace/ncm/phase2b_stories.json"
    if not stories_path.exists():
        # Try phase2a_queue.json as fallback
        fallback_path = workspace_path / "workspace/ncm/phase2a_queue.json"
        if fallback_path.exists():
            print(f"Using fallback queue: {fallback_path}")
            return fallback_path
        else:
            print(f"ERROR: Stories file not found: {stories_path}")
            print("Generate with: python scripts/generate_phase2b_queue.py")
            sys.exit(1)

    return stories_path


def generate_phase2b_queue():
    """Generate Phase 2B queue from Phase 2A queue (filter completed)."""
    workspace_path = Path.cwd() / "workspace/ncm"
    phase2a_path = workspace_path / "phase2a_queue.json"
    phase2b_path = workspace_path / "phase2b_stories.json"

    if phase2b_path.exists():
        print(f"Phase 2B queue already exists: {phase2b_path}")
        return phase2b_path

    if not phase2a_path.exists():
        print(f"ERROR: Phase 2A queue not found: {phase2a_path}")
        sys.exit(1)

    # Load Phase 2A queue
    with open(phase2a_path, "r", encoding="utf-8") as f:
        phase2a_data = json.load(f)

    # Load execution state to find completed stories
    state_path = workspace_path / "execution_state.json"
    completed_ids = set()
    if state_path.exists():
        with open(state_path, "r", encoding="utf-8") as f:
            state = json.load(f)
            completed_ids = set(state.get("completed_stories", []))

    # Filter to remaining stories
    all_stories = phase2a_data.get("stories", [])
    remaining_stories = [s for s in all_stories if s.get("story_id") not in completed_ids]

    # Enrich stories with additional metadata for multi-AI routing
    enriched_stories = []
    for story in remaining_stories:
        enriched = {
            "story_id": story.get("story_id"),
            "category": story.get("category"),
            "priority": story.get("priority"),
            "description": story.get("description"),
            "target_file": story.get("target_files", [""])[0],  # Primary target
            "target_files": story.get("target_files", []),
            "domains": story.get("domains", []),
        }

        # Parse additional metadata from description
        if story.get("category") == "dead_import":
            # Extract line number if present
            import re
            line_match = re.search(r"line (\d+)", story.get("description", ""))
            if line_match:
                enriched["line_number"] = int(line_match.group(1))

            # Extract import text
            import_match = re.search(r"Import '([^']+)'", story.get("description", ""))
            if import_match:
                enriched["import_text"] = import_match.group(1)

        enriched_stories.append(enriched)

    # Save Phase 2B queue
    phase2b_data = {
        "generated_at": datetime.now().isoformat(),
        "total_stories": len(enriched_stories),
        "by_category": {},
        "stories": enriched_stories,
    }

    # Count by category
    for story in enriched_stories:
        cat = story.get("category", "unknown")
        phase2b_data["by_category"][cat] = phase2b_data["by_category"].get(cat, 0) + 1

    with open(phase2b_path, "w", encoding="utf-8") as f:
        json.dump(phase2b_data, f, indent=2)

    print(f"Generated Phase 2B queue: {phase2b_path}")
    print(f"  Total stories: {len(enriched_stories)}")
    print(f"  By category: {phase2b_data['by_category']}")

    return phase2b_path


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Execute NCM Phase 2B with Multi-AI Acceleration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Providers:
  - SimpleExecutor: dead_import (~6s/story)
  - OpenCode/GLM: missing_doc (~45s/story)
  - Codex: type_error (~90s/story)
  - NEXUS: dead_code, complex (~5min/story)

Environment Variables:
  - OPENCODE_ZEN_API_KEY: OpenCode Zen API key
  - OPENAI_API_KEY: OpenAI API key for Codex

Examples:
    # Run with defaults
    python scripts/execute_ncm_phase2b_multi_ai.py

    # More parallel workers
    python scripts/execute_ncm_phase2b_multi_ai.py --workers=4

    # Reset state
    python scripts/execute_ncm_phase2b_multi_ai.py --reset
"""
    )

    parser.add_argument("--stories", type=str, help="Path to stories JSON file")
    parser.add_argument("--workers", type=int, default=3, help="Parallel workers (default: 3)")
    parser.add_argument("--reset", action="store_true", help="Reset state and start fresh")
    parser.add_argument("--opencode-url", type=str, default="http://localhost:5173",
                       help="OpenCode server URL")
    parser.add_argument("--opencode-model", type=str, default="glm-4.7",
                       help="OpenCode model (default: glm-4.7)")
    parser.add_argument("--codex-model", type=str, default="gpt-5.2-codex",
                       help="Codex model (default: gpt-5.2-codex)")
    parser.add_argument("--codex-reasoning", type=str, default="xhigh",
                       choices=["low", "medium", "high", "xhigh"],
                       help="Codex reasoning effort (default: xhigh)")
    parser.add_argument("--quiet", action="store_true", help="Reduce output verbosity")

    args = parser.parse_args()

    print("=" * 60)
    print("NCM PHASE 2B - MULTI-AI ACCELERATED EXECUTION")
    print("=" * 60)
    print()

    # Handle reset
    if args.reset:
        state_path = Path("workspace/ncm/multi_ai_state.json")
        if state_path.exists():
            state_path.unlink()
            print("Multi-AI state reset. Starting fresh.")

    # Generate Phase 2B queue if needed
    if args.stories:
        stories_path = Path(args.stories)
    else:
        stories_path = generate_phase2b_queue()

    # Check prerequisites
    print()
    print("Checking prerequisites...")

    # Check OpenCode server (optional)
    import httpx
    opencode_available = False
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{args.opencode_url}/health")
            if response.status_code == 200:
                opencode_available = True
                print(f"  OpenCode server: AVAILABLE at {args.opencode_url}")
    except Exception:
        print(f"  OpenCode server: NOT AVAILABLE (missing_doc stories will use fallback)")

    # Check Codex API key
    import os
    codex_available = bool(os.environ.get("OPENAI_API_KEY"))
    if codex_available:
        print(f"  Codex API key: FOUND")
    else:
        print(f"  Codex API key: NOT FOUND (type_error stories will use NEXUS fallback)")

    print()

    # Create config
    config = MultiAIExecutorConfig(
        workspace_path=Path.cwd(),
        stories_path=stories_path,
        parallel_workers=args.workers,
        opencode_server_url=args.opencode_url,
        opencode_model=args.opencode_model,
        codex_model=args.codex_model,
        codex_reasoning=args.codex_reasoning,
        verbose=not args.quiet,
    )

    # Create executor and run
    executor = MultiAIExecutor(config)

    try:
        result = await executor.execute_phase2b(
            stories_path=stories_path,
            resume=not args.reset
        )

        # Print final summary
        print()
        print("=" * 60)
        print("EXECUTION SUMMARY")
        print("=" * 60)
        print(f"Status: {result.get('status', 'UNKNOWN')}")
        print(f"Total stories: {result.get('total', 0)}")
        print(f"Success: {result.get('success', 0)}")
        print(f"Failed: {result.get('failed', 0)}")
        print(f"Duration: {result.get('duration_minutes', 0):.1f} minutes")
        print(f"Tokens used: {result.get('total_tokens', 0):,}")
        print(f"Log file: {result.get('log_file', 'N/A')}")
        print("=" * 60)

        return result

    except KeyboardInterrupt:
        print("\nExecution interrupted by user.")
        return {"status": "INTERRUPTED"}


if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result.get("status") in ("COMPLETE", "PAUSED") else 1)
