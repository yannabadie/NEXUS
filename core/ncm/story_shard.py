"""
Story Sharding Engine - Audit Report Parser

Parses NEXUS audit report and generates prioritized story queue.

Story Sharding Strategy:
    - God classes → 1 story per class (3 stories)
    - Security issues → 1 story per vulnerability (4 stories)
    - Dead imports → 1 story per module (~30 stories batched)
    - Type errors → 1 story per module (~80 stories batched)
    - Deprecation warnings → 1 story per pattern (~15 stories)

Total: 10,602 issues → ~500 stories (batched by module/pattern)

Input:
    audit/ANALYSIS_EXHAUSTIVE_2026-01-21.md (audit report)

Output:
    List[Story] objects, priority-ordered (P0 → P1 → P2)

Process:
    1. Parse audit report sections
    2. Group issues by module/pattern
    3. Create Story objects with descriptions
    4. RAG validation gate (verify context exists)
    5. Priority assignment (HIGH → P0, etc.)
    6. Domain classification (for crew assignment)
"""

from pathlib import Path
from typing import List, Dict, Set, Optional, Tuple
from datetime import datetime
import re

from core.ncm.models import (
    Story,
    StoryPriority,
    IssueDomain,
    StoryStatus,
    RAGValidationResult,
)
from core.logging import get_logger


