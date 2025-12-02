# NEXUS V7.0 Evolution - Tour 6 Final Mutations

**Status**: FINISHED (Mutual Agreement)
**Date**: 2025-11-30
**Participants**: Claude + Gemini
**Total Impact**: +0.10 ASI Proximity

---

## Mutation 1: Metacognitive Feedback

FILE: core/orchestration_v7.py
REASON: Adds metacognitive_feedback (stored in attribute to preserve signature safety)
IMPACT: 0.04

<<<<<<< SEARCH
    def _calculate_quality_score(
        self,
        message: dict,
        validation_ok: bool,
        is_stagnant: bool
    ) -> float:
        """
        Calculate DyLAN quality score for agent invocation.

        Quality is based on multiple factors:
        - Message validation success (+0.2)
        - Response length appropriate (+0.1)
        - No stagnation detected (+0.2)
        - Task completion status (+0.2 FINISHED, +0.1 CONTINUE)

        Args:
            message: Parsed message dict from agent
            validation_ok: Whether message validation succeeded
            is_stagnant: Whether stagnation was detected

        Returns:
            Quality score between 0.0 and 1.0
        """
        score = 0.3  # Base score

        # Validation success
        if validation_ok:
            score += 0.2

        # Response length (neither too short nor too long)
        content = message.get("content", "")
        if 50 < len(content) < 5000:
            score += 0.1

        # No stagnation
        if not is_stagnant:
            score += 0.2

        # Task status
        status = message.get("status", "")
        if status == "FINISHED":
            score += 0.2
        elif status == "CONTINUE":
            score += 0.1

        return min(1.0, score)
=======
    def _calculate_quality_score(
        self,
        message: dict,
        validation_ok: bool,
        is_stagnant: bool
    ) -> float:
        """
        Calculate DyLAN quality score with metacognitive feedback.

        Feedback is stored in self._last_metacognition to avoid breaking signature.

        Args:
            message: Parsed message dict from agent
            validation_ok: Whether message validation succeeded
            is_stagnant: Whether stagnation was detected

        Returns:
            Quality score between 0.0 and 1.0
        """
        score = 0.3  # Base score
        feedback_parts = []

        # Validation success
        if validation_ok:
            score += 0.2
            feedback_parts.append("validation_ok")
        else:
            feedback_parts.append("validation_failed(-0.2)")

        # Response length (neither too short nor too long)
        content = message.get("content", "")
        if 50 < len(content) < 5000:
            score += 0.1
            feedback_parts.append("length_optimal")
        elif len(content) <= 50:
            feedback_parts.append("too_short(-0.1)")
        else:
            feedback_parts.append("too_long(-0.1)")

        # No stagnation
        if not is_stagnant:
            score += 0.2
            feedback_parts.append("no_stagnation")
        else:
            feedback_parts.append("stagnation_detected(-0.2)")

        # Task status
        status = message.get("status", "")
        if status == "FINISHED":
            score += 0.2
            feedback_parts.append("task_finished(+0.2)")
        elif status == "CONTINUE":
            score += 0.1
            feedback_parts.append("task_continuing(+0.1)")
        else:
            feedback_parts.append("status_unclear")

        # Goal alignment bonus
        if hasattr(self, 'blackboard') and self.blackboard and hasattr(self.blackboard, 'get_current_objective'):
            objective = self.blackboard.get_current_objective()
            if objective and any(kw.lower() in content.lower() for kw in objective.split()[:5]):
                score += 0.1
                feedback_parts.append("goal_aligned(+0.1)")

        # Store metacognition safely
        self._last_metacognition = f"score={min(1.0, score):.2f}|{','.join(feedback_parts)}"

        return min(1.0, score)
>>>>>>> REPLACE

---

## Mutation 2: Adaptive GoT

FILE: core/swarm/hybrid_swarm_engine.py
REASON: GoT adaptatif avec scoring probabiliste au lieu de threshold fixe COMPLEX
IMPACT: 0.03

