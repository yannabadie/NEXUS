"""
Memory Coordinator - V11.2 MEMORIA

Coordinates SuccessMemory (episodic) and AutoMemory (procedural) for:
1. Unified query interface
2. Conflict resolution
3. Score normalization
4. Consolidation (episodic → procedural)

Design Pattern: Adapter + Facade
- Keeps both memories intact
- Adds coordination without breaking existing code
- Gradual migration path

Architecture:
    ┌─────────────────┐   ┌─────────────────┐
    │  SuccessMemory  │   │   AutoMemory    │
    │  (Episodic)     │   │  (Procedural)   │
    │                 │   │                 │
    │  - Similarity   │   │  - Task type    │
    │  - Time decay   │   │  - Lead/Mode    │
    └────────┬────────┘   └────────┬────────┘
             │                     │
             └──────────┬──────────┘
                        │
              ┌─────────▼─────────┐
              │ MemoryCoordinator │
              │ - Normalize       │
              │ - Weight          │
              │ - Resolve         │
              └─────────┬─────────┘
                        │
              ┌─────────▼─────────┐
              │ UnifiedRec        │
              │ - mode            │
              │ - lead            │
              │ - confidence      │
              │ - source          │
              └───────────────────┘

Author: Claude (NEXUS V11.2 MEMORIA)
Date: 2025-12-15
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .success_memory import SuccessMemory
    from .auto_memory import AutoMemory


class MemorySource(Enum):
    """Which memory provided the recommendation."""
    SUCCESS = "success_memory"      # Episodic (semantic similarity)
    AUTO = "auto_memory"            # Procedural (task type)
    BOTH = "both"                   # Both agree
    NONE = "none"                   # Neither has data


@dataclass
class UnifiedRecommendation:
    """
    Normalized recommendation from unified memory.

    Attributes:
        mode: Recommended swarm mode (or None)
        lead: Recommended lead agent (or None)
        confidence: Normalized 0.0-1.0 confidence score
        source: Which memory provided this recommendation
        modes_to_avoid: List of modes to penalize
        reasoning: Human-readable explanation
    """
    mode: Optional[str]
    lead: Optional[str]
    confidence: float
    source: MemorySource
    modes_to_avoid: List[str]
    reasoning: str

    def to_dict(self) -> Dict:
        """Convert to dictionary for logging/serialization."""
        return {
            "mode": self.mode,
            "lead": self.lead,
            "confidence": round(self.confidence, 3),
            "source": self.source.value,
            "modes_to_avoid": self.modes_to_avoid,
            "reasoning": self.reasoning
        }


class MemoryCoordinator:
    """
    Coordinates SuccessMemory and AutoMemory.

    Query Flow:
    1. Query both memories in parallel (well, sequentially but fast)
    2. Normalize scores to 0-1
    3. Apply weighting (semantic > categorical for specific tasks)
    4. Resolve conflicts
    5. Return UnifiedRecommendation

    Consolidation Flow:
    1. Periodically scan SuccessMemory for patterns
    2. Extract mode/lead success rates by task_type
    3. Log insights (AutoMemory update could be added later)

    Weights:
    - SEMANTIC_WEIGHT (0.6): SuccessMemory similarity-based recommendations
    - PROCEDURAL_WEIGHT (0.4): AutoMemory task-type-based recommendations

    Rationale: Semantic similarity is more specific (finds exact matches),
    while categorical is broader (works with less data).
    """

    # Weights for combining scores
    SEMANTIC_WEIGHT = 0.6      # SuccessMemory (similarity-based)
    PROCEDURAL_WEIGHT = 0.4    # AutoMemory (task-type-based)

    # Thresholds
    MIN_CONFIDENCE = 0.3       # Below this, don't recommend
    HIGH_CONFIDENCE = 0.7      # Above this, strong recommendation

    def __init__(
        self,
        success_memory: Optional['SuccessMemory'],
        auto_memory: Optional['AutoMemory']
    ):
        """
        Initialize the coordinator.

        Args:
            success_memory: SuccessMemory instance (episodic)
            auto_memory: AutoMemory instance (procedural)
        """
        self.success = success_memory
        self.auto = auto_memory
        self._logger = logging.getLogger("nexus.memory.coordinator")

    def get_recommendation(
        self,
        task_description: str,
        task_type: str,
        domains: Optional[List[str]] = None
    ) -> UnifiedRecommendation:
        """
        Get unified recommendation from both memory systems.

        Algorithm:
        1. Query SuccessMemory with semantic similarity
        2. Query AutoMemory with task_type lookup
        3. Normalize and weight scores
        4. Resolve conflicts (if any)
        5. Return unified recommendation

        Args:
            task_description: Full task description for semantic search
            task_type: Task category for categorical lookup (e.g., "coding")
            domains: Optional list of domains for domain boosting

        Returns:
            UnifiedRecommendation with normalized confidence
        """
        self._logger.debug(f"[COORDINATOR] Getting recommendation for task_type={task_type}")

        # 1. Query SuccessMemory (semantic)
        success_rec = None
        success_score = 0.0
        if self.success:
            try:
                result = self.success.get_best_mode_for_similar(
                    query=task_description,
                    min_similarity=0.2,
                    apply_decay=True,
                    query_domains=domains,
                    domain_boost=0.15
                )
                if result:
                    success_rec = {
                        'mode': result[0],
                        'task_id': result[1],
                        'similarity': result[2]
                    }
                    success_score = result[2]  # similarity is 0-1
                    self._logger.debug(
                        f"[COORDINATOR] SuccessMemory: mode={result[0]}, "
                        f"similarity={result[2]:.3f}"
                    )
            except Exception as e:
                self._logger.warning(f"[COORDINATOR] SuccessMemory query failed: {e}")

        # 2. Query AutoMemory (procedural)
        auto_rec = None
        auto_score = 0.0
        if self.auto:
            try:
                result = self.auto.get_recommendation(task_type, task_description)
                if result and result.get('confidence', 0) > 0:
                    auto_rec = result
                    auto_score = result['confidence']  # already 0-1
                    self._logger.debug(
                        f"[COORDINATOR] AutoMemory: mode={result.get('suggested_mode')}, "
                        f"confidence={auto_score:.3f}"
                    )
            except Exception as e:
                self._logger.warning(f"[COORDINATOR] AutoMemory query failed: {e}")

        # 3. Handle cases
        if not success_rec and not auto_rec:
            self._logger.debug("[COORDINATOR] No memory data (cold start)")
            return UnifiedRecommendation(
                mode=None,
                lead=None,
                confidence=0.0,
                source=MemorySource.NONE,
                modes_to_avoid=[],
                reasoning="No memory data available (cold start)"
            )

        # 4. Both have data - combine
        if success_rec and auto_rec:
            return self._combine_recommendations(
                success_rec, success_score,
                auto_rec, auto_score,
                task_description
            )

        # 5. Only one has data
        if success_rec:
            weighted_conf = success_score * self.SEMANTIC_WEIGHT
            return UnifiedRecommendation(
                mode=success_rec['mode'],
                lead=None,
                confidence=weighted_conf,
                source=MemorySource.SUCCESS,
                modes_to_avoid=[],
                reasoning=f"Similar task '{success_rec['task_id'][:20]}...' used {success_rec['mode']}"
            )

        # Only auto_rec
        weighted_conf = auto_score * self.PROCEDURAL_WEIGHT
        return UnifiedRecommendation(
            mode=auto_rec.get('suggested_mode'),
            lead=auto_rec.get('suggested_lead'),
            confidence=weighted_conf,
            source=MemorySource.AUTO,
            modes_to_avoid=auto_rec.get('modes_to_avoid', []),
            reasoning=f"Task type '{task_type}' typically uses {auto_rec.get('suggested_mode')}"
        )

    def _combine_recommendations(
        self,
        success_rec: Dict,
        success_score: float,
        auto_rec: Dict,
        auto_score: float,
        task_description: str
    ) -> UnifiedRecommendation:
        """
        Combine recommendations when both memories have data.

        Conflict Resolution:
        - If both agree: combine confidence scores
        - If they differ: prioritize based on weighted scores
        - Semantic (SuccessMemory) wins ties due to specificity

        Args:
            success_rec: SuccessMemory recommendation dict
            success_score: Raw similarity score (0-1)
            auto_rec: AutoMemory recommendation dict
            auto_score: Raw confidence score (0-1)
            task_description: Original task (for logging)

        Returns:
            UnifiedRecommendation
        """
        success_mode = success_rec['mode']
        auto_mode = auto_rec.get('suggested_mode')

        # Agreement case - both recommend same mode
        if success_mode == auto_mode:
            combined_confidence = (
                success_score * self.SEMANTIC_WEIGHT +
                auto_score * self.PROCEDURAL_WEIGHT
            )
            self._logger.debug(
                f"[COORDINATOR] Agreement: both recommend {success_mode}, "
                f"combined_confidence={combined_confidence:.3f}"
            )
            return UnifiedRecommendation(
                mode=success_mode,
                lead=auto_rec.get('suggested_lead'),
                confidence=min(1.0, combined_confidence),
                source=MemorySource.BOTH,
                modes_to_avoid=auto_rec.get('modes_to_avoid', []),
                reasoning=f"Both memories agree: {success_mode}"
            )

        # Conflict case - different recommendations
        # Prioritize based on weighted scores
        weighted_success = success_score * self.SEMANTIC_WEIGHT
        weighted_auto = auto_score * self.PROCEDURAL_WEIGHT

        self._logger.debug(
            f"[COORDINATOR] Conflict: success={success_mode} ({weighted_success:.3f}) "
            f"vs auto={auto_mode} ({weighted_auto:.3f})"
        )

        if weighted_success >= weighted_auto:
            # Semantic similarity wins (more specific)
            return UnifiedRecommendation(
                mode=success_mode,
                lead=auto_rec.get('suggested_lead'),  # Still use lead from auto
                confidence=weighted_success,
                source=MemorySource.SUCCESS,
                modes_to_avoid=auto_rec.get('modes_to_avoid', []),
                reasoning=f"Semantic match ({success_score:.2f}) beats categorical ({auto_score:.2f})"
            )
        else:
            # Categorical wins (more samples)
            return UnifiedRecommendation(
                mode=auto_mode,
                lead=auto_rec.get('suggested_lead'),
                confidence=weighted_auto,
                source=MemorySource.AUTO,
                modes_to_avoid=auto_rec.get('modes_to_avoid', []),
                reasoning=f"Categorical confidence ({auto_score:.2f}) beats semantic ({success_score:.2f})"
            )

    def consolidate(self) -> int:
        """
        Consolidate episodic patterns into procedural memory.

        Scans SuccessMemory for recurring patterns by domain.
        Logs insights that could be used to update AutoMemory.

        Should be called periodically (e.g., end of session).

        Returns:
            Number of patterns found
        """
        if not self.success:
            return 0

        try:
            entries = self.success.get_all()
        except Exception as e:
            self._logger.warning(f"[CONSOLIDATE] Failed to get entries: {e}")
            return 0

        if len(entries) < 10:
            self._logger.debug("[CONSOLIDATE] Not enough data (<10 entries)")
            return 0

        # Group by primary_domain (task_type equivalent)
        from collections import defaultdict
        by_domain: Dict[str, list] = defaultdict(list)

        for entry in entries:
            domain = entry.primary_domain or (entry.domains[0] if entry.domains else 'general')
            by_domain[domain].append(entry)

        consolidated = 0
        for domain, domain_entries in by_domain.items():
            if len(domain_entries) < 5:
                continue

            # Find most successful mode
            mode_scores: Dict[str, List[float]] = defaultdict(list)
            for entry in domain_entries:
                mode_scores[entry.swarm_mode].append(entry.quality_score)

            if not mode_scores:
                continue

            best_mode = max(
                mode_scores.keys(),
                key=lambda m: sum(mode_scores[m]) / len(mode_scores[m])
            )
            avg_score = sum(mode_scores[best_mode]) / len(mode_scores[best_mode])

            # Log the insight (AutoMemory update could be added here)
            self._logger.info(
                f"[CONSOLIDATE] {domain}: {best_mode} "
                f"(avg={avg_score:.2f}, n={len(mode_scores[best_mode])})"
            )
            consolidated += 1

        return consolidated

    def get_stats(self) -> Dict:
        """
        Get coordinator statistics.

        Returns:
            Dictionary with status of both memories
        """
        stats = {
            "success_memory_available": self.success is not None,
            "auto_memory_available": self.auto is not None,
            "semantic_weight": self.SEMANTIC_WEIGHT,
            "procedural_weight": self.PROCEDURAL_WEIGHT,
        }

        if self.success:
            try:
                sm_stats = self.success.get_stats()
                stats["success_memory_entries"] = sm_stats.get("total_entries", 0)
            except Exception:
                stats["success_memory_entries"] = -1

        if self.auto:
            try:
                am_stats = self.auto.get_stats()
                stats["auto_memory_successes"] = am_stats.get("total_successes", 0)
                stats["auto_memory_failures"] = am_stats.get("total_failures", 0)
            except Exception:
                stats["auto_memory_successes"] = -1

        return stats