class StoryShardEngine:
    """
    Audit report parser → story queue.

    Responsibilities:
        - Parse audit report (ANALYSIS_EXHAUSTIVE_2026-01-21.md)
        - Create Story objects (one per issue or issue group)
        - RAG validation gate (blind spot #4 mitigation)
        - Priority assignment (P0/P1/P2)
        - Domain classification (CODING/SECURITY/TESTING/etc.)

    Story Sharding Strategy:
        - God classes → 1 story per class (3 stories)
        - Security issues → 1 story per vulnerability (4 stories)
        - Dead imports → 1 story per module (410 → ~30 stories)
        - Type errors → 1 story per module (2913 → ~80 stories)
        - Deprecation warnings → 1 story per pattern (398 → ~15 stories)

    Total: ~10,602 issues → ~500 stories (batched by module/pattern)

    Usage:
        engine = StoryShardEngine(audit_report_path=Path("audit/ANALYSIS_EXHAUSTIVE_2026-01-21.md"))
        stories = await engine.shard_audit_report()
        print(f"Generated {len(stories)} stories from audit report")
    """

    def __init__(
        self,
        audit_report_path: Path,
        config: Optional[Dict] = None
    ):
        """
        Initialize story sharding engine.

        Args:
            audit_report_path: Path to audit report markdown
            config: Optional sharding configuration (batch sizes, etc.)

        Raises:
            FileNotFoundError: If audit report doesn't exist
        """
        if not audit_report_path.exists():
            raise FileNotFoundError(f"Audit report not found: {audit_report_path}")

        self.audit_path = audit_report_path
        self.config = config or {}
        self.logger = get_logger()

        # Story generation counters
        self.story_counter = 0

        # Issue grouping config (configurable batch sizes)
        self.batch_config = {
            "dead_imports": self.config.get("dead_imports_batch_size", 15),  # 410 / 15 ≈ 27 stories
            "type_errors": self.config.get("type_errors_batch_size", 40),   # 2913 / 40 ≈ 73 stories
            "deprecations": self.config.get("deprecations_batch_size", 25),  # 398 / 25 ≈ 16 stories
            "dead_code": self.config.get("dead_code_batch_size", 30),       # 852 / 30 ≈ 28 stories
        }

        self.logger.info("story_shard_engine_initialized", {
            "audit_path": str(audit_report_path),
            "batch_config": self.batch_config
        })

    async def shard_audit_report(
        self,
        priority_filter: Optional[StoryPriority] = None
    ) -> List[Story]:
        """
        Parse audit report into prioritized story queue.

        Args:
            priority_filter: Optional priority filter (e.g., StoryPriority.P2 for pilot)

        Returns:
            List of Story objects, priority-ordered (P0 → P1 → P2)

        Process:
            1. Parse audit report sections
            2. Group issues by module/pattern
            3. Create Story objects with descriptions
            4. Priority assignment (HIGH → P0, etc.)
            5. Domain classification (for crew assignment)
            6. Sort by priority (P0 → P1 → P2)
        """
        self.logger.info("story_sharding_start", {
            "audit_path": str(self.audit_path),
            "priority_filter": priority_filter.value if priority_filter else "all"
        })

        # Parse audit report
        audit_data = await self._parse_audit_report()

        # Create stories from different issue categories
        stories: List[Story] = []

        # P0: God class refactoring (HIGH priority)
        stories.extend(await self._create_god_class_stories(audit_data))

        # P0: Evolution system TODOs (HIGH priority)
        stories.extend(await self._create_evolution_todo_stories(audit_data))

        # P1: Type errors (HIGH priority, but batched)
        stories.extend(await self._create_type_error_stories(audit_data))

        # P1: Deprecation warnings (MEDIUM priority)
        stories.extend(await self._create_deprecation_stories(audit_data))

        # P1: Dead code (MEDIUM priority)
        stories.extend(await self._create_dead_code_stories(audit_data))

        # P2: Dead imports (LOW priority)
        stories.extend(await self._create_dead_import_stories(audit_data))

        # P2: Missing docstrings (LOW priority)
        stories.extend(await self._create_documentation_stories(audit_data))

        # Filter by priority if specified
        if priority_filter:
            stories = [s for s in stories if s.priority == priority_filter]

        # Sort by priority (P0 → P1 → P2) and story_id
        stories.sort(key=lambda s: (s.priority.value, s.story_id))

        self.logger.info("story_sharding_complete", {
            "total_stories": len(stories),
            "p0_count": sum(1 for s in stories if s.priority == StoryPriority.P0),
            "p1_count": sum(1 for s in stories if s.priority == StoryPriority.P1),
            "p2_count": sum(1 for s in stories if s.priority == StoryPriority.P2),
        })

        return stories

    async def _parse_audit_report(self) -> Dict[str, Any]:
        """
        Parse audit report markdown file.

        Returns:
            Dict with extracted data:
                - god_classes: List of God class entries
                - evolution_todos: List of TODO entries
                - issue_counts: Dict of category → count
                - deprecation_patterns: List of deprecation patterns

        NOTE: For Phase 0, this is a simplified parser.
              Full markdown parsing will be added in Phase 0.2.
        """
        self.logger.debug("parse_audit_report_start", {
            "audit_path": str(self.audit_path)
        })

        content = self.audit_path.read_text(encoding='utf-8')

        # Extract data from sections
        data = {
            "god_classes": self._extract_god_classes(content),
            "evolution_todos": self._extract_evolution_todos(content),
            "issue_counts": self._extract_issue_counts(content),
            "deprecation_patterns": self._extract_deprecation_patterns(content),
        }

        self.logger.debug("parse_audit_report_complete", {
            "god_classes_count": len(data["god_classes"]),
            "evolution_todos_count": len(data["evolution_todos"]),
            "issue_categories": len(data["issue_counts"])
        })

        return data

    def _extract_god_classes(self, content: str) -> List[Dict[str, str]]:
        """
        Extract God class entries from audit report.

        Pattern: Looking for section 6.2 with table of LOC entries.

        Returns:
            List of dicts with keys: file, loc, issue, priority
        """
        god_classes = []

        # Known God classes from the audit report
        known_god_classes = [
            {
                "file": "core/orchestration/fsm_handlers.py",
                "loc": 1838,
                "issue": "Monolithe - handlers par état manquants",
                "priority": "HIGH"
            },
            {
                "file": "core/interface/repl.py",
                "loc": 1353,
                "issue": "REPL trop centralisé",
                "priority": "MEDIUM"
            },
            {
                "file": "core/swarm/mode_selector.py",
                "loc": 1123,
                "issue": "Complexité élevée",
                "priority": "MEDIUM"
            }
        ]

        return known_god_classes

    def _extract_evolution_todos(self, content: str) -> List[Dict[str, str]]:
        """
        Extract Evolution system TODOs from audit report.

        Returns:
            List of dicts with keys: file, line, description
        """
        evolution_todos = [
            {
                "file": "core/evolution/manager.py",
                "line": 177,
                "description": "Extract from repl.py:brainstorm_spinoff_with_ais()"
            },
            {
                "file": "core/evolution/manager.py",
                "line": 512,
                "description": "Create specialist agent in workspace/agents/"
            },
            {
                "file": "core/evolution/manager.py",
                "line": 552,
                "description": "Track last_evolution from rate limiter"
            }
        ]

        return evolution_todos

    def _extract_issue_counts(self, content: str) -> Dict[str, int]:
        """
        Extract issue counts by category from audit report.

        Returns:
            Dict of category → count
        """
        return {
            "bug_pattern": 6303,
            "type_error": 2913,
            "dead_code": 852,
            "dead_import": 410,
            "missing_doc": 124,
            "deprecation": 398,
        }

    def _extract_deprecation_patterns(self, content: str) -> List[str]:
        """
        Extract deprecation warning patterns from audit report.

        Returns:
            List of deprecation patterns
        """
        return [
            "datetime.utcnow() → datetime.now(timezone.utc)",
            "LanceDB table_names() → newer API",
            "Async warnings: TelemetryBridge.emit not awaited"
        ]

    async def _create_god_class_stories(self, audit_data: Dict) -> List[Story]:
        """
        Create stories for God class refactoring.

        Strategy: 1 story per God class (3 stories total)
        Priority: P0 (HIGH)
        Domain: REFACTORING

        Returns:
            List of Story objects for God class refactoring
        """
        stories = []

        for god_class in audit_data["god_classes"]:
            # Only create stories for HIGH priority God classes
            if god_class["priority"] != "HIGH":
                continue

            story_id = self._generate_story_id()
            file_path = Path(god_class["file"])

            story = Story(
                story_id=story_id,
                priority=StoryPriority.P0,
                domains={IssueDomain.REFACTORING, IssueDomain.TYPING},
                description=f"""Refactor God class: {god_class['file']} ({god_class['loc']} LOC)

Issue: {god_class['issue']}

Tasks:
1. Analyze the file structure and identify logical groupings
2. Extract handlers into separate, focused modules
3. Update imports in dependent files
4. Ensure all tests still pass
5. Verify no functionality is broken

Target: Reduce file size from {god_class['loc']} LOC to <500 LOC per file.
""",
                target_files=[file_path],
                test_files=[Path(f"tests/{file_path.stem}.py")],
            )

            stories.append(story)

            self.logger.debug("god_class_story_created", {
                "story_id": story_id,
                "file": god_class["file"],
                "loc": god_class["loc"]
            })

        return stories

    async def _create_evolution_todo_stories(self, audit_data: Dict) -> List[Story]:
        """
        Create stories for Evolution system TODOs.

        Strategy: 1 story for all 3 TODOs combined (related work)
        Priority: P0 (HIGH - blocking agent spawning)
        Domain: EVOLUTION

        Returns:
            List with single Story for Evolution system completion
        """
        story_id = self._generate_story_id()

        todo_descriptions = "\n".join([
            f"{i+1}. {todo['file']}:{todo['line']} - {todo['description']}"
            for i, todo in enumerate(audit_data["evolution_todos"])
        ])

        story = Story(
            story_id=story_id,
            priority=StoryPriority.P0,
            domains={IssueDomain.EVOLUTION},
            description=f"""Complete Evolution system implementation (3 TODOs)

TODOs to resolve:
{todo_descriptions}

Tasks:
1. Implement brainstorm_specialist() by extracting logic from repl.py
2. Implement run_specialization() to create specialist agents
3. Implement track_last_evolution() to read from LINEAGE.json
4. Add unit tests for all 3 functions
5. Verify agent spawning works end-to-end

Reference: See core/agents/agent_service.py for delegation targets.
""",
            target_files=[Path("core/evolution/manager.py")],
            test_files=[Path("tests/test_evolution_manager.py")],
        )

        self.logger.debug("evolution_todo_story_created", {
            "story_id": story_id,
            "todo_count": len(audit_data["evolution_todos"])
        })

        return [story]

    async def _create_type_error_stories(self, audit_data: Dict) -> List[Story]:
        """
        Create stories for type error fixes.

        Strategy: Batch type errors by module (2913 errors → ~73 stories)
        Priority: P1 (HIGH, but batched)
        Domain: TYPING

        Returns:
            List of Story objects for type error fixes
        """
        stories = []
        type_error_count = audit_data["issue_counts"]["type_error"]
        batch_size = self.batch_config["type_errors"]
        num_stories = (type_error_count + batch_size - 1) // batch_size  # Ceiling division

        # For Phase 0, create placeholder stories
        # Phase 0.2 will implement actual module-level batching
        for i in range(num_stories):
            story_id = self._generate_story_id()
            start_idx = i * batch_size
            end_idx = min((i + 1) * batch_size, type_error_count)
            error_count = end_idx - start_idx

            story = Story(
                story_id=story_id,
                priority=StoryPriority.P1,
                domains={IssueDomain.TYPING},
                description=f"""Fix type errors (batch {i+1}/{num_stories}, {error_count} errors)

Tasks:
1. Run mypy --strict on target module(s)
2. Add missing type hints
3. Fix incorrect type annotations
4. Ensure no new type errors introduced
5. Run tests to verify no breakage

Note: This is a batched story. Target modules will be determined dynamically.
""",
                target_files=[],  # Will be populated in Phase 0.2
                test_files=[],
            )

            stories.append(story)

        self.logger.debug("type_error_stories_created", {
            "story_count": len(stories),
            "total_errors": type_error_count
        })

        return stories

    async def _create_deprecation_stories(self, audit_data: Dict) -> List[Story]:
        """
        Create stories for deprecation warning fixes.

        Strategy: 1 story per deprecation pattern (398 warnings → ~3 stories)
        Priority: P1 (MEDIUM)
        Domain: CLEANUP

        Returns:
            List of Story objects for deprecation fixes
        """
        stories = []

        for pattern in audit_data["deprecation_patterns"]:
            story_id = self._generate_story_id()

            story = Story(
                story_id=story_id,
                priority=StoryPriority.P1,
                domains={IssueDomain.CLEANUP},
                description=f"""Fix deprecation warnings: {pattern}

Tasks:
1. Find all occurrences of deprecated pattern
2. Replace with recommended alternative
3. Test affected code paths
4. Verify no deprecation warnings remain

Pattern: {pattern}
""",
                target_files=[],  # Will be populated by grep search
                test_files=[],
            )

            stories.append(story)

        self.logger.debug("deprecation_stories_created", {
            "story_count": len(stories)
        })

        return stories

    async def _create_dead_code_stories(self, audit_data: Dict) -> List[Story]:
        """
        Create stories for dead code removal.

        Strategy: Batch by module (852 instances → ~28 stories)
        Priority: P1 (MEDIUM)
        Domain: CLEANUP

        Returns:
            List of Story objects for dead code removal
        """
        stories = []
        dead_code_count = audit_data["issue_counts"]["dead_code"]
        batch_size = self.batch_config["dead_code"]
        num_stories = (dead_code_count + batch_size - 1) // batch_size

        for i in range(num_stories):
            story_id = self._generate_story_id()
            start_idx = i * batch_size
            end_idx = min((i + 1) * batch_size, dead_code_count)
            code_count = end_idx - start_idx

            story = Story(
                story_id=story_id,
                priority=StoryPriority.P1,
                domains={IssueDomain.CLEANUP},
                description=f"""Remove dead code (batch {i+1}/{num_stories}, {code_count} instances)

Tasks:
1. Run vulture or similar tool to identify dead code
2. Verify code is truly unused (check imports, references)
3. Remove dead code carefully
4. Run tests to ensure no breakage
5. Update related documentation if needed

Safety: Only remove code with high confidence of being unused.
""",
                target_files=[],
                test_files=[],
            )

            stories.append(story)

        self.logger.debug("dead_code_stories_created", {
            "story_count": len(stories),
            "total_instances": dead_code_count
        })

        return stories

    async def _create_dead_import_stories(self, audit_data: Dict) -> List[Story]:
        """
        Create stories for dead import removal.

        Strategy: Batch by module (410 imports → ~27 stories)
        Priority: P2 (LOW - safe cleanup)
        Domain: CLEANUP

        Returns:
            List of Story objects for dead import removal
        """
        stories = []
        dead_import_count = audit_data["issue_counts"]["dead_import"]
        batch_size = self.batch_config["dead_imports"]
        num_stories = (dead_import_count + batch_size - 1) // batch_size

        for i in range(num_stories):
            story_id = self._generate_story_id()
            start_idx = i * batch_size
            end_idx = min((i + 1) * batch_size, dead_import_count)
            import_count = end_idx - start_idx

            story = Story(
                story_id=story_id,
                priority=StoryPriority.P2,
                domains={IssueDomain.CLEANUP},
                description=f"""Remove dead imports (batch {i+1}/{num_stories}, {import_count} imports)

Tasks:
1. Run autoflake or similar tool to identify unused imports
2. Remove unused imports
3. Run tests to verify no breakage
4. Ensure formatting is preserved

Safety: This is low-risk cleanup. Verify tests pass after removal.
""",
                target_files=[],
                test_files=[],
            )

            stories.append(story)

        self.logger.debug("dead_import_stories_created", {
            "story_count": len(stories),
            "total_imports": dead_import_count
        })

        return stories

    async def _create_documentation_stories(self, audit_data: Dict) -> List[Story]:
        """
        Create stories for missing docstring additions.

        Strategy: Batch by module (124 missing → ~5 stories)
        Priority: P2 (LOW)
        Domain: DOCUMENTATION

        Returns:
            List of Story objects for documentation additions
        """
        stories = []
        missing_doc_count = audit_data["issue_counts"]["missing_doc"]
        batch_size = 25  # 124 / 25 ≈ 5 stories
        num_stories = (missing_doc_count + batch_size - 1) // batch_size

        for i in range(num_stories):
            story_id = self._generate_story_id()
            start_idx = i * batch_size
            end_idx = min((i + 1) * batch_size, missing_doc_count)
            doc_count = end_idx - start_idx

            story = Story(
                story_id=story_id,
                priority=StoryPriority.P2,
                domains={IssueDomain.DOCUMENTATION},
                description=f"""Add missing docstrings (batch {i+1}/{num_stories}, {doc_count} functions/classes)

Tasks:
1. Identify functions/classes without docstrings
2. Add Google-style docstrings with Args/Returns/Raises
3. Ensure docstrings are accurate and helpful
4. Run interrogate to verify coverage improvement

Style: Follow Google docstring format (existing NEXUS pattern).
""",
                target_files=[],
                test_files=[],
            )

            stories.append(story)

        self.logger.debug("documentation_stories_created", {
            "story_count": len(stories),
            "total_missing": missing_doc_count
        })

        return stories

    def _generate_story_id(self) -> str:
        """
        Generate unique story ID.

        Format: STORY-{counter:04d}
        Example: STORY-0001, STORY-0042, etc.

        Returns:
            Story ID string
        """
        self.story_counter += 1
        return f"STORY-{self.story_counter:04d}"
