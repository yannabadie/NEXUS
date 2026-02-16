"""
NEXUS V9.2 - Phase 4: Monitored Execution

Executes the architecture plan with real-time monitoring.
Tracks issues, verifies outputs, and prepares for diagnosis if needed.

V9.2 Enhancement: Session Isolation per Execution Step
- Each execution step gets isolated session
- Context inheritance from Phase 3 via TASK_PLUS_RESULTS scope
- Spawned agent execution uses separate sessions

Flow:
1. Execute each step according to plan (session per step)
2. Monitor for issues (timeout, errors, hallucinations)
3. Verify artifacts created
4. Report step-by-step results
5. If failure detected → Phase 5 (Diagnosis)

Key Features:
- Real-time monitoring with issue detection
- Artifact verification
- Timeout handling per step
- Issue severity classification
- V9.2: Session isolation per execution step
"""

import asyncio
import logging
import time
from typing import List, Dict, Any, Optional, Callable, TYPE_CHECKING
from dataclasses import dataclass, field
from datetime import datetime

from ..types import (
    AgentArchitecture,
    ExecutionStep,
    ExecutionIssue,
    MonitoredStepResult,
    IssueSeverity,
)
from ..cost_estimator import CostEstimator
from ..context_manager import HiveMindContextManager
from ..context_scope import ContextScope
from ..session_integration import HiveMindSessionIntegration, generate_hivemind_task_id
from ..swarm_bridge import SwarmBridge, HivePhase
from core.agents.unified_registry import get_registry  # V8.4.0

# V13.0 CEREBRO LIVE: Telemetry for agent exchanges
from core.events.telemetry_bridge import emit_agent_exchange, emit_agent_speak

if TYPE_CHECKING:
    from core.swarm.session_manager import SwarmSessionManager
    from core.drivers.legacy import GeminiDriverV7
    from core.drivers.claude_driver_v7 import ClaudeDriverV7
    from core.swarm.hybrid_swarm_engine import HybridSwarmEngine

logger = logging.getLogger(__name__)


# Execution prompt template
EXECUTION_PROMPT = """Execute this step for NEXUS Hive Mind.

TASK CONTEXT: {task}

STEP: {step_name}
ACTION: {action}
EXPECTED DURATION: {expected_duration}s

PREVIOUS STEPS:
{previous_results}

Execute this step now. Provide your output and any artifacts created.

Respond in JSON format:
{{
    "status": "success" or "warning" or "error",
    "output": "What you accomplished",
    "artifacts_created": ["file1.py", "dir/file2.ts", ...],
    "issues": [
        {{"type": "issue_type", "severity": "info|warning|error|critical", "details": "..."}}
    ],
    "next_step_ready": true or false,
    "notes": "Any additional notes"
}}
"""


@dataclass
class ExecutionPhaseResult:
    """Result of Phase 4."""
    success: bool
    step_results: List[MonitoredStepResult]
    total_duration: float
    total_tokens: int
    issues: List[ExecutionIssue]
    artifacts_created: List[str]
    needs_diagnosis: bool
    failure_step: Optional[str] = None
    quality_score: float = 0.0  # V12.4: composite reasoning quality (0.0-1.0)


