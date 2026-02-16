"""
NEXUS Budget Tracker - V12.4 COGNITIVE BOOST

Financial circuit breaker to prevent runaway API costs.
Tracks token usage and enforces daily spending limits.

Usage:
    tracker = BudgetTracker(config, workspace_path)
    tracker.track_cost("claude-opus", input_tokens=1000, output_tokens=500)
    tracker.check_budget()  # Raises BudgetExceededError if over limit

Pricing (Feb 2026):
    Claude Opus 4.6:   $15/1M input, $75/1M output
    Claude Sonnet 4.5:  $3/1M input, $15/1M output
    Claude Haiku 4.5:   $1/1M input, $5/1M output
    Gemini 3 Pro:      $1.25/1M input, $5/1M output
    Gemini 3 Flash:    $0.075/1M input, $0.30/1M output
"""

import json
import logging
import time
from datetime import datetime, date
from pathlib import Path
from threading import Lock
from typing import Dict, Optional, Tuple

_logger = logging.getLogger(__name__)
from dataclasses import dataclass, asdict


# =============================================================================
# PRICING CONSTANTS (Feb 2026)
# =============================================================================

# Cost per 1 MILLION tokens (USD)
PRICING = {
    # Claude models (Opus 4.6, Sonnet 4.5, Haiku 4.5)
    "claude-opus-4-6-20250116": {"input": 15.00, "output": 75.00},
    "claude-opus-4-6": {"input": 15.00, "output": 75.00},  # Alias
    "claude-opus-4-5-20251101": {"input": 15.00, "output": 75.00},  # Legacy
    "claude-opus": {"input": 15.00, "output": 75.00},  # Alias
    "claude-sonnet-4-5-20250929": {"input": 3.00, "output": 15.00},
    "claude-sonnet": {"input": 3.00, "output": 15.00},  # Alias
    "claude-haiku-4-5-20251001": {"input": 1.00, "output": 5.00},
    "claude-haiku": {"input": 1.00, "output": 5.00},  # Alias

    # Gemini models
    "gemini-3-pro-preview": {"input": 1.25, "output": 5.00},
    "gemini-3-pro": {"input": 1.25, "output": 5.00},  # Alias
    "gemini-pro": {"input": 1.25, "output": 5.00},  # Alias
    "gemini-2.5-flash": {"input": 0.15, "output": 0.60},
    "gemini-3-flash": {"input": 0.075, "output": 0.30},
    "gemini-flash": {"input": 0.15, "output": 0.60},  # Alias (default to 2.5)

    # Local models (zero cost)
    "ollama": {"input": 0.0, "output": 0.0},
    "llama3.1": {"input": 0.0, "output": 0.0},

    # Default fallback (conservative estimate)
    "default": {"input": 5.00, "output": 20.00},
}

# Warning thresholds (percentage of limit)
BUDGET_WARNING_THRESHOLD = 0.80   # 80% -> warning
BUDGET_CRITICAL_THRESHOLD = 0.90  # 90% -> critical alert
BUDGET_LIMIT_THRESHOLD = 1.00     # 100% -> hard stop


# =============================================================================
# EXCEPTIONS
# =============================================================================

class BudgetExceededError(Exception):
    """Raised when daily budget limit is exceeded."""

    def __init__(self, spent: float, limit: float, message: str = None):
        self.spent = spent
        self.limit = limit
        self.message = message or f"Budget exceeded: ${spent:.2f} / ${limit:.2f} limit"
        super().__init__(self.message)


