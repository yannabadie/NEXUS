#!/usr/bin/env python3
"""
NEXUS Learning Engine
Self-improvement system inspired by ACE+COMPASS architecture
Processes CHAT_HISTORY_MASTER.md to extract patterns and improve performance

Based on Stanford ACE framework (arXiv:2510.04618):
- Generator: Creates execution traces from interactions
- Reflector: Extracts insights and patterns
- Curator: Updates playbooks with learned strategies
"""

import json
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum


class PatternType(Enum):
    """Types of patterns we can learn"""
    SUCCESS_STRATEGY = "success_strategy"
    ERROR_PATTERN = "error_pattern"
    OPTIMIZATION = "optimization"
    DOMAIN_INSIGHT = "domain_insight"


@dataclass
class ExecutionTrace:
    """Record of a single Worker execution"""
    timestamp: str
    command: str
    action: str
    status: str  # SUCCESS or FAILURE
    details: str
    duration: Optional[float] = None
    error: Optional[str] = None

    @classmethod
    def from_worker_report(cls, report_text: str) -> 'ExecutionTrace':
        """Parse a [WORKER REPORT] block into ExecutionTrace"""
        # Extract fields using regex
        action_match = re.search(r'Action:\s*(.+)', report_text)
        status_match = re.search(r'Status:\s*(.+)', report_text)
        details_match = re.search(r'Details:\s*(.+)', report_text, re.DOTALL)

        return cls(
            timestamp=datetime.now().isoformat(),
            command="",  # To be filled from context
            action=action_match.group(1) if action_match else "",
            status=status_match.group(1) if status_match else "",
            details=details_match.group(1) if details_match else ""
        )


@dataclass
class LearnedPattern:
    """A pattern extracted from execution history"""
    pattern_type: PatternType
    trigger_context: str  # What situation triggers this pattern
    strategy: str  # What to do
    confidence: float  # 0.0 to 1.0
    success_count: int
    failure_count: int
    last_used: str
    examples: List[str]  # Example executions

    @property
    def success_rate(self) -> float:
        total = self.success_count + self.failure_count
        return self.success_count / total if total > 0 else 0.0


