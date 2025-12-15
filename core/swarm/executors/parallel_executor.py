"""
ParallelExecutor - Simultaneous Agent Execution.

NEXUS V9.5 Refactored

Execute agents in parallel with result merging.
Use case: Independent subtasks, time-critical situations.

V10 FIX F4: Added ConflictDetector for parallel execution safety.
"""

from __future__ import annotations

import asyncio
import re
import sys
from dataclasses import dataclass, field
from typing import List, Optional, Set, Dict, TYPE_CHECKING

from .base import (
    ModeExecutor,
    ExecutionContext,
    ExecutionResult,
    ExecutionStatus,
    AgentResponse,
)
from ..collaboration_modes import CollaborationMode
from ...agents.unified_registry import get_registry

if TYPE_CHECKING:
    from ..merge_strategies import MergeStrategy, MergeResult


# =============================================================================
# V10 FIX F4: Conflict Detection for Parallel Execution
# =============================================================================

@dataclass
class ConflictReport:
    """Report of detected conflicts in parallel execution."""
    has_conflicts: bool = False
    file_conflicts: List[str] = field(default_factory=list)
    command_conflicts: List[str] = field(default_factory=list)
    semantic_conflicts: List[str] = field(default_factory=list)
    severity: str = "NONE"  # NONE, LOW, MEDIUM, HIGH

    def to_dict(self) -> Dict:
        return {
            "has_conflicts": self.has_conflicts,
            "file_conflicts": self.file_conflicts,
            "command_conflicts": self.command_conflicts,
            "semantic_conflicts": self.semantic_conflicts,
            "severity": self.severity
        }


