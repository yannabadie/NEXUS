"""
Mode Executors - Sprint 9 Hybrid Swarm Engine

Implements the 6 collaboration mode executors:
- ParallelExecutor: Simultaneous work with result merging
- SequentialExecutor: Ordered execution (first → second)
- LeadSupportExecutor: Lead drives, support reviews
- PingPongExecutor: Rapid alternation until convergence
- SpecialistExecutor: Single expert handles all
- RedBlueExecutor: Adversarial propose/attack/defend

Each executor manages agent invocations according to its mode's pattern.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable, Any, TYPE_CHECKING
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from enum import Enum
from pathlib import Path

from .collaboration_modes import CollaborationMode
from .mode_selector import AgentAssignment
from ..utils.artifact_verifier import ArtifactVerifier
from .task_completion_validator import TaskCompletionValidator, get_adaptive_max_rounds

# V8.3.3: Type hints for merge strategies (avoid circular import)
if TYPE_CHECKING:
    from .merge_strategies import MergeStrategy, MergeResult


class ExecutionStatus(Enum):
    """Status of mode execution"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CONVERGED = "converged"


@dataclass
class AgentResponse:
    """Response from a single agent invocation"""
    agent_id: str
    content: str
    status: str = "success"
    tool_results: List[Dict] = field(default_factory=list)
    tokens_used: int = 0
    time_seconds: float = 0.0
    error: Optional[str] = None

    @property
    def is_finished(self) -> bool:
        """
        Check if agent signals completion.

        V7.9 IMPROVED: More robust detection that avoids false positives.
        - Checks for completion keywords
        - Rejects if ongoing work indicators are present
        """
        content_upper = self.content.upper()

        # Completion signals
        completion_signals = (
            "FINISHED" in content_upper
            or "DONE" in content_upper
            or "TASK COMPLETE" in content_upper
            or self.status == "finished"
        )

        if not completion_signals:
            return False

        # V7.9: Check for ongoing work indicators (false positive prevention)
        content_lower = self.content.lower()
        ongoing_indicators = [
            "will ", "going to", "next step", "todo", "remaining",
            "need to", "should ", "plan to", "working on", "then we"
        ]

        has_ongoing = any(indicator in content_lower for indicator in ongoing_indicators)

        # Only consider finished if no ongoing work detected
        return not has_ongoing

    def to_dict(self) -> Dict:
        return {
            "agent_id": self.agent_id,
            "content": self.content,  # Full content (no truncation)
            "status": self.status,
            "tool_results_count": len(self.tool_results),
            "tokens_used": self.tokens_used,
            "time_seconds": round(self.time_seconds, 2),
            "error": self.error
        }


@dataclass
class ExecutionContext:
    """Context for mode execution.

    V7.5 Phase 7: Added task_id and session_manager for session isolation.
    V7.7 Phase 14e: Added force_cot for Chain-of-Thought enforcement.
    """
    task_input: str
    agent_assignments: List[AgentAssignment]
    blackboard: Dict = field(default_factory=dict)
    max_rounds: int = 6
    invoke_agent: Optional[Callable] = None  # Callable[[str, str, str], AgentResponse]
    on_round: Optional[Callable[[int, "AgentResponse"], None]] = None  # V7.5: Streaming callback
    # V7.5 Phase 7: Session isolation
    task_id: Optional[str] = None
    session_manager: Optional[Any] = None  # SwarmSessionManager (avoid circular import)
    # V7.7 Phase 14e: Force Chain-of-Thought for EXPERT complexity
    force_cot: bool = False

    def get_agent_by_role(self, role: str) -> Optional[AgentAssignment]:
        """Get agent assignment by role"""
        for assignment in self.agent_assignments:
            if assignment.role == role:
                return assignment
        return None

    def get_all_agents(self) -> List[AgentAssignment]:
        """Get all agent assignments"""
        return self.agent_assignments

    def get_session_uuid(self, role: str, agent_id: str) -> Optional[str]:
        """
        Get or create session UUID for an agent-role combination.

        V7.5 Phase 7: Session isolation for parallel task execution.

        Args:
            role: The role in the task (e.g., "lead", "support")
            agent_id: The agent identifier (e.g., "gemini", "claude")

        Returns:
            Session UUID string if session_manager is available, None otherwise
        """
        if self.session_manager is None or self.task_id is None:
            return None

        try:
            return self.session_manager.get_or_create_session(
                self.task_id, role, agent_id
            )
        except Exception:
            return None