class NexusLearningEngine:
    """
    Self-improvement engine for NEXUS system
    Implements the Generator-Reflector-Curator loop
    """

    def __init__(self, history_path: str = "20_NEXUS/05_LOGS/CHAT_HISTORY_MASTER.md"):
        self.history_path = Path(history_path)
        self.playbook_path = Path("20_NEXUS/04_OUTPUTS/playbooks")
        self.playbook_path.mkdir(parents=True, exist_ok=True)

        # In-memory storage
        self.traces: List[ExecutionTrace] = []
        self.patterns: Dict[str, LearnedPattern] = {}
        self.current_playbook: Dict[str, List[Dict]] = {
            "success_strategies": [],
            "error_patterns": [],
            "optimizations": [],
            "domain_insights": []
        }

        # Learning configuration
        self.min_confidence_threshold = 0.6
        self.min_examples_for_pattern = 3
        self.pattern_decay_rate = 0.95  # Confidence decay per day

    # ==================== GENERATOR PHASE ====================

    def parse_chat_history(self, history_content: str) -> List[ExecutionTrace]:
        """
        Generator Phase: Parse CHAT_HISTORY_MASTER.md into execution traces
        """
        traces = []

        # Find all [WORKER REPORT] blocks
        worker_reports = re.findall(
            r'\[WORKER REPORT\](.*?)(?=\[WORKER REPORT\]|\Z)',
            history_content,
            re.DOTALL
        )

        for report in worker_reports:
            try:
                trace = ExecutionTrace.from_worker_report(report)
                traces.append(trace)
            except Exception as e:
                print(f"[GENERATOR] Failed to parse report: {e}")

        print(f"[GENERATOR] Extracted {len(traces)} execution traces")
        return traces

    # ==================== REFLECTOR PHASE ====================

    def extract_patterns(self, traces: List[ExecutionTrace]) -> List[LearnedPattern]:
        """
        Reflector Phase: Analyze traces to extract patterns
        """
        patterns = []

        # Group traces by action type
        action_groups = {}
        for trace in traces:
            action = trace.action
            if action not in action_groups:
                action_groups[action] = []
            action_groups[action].append(trace)

        # Analyze each action group
        for action, group_traces in action_groups.items():
            if len(group_traces) >= self.min_examples_for_pattern:
                pattern = self._analyze_action_group(action, group_traces)
                if pattern and pattern.confidence >= self.min_confidence_threshold:
                    patterns.append(pattern)

        print(f"[REFLECTOR] Extracted {len(patterns)} patterns")
        return patterns

    def _analyze_action_group(self, action: str, traces: List[ExecutionTrace]) -> Optional[LearnedPattern]:
        """Analyze a group of similar actions to find patterns"""
        success_traces = [t for t in traces if "SUCCESS" in t.status]
        failure_traces = [t for t in traces if "FAILURE" in t.status]

        if not success_traces and not failure_traces:
            return None

        # Determine pattern type
        if len(success_traces) > len(failure_traces):
            pattern_type = PatternType.SUCCESS_STRATEGY
            strategy = self._extract_success_strategy(success_traces)
        else:
            pattern_type = PatternType.ERROR_PATTERN
            strategy = self._extract_error_pattern(failure_traces)

        # Calculate confidence based on consistency
        total = len(traces)
        confidence = max(len(success_traces), len(failure_traces)) / total

        return LearnedPattern(
            pattern_type=pattern_type,
            trigger_context=action,
            strategy=strategy,
            confidence=confidence,
            success_count=len(success_traces),
            failure_count=len(failure_traces),
            last_used=datetime.now().isoformat(),
            examples=[t.details[:100] for t in traces[:3]]  # First 3 examples
        )

    def _extract_success_strategy(self, traces: List[ExecutionTrace]) -> str:
        """Extract common strategy from successful executions"""
        # Find common patterns in successful traces
        common_words = set(traces[0].details.split())
        for trace in traces[1:]:
            common_words &= set(trace.details.split())

        if common_words:
            return f"Common success pattern: {' '.join(list(common_words)[:10])}"
        return "Successful execution pattern detected"

    def _extract_error_pattern(self, traces: List[ExecutionTrace]) -> str:
        """Extract common error pattern from failed executions"""
        # Find common error messages
        errors = [t.error or t.details for t in traces if t.error or "error" in t.details.lower()]
        if errors:
            # Find most common error substring
            return f"Common error: {errors[0][:100]}"
        return "Error pattern detected - needs investigation"

    # ==================== CURATOR PHASE ====================

    def update_playbook(self, patterns: List[LearnedPattern]):
        """
        Curator Phase: Update playbook with new patterns
        """
        for pattern in patterns:
            category = self._get_playbook_category(pattern.pattern_type)

            # Check if pattern already exists
            existing = self._find_similar_pattern(pattern, category)

            if existing:
                # Merge with existing pattern
                self._merge_patterns(existing, pattern)
            else:
                # Add new pattern
                self.current_playbook[category].append({
                    "id": f"pattern_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    "trigger": pattern.trigger_context,
                    "strategy": pattern.strategy,
                    "confidence": pattern.confidence,
                    "success_rate": pattern.success_rate,
                    "examples": pattern.examples,
                    "last_updated": pattern.last_used
                })

        # Prune low-confidence patterns
        self._prune_playbook()

        # Save to disk
        self._save_playbook()

        print(f"[CURATOR] Playbook updated with {len(patterns)} patterns")

    def _get_playbook_category(self, pattern_type: PatternType) -> str:
        """Map pattern type to playbook category"""
        mapping = {
            PatternType.SUCCESS_STRATEGY: "success_strategies",
            PatternType.ERROR_PATTERN: "error_patterns",
            PatternType.OPTIMIZATION: "optimizations",
            PatternType.DOMAIN_INSIGHT: "domain_insights"
        }
        return mapping[pattern_type]

    def _find_similar_pattern(self, pattern: LearnedPattern, category: str) -> Optional[Dict]:
        """Find existing similar pattern in playbook"""
        for existing in self.current_playbook[category]:
            if existing["trigger"] == pattern.trigger_context:
                return existing
        return None

    def _merge_patterns(self, existing: Dict, new: LearnedPattern):
        """Merge new pattern with existing one"""
        # Update confidence using weighted average
        old_weight = existing.get("confidence", 0.5)
        new_weight = new.confidence
        existing["confidence"] = (old_weight * 0.7 + new_weight * 0.3)

        # Update examples
        existing["examples"].extend(new.examples[:2])
        existing["examples"] = existing["examples"][-5:]  # Keep last 5

        # Update timestamp
        existing["last_updated"] = new.last_used

    def _prune_playbook(self):
        """Remove low-confidence or outdated patterns"""
        for category in self.current_playbook:
            self.current_playbook[category] = [
                p for p in self.current_playbook[category]
                if p["confidence"] >= self.min_confidence_threshold
            ]
            # Keep max 50 patterns per category
            self.current_playbook[category] = sorted(
                self.current_playbook[category],
                key=lambda x: x["confidence"],
                reverse=True
            )[:50]

    def _save_playbook(self):
        """Save playbook to disk"""
        playbook_file = self.playbook_path / f"playbook_{datetime.now().strftime('%Y%m%d')}.json"
        with open(playbook_file, 'w', encoding='utf-8') as f:
            json.dump(self.current_playbook, f, indent=2, ensure_ascii=False)
        print(f"[CURATOR] Playbook saved to {playbook_file}")

    # ==================== PUBLIC API ====================

    def learn_from_history(self) -> Dict:
        """
        Main learning loop: Process history and update playbooks
        """
        print("=" * 60)
        print("NEXUS LEARNING ENGINE - Processing History")
        print("=" * 60)

        # Load history
        if not self.history_path.exists():
            print(f"[ERROR] History file not found: {self.history_path}")
            return {"error": "History file not found"}

        with open(self.history_path, 'r', encoding='utf-8') as f:
            history_content = f.read()

        # Generator Phase
        traces = self.parse_chat_history(history_content)
        self.traces.extend(traces)

        # Reflector Phase
        patterns = self.extract_patterns(traces)

        # Curator Phase
        self.update_playbook(patterns)

        # Return summary
        return {
            "traces_processed": len(traces),
            "patterns_extracted": len(patterns),
            "playbook_stats": {
                category: len(items)
                for category, items in self.current_playbook.items()
            }
        }

    def suggest_strategy(self, context: str) -> Optional[Dict]:
        """
        Suggest best strategy for given context based on learned patterns
        """
        best_match = None
        best_score = 0

        for category in self.current_playbook:
            for pattern in self.current_playbook[category]:
                # Simple similarity check (could use embeddings for better matching)
                if pattern["trigger"].lower() in context.lower():
                    score = pattern["confidence"] * pattern.get("success_rate", 0.5)
                    if score > best_score:
                        best_score = score
                        best_match = pattern

        return best_match