class ConflictDetector:
    """
    V10 FIX F4: Detects potential conflicts in parallel agent outputs.

    Checks for:
    - File operation conflicts (multiple agents editing same file)
    - Command conflicts (conflicting bash operations)
    - Semantic conflicts (contradictory conclusions)
    """

    # Patterns to extract file paths from agent outputs
    FILE_PATH_PATTERNS = [
        r'(?:file|path|edit(?:ed|ing)?|creat(?:ed|ing)?|writ(?:e|ing)|read(?:ing)?)[:\s]+[`"]?([^\s`"]+\.\w+)[`"]?',
        r'`([^\s`]+\.\w{1,5})`',
        r'(?:in|at|from)\s+([^\s]+\.\w{1,5})',
    ]

    # Patterns to extract bash commands
    BASH_PATTERNS = [
        r'```bash\n([^`]+)```',
        r'(?:run|execute|command):\s*`([^`]+)`',
    ]

    # Semantic conflict indicators
    CONTRADICTION_PATTERNS = [
        (r'\bshould\s+(?:not|n\'t)\b', r'\bshould\b'),
        (r'\bdo\s+(?:not|n\'t)\b', r'\bdo\b'),
        (r'\brecommend\s+against\b', r'\brecommend\b'),
        (r'\bavoid\b', r'\buse\b'),
    ]

    def detect_conflicts(self, outputs: List["AgentResponse"]) -> ConflictReport:
        """
        Analyze parallel outputs for conflicts.

        Args:
            outputs: List of agent responses

        Returns:
            ConflictReport with detected conflicts
        """
        report = ConflictReport()

        # Extract data from each output
        file_operations: Dict[str, List[str]] = {}  # file -> [agents]
        bash_commands: Dict[str, List[str]] = {}     # command -> [agents]

        for output in outputs:
            if output.status == "error":
                continue

            agent_id = output.agent_id
            content = output.content

            # Check file operations
            for pattern in self.FILE_PATH_PATTERNS:
                for match in re.finditer(pattern, content, re.IGNORECASE):
                    file_path = match.group(1)
                    if file_path not in file_operations:
                        file_operations[file_path] = []
                    if agent_id not in file_operations[file_path]:
                        file_operations[file_path].append(agent_id)

            # Check bash commands
            for pattern in self.BASH_PATTERNS:
                for match in re.finditer(pattern, content, re.DOTALL):
                    command = match.group(1).strip()
                    if command not in bash_commands:
                        bash_commands[command] = []
                    if agent_id not in bash_commands[command]:
                        bash_commands[command].append(agent_id)

        # Detect file conflicts (multiple agents touching same file)
        for file_path, agents in file_operations.items():
            if len(agents) > 1:
                report.file_conflicts.append(
                    f"{file_path}: edited by {', '.join(agents)}"
                )

        # Detect command conflicts
        commands_list = list(bash_commands.keys())
        for i, cmd1 in enumerate(commands_list):
            for cmd2 in commands_list[i+1:]:
                if self._commands_conflict(cmd1, cmd2):
                    agents1 = bash_commands[cmd1]
                    agents2 = bash_commands[cmd2]
                    report.command_conflicts.append(
                        f"'{cmd1[:50]}' ({agents1}) conflicts with '{cmd2[:50]}' ({agents2})"
                    )

        # Detect semantic conflicts
        report.semantic_conflicts = self._detect_semantic_conflicts(outputs)

        # Update report
        report.has_conflicts = bool(
            report.file_conflicts or
            report.command_conflicts or
            report.semantic_conflicts
        )

        # Calculate severity
        if report.file_conflicts:
            report.severity = "HIGH"
        elif report.command_conflicts:
            report.severity = "MEDIUM"
        elif report.semantic_conflicts:
            report.severity = "LOW"

        return report

    def _commands_conflict(self, cmd1: str, cmd2: str) -> bool:
        """Check if two bash commands conflict."""
        # Same file, different operations
        cmd1_lower = cmd1.lower()
        cmd2_lower = cmd2.lower()

        # Create vs delete same path
        create_patterns = [r'mkdir', r'touch', r'echo.*>', r'cat.*>']
        delete_patterns = [r'rm\s', r'rmdir']

        for create_p in create_patterns:
            for delete_p in delete_patterns:
                if re.search(create_p, cmd1_lower) and re.search(delete_p, cmd2_lower):
                    # Check if same path
                    paths1 = re.findall(r'[\w/.-]+', cmd1)
                    paths2 = re.findall(r'[\w/.-]+', cmd2)
                    if set(paths1) & set(paths2):
                        return True
                if re.search(delete_p, cmd1_lower) and re.search(create_p, cmd2_lower):
                    paths1 = re.findall(r'[\w/.-]+', cmd1)
                    paths2 = re.findall(r'[\w/.-]+', cmd2)
                    if set(paths1) & set(paths2):
                        return True

        return False

    def _detect_semantic_conflicts(self, outputs: List["AgentResponse"]) -> List[str]:
        """Detect semantic contradictions between outputs."""
        conflicts = []

        for i, out1 in enumerate(outputs):
            for out2 in outputs[i+1:]:
                if out1.status == "error" or out2.status == "error":
                    continue

                content1 = out1.content.lower()
                content2 = out2.content.lower()

                for neg_pattern, pos_pattern in self.CONTRADICTION_PATTERNS:
                    has_neg1 = bool(re.search(neg_pattern, content1))
                    has_pos2 = bool(re.search(pos_pattern, content2))
                    has_neg2 = bool(re.search(neg_pattern, content2))
                    has_pos1 = bool(re.search(pos_pattern, content1))

                    if (has_neg1 and has_pos2) or (has_neg2 and has_pos1):
                        conflicts.append(
                            f"Potential contradiction between {out1.agent_id} and {out2.agent_id}"
                        )
                        break

        return conflicts


