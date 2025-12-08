"""
NEXUS V8.0 - Phase 7: Knowledge Consolidation

Post-task debate between agents about what to retain.
Implements user's decision: agents debate what knowledge to keep.

Flow:
1. Gemini reflects on task outcome
2. Claude reflects on task outcome
3. Agents debate: What learned? What to keep?
4. User Breakpoint: KNOWLEDGE_CONSOLIDATION
5. Archive decisions to Registry and RAG

Key Innovation:
- Post-task reflection improves future performance
- Agents decide together what's worth keeping
- Patterns/antipatterns extracted for learning
- Spawned agents evaluated for retention
"""

import asyncio
import json
import logging
import re
from typing import List, Dict, Any, Optional, TYPE_CHECKING
from dataclasses import dataclass

from ..types import (
    KnowledgeConsolidation,
    KnowledgeEntry,
    AgentRetention,
    RetentionDecision,
    UserBreakpoint,
)
from ..cost_estimator import CostEstimator
from ..context_manager import HiveMindContextManager
from ..agent_registry import AgentRegistry
from ..user_interaction import UserInteractionHandler

if TYPE_CHECKING:
    from core.drivers.gemini_driver_v7 import GeminiDriverV7
    from core.drivers.claude_driver_v7 import ClaudeDriverV7
    from core.memory.project_memory import ProjectMemory

logger = logging.getLogger(__name__)


# Reflection prompt
REFLECTION_PROMPT = """Reflect on this NEXUS Hive Mind task execution.

TASK: {task}

EXECUTION SUMMARY:
- Success: {success}
- Total Duration: {duration:.1f}s
- Steps Completed: {steps_completed}
- Issues Encountered: {issues_count}

APPROACH USED: {approach}

AGENTS USED: {agents_used}
AGENTS SPAWNED: {agents_spawned}

Reflect on:
1. What worked well?
2. What could be improved?
3. What patterns should be remembered?
4. What mistakes should be avoided?
5. Should spawned agents be kept?

Respond in JSON format:
{{
    "learned_patterns": ["pattern1", "pattern2", ...],
    "learned_antipatterns": ["avoid1", "avoid2", ...],
    "new_capabilities_identified": ["cap1", "cap2", ...],
    "agents_to_retain": [
        {{"agent_id": "agent1", "reason": "why keep", "vote": "KEEP_PERMANENT|ARCHIVE_KNOWLEDGE|MERGE_INTO_EXISTING|DELETE"}}
    ],
    "knowledge_to_archive": [
        {{"category": "pattern|antipattern|recipe|insight", "content": "...", "usefulness": 0.0-1.0, "tags": ["tag1", ...]}}
    ],
    "nexus_improvements": ["suggestion1", ...],
    "overall_reflection": "Your thoughts on the task",
    "satisfaction": 0.0 to 1.0
}}
"""

CONSOLIDATION_DEBATE_PROMPT = """You are debating knowledge consolidation with the other agent.

TASK: {task}

YOUR REFLECTION:
{your_reflection}

OTHER AGENT'S REFLECTION:
{other_reflection}

Discuss and propose final consolidation decisions.
Focus on: What should definitely be kept? What's debatable? What should be discarded?

Respond in JSON format:
{{
    "agreed_patterns": ["pattern1", ...],
    "debated_patterns": [{{"pattern": "...", "your_vote": "keep|discard", "reason": "..."}}],
    "agreed_agent_decisions": [{{"agent_id": "...", "decision": "KEEP_PERMANENT|DELETE", "both_agreed": true}}],
    "debated_agent_decisions": [{{"agent_id": "...", "your_vote": "KEEP|DELETE", "reason": "..."}}],
    "final_recommendation": "Overall recommendation for consolidation"
}}
"""


@dataclass
class ConsolidationPhaseResult:
    """Result of Phase 7."""
    consolidation: KnowledgeConsolidation
    gemini_reflection: str
    claude_reflection: str
    user_decision: str
    archived_to_rag: int
    agents_retained: List[str]
    agents_deleted: List[str]


