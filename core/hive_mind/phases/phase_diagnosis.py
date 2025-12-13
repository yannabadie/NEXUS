"""
NEXUS V8.0 - Phase 5: Failure Diagnosis

Dual-agent failure analysis when execution encounters issues.
Both agents independently diagnose, then synthesize.

Flow:
1. Gemini diagnoses failure
2. Claude diagnoses failure (in parallel)
3. Synthesize diagnoses
4. User Breakpoint: AFTER_DIAGNOSIS
5. Return diagnosis for Phase 6 (Retry)

Key Innovation:
- Dual diagnosis catches more root causes
- Cross-validation reduces misdiagnosis
- User can override or guide retry
"""

import asyncio
import json
import logging
import re
from typing import List, Dict, Any, Optional, TYPE_CHECKING
from dataclasses import dataclass

from ..types import (
    FailureDiagnosis,
    FailureType,
    ExecutionIssue,
    IssueSeverity,
    MonitoredStepResult,
    UserBreakpoint,
    BreakpointOption,
)
from ..cost_estimator import CostEstimator
from ..context_manager import HiveMindContextManager
from ..user_interaction import UserInteractionHandler

if TYPE_CHECKING:
    from core.drivers.gemini_driver_v7 import GeminiDriverV7
    from core.drivers.claude_driver_v7 import ClaudeDriverV7

logger = logging.getLogger(__name__)


# Diagnosis prompt
DIAGNOSIS_PROMPT = """You are diagnosing a failure in NEXUS Hive Mind execution.

TASK: {task}

EXECUTION CONTEXT:
{execution_context}

FAILURE STEP: {failure_step}

ISSUES DETECTED:
{issues}

Analyze the failure and provide diagnosis.

Respond in JSON format:
{{
    "failure_type": "timeout|capability_missing|hallucination|strategy_wrong|tool_error|context_lost|budget_exceeded|unknown",
    "root_cause": "The fundamental cause of failure",
    "contributing_factors": ["factor1", "factor2", ...],
    "evidence": ["evidence1", "evidence2", ...],
    "recommended_changes": [
        "change1",
        "change2",
        ...
    ],
    "missing_capability": "If capability was missing, what was it?",
    "confidence": 0.0 to 1.0,
    "reasoning": "Why you believe this is the root cause"
}}

Be specific. Focus on actionable fixes.
"""

SYNTHESIS_PROMPT = """Synthesize these two diagnoses of a NEXUS execution failure.

TASK: {task}

GEMINI'S DIAGNOSIS:
{gemini_diagnosis}

CLAUDE'S DIAGNOSIS:
{claude_diagnosis}

Create a unified diagnosis that:
1. Identifies the most likely root cause
2. Merges recommended changes (prioritize by likelihood)
3. Notes where agents disagree

Respond in JSON format:
{{
    "failure_type": "timeout|capability_missing|hallucination|strategy_wrong|tool_error|context_lost|budget_exceeded|unknown",
    "root_cause": "The agreed/most likely root cause",
    "contributing_factors": ["factor1", "factor2", ...],
    "evidence": ["evidence1", "evidence2", ...],
    "recommended_changes": ["change1", "change2", ...],
    "confidence": 0.0 to 1.0,
    "agents_agreed": true or false,
    "disagreement_notes": "Where the agents disagreed (if any)"
}}
"""


@dataclass
class DiagnosisPhaseResult:
    """Result of Phase 5."""
    diagnosis: FailureDiagnosis
    gemini_diagnosis: str
    claude_diagnosis: str
    user_decision: str  # "retry", "modify_changes", "escalate", "abort"
    user_modifications: Optional[str] = None


