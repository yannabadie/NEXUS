"""
NEXUS V10.2 - Budget Command Helpers

Extracted helper functions for /budget commands.

Usage:
    from core.interface.repl.budget_helpers import (
        format_budget_status,
        validate_credit_amount
    )
"""

from typing import Dict, Optional
from datetime import datetime
import logging

logger = logging.getLogger("nexus.repl.budget")


# Budget status thresholds
BUDGET_WARNING_THRESHOLD = 0.8  # 80% spent = warning
BUDGET_CRITICAL_THRESHOLD = 0.95  # 95% spent = critical


def format_budget_status(tracker_status: Dict) -> str:
    """
    Format budget status as a report string.
    
    Args:
        tracker_status: Status dict from BudgetTracker
        
    Returns:
        Formatted status string
    """
    spent = tracker_status.get("spent", 0)
    limit = tracker_status.get("limit", 0)
    remaining = tracker_status.get("remaining", 0)
    
    # Calculate percentage
    pct = (spent / limit * 100) if limit > 0 else 0
    
    # Status indicator
    if pct >= BUDGET_CRITICAL_THRESHOLD * 100:
        status_icon = "🔴"
        status_text = "CRITICAL"
    elif pct >= BUDGET_WARNING_THRESHOLD * 100:
        status_icon = "🟡"
        status_text = "WARNING"
    else:
        status_icon = "🟢"
        status_text = "OK"
    
    lines = [
        f"## Budget Status {status_icon} {status_text}",
        "",
        "| Metric | Value |",
        "|--------|-------|",
        f"| Daily Limit | ${limit:.2f} |",
        f"| Spent Today | ${spent:.4f} |",
        f"| Remaining | ${remaining:.4f} |",
        f"| Usage | {pct:.1f}% |",
    ]
    
    return "\n".join(lines)


def format_cost_history(history: list, limit: int = 10) -> str:
    """
    Format recent API costs as a table.
    
    Args:
        history: List of cost records
        limit: Max records to show
        
    Returns:
        Formatted history string
    """
    if not history:
        return "No cost history available."
    
    lines = [
        "",
        "### Recent API Costs",
        "",
        "| Time | Model | Cost |",
        "|------|-------|------|"
    ]
    
    for record in history[-limit:]:
        time_str = record.get("time", "")[:19]  # Truncate to seconds
        model = record.get("model", "unknown")[:15]
        cost = record.get("cost", 0)
        lines.append(f"| {time_str} | {model} | ${cost:.4f} |")
    
    return "\n".join(lines)


def validate_credit_amount(amount: str) -> Optional[float]:
    """
    Validate and parse credit amount string.
    
    Args:
        amount: Credit amount string (e.g., "5", "10.50")
        
    Returns:
        Parsed float or None if invalid
    """
    try:
        value = float(amount)
        if value <= 0:
            return None
        if value > 100:  # Sanity check
            logger.warning(f"Large credit amount requested: {value}")
        return value
    except (ValueError, TypeError):
        return None


def should_warn_budget(spent: float, limit: float) -> bool:
    """
    Check if budget usage should trigger a warning.
    
    Args:
        spent: Amount spent
        limit: Budget limit
        
    Returns:
        True if warning should be shown
    """
    if limit <= 0:
        return False
    return (spent / limit) >= BUDGET_WARNING_THRESHOLD


def estimate_remaining_tasks(
    remaining_budget: float,
    avg_cost_per_task: float = 0.01
) -> int:
    """
    Estimate remaining tasks based on budget.
    
    Args:
        remaining_budget: Remaining budget in dollars
        avg_cost_per_task: Average cost per task
        
    Returns:
        Estimated remaining tasks
    """
    if avg_cost_per_task <= 0:
        return 0
    return int(remaining_budget / avg_cost_per_task)
