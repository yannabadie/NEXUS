"""
SuccessMemory - Phase 10a: Auto-Memory Storage

NEXUS V7.6 HIVE MIND - Learning from successful task executions.

This module provides persistent storage for successful Swarm task executions,
enabling NEXUS to remember what worked and apply similar strategies to future tasks.

Storage:
    Uses AtomicJsonStore for thread-safe persistence to workspace/memory/successes.json
    (V7.6 decision: JSON list instead of JSONL for simplicity and thread-safety)

Schema per entry:
    - task_id: Unique task identifier
    - task_hash: Hash of task description (for similarity matching in Phase 10b)
    - description: Original task description (for semantic search)
    - swarm_mode: CollaborationMode used
    - agents_used: List of agent IDs that participated
    - duration_seconds: Total execution time
    - complexity: TaskComplexity level
    - domains: List of detected task domains
    - quality_score: Execution quality (0.0-1.0, if available)
    - timestamp: ISO timestamp of completion

Author: Claude (NEXUS V7.6)
Date: 2025-12-04
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ..utils.atomic_store import AtomicJsonStore


@dataclass
class SuccessEntry:
    """
    A single success record in memory.

    Contains all metadata about a successfully completed Swarm task.
    """
    task_id: str
    task_hash: str
    description: str
    swarm_mode: str
    agents_used: List[str]
    duration_seconds: float
    complexity: str
    domains: List[str]
    quality_score: float
    timestamp: str

    # Optional extended metadata
    primary_domain: Optional[str] = None
    negotiation_turns: Optional[int] = None
    execution_rounds: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON storage."""
        return {
            "task_id": self.task_id,
            "task_hash": self.task_hash,
            "description": self.description,
            "swarm_mode": self.swarm_mode,
            "agents_used": self.agents_used,
            "duration_seconds": round(self.duration_seconds, 2),
            "complexity": self.complexity,
            "domains": self.domains,
            "quality_score": round(self.quality_score, 3),
            "timestamp": self.timestamp,
            "primary_domain": self.primary_domain,
            "negotiation_turns": self.negotiation_turns,
            "execution_rounds": self.execution_rounds
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SuccessEntry":
        """Create from dictionary."""
        return cls(
            task_id=data.get("task_id", ""),
            task_hash=data.get("task_hash", ""),
            description=data.get("description", ""),
            swarm_mode=data.get("swarm_mode", ""),
            agents_used=data.get("agents_used", []),
            duration_seconds=data.get("duration_seconds", 0.0),
            complexity=data.get("complexity", "UNKNOWN"),
            domains=data.get("domains", []),
            quality_score=data.get("quality_score", 0.0),
            timestamp=data.get("timestamp", ""),
            primary_domain=data.get("primary_domain"),
            negotiation_turns=data.get("negotiation_turns"),
            execution_rounds=data.get("execution_rounds")
        )


class SuccessMemory:
    """
    Thread-safe storage for successful Swarm task executions.

    Uses AtomicJsonStore to persist success records for future retrieval.
    Phase 10b will add TF-IDF search over this data.
    Phase 10c will add semantic retrieval with embeddings.

    Attributes:
        filepath: Path to the JSON storage file.
        max_entries: Maximum entries to keep (FIFO eviction).

    Example:
        >>> memory = SuccessMemory(workspace_path=Path("workspace"))
        >>> memory.record_success(task_id, analysis, result)
        >>> entries = memory.get_all()
    """

    DEFAULT_MAX_ENTRIES = 10000

    def __init__(
        self,
        workspace_path: Path,
        max_entries: int = DEFAULT_MAX_ENTRIES
    ) -> None:
        """
        Initialize SuccessMemory.

        Args:
            workspace_path: Path to workspace root.
            max_entries: Maximum entries to store (oldest evicted first).
        """
        self.workspace_path = Path(workspace_path)
        self.max_entries = max_entries

        # Ensure memory directory exists
        memory_dir = self.workspace_path / "memory"
        memory_dir.mkdir(parents=True, exist_ok=True)

        # Initialize atomic store
        self._store = AtomicJsonStore(memory_dir / "successes.json")

    @property
    def filepath(self) -> Path:
        """Return the path to the storage file."""
        return self._store.filepath

    def _compute_task_hash(self, description: str) -> str:
        """
        Compute a hash of the task description.

        Used for quick similarity matching in Phase 10b.
        Normalizes whitespace and case for better matching.

        Args:
            description: Task description text.

        Returns:
            SHA-256 hash (first 16 characters).
        """
        normalized = " ".join(description.lower().split())
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]

    def record_success(
        self,
        task_id: str,
        analysis: Any,  # TaskAnalysis
        result: Any,    # ExecutionResult or SwarmResult
        quality_score: Optional[float] = None
    ) -> SuccessEntry:
        """
        Record a successful task execution.

        Extracts metadata from TaskAnalysis and ExecutionResult,
        then persists to storage.

        Args:
            task_id: Unique task identifier.
            analysis: TaskAnalysis from the Swarm Engine.
            result: ExecutionResult or SwarmResult from execution.
            quality_score: Optional quality score (0.0-1.0).
                          If not provided, estimated from result.

        Returns:
            The created SuccessEntry.
        """
        # Extract task description
        description = getattr(analysis, "raw_input", str(analysis))
        if hasattr(analysis, "raw_input") and analysis.raw_input:
            description = analysis.raw_input

        # Extract complexity
        complexity = "UNKNOWN"
        if hasattr(analysis, "complexity"):
            complexity = (
                analysis.complexity.name
                if hasattr(analysis.complexity, "name")
                else str(analysis.complexity)
            )

        # Extract domains
        domains = []
        if hasattr(analysis, "domains"):
            domains = [
                d.value if hasattr(d, "value") else str(d)
                for d in analysis.domains
            ]

        # Extract primary domain
        primary_domain = None
        if hasattr(analysis, "primary_domain") and analysis.primary_domain:
            primary_domain = (
                analysis.primary_domain.value
                if hasattr(analysis.primary_domain, "value")
                else str(analysis.primary_domain)
            )

        # Extract mode from result
        swarm_mode = "UNKNOWN"
        if hasattr(result, "selected_mode"):
            # SwarmResult
            swarm_mode = (
                result.selected_mode.value
                if hasattr(result.selected_mode, "value")
                else str(result.selected_mode)
            )
        elif hasattr(result, "mode"):
            # ExecutionResult
            swarm_mode = (
                result.mode.value
                if hasattr(result.mode, "value")
                else str(result.mode)
            )

        # Extract agents used
        agents_used = []
        if hasattr(result, "execution_result") and hasattr(result.execution_result, "agent_outputs"):
            # SwarmResult
            agents_used = list(set(
                ao.agent_id for ao in result.execution_result.agent_outputs
            ))
        elif hasattr(result, "agent_outputs"):
            # ExecutionResult
            agents_used = list(set(
                ao.agent_id for ao in result.agent_outputs
            ))

        # Extract duration
        duration = 0.0
        if hasattr(result, "total_time_seconds"):
            duration = result.total_time_seconds

        # Extract execution rounds
        execution_rounds = None
        if hasattr(result, "execution_result") and hasattr(result.execution_result, "total_rounds"):
            execution_rounds = result.execution_result.total_rounds
        elif hasattr(result, "total_rounds"):
            execution_rounds = result.total_rounds

        # Extract negotiation turns
        negotiation_turns = None
        if hasattr(result, "negotiation_result") and result.negotiation_result:
            if hasattr(result.negotiation_result, "total_turns"):
                negotiation_turns = result.negotiation_result.total_turns

        # Estimate quality score if not provided
        if quality_score is None:
            quality_score = self._estimate_quality(result)

        # Create entry
        entry = SuccessEntry(
            task_id=task_id,
            task_hash=self._compute_task_hash(description),
            description=description[:500],  # Truncate very long descriptions
            swarm_mode=swarm_mode,
            agents_used=agents_used,
            duration_seconds=duration,
            complexity=complexity,
            domains=domains,
            quality_score=quality_score,
            timestamp=datetime.now().isoformat(),
            primary_domain=primary_domain,
            negotiation_turns=negotiation_turns,
            execution_rounds=execution_rounds
        )

        # Persist
        self._append_entry(entry)

        return entry

    def _estimate_quality(self, result: Any) -> float:
        """
        Estimate quality score from result.

        Heuristics:
        - COMPLETED status = base 0.7
        - Fewer rounds = higher quality (efficient)
        - No errors = +0.1
        - Agent completion signals = +0.1
        """
        score = 0.5  # Base

        # Check status
        status = None
        if hasattr(result, "status"):
            status = (
                result.status.value
                if hasattr(result.status, "value")
                else str(result.status)
            )

        if status in ("completed", "COMPLETED", "converged", "CONVERGED"):
            score = 0.7

        # Bonus for efficiency (fewer rounds = better)
        rounds = None
        if hasattr(result, "execution_result") and hasattr(result.execution_result, "total_rounds"):
            rounds = result.execution_result.total_rounds
        elif hasattr(result, "total_rounds"):
            rounds = result.total_rounds

        if rounds is not None:
            if rounds <= 2:
                score += 0.15
            elif rounds <= 4:
                score += 0.1
            elif rounds <= 6:
                score += 0.05

        # Check for errors in agent outputs
        agent_outputs = []
        if hasattr(result, "execution_result") and hasattr(result.execution_result, "agent_outputs"):
            agent_outputs = result.execution_result.agent_outputs
        elif hasattr(result, "agent_outputs"):
            agent_outputs = result.agent_outputs

        has_errors = any(
            getattr(ao, "error", None) or getattr(ao, "status", "") == "error"
            for ao in agent_outputs
        )

        if not has_errors and agent_outputs:
            score += 0.1

        return min(1.0, score)

    def _append_entry(self, entry: SuccessEntry) -> None:
        """
        Append entry to storage with FIFO eviction.

        Thread-safe via AtomicJsonStore.
        """
        data = self._store.load_safe({"entries": []})
        entries = data.get("entries", [])

        # Append new entry
        entries.append(entry.to_dict())

        # FIFO eviction if over limit
        if len(entries) > self.max_entries:
            entries = entries[-self.max_entries:]

        # Update metadata
        data["entries"] = entries
        data["_meta"] = {
            "count": len(entries),
            "last_updated": datetime.now().isoformat(),
            "version": "10a"
        }

        self._store.save(data)

    def get_all(self) -> List[SuccessEntry]:
        """
        Get all success entries.

        Returns:
            List of SuccessEntry objects, oldest first.
        """
        data = self._store.load_safe({"entries": []})
        return [
            SuccessEntry.from_dict(e)
            for e in data.get("entries", [])
        ]

    def get_recent(self, limit: int = 10) -> List[SuccessEntry]:
        """
        Get most recent success entries.

        Args:
            limit: Maximum entries to return.

        Returns:
            List of SuccessEntry objects, most recent first.
        """
        entries = self.get_all()
        return list(reversed(entries[-limit:]))

    def get_by_mode(self, mode: str) -> List[SuccessEntry]:
        """
        Get entries filtered by Swarm mode.

        Args:
            mode: CollaborationMode value (e.g., "ping_pong").

        Returns:
            List of matching SuccessEntry objects.
        """
        return [
            e for e in self.get_all()
            if e.swarm_mode.lower() == mode.lower()
        ]

    def get_by_domain(self, domain: str) -> List[SuccessEntry]:
        """
        Get entries filtered by task domain.

        Args:
            domain: TaskDomain value (e.g., "coding").

        Returns:
            List of matching SuccessEntry objects.
        """
        return [
            e for e in self.get_all()
            if domain.lower() in [d.lower() for d in e.domains]
        ]

    # =========================================================================
    # Phase 10b: Similarity Search
    # =========================================================================

    # Basic English stop words for tokenization
    _STOP_WORDS = frozenset({
        "a", "an", "the", "is", "it", "to", "of", "in", "for", "on", "with",
        "and", "or", "but", "this", "that", "be", "are", "was", "were", "been",
        "have", "has", "had", "do", "does", "did", "will", "would", "could",
        "should", "can", "may", "might", "must", "shall", "i", "you", "he",
        "she", "we", "they", "me", "him", "her", "us", "them", "my", "your",
        "his", "its", "our", "their", "what", "which", "who", "whom", "when",
        "where", "why", "how", "all", "each", "every", "both", "few", "more",
        "most", "other", "some", "such", "no", "not", "only", "same", "so",
        "than", "too", "very", "just", "also", "now", "here", "there", "then",
        # French common words
        "le", "la", "les", "un", "une", "des", "de", "du", "et", "est", "en",
        "que", "qui", "dans", "pour", "sur", "avec", "ce", "cette", "ces",
        "je", "tu", "il", "elle", "nous", "vous", "ils", "elles", "mon", "ton",
        "son", "notre", "votre", "leur", "ne", "pas", "plus", "moins"
    })

    def _tokenize(self, text: str) -> set:
        """
        Tokenize text for similarity comparison.

        Normalizes case, removes punctuation, filters stop words.

        Args:
            text: Input text to tokenize.

        Returns:
            Set of normalized tokens.
        """
        # Lowercase and split on whitespace/punctuation
        import re
        tokens = re.findall(r'\b\w+\b', text.lower())

        # Filter stop words and short tokens
        return {
            t for t in tokens
            if t not in self._STOP_WORDS and len(t) > 2
        }

    def _jaccard_similarity(self, set1: set, set2: set) -> float:
        """
        Compute Jaccard similarity between two sets.

        Jaccard = |intersection| / |union|

        Args:
            set1: First set of tokens.
            set2: Second set of tokens.

        Returns:
            Similarity score between 0.0 and 1.0.
        """
        if not set1 or not set2:
            return 0.0

        intersection = len(set1 & set2)
        union = len(set1 | set2)

        return intersection / union if union > 0 else 0.0

    def find_similar_tasks(
        self,
        query: str,
        limit: int = 3,
        min_score: float = 0.1
    ) -> List[Tuple[SuccessEntry, float]]:
        """
        Find tasks similar to the query using Jaccard similarity.

        Phase 10b: Memory-Augmented Mode Selection.

        Uses simple tokenization and Jaccard similarity to find
        previously successful tasks that match the query.

        Args:
            query: Task description to match against.
            limit: Maximum number of results to return.
            min_score: Minimum similarity score (0.0-1.0).

        Returns:
            List of (SuccessEntry, similarity_score) tuples,
            sorted by similarity descending.
        """
        entries = self.get_all()
        if not entries:
            return []

        # Tokenize query
        query_tokens = self._tokenize(query)
        if not query_tokens:
            return []

        # Score all entries
        scored: List[Tuple[SuccessEntry, float]] = []
        for entry in entries:
            entry_tokens = self._tokenize(entry.description)
            score = self._jaccard_similarity(query_tokens, entry_tokens)

            if score >= min_score:
                scored.append((entry, score))

        # Sort by score descending
        scored.sort(key=lambda x: x[1], reverse=True)

        return scored[:limit]

    def _apply_time_decay(
        self,
        score: float,
        timestamp_str: str,
        decay_coefficient: float = 0.004,
        domain_bonus: float = 0.0
    ) -> float:
        """
        Apply exponential time decay to a score based on entry age.

        V8.8: Changed from linear to exponential decay (GROK-002).
        Exponential decay better captures the diminishing relevance of old data
        and allows faster adaptation to evolving task patterns.

        Formula: decayed_score = score * exp(-decay_coefficient * age_days) + domain_bonus

        Decay examples with coefficient=0.004:
        - 1 week old (7d):   0.97x (3% decay)
        - 4 weeks old (28d): 0.89x (11% decay)
        - 12 weeks old (84d): 0.71x (29% decay)
        - 52 weeks old (364d): 0.23x (77% decay)

        Args:
            score: Original score to decay.
            timestamp_str: ISO timestamp string from entry.
            decay_coefficient: Exponential decay rate (default 0.004 per day).
            domain_bonus: Optional bonus for domain matching (0.0-0.3).

        Returns:
            Decayed score (capped at 1.0).
        """
        from math import exp

        try:
            # Parse ISO timestamp
            entry_time = datetime.fromisoformat(timestamp_str)
            now = datetime.now()

            # Calculate age in days
            age_days = max(0, (now - entry_time).days)

            # V8.8: Exponential decay (GROK-002)
            decay_factor = exp(-decay_coefficient * age_days)
            decayed = score * decay_factor + domain_bonus

            return min(1.0, decayed)

        except (ValueError, TypeError):
            # If timestamp parsing fails, return original score
            return score

    def get_best_mode_for_similar(
        self,
        query: str,
        min_similarity: float = 0.2,
        apply_decay: bool = True,
        query_domains: Optional[List[str]] = None,
        domain_boost: float = 0.15
    ) -> Optional[Tuple[str, str, float]]:
        """
        Get the best mode based on similar successful tasks.

        Phase 10b: Memory-augmented mode selection helper.
        V8.1.0: Added time decay - recent successes weighted more heavily.
        V8.8: Added per-domain weighting (GROK-002) - domain-matched entries get boosted.

        Args:
            query: Task description to match.
            min_similarity: Minimum Jaccard score to consider.
            apply_decay: Whether to apply time decay (default True).
            query_domains: Optional list of domains for the query task (e.g., ["coding", "research"]).
                          If provided, entries with matching domains get a score boost.
            domain_boost: Boost amount for domain-matched entries (default 0.15).

        Returns:
            Tuple of (swarm_mode, task_id, similarity_score) or None.
        """
        similar = self.find_similar_tasks(query, limit=5, min_score=min_similarity)
        if not similar:
            return None

        # Find the mode with highest average quality from similar tasks
        mode_scores: Dict[str, List[float]] = {}
        mode_best_match: Dict[str, Tuple[str, float]] = {}

        # Normalize query domains for comparison
        normalized_query_domains = set()
        if query_domains:
            normalized_query_domains = {d.lower() for d in query_domains}

        for entry, similarity in similar:
            mode = entry.swarm_mode
            # Weight by both similarity and quality
            weighted_score = similarity * entry.quality_score

            # V8.8: Calculate domain bonus (GROK-002)
            # Boost if entry domains overlap with query domains
            entry_domain_bonus = 0.0
            if normalized_query_domains and entry.domains:
                entry_domains_lower = {d.lower() for d in entry.domains}
                domain_overlap = len(normalized_query_domains & entry_domains_lower)
                if domain_overlap > 0:
                    # Partial boost for each matching domain
                    entry_domain_bonus = min(domain_boost, domain_boost * domain_overlap / 2)

            # V8.1.0/V8.8: Apply exponential time decay with domain bonus
            if apply_decay:
                weighted_score = self._apply_time_decay(
                    weighted_score,
                    entry.timestamp,
                    domain_bonus=entry_domain_bonus
                )
            else:
                weighted_score = min(1.0, weighted_score + entry_domain_bonus)

            if mode not in mode_scores:
                mode_scores[mode] = []
                mode_best_match[mode] = (entry.task_id, similarity)

            mode_scores[mode].append(weighted_score)

            # Track best matching task per mode
            if similarity > mode_best_match[mode][1]:
                mode_best_match[mode] = (entry.task_id, similarity)

        if not mode_scores:
            return None

        # Find mode with highest average weighted score
        best_mode = max(
            mode_scores.keys(),
            key=lambda m: sum(mode_scores[m]) / len(mode_scores[m])
        )

        task_id, best_similarity = mode_best_match[best_mode]
        return (best_mode, task_id, best_similarity)

    # =========================================================================
    # Phase 10d: Session-Aware Agent Selection
    # =========================================================================

    def get_agent_success_rate(
        self,
        agent_id: str,
        domain: Optional[str] = None
    ) -> Tuple[float, int]:
        """
        Calculate success rate for an agent based on session history.

        Phase 10d: Session-Aware Agent Selection.

        Computes: (successful tasks with agent) / (total tasks with agent)
        Quality-weighted: tasks with quality_score > 0.6 count as success.

        Args:
            agent_id: Agent identifier to lookup.
            domain: Optional domain filter (e.g., "coding", "research").

        Returns:
            Tuple of (success_rate, sample_count).
            success_rate is 0.5 (neutral) if sample_count < 3.
        """
        entries = self.get_all()

        # Filter by domain if specified
        if domain:
            entries = [
                e for e in entries
                if domain.lower() in [d.lower() for d in e.domains]
            ]

        # Filter entries where this agent participated
        agent_entries = [
            e for e in entries
            if agent_id in e.agents_used
        ]

        sample_count = len(agent_entries)

        # Minimum sample threshold to avoid bias
        if sample_count < 3:
            return 0.5, sample_count  # Neutral score

        # Count successes (quality_score > 0.6 = success)
        successes = sum(
            1 for e in agent_entries
            if e.quality_score > 0.6
        )

        success_rate = successes / sample_count
        return success_rate, sample_count

    def get_agent_session_stats(
        self,
        agent_id: str
    ) -> Dict[str, Any]:
        """
        Get comprehensive session statistics for an agent.

        Phase 10d: Detailed metrics for DyLAN integration.

        Args:
            agent_id: Agent identifier.

        Returns:
            Dictionary with success rates by domain, avg quality, etc.
        """
        entries = self.get_all()

        # Filter entries where this agent participated
        agent_entries = [
            e for e in entries
            if agent_id in e.agents_used
        ]

        if not agent_entries:
            return {
                "agent_id": agent_id,
                "total_sessions": 0,
                "global_success_rate": 0.5,
                "avg_quality_score": 0.5,
                "domain_success_rates": {},
                "modes_participated": {}
            }

        # Global metrics
        total = len(agent_entries)
        successes = sum(1 for e in agent_entries if e.quality_score > 0.6)
        avg_quality = sum(e.quality_score for e in agent_entries) / total

        # By domain
        domain_stats: Dict[str, List[float]] = {}
        for entry in agent_entries:
            for domain in entry.domains:
                if domain not in domain_stats:
                    domain_stats[domain] = []
                domain_stats[domain].append(entry.quality_score)

        domain_success_rates = {
            domain: sum(1 for q in scores if q > 0.6) / len(scores)
            for domain, scores in domain_stats.items()
            if len(scores) >= 2  # Min samples
        }

        # By mode
        mode_counts: Dict[str, int] = {}
        for entry in agent_entries:
            mode = entry.swarm_mode
            mode_counts[mode] = mode_counts.get(mode, 0) + 1

        return {
            "agent_id": agent_id,
            "total_sessions": total,
            "global_success_rate": round(successes / total, 3),
            "avg_quality_score": round(avg_quality, 3),
            "domain_success_rates": domain_success_rates,
            "modes_participated": mode_counts
        }

    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about stored successes.

        Returns:
            Dictionary with counts, mode distribution, etc.
        """
        entries = self.get_all()

        if not entries:
            return {
                "total_entries": 0,
                "mode_distribution": {},
                "domain_distribution": {},
                "avg_duration_seconds": 0.0,
                "avg_quality_score": 0.0
            }

        # Mode distribution
        mode_counts: Dict[str, int] = {}
        for e in entries:
            mode_counts[e.swarm_mode] = mode_counts.get(e.swarm_mode, 0) + 1

        # Domain distribution
        domain_counts: Dict[str, int] = {}
        for e in entries:
            for d in e.domains:
                domain_counts[d] = domain_counts.get(d, 0) + 1

        # Averages
        avg_duration = sum(e.duration_seconds for e in entries) / len(entries)
        avg_quality = sum(e.quality_score for e in entries) / len(entries)

        return {
            "total_entries": len(entries),
            "mode_distribution": mode_counts,
            "domain_distribution": domain_counts,
            "avg_duration_seconds": round(avg_duration, 2),
            "avg_quality_score": round(avg_quality, 3)
        }

    def clear(self) -> int:
        """
        Clear all entries.

        Returns:
            Number of entries cleared.
        """
        data = self._store.load_safe({"entries": []})
        count = len(data.get("entries", []))

        self._store.save({
            "entries": [],
            "_meta": {
                "count": 0,
                "last_updated": datetime.now().isoformat(),
                "version": "10a",
                "cleared": True
            }
        })

        return count


# =============================================================================
# V10 PRISM: Multi-Tenant Success Memory Access
# =============================================================================

_default_memory: Optional[SuccessMemory] = None


def get_success_memory(workspace_path: Optional[Path] = None) -> Optional[SuccessMemory]:
    """
    Get the SuccessMemory for the current tenant context.

    V10 PRISM: Returns tenant-scoped instance via ServiceFactory.
    Falls back to global singleton if no context is active.

    Args:
        workspace_path: Required on first call to initialize (legacy mode).

    Returns:
        SuccessMemory instance scoped to current tenant, or None if not initialized.
    """
    # V10: Try ServiceFactory first (tenant-scoped)
    try:
        from ..context import has_active_session
        if has_active_session():
            from ..factory import ServiceFactory
            return ServiceFactory.get_success_memory()
    except ImportError:
        pass  # context module not available, use legacy

    # Legacy fallback: global singleton
    global _default_memory

    if _default_memory is None and workspace_path is not None:
        _default_memory = SuccessMemory(workspace_path)

    return _default_memory


def reset_success_memory() -> None:
    """
    Reset the global SuccessMemory instance (for testing).

    Note: In V10, also clears ServiceFactory cache for current tenant.
    """
    global _default_memory
    _default_memory = None

    # V10: Also clear factory cache
    try:
        from ..context import get_current_session_or_none
        from ..factory import ServiceFactory
        ctx = get_current_session_or_none()
        if ctx:
            ServiceFactory.clear_tenant_cache(ctx.tenant_id)
    except ImportError:
        pass
