"""
Unit tests for NCM token budget monitoring system.

Tests:
- Token usage tracking
- Budget percentage calculations
- Alert threshold triggering
- Budget exceeded detection
- Story projections
- Usage statistics
- Reset functionality
"""

import pytest
from datetime import datetime

from core.ncm.token_monitor import TokenBudgetMonitor, UsageRecord


@pytest.fixture
def monitor():
    """Create TokenBudgetMonitor with 1M budget for testing."""
    return TokenBudgetMonitor(budget=1_000_000)


class TestTokenBudgetMonitorInit:
    """Test TokenBudgetMonitor initialization."""

    def test_init_default_budget(self):
        """Test initialization with default budget."""
        monitor = TokenBudgetMonitor()
        assert monitor.budget == 100_000_000
        assert monitor.total_tokens_used == 0
        assert len(monitor.usage_records) == 0

    def test_init_custom_budget(self):
        """Test initialization with custom budget."""
        monitor = TokenBudgetMonitor(budget=50_000_000)
        assert monitor.budget == 50_000_000

    def test_init_custom_thresholds(self):
        """Test initialization with custom alert thresholds."""
        monitor = TokenBudgetMonitor(
            budget=1_000_000,
            alert_thresholds=[0.25, 0.5, 0.75, 0.9]
        )
        assert monitor.alert_thresholds == [0.25, 0.5, 0.75, 0.9]

    def test_init_invalid_budget(self):
        """Test that invalid budget raises ValueError."""
        with pytest.raises(ValueError, match="budget must be positive"):
            TokenBudgetMonitor(budget=0)

        with pytest.raises(ValueError, match="budget must be positive"):
            TokenBudgetMonitor(budget=-1000)


class TestUsageTracking:
    """Test token usage tracking."""

    def test_track_single_usage(self, monitor):
        """Test tracking single story usage."""
        monitor.track_usage(story_id="STORY-0001", tokens=45000)

        assert monitor.total_tokens_used == 45000
        assert monitor.stories_processed == 1
        assert monitor.avg_tokens_per_story == 45000
        assert len(monitor.usage_records) == 1

    def test_track_multiple_usages(self, monitor):
        """Test tracking multiple story usages."""
        monitor.track_usage("STORY-0001", 40000)
        monitor.track_usage("STORY-0002", 50000)
        monitor.track_usage("STORY-0003", 45000)

        assert monitor.total_tokens_used == 135000
        assert monitor.stories_processed == 3
        assert monitor.avg_tokens_per_story == 45000  # (40k + 50k + 45k) / 3

    def test_track_usage_updates_average(self, monitor):
        """Test that average is updated correctly."""
        monitor.track_usage("STORY-0001", 30000)
        assert monitor.avg_tokens_per_story == 30000

        monitor.track_usage("STORY-0002", 60000)
        assert monitor.avg_tokens_per_story == 45000  # (30k + 60k) / 2

        monitor.track_usage("STORY-0003", 45000)
        assert monitor.avg_tokens_per_story == 45000  # (30k + 60k + 45k) / 3

    def test_track_negative_tokens_ignored(self, monitor):
        """Test that negative tokens are ignored with warning."""
        monitor.track_usage("STORY-0001", -1000)

        # Should not affect totals
        assert monitor.total_tokens_used == 0
        assert monitor.stories_processed == 0

    def test_usage_record_creation(self, monitor):
        """Test that UsageRecord is created correctly."""
        monitor.track_usage("STORY-0001", 45000)

        record = monitor.usage_records[0]
        assert record.story_id == "STORY-0001"
        assert record.tokens == 45000
        assert isinstance(record.timestamp, datetime)


class TestBudgetCalculations:
    """Test budget percentage and remaining calculations."""

    def test_get_percent_used_empty(self, monitor):
        """Test percent used when no usage."""
        assert monitor.get_percent_used() == 0.0

    def test_get_percent_used_partial(self, monitor):
        """Test percent used with partial usage."""
        monitor.track_usage("STORY-0001", 250000)  # 25% of 1M
        assert monitor.get_percent_used() == 0.25

        monitor.track_usage("STORY-0002", 250000)  # Now 50%
        assert monitor.get_percent_used() == 0.5

    def test_get_percent_used_over_budget(self, monitor):
        """Test percent used when over budget."""
        monitor.track_usage("STORY-0001", 1_500_000)  # 150% of 1M
        assert monitor.get_percent_used() == 1.5

    def test_get_tokens_remaining(self, monitor):
        """Test tokens remaining calculation."""
        assert monitor.get_tokens_remaining() == 1_000_000

        monitor.track_usage("STORY-0001", 300_000)
        assert monitor.get_tokens_remaining() == 700_000

        monitor.track_usage("STORY-0002", 400_000)
        assert monitor.get_tokens_remaining() == 300_000

    def test_get_tokens_remaining_negative(self, monitor):
        """Test tokens remaining when over budget."""
        monitor.track_usage("STORY-0001", 1_200_000)
        assert monitor.get_tokens_remaining() == -200_000

    def test_is_budget_exceeded_false(self, monitor):
        """Test budget exceeded check when under budget."""
        monitor.track_usage("STORY-0001", 500_000)
        assert monitor.is_budget_exceeded() is False

    def test_is_budget_exceeded_true(self, monitor):
        """Test budget exceeded check when over budget."""
        monitor.track_usage("STORY-0001", 1_000_001)
        assert monitor.is_budget_exceeded() is True

    def test_is_budget_exceeded_exactly_at_budget(self, monitor):
        """Test budget exceeded when exactly at budget."""
        monitor.track_usage("STORY-0001", 1_000_000)
        assert monitor.is_budget_exceeded() is True  # >= budget