@dataclass
class ExecutionResult:
    """Result of mode execution"""
    mode: CollaborationMode
    status: ExecutionStatus
    final_output: str
    agent_outputs: List[AgentResponse]
    total_rounds: int
    total_tokens: int
    total_time_seconds: float
    metadata: Dict = field(default_factory=dict)

    @property
    def finished(self) -> bool:
        return self.status in [ExecutionStatus.COMPLETED, ExecutionStatus.CONVERGED]

    def to_dict(self) -> Dict:
        return {
            "mode": self.mode.value,
            "status": self.status.value,
            "final_output": self.final_output,  # Full output (no truncation)
            "agent_outputs": [a.to_dict() for a in self.agent_outputs],
            "total_rounds": self.total_rounds,
            "total_tokens": self.total_tokens,
            "total_time_seconds": round(self.total_time_seconds, 2),
            "metadata": self.metadata
        }


class ModeExecutor(ABC):
    """Base class for mode executors"""

    mode: CollaborationMode

    @abstractmethod
    def execute(self, context: ExecutionContext) -> ExecutionResult:
        """Execute the mode with given context"""
        pass

    def _invoke(
        self,
        context: ExecutionContext,
        agent_id: str,
        task_context: str,
        role: Optional[str] = None
    ) -> AgentResponse:
        """
        Invoke an agent with task context.

        V7.5 Phase 7: Session isolation via role-based session UUIDs.

        Args:
            context: Execution context
            agent_id: Agent identifier (e.g., "gemini", "claude")
            task_context: Task context string to send
            role: Agent's role in the task (e.g., "lead", "support").
                 Used to get session_uuid for isolation.
        """
        if context.invoke_agent is None:
            # Fallback for testing
            return AgentResponse(
                agent_id=agent_id,
                content=f"[Mock response from {agent_id}]",
                status="mock"
            )

        start_time = datetime.now()

        # V7.5 Phase 7: Get session UUID for isolation
        session_uuid = None
        if role:
            session_uuid = context.get_session_uuid(role, agent_id)
            if session_uuid:
                # Store in blackboard for driver access (legacy, kept for compatibility)
                context.blackboard[f"_session_uuid_{agent_id}"] = session_uuid

        try:
            # V8.1.6: Pass session_uuid directly to invoke_agent for thread-safe file access
            response = context.invoke_agent(agent_id, "execution", task_context, session_uuid)

            # If response is string, wrap in AgentResponse
            if isinstance(response, str):
                response = AgentResponse(
                    agent_id=agent_id,
                    content=response,
                    status="success"
                )

            response.time_seconds = (datetime.now() - start_time).total_seconds()
            return response

        except Exception as e:
            return AgentResponse(
                agent_id=agent_id,
                content="",
                status="error",
                error=str(e),
                time_seconds=(datetime.now() - start_time).total_seconds()
            )
        finally:
            # Clean up session UUID from blackboard
            if session_uuid:
                context.blackboard.pop(f"_session_uuid_{agent_id}", None)

    def _invoke_with_failover(
        self,
        context: ExecutionContext,
        primary_agent_id: str,
        backup_agent_id: str,
        task_context: str,
        primary_role: Optional[str] = None,
        backup_role: Optional[str] = None
    ) -> AgentResponse:
        """
        Invoke primary agent, failover to backup if primary fails.

        V7 Enhancement: Resilience when one agent times out or errors.
        V7.5 Phase 7: Session isolation via roles.

        Args:
            context: Execution context
            primary_agent_id: First agent to try
            backup_agent_id: Fallback agent if primary fails
            task_context: Task context to send
            primary_role: Role of primary agent (for session isolation)
            backup_role: Role of backup agent (for session isolation)

        Returns:
            AgentResponse from whichever agent succeeded
        """
        # Try primary agent
        response = self._invoke(context, primary_agent_id, task_context, role=primary_role)

        # Check if primary failed (error status or timeout indicator)
        if response.status == "error" or "timed out" in (response.error or "").lower():
            # Log failover (via print since we don't have logger here)
            import sys
            print(f"[FAILOVER] {primary_agent_id} failed, trying {backup_agent_id}",
                  file=sys.stderr)

            # Add failover context to task
            failover_context = (
                f"{task_context}\n\n"
                f"[NOTE: {primary_agent_id} was unavailable. You are the failover agent.]"
            )

            # Try backup agent
            backup_response = self._invoke(context, backup_agent_id, failover_context, role=backup_role)

            # Mark that this was a failover
            if backup_response.status != "error":
                backup_response.content = (
                    f"[Failover from {primary_agent_id}]\n\n{backup_response.content}"
                )

            return backup_response

        return response

    def _get_backup_agent(self, agent_id: str) -> str:
        """Get the backup agent for a given agent"""
        if "gemini" in agent_id.lower():
            return "claude_opus"
        else:
            return "gemini_primary"

    def _verify_artifacts(
        self,
        content: str,
        context: "ExecutionContext"
    ) -> Dict[str, Any]:
        """
        Verify artifacts mentioned in agent output.

        V7 Enhancement: Generalized artifact verification for all modes.

        Args:
            content: Agent output text
            context: Execution context (for workspace path)

        Returns:
            Dict with verification results:
            - verified: bool (all artifacts OK)
            - successes: List[str]
            - failures: List[str]
        """
        workspace_path = context.blackboard.get("workspace_path", Path.cwd())
        verifier = ArtifactVerifier(Path(workspace_path))

        verified, successes, failures = verifier.verify_from_content(content)

        return {
            "verified": verified,
            "successes": successes,
            "failures": failures
        }

    def execute_with_fallback(
        self,
        context: ExecutionContext,
        max_fallbacks: int = 2
    ) -> ExecutionResult:
        """
        Execute with automatic fallback to simpler modes on failure.

        V7.5 Phase 8: Self-Healing Swarm - Graceful Degradation

        Algorithm:
        1. Create checkpoint (if session_manager available)
        2. Try execute()
        3. If failure (ExecutionStatus.FAILED or exception):
           a. Log degradation
           b. Restore checkpoint
           c. Get fallback mode
           d. If fallback exists: instantiate new executor and retry
           e. Otherwise: re-raise exception
        4. If success after fallback: mark status="RECOVERED"

        Args:
            context: Execution context
            max_fallbacks: Maximum number of fallback attempts (default 2)

        Returns:
            ExecutionResult with status potentially marked as RECOVERED
        """
        import sys

        current_mode = self.mode
        checkpoint_id = None
        fallback_count = 0
        original_exception = None
        degradation_path = [current_mode.value]

        # Create checkpoint if session manager available
        if context.session_manager and context.task_id:
            try:
                checkpoint_id = context.session_manager.create_checkpoint(context.task_id)
            except Exception:
                pass  # Continue without checkpoint

        while fallback_count <= max_fallbacks:
            try:
                # Get appropriate executor
                executor = EXECUTOR_REGISTRY.get(current_mode, self)

                # Attempt execution
                result = executor.execute(context)

                # Check for failure status
                if result.status == ExecutionStatus.FAILED:
                    raise ExecutionError(
                        f"Mode {current_mode.value} returned FAILED status: "
                        f"{result.final_output[:200] if result.final_output else 'No output'}"
                    )

                # Success! Mark as recovered if we fell back
                if fallback_count > 0:
                    result.metadata["status"] = "RECOVERED"
                    result.metadata["original_mode"] = degradation_path[0]
                    result.metadata["fallback_path"] = degradation_path
                    result.metadata["fallback_count"] = fallback_count
                    print(
                        f"[SELF-HEALING] Recovered via {current_mode.value} after "
                        f"{fallback_count} fallback(s): {' -> '.join(degradation_path)}",
                        file=sys.stderr
                    )

                return result

            except Exception as e:
                if original_exception is None:
                    original_exception = e

                # Log degradation
                print(
                    f"[SWARM DEGRADATION] Mode {current_mode.value} failed: {str(e)[:100]}",
                    file=sys.stderr
                )

                # Restore checkpoint if available
                if checkpoint_id and context.session_manager and context.task_id:
                    try:
                        context.session_manager.restore_checkpoint(
                            context.task_id, checkpoint_id
                        )
                    except Exception:
                        pass  # Continue even if restore fails

                # Get fallback mode
                fallback = current_mode.fallback_mode
                if fallback is None:
                    # No more fallbacks available
                    print(
                        f"[SWARM DEGRADATION] No fallback available for {current_mode.value}. "
                        f"Degradation path: {' -> '.join(degradation_path)}",
                        file=sys.stderr
                    )
                    # Re-raise the original exception
                    raise original_exception

                # Prepare for next iteration
                fallback_count += 1
                current_mode = fallback
                degradation_path.append(current_mode.value)

                print(
                    f"[SWARM DEGRADATION] Falling back to {current_mode.value} "
                    f"(attempt {fallback_count}/{max_fallbacks})",
                    file=sys.stderr
                )

        # Exceeded max fallbacks
        raise original_exception or ExecutionError(
            f"Exceeded max fallbacks ({max_fallbacks}) without success"
        )