# ==================== CLI TEST ====================

def test_learning_engine():
    """Test the learning engine with sample data"""

    # Create sample history
    sample_history = """
[WORKER REPORT]
Action: Creating virtual environment
Status: ✅ SUCCESS
Details: Environment created successfully with UV in 6 seconds

[WORKER REPORT]
Action: Installing dependencies
Status: ✅ SUCCESS
Details: Installed 33 packages including MCP

[WORKER REPORT]
Action: Creating virtual environment
Status: ✅ SUCCESS
Details: Environment created successfully with UV in 5 seconds

[WORKER REPORT]
Action: Running tests
Status: ❌ FAILURE
Details: Import error - wrong module path

[WORKER REPORT]
Action: Running tests
Status: ❌ FAILURE
Details: Import error - module not found

[WORKER REPORT]
Action: Running tests
Status: ✅ SUCCESS
Details: All tests passed after fixing imports
"""

    # Save sample history
    history_path = Path("20_NEXUS/05_LOGS/CHAT_HISTORY_TEST.md")
    history_path.parent.mkdir(parents=True, exist_ok=True)
    with open(history_path, 'w') as f:
        f.write(sample_history)

    # Initialize engine
    engine = NexusLearningEngine(str(history_path))

    # Learn from history
    result = engine.learn_from_history()
    print(f"\nLearning Result: {json.dumps(result, indent=2)}")

    # Test strategy suggestion
    strategy = engine.suggest_strategy("Running tests")
    if strategy:
        print(f"\nSuggested Strategy: {json.dumps(strategy, indent=2)}")

    return engine


if __name__ == "__main__":
    test_learning_engine()