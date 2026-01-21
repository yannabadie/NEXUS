"""
Token Budget Monitor - Blind Spot #5 Mitigation

Monitors token usage and alerts before exceeding budget.

Blind Spot #5: Token Budget Exhaustion
    - 10,602 stories × 45k tokens/story = 477M tokens (exceeds budget)
    - Solution: Track tokens per story, alert at thresholds

Architecture:
    - Track cumulative token usage
    - Define alert thresholds (50%, 75%, 90%)
    - Alert when crossing thresholds
    - Provide projections (stories remaining)

Usage:
    from core.ncm.token_monitor import TokenBudgetMonitor

    monitor = TokenBudgetMonitor(budget=100_000_000)

    # Track usage
    monitor.track_usage(story_id="STORY-0001", tokens=45000)

    # Check status
    status = monitor.get_status()
    print(f"Budget used: {status['percent_used']:.1%}")
"""

from typing import Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass, field

from core.logging import get_logger


@dataclass
class UsageRecord:
    """Token usage record for a single story."""
    story_id: str
    tokens: int
    timestamp: datetime = field(default_factory=datetime.now)


class TokenBudgetMonitor:
    """
    Monitor token usage and alert before exceeding budget.

    Blind Spot #5 Mitigation:
        - 10,602 stories × 45k tokens/story = 477M tokens (exceeds budget)
        - Solution: Track tokens per story, alert at thresholds

    Alert Thresholds:
        - 50%: Info (halfway through budget)
        - 75%: Warning (3/4 through budget)
        - 90%: Critical (approaching limit)
        - 100%: Budget exceeded (stop execution)

    Projections:
        - Average tokens per story
        - Estimated stories remaining
        - Estimated completion time

    Usage:
        monitor = TokenBudgetMonitor(budget=100_000_000)

        # Track story execution
        monitor.track_usage(story_id="STORY-0001", tokens=45000)

        # Check if budget exceeded
        if monitor.is_budget_exceeded():
            print("Budget exceeded! Stop execution.")
    """

    def __init__(
        self,
        budget: int = 100_000_000,
        alert_thresholds: Optional[List[float]] = None
    ):
        """
        Initialize token budget monitor.

        Args:
            budget: Total token budget (default: 100M)
            alert_thresholds: List of alert thresholds as percentages
                              (default: [0.5, 0.75, 0.9])

        Raises:
            ValueError: If budget <= 0
        """
        if budget <= 0:
            raise ValueError(f"budget must be positive, got {budget}")

        self.budget = budget
        self.alert_thresholds = alert_thresholds or [0.5, 0.75, 0.9]
        self.logger = get_logger()

        # Fallback if logger is None (can happen in test environments)
        if self.logger is None:
            import logging
            self.logger = logging.getLogger(__name__)

        # Usage tracking
        self.total_tokens_used = 0
        self.usage_records: List[UsageRecord] = []

        # Alert tracking (threshold → already alerted)
        self.alerts_triggered: Dict[float, bool] = {
            threshold: False for threshold in self.alert_thresholds
        }

        # Statistics
        self.stories_processed = 0
        self.avg_tokens_per_story = 0

        self.logger.info("token_budget_monitor_initialized", {
            "budget": budget,
            "alert_thresholds": self.alert_thresholds
        })

    def track_usage(
        self,
        story_id: str,
        tokens: int
    ):
        """
        Track token usage for a story.

        Args:
            story_id: Story identifier
            tokens: Tokens used for this story

        Process:
            1. Record usage
            2. Update cumulative total
            3. Update statistics
            4. Check alert thresholds
            5. Log if threshold crossed

        Usage:
            monitor.track_usage(story_id="STORY-0001", tokens=45000)
        """
        if tokens < 0:
            self.logger.warning("negative_tokens_tracked", {
                "story_id": story_id,
                "tokens": tokens
            })
            return

        # Record usage
        record = UsageRecord(
            story_id=story_id,
            tokens=tokens,
            timestamp=datetime.now()
        )
        self.usage_records.append(record)

        # Update totals
        self.total_tokens_used += tokens
        self.stories_processed += 1

        # Update statistics
        self.avg_tokens_per_story = self.total_tokens_used / self.stories_processed

        # Check thresholds
        self._check_thresholds()

        self.logger.debug("token_usage_tracked", {
            "story_id": story_id,
            "tokens": tokens,
            "total_used": self.total_tokens_used,
            "percent_used": f"{self.get_percent_used():.2%}"
        })

    def _check_thresholds(self):
        """
        Check if any alert thresholds have been crossed.

        If a threshold is crossed for the first time, log an alert.
        """
        percent_used = self.get_percent_used()

        for threshold in self.alert_thresholds:
            if percent_used >= threshold and not self.alerts_triggered[threshold]:
                # Threshold crossed for the first time
                self.alerts_triggered[threshold] = True

                # Determine alert level
                if threshold >= 0.9:
                    log_level = "critical"
                elif threshold >= 0.75:
                    log_level = "warning"
                else:
                    log_level = "info"

                # Log alert
                alert_data = {
                    "threshold": f"{threshold:.0%}",
                    "total_used": self.total_tokens_used,
                    "budget": self.budget,
                    "stories_processed": self.stories_processed,
                    "avg_tokens_per_story": int(self.avg_tokens_per_story),
                    "estimated_stories_remaining": self.estimate_stories_remaining()
                }

                getattr(self.logger, log_level)("token_budget_threshold_crossed", alert_data)

    def get_percent_used(self) -> float:
        """
        Get percentage of budget used.

        Returns:
            Percentage as float (0.0 to 1.0+)

        Example:
            >>> monitor.get_percent_used()
            0.523  # 52.3% of budget used
        """
        if self.budget == 0:
            return 0.0
        return self.total_tokens_used / self.budget

    def is_budget_exceeded(self) -> bool:
        """
        Check if budget has been exceeded.

        Returns:
            True if total_tokens_used >= budget, False otherwise

        Usage:
            if monitor.is_budget_exceeded():
                print("Stop execution! Budget exceeded.")
        """
        return self.total_tokens_used >= self.budget

    def get_tokens_remaining(self) -> int:
        """
        Get tokens remaining in budget.

        Returns:
            Tokens remaining (may be negative if exceeded)

        Example:
            >>> monitor.get_tokens_remaining()
            45230000  # 45.23M tokens remaining
        """
        return self.budget - self.total_tokens_used

    def estimate_stories_remaining(self) -> int:
        """
        Estimate number of stories that can be processed with remaining budget.

        Based on average tokens per story so far.

        Returns:
            Estimated stories remaining (0 if budget exceeded or no data)

        Example:
            >>> monitor.estimate_stories_remaining()
            1005  # Can process ~1005 more stories
        """
        if self.avg_tokens_per_story == 0:
            return 0

        tokens_remaining = max(0, self.get_tokens_remaining())
        return int(tokens_remaining / self.avg_tokens_per_story)

    def estimate_total_stories_possible(self) -> int:
        """
        Estimate total stories possible with full budget.

        Based on current average tokens per story.

        Returns:
            Estimated total stories possible (0 if no data)

        Example:
            >>> monitor.estimate_total_stories_possible()
            2222  # Budget allows ~2222 total stories
        """
        if self.avg_tokens_per_story == 0:
            return 0

        return int(self.budget / self.avg_tokens_per_story)

    def get_status(self) -> Dict:
        """
        Get comprehensive budget status.

        Returns:
            Dict with status information:
                - budget: Total budget
                - total_used: Tokens used so far
                - tokens_remaining: Tokens remaining
                - percent_used: Percentage used (0-100+)
                - stories_processed: Stories processed so far
                - avg_tokens_per_story: Average tokens per story
                - estimated_stories_remaining: Stories that can still be processed
                - estimated_total_stories: Total stories possible with budget
                - budget_exceeded: True if budget exceeded

        Usage:
            status = monitor.get_status()
            print(f"Budget: {status['percent_used']:.1%} used")
            print(f"Stories remaining: {status['estimated_stories_remaining']}")
        """
        return {
            "budget": self.budget,
            "total_used": self.total_tokens_used,
            "tokens_remaining": self.get_tokens_remaining(),
            "percent_used": self.get_percent_used(),
            "stories_processed": self.stories_processed,
            "avg_tokens_per_story": int(self.avg_tokens_per_story),
            "estimated_stories_remaining": self.estimate_stories_remaining(),
            "estimated_total_stories": self.estimate_total_stories_possible(),
            "budget_exceeded": self.is_budget_exceeded(),
            "alerts_triggered": {
                f"{int(t*100)}%": triggered
                for t, triggered in self.alerts_triggered.items()
            }
        }

    def get_usage_history(
        self,
        limit: Optional[int] = None
    ) -> List[Dict]:
        """
        Get usage history records.

        Args:
            limit: Optional limit on number of records (None = all)

        Returns:
            List of usage records (most recent first)

        Usage:
            # Get last 10 records
            history = monitor.get_usage_history(limit=10)
            for record in history:
                print(f"{record['story_id']}: {record['tokens']} tokens")
        """
        records = [
            {
                "story_id": r.story_id,
                "tokens": r.tokens,
                "timestamp": r.timestamp.isoformat()
            }
            for r in reversed(self.usage_records)
        ]

        if limit:
            records = records[:limit]

        return records

    def get_statistics(self) -> Dict:
        """
        Get usage statistics.

        Returns:
            Dict with statistics:
                - total_stories: Total stories processed
                - total_tokens: Total tokens used
                - avg_tokens: Average tokens per story
                - min_tokens: Minimum tokens for a story (if any)
                - max_tokens: Maximum tokens for a story (if any)
                - median_tokens: Median tokens per story (if any)

        Usage:
            stats = monitor.get_statistics()
            print(f"Min: {stats['min_tokens']}, Max: {stats['max_tokens']}")
        """
        if not self.usage_records:
            return {
                "total_stories": 0,
                "total_tokens": 0,
                "avg_tokens": 0,
                "min_tokens": 0,
                "max_tokens": 0,
                "median_tokens": 0
            }

        tokens_list = [r.tokens for r in self.usage_records]
        tokens_list.sort()

        # Calculate median
        n = len(tokens_list)
        if n % 2 == 0:
            median = (tokens_list[n//2 - 1] + tokens_list[n//2]) / 2
        else:
            median = tokens_list[n//2]

        return {
            "total_stories": self.stories_processed,
            "total_tokens": self.total_tokens_used,
            "avg_tokens": int(self.avg_tokens_per_story),
            "min_tokens": min(tokens_list),
            "max_tokens": max(tokens_list),
            "median_tokens": int(median)
        }

    def reset(self):
        """
        Reset monitor to initial state.

        Clears all usage records and resets counters.
        Useful for starting a new batch or phase.

        Usage:
            # After completing pilot
            monitor.reset()
            # Start Phase 2
        """
        self.total_tokens_used = 0
        self.usage_records = []
        self.stories_processed = 0
        self.avg_tokens_per_story = 0
        self.alerts_triggered = {
            threshold: False for threshold in self.alert_thresholds
        }

        self.logger.info("token_budget_monitor_reset")
