"""
Generate Phase 2A Story Queue (500 P2 Stories)

Extends pilot queue (100 stories) to 500 P2 stories:
- 110 dead_import removals (continuing from pilot)
- 60 missing_doc additions
- 60 dead_code removals
- 150 type_error fixes (simple cases)
- 80 deprecation warnings
- 40 documentation improvements

Output: workspace/ncm/phase2a_queue.json
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


def load_pilot_queue() -> List[str]:
    """Load pilot queue to skip already-done stories."""
    pilot_path = Path("workspace/ncm/pilot/pilot_queue.json")
    if not pilot_path.exists():
        return []

    with open(pilot_path, "r", encoding="utf-8") as f:
        pilot_data = json.load(f)

    # Extract file paths already covered in pilot
    pilot_files = set()
    for story in pilot_data["stories"]:
        for file_path in story["target_files"]:
            pilot_files.add(file_path)

    return pilot_files


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


def create_dead_import_stories(issues: List[Dict], pilot_files: set, limit: int = 110, start_idx: int = 40) -> List[Dict]:
    """Create stories for dead import removal (continuing from pilot)."""
    stories = []
    grouped = group_issues_by_file(issues, "dead_import")

    story_count = 0
    file_count = 0
    for file_path, file_issues in sorted(grouped.items()):
        # Skip files already in pilot
        normalized_path = file_path.replace("\\", "/")
        if normalized_path in pilot_files:
            continue

        file_count += 1
        if file_count <= start_idx:  # Skip first 40 (pilot covered)
            continue

        story_id = f"P2A-{story_count + 1:03d}"

        target_file = file_path.replace("\\", "/")
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

    print(f"SUCCESS: Created {len(stories)} dead_import stories (continuing from pilot)")
    return stories


def create_type_error_stories(issues: List[Dict], pilot_files: set, limit: int = 150) -> List[Dict]:
    """
    Create stories for type error fixes (simple cases).

    Focus on: Missing return type hints, missing parameter type hints
    """
    stories = []
    grouped = group_issues_by_file(issues, "type_error")

    story_count = 0
    for file_path, file_issues in sorted(grouped.items()):
        normalized_path = file_path.replace("\\", "/")
        if normalized_path in pilot_files:
            continue

        # Filter for simple type errors (missing hints)
        simple_issues = [
            issue for issue in file_issues
            if "no return type hint" in issue["message"].lower() or
               "has no type hint" in issue["message"].lower()
        ]

        if not simple_issues:
            continue

        story_id = f"P2A-{110 + story_count + 1:03d}"

        target_file = file_path.replace("\\", "/")
        if target_file.startswith("core/"):
            test_file = f"tests/{target_file.replace('core/', '')}"
        else:
            test_file = f"tests/test_{Path(target_file).name}"

        story = {
            "story_id": story_id,
            "priority": "P2",
            "domains": ["TYPING", "REFACTORING"],
            "description": f"""Add missing type hints to {target_file} ({len(simple_issues)} items)

Type errors:
{chr(10).join([f"- Line {issue['line']}: {issue['message']}" for issue in simple_issues[:5]])}
{'...' if len(simple_issues) > 5 else ''}

Tasks:
1. Add type hints for {len(simple_issues)} function(s)/parameter(s)
2. Follow NEXUS type hint patterns (see existing code)
3. Use typing module imports (Optional, List, Dict, etc.)
4. Run: mypy {target_file} --strict
5. Run: pytest {test_file} -v

Example:
def foo(x, y):  # Before
    return x + y

def foo(x: int, y: int) -> int:  # After
    return x + y

Safety: Type hints are non-intrusive. No runtime logic changed.
""",
            "target_files": [target_file],
            "test_files": [test_file],
            "issue_count": len(simple_issues),
            "category": "type_error"
        }

        stories.append(story)
        story_count += 1

        if story_count >= limit:
            break

    print(f"SUCCESS: Created {len(stories)} type_error stories (simple cases)")
    return stories


def create_deprecation_stories(issues: List[Dict], limit: int = 80) -> List[Dict]:
    """
    Create stories for deprecation warning fixes.

    Focus on: datetime.utcnow() -> datetime.now(timezone.utc)
    """
    stories = []

    # Group by deprecation type
    deprecation_patterns = {
        "datetime.utcnow": [],
        "LanceDB table_names": [],
        "async warnings": []
    }

    for issue in issues:
        if issue["category"] == "bug_pattern":
            msg = issue["message"].lower()
            if "utcnow" in msg:
                deprecation_patterns["datetime.utcnow"].append(issue)
            elif "table_names" in msg:
                deprecation_patterns["LanceDB table_names"].append(issue)
            elif "not awaited" in msg:
                deprecation_patterns["async warnings"].append(issue)

    story_count = 0

    # Create stories for datetime.utcnow deprecations
    files_by_deprecation = defaultdict(list)
    for issue in deprecation_patterns["datetime.utcnow"]:
        files_by_deprecation[issue["file"]].append(issue)

    for file_path, file_issues in list(files_by_deprecation.items())[:limit]:
        story_id = f"P2A-{260 + story_count + 1:03d}"

        target_file = file_path.replace("\\", "/")
        if target_file.startswith("core/"):
            test_file = f"tests/{target_file.replace('core/', '')}"
        else:
            test_file = f"tests/test_{Path(target_file).name}"

        story = {
            "story_id": story_id,
            "priority": "P2",
            "domains": ["REFACTORING"],
            "description": f"""Fix deprecation warnings in {target_file} ({len(file_issues)} warnings)

Deprecations:
{chr(10).join([f"- Line {issue['line']}: {issue['message']}" for issue in file_issues[:5]])}
{'...' if len(file_issues) > 5 else ''}

