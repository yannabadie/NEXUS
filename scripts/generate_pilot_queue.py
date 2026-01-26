"""
Generate Phase 1 Pilot Story Queue (100 P2 Stories)

Reads audit/issues.json and generates 100 low-risk P2 stories:
- 40 dead_import removals (safest)
- 30 missing_doc additions (safe)
- 30 dead_code removals (moderate)

Output: workspace/ncm/pilot_queue.json
"""

import json
import sys
from pathlib import Path
from typing import List, Dict, Any
from collections import defaultdict


def load_issues() -> List[Dict[str, Any]]:
    """Load issues from audit/issues.json."""
    issues_path = Path("audit/issues.json")
    if not issues_path.exists():
        print(f"ERROR: {issues_path} not found")
        sys.exit(1)

    with open(issues_path, "r", encoding="utf-8") as f:
        return json.load(f)


def group_issues_by_file(issues: List[Dict], category: str) -> Dict[str, List[Dict]]:
    """Group issues by file for a specific category."""
    grouped = defaultdict(list)
    for issue in issues:
        if issue["category"] == category:
            grouped[issue["file"]].append(issue)
    return dict(grouped)


def _is_test_path(path: str) -> bool:
    normalized = path.replace("\\", "/")
    if normalized.startswith("tests/") or "/tests/" in normalized:
        return True
    name = Path(normalized).name
    return name.startswith("test_") or name.endswith("_test.py")


def create_dead_import_stories(issues: List[Dict], limit: int = 40) -> List[Dict]:
    """
    Create stories for dead import removal.

    Strategy: 1 story per file (up to limit)
    Priority: P2 (LOW - safe cleanup)
    Domain: CLEANUP
    """
    stories = []
    grouped = group_issues_by_file(issues, "dead_import")

    story_count = 0
    for file_path, file_issues in list(grouped.items())[:limit]:
        story_id = f"PILOT-{story_count + 1:03d}"

        # Create target file path (normalize Windows paths)
        target_file = file_path.replace("\\", "/")

        # Find corresponding test file
        if target_file.startswith("core/"):
            test_file = f"tests/{target_file.replace('core/', '')}"
        else:
            test_file = f"tests/test_{Path(target_file).name}"

        story = {
            "story_id": story_id,
            "priority": "P2",
            "domains": ["CLEANUP"],
            "description": f"""Remove dead imports from {target_file} ({len(file_issues)} imports)

Issues:
{chr(10).join([f"- Line {issue['line']}: {issue['message']}" for issue in file_issues[:5]])}
{'...' if len(file_issues) > 5 else ''}

Tasks:
1. Remove {len(file_issues)} unused import(s) from {target_file}
2. Verify no reference exists in file (grep for imported names)
3. Run tests to verify no breakage: pytest {test_file} -v
4. Ensure formatting is preserved (black, isort)

Safety: This is low-risk cleanup. Dead imports have no runtime impact.
""",
            "target_files": [target_file],
            "test_files": [test_file],
            "issue_count": len(file_issues),
            "category": "dead_import"
        }

        stories.append(story)
        story_count += 1

        if story_count >= limit:
            break

    print(f"SUCCESS: Created {len(stories)} dead_import stories")
    return stories


def create_missing_doc_stories(issues: List[Dict], limit: int = 30) -> List[Dict]:
    """
    Create stories for missing documentation.

    Strategy: 1 story per file (up to limit)
    Priority: P2 (LOW)
    Domain: DOCUMENTATION
    """
    stories = []
    grouped = group_issues_by_file(issues, "missing_doc")

    story_count = len(stories)  # Continue from previous
    for file_path, file_issues in list(grouped.items())[:limit]:
        story_id = f"PILOT-{41 + story_count:03d}"  # Start after dead_import stories

        target_file = file_path.replace("\\", "/")

        # Extract function/class names from messages
        items = []
        for issue in file_issues:
            if "Function" in issue["message"]:
                func_name = issue["message"].split("'")[1]
                items.append(f"Line {issue['line']}: {func_name}()")
            elif "Class" in issue["message"]:
                class_name = issue["message"].split("'")[1]
                items.append(f"Line {issue['line']}: class {class_name}")

        story = {
            "story_id": story_id,
            "priority": "P2",
            "domains": ["DOCUMENTATION"],
            "description": f"""Add missing docstrings to {target_file} ({len(file_issues)} items)

Missing docstrings:
{chr(10).join([f"- {item}" for item in items[:5]])}
{'...' if len(items) > 5 else ''}

Tasks:
1. Add Google-style docstrings for {len(file_issues)} function(s)/class(es)
2. Include Args, Returns, Raises sections as appropriate
3. Follow NEXUS docstring patterns (see existing code)
4. Run: pytest {target_file} -v (if tests exist)

Format:
\"\"\"
Brief one-line description.

Longer description if needed.

Args:
    param_name: Description

Returns:
    Description of return value

Raises:
    ExceptionType: When this happens
\"\"\"

Safety: Documentation-only changes. No code logic modified.
""",
            "target_files": [target_file],
            "test_files": [],
            "issue_count": len(file_issues),
            "category": "missing_doc"
        }

        stories.append(story)
        story_count += 1

        if story_count >= limit:
            break

    print(f"SUCCESS: Created {len(stories)} missing_doc stories")
    return stories