class ExecutionError(Exception):
    """Exception raised during mode execution."""
    pass


class ParallelExecutor(ModeExecutor):
    """
    Execute agents in parallel with result merging.

    Use case: Independent subtasks, time-critical situations.

    V8.3.3: Supports pluggable merge strategies via MergeStrategy classes.
    """

    mode = CollaborationMode.PARALLEL

    def __init__(self, merge_strategy: Optional["MergeStrategy"] = None):
        """
        Initialize ParallelExecutor with optional merge strategy.

        Args:
            merge_strategy: Strategy for merging parallel outputs.
                           If None, uses default from environment.
        """
        # Lazy import to avoid circular dependency
        from .merge_strategies import get_default_merge_strategy, MergeStrategy
        self._merge_strategy = merge_strategy or get_default_merge_strategy()

    def execute(self, context: ExecutionContext) -> ExecutionResult:
        agents = context.get_all_agents()
        outputs: List[AgentResponse] = []
        total_tokens = 0
        total_time = 0.0

        # Prepare tasks with subtask assignments
        tasks = []
        for agent in agents:
            subtask = agent.subtask or context.task_input
            task_context = f"PARALLEL MODE - Your subtask:\n{subtask}\n\nFull task: {context.task_input}"
            tasks.append((agent.agent_id, task_context))

        # Execute in parallel
        # V7.5 Phase 7: Each worker gets unique role for session isolation
        with ThreadPoolExecutor(max_workers=len(tasks)) as executor:
            futures = {
                executor.submit(
                    self._invoke, context, agent_id, task_ctx, f"worker_{idx}"
                ): agent_id
                for idx, (agent_id, task_ctx) in enumerate(tasks)
            }

            for future in as_completed(futures):
                try:
                    response = future.result()
                    outputs.append(response)
                    total_tokens += response.tokens_used
                    total_time = max(total_time, response.time_seconds)  # Parallel: max time
                except Exception as e:
                    agent_id = futures[future]
                    outputs.append(AgentResponse(
                        agent_id=agent_id,
                        content="",
                        status="error",
                        error=str(e)
                    ))

        # V8.3.3: Use pluggable merge strategy
        merge_result = self._merge_with_strategy(context, outputs)

        return ExecutionResult(
            mode=self.mode,
            status=ExecutionStatus.COMPLETED,
            final_output=merge_result.content,
            agent_outputs=outputs,
            total_rounds=1,
            total_tokens=total_tokens,
            total_time_seconds=total_time,
            metadata={
                "execution_type": "parallel",
                "merge_strategy": merge_result.strategy_used.value,
                **merge_result.metadata
            }
        )

    def _merge_with_strategy(
        self,
        context: ExecutionContext,
        outputs: List[AgentResponse]
    ) -> "MergeResult":
        """
        Merge outputs using the configured merge strategy.

        V8.3.3: Builds MergeContext with task analysis for intelligent merging.
        """
        from .merge_strategies import MergeContext

        # Build merge context with all available information
        merge_context = MergeContext(
            task_input=context.task_input,
            outputs=outputs,
            task_analysis=context.blackboard.get("task_analysis"),
            agent_assignments=context.agent_assignments
        )

        return self._merge_strategy.merge(merge_context)

    def _merge_outputs(self, outputs: List[AgentResponse], task: str) -> str:
        """
        Legacy merge method for backward compatibility.

        Deprecated in V8.3.3 - use _merge_with_strategy instead.
        """
        merged_parts = []
        for output in outputs:
            if output.status == "error":
                agent_name = "Gemini" if "gemini" in output.agent_id.lower() else "Claude"
                merged_parts.append(f"[{agent_name}] ❌ Error:\n{output.error or output.content}")
            else:
                agent_name = "Gemini" if "gemini" in output.agent_id.lower() else "Claude"
                merged_parts.append(f"[{agent_name}]:\n{output.content}")

        return "\n\n---\n\n".join(merged_parts)