class TestAlertThresholds:
    """Test alert threshold triggering."""

    def test_no_alerts_below_threshold(self, monitor):
        """Test that no alerts triggered below first threshold."""
        monitor.track_usage("STORY-0001", 400_000)  # 40% (below 50%)

        assert not monitor.alerts_triggered[0.5]
        assert not monitor.alerts_triggered[0.75]
        assert not monitor.alerts_triggered[0.9]

    def test_alert_triggered_at_50_percent(self, monitor):
        """Test alert triggered at 50% threshold."""
        monitor.track_usage("STORY-0001", 500_000)  # Exactly 50%

        assert monitor.alerts_triggered[0.5] is True
        assert monitor.alerts_triggered[0.75] is False
        assert monitor.alerts_triggered[0.9] is False

    def test_alert_triggered_at_75_percent(self, monitor):
        """Test alerts triggered at 75% threshold."""
        monitor.track_usage("STORY-0001", 750_000)  # 75%

        assert monitor.alerts_triggered[0.5] is True
        assert monitor.alerts_triggered[0.75] is True
        assert monitor.alerts_triggered[0.9] is False

    def test_alert_triggered_at_90_percent(self, monitor):
        """Test alerts triggered at 90% threshold."""
        monitor.track_usage("STORY-0001", 900_000)  # 90%

        assert monitor.alerts_triggered[0.5] is True
        assert monitor.alerts_triggered[0.75] is True
        assert monitor.alerts_triggered[0.9] is True

    def test_alert_triggered_only_once(self, monitor):
        """Test that each alert only triggers once."""
        # Cross 50% threshold
        monitor.track_usage("STORY-0001", 500_000)
        assert monitor.alerts_triggered[0.5] is True

        # Track more usage (still in 50-75% range)
        monitor.track_usage("STORY-0002", 100_000)
        # Alert should still be marked as triggered (not re-triggered)
        assert monitor.alerts_triggered[0.5] is True


class TestProjections:
    """Test story and budget projections."""

    def test_estimate_stories_remaining_no_data(self, monitor):
        """Test estimate with no usage data."""
        assert monitor.estimate_stories_remaining() == 0

    def test_estimate_stories_remaining_with_data(self, monitor):
        """Test estimate based on average usage."""
        monitor.track_usage("STORY-0001", 40_000)
        monitor.track_usage("STORY-0002", 50_000)
        # Average: 45k tokens/story
        # Remaining: 910k tokens
        # Estimate: 910k / 45k = ~20 stories

        remaining = monitor.estimate_stories_remaining()
        assert remaining == 20  # (1M - 90k) / 45k = 20.2 → 20

    def test_estimate_stories_remaining_budget_exceeded(self, monitor):
        """Test estimate when budget exceeded."""
        monitor.track_usage("STORY-0001", 1_500_000)

        assert monitor.estimate_stories_remaining() == 0

    def test_estimate_total_stories_possible(self, monitor):
        """Test total stories possible with full budget."""
        monitor.track_usage("STORY-0001", 40_000)
        monitor.track_usage("STORY-0002", 60_000)
        # Average: 50k tokens/story
        # Budget: 1M
        # Total possible: 1M / 50k = 20 stories

        total = monitor.estimate_total_stories_possible()
        assert total == 20

    def test_estimate_total_stories_possible_no_data(self, monitor):
        """Test total estimate with no data."""
        assert monitor.estimate_total_stories_possible() == 0


