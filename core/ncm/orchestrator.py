"""
NCM Orchestrator - Story Queue Coordinator

This is a CLIENT of OrchestratorV7, not a replacement. For each story, it invokes
orchestrator.process_turn(story.description) and leverages all existing NEXUS
capabilities (FSM, HiveMind, Swarm, RAG, Evolution).

Architecture:
    ┌─────────────────────────────────────────┐
    │  NCMOrchestrator (THIS FILE)            │
    │  - Story queue management               │
    │  - Crew assignment                      │
    │  - Progress tracking                    │
    │  - Token budget monitoring              │
    │  - State snapshot every 100 stories     │
    └─────────────────────────────────────────┘
                    ↓ process_turn()
    ┌─────────────────────────────────────────┐
    │  OrchestratorV7 (EXISTING)              │
    │  - FSM (12 states)                      │
    │  - HiveMind (7 phases)                  │
    │  - Swarm (6 modes)                      │
    │  - RAG, Evolution, Security             │
    └─────────────────────────────────────────┘

Responsibilities:
    - Story queue management (priority order)
    - Crew assignment (which agents for which story)
    - Progress tracking (stories completed/failed)
    - Token budget monitoring (blind spot #5 mitigation)
    - State snapshot every 100 stories (blind spot #6 mitigation)

NOT responsible for:
    - Low-level agent coordination (OrchestratorV7 handles this)
    - Tool execution (OrchestratorV7 → HiveMind → Swarm)
    - Fault tolerance (inherited from OrchestratorV7)
"""

from pathlib import Path
from typing import List, Dict, Optional, Any
from datetime import datetime
import asyncio
import time
import json
import re
import importlib.util

from core.ncm.models import (
    Story,
    StoryStatus,
    StoryPriority,
    CrewAssignment,
    ValidationResult,
    ExecutionMetrics,
    StateSnapshot,
    NCMConfig,
)
from core.ncm.simple_executor import SimpleExecutor
from core.logging import get_logger