class SequentialExecutor(ModeExecutor):
    """
    Execute agents sequentially, passing output to next.

    Use case: Clear dependencies, pipeline tasks.
    """

    mode = CollaborationMode.SEQUENTIAL

    def execute(self, context: ExecutionContext) -> ExecutionResult:
        first = context.get_agent_by_role("first")
        second = context.get_agent_by_role("second")

        if not first or not second:
            # Fallback to order
            agents = context.get_all_agents()
            first = agents[0] if agents else None
            second = agents[1] if len(agents) > 1 else None

        outputs: List[AgentResponse] = []
        total_tokens = 0
        total_time = 0.0

        # First agent
        # V7.5 Phase 7: Role-based session isolation
        if first:
            first_context = f"SEQUENTIAL MODE - Phase 1:\n{context.task_input}\n\nYou are first. Provide your analysis/output."
            first_response = self._invoke(context, first.agent_id, first_context, role="first")
            outputs.append(first_response)
            total_tokens += first_response.tokens_used
            total_time += first_response.time_seconds

            # Second agent receives first's output
            if second:
                second_context = (
                    f"SEQUENTIAL MODE - Phase 2:\n{context.task_input}\n\n"
                    f"Previous agent ({first.agent_id}) output:\n{first_response.content}\n\n"
                    "Continue/refine based on this."
                )
                second_response = self._invoke(context, second.agent_id, second_context, role="second")
                outputs.append(second_response)
                total_tokens += second_response.tokens_used
                total_time += second_response.time_seconds

        final_output = outputs[-1].content if outputs else ""

        return ExecutionResult(
            mode=self.mode,
            status=ExecutionStatus.COMPLETED,
            final_output=final_output,
            agent_outputs=outputs,
            total_rounds=len(outputs),
            total_tokens=total_tokens,
            total_time_seconds=total_time,
            metadata={"execution_type": "sequential"}
        )