Tasks:
1. Replace datetime.utcnow() with datetime.now(timezone.utc)
2. Add: from datetime import timezone
3. Verify all usages updated
4. Run: pytest {test_file} -v
5. Check for any timezone-related test failures

Migration:
# Before
from datetime import datetime
now = datetime.utcnow()

# After
from datetime import datetime, timezone
now = datetime.now(timezone.utc)

Safety: Standard deprecation migration. Python 3.12+ compatible.
""",
            "target_files": [target_file],
            "test_files": [test_file],
            "issue_count": len(file_issues),
            "category": "deprecation"
        }

        stories.append(story)
        story_count += 1

        if story_count >= limit:
            break

    print(f"SUCCESS: Created {len(stories)} deprecation stories")
    return stories


def create_documentation_stories(issues: List[Dict], pilot_files: set, limit: int = 60, start_idx: int = 30) -> List[Dict]:
    """Create stories for missing documentation (continuing from pilot)."""
    stories = []
    grouped = group_issues_by_file(issues, "missing_doc")

    story_count = 0
    file_count = 0
    for file_path, file_issues in sorted(grouped.items()):
        normalized_path = file_path.replace("\\", "/")
        if normalized_path in pilot_files:
            continue

        file_count += 1
        if file_count <= start_idx:
            continue

        story_id = f"P2A-{340 + story_count + 1:03d}"

        target_file = file_path.replace("\\", "/")

        items = []
        for issue in file_issues:
            if "Function" in issue["message"]:
                func_name = issue["message"].split("'")[1] if "'" in issue["message"] else "unknown"
                items.append(f"Line {issue['line']}: {func_name}()")
            elif "Class" in issue["message"]:
                class_name = issue["message"].split("'")[1] if "'" in issue["message"] else "unknown"
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

    print(f"SUCCESS: Created {len(stories)} missing_doc stories (continuing from pilot)")
    return stories


def create_dead_code_stories(issues: List[Dict], pilot_files: set, limit: int = 60, start_idx: int = 30) -> List[Dict]:
    """Create stories for dead code removal (continuing from pilot)."""
    stories = []
    grouped = group_issues_by_file(issues, "dead_code")

    story_count = 0
    file_count = 0
    for file_path, file_issues in sorted(grouped.items()):
        normalized_path = file_path.replace("\\", "/")
        if normalized_path in pilot_files:
            continue
        if _is_test_path(normalized_path):
            continue

        file_count += 1
        if file_count <= start_idx:
            continue

        story_id = f"P2A-{400 + story_count + 1:03d}"

        target_file = file_path.replace("\\", "/")
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

    print(f"SUCCESS: Created {len(stories)} dead_code stories (continuing from pilot)")
    return stories


def generate_phase2a_queue():
    """Generate Phase 2A queue (500 P2 stories)."""
    print("=" * 60)
    print("NCM Phase 2A Story Queue Generator")
    print("=" * 60)
    print()

    # Load issues
    print("Loading issues from audit/issues.json...")
    issues = load_issues()
    print(f"SUCCESS: Loaded {len(issues)} issues")
    print()

    # Load pilot files to avoid duplicates
    print("Loading pilot queue to avoid duplicates...")
    pilot_files = load_pilot_queue()
    print(f"SUCCESS: Loaded {len(pilot_files)} files from pilot")
    print()

    # Generate stories by category
    print("Generating Phase 2A stories...")
    print()

    all_stories = []

    # 110 dead_import stories (continuing from pilot's 40)
    dead_import_stories = create_dead_import_stories(issues, pilot_files, limit=110, start_idx=40)
    all_stories.extend(dead_import_stories)
    print()

    # 150 type_error stories (simple cases - missing type hints)
    type_error_stories = create_type_error_stories(issues, pilot_files, limit=150)
    all_stories.extend(type_error_stories)
    print()

    # 80 deprecation stories
    deprecation_stories = create_deprecation_stories(issues, limit=80)
    all_stories.extend(deprecation_stories)
    print()

    # 60 missing_doc stories (continuing from pilot's 30)
    missing_doc_stories = create_documentation_stories(issues, pilot_files, limit=60, start_idx=30)
    all_stories.extend(missing_doc_stories)
    print()

    # 60 dead_code stories (continuing from pilot's 30)
    dead_code_stories = create_dead_code_stories(issues, pilot_files, limit=60, start_idx=30)
    all_stories.extend(dead_code_stories)
    print()

    # Save to workspace/ncm/phase2a_queue.json
    output_dir = Path("workspace/ncm")
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / "phase2a_queue.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({
            "phase": "Phase 2A",
            "total_stories": len(all_stories),
            "story_breakdown": {
                "dead_import": 110,
                "type_error": 150,
                "deprecation": 80,
                "missing_doc": 60,
                "dead_code": 60
            },
            "generated": "2026-01-21",
            "stories": all_stories
        }, f, indent=2)

    print("=" * 60)
    print(f"SUCCESS: Phase 2A queue generated successfully!")
    print(f"Output: {output_path}")
    print(f"Total stories: {len(all_stories)}")
    print()
    print("Story breakdown:")
    print(f"  - Dead imports:   110 stories (continuing from pilot)")
    print(f"  - Type errors:    150 stories (simple - missing hints)")
    print(f"  - Deprecations:   80 stories (datetime.utcnow, etc.)")
    print(f"  - Missing docs:   60 stories (continuing from pilot)")
    print(f"  - Dead code:      60 stories (continuing from pilot)")
    print("=" * 60)
    print()
    print("Next steps:")
    print("1. Review generated stories: cat workspace/ncm/phase2a_queue.json | jq")
    print("2. Execute Phase 2A: python scripts/execute_ncm_pilot.py --phase=2a")
    print()


if __name__ == "__main__":
    generate_phase2a_queue()
