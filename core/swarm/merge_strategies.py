"""
Parallel Merge Strategies for NEXUS V8.3.3

Strategies for intelligently merging results from PARALLEL mode execution.

Available strategies:
- NAIVE: Simple concatenation (backward compatible, default)
- DEDUPLICATE: Remove semantically similar sentences
- WEIGHTED: Prioritize by domain fit scores from TaskAnalysis

Future strategies (require LLM):
- CONSENSUS: LLM identifies agreements/conflicts
- SUMMARY: LLM synthesizes into coherent summary
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, TYPE_CHECKING
from enum import Enum
import re
import os

from ..agents.unified_registry import get_registry  # V8.4.0

if TYPE_CHECKING:
    from .mode_executors import AgentResponse


class MergeStrategyType(Enum):
    """Available merge strategies for PARALLEL mode"""
    NAIVE = "naive"              # Current behavior (backward compat)
    DEDUPLICATE = "deduplicate"  # Remove semantic duplicates
    WEIGHTED = "weighted"        # Weight by domain fit scores
    # Future: requires LLM invocation
    # CONSENSUS = "consensus"    # LLM identifies agreements/conflicts
    # SUMMARY = "summary"        # LLM synthesizes into coherent summary


@dataclass
class MergeContext:
    """
    Context available to merge strategies.

    Contains all information needed to intelligently merge parallel outputs.

    Attributes:
        task_input: The original task input string.
        outputs: List of agent responses to be merged.
        task_analysis: Optional dictionary containing task analysis data.
        agent_assignments: Optional list of agent assignments.
    """
    task_input: str
    outputs: List["AgentResponse"]
    task_analysis: Optional[Dict[str, Any]] = None  # From blackboard
    agent_assignments: Optional[List[Any]] = None   # AgentAssignment list


@dataclass
class MergeResult:
    """
    Result of a merge operation.

    Contains the merged content and metadata about the merge process.

    Attributes:
        content: The merged string content.
        strategy_used: The type of strategy used for the merge.
        metadata: Additional metadata about the merge result.
    """
    content: str
    strategy_used: MergeStrategyType
    metadata: Dict[str, Any] = field(default_factory=dict)


class MergeStrategy(ABC):
    """
    Base class for merge strategies.

    Subclasses implement different algorithms for combining
    parallel agent outputs into a single coherent result.
    """

    @property
    @abstractmethod
    def strategy_type(self) -> MergeStrategyType:
        """Gets the strategy type enum value.

        Returns:
            MergeStrategyType: The enum value corresponding to this strategy.
        """
        pass

    @abstractmethod
    def merge(self, context: MergeContext) -> MergeResult:
        """
        Merge parallel outputs according to this strategy.

        Args:
            context: MergeContext with outputs and metadata

        Returns:
            MergeResult with merged content and strategy metadata
        """
        pass

    def _get_agent_name(self, agent_id: str) -> str:
        """Extracts the display name from an agent ID using the registry.

        Retrieves the user-friendly display name for a given agent ID by consulting
        the unified agent registry.

        Args:
            agent_id: The unique identifier of the agent.

        Returns:
            The display name of the agent associated with the provided ID.
        """
        registry = get_registry()
        return registry.get_display_name(agent_id)


class NaiveMergeStrategy(MergeStrategy):
    """
    Naive merge: concatenate outputs with separators.

    This is the V8.3.2 behavior, preserved for backward compatibility.
    Simple but may result in redundant or contradictory content.
    """

    @property
    def strategy_type(self) -> MergeStrategyType:
        """Gets the strategy type for this strategy.

        Returns:
            MergeStrategyType: The NAIVE strategy type.
        """
        return MergeStrategyType.NAIVE

    def merge(self, context: MergeContext) -> MergeResult:
        """Merges outputs by simple concatenation.

        Combines the content from all agent outputs into a single string, separated
        by a delimiter. Error statuses are formatted distinctively.

        Args:
            context: The merge context containing agent outputs and metadata.

        Returns:
            A MergeResult object containing the concatenated string and metadata
            about the operation (agent count, total characters).
        """
        merged_parts = []

        for output in context.outputs:
            agent_name = self._get_agent_name(output.agent_id)
            if output.status == "error":
                merged_parts.append(
                    f"[{agent_name}] ❌ Error:\n{output.error or output.content}"
                )
            else:
                merged_parts.append(f"[{agent_name}]:\n{output.content}")

        return MergeResult(
            content="\n\n---\n\n".join(merged_parts),
            strategy_used=self.strategy_type,
            metadata={
                "agent_count": len(context.outputs),
                "total_chars": sum(len(o.content) for o in context.outputs)
            }
        )


class DeduplicateMergeStrategy(MergeStrategy):
    """
    Deduplicate merge: remove semantically similar sentences.

    Uses Jaccard similarity on word sets to identify duplicates.
    Keeps the first occurrence of each unique point.
    """

    # Minimum similarity threshold for considering sentences as duplicates
    SIMILARITY_THRESHOLD = 0.6

    @property
    def strategy_type(self) -> MergeStrategyType:
        """Gets the strategy type for this strategy.

        Returns:
            MergeStrategyType: The DEDUPLICATE strategy type.
        """
        return MergeStrategyType.DEDUPLICATE

    def merge(self, context: MergeContext) -> MergeResult:
        """Merges outputs while removing semantically duplicate sentences.

        Processes outputs to extract sentences, identifies duplicates using Jaccard
        similarity, and reconstructs the content with duplicates removed.
        Preserves the first occurrence of unique information.

        Args:
            context: The merge context containing agent outputs and metadata.

        Returns:
            A MergeResult object containing the deduplicated content and metadata
            about the operation (duplicate count, dedup ratio).
        """
        # Collect all sentences with their source
        all_sentences: List[tuple] = []  # (sentence, agent_name, output_idx)

        for idx, output in enumerate(context.outputs):
            if output.status == "error":
                continue
            agent_name = self._get_agent_name(output.agent_id)
            sentences = self._split_into_sentences(output.content)
            for sentence in sentences:
                if sentence.strip():
                    all_sentences.append((sentence.strip(), agent_name, idx))

        # Deduplicate using Jaccard similarity
        unique_sentences: List[tuple] = []
        duplicates_removed = 0

        for sentence, agent, idx in all_sentences:
            is_duplicate = False
            sentence_words = self._get_word_set(sentence)

            for existing, _, _ in unique_sentences:
                existing_words = self._get_word_set(existing)
                similarity = self._jaccard_similarity(sentence_words, existing_words)
                if similarity >= self.SIMILARITY_THRESHOLD:
                    is_duplicate = True
                    duplicates_removed += 1
                    break

            if not is_duplicate:
                unique_sentences.append((sentence, agent, idx))

        # Group by agent for organized output
        agent_sentences: Dict[str, List[str]] = {}
        for sentence, agent, _ in unique_sentences:
            if agent not in agent_sentences:
                agent_sentences[agent] = []
            agent_sentences[agent].append(sentence)

        # Build merged output
        merged_parts = []
        for agent, sentences in agent_sentences.items():
            merged_parts.append(f"[{agent}]:\n" + " ".join(sentences))

        # Add error outputs at the end
        for output in context.outputs:
            if output.status == "error":
                agent_name = self._get_agent_name(output.agent_id)
                merged_parts.append(
                    f"[{agent_name}] ❌ Error:\n{output.error or output.content}"
                )

        return MergeResult(
            content="\n\n---\n\n".join(merged_parts),
            strategy_used=self.strategy_type,
            metadata={
                "agent_count": len(context.outputs),
                "original_sentences": len(all_sentences),
                "unique_sentences": len(unique_sentences),
                "duplicates_removed": duplicates_removed,
                "dedup_ratio": round(
                    duplicates_removed / max(len(all_sentences), 1), 2
                )
            }
        )

    def _split_into_sentences(self, text: str) -> List[str]:
        """Splits text into a list of sentences.

        Uses regular expressions to split text based on common sentence-ending
        punctuation marks (.!?) and newlines.

        Args:
            text: The input text to split.

        Returns:
            A list of non-empty strings, where each string is a sentence or line.
        """
        # Split on sentence-ending punctuation followed by space or newline
        sentences = re.split(r'(?<=[.!?])\s+', text)
        # Also split on newlines for list items
        result = []
        for s in sentences:
            result.extend(s.split('\n'))
        return [s.strip() for s in result if s.strip()]

    def _get_word_set(self, text: str) -> set:
        """Extracts a set of significant words from text.

        Tokenizes the text into lowercase words and filters out short words
        (length <= 2) to focus on significant content words.

        Args:
            text: The input text to process.

        Returns:
            A set of strings containing the unique, significant words found in the text.
        """
        words = re.findall(r'\b\w+\b', text.lower())
        # Filter out very short words (articles, etc.)
        return set(w for w in words if len(w) > 2)

    def _jaccard_similarity(self, set1: set, set2: set) -> float:
        """Calculates the Jaccard similarity coefficient between two sets.

        The Jaccard index is computed as the size of the intersection divided by
        the size of the union of the sample sets.

        Args:
            set1: The first set of elements.
            set2: The second set of elements.

        Returns:
            A float between 0.0 and 1.0 representing the similarity, where 1.0
            indicates identical sets. Returns 0.0 if both sets are empty.
        """
        if not set1 or not set2:
            return 0.0
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        return intersection / union if union > 0 else 0.0


class WeightedMergeStrategy(MergeStrategy):
    """
    Weighted merge: prioritize outputs by domain fit scores.

    Uses TaskAnalysis fit scores to determine which agent's
    output should be emphasized for the given task domain.
    """

    @property
    def strategy_type(self) -> MergeStrategyType:
        """Gets the strategy type for this strategy.

        Returns:
            MergeStrategyType: The WEIGHTED strategy type.
        """
        return MergeStrategyType.WEIGHTED

    def merge(self, context: MergeContext) -> MergeResult:
        """Merges outputs prioritizing them based on domain fit scores.

        Sorts agent outputs according to their fit scores derived from task
        analysis. Higher-scoring agents appear earlier in the merged result,
        and exceptional scores may trigger visual indicators (e.g., stars).

        Args:
            context: The merge context containing agent outputs and task analysis data.

        Returns:
            A MergeResult object containing the weighted/ordered content and
            metadata about the scoring (primary domain, fit scores).
        """
        # Get fit scores from task_analysis
        gemini_fit = 0.5
        claude_fit = 0.5
        primary_domain = None

        if context.task_analysis:
            gemini_fit = context.task_analysis.get("gemini_fit_score", 0.5)
            claude_fit = context.task_analysis.get("claude_fit_score", 0.5)
            primary_domain = context.task_analysis.get("primary_domain")

        # Sort outputs by fit score (higher first) - V8.4.0: via registry
        registry = get_registry()

        def get_fit_score(output) -> float:
            if registry.is_gemini(output.agent_id):
                return gemini_fit
            elif registry.is_claude(output.agent_id):
                return claude_fit
            return 0.5

        sorted_outputs = sorted(
            context.outputs,
            key=get_fit_score,
            reverse=True
        )

        # Build merged output with fit indicators
        merged_parts = []
        for output in sorted_outputs:
            agent_name = self._get_agent_name(output.agent_id)
            fit_score = get_fit_score(output)

            if output.status == "error":
                merged_parts.append(
                    f"[{agent_name}] ❌ Error:\n{output.error or output.content}"
                )
            else:
                # Add fit indicator for high-scoring agents
                fit_indicator = ""
                if fit_score >= 0.7:
                    fit_indicator = " ⭐ (domain expert)"
                merged_parts.append(
                    f"[{agent_name}{fit_indicator}]:\n{output.content}"
                )

        return MergeResult(
            content="\n\n---\n\n".join(merged_parts),
            strategy_used=self.strategy_type,
            metadata={
                "agent_count": len(context.outputs),
                "primary_domain": primary_domain,
                "gemini_fit_score": gemini_fit,
                "claude_fit_score": claude_fit,
                "lead_agent": sorted_outputs[0].agent_id if sorted_outputs else None
            }
        )


# Strategy registry
_STRATEGY_REGISTRY: Dict[MergeStrategyType, type] = {
    MergeStrategyType.NAIVE: NaiveMergeStrategy,
    MergeStrategyType.DEDUPLICATE: DeduplicateMergeStrategy,
    MergeStrategyType.WEIGHTED: WeightedMergeStrategy,
}


def get_merge_strategy(
    strategy_type: MergeStrategyType = MergeStrategyType.NAIVE
) -> MergeStrategy:
    """
    Factory function for merge strategies.

    Args:
        strategy_type: The type of merge strategy to create

    Returns:
        An instance of the requested merge strategy

    Raises:
        ValueError: If strategy_type is not registered
    """
    if strategy_type not in _STRATEGY_REGISTRY:
        raise ValueError(
            f"Unknown merge strategy: {strategy_type}. "
            f"Available: {list(_STRATEGY_REGISTRY.keys())}"
        )
    return _STRATEGY_REGISTRY[strategy_type]()


def get_default_merge_strategy() -> MergeStrategy:
    """
    Get the default merge strategy based on environment configuration.

    Reads NEXUS_PARALLEL_MERGE_STRATEGY from environment.
    Falls back to NAIVE if not set or invalid.

    Returns:
        MergeStrategy: The default merge strategy instance.
    """
    strategy_name = os.getenv("NEXUS_PARALLEL_MERGE_STRATEGY", "naive").lower()

    try:
        strategy_type = MergeStrategyType(strategy_name)
        return get_merge_strategy(strategy_type)
    except ValueError:
        # Invalid strategy name, fall back to naive
        return NaiveMergeStrategy()