class LeadSupportExecutor(ModeExecutor):
    """
    Lead agent drives (80%), support reviews (20%).

    Use case: Clear expertise dominance, complex coding tasks.
    """

    mode = CollaborationMode.LEAD_SUPPORT

    def execute(self, context: ExecutionContext) -> ExecutionResult:
        lead = context.get_agent_by_role("lead")
        support = context.get_agent_by_role("support")

        if not lead or not support:
            agents = context.get_all_agents()
            lead = agents[0] if agents else None
            support = agents[1] if len(agents) > 1 else None

        outputs: List[AgentResponse] = []
        total_tokens = 0
        total_time = 0.0

        # Lead produces solution
        # V7.5 Phase 7: Role-based session isolation
        round_num = 0
        if lead:
            lead_context = f"LEAD_SUPPORT MODE - You are LEAD:\n{context.task_input}\n\nProvide complete solution."
            lead_response = self._invoke(context, lead.agent_id, lead_context, role="lead")
            outputs.append(lead_response)
            total_tokens += lead_response.tokens_used
            total_time += lead_response.time_seconds
            if context.on_round:
                context.on_round(round_num, lead_response)
            round_num += 1

            # Support reviews
            if support:
                review_context = (
                    f"LEAD_SUPPORT MODE - You are SUPPORT:\n{context.task_input}\n\n"
                    f"Lead ({lead.agent_id}) solution:\n{lead_response.content}\n\n"
                    "Review and provide feedback. Suggest improvements if needed."
                )
                review_response = self._invoke(context, support.agent_id, review_context, role="support")
                outputs.append(review_response)
                total_tokens += review_response.tokens_used
                total_time += review_response.time_seconds
                if context.on_round:
                    context.on_round(round_num, review_response)
                round_num += 1

                # If support has suggestions, lead revises
                if "suggest" in review_response.content.lower() or "improve" in review_response.content.lower():
                    revision_context = (
                        f"LEAD_SUPPORT MODE - Revision:\n"
                        f"Your original solution:\n{lead_response.content}\n\n"
                        f"Support feedback:\n{review_response.content}\n\n"
                        "Revise if appropriate."
                    )
                    revision_response = self._invoke(context, lead.agent_id, revision_context, role="lead")
                    outputs.append(revision_response)
                    total_tokens += revision_response.tokens_used
                    total_time += revision_response.time_seconds
                    if context.on_round:
                        context.on_round(round_num, revision_response)

        final_output = outputs[-1].content if outputs else ""

        # V7 Enhancement: Verify artifacts in final output
        artifact_result = self._verify_artifacts(final_output, context)

        return ExecutionResult(
            mode=self.mode,
            status=ExecutionStatus.COMPLETED,
            final_output=final_output,
            agent_outputs=outputs,
            total_rounds=len(outputs),
            total_tokens=total_tokens,
            total_time_seconds=total_time,
            metadata={
                "execution_type": "lead_support",
                "artifacts_verified": artifact_result["verified"],
                "artifact_successes": artifact_result["successes"],
                "artifact_failures": artifact_result["failures"]
            }
        )


