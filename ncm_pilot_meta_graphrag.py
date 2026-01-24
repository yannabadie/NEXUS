#!/usr/bin/env python
"""
NCM Pilot with Meta GraphRAG Tasks - Use the 80 tasks from deep analysis.

This script converts Meta GraphRAG tasks to NCM Story objects and executes them.

Usage:
    python ncm_pilot_meta_graphrag.py --priority=p2 --count=10
    python ncm_pilot_meta_graphrag.py --priority=p0 --count=5
"""

import sys
import json
from pathlib import Path
from typing import List

# Add NEXUS root to path
NEXUS_ROOT = Path(__file__).parent
sys.path.insert(0, str(NEXUS_ROOT))

from core.ncm.models import Story, StoryPriority, IssueDomain


def load_meta_graphrag_tasks(json_file: Path) -> List[dict]:
    """Load tasks from Meta GraphRAG analysis JSON."""
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data.get('tasks', [])


def convert_to_story(task: dict, story_number: int) -> Story:
    """Convert Meta GraphRAG task to NCM Story object."""
    # Map issue_type to IssueDomain
    domain_map = {
        'missing_docstring': IssueDomain.DOCUMENTATION,
        'missing_type_hint': IssueDomain.TYPING,
        'security_issue': IssueDomain.SECURITY,
        'complexity': IssueDomain.REFACTORING,
        'test_coverage': IssueDomain.TESTING,
        'dead_import': IssueDomain.CLEANUP,
    }

    # Map priority string to StoryPriority
    priority_map = {
        'P0': StoryPriority.P0,
        'P1': StoryPriority.P1,
        'P2': StoryPriority.P2,
    }

    # Build description with verification method
    description = f"""
{task['description']}

Reason: {task['reason']}

Verification: {task['verification_method']}

File: {task['file_path']} ({task['line_numbers']})
""".strip()

    return Story(
        story_id=task['task_id'],
        priority=priority_map.get(task['priority'], StoryPriority.P2),
        domains={domain_map.get(task['issue_type'], IssueDomain.CLEANUP)},
        description=description,
        target_files=[Path(task['file_path'])],
        test_files=[],  # Will be inferred by NCM
    )


def filter_tasks_by_priority(tasks: List[dict], priority: str) -> List[dict]:
    """Filter tasks by priority (P0, P1, P2)."""
    return [t for t in tasks if t['priority'].upper() == priority.upper()]


def filter_tasks_by_type(tasks: List[dict], issue_type: str) -> List[dict]:
    """Filter tasks by issue type."""
    return [t for t in tasks if t['issue_type'] == issue_type]


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description='NCM Pilot with Meta GraphRAG tasks')
    parser.add_argument('--priority', default='p2', help='Priority filter (p0, p1, p2)')
    parser.add_argument('--type', help='Issue type filter (missing_type_hint, security_issue, etc.)')
    parser.add_argument('--count', type=int, default=10, help='Number of tasks to execute')
    parser.add_argument('--list', action='store_true', help='List available tasks and exit')

    args = parser.parse_args()

    # Load tasks from Meta GraphRAG analysis
    json_file = NEXUS_ROOT / 'workspace' / 'ncm_analysis' / 'ncm_deep_analysis_output.json'

    if not json_file.exists():
        print(f"[ERROR] Meta GraphRAG analysis file not found: {json_file}")
        print("Run: python ncm_deep_analysis.py")
        return 1

    print(f"[META_GRAPHRAG] Loading tasks from {json_file}")
    all_tasks = load_meta_graphrag_tasks(json_file)
    print(f"  Total tasks loaded: {len(all_tasks)}")

    # Filter by priority
    if args.priority:
        all_tasks = filter_tasks_by_priority(all_tasks, args.priority)
        print(f"  After priority filter ({args.priority.upper()}): {len(all_tasks)}")

    # Filter by type
    if args.type:
        all_tasks = filter_tasks_by_type(all_tasks, args.type)
        print(f"  After type filter ({args.type}): {len(all_tasks)}")

    # List mode
    if args.list:
        print(f"\n[AVAILABLE TASKS] {len(all_tasks)} tasks:\n")
        for i, task in enumerate(all_tasks[:50], 1):  # Show first 50
            print(f"{i}. {task['task_id']} ({task['priority']}) - {task['file_path']}:{task['line_numbers']}")
            print(f"   Type: {task['issue_type']}")
            print(f"   Reason: {task['reason'][:80]}...")
            print()
        if len(all_tasks) > 50:
            print(f"... and {len(all_tasks) - 50} more tasks")
        return 0

    # Limit to count
    selected_tasks = all_tasks[:args.count]
    print(f"  Selected for execution: {len(selected_tasks)}")

    # Convert to Story objects
    print(f"\n[NCM_STORIES] Converting {len(selected_tasks)} tasks to Story objects...")
    stories = [convert_to_story(task, i) for i, task in enumerate(selected_tasks, 1)]

    # Save stories to file for NCM command to load
    stories_file = NEXUS_ROOT / 'workspace' / 'ncm_analysis' / 'ncm_pilot_stories.json'
    stories_data = {
        'stories': [
            {
                'story_id': s.story_id,
                'priority': s.priority.value,
                'domains': [d.value for d in s.domains],
                'description': s.description,
                'target_files': [str(f) for f in s.target_files],
                'test_files': [str(f) for f in s.test_files],
            }
            for s in stories
        ]
    }

    stories_file.write_text(json.dumps(stories_data, indent=2, ensure_ascii=False), encoding='utf-8')
    print(f"  Stories saved to: {stories_file}")

    # Print summary
    print(f"\n{'=' * 80}")
    print(f"NCM PILOT - Meta GraphRAG Tasks")
    print(f"{'=' * 80}")
    print(f"Priority: {args.priority.upper()}")
    if args.type:
        print(f"Type: {args.type}")
    print(f"Stories: {len(stories)}")
    print(f"\nBreakdown by type:")

    type_counts = {}
    for task in selected_tasks:
        issue_type = task['issue_type']
        type_counts[issue_type] = type_counts.get(issue_type, 0) + 1

    for issue_type, count in sorted(type_counts.items()):
        print(f"  - {issue_type}: {count}")

    print(f"\n{'=' * 80}")
    print(f"\nNext steps:")
    print(f"1. Start NEXUS REPL: python nexus7.py")
    print(f"2. Load stories: /ncm load {stories_file}")
    print(f"3. Execute: /ncm execute --batch={len(stories)}")
    print(f"\nOr use the stories file directly in your NCM code.")
    print(f"{'=' * 80}\n")

    return 0


if __name__ == '__main__':
    sys.exit(main())