class MonitoredExecutionPhase:
    """
    Phase 4: Monitored Execution

    Executes plan with real-time monitoring and issue detection.
    """

    # Issue detection patterns
    HALLUCINATION_PATTERNS = [
        "I cannot access",
        "file not found",
        "does not exist",
        "no such file",
        "unable to locate",
    ]

    ERROR_PATTERNS = [
        "error:",
        "exception:",
        "failed:",
        "traceback",
        "syntaxerror",
        "typeerror",
    ]

    def __init__(
        self,
        gemini_driver: "GeminiDriverV7",
        claude_driver: "ClaudeDriverV7",
        cost_estimator: CostEstimator,
        context_manager: HiveMindContextManager,
        tool_executor: Callable = None,
        swarm_engine: "HybridSwarmEngine" = None,
        task_id: Optional[str] = None,
        session_manager: Optional["SwarmSessionManager"] = None
    ):
        """
        Initialize Phase 4.

        Args:
            gemini_driver: Gemini driver
            claude_driver: Claude driver
            cost_estimator: Cost estimator
            context_manager: Context manager
            tool_executor: Optional tool execution callback
            swarm_engine: V8.3 - Optional Swarm Engine for delegation
            task_id: V9.2 - Unique task identifier for session isolation
            session_manager: V9.2 - Optional session manager for persistence
        """
        self.gemini = gemini_driver
        self.claude = claude_driver
        self.cost_estimator = cost_estimator
        self.context_manager = context_manager
        self.tool_executor = tool_executor
        # V8.3: SwarmBridge for Dictator Mode delegation
        self.swarm_bridge = None
        if swarm_engine is not None:
            self.swarm_bridge = SwarmBridge(
                swarm_engine=swarm_engine,
                context_manager=context_manager
            )

        # V9.2: Session isolation
        self._task_id = task_id or generate_hivemind_task_id("execution")
        self._session_manager = session_manager
        self._session_integration: Optional[HiveMindSessionIntegration] = None

    async def execute(
        self,
        task: str,
        architecture: AgentArchitecture
    ) -> ExecutionPhaseResult:
        """
        Execute Phase 4: Monitored Execution.

        V9.2: Each step gets an isolated session to prevent context bleeding.

        Args:
            task: Original task
            architecture: Architecture from Phase 3

        Returns:
            ExecutionPhaseResult with all step results
        """
        logger.info(f"Phase 4: Starting Monitored Execution ({len(architecture.execution_plan.steps)} steps)")

        # V9.2: Initialize session integration for this phase
        self._session_integration = HiveMindSessionIntegration(
            task_id=self._task_id,
            phase_name="execution",
            context_manager=self.context_manager,
            session_manager=self._session_manager,
            complexity="MODERATE"
        )
        self._session_integration.set_previous_phase("architecture")

        step_results: List[MonitoredStepResult] = []
        all_issues: List[ExecutionIssue] = []
        all_artifacts: List[str] = []
        total_tokens = 0
        start_time = time.time()

        # Execute each step
        for step in architecture.execution_plan.steps:
            # Check dependencies
            if step.depends_on:
                unmet = [
                    dep for dep in step.depends_on
                    if not self._is_step_complete(dep, step_results)
                ]
                if unmet:
                    logger.warning(f"Step '{step.name}' has unmet dependencies: {unmet}")
                    # Skip or fail based on severity
                    issue = ExecutionIssue(
                        issue_type="dependency_unmet",
                        severity=IssueSeverity.ERROR,
                        details=f"Unmet dependencies: {unmet}",
                        step_name=step.name
                    )
                    all_issues.append(issue)
                    continue

            # Check budget
            if not self.cost_estimator.can_afford("execution_step"):
                logger.warning("Budget exceeded during execution")
                issue = ExecutionIssue(
                    issue_type="budget_exceeded",
                    severity=IssueSeverity.CRITICAL,
                    details="Cannot afford execution step",
                    step_name=step.name
                )
                all_issues.append(issue)
                break

            # Execute step with monitoring
            result = await self._execute_step(
                task=task,
                step=step,
                previous_results=step_results
            )

            step_results.append(result)
            all_issues.extend(result.issues)
            all_artifacts.extend(result.artifacts_created)
            total_tokens += result.tokens_used

            # V12.4: Record tool call for SkillCrystallizer
            try:
                from core.skills.crystallizer import get_crystallizer, ToolCallRecord
                crystallizer = get_crystallizer()
                crystallizer.record(ToolCallRecord(
                    tool_name=step.name,
                    arguments={"agent": step.agent_id, "task": task[:100]},
                    success=result.status == "success",
                    output=result.output[:200] if result.output else "",
                    duration_seconds=result.duration,
                ))
            except Exception:
                pass  # Non-blocking

            # Add to context
            self.context_manager.add_execution_result(
                step.name,
                result.output,
                result.status == "success"
            )

            # V13.0 CEREBRO LIVE: Emit execution step result
            emit_agent_speak(
                step.agent_id,
                f"Step '{step.name}': {result.output[:150]}",
                action_type="EXECUTION"
            )
            emit_agent_exchange(
                step.agent_id, "user",
                f"[{result.status.upper()}] {step.name}",
                exchange_type="execution"
            )

            # Check for critical failure
            critical_issues = [
                i for i in result.issues
                if i.severity == IssueSeverity.CRITICAL
            ]
            if critical_issues:
                logger.error(f"Critical failure in step '{step.name}'")
                return ExecutionPhaseResult(
                    success=False,
                    step_results=step_results,
                    total_duration=time.time() - start_time,
                    total_tokens=total_tokens,
                    issues=all_issues,
                    artifacts_created=all_artifacts,
                    needs_diagnosis=True,
                    failure_step=step.name
                )

        # Determine overall success
        error_count = sum(
            1 for r in step_results
            if r.status == "error"
        )
        success = error_count == 0

        # V12.4: Score reasoning quality via ReasoningQualityScorer
        quality_score = self._score_execution_quality(
            step_results, all_issues, architecture, error_count,
        )

        # V12.4: Check for cognitive degradation
        degradation_detected = False
        try:
            from core.reasoning.cognitive_degradation import get_degradation_detector
            detector = get_degradation_detector()
            for agent_id in {s.agent_id for s in architecture.execution_steps if hasattr(s, 'agent_id')}:
                signal = detector.check_agent(agent_id)
                if signal.degraded:
                    degradation_detected = True
                    all_issues.append(ExecutionIssue(
                        step_name="degradation_check",
                        description=f"Cognitive degradation: {signal.details}",
                        severity=IssueSeverity.WARNING,
                    ))
        except Exception:
            pass  # Degradation detection is advisory, not critical

        # Determine if diagnosis needed (quality-aware)
        needs_diagnosis = (
            not success
            or any(i.severity in (IssueSeverity.ERROR, IssueSeverity.CRITICAL) for i in all_issues)
            or quality_score < 0.4
            or degradation_detected
        )

        total_duration = time.time() - start_time
        logger.info(
            f"Phase 4 Complete: {len(step_results)} steps, "
            f"{error_count} errors, quality={quality_score:.2f}, {total_duration:.1f}s"
        )

        return ExecutionPhaseResult(
            success=success,
            step_results=step_results,
            total_duration=total_duration,
            total_tokens=total_tokens,
            issues=all_issues,
            artifacts_created=all_artifacts,
            needs_diagnosis=needs_diagnosis,
            failure_step=step_results[-1].step_name if not success and step_results else None,
            quality_score=quality_score,
        )

    def _score_execution_quality(
        self,
        step_results: List[MonitoredStepResult],
        issues: List[ExecutionIssue],
        architecture: AgentArchitecture,
        error_count: int,
    ) -> float:
        """
        Score execution quality using ReasoningQualityScorer (V12.4).

        Evaluates:
        - Depth: fraction of planned steps completed successfully
        - Coherence: absence of contradictory/hallucination issues
        - Completeness: fraction of artifacts verified
        - Confidence calibration: low error rate = high calibration

        Records evaluation per agent for DyLAN routing feedback.

        Returns:
            Composite quality score (0.0-1.0)
        """
        if not step_results:
            return 0.0

        planned_steps = len(architecture.execution_plan.steps)
        completed = sum(1 for r in step_results if r.status == "success")
        total = len(step_results)

        # Depth: fraction of planned steps completed
        depth = completed / max(planned_steps, 1)

        # Coherence: penalize hallucination and error issues
        hallucination_count = sum(
            1 for i in issues if i.issue_type == "hallucination"
        )
        error_issues = sum(
            1 for i in issues
            if i.severity in (IssueSeverity.ERROR, IssueSeverity.CRITICAL)
        )
        coherence = max(0.0, 1.0 - (hallucination_count * 0.3) - (error_issues * 0.15))

        # Completeness: fraction of artifacts verified
        verified = sum(1 for r in step_results if r.artifacts_verified)
        completeness = verified / max(total, 1)

        # Composite
        quality = (depth + coherence + completeness) / 3

        # Record per-agent evaluations via ReasoningQualityScorer
        try:
            from core.reasoning.reasoning_quality_scorer import get_quality_scorer
            scorer = get_quality_scorer()
            agents_seen = set()
            for r in step_results:
                if r.agent_id not in agents_seen:
                    agents_seen.add(r.agent_id)
                    agent_success_rate = sum(
                        1 for sr in step_results
                        if sr.agent_id == r.agent_id and sr.status == "success"
                    ) / max(sum(1 for sr in step_results if sr.agent_id == r.agent_id), 1)
                    scorer.record_evaluation(
                        agent_id=r.agent_id,
                        task_domain="execution",
                        depth_score=depth,
                        coherence_score=coherence,
                        completeness_score=completeness,
                        confidence=agent_success_rate,
                        actual_outcome_quality=quality,
                    )
        except Exception as e:
            logger.debug("Quality scorer unavailable: %s", e)

        return round(quality, 4)

    def _is_step_complete(
        self,
        step_name: str,
        results: List[MonitoredStepResult]
    ) -> bool:
        """Check if a step has completed successfully."""
        for result in results:
            if result.step_name == step_name and result.status == "success":
                return True
        return False

    async def _execute_step(
        self,
        task: str,
        step: ExecutionStep,
        previous_results: List[MonitoredStepResult]
    ) -> MonitoredStepResult:
        """Execute a single step with monitoring."""
        logger.info(f"Executing step: {step.name}")

        # V8.3: Check if step should be delegated to Swarm
        if step.swarm_mode and self.swarm_bridge:
            return await self._execute_via_swarm(task, step, previous_results)

        # Format previous results for context
        prev_text = self._format_previous_results(previous_results)

        # Build prompt
        prompt = EXECUTION_PROMPT.format(
            task=task,
            step_name=step.name,
            action=step.action,
            expected_duration=step.expected_duration,
            previous_results=prev_text
        )

        # Select driver (V8.4.0: use registry for agent identification)
        registry = get_registry()
        driver = self.claude if registry.is_claude(step.agent_id) else self.gemini

        # V9.2: Get isolated session for this step's agent
        session_uuid = None
        if self._session_integration:
            # Use step name as role for unique session per step
            session_uuid = self._session_integration.get_agent_session(
                f"{step.agent_id}_{step.name}"
            )
            logger.debug(f"Step '{step.name}' using session {session_uuid[:8] if session_uuid else 'none'}")

        # Execute with timeout
        start_time = time.time()
        issues: List[ExecutionIssue] = []

        try:
            response = await asyncio.wait_for(
                driver.send_message_async(prompt, session_uuid=session_uuid),
                timeout=step.expected_duration * 2  # Allow 2x expected time
            )

            duration = time.time() - start_time

            # Parse response
            result_data = self._parse_execution_response(response)

            # Check for timeout warning
            if duration > step.expected_duration:
                issues.append(ExecutionIssue(
                    issue_type="slow_execution",
                    severity=IssueSeverity.WARNING,
                    details=f"Step took {duration:.1f}s (expected {step.expected_duration}s)",
                    step_name=step.name
                ))

            # Detect hallucinations
            hallucination_issues = self._detect_hallucinations(
                response,
                step.name
            )
            issues.extend(hallucination_issues)

            # Detect errors in output
            error_issues = self._detect_errors(
                result_data.get("output", ""),
                step.name
            )
            issues.extend(error_issues)

            # Add issues from response
            for issue_data in result_data.get("issues", []):
                issues.append(ExecutionIssue(
                    issue_type=issue_data.get("type", "unknown"),
                    severity=IssueSeverity(issue_data.get("severity", "warning")),
                    details=issue_data.get("details", ""),
                    step_name=step.name
                ))

            # Verify artifacts if required
            artifacts = result_data.get("artifacts_created", [])
            artifacts_verified = True
            if step.verification_required and artifacts:
                artifacts_verified = await self._verify_artifacts(artifacts)
                if not artifacts_verified:
                    issues.append(ExecutionIssue(
                        issue_type="artifact_verification_failed",
                        severity=IssueSeverity.ERROR,
                        details=f"Could not verify artifacts: {artifacts}",
                        step_name=step.name
                    ))

            # Record cost
            tokens = len(response) // 4
            self.cost_estimator.record_cost("execution_step", tokens)

            # Determine status
            status = result_data.get("status", "success")
            if issues:
                worst_severity = max(i.severity for i in issues)
                if worst_severity == IssueSeverity.CRITICAL:
                    status = "error"
                elif worst_severity == IssueSeverity.ERROR:
                    status = "error"
                elif worst_severity == IssueSeverity.WARNING:
                    status = "warning"

            return MonitoredStepResult(
                step_name=step.name,
                agent_id=step.agent_id,
                status=status,
                output=result_data.get("output", response[:500]),
                duration=duration,
                expected_duration=step.expected_duration,
                tokens_used=tokens,
                issues=issues,
                artifacts_created=artifacts,
                artifacts_verified=artifacts_verified
            )

        except asyncio.TimeoutError:
            duration = time.time() - start_time
            issues.append(ExecutionIssue(
                issue_type="timeout",
                severity=IssueSeverity.CRITICAL,
                details=f"Step timed out after {duration:.1f}s",
                step_name=step.name
            ))

            return MonitoredStepResult(
                step_name=step.name,
                agent_id=step.agent_id,
                status="error",
                output="Step timed out",
                duration=duration,
                expected_duration=step.expected_duration,
                tokens_used=0,
                issues=issues,
                artifacts_created=[],
                artifacts_verified=False
            )

        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Step execution error: {e}")
            issues.append(ExecutionIssue(
                issue_type="execution_error",
                severity=IssueSeverity.CRITICAL,
                details=str(e),
                step_name=step.name
            ))

            return MonitoredStepResult(
                step_name=step.name,
                agent_id=step.agent_id,
                status="error",
                output=f"Error: {e}",
                duration=duration,
                expected_duration=step.expected_duration,
                tokens_used=0,
                issues=issues,
                artifacts_created=[],
                artifacts_verified=False
            )

    def _format_previous_results(self, results: List[MonitoredStepResult]) -> str:
        """Format previous results for context."""
        if not results:
            return "No previous steps executed"

        lines = []
        for r in results[-3:]:  # Last 3 steps
            status_icon = "✓" if r.status == "success" else "✗" if r.status == "error" else "⚠"
            lines.append(f"{status_icon} {r.step_name}: {r.output[:100]}...")
        return "\n".join(lines)

    def _parse_execution_response(self, response) -> Dict[str, Any]:
        """Parse execution JSON from response."""
        from ..json_parser import parse_json_response

        # Get raw string for fallback
        raw = response
        if isinstance(raw, dict):
            raw = raw.get("content", raw.get("text", str(raw)))
        if not isinstance(raw, str):
            raw = str(raw)

        data = parse_json_response(response, "execution", default=None)
        if data is None:
            return {"output": raw[:500], "status": "success"}
        return data

    def _detect_hallucinations(
        self,
        response: str,
        step_name: str
    ) -> List[ExecutionIssue]:
        """Detect potential hallucinations in response."""
        issues = []
        response_lower = response.lower()

        for pattern in self.HALLUCINATION_PATTERNS:
            if pattern in response_lower:
                issues.append(ExecutionIssue(
                    issue_type="potential_hallucination",
                    severity=IssueSeverity.WARNING,
                    details=f"Response contains '{pattern}' - may indicate hallucination",
                    step_name=step_name
                ))
                break  # One hallucination warning is enough

        return issues

    def _detect_errors(
        self,
        output: str,
        step_name: str
    ) -> List[ExecutionIssue]:
        """Detect errors in output."""
        issues = []
        output_lower = output.lower()

        for pattern in self.ERROR_PATTERNS:
            if pattern in output_lower:
                issues.append(ExecutionIssue(
                    issue_type="error_in_output",
                    severity=IssueSeverity.ERROR,
                    details=f"Output contains error pattern: '{pattern}'",
                    step_name=step_name,
                    error_category=pattern.rstrip(":")
                ))

        return issues

    async def _verify_artifacts(self, artifacts: List[str]) -> bool:
        """
        Verify that artifacts actually exist on filesystem.

        V10 FIX F15: Implements real verification instead of always True.

        Args:
            artifacts: List of artifact paths or descriptors.
                       Supports formats: "file:path", "path", or bare filenames.

        Returns:
            True if ALL artifacts verified, False if ANY missing.
        """
        from pathlib import Path

        if not artifacts:
            return True  # No artifacts to verify

        verified_count = 0
        failed_artifacts = []

        for artifact in artifacts:
            # Normalize artifact path
            if artifact.startswith("file:"):
                path_str = artifact[5:]
            elif artifact.startswith("created:"):
                path_str = artifact[8:]
            else:
                path_str = artifact

            # Skip non-file artifacts (URLs, etc.)
            if path_str.startswith(("http://", "https://", "data:")):
                verified_count += 1
                continue

            # Verify file exists
            try:
                path = Path(path_str)
                if path.exists():
                    verified_count += 1
                    logger.debug(f"Artifact verified: {path_str}")
                else:
                    failed_artifacts.append(path_str)
                    logger.warning(f"Artifact NOT FOUND: {path_str}")
            except Exception as e:
                failed_artifacts.append(f"{path_str} (error: {e})")
                logger.warning(f"Artifact verification error: {path_str} - {e}")

        # Log summary
        if failed_artifacts:
            logger.error(
                f"Artifact verification FAILED: {len(failed_artifacts)}/{len(artifacts)} missing. "
                f"Missing: {failed_artifacts[:5]}{'...' if len(failed_artifacts) > 5 else ''}"
            )
            return False

        logger.info(f"All {verified_count} artifacts verified successfully")
        return True

    def get_execution_summary(self, result: ExecutionPhaseResult) -> Dict[str, Any]:
        """Get a summary of execution for diagnosis."""
        return {
            "success": result.success,
            "total_steps": len(result.step_results),
            "successful_steps": sum(1 for r in result.step_results if r.status == "success"),
            "failed_steps": sum(1 for r in result.step_results if r.status == "error"),
            "total_duration": result.total_duration,
            "total_tokens": result.total_tokens,
            "issues_by_severity": {
                s.value: sum(1 for i in result.issues if i.severity == s)
                for s in IssueSeverity
            },
            "failure_step": result.failure_step,
            "artifacts": result.artifacts_created
        }

    # =========================================================================
    # V8.3: SWARM DELEGATION (Dictator Mode)
    # =========================================================================

    async def _execute_via_swarm(
        self,
        task: str,
        step: ExecutionStep,
        previous_results: List[MonitoredStepResult]
    ) -> MonitoredStepResult:
        """
        Execute a step via SwarmBridge delegation.

        V8.3 Dictator Mode: HiveMind delegates to Swarm for tactical execution.

        Args:
            task: Original task context
            step: Step with swarm_mode set
            previous_results: Previous step results for context

        Returns:
            MonitoredStepResult with Swarm execution results
        """
        from core.swarm.collaboration_modes import CollaborationMode

        logger.info(f"[V8.3 Dictator Mode] Delegating step '{step.name}' to Swarm (mode={step.swarm_mode})")

        start_time = time.time()
        issues: List[ExecutionIssue] = []

        try:
            # Parse Swarm mode
            mode = CollaborationMode.from_string(step.swarm_mode)

            # Build context-enriched task
            prev_text = self._format_previous_results(previous_results)
            enriched_task = f"""Execute this step for NEXUS Hive Mind.

TASK CONTEXT: {task}

STEP: {step.name}
ACTION: {step.action}

PREVIOUS STEPS:
{prev_text}

Execute using {mode.value.upper()} collaboration mode."""

            # Delegate to Swarm via SwarmBridge
            delegation_result = await self.swarm_bridge.delegate(
                task=enriched_task,
                mode=mode,
                phase=HivePhase.EXECUTION,
                context_categories=["task", "architecture", "tools"]
            )

            duration = time.time() - start_time

            # Convert SwarmDelegationResult to MonitoredStepResult
            if delegation_result.success:
                status = "success"
                output = delegation_result.summary or "Swarm execution completed"
            else:
                status = "error"
                output = f"Swarm delegation failed: {', '.join(delegation_result.failure_diagnostics)}"
                for diagnostic in delegation_result.failure_diagnostics:
                    issues.append(ExecutionIssue(
                        issue_type="swarm_delegation_failed",
                        severity=IssueSeverity.ERROR,
                        details=diagnostic,
                        step_name=step.name
                    ))

            # Record fallback chain if any
            if len(delegation_result.fallback_chain) > 1:
                modes_tried = [m.value for m in delegation_result.fallback_chain]
                logger.info(f"Swarm fallback chain: {' → '.join(modes_tried)}")

            # Inject results back into HiveMind context
            self.swarm_bridge.inject_results_into_context(delegation_result)

            # Estimate tokens (rough)
            tokens_used = len(output) // 4 + 100  # Base overhead for Swarm

            return MonitoredStepResult(
                step_name=step.name,
                agent_id=f"swarm:{delegation_result.mode_used.value}",
                status=status,
                output=output,
                duration=duration,
                expected_duration=step.expected_duration,
                tokens_used=tokens_used,
                issues=issues,
                artifacts_created=[],  # Swarm doesn't track artifacts yet
                artifacts_verified=True
            )

        except ValueError as e:
            # Invalid swarm_mode string
            duration = time.time() - start_time
            issues.append(ExecutionIssue(
                issue_type="invalid_swarm_mode",
                severity=IssueSeverity.ERROR,
                details=f"Invalid swarm_mode '{step.swarm_mode}': {e}",
                step_name=step.name
            ))
            return MonitoredStepResult(
                step_name=step.name,
                agent_id="swarm:error",
                status="error",
                output=f"Invalid swarm mode: {step.swarm_mode}",
                duration=duration,
                expected_duration=step.expected_duration,
                tokens_used=0,
                issues=issues,
                artifacts_created=[],
                artifacts_verified=False
            )

        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Swarm delegation error: {e}")
            issues.append(ExecutionIssue(
                issue_type="swarm_exception",
                severity=IssueSeverity.CRITICAL,
                details=str(e),
                step_name=step.name
            ))
            return MonitoredStepResult(
                step_name=step.name,
                agent_id="swarm:error",
                status="error",
                output=f"Swarm delegation error: {e}",
                duration=duration,
                expected_duration=step.expected_duration,
                tokens_used=0,
                issues=issues,
                artifacts_created=[],
                artifacts_verified=False
            )