class PingPongExecutor(ModeExecutor):
    """
    Rapid alternation until convergence.

    Use case: Creative tasks, brainstorming, iterative refinement.

    V7.9: Enhanced with TaskCompletionValidator to prevent premature FINISHED.
    """

    mode = CollaborationMode.PING_PONG

    def __init__(self, workspace_path: Optional[Path] = None):
        """
        Initialize PingPongExecutor.

        Args:
            workspace_path: Path to workspace for artifact verification
        """
        self._workspace_path = workspace_path

    def execute(self, context: ExecutionContext) -> ExecutionResult:
        agents = context.get_all_agents()
        if len(agents) < 2:
            return ExecutionResult(
                mode=self.mode,
                status=ExecutionStatus.FAILED,
                final_output="Need 2 agents for ping-pong",
                agent_outputs=[],
                total_rounds=0,
                total_tokens=0,
                total_time_seconds=0.0
            )

        # V7.9: Initialize completion validator
        workspace_path = context.blackboard.get("workspace_path") or self._workspace_path
        completion_validator = TaskCompletionValidator(workspace_path) if workspace_path else None

        # V7.9: Get task analysis for validation (from blackboard if available)
        task_analysis = context.blackboard.get("task_analysis")

        outputs: List[AgentResponse] = []
        tool_results: List[Dict] = []  # Collect tool results for validation
        total_tokens = 0
        total_time = 0.0
        current_idx = 0
        accumulated_context = context.task_input
        false_finish_count = 0  # Track rejected FINISHED signals

        # V7.5 Phase 7: Alternating roles for session isolation
        for round_num in range(context.max_rounds):
            agent = agents[current_idx % len(agents)]
            role = f"ping_{current_idx % len(agents)}"  # ping_0, ping_1, etc.

            # V7.9: Add context about rejected finishes if any
            rejection_notice = ""
            if false_finish_count > 0:
                rejection_notice = (
                    f"\n\n[IMPORTANT: {false_finish_count} premature FINISHED signal(s) were rejected. "
                    "Only say FINISHED when ALL work is truly complete with no remaining tasks.]"
                )

            round_context = (
                f"PING_PONG MODE - Round {round_num + 1}:\n"
                f"Original task: {context.task_input}\n\n"
                f"Conversation so far:\n{accumulated_context}{rejection_notice}\n\n"
                "Continue the work. Say 'FINISHED' ONLY when the task is FULLY complete."
            )

            response = self._invoke(context, agent.agent_id, round_context, role=role)
            outputs.append(response)
            total_tokens += response.tokens_used
            total_time += response.time_seconds

            # Collect tool results from response
            if response.tool_results:
                tool_results.extend(response.tool_results)

            # V7.5: Stream round to callback for real-time display
            if context.on_round:
                context.on_round(round_num, response)

            # Update accumulated context
            accumulated_context += f"\n\n[{agent.agent_id} - Round {round_num + 1}]:\n{response.content}"

            # V7.9: Enhanced convergence check with validation
            if response.is_finished:
                # Validate the completion claim
                is_valid_finish = True
                validation_reason = "Basic completion check passed"

                if completion_validator and task_analysis:
                    validation_result = completion_validator.validate_completion(
                        task_input=context.task_input,
                        agent_response=response.content,
                        task_analysis=task_analysis,
                        tool_results=tool_results
                    )
                    is_valid_finish = validation_result.is_valid
                    validation_reason = validation_result.reason

                    if not is_valid_finish:
                        # Reject the FINISHED signal
                        false_finish_count += 1
                        import sys
                        print(
                            f"[COMPLETION VALIDATOR] Rejected FINISHED signal (round {round_num + 1}): "
                            f"{validation_reason}",
                            file=sys.stderr
                        )
                        # Continue to next round
                        current_idx += 1
                        continue

                # Valid completion - return result
                return ExecutionResult(
                    mode=self.mode,
                    status=ExecutionStatus.CONVERGED,
                    final_output=response.content,
                    agent_outputs=outputs,
                    total_rounds=round_num + 1,
                    total_tokens=total_tokens,
                    total_time_seconds=total_time,
                    metadata={
                        "execution_type": "ping_pong",
                        "converged_at": round_num + 1,
                        "validation_reason": validation_reason,
                        "false_finish_count": false_finish_count
                    }
                )

            current_idx += 1

        # Max rounds reached
        final_output = outputs[-1].content if outputs else ""

        return ExecutionResult(
            mode=self.mode,
            status=ExecutionStatus.COMPLETED,
            final_output=final_output,
            agent_outputs=outputs,
            total_rounds=context.max_rounds,
            total_tokens=total_tokens,
            total_time_seconds=total_time,
            metadata={
                "execution_type": "ping_pong",
                "max_rounds_reached": True,
                "false_finish_count": false_finish_count
            }
        )