def create_dead_code_stories(issues: List[Dict], limit: int = 30) -> List[Dict]:
    """
    Create stories for dead code removal.

    Strategy: 1 story per file (up to limit)
    Priority: P2 (MEDIUM - moderate risk)
    Domain: CLEANUP
    """
    stories = []
    grouped = group_issues_by_file(issues, "dead_code")

    story_count = len(stories)
    for file_path, file_issues in list(grouped.items())[:limit]:
        story_id = f"PILOT-{71 + story_count:03d}"  # Start after missing_doc stories

        target_file = file_path.replace("\\", "/")
        if _is_test_path(target_file):
            continue

        if target_file.startswith("core/"):
            test_file = f"tests/{target_file.replace('core/', '')}"
        else:
            test_file = f"tests/test_{Path(target_file).name}"

        story = {
            "story_id": story_id,
            "priority": "P2",
            "domains": ["CLEANUP"],
            "description": f"""Remove dead code from {target_file} ({len(file_issues)} items)

Dead code detected:
{chr(10).join([f"- Line {issue['line']}: {issue['message']}" for issue in file_issues[:5]])}
{'...' if len(file_issues) > 5 else ''}

Tasks:
1. Verify code is truly unused (grep for references)
2. Remove {len(file_issues)} unused function(s)/class(es)/variable(s)
3. Run tests to verify no breakage: pytest {test_file} -v
4. Check for indirect usage (reflection, dynamic imports)

Safety: MODERATE RISK. Verify thoroughly before removal. Vulture may have false positives.
""",
            "target_files": [target_file],
            "test_files": [test_file],
            "issue_count": len(file_issues),
            "category": "dead_code"
        }

        stories.append(story)
        story_count += 1

        if story_count >= limit:
            break

    print(f"SUCCESS: Created {len(stories)} dead_code stories")
    return stories


def generate_pilot_queue():
    """Generate Phase 1 pilot queue (100 P2 stories)."""
    print("=" * 60)
    print("NCM Phase 1 Pilot Story Queue Generator")
    print("=" * 60)
    print()

    # Load issues
    print("Loading issues from audit/issues.json...")
    issues = load_issues()
    print(f"SUCCESS: Loaded {len(issues)} issues")
    print()

    # Generate stories by category
    print("Generating pilot stories...")
    print()

    all_stories = []

    # 40 dead_import stories (safest)
    dead_import_stories = create_dead_import_stories(issues, limit=40)
    all_stories.extend(dead_import_stories)
    print()

    # 30 missing_doc stories (safe)
    missing_doc_stories = create_missing_doc_stories(issues, limit=30)
    all_stories.extend(missing_doc_stories)
    print()

    # 30 dead_code stories (moderate risk)
    dead_code_stories = create_dead_code_stories(issues, limit=30)
    all_stories.extend(dead_code_stories)
    print()

    # Save to workspace/ncm/pilot_queue.json
    output_dir = Path("workspace/ncm")
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / "pilot_queue.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({
            "phase": "Phase 1 Pilot",
            "total_stories": len(all_stories),
            "story_breakdown": {
                "dead_import": 40,
                "missing_doc": 30,
                "dead_code": 30
            },
            "generated": "2026-01-21",
            "stories": all_stories
        }, f, indent=2)

    print("=" * 60)
    print(f"SUCCESS: Pilot queue generated successfully!")
    print(f"Output: {output_path}")
    print(f"Total stories: {len(all_stories)}")
    print()
    print("Story breakdown:")
    print(f"  - Dead imports:   40 stories (safest)")
    print(f"  - Missing docs:   30 stories (safe)")
    print(f"  - Dead code:      30 stories (moderate)")
    print("=" * 60)
    print()
    print("Next steps:")
    print("1. Review generated stories: cat workspace/ncm/pilot_queue.json | jq")
    print("2. Set up NCM workspace directories")
    print("3. Execute pilot: python nexus7.py --ncm-pilot")
    print()


if __name__ == "__main__":
    generate_pilot_queue()