class TestStatus:
    """Test status reporting."""

    def test_get_status_empty(self, monitor):
        """Test status with no usage."""
        status = monitor.get_status()

        assert status["budget"] == 1_000_000
        assert status["total_used"] == 0
        assert status["tokens_remaining"] == 1_000_000
        assert status["percent_used"] == 0.0
        assert status["stories_processed"] == 0
        assert status["budget_exceeded"] is False

    def test_get_status_with_usage(self, monitor):
        """Test status with usage data."""
        monitor.track_usage("STORY-0001", 300_000)
        monitor.track_usage("STORY-0002", 200_000)

        status = monitor.get_status()

        assert status["budget"] == 1_000_000
        assert status["total_used"] == 500_000
        assert status["tokens_remaining"] == 500_000
        assert status["percent_used"] == 0.5
        assert status["stories_processed"] == 2
        assert status["avg_tokens_per_story"] == 250_000
        assert status["budget_exceeded"] is False

    def test_get_status_alerts(self, monitor):
        """Test status includes alert information."""
        monitor.track_usage("STORY-0001", 600_000)  # Cross 50% threshold

        status = monitor.get_status()

        assert "alerts_triggered" in status
        assert status["alerts_triggered"]["50%"] is True
        assert status["alerts_triggered"]["75%"] is False


class TestUsageHistory:
    """Test usage history retrieval."""

    def test_get_usage_history_empty(self, monitor):
        """Test history when no usage."""
        history = monitor.get_usage_history()
        assert history == []

    def test_get_usage_history_all(self, monitor):
        """Test retrieving all usage history."""
        monitor.track_usage("STORY-0001", 40_000)
        monitor.track_usage("STORY-0002", 50_000)
        monitor.track_usage("STORY-0003", 45_000)

        history = monitor.get_usage_history()

        assert len(history) == 3
        # Most recent first
        assert history[0]["story_id"] == "STORY-0003"
        assert history[1]["story_id"] == "STORY-0002"
        assert history[2]["story_id"] == "STORY-0001"

    def test_get_usage_history_limited(self, monitor):
        """Test retrieving limited usage history."""
        for i in range(10):
            monitor.track_usage(f"STORY-{i:04d}", 40_000)

        history = monitor.get_usage_history(limit=5)

        assert len(history) == 5
        # Should be most recent 5
        assert history[0]["story_id"] == "STORY-0009"
        assert history[4]["story_id"] == "STORY-0005"


class TestStatistics:
    """Test usage statistics."""

    def test_get_statistics_empty(self, monitor):
        """Test statistics with no data."""
        stats = monitor.get_statistics()

        assert stats["total_stories"] == 0
        assert stats["total_tokens"] == 0
        assert stats["avg_tokens"] == 0
        assert stats["min_tokens"] == 0
        assert stats["max_tokens"] == 0
        assert stats["median_tokens"] == 0

    def test_get_statistics_with_data(self, monitor):
        """Test statistics with usage data."""
        monitor.track_usage("STORY-0001", 30_000)
        monitor.track_usage("STORY-0002", 40_000)
        monitor.track_usage("STORY-0003", 50_000)
        monitor.track_usage("STORY-0004", 60_000)
        monitor.track_usage("STORY-0005", 70_000)

        stats = monitor.get_statistics()

        assert stats["total_stories"] == 5
        assert stats["total_tokens"] == 250_000
        assert stats["avg_tokens"] == 50_000  # (30+40+50+60+70)/5
        assert stats["min_tokens"] == 30_000
        assert stats["max_tokens"] == 70_000
        assert stats["median_tokens"] == 50_000  # Middle value

    def test_get_statistics_median_even_count(self, monitor):
        """Test median calculation with even number of values."""
        monitor.track_usage("STORY-0001", 40_000)
        monitor.track_usage("STORY-0002", 50_000)
        monitor.track_usage("STORY-0003", 60_000)
        monitor.track_usage("STORY-0004", 70_000)

        stats = monitor.get_statistics()

        # Median of [40k, 50k, 60k, 70k] = (50k + 60k) / 2 = 55k
        assert stats["median_tokens"] == 55_000


class TestReset:
    """Test monitor reset functionality."""

    def test_reset(self, monitor):
        """Test reset clears all state."""
        # Add some usage
        monitor.track_usage("STORY-0001", 400_000)
        monitor.track_usage("STORY-0002", 300_000)

        # Verify state
        assert monitor.total_tokens_used == 700_000
        assert monitor.stories_processed == 2
        assert len(monitor.usage_records) == 2

        # Reset
        monitor.reset()

        # Verify cleared
        assert monitor.total_tokens_used == 0
        assert monitor.stories_processed == 0
        assert monitor.avg_tokens_per_story == 0
        assert len(monitor.usage_records) == 0

        # Alerts should be reset
        assert not any(monitor.alerts_triggered.values())

    def test_reset_preserves_config(self, monitor):
        """Test that reset preserves configuration."""
        original_budget = monitor.budget
        original_thresholds = monitor.alert_thresholds

        monitor.track_usage("STORY-0001", 500_000)
        monitor.reset()

        # Config should be preserved
        assert monitor.budget == original_budget
        assert monitor.alert_thresholds == original_thresholds
