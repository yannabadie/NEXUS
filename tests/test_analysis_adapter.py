"""
NEXUS V8.2.0a - AnalysisAdapter Tests

Tests for bidirectional conversion between TaskAnalysis and IndependentAnalysis.
"""

import pytest
import sys
from pathlib import Path
from datetime import datetime

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.adapters import AnalysisAdapter
from core.swarm.task_analyzer import TaskAnalysis, TaskComplexity, TaskDomain
from core.hive_mind.types import IndependentAnalysis


class TestAnalysisAdapter:
    """Tests for AnalysisAdapter bidirectional conversion."""

    def test_import(self):
        """Test that AnalysisAdapter can be imported."""
        assert AnalysisAdapter is not None

    def test_complexity_to_string(self):
        """Test complexity enum to string conversion."""
        result = AnalysisAdapter.complexity_to_string(TaskComplexity.MODERATE)
        assert "moderate" in result.lower()

    def test_string_to_complexity(self):
        """Test string to complexity enum conversion."""
        assert AnalysisAdapter.string_to_complexity("simple task") == TaskComplexity.SIMPLE
        assert AnalysisAdapter.string_to_complexity("Complex multi-step") == TaskComplexity.COMPLEX
        assert AnalysisAdapter.string_to_complexity("EXPERT level") == TaskComplexity.EXPERT
        assert AnalysisAdapter.string_to_complexity("unknown") == TaskComplexity.MODERATE  # Default

    def test_to_task_analysis_basic(self):
        """Test basic HiveMind -> Swarm conversion."""
        hive = IndependentAnalysis(
            agent_id="gemini_primary",
            task_understanding="Implement a login form",
            complexity_assessment="moderate",
            proposed_approach="Use React for frontend",
            required_capabilities=["code_execution", "web_search"],
            potential_risks=["Security issues"],
            confidence=0.8,
            reasoning="Standard web task",
            timestamp=datetime.now()
        )

        result = AnalysisAdapter.to_task_analysis(hive, "Create a login page")

        assert isinstance(result, TaskAnalysis)
        assert result.complexity == TaskComplexity.MODERATE
        assert result.confidence == 0.8
        assert result.raw_input == "Create a login page"
        assert result.requires_web  # Because "web_search" in capabilities

    def test_to_task_analysis_complexity_mapping(self):
        """Test different complexity mappings."""
        test_cases = [
            ("trivial one-liner", TaskComplexity.TRIVIAL),
            ("simple straightforward", TaskComplexity.SIMPLE),
            ("moderate complexity", TaskComplexity.MODERATE),
            ("complex architecture", TaskComplexity.COMPLEX),
            ("expert-level security audit", TaskComplexity.EXPERT),
        ]

        for complexity_str, expected in test_cases:
            hive = IndependentAnalysis(
                agent_id="test",
                task_understanding="test",
                complexity_assessment=complexity_str,
                proposed_approach="test",
                required_capabilities=[],
                potential_risks=[],
                confidence=0.5,
                reasoning="test",
                timestamp=datetime.now()
            )
            result = AnalysisAdapter.to_task_analysis(hive, "test")
            assert result.complexity == expected, f"Failed for '{complexity_str}'"

    def test_to_independent_analysis_basic(self):
        """Test basic Swarm -> HiveMind conversion."""
        swarm = TaskAnalysis(
            complexity=TaskComplexity.COMPLEX,
            domains=[TaskDomain.CODING, TaskDomain.SECURITY],
            primary_domain=TaskDomain.CODING,
            requires_web=True,
            requires_code_execution=True,
            requires_deep_reasoning=True,
            requires_iteration=False,
            gemini_fit_score=0.6,
            claude_fit_score=0.9,
            raw_input="Audit the authentication module",
            confidence=0.85,
            detected_keywords=["audit", "authentication"]
        )

        result = AnalysisAdapter.to_independent_analysis(swarm, "claude_opus")

        assert isinstance(result, IndependentAnalysis)
        assert result.agent_id == "claude_opus"
        assert result.complexity_assessment == "COMPLEX"
        assert result.confidence == 0.85
        assert "web_search" in result.required_capabilities
        assert "deep_reasoning" in result.required_capabilities

    def test_roundtrip_preserves_key_fields(self):
        """Test that roundtrip conversion preserves key fields."""
        original = IndependentAnalysis(
            agent_id="test_agent",
            task_understanding="Fix bug in parser",
            complexity_assessment="moderate",
            proposed_approach="Debug and fix",
            required_capabilities=["debugging"],
            potential_risks=["Regression"],
            confidence=0.75,
            reasoning="Standard bug fix",
            timestamp=datetime.now()
        )

        # HiveMind -> Swarm
        swarm = AnalysisAdapter.to_task_analysis(original, "Fix the parser bug")

        # Swarm -> HiveMind
        recovered = AnalysisAdapter.to_independent_analysis(swarm, "test_agent")

        # Key fields should be preserved (with some transformation)
        assert recovered.confidence == original.confidence
        assert recovered.complexity_assessment == "MODERATE"  # Normalized

    def test_domain_detection(self):
        """Test automatic domain detection."""
        hive = IndependentAnalysis(
            agent_id="test",
            task_understanding="Write unit tests for the API",
            complexity_assessment="moderate",
            proposed_approach="Use pytest",
            required_capabilities=[],
            potential_risks=[],
            confidence=0.5,
            reasoning="test",
            timestamp=datetime.now()
        )

        result = AnalysisAdapter.to_task_analysis(
            hive,
            "Create tests for the REST API endpoints",
            detect_domains=True
        )

        # Should detect TESTING and possibly WEB_INTERACTION
        assert TaskDomain.TESTING in result.domains