class SpecialistExecutor(ModeExecutor):
    """
    Single expert handles everything.

    Use case: Exclusive expertise, highly specialized tasks.

    V7 Enhancement: Failover to backup agent if specialist fails.
    """

    mode = CollaborationMode.SPECIALIST

    def execute(self, context: ExecutionContext) -> ExecutionResult:
        specialist = context.get_agent_by_role("specialist")

        if not specialist:
            # Find best agent
            agents = context.get_all_agents()
            specialist = agents[0] if agents else None

        if not specialist:
            return ExecutionResult(
                mode=self.mode,
                status=ExecutionStatus.FAILED,
                final_output="No specialist agent available",
                agent_outputs=[],
                total_rounds=0,
                total_tokens=0,
                total_time_seconds=0.0
            )

        task_context = f"SPECIALIST MODE - You are the sole expert:\n{context.task_input}\n\nHandle this task completely."

        # V7 Enhancement: Use failover for resilience
        # V7.5 Phase 7: Role-based session isolation
        backup_agent = self._get_backup_agent(specialist.agent_id)
        response = self._invoke_with_failover(
            context,
            specialist.agent_id,
            backup_agent,
            task_context,
            primary_role="specialist",
            backup_role="specialist_backup"
        )

        # V7 Enhancement: Verify artifacts in output
        artifact_result = self._verify_artifacts(response.content, context)

        return ExecutionResult(
            mode=self.mode,
            status=ExecutionStatus.COMPLETED if response.status != "error" else ExecutionStatus.FAILED,
            final_output=response.content,
            agent_outputs=[response],
            total_rounds=1,
            total_tokens=response.tokens_used,
            total_time_seconds=response.time_seconds,
            metadata={
                "execution_type": "specialist",
                "specialist": specialist.agent_id,
                "used_failover": "Failover" in response.content,
                "artifacts_verified": artifact_result["verified"],
                "artifact_successes": artifact_result["successes"],
                "artifact_failures": artifact_result["failures"]
            }
        )


