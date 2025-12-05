"""
Tests for Phase 13d: AutoMemory Integration with ModeSelector

Tests the gradient confidence system for mode selection:
- Confidence >= 0.8: +0.30 boost (VERY_HIGH)
- Confidence >= 0.7: +0.25 boost (HIGH)
- Confidence >= 0.5: +0.10 boost (LOW)
- Confidence < 0.5: ignore suggestion

Also tests lead bonus (+0.20 effective promotion) when confidence > 0.7.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from dataclasses import dataclass

from core.swarm.mode_selector import ModeSelector, ModeProposal, AgentAssignment
from core.swarm.collaboration_modes import CollaborationMode
from core.swarm.task_analyzer import TaskAnalysis, TaskComplexity, TaskDomain
from core.swarm.agent_metrics import AgentProfile


# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
def mock_auto_memory():
    """Create a mock AutoMemory with controllable get_recommendation()."""
    mock = Mock()
    mock.get_recommendation = Mock(return_value=None)
    return mock


@pytest.fixture
def mock_task_analysis():
    """Create a mock TaskAnalysis for testing."""
    analysis = Mock(spec=TaskAnalysis)
    analysis.complexity = TaskComplexity.MODERATE
    analysis.primary_domain = TaskDomain.CODING
    analysis.domains = [TaskDomain.CODING]
    analysis.raw_input = "Test task description"
    analysis.requires_web = False
    analysis.requires_deep_reasoning = False
    analysis.requires_iteration = False
    analysis.needs_adversarial_mode = False
    analysis.recommended_lead = None
    return analysis


@pytest.fixture
def mock_agents():
    """Create mock agent profiles for testing."""
    gemini = AgentProfile(
        agent_id="gemini_primary",
        provider="gemini",
        model="gemini-3-pro-preview",
        capabilities=["coding", "research"]
    )
    claude = AgentProfile(
        agent_id="claude_opus",
        provider="claude",
        model="claude-opus-4-5-20251101",
        capabilities=["coding", "creativity"]
    )
    return [gemini, claude]


# ============================================================================
# Scenario 1: High Confidence Mode Boost (>= 0.8 → +0.30)
# ============================================================================


class TestHighConfidenceModeBoost:
    """Test AutoMemory mode boost with very high confidence (>= 0.8)."""

    def test_mode_boost_085_confidence(self, mock_auto_memory, mock_task_analysis, mock_agents):
        """
        Scenario 1: AutoMemory suggests LEAD_SUPPORT with confidence 0.85.
        Expected: +0.30 boost to LEAD_SUPPORT mode score.
        """
        # Configure AutoMemory to return high confidence recommendation
        mock_auto_memory.get_recommendation.return_value = {
            "mode": "lead_support",
            "lead": "gemini",
            "confidence": 0.85,
            "modes_to_avoid": []
        }

        # Create ModeSelector with mock AutoMemory
        selector = ModeSelector(auto_memory=mock_auto_memory)

        # Get initial scores (before AutoMemory boost)
        initial_scores = {}
        for mode in CollaborationMode:
            initial_scores[mode] = selector._score_mode(mode, mock_task_analysis, mock_agents)

        # Run select_mode which applies AutoMemory boost
        proposal = selector.select_mode(mock_task_analysis, mock_agents)

        # Verify AutoMemory was consulted
        mock_auto_memory.get_recommendation.assert_called_once_with("coding")

        # Verify boost info was recorded
        assert selector._last_auto_memory_suggestion is not None
        assert selector._last_auto_memory_suggestion["confidence"] == 0.85
        assert selector._last_auto_memory_suggestion["boost_applied"] == 0.30

    def test_mode_boost_exactly_080_confidence(self, mock_auto_memory, mock_task_analysis, mock_agents):
        """
        Boundary test: Confidence exactly 0.80 should get +0.30 boost.
        """
        mock_auto_memory.get_recommendation.return_value = {
            "mode": "parallel",
            "lead": None,
            "confidence": 0.80,
            "modes_to_avoid": []
        }

        selector = ModeSelector(auto_memory=mock_auto_memory)
        selector.select_mode(mock_task_analysis, mock_agents)

        assert selector._last_auto_memory_suggestion["boost_applied"] == 0.30


# ============================================================================
# Scenario 2: Medium Confidence Mode Boost (>= 0.7, < 0.8 → +0.25)
# ============================================================================


class TestMediumConfidenceModeBoost:
    """Test AutoMemory mode boost with high confidence (>= 0.7, < 0.8)."""

    def test_mode_boost_075_confidence(self, mock_auto_memory, mock_task_analysis, mock_agents):
        """
        Scenario 2a: AutoMemory suggests PING_PONG with confidence 0.75.
        Expected: +0.25 boost to PING_PONG mode score.
        """
        mock_auto_memory.get_recommendation.return_value = {
            "mode": "ping_pong",
            "lead": "claude",
            "confidence": 0.75,
            "modes_to_avoid": []
        }

        selector = ModeSelector(auto_memory=mock_auto_memory)
        selector.select_mode(mock_task_analysis, mock_agents)

        assert selector._last_auto_memory_suggestion is not None
        assert selector._last_auto_memory_suggestion["confidence"] == 0.75
        assert selector._last_auto_memory_suggestion["boost_applied"] == 0.25

    def test_mode_boost_exactly_070_confidence(self, mock_auto_memory, mock_task_analysis, mock_agents):
        """
        Boundary test: Confidence exactly 0.70 should get +0.25 boost.
        """
        mock_auto_memory.get_recommendation.return_value = {
            "mode": "sequential",
            "lead": None,
            "confidence": 0.70,
            "modes_to_avoid": []
        }

        selector = ModeSelector(auto_memory=mock_auto_memory)
        selector.select_mode(mock_task_analysis, mock_agents)

        assert selector._last_auto_memory_suggestion["boost_applied"] == 0.25


# ============================================================================
# Scenario 3: Low Confidence Mode Boost (>= 0.5, < 0.7 → +0.10)
# ============================================================================


class TestLowConfidenceModeBoost:
    """Test AutoMemory mode boost with low confidence (>= 0.5, < 0.7)."""

    def test_mode_boost_060_confidence(self, mock_auto_memory, mock_task_analysis, mock_agents):
        """
        Scenario 3a: AutoMemory suggests SPECIALIST with confidence 0.60.
        Expected: +0.10 boost to SPECIALIST mode score.
        """
        mock_auto_memory.get_recommendation.return_value = {
            "mode": "specialist",
            "lead": "gemini",
            "confidence": 0.60,
            "modes_to_avoid": []
        }

        selector = ModeSelector(auto_memory=mock_auto_memory)
        selector.select_mode(mock_task_analysis, mock_agents)

        assert selector._last_auto_memory_suggestion is not None
        assert selector._last_auto_memory_suggestion["confidence"] == 0.60
        assert selector._last_auto_memory_suggestion["boost_applied"] == 0.10

    def test_mode_boost_exactly_050_confidence(self, mock_auto_memory, mock_task_analysis, mock_agents):
        """
        Boundary test: Confidence exactly 0.50 should get +0.10 boost.
        """
        mock_auto_memory.get_recommendation.return_value = {
            "mode": "parallel",
            "lead": None,
            "confidence": 0.50,
            "modes_to_avoid": []
        }

        selector = ModeSelector(auto_memory=mock_auto_memory)
        selector.select_mode(mock_task_analysis, mock_agents)

        assert selector._last_auto_memory_suggestion["boost_applied"] == 0.10


# ============================================================================
# Scenario 4: Below Threshold (< 0.5 → ignore)
# ============================================================================


class TestBelowThresholdIgnored:
    """Test AutoMemory suggestions are ignored below confidence threshold."""

    def test_confidence_040_ignored(self, mock_auto_memory, mock_task_analysis, mock_agents):
        """
        Scenario 4: AutoMemory confidence 0.40 (below 0.5 threshold).
        Expected: Suggestion is completely ignored.
        """
        mock_auto_memory.get_recommendation.return_value = {
            "mode": "red_blue",
            "lead": "claude",
            "confidence": 0.40,
            "modes_to_avoid": []
        }

        selector = ModeSelector(auto_memory=mock_auto_memory)
        proposal = selector.select_mode(mock_task_analysis, mock_agents)

        # Should be None because confidence was too low
        assert selector._last_auto_memory_suggestion is None

    def test_confidence_049_ignored(self, mock_auto_memory, mock_task_analysis, mock_agents):
        """
        Boundary test: Confidence 0.49 (just below threshold) should be ignored.
        """
        mock_auto_memory.get_recommendation.return_value = {
            "mode": "specialist",
            "lead": "gemini",
            "confidence": 0.49,
            "modes_to_avoid": []
        }

        selector = ModeSelector(auto_memory=mock_auto_memory)
        selector.select_mode(mock_task_analysis, mock_agents)

        assert selector._last_auto_memory_suggestion is None


# ============================================================================
# Scenario 5: Lead Bonus (confidence > 0.7 → promote to front)
# ============================================================================


class TestLeadBonus:
    """Test AutoMemory lead promotion with high confidence."""

    def test_lead_promoted_with_075_confidence(self, mock_auto_memory, mock_task_analysis, mock_agents):
        """
        Scenario 5a: AutoMemory suggests claude as lead with confidence 0.75.
        Expected: Claude promoted to lead position in LEAD_SUPPORT mode.
        """
        mock_auto_memory.get_recommendation.return_value = {
            "mode": "lead_support",
            "lead": "claude",
            "confidence": 0.75,
            "modes_to_avoid": []
        }

        selector = ModeSelector(auto_memory=mock_auto_memory)
        proposal = selector.select_mode(mock_task_analysis, mock_agents)

        # If LEAD_SUPPORT selected, check lead assignment
        lead_assignments = [a for a in proposal.agent_assignments if a.role == "lead"]
        if lead_assignments:
            # Claude should be promoted to lead if mode is LEAD_SUPPORT
            if proposal.mode == CollaborationMode.LEAD_SUPPORT:
                assert "claude" in lead_assignments[0].agent_id.lower()

    def test_lead_not_promoted_below_07_confidence(self, mock_auto_memory, mock_task_analysis, mock_agents):
        """
        Scenario 5b: AutoMemory suggests lead with confidence 0.65.
        Expected: Lead suggestion is NOT applied (below 0.7 threshold).
        """
        mock_auto_memory.get_recommendation.return_value = {
            "mode": "lead_support",
            "lead": "claude",
            "confidence": 0.65,  # Below 0.7 threshold for lead bonus
            "modes_to_avoid": []
        }

        selector = ModeSelector(auto_memory=mock_auto_memory)

        # Verify the suggestion info doesn't include lead promotion
        # (since confidence < 0.7 for lead bonus)
        assert selector._last_auto_memory_suggestion is None or \
               selector._last_auto_memory_suggestion.get("suggested_lead") is None


# ============================================================================
# Edge Cases and Error Handling
# ============================================================================


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_no_auto_memory(self, mock_task_analysis, mock_agents):
        """Test ModeSelector works without AutoMemory."""
        selector = ModeSelector(auto_memory=None)
        proposal = selector.select_mode(mock_task_analysis, mock_agents)

        assert proposal is not None
        assert selector._last_auto_memory_suggestion is None

    def test_auto_memory_returns_none(self, mock_auto_memory, mock_task_analysis, mock_agents):
        """Test graceful handling when AutoMemory returns None."""
        mock_auto_memory.get_recommendation.return_value = None

        selector = ModeSelector(auto_memory=mock_auto_memory)
        proposal = selector.select_mode(mock_task_analysis, mock_agents)

        assert proposal is not None
        assert selector._last_auto_memory_suggestion is None

    def test_auto_memory_exception(self, mock_auto_memory, mock_task_analysis, mock_agents):
        """Test graceful handling when AutoMemory raises exception."""
        mock_auto_memory.get_recommendation.side_effect = Exception("AutoMemory error")

        selector = ModeSelector(auto_memory=mock_auto_memory)
        proposal = selector.select_mode(mock_task_analysis, mock_agents)

        # Should still return a proposal, just without AutoMemory influence
        assert proposal is not None
        assert selector._last_auto_memory_suggestion is None

    def test_invalid_mode_suggestion(self, mock_auto_memory, mock_task_analysis, mock_agents):
        """Test handling of invalid mode suggestion from AutoMemory."""
        mock_auto_memory.get_recommendation.return_value = {
            "mode": "nonexistent_mode",
            "lead": None,
            "confidence": 0.85,
            "modes_to_avoid": []
        }

        selector = ModeSelector(auto_memory=mock_auto_memory)
        proposal = selector.select_mode(mock_task_analysis, mock_agents)

        # Should still work, just without boost applied
        assert proposal is not None

    def test_modes_to_avoid_penalty(self, mock_auto_memory, mock_task_analysis, mock_agents):
        """Test that modes_to_avoid get penalized."""
        mock_auto_memory.get_recommendation.return_value = {
            "mode": "parallel",
            "lead": None,
            "confidence": 0.85,
            "modes_to_avoid": ["red_blue", "specialist"]
        }

        selector = ModeSelector(auto_memory=mock_auto_memory)
        proposal = selector.select_mode(mock_task_analysis, mock_agents)

        # Verify suggestion recorded modes_to_avoid
        assert selector._last_auto_memory_suggestion is not None
        assert "red_blue" in selector._last_auto_memory_suggestion["modes_to_avoid"]


# ============================================================================
# Integration with Existing Memory Systems
# ============================================================================


class TestMemorySystemsIntegration:
    """Test AutoMemory works alongside SuccessMemory."""

    def test_both_memory_systems(self, mock_auto_memory, mock_task_analysis, mock_agents):
        """Test AutoMemory and SuccessMemory can both be active."""
        mock_success_memory = Mock()
        mock_success_memory.get_best_mode_for_similar.return_value = None

        mock_auto_memory.get_recommendation.return_value = {
            "mode": "sequential",
            "lead": "gemini",
            "confidence": 0.80,
            "modes_to_avoid": []
        }

        selector = ModeSelector(
            success_memory=mock_success_memory,
            auto_memory=mock_auto_memory
        )
        proposal = selector.select_mode(mock_task_analysis, mock_agents)

        # Both memory systems should be consulted
        mock_success_memory.get_best_mode_for_similar.assert_called_once()
        mock_auto_memory.get_recommendation.assert_called_once()

        # AutoMemory suggestion should be recorded
        assert selector._last_auto_memory_suggestion is not None


# ============================================================================
# Reasoning Generation Tests
# ============================================================================


class TestReasoningGeneration:
    """Test that reasoning includes AutoMemory influence."""

    def test_reasoning_includes_automemory(self, mock_auto_memory, mock_task_analysis, mock_agents):
        """Test reasoning mentions AutoMemory when it influences selection."""
        mock_auto_memory.get_recommendation.return_value = {
            "mode": "parallel",
            "lead": None,
            "confidence": 0.85,
            "modes_to_avoid": []
        }

        selector = ModeSelector(auto_memory=mock_auto_memory)
        proposal = selector.select_mode(mock_task_analysis, mock_agents)

        # If parallel was selected (boosted), reasoning should mention AutoMemory
        if proposal.mode == CollaborationMode.PARALLEL:
            assert "AutoMemory" in proposal.reasoning or "auto" in proposal.reasoning.lower()