class ParallelExecutor(ModeExecutor):
    """
    Execute agents in parallel with result merging.

    Supports pluggable merge strategies via MergeStrategy classes.
    """

    mode = CollaborationMode.PARALLEL

    def __init__(self, merge_strategy: Optional["MergeStrategy"] = None):
        """
        Initialize ParallelExecutor with optional merge strategy.

        Args:
            merge_strategy: Strategy for merging parallel outputs.
        """
        from ..merge_strategies import get_default_merge_strategy
        self._merge_strategy = merge_strategy or get_default_merge_strategy()
        # V10 FIX F4: Conflict detector
        self._conflict_detector = ConflictDetector()

    def execute(self, context: ExecutionContext) -> ExecutionResult:
        """
        Sync execute - calls async execute_async().

        .. deprecated::
            Use `await executor.execute_async(context)` in async code.
        """
        import warnings
        warnings.warn(
            "ParallelExecutor.execute() is deprecated. "
            "Use `await executor.execute_async(context)` in async code.",
            DeprecationWarning,
            stacklevel=2
        )

        try:
            loop = asyncio.get_running_loop()
            import concurrent.futures
            future = asyncio.run_coroutine_threadsafe(self.execute_async(context), loop)
            return future.result(timeout=300)
        except RuntimeError:
            return asyncio.run(self.execute_async(context))

    async def execute_async(self, context: ExecutionContext) -> ExecutionResult:
        """
        True async parallel execution using asyncio.gather().

        Performance gain: 40-50% for I/O-bound tasks.
        """
        agents = context.get_all_agents()
        total_tokens = 0
        total_time = 0.0

        # Show parallel execution start
        agent_names = [a.agent_id for a in agents]
        print(f"\n🔀 [PARALLEL] Starting with {len(agents)} agents: {', '.join(agent_names)}", file=sys.stderr)

        # Prepare async tasks
        tasks_info = []
        async_tasks = []
        for idx, agent in enumerate(agents):
            subtask = agent.subtask or context.task_input
            task_context = f"PARALLEL MODE - Your subtask:\n{subtask}\n\nFull task: {context.task_input}"
            tasks_info.append((agent.agent_id, task_context))

            subtask_preview = (subtask[:100] + "...") if len(subtask) > 100 else subtask
            print(f"   → {agent.agent_id}: {subtask_preview}", file=sys.stderr)

            async_tasks.append(
                self._invoke_async(context, agent.agent_id, task_context, f"worker_{idx}")
            )

        print(f"   ⏳ Agents working...", file=sys.stderr)

        # TRUE PARALLEL EXECUTION
        results = await asyncio.gather(*async_tasks, return_exceptions=True)

        # Process results
        outputs: List[AgentResponse] = []
        for i, result in enumerate(results):
            agent_id = tasks_info[i][0]
            if isinstance(result, Exception):
                outputs.append(AgentResponse(
                    agent_id=agent_id,
                    content="",
                    status="error",
                    error=str(result)
                ))
                print(f"   ❌ {agent_id}: ERROR - {str(result)[:100]}", file=sys.stderr)
            else:
                outputs.append(result)
                total_tokens += result.tokens_used
                total_time = max(total_time, result.time_seconds)
                content_preview = (result.content[:80] + "...") if len(result.content) > 80 else result.content
                content_preview = content_preview.replace('\n', ' ')
                print(f"   ✓ {agent_id}: {content_preview}", file=sys.stderr)

        # V10 FIX F4: Detect conflicts before merging
        conflict_report = self._conflict_detector.detect_conflicts(outputs)
        if conflict_report.has_conflicts:
            print(f"⚠️  [PARALLEL] Conflicts detected ({conflict_report.severity}):", file=sys.stderr)
            for fc in conflict_report.file_conflicts[:3]:
                print(f"      📄 {fc}", file=sys.stderr)
            for cc in conflict_report.command_conflicts[:2]:
                print(f"      ⚡ {cc}", file=sys.stderr)
            for sc in conflict_report.semantic_conflicts[:2]:
                print(f"      💭 {sc}", file=sys.stderr)

        # Merge results
        merge_result = self._merge_with_strategy(context, outputs)

        success_count = sum(1 for o in outputs if o.status != "error")
        conflict_indicator = f" ⚠️ {conflict_report.severity} conflicts" if conflict_report.has_conflicts else ""
        print(f"✅ [PARALLEL] Complete: {success_count}/{len(outputs)} succeeded | {total_time:.1f}s{conflict_indicator}\n", file=sys.stderr)

        return ExecutionResult(
            mode=self.mode,
            status=ExecutionStatus.COMPLETED,
            final_output=merge_result.content,
            agent_outputs=outputs,
            total_rounds=1,
            total_tokens=total_tokens,
            total_time_seconds=total_time,
            metadata={
                "execution_type": "parallel_async",
                "merge_strategy": merge_result.strategy_used.value,
                # V10 FIX F4: Include conflict report
                "conflict_report": conflict_report.to_dict(),
                **merge_result.metadata
            }
        )

    def _merge_with_strategy(
        self,
        context: ExecutionContext,
        outputs: List[AgentResponse]
    ) -> "MergeResult":
        """Merge outputs using the configured merge strategy."""
        from ..merge_strategies import MergeContext

        merge_context = MergeContext(
            task_input=context.task_input,
            outputs=outputs,
            task_analysis=context.blackboard.get("task_analysis"),
            agent_assignments=context.agent_assignments
        )

        return self._merge_strategy.merge(merge_context)

    def _merge_outputs(self, outputs: List[AgentResponse], task: str) -> str:
        """Legacy merge method for backward compatibility."""
        registry = get_registry()
        merged_parts = []
        for output in outputs:
            agent_name = registry.get_display_name(output.agent_id)
            if output.status == "error":
                merged_parts.append(f"[{agent_name}] ❌ Error:\n{output.error or output.content}")
            else:
                merged_parts.append(f"[{agent_name}]:\n{output.content}")

        return "\n\n---\n\n".join(merged_parts)
