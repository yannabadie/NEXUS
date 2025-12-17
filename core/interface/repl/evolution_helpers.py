"""
NEXUS V10.2 - Evolution Command Helpers

Extracted helper functions for /evolve commands.

Usage:
    from core.interface.repl.evolution_helpers import (
        format_evolution_status,
        calculate_fitness_trend
    )
"""

from typing import Dict, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger("nexus.repl.evolution")


def format_evolution_status(
    evolution_count: int,
    stagnation_counter: int,
    auto_threshold: int = 50
) -> str:
    """
    Format evolution status as a report string.
    
    Args:
        evolution_count: Number of evolutions performed
        stagnation_counter: Current stagnation counter
        auto_threshold: Threshold for auto-evolution
        
    Returns:
        Formatted status string
    """
    progress_pct = (stagnation_counter / auto_threshold * 100) if auto_threshold > 0 else 0
    progress_bar = "█" * int(progress_pct / 10) + "░" * (10 - int(progress_pct / 10))
    
    lines = [
        "## Evolution Status",
        "",
        "| Metric | Value |",
        "|--------|-------|",
        f"| Total Evolutions | {evolution_count} |",
        f"| Stagnation Counter | {stagnation_counter}/{auto_threshold} |",
        f"| Progress | [{progress_bar}] {progress_pct:.0f}% |",
    ]
    
    if stagnation_counter >= auto_threshold * 0.8:
        lines.append("")
        lines.append("⚠️ Approaching auto-evolution threshold!")
    
    return "\n".join(lines)


def format_fitness_scores(scores: Dict) -> str:
    """
    Format fitness scores as a table.
    
    Args:
        scores: Dict of agent -> fitness score
        
    Returns:
        Formatted table string
    """
    if not scores:
        return "No fitness scores available."
    
    lines = [
        "",
        "### Fitness Scores",
        "",
        "| Agent | Fitness | Grade |",
        "|-------|---------|-------|"
    ]
    
    for agent, score in sorted(scores.items(), key=lambda x: x[1], reverse=True):
        grade = get_fitness_grade(score)
        lines.append(f"| {agent} | {score:.3f} | {grade} |")
    
    return "\n".join(lines)


def get_fitness_grade(score: float) -> str:
    """
    Convert fitness score to letter grade.
    
    Args:
        score: Fitness score (0-1)
        
    Returns:
        Letter grade (A-F)
    """
    if score >= 0.9:
        return "A+"
    elif score >= 0.8:
        return "A"
    elif score >= 0.7:
        return "B"
    elif score >= 0.6:
        return "C"
    elif score >= 0.5:
        return "D"
    else:
        return "F"


def calculate_fitness_trend(history: List[Dict]) -> Dict:
    """
    Calculate fitness trend from history.
    
    Args:
        history: List of fitness records
        
    Returns:
        Trend analysis dict
    """
    if len(history) < 2:
        return {"trend": "insufficient_data", "change": 0.0}
    
    # Compare last score to average
    scores = [h.get("score", 0) for h in history]
    avg = sum(scores) / len(scores)
    last = scores[-1]
    
    if last > avg + 0.05:
        trend = "improving"
    elif last < avg - 0.05:
        trend = "declining"
    else:
        trend = "stable"
    
    return {
        "trend": trend,
        "change": last - avg,
        "last": last,
        "average": avg
    }


def should_auto_evolve(stagnation: int, threshold: int, enabled: bool = True) -> bool:
    """
    Check if auto-evolution should be triggered.
    
    Args:
        stagnation: Current stagnation counter
        threshold: Auto-evolution threshold
        enabled: Whether auto-evolution is enabled
        
    Returns:
        True if should auto-evolve
    """
    return enabled and stagnation >= threshold