class FailureDiagnosisPhase:
    """
    Phase 5: Failure Diagnosis

    Dual-agent analysis of execution failures.
    """

    def __init__(
        self,
        gemini_driver: "GeminiDriverV7",
        claude_driver: "ClaudeDriverV7",
        cost_estimator: CostEstimator,
        context_manager: HiveMindContextManager,
        user_handler: UserInteractionHandler
    ):
        """
        Initialize Phase 5.

        Args:
            gemini_driver: Gemini driver
            claude_driver: Claude driver
            cost_estimator: Cost estimator
            context_manager: Context manager
            user_handler: User interaction handler
        """
        self.gemini = gemini_driver
        self.claude = claude_driver
        self.cost_estimator = cost_estimator
        self.context_manager = context_manager
        self.user_handler = user_handler

    async def execute(
        self,
        task: str,
        step_results: List[MonitoredStepResult],
        issues: List[ExecutionIssue],
        failure_step: Optional[str],
        session_uuid: str = None  # V10: Session isolation
    ) -> DiagnosisPhaseResult:
        """
        Execute Phase 5: Failure Diagnosis.

        Args:
            task: Original task
            step_results: Results from execution
            issues: Issues detected
            failure_step: Step that failed
            session_uuid: V10 - Session UUID for context isolation

        Returns:
            DiagnosisPhaseResult with diagnosis and user decision
        """
        self._session_uuid = session_uuid  # Store for driver calls
        logger.info("Phase 5: Starting Failure Diagnosis")

        # Check budget
        if not self.cost_estimator.can_afford_multiple({
            "failure_diagnosis_gemini": 1,
            "failure_diagnosis_claude": 1,
            "synthesize_diagnosis": 1
        }):
            logger.warning("Limited budget for diagnosis")

        # Format context
        execution_context = self._format_execution_context(step_results)
        issues_text = self._format_issues(issues)

        # Get diagnoses in parallel
        prompt = DIAGNOSIS_PROMPT.format(
            task=task,
            execution_context=execution_context,
            failure_step=failure_step or "Unknown",
            issues=issues_text
        )

        gemini_task = self._diagnose_with_gemini(prompt)
        claude_task = self._diagnose_with_claude(prompt)

        gemini_result, claude_result = await asyncio.gather(
            gemini_task,
            claude_task,
            return_exceptions=True
        )

        # Handle errors
        if isinstance(gemini_result, Exception):
            gemini_result = f"Diagnosis failed: {gemini_result}"
        if isinstance(claude_result, Exception):
            claude_result = f"Diagnosis failed: {claude_result}"

        # Synthesize diagnoses
        diagnosis = await self._synthesize_diagnoses(
            task=task,
            gemini_diagnosis=gemini_result,
            claude_diagnosis=claude_result
        )

        # Add to context
        self.context_manager.add_diagnosis("gemini", gemini_result)
        self.context_manager.add_diagnosis("claude", claude_result)

        # User breakpoint
        user_response = self.user_handler.after_diagnosis(
            failure_type=diagnosis.failure_type.value,
            root_cause=diagnosis.root_cause,
            recommended_changes=diagnosis.recommended_changes
        )

        return DiagnosisPhaseResult(
            diagnosis=diagnosis,
            gemini_diagnosis=gemini_result,
            claude_diagnosis=claude_result,
            user_decision=user_response.chosen_option,
            user_modifications=user_response.custom_input
        )

    def _format_execution_context(self, results: List[MonitoredStepResult]) -> str:
        """Format execution results for context."""
        lines = []
        for r in results:
            status_icon = "✓" if r.status == "success" else "✗" if r.status == "error" else "⚠"
            lines.append(f"{status_icon} [{r.step_name}] ({r.agent_id})")
            lines.append(f"   Output: {r.output[:200]}...")
            lines.append(f"   Duration: {r.duration:.1f}s (expected {r.expected_duration}s)")
            if r.issues:
                lines.append(f"   Issues: {len(r.issues)}")
        return "\n".join(lines)

    def _format_issues(self, issues: List[ExecutionIssue]) -> str:
        """Format issues for diagnosis."""
        if not issues:
            return "No specific issues detected"

        lines = []
        for i in issues:
            lines.append(f"- [{i.severity.value.upper()}] {i.issue_type}: {i.details}")
        return "\n".join(lines)

    async def _diagnose_with_gemini(self, prompt: str) -> str:
        """Get diagnosis from Gemini."""
        try:
            response = await self.gemini.send_message_async(prompt, session_uuid=self._session_uuid)
            
            # Extract content if response is a dict
            if isinstance(response, dict):
                content = response.get("content", response.get("text", str(response)))
            else:
                content = str(response)
                
            tokens = len(content) // 4
            self.cost_estimator.record_cost("failure_diagnosis_gemini", tokens)
            return content
        except Exception as e:
            logger.error(f"Gemini diagnosis failed: {e}")
            raise

    async def _diagnose_with_claude(self, prompt: str) -> str:
        """Get diagnosis from Claude."""
        try:
            response = await self.claude.send_message_async(prompt, session_uuid=self._session_uuid)
            
            # Extract content if response is a dict
            if isinstance(response, dict):
                content = response.get("content", response.get("text", str(response)))
            else:
                content = str(response)
                
            tokens = len(content) // 4
            self.cost_estimator.record_cost("failure_diagnosis_claude", tokens)
            return content
        except Exception as e:
            logger.error(f"Claude diagnosis failed: {e}")
            raise

    async def _synthesize_diagnoses(
        self,
        task: str,
        gemini_diagnosis: str,
        claude_diagnosis: str
    ) -> FailureDiagnosis:
        """Synthesize two diagnoses into one."""
        prompt = SYNTHESIS_PROMPT.format(
            task=task,
            gemini_diagnosis=gemini_diagnosis,
            claude_diagnosis=claude_diagnosis
        )

        try:
            response = await self.gemini.send_message_async(prompt, session_uuid=self._session_uuid)
            
            # Extract content if response is a dict
            if isinstance(response, dict):
                content = response.get("content", response.get("text", str(response)))
            else:
                content = str(response)
                
            tokens = len(content) // 4
            self.cost_estimator.record_cost("synthesize_diagnosis", tokens)

            # Parse response
            return self._parse_diagnosis_response(
                content,
                gemini_diagnosis,
                claude_diagnosis
            )

        except Exception as e:
            logger.error(f"Synthesis failed: {e}")
            return self._create_fallback_diagnosis(
                gemini_diagnosis,
                claude_diagnosis
            )

    def _parse_diagnosis_response(
        self,
        response: str,
        gemini_diagnosis: str,
        claude_diagnosis: str
    ) -> FailureDiagnosis:
        """Parse synthesis response into FailureDiagnosis."""
        json_match = re.search(r'\{[\s\S]*\}', response)
        if not json_match:
            return self._create_fallback_diagnosis(gemini_diagnosis, claude_diagnosis)

        try:
            data = json.loads(json_match.group())

            # Parse failure type
            failure_type_str = data.get("failure_type", "unknown")
            try:
                failure_type = FailureType(failure_type_str)
            except ValueError:
                failure_type = FailureType.UNKNOWN

            return FailureDiagnosis(
                failure_type=failure_type,
                root_cause=data.get("root_cause", "Unknown"),
                contributing_factors=data.get("contributing_factors", []),
                evidence=data.get("evidence", []),
                recommended_changes=data.get("recommended_changes", []),
                confidence=float(data.get("confidence", 0.5)),
                gemini_diagnosis=gemini_diagnosis,
                claude_diagnosis=claude_diagnosis,
                missing_capability=data.get("missing_capability")
            )

        except json.JSONDecodeError:
            return self._create_fallback_diagnosis(gemini_diagnosis, claude_diagnosis)

    def _create_fallback_diagnosis(
        self,
        gemini_diagnosis: str,
        claude_diagnosis: str
    ) -> FailureDiagnosis:
        """Create fallback diagnosis when parsing fails."""
        return FailureDiagnosis(
            failure_type=FailureType.UNKNOWN,
            root_cause="Could not synthesize diagnoses",
            contributing_factors=["Diagnosis synthesis failed"],
            evidence=[],
            recommended_changes=["Review task and retry manually"],
            confidence=0.3,
            gemini_diagnosis=gemini_diagnosis,
            claude_diagnosis=claude_diagnosis
        )

    def get_retry_recommendations(
        self,
        result: DiagnosisPhaseResult
    ) -> Dict[str, Any]:
        """
        Get recommendations for retry phase.

        Args:
            result: Diagnosis result

        Returns:
            Recommendations for Phase 6
        """
        diagnosis = result.diagnosis

        # Build recommendations based on failure type
        recommendations = {
            "should_retry": result.user_decision == "retry",
            "failure_type": diagnosis.failure_type.value,
            "changes": diagnosis.recommended_changes,
            "confidence": diagnosis.confidence
        }

        # Add specific recommendations by failure type
        if diagnosis.failure_type == FailureType.TIMEOUT:
            recommendations["architecture_changes"] = {
                "increase_timeout": True,
                "simplify_steps": True,
                "parallelize": False
            }

        elif diagnosis.failure_type == FailureType.CAPABILITY_MISSING:
            recommendations["architecture_changes"] = {
                "spawn_specialist": True,
                "capability_needed": diagnosis.missing_capability,
                "fallback_agent": "claude"
            }

        elif diagnosis.failure_type == FailureType.HALLUCINATION:
            recommendations["architecture_changes"] = {
                "add_verification": True,
                "use_tools": True,
                "reduce_ambiguity": True
            }

        elif diagnosis.failure_type == FailureType.STRATEGY_WRONG:
            recommendations["architecture_changes"] = {
                "rethink_approach": True,
                "use_alternative": True,
                "debate_again": diagnosis.confidence < 0.5
            }

        elif diagnosis.failure_type == FailureType.TOOL_ERROR:
            recommendations["architecture_changes"] = {
                "check_prerequisites": True,
                "use_alternative_tool": True,
                "validate_paths": True
            }

        elif diagnosis.failure_type == FailureType.CONTEXT_LOST:
            recommendations["architecture_changes"] = {
                "reduce_context": True,
                "summarize_history": True,
                "fresh_start": diagnosis.confidence > 0.7
            }

        elif diagnosis.failure_type == FailureType.BUDGET_EXCEEDED:
            recommendations["architecture_changes"] = {
                "increase_budget": True,
                "simplify_task": True,
                "skip_optional": True
            }

        # Apply user modifications if any
        if result.user_modifications:
            recommendations["user_override"] = result.user_modifications

        return recommendations