class NCMOrchestrator:
    """
    NCM story queue coordinator (CLIENT of OrchestratorV7).

    This orchestrator manages the high-level story execution workflow while
    delegating all low-level coordination to the existing OrchestratorV7.

    Lifecycle:
        1. Initialize with OrchestratorV7 instance (singleton)
        2. Load story queue from audit report
        3. Execute stories in priority order (P0 → P1 → P2)
        4. Track metrics and take snapshots
        5. Generate completion reports

    Usage:
        from core.ncm import NCMOrchestrator, NCMConfig
        from core.orchestration_v7 import OrchestratorV7

        orch = OrchestratorV7(workspace_path, config, gemini_info, claude_info)
        ncm_config = NCMConfig(story_batch_size=50, token_limit=100_000_000)
        ncm = NCMOrchestrator(orchestrator=orch, workspace_path=Path("workspace"), config=ncm_config)

        # Execute pilot
        await ncm.execute_batch(story_count=100, priority="P2")

        # Check metrics
        metrics = ncm.get_metrics()
        print(f"Success rate: {metrics.success_rate:.2%}")
    """

    def __init__(
        self,
        orchestrator: "OrchestratorV7",
        workspace_path: Path,
        config: NCMConfig
    ):
        """
        Initialize NCM orchestrator.

        Args:
            orchestrator: Existing OrchestratorV7 instance (singleton)
            workspace_path: NEXUS workspace root (e.g., Path("workspace"))
            config: NCM configuration (story batch size, token limits, etc.)

        Raises:
            ValueError: If orchestrator is None or workspace_path doesn't exist
        """
        if orchestrator is None:
            raise ValueError("orchestrator cannot be None")
        if not workspace_path.exists():
            raise ValueError(f"workspace_path does not exist: {workspace_path}")

        self.orchestrator = orchestrator
        self.workspace_path = workspace_path
        self.config = config
        self.logger = get_logger()
        self.repo_root = self._detect_repo_root(workspace_path)

        # NCM workspace paths
        self.ncm_workspace = workspace_path / "ncm"
        self.ncm_workspace.mkdir(exist_ok=True)
        (self.ncm_workspace / "logs").mkdir(exist_ok=True)
        (self.ncm_workspace / "metrics").mkdir(exist_ok=True)
        (self.ncm_workspace / "snapshots").mkdir(exist_ok=True)

        # Story queue (priority-ordered)
        self.story_queue: List[Story] = []
        self.completed: List[Story] = []
        self.failed: List[Story] = []
        self.partial: List[Story] = []

        # Current execution state
        self.current_story: Optional[Story] = None
        self.current_phase: str = "idle"  # idle, pilot, 2A, 2B, 3A, 3B

        # Crew assignments (story_id → CrewAssignment)
        self.assignments: Dict[str, CrewAssignment] = {}

        # Token budget tracking (blind spot #5 mitigation)
        self.tokens_used = 0
        self.token_limit = config.token_limit

        # Prompt refresh counter (blind spot #3 mitigation)
        self.tool_calls_since_refresh = 0
        self.refresh_interval = config.refresh_interval

        # Execution metrics
        self.metrics_history: List[ExecutionMetrics] = []
        self.current_metrics: Optional[ExecutionMetrics] = None

        # State snapshots (blind spot #6 mitigation)
        self.snapshots: List[StateSnapshot] = []
        self.last_snapshot_count = 0

        # Simple executor for P2 stories (bypasses OrchestratorV7 for simple tasks)
        self.simple_executor = SimpleExecutor()
        self.use_simple_executor = True  # Flag to enable/disable simple execution

        self.logger.info("ncm_orchestrator_initialized", {
            "workspace": str(workspace_path),
            "story_batch_size": config.story_batch_size,
            "token_limit": config.token_limit,
            "refresh_interval": config.refresh_interval,
            "use_simple_executor": self.use_simple_executor
        })

    def _detect_repo_root(self, workspace_path: Path) -> Path:
        """
        Resolve repository root for relative path normalization.
        """
        candidates = [
            workspace_path,
            workspace_path.parent,
            workspace_path.parent.parent,
        ]
        for candidate in candidates:
            if (candidate / "core").exists():
                return candidate
        return workspace_path

    async def load_story_queue(
        self,
        stories: List[Story],
        priority_filter: Optional[StoryPriority] = None
    ) -> int:
        """
        Load story queue from list of stories.

        Args:
            stories: List of Story objects (from StoryShardEngine)
            priority_filter: Optional priority filter (e.g., StoryPriority.P2 for pilot)

        Returns:
            Number of stories loaded

        Process:
            1. Filter by priority if specified
            2. Sort by priority (P0 → P1 → P2) and story_id
            3. Reset execution state
            4. Log loaded count
        """
        self.logger.info("ncm_load_story_queue_start", {
            "total_stories": len(stories),
            "priority_filter": priority_filter.value if priority_filter else "all"
        })

        # Filter by priority
        if priority_filter:
            stories = [s for s in stories if s.priority == priority_filter]

        # Sort by priority and story_id
        stories.sort(key=lambda s: (s.priority.value, s.story_id))

        # Reset state
        self.story_queue = stories
        self.completed = []
        self.failed = []
        self.partial = []
        self.assignments = {}
        self.current_story = None

        self.logger.info("ncm_load_story_queue_complete", {
            "stories_loaded": len(self.story_queue)
        })

        return len(self.story_queue)

    async def execute_batch(
        self,
        story_count: Optional[int] = None,
        priority: Optional[str] = None
    ) -> ExecutionMetrics:
        """
        Execute a batch of stories from the queue.

        Args:
            story_count: Number of stories to execute (None = all)
            priority: Priority filter (P0/P1/P2)

        Returns:
            ExecutionMetrics with results

        Process:
            1. Initialize batch metrics
            2. Execute stories one by one (or in parallel if config.parallel_execution)
            3. Track progress and update metrics
            4. Take snapshots every config.snapshot_interval stories
            5. Check token budget and prompt refresh
            6. Return final metrics

        Example:
            # Pilot: Execute 100 P2 stories
            metrics = await ncm.execute_batch(story_count=100, priority="P2")

            # Phase 2A: Execute all P2 stories
            metrics = await ncm.execute_batch(priority="P2")

            # Phase 3B: Execute all remaining
            metrics = await ncm.execute_batch()
        """
        phase_name = priority or "all"
        batch_size = story_count or len(self.story_queue)

        self.logger.info("ncm_execute_batch_start", {
            "phase": phase_name,
            "batch_size": batch_size,
            "queue_size": len(self.story_queue)
        })

        # Initialize metrics
        self.current_metrics = ExecutionMetrics(
            phase=phase_name,
            stories_total=batch_size,
            started_at=datetime.now()
        )

        start_time = time.time()
        stories_to_execute = self.story_queue[:batch_size]

        # Execute stories
        for i, story in enumerate(stories_to_execute):
            self.logger.info("ncm_story_start", {
                "story_id": story.story_id,
                "progress": f"{i+1}/{batch_size}",
                "priority": story.priority.value
            })

            # Execute story
            status = await self.execute_story(story)

            # Update metrics
            if status == StoryStatus.SUCCESS:
                self.completed.append(story)
                self.current_metrics.stories_completed += 1
            elif status == StoryStatus.FAILED:
                self.failed.append(story)
                self.current_metrics.stories_failed += 1
            elif status == StoryStatus.PARTIAL:
                self.partial.append(story)
                self.current_metrics.stories_partial += 1

            # Update success rate
            total_processed = self.current_metrics.stories_completed + self.current_metrics.stories_failed + self.current_metrics.stories_partial
            if total_processed > 0:
                self.current_metrics.success_rate = self.current_metrics.stories_completed / total_processed

            # Remove from queue
            self.story_queue.remove(story)

            # Snapshot check (every config.snapshot_interval stories)
            if (i + 1) % self.config.snapshot_interval == 0:
                await self._take_state_snapshot()

            # Log progress
            if (i + 1) % 10 == 0:
                self.logger.info("ncm_batch_progress", {
                    "progress": f"{i+1}/{batch_size}",
                    "success_rate": f"{self.current_metrics.success_rate:.2%}",
                    "tokens_used": self.tokens_used
                })

        # Finalize metrics
        duration = time.time() - start_time
        self.current_metrics.completed_at = datetime.now()
        self.current_metrics.duration_hours = duration / 3600
        if batch_size > 0 and duration > 0:
            self.current_metrics.stories_per_hour = batch_size / (duration / 3600)
        if batch_size > 0:
            self.current_metrics.avg_tokens_per_story = self.tokens_used / batch_size

        # Save metrics
        self.metrics_history.append(self.current_metrics)
        await self._save_metrics()

        self.logger.info("ncm_execute_batch_complete", {
            "phase": phase_name,
            "completed": self.current_metrics.stories_completed,
            "failed": self.current_metrics.stories_failed,
            "partial": self.current_metrics.stories_partial,
            "success_rate": f"{self.current_metrics.success_rate:.2%}",
            "duration_hours": f"{self.current_metrics.duration_hours:.2f}",
            "stories_per_hour": f"{self.current_metrics.stories_per_hour:.1f}"
        })

        return self.current_metrics

    async def execute_story(self, story: Story) -> StoryStatus:
        """
        Execute a single story by invoking OrchestratorV7.

        Args:
            story: Story to execute (with description, priority, assigned agents)

        Returns:
            StoryStatus (SUCCESS/FAILED/PARTIAL)

        Process:
            1. Mark story as IN_PROGRESS
            2. Invoke orchestrator.process_turn(story.description)
            3. Validate results (syntax, types, tests)
            4. Update story status
            5. Check prompt refresh (every 500 tool calls)
            6. Return status

        Delegation:
            - OrchestratorV7 handles all low-level coordination
            - HiveMind handles 7-phase execution
            - Swarm handles agent collaboration
            - No NCM-specific coordination needed
        """
        self.logger.info("ncm_story_execution_start", {
            "story_id": story.story_id,
            "priority": story.priority.value,
            "domains": [d.value for d in story.domains]
        })

        # Mark story as in progress
        story.status = StoryStatus.IN_PROGRESS
        story.started_at = datetime.now()
        self.current_story = story

        try:
            # Check if we can use SimpleExecutor for this story
            if self.use_simple_executor and self._can_execute_simply(story):
                self.logger.info("ncm_using_simple_executor", {
                    "story_id": story.story_id,
                    "description": story.description[:100]
                })

                # Execute with SimpleExecutor (fast, direct)
                success, error = await self._execute_story_simple(story)

                if success:
                    story.status = StoryStatus.SUCCESS
                    story.completed_at = datetime.now()
                    return StoryStatus.SUCCESS
                else:
                    # Simple execution failed, try OrchestratorV7 as fallback
                    self.logger.warning("ncm_simple_executor_failed_fallback", {
                        "story_id": story.story_id,
                        "error": error
                    })
                    # Continue to OrchestratorV7 below

            # Simplify story description for OrchestratorV7
            # Extract the first line (main task) to avoid complexity analysis issues
            simplified_task = self._simplify_story_description(story)

            self.logger.debug("ncm_simplified_task", {
                "story_id": story.story_id,
                "original_length": len(story.description),
                "simplified": simplified_task
            })

            # Invoke OrchestratorV7 (THIS IS WHERE NEXUS DOES THE WORK)
            # NCM just provides the task description and lets NEXUS orchestrate
            # NOTE: process_turn() is synchronous (not async), returns dict directly
            result = self.orchestrator.process_turn(
                user_input=simplified_task,
                # context can be used to pass NCM-specific metadata
            )

            # Track tokens used (if available in result)
            if isinstance(result, dict) and "tokens_used" in result:
                story.tokens_used = result["tokens_used"]
                self.tokens_used += story.tokens_used

            # Track tool calls for prompt refresh
            if isinstance(result, dict) and "tool_calls_count" in result:
                self.tool_calls_since_refresh += result["tool_calls_count"]

            # Validate results (blind spot #7 mitigation)
            validation = await self._validate_story_result(story)

            # Update story status based on validation
            if validation.passed:
                story.status = StoryStatus.SUCCESS
            elif validation.syntax_valid and validation.imports_valid:
                # Partial success (syntax/imports OK but tests failed)
                story.status = StoryStatus.PARTIAL
            else:
                story.status = StoryStatus.FAILED
                story.error_message = "; ".join(validation.errors)

            story.completed_at = datetime.now()

            # Check prompt refresh (blind spot #3 mitigation)
            if self.tool_calls_since_refresh >= self.refresh_interval:
                await self._refresh_prompts()

            self.logger.info("ncm_story_execution_complete", {
                "story_id": story.story_id,
                "status": story.status.value,
                "tokens_used": story.tokens_used,
                "validation_passed": validation.passed
            })

            return story.status

        except Exception as e:
            self.logger.error("ncm_story_execution_failed", {
                "story_id": story.story_id,
                "error": str(e)
            })
            story.status = StoryStatus.FAILED
            story.error_message = str(e)
            story.completed_at = datetime.now()
            return StoryStatus.FAILED

    def _can_execute_simply(self, story: Story) -> bool:
        """
        Determine if story can be executed with SimpleExecutor.

        Args:
            story: Story to check

        Returns:
            True if SimpleExecutor can handle this story

        Criteria for simple execution:
            - Priority P2 (low risk) - ALL P2 stories
            - Avoids process_turn() hang issue with collaborative modes

        Note: For NCM pilot, we use SimpleExecutor for ALL P2 stories to avoid
              the Windows subprocess hang issue where Claude CLI waits for Gemini
              in collaborative modes but the FSM cycle doesn't complete cleanly.
        """
        # For pilot: ALL P2 stories use SimpleExecutor
        # This avoids the collaborative mode hang issue
        if story.priority == StoryPriority.P2:
            # For now, only handle simple patterns
            # TODO: Expand SimpleExecutor for more patterns
            desc_lower = story.description.lower()
            supported_patterns = [
                "dead import",
                "unused import",
                "docstring",
                "add missing doc",
                "type hint",
                "deprecation",
                "deprecated"
            ]

            if not any(pattern in desc_lower for pattern in supported_patterns):
                return False

            target_files = self._get_existing_target_files(story)
            if len(target_files) != 1:
                return False

            return True

        return False

    def _get_story_target_files(self, story: Story) -> List[Path]:
        """
        Resolve target files from story or infer from description.
        """
        if story.target_files:
            return self._dedupe_paths(story.target_files)

        inferred = self._infer_target_files_from_description(story.description)
        if inferred:
            story.target_files = self._dedupe_paths(inferred)

        return story.target_files

    def _get_existing_target_files(self, story: Story) -> List[Path]:
        """
        Resolve story target files to existing paths on disk.
        """
        targets = self._get_story_target_files(story)
        resolved = []
        for path in targets:
            resolved_path = self._resolve_existing_path(path)
            if resolved_path:
                resolved.append(resolved_path)
        return self._dedupe_paths(resolved)

    def _infer_target_files_from_description(self, description: str) -> List[Path]:
        """
        Infer target files from a story description.
        """
        pattern = re.compile(
            r"(?i)\b(?:in|from|at)\s+"
            r"([A-Za-z]:\\[^\s:]+?\.[A-Za-z0-9_]+|"
            r"[\w./\\-]+\.[A-Za-z0-9_]+)"
        )
        matches = pattern.findall(description)
        paths = []
        for match in matches:
            cleaned = match.rstrip(").,;")
            paths.append(Path(cleaned))
        return paths

    def _resolve_existing_path(self, path: Path) -> Optional[Path]:
        """
        Resolve a path to an existing file if possible.
        """
        if path.is_absolute():
            return path if path.exists() else None

        candidates = [
            path,
            self.repo_root / path,
            self.workspace_path / path,
        ]
        for candidate in candidates:
            if candidate.exists():
                return candidate
        return None

    def _dedupe_paths(self, paths: List[Path]) -> List[Path]:
        """
        Deduplicate paths while preserving order.
        """
        seen = set()
        deduped = []
        for path in paths:
            key = str(path)
            if key in seen:
                continue
            seen.add(key)
            deduped.append(path)
        return deduped

    async def _execute_story_simple(self, story: Story) -> tuple[bool, Optional[str]]:
        """
        Execute story using SimpleExecutor (direct, no OrchestratorV7).

        Args:
            story: Story to execute

        Returns:
            (success: bool, error_message: Optional[str])

        Process:
            1. Detect story type (dead import, docstring, type hint, deprecation)
            2. Dispatch to appropriate SimpleExecutor method
            3. Validate syntax
        4. Run tests

        Note: This bypasses OrchestratorV7 entirely for speed.
        """
        desc_lower = story.description.lower()
        target_files = self._get_existing_target_files(story)
        if not target_files:
            return False, "No resolvable target file for SimpleExecutor"
        if len(target_files) > 1:
            return False, "SimpleExecutor only supports single-file stories"

        target_file = target_files[0]
        success = False
        error = None

        # Dispatch based on story type
        if "dead import" in desc_lower or "unused import" in desc_lower:
            # Extract import names from description
            import_names = []
            for line in story.description.split('\n'):
                if "Import '" in line and "may be unused" in line:
                    parts = line.split("'")
                    if len(parts) >= 2:
                        import_names.append(parts[1])

            if not import_names:
                match = re.search(
                    r"remove\s+(?:dead|unused)\s+import\s+'([^']+)'",
                    story.description,
                    flags=re.IGNORECASE
                )
                if match:
                    import_names.append(match.group(1))

            if not import_names:
                return False, "Could not extract import names from description"

            success, error = await self.simple_executor.execute_dead_import_removal(
                target_file,
                import_names
            )

        elif "docstring" in desc_lower or "add missing doc" in desc_lower:
            # Extract target function/class name
            # Pattern: "Add docstring to function 'function_name'"
            match = re.search(r"(function|class)\s+'([^']+)'", story.description)
            if not match:
                match = re.search(
                    r"docstring\s+to\s+(function|class)\s+([A-Za-z_][A-Za-z0-9_]*)",
                    story.description,
                    flags=re.IGNORECASE
                )
            if not match:
                return False, "Could not extract target name from description"

            target_type = match.group(1)  # "function" or "class"
            target_name = match.group(2)

            success, error = await self.simple_executor.execute_docstring_addition(
                target_file,
                target_name,
                target_type
            )

        elif "type hint" in desc_lower:
            # Extract function name, parameter, and type hint
            # Pattern: "Add type hint 'str' to parameter 'param_name' in function 'function_name'"
            match = re.search(
                r"type hint\s+'([^']+)'\s+to parameter\s+'([^']+)'\s+in function\s+'([^']+)'",
                story.description
            )
            if not match:
                match = re.search(
                    r"type hint\s+'([^']+)'\s+to parameter\s+([A-Za-z_][A-Za-z0-9_]*)\s+"
                    r"in function\s+([A-Za-z_][A-Za-z0-9_]*)",
                    story.description,
                    flags=re.IGNORECASE
                )
            if not match:
                return False, "Could not extract type hint info from description"

            type_hint = match.group(1)
            param_name = match.group(2)
            function_name = match.group(3)

            success, error = await self.simple_executor.execute_type_hint_addition(
                target_file,
                function_name,
                param_name,
                type_hint
            )

        elif "deprecation" in desc_lower:
            # Extract deprecated pattern and replacement
            # Pattern: "Fix deprecation: replace 'old_pattern' with 'new_pattern'"
            match = re.search(r"replace\s+'([^']+)'\s+with\s+'([^']+)'", story.description)
            if not match:
                match = re.search(
                    r"([A-Za-z0-9_().]+)\s*->\s*([A-Za-z0-9_().]+)",
                    story.description
                )
            if not match:
                return False, "Could not extract deprecation info from description"

            deprecated_pattern = match.group(1)
            replacement = match.group(2)

            success, error = await self.simple_executor.execute_deprecation_fix(
                target_file,
                deprecated_pattern,
                replacement
            )

        else:
            return False, f"Unknown story type: {story.description[:100]}"

        if not success:
            return False, error

        # Run tests
        test_success, test_error = await self.simple_executor.run_tests(story.test_files)
        if not test_success:
            return False, test_error

        return True, None

    def _simplify_story_description(self, story: Story) -> str:
        """
        Simplify verbose story description into concise, actionable instruction.

        Args:
            story: Story with potentially verbose description

        Returns:
            Simplified task description for OrchestratorV7

        Purpose:
            Story descriptions are detailed (issues, tasks, safety notes) for human review,
            but OrchestratorV7's task analyzer classifies them as EXPERT complexity,
            triggering unnecessary Hive Mind routing and timeouts.

            This method extracts the core action and target files into a simple instruction.

        Examples:
            Before: "Remove dead imports from core/auth.py (3 imports)\n\nIssues:\n- Line 10: ..."
            After: "Remove unused imports from core/auth.py: 'Set', 'Dict', 'Optional'"

            Before: "Add missing type hints to core/utils.py (5 items)\n\nType errors:\n- Line 42: ..."
            After: "Add type hints to functions in core/utils.py"
        """
        # Extract first line (main task)
        first_line = story.description.split('\n')[0]

        # Add target file explicitly (in case it's not clear)
        target_files = self._get_story_target_files(story)
        target_files_str = ", ".join([f.name for f in target_files])
        target_file = target_files[0] if target_files else None

        # Build simplified instruction based on category pattern
        if "dead import" in first_line.lower() or "unused import" in first_line.lower():
            # Extract import names from Issues section if available
            import_names = []
            for line in story.description.split('\n'):
                if "Import '" in line and "may be unused" in line:
                    # Extract import name from "Import 'Set' from 'typing' may be unused"
                    parts = line.split("'")
                    if len(parts) >= 2:
                        import_names.append(parts[1])

            if import_names:
                imports_str = ", ".join([f"'{name}'" for name in import_names])
                if target_file:
                    return f"Remove unused imports from {target_file}: {imports_str}"
                return f"Remove unused imports: {imports_str}"
            if target_file:
                return f"Remove unused imports from {target_file}"
            return "Remove unused imports"

        elif "type hint" in first_line.lower() or "type error" in first_line.lower():
            if target_file:
                return f"Add missing type hints to {target_file}"
            return "Add missing type hints"

        elif "docstring" in first_line.lower() or "missing doc" in first_line.lower():
            if target_file:
                return f"Add missing docstrings to {target_file}"
            return "Add missing docstrings"

        elif "dead code" in first_line.lower() or "unused" in first_line.lower():
            if target_file:
                return f"Remove unused code from {target_file}"
            return "Remove unused code"

        elif "deprecation" in first_line.lower() or "deprecated" in first_line.lower():
            if target_file:
                return f"Fix deprecation warnings in {target_file}"
            return "Fix deprecation warnings"

        else:
            # Fallback: Use first line + target file
            if target_files_str:
                return f"{first_line} (target: {target_files_str})"
            return first_line

    async def _validate_story_result(self, story: Story) -> ValidationResult:
        """
        Validate story execution results (Blind Spot #7 mitigation).

        Args:
            story: Story to validate

        Returns:
            ValidationResult with validation details

        Validation phases:
            1. Syntax check (Python ast.parse on modified files)
            2. Import check (no circular imports)
            3. Type check (mypy --strict on modified files)
            4. Unit tests (pytest on test_files)
            5. Integration tests (if P0 story, run full suite)

        NOTE: For Phase 0 implementation, we do basic validation.
              Full validation (mypy, pytest) will be added in Phase 0.3.
        """
        self.logger.debug("ncm_validate_story_start", {
            "story_id": story.story_id,
            "target_files": [str(f) for f in story.target_files]
        })

        result = ValidationResult(
            story_id=story.story_id,
            passed=False
        )

        try:
            # Phase 1: Syntax check
            result.syntax_valid = await self._check_syntax(story.target_files)

            # Phase 2: Import check
            result.imports_valid, import_errors = await self._check_imports(story.target_files)
            if import_errors:
                result.errors.extend(import_errors)

            # Phase 3: Type check (Phase 0.2)
            result.types_valid, type_errors, type_warnings = await self._check_types(story.target_files)
            if type_errors:
                result.errors.extend(type_errors)
            if type_warnings:
                result.warnings.extend(type_warnings)

            # Phase 4: Tests (Phase 2A - Real implementation)
            result.tests_passed = await self._run_tests(story.test_files)

            # Overall pass if all phases pass
            result.passed = (
                result.syntax_valid and
                result.imports_valid and
                result.types_valid and
                result.tests_passed
            )

            self.logger.debug("ncm_validate_story_complete", {
                "story_id": story.story_id,
                "passed": result.passed,
                "syntax": result.syntax_valid,
                "imports": result.imports_valid
            })

        except Exception as e:
            self.logger.error("ncm_validate_story_error", {
                "story_id": story.story_id,
                "error": str(e)
            })
            result.errors.append(str(e))

        return result

    async def _check_syntax(self, files: List[Path]) -> bool:
        """
        Check Python syntax for modified files.

        Args:
            files: List of file paths to check

        Returns:
            True if all files have valid syntax, False otherwise
        """
        import ast

        for file_path in files:
            if not file_path.exists():
                self.logger.warning("ncm_syntax_check_file_not_found", {
                    "file": str(file_path)
                })
                continue

            try:
                content = file_path.read_text()
                ast.parse(content)
            except SyntaxError as e:
                self.logger.error("ncm_syntax_check_failed", {
                    "file": str(file_path),
                    "error": str(e)
                })
                return False

        return True

    async def _check_imports(self, files: List[Path]) -> tuple[bool, List[str]]:
        """
        Check for circular imports.

        Args:
            files: List of file paths to check

        Returns:
            True if no circular imports, False otherwise

        NOTE: Basic implementation for Phase 0.
              Full circular import detection will be added in Phase 0.3.
        """
        import ast

        resolved_files = []
        for file_path in files:
            resolved = self._resolve_existing_path(file_path)
            if resolved and resolved.suffix == ".py":
                resolved_files.append(resolved)

        if len(resolved_files) < 2:
            return True, []

        module_map = {}
        for file_path in resolved_files:
            module_name = self._module_name_from_path(file_path)
            if module_name:
                module_map[module_name] = file_path

        if len(module_map) < 2:
            return True, []

        graph: Dict[str, List[str]] = {module: [] for module in module_map}

        for module_name, file_path in module_map.items():
            try:
                content = file_path.read_text(encoding="utf-8")
                tree = ast.parse(content)
            except Exception as e:
                self.logger.warning("ncm_import_check_parse_failed", {
                    "file": str(file_path),
                    "error": str(e)
                })
                continue

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imported = alias.name
                        if imported in module_map:
                            graph[module_name].append(imported)
                elif isinstance(node, ast.ImportFrom):
                    imported = self._resolve_import_from_module(module_name, node.module, node.level)
                    if imported and imported in module_map:
                        graph[module_name].append(imported)

        cycles = self._detect_import_cycles(graph)
        if not cycles:
            return True, []

        errors = []
        for cycle in cycles:
            cycle_paths = [str(module_map.get(module, module)) for module in cycle]
            errors.append(f"Circular import detected: {' -> '.join(cycle_paths)}")

        self.logger.error("ncm_circular_imports_detected", {
            "cycles": errors
        })

        return False, errors

    def _module_name_from_path(self, file_path: Path) -> Optional[str]:
        """
        Convert a file path to a module name relative to repo root.
        """
        try:
            relative = file_path.resolve().relative_to(self.repo_root.resolve())
        except Exception:
            relative = file_path

        if relative.name == "__init__.py":
            parts = relative.parts[:-1]
        else:
            parts = relative.with_suffix("").parts

        if not parts:
            return None

        return ".".join(parts)

    def _resolve_import_from_module(
        self,
        current_module: str,
        imported_module: Optional[str],
        level: int
    ) -> Optional[str]:
        """
        Resolve an ast.ImportFrom module to an absolute module name.
        """
        if level == 0:
            return imported_module

        if not current_module:
            return imported_module

        current_parts = current_module.split(".")
        if level > len(current_parts):
            base_parts = []
        else:
            base_parts = current_parts[:-level]

        if imported_module:
            base_parts.extend(imported_module.split("."))

        if not base_parts:
            return None

        return ".".join(base_parts)

    def _detect_import_cycles(self, graph: Dict[str, List[str]]) -> List[List[str]]:
        """
        Detect cycles in an import graph.
        """
        cycles: List[List[str]] = []
        visiting: set[str] = set()
        visited: set[str] = set()
        stack: List[str] = []

        def dfs(node: str):
            visiting.add(node)
            stack.append(node)

            for neighbor in graph.get(node, []):
                if neighbor in visiting:
                    if neighbor in stack:
                        start_index = stack.index(neighbor)
                        cycle = stack[start_index:] + [neighbor]
                        if cycle not in cycles:
                            cycles.append(cycle)
                    continue
                if neighbor not in visited:
                    dfs(neighbor)

            visiting.remove(node)
            stack.pop()
            visited.add(node)

        for node in graph:
            if node not in visited:
                dfs(node)

        return cycles

    async def _check_types(self, files: List[Path]) -> tuple[bool, List[str], List[str]]:
        """
        Run type checking on target files using mypy (strict).

        Returns:
            (types_valid, errors, warnings)
        """
        import subprocess

        resolved_files = []
        for file_path in files:
            resolved = self._resolve_existing_path(file_path)
            if resolved and resolved.suffix == ".py":
                resolved_files.append(resolved)

        if not resolved_files:
            return True, [], []

        if importlib.util.find_spec("mypy") is None:
            message = "Type check skipped: mypy not installed"
            self.logger.warning("ncm_type_check_skipped", {
                "reason": message
            })
            if self.config.validation_mode == "strict":
                return False, [message], []
            return True, [], [message]

        command = [
            "python",
            "-m",
            "mypy",
            "--strict",
            "--show-error-codes",
        ] + [str(path) for path in resolved_files]

        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=300,
                cwd=str(self.repo_root)
            )
        except subprocess.TimeoutExpired:
            return False, ["Type check timed out"], []
        except Exception as e:
            return False, [f"Type check error: {e}"], []

        if result.returncode == 0:
            return True, [], []

        output = (result.stdout + "\n" + result.stderr).strip()
        if len(output) > 2000:
            output = output[:1500] + "\n...[truncated]...\n" + output[-400:]

        return False, [f"Type check failed:\n{output}"], []

    async def _run_tests(self, test_files: List[Path]) -> bool:
        """
        Run pytest on test files (Phase 2A implementation).

        Args:
            test_files: List of test file paths to run

        Returns:
            True if all tests pass, False otherwise

        Process:
            1. Skip if no test files specified
            2. Run pytest for each test file
            3. Return False if any test fails
        """
        import subprocess

        if not test_files:
            # No tests specified - consider this a pass
            return True

        for test_file in test_files:
            if not test_file.exists():
                self.logger.warning("ncm_test_file_not_found", {
                    "file": str(test_file)
                })
                continue

            try:
                self.logger.debug("ncm_running_tests", {
                    "file": str(test_file)
                })

                # Run pytest with minimal output
                result = subprocess.run(
                    ["pytest", str(test_file), "-v", "--tb=short", "-q"],
                    capture_output=True,
                    text=True,
                    timeout=300  # 5 min timeout per test file
                )

                if result.returncode != 0:
                    self.logger.error("ncm_tests_failed", {
                        "file": str(test_file),
                        "returncode": result.returncode,
                        "output": result.stdout[:500]  # First 500 chars
                    })
                    return False

                self.logger.debug("ncm_tests_passed", {
                    "file": str(test_file)
                })

            except subprocess.TimeoutExpired:
                self.logger.error("ncm_tests_timeout", {
                    "file": str(test_file)
                })
                return False
            except Exception as e:
                self.logger.error("ncm_tests_error", {
                    "file": str(test_file),
                    "error": str(e)
                })
                return False

        return True

    async def _refresh_prompts(self):
        """
        Refresh agent prompts (Blind Spot #3 mitigation).

        This reloads system prompts from disk to prevent prompt drift/decay
        during long-running execution.

        Process:
            1. Reload prompts from prompts/ directory
            2. Update orchestrator's prompt cache
            3. Reset tool_calls_since_refresh counter

        NOTE: For Phase 0, this is a stub.
              Full implementation will be added in Phase 0.3.
        """
        from core.prompts import list_prompts, load_prompt

        self.logger.info("ncm_prompt_refresh_start", {
            "tool_calls": self.tool_calls_since_refresh
        })

        refreshed = 0
        failures = 0

        for prompt_name in list_prompts():
            try:
                load_prompt(prompt_name)
                refreshed += 1
            except Exception as e:
                failures += 1
                self.logger.warning("ncm_prompt_refresh_failed", {
                    "prompt": prompt_name,
                    "error": str(e)
                })

        self.tool_calls_since_refresh = 0

        self.logger.info("ncm_prompt_refresh_complete", {
            "refreshed": refreshed,
            "failed": failures
        })

    async def _take_state_snapshot(self):
        """
        Take Blackboard state snapshot (Blind Spot #6 mitigation).

        Saves complete state to enable recovery from corruption or crashes.

        Process:
            1. Export Blackboard state from OrchestratorV7
            2. Save story queue checkpoint
            3. Save metrics and agent data
            4. Write snapshot to disk

        NOTE: For Phase 0, this is a stub.
              Full implementation will be added in Phase 0.3.
        """
        completed_count = len(self.completed)

        self.logger.info("ncm_state_snapshot_start", {
            "stories_completed": completed_count
        })

        blackboard_state = {}
        if getattr(self.orchestrator, "blackboard", None) is not None:
            blackboard_state = self.orchestrator.blackboard
        elif getattr(self.orchestrator, "memory", None) is not None:
            blackboard_state = getattr(self.orchestrator.memory, "blackboard", {})

        agent_metrics = {}
        agent_pool = getattr(self.orchestrator, "agent_pool", None)
        if agent_pool and getattr(agent_pool, "agents", None):
            agent_metrics = {
                agent_id: profile.to_dict(include_history=False)
                for agent_id, profile in agent_pool.agents.items()
            }

        crew_snapshot = {}
        if getattr(self, "crew_manager", None):
            try:
                crew_snapshot = {
                    "workload": self.crew_manager.get_workload_status(),
                    "assignments": self.crew_manager.get_assignments_snapshot()
                }
            except Exception as e:
                self.logger.warning("ncm_snapshot_crew_failed", {
                    "error": str(e)
                })

        snapshot = StateSnapshot(
            snapshot_id=f"SNAP-{completed_count}",
            stories_completed=completed_count,
            blackboard_state=blackboard_state,
            story_queue=[s.story_id for s in self.story_queue],
            agent_metrics=agent_metrics,
            tokens_remaining=self.token_limit - self.tokens_used,
            snapshot_path=self.ncm_workspace / "snapshots" / f"snapshot_{completed_count}.json"
        )

        snapshot.snapshot_path.parent.mkdir(parents=True, exist_ok=True)

        # Save snapshot to disk
        snapshot_data = {
            "snapshot_id": snapshot.snapshot_id,
            "stories_completed": snapshot.stories_completed,
            "story_queue": snapshot.story_queue,
            "tokens_remaining": snapshot.tokens_remaining,
            "created_at": snapshot.created_at.isoformat(),
            "blackboard_state": snapshot.blackboard_state,
            "agent_metrics": snapshot.agent_metrics,
            "crew_snapshot": crew_snapshot,
        }

        snapshot.snapshot_path.write_text(json.dumps(snapshot_data, indent=2, default=str))

        self.snapshots.append(snapshot)
        self.last_snapshot_count = completed_count

        self.logger.info("ncm_state_snapshot_complete", {
            "snapshot_id": snapshot.snapshot_id,
            "snapshot_path": str(snapshot.snapshot_path)
        })

    async def _save_metrics(self):
        """
        Save execution metrics to disk.

        Saves current_metrics to workspace/ncm/metrics/metrics_<phase>.json
        for later analysis and reporting.
        """
        if self.current_metrics is None:
            return

        metrics_file = self.ncm_workspace / "metrics" / f"metrics_{self.current_metrics.phase}.json"

        metrics_data = {
            "phase": self.current_metrics.phase,
            "stories_total": self.current_metrics.stories_total,
            "stories_completed": self.current_metrics.stories_completed,
            "stories_failed": self.current_metrics.stories_failed,
            "stories_partial": self.current_metrics.stories_partial,
            "success_rate": self.current_metrics.success_rate,
            "tokens_used": self.current_metrics.tokens_used,
            "avg_tokens_per_story": self.current_metrics.avg_tokens_per_story,
            "stories_per_hour": self.current_metrics.stories_per_hour,
            "duration_hours": self.current_metrics.duration_hours,
            "started_at": self.current_metrics.started_at.isoformat(),
            "completed_at": self.current_metrics.completed_at.isoformat() if self.current_metrics.completed_at else None,
        }

        metrics_file.write_text(json.dumps(metrics_data, indent=2))

        self.logger.debug("ncm_metrics_saved", {
            "metrics_file": str(metrics_file)
        })

    def get_metrics(self) -> Optional[ExecutionMetrics]:
        """
        Get current execution metrics.

        Returns:
            Current ExecutionMetrics or None if no batch executing
        """
        return self.current_metrics

    def get_status(self) -> Dict[str, Any]:
        """
        Get NCM status summary.

        Returns:
            Dict with current status:
                - queue_size: Stories remaining in queue
                - completed_count: Stories completed
                - failed_count: Stories failed
                - partial_count: Stories partially completed
                - success_rate: Overall success rate
                - tokens_used: Tokens used so far
                - tokens_remaining: Tokens remaining in budget
                - current_phase: Current execution phase
        """
        total_processed = len(self.completed) + len(self.failed) + len(self.partial)
        success_rate = len(self.completed) / total_processed if total_processed > 0 else 0.0

        return {
            "queue_size": len(self.story_queue),
            "completed_count": len(self.completed),
            "failed_count": len(self.failed),
            "partial_count": len(self.partial),
            "success_rate": success_rate,
            "tokens_used": self.tokens_used,
            "tokens_remaining": self.token_limit - self.tokens_used,
            "current_phase": self.current_phase,
            "current_story": self.current_story.story_id if self.current_story else None,
        }
