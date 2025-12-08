"""
NEXUS V8.0 - Hive Mind Context Manager

Sliding window context management to prevent token explosion.
Maintains essential context while discarding old/irrelevant information.

Integration with ProjectMemory RAG:
- Important insights are indexed for long-term retrieval
- Context can be enriched from RAG before operations

Usage:
    manager = HiveMindContextManager(max_tokens=30000)

    # Add to context
    manager.add_analysis("gemini", analysis_dict)
    manager.add_debate_turn(debate_argument)

    # Get context for an operation
    context = manager.get_context_for("debate", max_tokens=8000)

    # Archive important insights to RAG
    manager.archive_to_rag(project_memory, session_id)
"""

import logging
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, TYPE_CHECKING
from datetime import datetime
from enum import Enum
from collections import deque

if TYPE_CHECKING:
    from core.memory.project_memory import ProjectMemory

logger = logging.getLogger(__name__)


class ContextPriority(Enum):
    """Priority levels for context items."""
    CRITICAL = 4  # Never evict (task definition, final decisions)
    HIGH = 3      # Evict last (current analysis, active debate)
    MEDIUM = 2    # Standard eviction (historical debate turns)
    LOW = 1       # Evict first (verbose tool outputs, logs)


@dataclass
class ContextItem:
    """A single item in the context window."""
    category: str  # "analysis", "debate", "execution", "diagnosis", etc.
    source: str    # "gemini", "claude", "system", "tool"
    content: str
    priority: ContextPriority = ContextPriority.MEDIUM
    timestamp: datetime = field(default_factory=datetime.now)
    token_estimate: int = 0
    metadata: Dict = field(default_factory=dict)

    def __post_init__(self):
        if self.token_estimate == 0:
            # Rough estimate: ~4 chars per token
            self.token_estimate = len(self.content) // 4


@dataclass
class ContextSnapshot:
    """Snapshot of context for a specific operation."""
    items: List[ContextItem]
    total_tokens: int
    categories_included: List[str]
    truncated: bool = False