class KnowledgeConsolidationPhase:
    """
    Phase 7: Knowledge Consolidation

    Post-task debate on what to retain.
    """

    def __init__(
        self,
        gemini_driver: "GeminiDriverV7",
        claude_driver: "ClaudeDriverV7",
        cost_estimator: CostEstimator,
        context_manager: HiveMindContextManager,
        agent_registry: AgentRegistry,
        user_handler: UserInteractionHandler,
        project_memory: "ProjectMemory" = None
    ):
        """
        Initialize Phase 7.

        Args:
            gemini_driver: Gemini driver
            claude_driver: Claude driver
            cost_estimator: Cost estimator
            context_manager: Context manager
            agent_registry: Agent registry
            user_handler: User interaction handler
            project_memory: Optional ProjectMemory for RAG archival
        """
        self.gemini = gemini_driver
        self.claude = claude_driver
        self.cost_estimator = cost_estimator
        self.context_manager = context_manager
        self.registry = agent_registry
        self.user_handler = user_handler
        self.project_memory = project_memory

    async def execute(
        self,
        task: str,
        success: bool,
        duration: float,
        steps_completed: int,
        issues_count: int,
        approach: str,
        agents_used: List[str],
        agents_spawned: List[str]
    ) -> ConsolidationPhaseResult:
        """
        Execute Phase 7: Knowledge Consolidation.

        Args:
            task: Original task
            success: Whether task succeeded
            duration: Total execution duration
            steps_completed: Number of steps completed
            issues_count: Number of issues encountered
            approach: Approach used
            agents_used: Agents that were used
            agents_spawned: Agents that were spawned

        Returns:
            ConsolidationPhaseResult with decisions
        """
        logger.info("Phase 7: Starting Knowledge Consolidation")

        # Check budget
        if not self.cost_estimator.can_afford_multiple({
            "reflection_gemini": 1,
            "reflection_claude": 1,
            "decide_retention": 1,
            "consolidate": 1
        }):
            logger.warning("Limited budget for consolidation")
            return self._create_minimal_result(task, success)

        # Get reflections in parallel
        reflection_prompt = REFLECTION_PROMPT.format(
            task=task,
            success="Yes" if success else "No",
            duration=duration,
            steps_completed=steps_completed,
            issues_count=issues_count,
            approach=approach,
            agents_used=", ".join(agents_used),
            agents_spawned=", ".join(agents_spawned) or "None"
        )

        gemini_task = self._reflect_with_gemini(reflection_prompt)
        claude_task = self._reflect_with_claude(reflection_prompt)

        gemini_result, claude_result = await asyncio.gather(
            gemini_task,
            claude_task,
            return_exceptions=True
        )

        # Handle errors
        if isinstance(gemini_result, Exception):
            gemini_result = f"Reflection failed: {gemini_result}"
        if isinstance(claude_result, Exception):
            claude_result = f"Reflection failed: {claude_result}"

        # Debate consolidation decisions
        consolidation = await self._debate_consolidation(
            task=task,
            gemini_reflection=gemini_result,
            claude_reflection=claude_result,
            success=success
        )

        # User breakpoint
        user_response = self.user_handler.knowledge_consolidation(
            learned_patterns=consolidation.learned_patterns,
            agents_to_retain=[
                {
                    "agent_id": ar.agent_id,
                    "reason": ar.reason
                }
                for ar in consolidation.agents_retention
                if ar.decision in (RetentionDecision.KEEP_PERMANENT, RetentionDecision.ARCHIVE_KNOWLEDGE)
            ],
            knowledge_to_archive=[
                ke.content[:100]
                for ke in consolidation.knowledge_to_archive
            ]
        )

        # Apply decisions based on user choice
        agents_retained = []
        agents_deleted = []
        archived_count = 0

        if user_response.chosen_option in ("accept_all", "selective"):
            # Apply agent retention decisions
            agents_retained, agents_deleted = self._apply_agent_decisions(
                consolidation.agents_retention
            )

            # Archive knowledge to RAG
            archived_count = self._archive_knowledge(
                consolidation.knowledge_to_archive,
                task
            )

            # Add insights to context manager
            for pattern in consolidation.learned_patterns:
                self.context_manager.add_insight(
                    category="pattern",
                    content=pattern,
                    tags=["hive_mind", "learned"]
                )

            for antipattern in consolidation.learned_antipatterns:
                self.context_manager.add_insight(
                    category="antipattern",
                    content=antipattern,
                    tags=["hive_mind", "avoid"]
                )

        # Record costs
        self.cost_estimator.record_cost("decide_retention", 500)
        self.cost_estimator.record_cost("consolidate", 300)

        return ConsolidationPhaseResult(
            consolidation=consolidation,
            gemini_reflection=gemini_result,
            claude_reflection=claude_result,
            user_decision=user_response.chosen_option,
            archived_to_rag=archived_count,
            agents_retained=agents_retained,
            agents_deleted=agents_deleted
        )

    async def _reflect_with_gemini(self, prompt: str) -> str:
        """Get reflection from Gemini."""
        try:
            response = await self.gemini.send_message_async(prompt)
            tokens = len(response) // 4
            self.cost_estimator.record_cost("reflection_gemini", tokens)
            return response
        except Exception as e:
            logger.error(f"Gemini reflection failed: {e}")
            raise

    async def _reflect_with_claude(self, prompt: str) -> str:
        """Get reflection from Claude."""
        try:
            response = await self.claude.send_message_async(prompt)
            tokens = len(response) // 4
            self.cost_estimator.record_cost("reflection_claude", tokens)
            return response
        except Exception as e:
            logger.error(f"Claude reflection failed: {e}")
            raise

    async def _debate_consolidation(
        self,
        task: str,
        gemini_reflection: str,
        claude_reflection: str,
        success: bool
    ) -> KnowledgeConsolidation:
        """Debate and finalize consolidation decisions."""
        # Parse reflections
        gemini_data = self._parse_reflection(gemini_reflection)
        claude_data = self._parse_reflection(claude_reflection)

        # Merge learned patterns (union)
        all_patterns = list(set(
            gemini_data.get("learned_patterns", []) +
            claude_data.get("learned_patterns", [])
        ))

        all_antipatterns = list(set(
            gemini_data.get("learned_antipatterns", []) +
            claude_data.get("learned_antipatterns", [])
        ))

        all_capabilities = list(set(
            gemini_data.get("new_capabilities_identified", []) +
            claude_data.get("new_capabilities_identified", [])
        ))

        # Merge agent retention decisions
        agent_decisions = self._merge_agent_decisions(
            gemini_data.get("agents_to_retain", []),
            claude_data.get("agents_to_retain", [])
        )

        # Merge knowledge to archive
        knowledge_entries = self._merge_knowledge_entries(
            gemini_data.get("knowledge_to_archive", []),
            claude_data.get("knowledge_to_archive", [])
        )

        # Merge improvement suggestions
        all_improvements = list(set(
            gemini_data.get("nexus_improvements", []) +
            claude_data.get("nexus_improvements", [])
        ))

        # Calculate satisfaction
        gemini_satisfaction = gemini_data.get("satisfaction", 0.5)
        claude_satisfaction = claude_data.get("satisfaction", 0.5)

        return KnowledgeConsolidation(
            learned_patterns=all_patterns,
            learned_antipatterns=all_antipatterns,
            new_capabilities_identified=all_capabilities,
            agents_retention=agent_decisions,
            knowledge_to_archive=knowledge_entries,
            tools_to_create=[],  # Future feature
            nexus_improvements=all_improvements,
            task_success=success,
            confidence_in_decisions=(gemini_satisfaction + claude_satisfaction) / 2,
            gemini_reflection=gemini_data.get("overall_reflection", ""),
            claude_reflection=claude_data.get("overall_reflection", "")
        )

    def _parse_reflection(self, response: str) -> Dict[str, Any]:
        """Parse reflection JSON from response."""
        json_match = re.search(r'\{[\s\S]*\}', response)
        if not json_match:
            return {}

        try:
            return json.loads(json_match.group())
        except json.JSONDecodeError:
            return {}

    def _merge_agent_decisions(
        self,
        gemini_decisions: List[Dict],
        claude_decisions: List[Dict]
    ) -> List[AgentRetention]:
        """Merge agent retention decisions from both agents."""
        decisions_by_agent = {}

        # Process Gemini's decisions
        for d in gemini_decisions:
            agent_id = d.get("agent_id")
            if agent_id:
                vote = d.get("vote", "DELETE")
                try:
                    retention = RetentionDecision(vote)
                except ValueError:
                    retention = RetentionDecision.DELETE

                decisions_by_agent[agent_id] = {
                    "gemini_vote": retention,
                    "claude_vote": None,
                    "reason": d.get("reason", "")
                }

        # Process Claude's decisions
        for d in claude_decisions:
            agent_id = d.get("agent_id")
            if agent_id:
                vote = d.get("vote", "DELETE")
                try:
                    retention = RetentionDecision(vote)
                except ValueError:
                    retention = RetentionDecision.DELETE

                if agent_id in decisions_by_agent:
                    decisions_by_agent[agent_id]["claude_vote"] = retention
                else:
                    decisions_by_agent[agent_id] = {
                        "gemini_vote": None,
                        "claude_vote": retention,
                        "reason": d.get("reason", "")
                    }

        # Create final decisions
        results = []
        for agent_id, data in decisions_by_agent.items():
            gemini_vote = data.get("gemini_vote") or RetentionDecision.DELETE
            claude_vote = data.get("claude_vote") or RetentionDecision.DELETE

            # If both agree, use that decision
            if gemini_vote == claude_vote:
                final_decision = gemini_vote
            # If one says keep and other says delete, default to keep
            elif gemini_vote != RetentionDecision.DELETE and claude_vote == RetentionDecision.DELETE:
                final_decision = gemini_vote
            elif claude_vote != RetentionDecision.DELETE and gemini_vote == RetentionDecision.DELETE:
                final_decision = claude_vote
            else:
                # Different keep types - use most conservative (ARCHIVE)
                final_decision = RetentionDecision.ARCHIVE_KNOWLEDGE

            results.append(AgentRetention(
                agent_id=agent_id,
                decision=final_decision,
                reason=data.get("reason", ""),
                gemini_vote=gemini_vote,
                claude_vote=claude_vote
            ))

        return results

    def _merge_knowledge_entries(
        self,
        gemini_entries: List[Dict],
        claude_entries: List[Dict]
    ) -> List[KnowledgeEntry]:
        """Merge knowledge entries from both agents."""
        entries = []

        for e in gemini_entries + claude_entries:
            entries.append(KnowledgeEntry(
                category=e.get("category", "insight"),
                content=e.get("content", ""),
                source_task="hive_mind",
                usefulness_score=float(e.get("usefulness", 0.5)),
                tags=e.get("tags", [])
            ))

        # Deduplicate by content similarity (simple)
        seen_content = set()
        unique_entries = []
        for e in entries:
            content_key = e.content[:50].lower()
            if content_key not in seen_content:
                seen_content.add(content_key)
                unique_entries.append(e)

        return unique_entries

    def _apply_agent_decisions(
        self,
        decisions: List[AgentRetention]
    ) -> tuple[List[str], List[str]]:
        """Apply agent retention decisions to registry."""
        retained = []
        deleted = []

        for decision in decisions:
            if decision.decision == RetentionDecision.DELETE:
                # Deactivate in registry
                self.registry.deactivate_agent(
                    decision.agent_id,
                    reason=decision.reason
                )
                deleted.append(decision.agent_id)
            else:
                # Update usage (mark as retained)
                self.registry.record_usage(decision.agent_id, success=True)
                retained.append(decision.agent_id)

        return retained, deleted

    def _archive_knowledge(
        self,
        entries: List[KnowledgeEntry],
        task: str
    ) -> int:
        """Archive knowledge entries to RAG."""
        if not self.project_memory:
            # Fall back to context manager
            for entry in entries:
                self.context_manager.add_insight(
                    category=entry.category,
                    content=entry.content,
                    tags=entry.tags
                )
            return len(entries)

        archived = 0
        for entry in entries:
            try:
                doc_content = f"""
# Hive Mind Knowledge: {entry.category}

Task Context: {task[:100]}...

{entry.content}

Usefulness: {entry.usefulness_score:.0%}
Tags: {', '.join(entry.tags)}
"""
                if hasattr(self.project_memory, 'add_document'):
                    self.project_memory.add_document(
                        content=doc_content,
                        metadata={
                            "type": "hive_mind_knowledge",
                            "category": entry.category,
                            "tags": entry.tags
                        }
                    )
                    archived += 1

            except Exception as e:
                logger.warning(f"Failed to archive knowledge: {e}")

        return archived

    def _create_minimal_result(
        self,
        task: str,
        success: bool
    ) -> ConsolidationPhaseResult:
        """Create minimal result when budget is limited."""
        return ConsolidationPhaseResult(
            consolidation=KnowledgeConsolidation(
                learned_patterns=[],
                learned_antipatterns=[],
                new_capabilities_identified=[],
                agents_retention=[],
                knowledge_to_archive=[],
                tools_to_create=[],
                nexus_improvements=[],
                task_success=success,
                confidence_in_decisions=0.3,
                gemini_reflection="Budget limited",
                claude_reflection="Budget limited"
            ),
            gemini_reflection="Budget limited",
            claude_reflection="Budget limited",
            user_decision="skip",
            archived_to_rag=0,
            agents_retained=[],
            agents_deleted=[]
        )