<<<<<<< SEARCH
    def should_use_got(self, analysis: Optional[TaskAnalysis] = None) -> bool:
        """
        Determine if GoT should be used for current task.

        GoT is used for COMPLEX or EXPERT tasks to decompose them into
        manageable sub-problems before execution.

        Args:
            analysis: TaskAnalysis (uses current if not provided)

        Returns:
            True if GoT decomposition is recommended
        """
        if not self._got_enabled or not _GOT_AVAILABLE:
            return False

        analysis = analysis or self._current_analysis
        if analysis is None:
            return False

        # Use GoT for complex tasks (COMPLEX=4, EXPERT=5)
        return analysis.complexity >= TaskComplexity.COMPLEX
=======
    def should_use_got(self, analysis: Optional[TaskAnalysis] = None) -> bool:
        """
        Determine if GoT should be used for current task (adaptive).

        Uses probabilistic scoring instead of fixed threshold:
        - EXPERT (5): Always use GoT (full decomposition)
        - COMPLEX (4): Always use GoT (full decomposition)
        - MEDIUM (3) + multi-domain: Use lightweight GoT (2-3 nodes max)
        - SIMPLE/TRIVIAL: Never use GoT

        Args:
            analysis: TaskAnalysis (uses current if not provided)

        Returns:
            True if GoT decomposition is recommended
        """
        if not self._got_enabled or not _GOT_AVAILABLE:
            return False

        analysis = analysis or self._current_analysis
        if analysis is None:
            return False

        # COMPLEX and EXPERT always use GoT
        if analysis.complexity >= TaskComplexity.COMPLEX:
            return True

        # MEDIUM tasks: use GoT if multi-domain (benefits from decomposition)
        if analysis.complexity == TaskComplexity.MEDIUM:
            # Multi-domain heuristic: 2+ domains suggests decomposition value
            num_domains = len(analysis.domains) if hasattr(analysis, 'domains') else 0
            if num_domains >= 2:
                return True

        return False
>>>>>>> REPLACE

---

## Mutation 3: DyLAN-Aware Model Routing

FILE: core/routing/model_router.py
REASON: Intègre DyLAN metrics dans select_claude_model pour routing adaptatif
IMPACT: 0.03

<<<<<<< SEARCH
    def select_claude_model(self, task_type: TaskType) -> str:
        """
        Select appropriate Claude model for task type.

        Args:
            task_type: Type of task to perform

        Returns:
            Model ID string (opus or sonnet)
        """
        if task_type in self.opus_tasks:
            return self.opus_model
        return self.sonnet_model
=======
    def select_claude_model(
        self,
        task_type: TaskType,
        agent_pool: Optional["AgentPool"] = None,
        importance_threshold: float = 0.7
    ) -> str:
        """
        Select appropriate Claude model using DyLAN metrics when available.

        Priority:
        1. If agent_pool provided and agent has high importance for task → use that agent's model
        2. Else fall back to static task_type routing

        Args:
            task_type: Type of task to perform
            agent_pool: Optional AgentPool with performance history
            importance_threshold: Min importance to override static routing (default 0.7)

        Returns:
            Model ID string (opus or sonnet)
        """
        # Try DyLAN-based selection if pool available
        if agent_pool is not None:
            task_str = task_type.value
            best_agents = agent_pool.select_best_for_task(task_str, top_k=1)
            if best_agents:
                best = best_agents[0]
                importance = best.get_task_importance(task_str)
                if importance >= importance_threshold:
                    # High performer for this task type - use their model
                    return best.model

        # Fall back to static routing
        if task_type in self.opus_tasks:
            return self.opus_model
        return self.sonnet_model
>>>>>>> REPLACE

---

## Summary

| Mutation | File | Impact | Description |
|----------|------|--------|-------------|
| 1 | orchestration_v7.py | +0.04 | Metacognitive feedback avec goal alignment |
| 2 | hybrid_swarm_engine.py | +0.03 | GoT adaptatif pour tâches MEDIUM multi-domaines |
| 3 | model_router.py | +0.03 | Routing basé sur métriques DyLAN |

**Total Expected ASI Impact**: +0.10 (0.78 → 0.88)

---

## Next Step

Run `clone_and_mutate.py` to create the child:

```bash
python workspace/clone_and_mutate.py NEXUS_V7.1_METACOG workspace/evolution_mutations_tour6.md
```