class TestSuccessMemoryDecay:
    """Tests for time decay in SuccessMemory."""

    def test_decay_function_exists(self):
        """Test that _apply_time_decay method exists."""
        from core.memory.success_memory import SuccessMemory
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tmp:
            memory = SuccessMemory(Path(tmp))
            assert hasattr(memory, '_apply_time_decay')

    def test_decay_recent_entry(self):
        """Test that recent entries have minimal decay."""
        from core.memory.success_memory import SuccessMemory
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tmp:
            memory = SuccessMemory(Path(tmp))

            # Today's timestamp
            recent = datetime.now().isoformat()
            score = memory._apply_time_decay(1.0, recent)

            # Should be close to 1.0 (minimal decay)
            assert score >= 0.95

    def test_decay_old_entry(self):
        """Test that old entries have significant decay."""
        from core.memory.success_memory import SuccessMemory
        import tempfile
        from pathlib import Path
        from datetime import timedelta

        with tempfile.TemporaryDirectory() as tmp:
            memory = SuccessMemory(Path(tmp))

            # 52 weeks ago
            old = (datetime.now() - timedelta(weeks=52)).isoformat()
            score = memory._apply_time_decay(1.0, old)

            # Should be significantly decayed (around 0.28)
            assert score < 0.35

    def test_decay_invalid_timestamp(self):
        """Test that invalid timestamps return original score."""
        from core.memory.success_memory import SuccessMemory
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tmp:
            memory = SuccessMemory(Path(tmp))

            # Invalid timestamp should return original
            score = memory._apply_time_decay(0.5, "invalid-timestamp")
            assert score == 0.5

    def test_get_best_mode_with_decay(self):
        """Test that get_best_mode_for_similar accepts apply_decay parameter."""
        from core.memory.success_memory import SuccessMemory
        import tempfile
        from pathlib import Path
        import inspect

        with tempfile.TemporaryDirectory() as tmp:
            memory = SuccessMemory(Path(tmp))

            # Check signature includes apply_decay
            sig = inspect.signature(memory.get_best_mode_for_similar)
            assert 'apply_decay' in sig.parameters


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
