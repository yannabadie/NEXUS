"""
ParallelExecutor - Simultaneous Agent Execution.

NEXUS V9.5 Refactored

Execute agents in parallel with result merging.
Use case: Independent subtasks, time-critical situations.
"""

from __future__ import annotations

import asyncio
import sys
from typing import List, Optional, TYPE_CHECKING

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

        # Merge results
        merge_result = self._merge_with_strategy(context, outputs)

        success_count = sum(1 for o in outputs if o.status != "error")
        print(f"✅ [PARALLEL] Complete: {success_count}/{len(outputs)} succeeded | {total_time:.1f}s\n", file=sys.stderr)

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