class RedBlueExecutor(ModeExecutor):
    """
    Adversarial: Blue proposes, Red attacks, iterate.

    Use case: Security reviews, critical decisions, risk assessment.
    """

    mode = CollaborationMode.RED_BLUE

    def execute(self, context: ExecutionContext) -> ExecutionResult:
        blue = context.get_agent_by_role("blue")
        red = context.get_agent_by_role("red")

        if not blue or not red:
            agents = context.get_all_agents()
            blue = agents[0] if agents else None
            red = agents[1] if len(agents) > 1 else None

        if not blue or not red:
            return ExecutionResult(
                mode=self.mode,
                status=ExecutionStatus.FAILED,
                final_output="Need both blue (proposer) and red (attacker) agents",
                agent_outputs=[],
                total_rounds=0,
                total_tokens=0,
                total_time_seconds=0.0
            )

        outputs: List[AgentResponse] = []
        total_tokens = 0
        total_time = 0.0

        # V7.5 Phase 7: Role-based session isolation for adversarial mode
        # Phase 1: Blue proposes
        propose_context = (
            f"RED_BLUE MODE - You are BLUE (proposer):\n{context.task_input}\n\n"
            "Propose a complete solution. Be thorough as it will be attacked."
        )
        proposal = self._invoke(context, blue.agent_id, propose_context, role="blue")
        outputs.append(proposal)
        total_tokens += proposal.tokens_used
        total_time += proposal.time_seconds
        if context.on_round:
            context.on_round(0, proposal)

        # Phase 2: Red attacks
        attack_context = (
            f"RED_BLUE MODE - You are RED (attacker):\n{context.task_input}\n\n"
            f"Blue's proposal:\n{proposal.content}\n\n"
            "Find weaknesses, security issues, edge cases, flaws. Be adversarial."
        )
        attack = self._invoke(context, red.agent_id, attack_context, role="red")
        outputs.append(attack)
        total_tokens += attack.tokens_used
        total_time += attack.time_seconds
        if context.on_round:
            context.on_round(1, attack)

        # Phase 3: Blue defends
        defend_context = (
            f"RED_BLUE MODE - Defense phase:\n"
            f"Your original proposal:\n{proposal.content}\n\n"
            f"Red's attack:\n{attack.content}\n\n"
            "Defend your proposal and/or revise to address valid concerns."
        )
        defense = self._invoke(context, blue.agent_id, defend_context, role="blue")
        outputs.append(defense)
        total_tokens += defense.tokens_used
        total_time += defense.time_seconds
        if context.on_round:
            context.on_round(2, defense)

        # Phase 4: Red verifies
        verify_context = (
            f"RED_BLUE MODE - Verification:\n"
            f"Original proposal:\n{proposal.content}\n\n"
            f"Your attack:\n{attack.content}\n\n"
            f"Blue's defense:\n{defense.content}\n\n"
            "Verify if concerns were addressed. Final verdict: PASS or FAIL with reasons."
        )
        verdict = self._invoke(context, red.agent_id, verify_context, role="red")
        outputs.append(verdict)
        total_tokens += verdict.tokens_used
        total_time += verdict.time_seconds
        if context.on_round:
            context.on_round(3, verdict)

        # Determine status with robust validation
        verdict_upper = verdict.content.upper()

        # 1. Improved text-based verdict detection
        # Require explicit "VERDICT: PASS" or "PASS" without "FAIL"
        text_passed = (
            "VERDICT: PASS" in verdict_upper or
            ("PASS" in verdict_upper and "FAIL" not in verdict_upper)
        )

        # 2. Artifact verification - check if mentioned files actually exist
        workspace_path = context.blackboard.get("workspace_path", Path.cwd())
        verifier = ArtifactVerifier(Path(workspace_path))
        artifacts_ok, successes, failures = verifier.verify_from_content(defense.content)

        # 3. Combined verdict: PASS only if BOTH text verdict AND artifacts are OK
        passed = text_passed and artifacts_ok

        # 4. Override verdict if false positive detected (text says PASS but artifacts broken)
        final_verdict_content = verdict.content
        if text_passed and not artifacts_ok:
            override_msg = "\n\n[ARTIFACT VERIFICATION FAILED]\n" + "\n".join(failures)
            final_verdict_content = verdict.content + override_msg

        # FIX: Status was always COMPLETED before - now properly set to FAILED if not passed
        status = ExecutionStatus.COMPLETED if passed else ExecutionStatus.FAILED

        return ExecutionResult(
            mode=self.mode,
            status=status,
            final_output=defense.content,  # Defended solution
            agent_outputs=outputs,
            total_rounds=4,
            total_tokens=total_tokens,
            total_time_seconds=total_time,
            metadata={
                "execution_type": "red_blue",
                "verdict": "PASS" if passed else "FAIL",
                "text_verdict": text_passed,
                "artifacts_verified": artifacts_ok,
                "artifact_successes": successes,
                "artifact_failures": failures,
                "verdict_content": final_verdict_content,
                "validation_method": "robust_artifacts"
            }
        )


# Registry of all executors
EXECUTOR_REGISTRY: Dict[CollaborationMode, ModeExecutor] = {
    CollaborationMode.PARALLEL: ParallelExecutor(),
    CollaborationMode.SEQUENTIAL: SequentialExecutor(),
    CollaborationMode.LEAD_SUPPORT: LeadSupportExecutor(),
    CollaborationMode.PING_PONG: PingPongExecutor(),
    CollaborationMode.SPECIALIST: SpecialistExecutor(),
    CollaborationMode.RED_BLUE: RedBlueExecutor(),
}


def get_executor(mode: CollaborationMode, workspace_path: Optional[Path] = None) -> ModeExecutor:
    """
    Get executor for a collaboration mode.

    V7.9: PingPongExecutor now accepts workspace_path for artifact verification.

    Args:
        mode: Collaboration mode
        workspace_path: Optional workspace path for artifact verification

    Returns:
        ModeExecutor instance
    """
    if mode == CollaborationMode.PING_PONG:
        # V7.9: Create new instance with workspace_path for validation
        return PingPongExecutor(workspace_path=workspace_path)
    return EXECUTOR_REGISTRY[mode]
