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
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from enum import Enum
from pathlib import Path

from .collaboration_modes import CollaborationMode
from .mode_selector import AgentAssignment
from ..utils.artifact_verifier import ArtifactVerifier


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
        """Check if agent signals completion"""
        return (
            "FINISHED" in self.content.upper()
            or "DONE" in self.content.upper()
            or self.status == "finished"
        )

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
    """Context for mode execution"""
    task_input: str
    agent_assignments: List[AgentAssignment]
    blackboard: Dict = field(default_factory=dict)
    max_rounds: int = 6
    invoke_agent: Optional[Callable] = None  # Callable[[str, str, str], AgentResponse]
    on_round: Optional[Callable[[int, "AgentResponse"], None]] = None  # V7.5: Streaming callback

    def get_agent_by_role(self, role: str) -> Optional[AgentAssignment]:
        """Get agent assignment by role"""
        for assignment in self.agent_assignments:
            if assignment.role == role:
                return assignment
        return None

    def get_all_agents(self) -> List[AgentAssignment]:
        """Get all agent assignments"""
        return self.agent_assignments


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
        task_context: str
    ) -> AgentResponse:
        """Invoke an agent with task context"""
        if context.invoke_agent is None:
            # Fallback for testing
            return AgentResponse(
                agent_id=agent_id,
                content=f"[Mock response from {agent_id}]",
                status="mock"
            )

        start_time = datetime.now()

        try:
            response = context.invoke_agent(agent_id, "execution", task_context)

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

    def _invoke_with_failover(
        self,
        context: ExecutionContext,
        primary_agent_id: str,
        backup_agent_id: str,
        task_context: str
    ) -> AgentResponse:
        """
        Invoke primary agent, failover to backup if primary fails.

        V7 Enhancement: Resilience when one agent times out or errors.

        Args:
            context: Execution context
            primary_agent_id: First agent to try
            backup_agent_id: Fallback agent if primary fails
            task_context: Task context to send

        Returns:
            AgentResponse from whichever agent succeeded
        """
        # Try primary agent
        response = self._invoke(context, primary_agent_id, task_context)

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
            backup_response = self._invoke(context, backup_agent_id, failover_context)

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


class ParallelExecutor(ModeExecutor):
    """
    Execute agents in parallel with result merging.

    Use case: Independent subtasks, time-critical situations.
    """

    mode = CollaborationMode.PARALLEL

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
        with ThreadPoolExecutor(max_workers=len(tasks)) as executor:
            futures = {
                executor.submit(
                    self._invoke, context, agent_id, task_ctx
                ): agent_id
                for agent_id, task_ctx in tasks
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

        # Merge results
        merged_output = self._merge_outputs(outputs, context.task_input)

        return ExecutionResult(
            mode=self.mode,
            status=ExecutionStatus.COMPLETED,
            final_output=merged_output,
            agent_outputs=outputs,
            total_rounds=1,
            total_tokens=total_tokens,
            total_time_seconds=total_time,
            metadata={"execution_type": "parallel"}
        )

    def _merge_outputs(self, outputs: List[AgentResponse], task: str) -> str:
        """Merge parallel outputs into unified result"""
        merged_parts = []
        for output in outputs:
            if output.status == "error":
                # V7 FIX: Show errors in output so user knows what happened
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
        if first:
            first_context = f"SEQUENTIAL MODE - Phase 1:\n{context.task_input}\n\nYou are first. Provide your analysis/output."
            first_response = self._invoke(context, first.agent_id, first_context)
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
                second_response = self._invoke(context, second.agent_id, second_context)
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
        round_num = 0
        if lead:
            lead_context = f"LEAD_SUPPORT MODE - You are LEAD:\n{context.task_input}\n\nProvide complete solution."
            lead_response = self._invoke(context, lead.agent_id, lead_context)
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
                review_response = self._invoke(context, support.agent_id, review_context)
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
                    revision_response = self._invoke(context, lead.agent_id, revision_context)
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
    """

    mode = CollaborationMode.PING_PONG

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

        outputs: List[AgentResponse] = []
        total_tokens = 0
        total_time = 0.0
        current_idx = 0
        accumulated_context = context.task_input

        for round_num in range(context.max_rounds):
            agent = agents[current_idx % len(agents)]

            round_context = (
                f"PING_PONG MODE - Round {round_num + 1}:\n"
                f"Original task: {context.task_input}\n\n"
                f"Conversation so far:\n{accumulated_context}\n\n"
                "Continue the work. Say 'FINISHED' when task is complete."
            )

            response = self._invoke(context, agent.agent_id, round_context)
            outputs.append(response)
            total_tokens += response.tokens_used
            total_time += response.time_seconds

            # V7.5: Stream round to callback for real-time display
            if context.on_round:
                context.on_round(round_num, response)

            # Update accumulated context
            accumulated_context += f"\n\n[{agent.agent_id} - Round {round_num + 1}]:\n{response.content}"

            # Check for convergence
            if response.is_finished:
                return ExecutionResult(
                    mode=self.mode,
                    status=ExecutionStatus.CONVERGED,
                    final_output=response.content,
                    agent_outputs=outputs,
                    total_rounds=round_num + 1,
                    total_tokens=total_tokens,
                    total_time_seconds=total_time,
                    metadata={"execution_type": "ping_pong", "converged_at": round_num + 1}
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
            metadata={"execution_type": "ping_pong", "max_rounds_reached": True}
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
        backup_agent = self._get_backup_agent(specialist.agent_id)
        response = self._invoke_with_failover(
            context,
            specialist.agent_id,
            backup_agent,
            task_context
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

        # Phase 1: Blue proposes
        propose_context = (
            f"RED_BLUE MODE - You are BLUE (proposer):\n{context.task_input}\n\n"
            "Propose a complete solution. Be thorough as it will be attacked."
        )
        proposal = self._invoke(context, blue.agent_id, propose_context)
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
        attack = self._invoke(context, red.agent_id, attack_context)
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
        defense = self._invoke(context, blue.agent_id, defend_context)
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
        verdict = self._invoke(context, red.agent_id, verify_context)
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


def get_executor(mode: CollaborationMode) -> ModeExecutor:
    """Get executor for a collaboration mode"""
    return EXECUTOR_REGISTRY[mode]