class BudgetWarning(Warning):
    """Warning when approaching budget limit."""
    pass


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class BudgetState:
    """Persisted budget state."""
    spent_today_usd: float = 0.0
    reset_date: str = ""  # ISO date (YYYY-MM-DD)
    total_lifetime_usd: float = 0.0
    api_calls_today: int = 0
    last_updated: str = ""

    def to_dict(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> "BudgetState":
        return cls(
            spent_today_usd=data.get("spent_today_usd", 0.0),
            reset_date=data.get("reset_date", ""),
            total_lifetime_usd=data.get("total_lifetime_usd", 0.0),
            api_calls_today=data.get("api_calls_today", 0),
            last_updated=data.get("last_updated", ""),
        )


@dataclass
class CostRecord:
    """Record of a single API cost."""
    timestamp: str
    model: str
    input_tokens: int
    output_tokens: int
    cost_usd: float


# =============================================================================
# BUDGET TRACKER
# =============================================================================

class BudgetTracker:
    """
    Tracks API costs and enforces budget limits.

    Thread-safe with file-based persistence.
    Resets daily at local midnight.
    """

    def __init__(
        self,
        config=None,
        workspace_path: Optional[Path] = None,
        budget_file: Optional[Path] = None,
    ):
        """
        Initialize BudgetTracker.

        Args:
            config: NEXUS config (uses budget_limit_usd if available)
            workspace_path: Path to workspace directory
            budget_file: Override budget state file path
        """
        self._lock = Lock()

        # Get budget limit from config
        self.limit_usd = 50.0  # Default
        if config:
            self.limit_usd = getattr(config, 'budget_limit_usd', 50.0)

        # Set up persistence path
        if budget_file:
            self.budget_file = budget_file
        elif workspace_path:
            self.budget_file = Path(workspace_path) / ".nexus" / "budget.json"
        else:
            self.budget_file = Path("workspace/.nexus/budget.json")

        # Ensure directory exists
        self.budget_file.parent.mkdir(parents=True, exist_ok=True)

        # Load or initialize state
        self._state = self._load_state()

        # Check for daily reset
        self._check_daily_reset()

    def _load_state(self) -> BudgetState:
        """Load budget state from file."""
        if self.budget_file.exists():
            try:
                data = json.loads(self.budget_file.read_text(encoding='utf-8'))
                return BudgetState.from_dict(data)
            except (json.JSONDecodeError, KeyError):
                pass
        return BudgetState(reset_date=date.today().isoformat())

    def _save_state(self):
        """Save budget state to file."""
        self._state.last_updated = datetime.now().isoformat()
        try:
            self.budget_file.write_text(
                json.dumps(self._state.to_dict(), indent=2),
                encoding='utf-8'
            )
        except Exception as e:
            _logger.warning("BudgetTracker save error: %s", e)

    def _check_daily_reset(self):
        """Reset counters if it's a new day."""
        today = date.today().isoformat()
        if self._state.reset_date != today:
            with self._lock:
                self._state.spent_today_usd = 0.0
                self._state.api_calls_today = 0
                self._state.reset_date = today
                self._save_state()

    def estimate_tokens(self, text: str) -> int:
        """
        Estimate token count from text.

        Uses approximate ratio of 4 characters per token.
        This is a rough estimate - actual tokenization varies by model.

        Args:
            text: Input text

        Returns:
            Estimated token count
        """
        if not text:
            return 0
        # Rough estimate: ~4 chars per token for English text
        return max(1, len(text) // 4)

    def get_model_pricing(self, model: str) -> Dict[str, float]:
        """
        Get pricing for a model.

        Args:
            model: Model name or alias

        Returns:
            Dict with 'input' and 'output' prices per 1M tokens
        """
        model_lower = model.lower()

        # Try exact match first
        if model_lower in PRICING:
            return PRICING[model_lower]

        # Try partial matches
        for key, pricing in PRICING.items():
            if key in model_lower or model_lower in key:
                return pricing

        # Fallback to default
        return PRICING["default"]

    def calculate_cost(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int
    ) -> float:
        """
        Calculate cost for an API call.

        Args:
            model: Model name
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens

        Returns:
            Cost in USD
        """
        pricing = self.get_model_pricing(model)

        # Cost = (tokens / 1M) * price_per_1M
        input_cost = (input_tokens / 1_000_000) * pricing["input"]
        output_cost = (output_tokens / 1_000_000) * pricing["output"]

        return input_cost + output_cost

    def track_cost(
        self,
        model: str,
        input_tokens: int = 0,
        output_tokens: int = 0,
        input_text: Optional[str] = None,
        output_text: Optional[str] = None,
    ) -> float:
        """
        Track cost of an API call.

        Can provide either token counts or text for estimation.

        Args:
            model: Model name
            input_tokens: Input token count (or 0 to estimate from text)
            output_tokens: Output token count (or 0 to estimate from text)
            input_text: Input text for estimation (if tokens not provided)
            output_text: Output text for estimation (if tokens not provided)

        Returns:
            Cost in USD for this call
        """
        # Estimate tokens from text if not provided
        if input_tokens == 0 and input_text:
            input_tokens = self.estimate_tokens(input_text)
        if output_tokens == 0 and output_text:
            output_tokens = self.estimate_tokens(output_text)

        # Calculate cost
        cost = self.calculate_cost(model, input_tokens, output_tokens)

        # Update state
        with self._lock:
            self._check_daily_reset()
            self._state.spent_today_usd += cost
            self._state.total_lifetime_usd += cost
            self._state.api_calls_today += 1
            self._save_state()

        return cost

    def get_budget_status(self) -> Tuple[float, float, float]:
        """
        Get current budget status.

        Returns:
            Tuple of (spent_today, limit, percentage_used)
        """
        self._check_daily_reset()
        spent = self._state.spent_today_usd
        pct = (spent / self.limit_usd * 100) if self.limit_usd > 0 else 0
        return spent, self.limit_usd, pct

    def check_budget(self) -> bool:
        """
        Check if budget is exceeded.

        Returns:
            True if within budget

        Raises:
            BudgetExceededError: If budget limit exceeded
        """
        self._check_daily_reset()
        spent = self._state.spent_today_usd

        if spent >= self.limit_usd * BUDGET_LIMIT_THRESHOLD:
            raise BudgetExceededError(spent, self.limit_usd)

        return True

    def get_warning_level(self) -> Optional[str]:
        """
        Get current warning level.

        Returns:
            "warning" at 80%, "critical" at 90%, None if under 80%
        """
        self._check_daily_reset()
        spent = self._state.spent_today_usd
        pct = spent / self.limit_usd if self.limit_usd > 0 else 0

        if pct >= BUDGET_CRITICAL_THRESHOLD:
            return "critical"
        elif pct >= BUDGET_WARNING_THRESHOLD:
            return "warning"
        return None

    def get_remaining(self) -> float:
        """Get remaining budget for today in USD."""
        self._check_daily_reset()
        return max(0, self.limit_usd - self._state.spent_today_usd)

    def get_stats(self) -> Dict:
        """
        Get comprehensive budget statistics.

        Returns:
            Dict with current budget stats
        """
        self._check_daily_reset()
        spent, limit, pct = self.get_budget_status()

        return {
            "spent_today_usd": round(spent, 4),
            "limit_usd": limit,
            "remaining_usd": round(self.get_remaining(), 4),
            "percentage_used": round(pct, 2),
            "api_calls_today": self._state.api_calls_today,
            "total_lifetime_usd": round(self._state.total_lifetime_usd, 4),
            "reset_date": self._state.reset_date,
            "warning_level": self.get_warning_level(),
        }

    def reset_daily(self):
        """Manually reset daily counters (for testing or emergency)."""
        with self._lock:
            self._state.spent_today_usd = 0.0
            self._state.api_calls_today = 0
            self._state.reset_date = date.today().isoformat()
            self._save_state()

    def add_credit(self, amount_usd: float):
        """
        Add credit to today's budget (for emergency unlock).

        Args:
            amount_usd: Amount to add to limit for today
        """
        with self._lock:
            self.limit_usd += amount_usd
            self._save_state()


# =============================================================================
# MODULE-LEVEL FUNCTIONS
# =============================================================================

_tracker: Optional[BudgetTracker] = None


def get_budget_tracker(config=None, workspace_path: Optional[Path] = None) -> BudgetTracker:
    """Get or create the global budget tracker."""
    global _tracker
    if _tracker is None:
        _tracker = BudgetTracker(config, workspace_path)
    return _tracker


def reset_budget_tracker():
    """Reset the global budget tracker (for testing)."""
    global _tracker
    _tracker = None
