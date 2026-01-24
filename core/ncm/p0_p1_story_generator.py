"""
NCM P0/P1 Story Generator - Complex stories requiring collaborative mode.

Generates high-priority stories from audit analysis:
- P0: Security fixes (40 HIGH issues)
- P1: God class refactoring
- P1: Critical bug fixes
"""

from pathlib import Path
from typing import List
import re

from core.ncm.models import Story, StoryPriority, IssueDomain


class P0P1StoryGenerator:
    """Generate P0/P1 stories from audit findings."""

    def __init__(self, workspace_path: Path):
        if workspace_path.name == "workspace":
            self.project_root = workspace_path.parent
        else:
            self.project_root = workspace_path

        self.workspace_path = self.project_root
        self.audit_path = self.project_root / "audit"

    def generate_security_stories(self, limit: int = 20) -> List[Story]:
        """
        Generate P0 security stories from audit findings.

        Args:
            limit: Maximum number of stories to generate

        Returns:
            List of Story objects for security fixes
        """
        stories = []

        # Common security issues found in audit
        security_issues = [
            {
                "title": "Fix JWT secret generation (hardcoded secret)",
                "file": "core/security/auth.py",
                "description": "Security vulnerability: JWT secret is hardcoded instead of using environment variable.\n\nImpact:\n- All tokens can be forged with known secret\n- Critical security breach\n\nFix:\n- Use os.environ['JWT_SECRET'] with validation\n- Add fallback to secrets.token_hex(32) for development\n- Update tests to use temporary secrets",
                "priority": StoryPriority.P0,
                "domains": {IssueDomain.SECURITY},
            },
            {
                "title": "Add input validation to ExecutionPolicy",
                "file": "core/security/execution_policy.py",
                "description": "Security gap: User input not validated before execution.\n\nImpact:\n- Command injection possible\n- Arbitrary code execution risk\n\nFix:\n- Add input sanitization layer\n- Whitelist allowed characters\n- Validate paths against workspace boundaries",
                "priority": StoryPriority.P0,
                "domains": {IssueDomain.SECURITY},
            },
            {
                "title": "Implement rate limiting for API endpoints",
                "file": "core/api/cerebro/rate_limit.py",
                "description": "Security vulnerability: No rate limiting on sensitive endpoints.\n\nImpact:\n- DDoS vulnerability\n- Brute force attacks possible\n\nFix:\n- Implement token bucket algorithm\n- Add per-IP and per-user limits\n- Configure thresholds per endpoint",
                "priority": StoryPriority.P0,
                "domains": {IssueDomain.SECURITY},
            },
        ]

        for i, issue in enumerate(security_issues[:limit], 1):
            story = Story(
                story_id=f"P0-SEC-{i:03d}",
                priority=issue["priority"],
                domains=issue["domains"],
                description=f"{issue['title']}\n\nFile: {issue['file']}\n\n{issue['description']}",
                target_files=[self.project_root / issue["file"]],
                test_files=[],
            )
            stories.append(story)

        return stories

    def generate_god_class_refactoring_stories(self, limit: int = 10) -> List[Story]:
        """
        Generate P1 stories for God class refactoring.

        Args:
            limit: Maximum number of stories to generate

        Returns:
            List of Story objects for refactoring
        """
        stories = []

        # God classes identified in audit
        god_classes = [
            {
                "title": "Refactor fsm_handlers.py (1838 LOC) into handler modules",
                "file": "core/orchestration/fsm_handlers.py",
                "lines": 1838,
                "description": "God class: fsm_handlers.py is too large (1838 LOC).\n\nImpact:\n- Difficult to maintain\n- High coupling\n- Test complexity\n\nRefactoring Plan:\n1. Extract state handlers into separate files:\n   - handlers/brainstorm_handler.py\n   - handlers/tool_execution_handler.py\n   - handlers/validation_handler.py\n   - handlers/swarm_handler.py\n   - etc. (12 handlers total)\n2. Create handlers/ package with __init__.py\n3. Update imports in orchestrator\n4. Run full test suite to validate\n\nSuccess Criteria:\n- All 12 handlers extracted\n- Each handler < 200 LOC\n- All tests pass\n- No regression",
                "priority": StoryPriority.P1,
                "domains": {IssueDomain.REFACTORING},
            },
            {
                "title": "Split tool_manager.py into focused modules",
                "file": "core/execution/tool_manager.py",
                "lines": 800,
                "description": "Centralized God class: tool_manager.py handles too many responsibilities.\n\nImpact:\n- Single point of failure\n- Hard to extend\n- Circular dependencies\n\nRefactoring Plan:\n1. Extract tool registration → tool_registry.py\n2. Extract tool execution → tool_executor.py\n3. Extract tool validation → tool_validator.py\n4. Keep ToolManager as coordinator\n\nSuccess Criteria:\n- 3 new focused modules\n- Clear separation of concerns\n- All tests pass",
                "priority": StoryPriority.P1,
                "domains": {IssueDomain.REFACTORING},
            },
        ]

        for i, issue in enumerate(god_classes[:limit], 1):
            story = Story(
                story_id=f"P1-REFACTOR-{i:03d}",
                priority=issue["priority"],
                domains=issue["domains"],
                description=f"{issue['title']}\n\nFile: {issue['file']} ({issue['lines']} LOC)\n\n{issue['description']}",
                target_files=[self.project_root / issue["file"]],
                test_files=[],
            )
            stories.append(story)

        return stories

    def generate_critical_bug_stories(self, limit: int = 10) -> List[Story]:
        """
        Generate P1 stories for critical bugs.

        Args:
            limit: Maximum number of stories to generate

        Returns:
            List of Story objects for bug fixes
        """
        stories = []

        # Critical bugs from audit
        critical_bugs = [
            {
                "title": "Fix async context manager leak in session_abstraction.py",
                "file": "core/drivers/session_abstraction.py",
                "description": "Memory leak: Async context managers not properly closed.\n\nImpact:\n- Memory leak over time\n- Resource exhaustion\n- Session corruption\n\nFix:\n- Add explicit cleanup in __aexit__\n- Use try/finally blocks\n- Add tests for resource cleanup",
                "priority": StoryPriority.P1,
                "domains": {IssueDomain.REFACTORING, IssueDomain.TESTING},
            },
            {
                "title": "Fix race condition in AsyncBlackboard",
                "file": "core/memory/blackboard.py",
                "description": "Race condition: Concurrent writes to Blackboard not properly locked.\n\nImpact:\n- Data corruption\n- Lost updates\n- FSM state inconsistency\n\nFix:\n- Add asyncio.Lock for write operations\n- Use atomic transactions\n- Add stress tests",
                "priority": StoryPriority.P1,
                "domains": {IssueDomain.REFACTORING, IssueDomain.TESTING},
            },
        ]

        for i, issue in enumerate(critical_bugs[:limit], 1):
            story = Story(
                story_id=f"P1-BUG-{i:03d}",
                priority=issue["priority"],
                domains=issue["domains"],
                description=f"{issue['title']}\n\nFile: {issue['file']}\n\n{issue['description']}",
                target_files=[self.project_root / issue["file"]],
                test_files=[],
            )
            stories.append(story)

        return stories

    def generate_p0_p1_stories(self, count: int = 50) -> List[Story]:
        """
        Generate mixed P0/P1 stories.

        Mix:
        - 40% P0 security fixes
        - 40% P1 god class refactoring
        - 20% P1 critical bugs

        Args:
            count: Total number of stories to generate

        Returns:
            List of Story objects
        """
        stories = []

        # Calculate counts
        security_count = int(count * 0.4)
        refactor_count = int(count * 0.4)
        bug_count = count - security_count - refactor_count

        print(f"[P0P1Generator] Generating {security_count} security stories...")
        stories.extend(self.generate_security_stories(limit=security_count))

        print(f"[P0P1Generator] Generating {refactor_count} refactoring stories...")
        stories.extend(self.generate_god_class_refactoring_stories(limit=refactor_count))

        print(f"[P0P1Generator] Generating {bug_count} bug fix stories...")
        stories.extend(self.generate_critical_bug_stories(limit=bug_count))

        print(f"[P0P1Generator] Total P0/P1 stories generated: {len(stories)}")
        return stories


if __name__ == "__main__":
    # Test the generator
    from pathlib import Path
    workspace = Path(__file__).parent.parent.parent
    generator = P0P1StoryGenerator(workspace)

    stories = generator.generate_p0_p1_stories(count=10)
    print(f"\nGenerated {len(stories)} P0/P1 stories:")
    for story in stories:
        print(f"  {story.story_id} ({story.priority.value}): {story.description[:80]}...")