class HiveMindContextManager:
    """
    Manages context window for Hive Mind operations.

    Uses a sliding window with priority-based eviction:
    - CRITICAL items never evicted
    - Older LOW priority items evicted first
    - Maintains coherence by keeping related items together
    """

    # Token budgets by operation type
    OPERATION_BUDGETS = {
        "analysis": 10000,      # Independent analysis
        "debate": 8000,         # Each debate turn
        "architecture": 6000,   # Architecture generation
        "execution": 5000,      # Execution context
        "diagnosis": 12000,     # Failure diagnosis (needs more context)
        "consolidation": 15000, # Knowledge consolidation
        "default": 8000,
    }

    def __init__(self, max_tokens: int = 50000):
        """
        Initialize context manager.

        Args:
            max_tokens: Maximum total tokens to maintain
        """
        self.max_tokens = max_tokens
        self._items: deque[ContextItem] = deque()
        self._current_tokens = 0
        self._archived_insights: List[Dict] = []  # Insights to index in RAG

    @property
    def current_tokens(self) -> int:
        """Get current token count."""
        return self._current_tokens

    @property
    def available_tokens(self) -> int:
        """Get available token space."""
        return max(0, self.max_tokens - self._current_tokens)

    def add_item(
        self,
        category: str,
        source: str,
        content: str,
        priority: ContextPriority = ContextPriority.MEDIUM,
        metadata: Dict = None
    ):
        """
        Add an item to context.

        Args:
            category: Item category (analysis, debate, etc.)
            source: Source agent/system
            content: Content text
            priority: Priority level
            metadata: Additional metadata
        """
        item = ContextItem(
            category=category,
            source=source,
            content=content,
            priority=priority,
            metadata=metadata or {}
        )

        # Evict if needed before adding
        while self._current_tokens + item.token_estimate > self.max_tokens:
            if not self._evict_one():
                # Can't evict anything, truncate new item
                logger.warning(
                    f"Cannot fit item ({item.token_estimate} tokens), "
                    f"truncating content"
                )
                # Truncate to fit
                available = self.max_tokens - self._current_tokens
                if available > 100:
                    ratio = available / item.token_estimate
                    new_len = int(len(item.content) * ratio * 0.9)
                    item.content = item.content[:new_len] + "... [truncated]"
                    item.token_estimate = available
                else:
                    logger.error("No space for item even after truncation")
                    return
                break

        self._items.append(item)
        self._current_tokens += item.token_estimate
        logger.debug(
            f"Added context item: {category}/{source} "
            f"({item.token_estimate} tokens, total: {self._current_tokens})"
        )

    def _evict_one(self) -> bool:
        """
        Evict one item based on priority and age.

        Returns:
            True if an item was evicted, False if nothing to evict
        """
        # Find lowest priority, oldest item
        candidates = []
        for i, item in enumerate(self._items):
            if item.priority != ContextPriority.CRITICAL:
                candidates.append((i, item))

        if not candidates:
            return False

        # Sort by priority (ascending), then age (oldest first)
        candidates.sort(key=lambda x: (x[1].priority.value, x[1].timestamp))

        # Remove the best candidate
        idx, item = candidates[0]
        del self._items[idx]
        self._current_tokens -= item.token_estimate

        logger.debug(
            f"Evicted context item: {item.category}/{item.source} "
            f"(priority: {item.priority.name}, {item.token_estimate} tokens)"
        )
        return True

    # Convenience methods for common operations

    def add_task(self, task: str):
        """Add task definition (CRITICAL priority)."""
        self.add_item(
            category="task",
            source="user",
            content=task,
            priority=ContextPriority.CRITICAL,
            metadata={"type": "task_definition"}
        )

    def add_analysis(self, agent_id: str, analysis: Dict):
        """Add independent analysis result."""
        content = self._format_analysis(analysis)
        self.add_item(
            category="analysis",
            source=agent_id,
            content=content,
            priority=ContextPriority.HIGH,
            metadata={"agent": agent_id, "type": "independent_analysis"}
        )

    def add_debate_turn(self, turn_number: int, agent_id: str, argument: str):
        """Add a debate turn."""
        # Earlier turns get lower priority
        priority = ContextPriority.HIGH if turn_number >= 3 else ContextPriority.MEDIUM
        self.add_item(
            category="debate",
            source=agent_id,
            content=f"[Turn {turn_number}] {argument}",
            priority=priority,
            metadata={"turn": turn_number, "agent": agent_id}
        )

    def add_execution_result(self, step_name: str, result: str, success: bool):
        """Add execution step result."""
        priority = ContextPriority.MEDIUM if success else ContextPriority.HIGH
        self.add_item(
            category="execution",
            source="system",
            content=f"[{step_name}] {'SUCCESS' if success else 'FAILED'}: {result}",
            priority=priority,
            metadata={"step": step_name, "success": success}
        )

    def add_diagnosis(self, agent_id: str, diagnosis: str):
        """Add failure diagnosis (HIGH priority for debugging)."""
        self.add_item(
            category="diagnosis",
            source=agent_id,
            content=diagnosis,
            priority=ContextPriority.HIGH,
            metadata={"agent": agent_id, "type": "diagnosis"}
        )

    def add_insight(self, category: str, content: str, tags: List[str] = None):
        """
        Add a learned insight (will be archived to RAG).

        Args:
            category: Insight category (pattern, antipattern, recipe, etc.)
            content: The insight content
            tags: Tags for indexing
        """
        self.add_item(
            category="insight",
            source="hive_mind",
            content=content,
            priority=ContextPriority.MEDIUM,
            metadata={"insight_category": category, "tags": tags or []}
        )
        # Queue for RAG archival
        self._archived_insights.append({
            "category": category,
            "content": content,
            "tags": tags or [],
            "timestamp": datetime.now().isoformat()
        })

    def get_context_for(
        self,
        operation: str,
        max_tokens: int = None,
        include_categories: List[str] = None,
        exclude_categories: List[str] = None
    ) -> ContextSnapshot:
        """
        Get context snapshot for a specific operation.

        Args:
            operation: Operation type (analysis, debate, etc.)
            max_tokens: Max tokens (defaults to operation budget)
            include_categories: Only include these categories
            exclude_categories: Exclude these categories

        Returns:
            ContextSnapshot with relevant items
        """
        budget = max_tokens or self.OPERATION_BUDGETS.get(
            operation,
            self.OPERATION_BUDGETS["default"]
        )

        # Filter items
        filtered = []
        for item in self._items:
            if include_categories and item.category not in include_categories:
                continue
            if exclude_categories and item.category in exclude_categories:
                continue
            filtered.append(item)

        # Sort by priority (descending) then recency
        filtered.sort(
            key=lambda x: (-x.priority.value, x.timestamp),
            reverse=True
        )

        # Select items within budget
        selected = []
        total = 0
        truncated = False

        for item in filtered:
            if total + item.token_estimate <= budget:
                selected.append(item)
                total += item.token_estimate
            else:
                truncated = True

        # Sort selected by timestamp for chronological order
        selected.sort(key=lambda x: x.timestamp)

        categories = list(set(item.category for item in selected))

        return ContextSnapshot(
            items=selected,
            total_tokens=total,
            categories_included=categories,
            truncated=truncated
        )

    def get_full_context_string(self, operation: str = "default") -> str:
        """Get context as a formatted string."""
        snapshot = self.get_context_for(operation)
        lines = []

        current_category = None
        for item in snapshot.items:
            if item.category != current_category:
                current_category = item.category
                lines.append(f"\n=== {current_category.upper()} ===")
            lines.append(f"[{item.source}] {item.content}")

        if snapshot.truncated:
            lines.append("\n[Context truncated due to token limit]")

        return "\n".join(lines)

    def _format_analysis(self, analysis: Dict) -> str:
        """Format analysis dict as string."""
        parts = []
        if "task_understanding" in analysis:
            parts.append(f"Understanding: {analysis['task_understanding']}")
        if "complexity_assessment" in analysis:
            parts.append(f"Complexity: {analysis['complexity_assessment']}")
        if "proposed_approach" in analysis:
            parts.append(f"Approach: {analysis['proposed_approach']}")
        if "required_capabilities" in analysis:
            caps = ", ".join(analysis["required_capabilities"])
            parts.append(f"Capabilities: {caps}")
        if "potential_risks" in analysis:
            risks = ", ".join(analysis["potential_risks"])
            parts.append(f"Risks: {risks}")
        if "confidence" in analysis:
            parts.append(f"Confidence: {analysis['confidence']:.1%}")
        if "reasoning" in analysis:
            parts.append(f"Reasoning: {analysis['reasoning']}")
        return "\n".join(parts)

    # RAG Integration

    def archive_to_rag(
        self,
        project_memory: "ProjectMemory",
        session_id: str
    ) -> int:
        """
        Archive accumulated insights to ProjectMemory RAG.

        Args:
            project_memory: ProjectMemory instance
            session_id: Current session identifier

        Returns:
            Number of insights archived
        """
        if not self._archived_insights:
            return 0

        archived = 0
        for insight in self._archived_insights:
            try:
                # Create a document for the insight
                doc_content = f"""
# Hive Mind Insight: {insight['category']}

{insight['content']}

Tags: {', '.join(insight['tags'])}
Session: {session_id}
Timestamp: {insight['timestamp']}
"""
                # Use project_memory's add_document if available
                if hasattr(project_memory, 'add_document'):
                    project_memory.add_document(
                        content=doc_content,
                        metadata={
                            "type": "hive_mind_insight",
                            "category": insight['category'],
                            "tags": insight['tags'],
                            "session": session_id
                        }
                    )
                    archived += 1
                    logger.info(
                        f"Archived insight to RAG: {insight['category']}"
                    )
            except Exception as e:
                logger.warning(f"Failed to archive insight: {e}")

        # Clear archived insights
        self._archived_insights.clear()
        return archived

    def get_pending_insights(self) -> List[Dict]:
        """Get insights pending RAG archival."""
        return self._archived_insights.copy()

    # State management

    def clear(self, keep_critical: bool = True):
        """
        Clear context.

        Args:
            keep_critical: Whether to keep CRITICAL items
        """
        if keep_critical:
            critical = [
                item for item in self._items
                if item.priority == ContextPriority.CRITICAL
            ]
            self._items = deque(critical)
            self._current_tokens = sum(item.token_estimate for item in critical)
        else:
            self._items.clear()
            self._current_tokens = 0

    def get_stats(self) -> Dict:
        """Get context statistics."""
        category_counts = {}
        priority_counts = {p.name: 0 for p in ContextPriority}

        for item in self._items:
            category_counts[item.category] = category_counts.get(item.category, 0) + 1
            priority_counts[item.priority.name] += 1

        return {
            "total_items": len(self._items),
            "total_tokens": self._current_tokens,
            "max_tokens": self.max_tokens,
            "utilization_percent": round(
                self._current_tokens / self.max_tokens * 100, 1
            ),
            "category_counts": category_counts,
            "priority_counts": priority_counts,
            "pending_insights": len(self._archived_insights)
        }
