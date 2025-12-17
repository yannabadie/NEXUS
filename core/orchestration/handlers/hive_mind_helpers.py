"""
NEXUS V10.2 - Hive Mind Routing Helpers

Extracted helper functions for Hive Mind routing decisions.

Usage:
    from core.orchestration.handlers.hive_mind_helpers import (
        should_use_hive_mind,
        get_hive_complexity_mapping
    )
"""

from typing import Optional, Dict
import logging

logger = logging.getLogger("nexus.handlers.hive_mind")


# Complexity threshold for Hive Mind routing
HIVE_MIND_THRESHOLDS = {
    "TRIVIAL": False,   # Never use Hive Mind
    "SIMPLE": False,    # Never use Hive Mind
    "MODERATE": True,   # Use if hive_mind_moderate=True (default)
    "COMPLEX": True,    # Always use Hive Mind
    "EXPERT": True,     # Always use Hive Mind
}


def should_use_hive_mind(
    complexity_name: str,
    hive_mind_available: bool = True,
    hive_mind_moderate: bool = True
) -> bool:
    """
    Determine if task should be routed to Hive Mind pipeline.
    
    Args:
        complexity_name: Task complexity name (TRIVIAL, SIMPLE, etc.)
        hive_mind_available: Whether Hive Mind is importable
        hive_mind_moderate: Config flag for MODERATE task routing
        
    Returns:
        True if should use Hive Mind
    """
    if not hive_mind_available:
        return False
    
    is_hive_threshold = HIVE_MIND_THRESHOLDS.get(complexity_name, False)
    
    # MODERATE requires special config check
    if complexity_name == "MODERATE":
        return is_hive_threshold and hive_mind_moderate
    
    return is_hive_threshold


def get_hive_complexity_mapping(swarm_complexity) -> Optional[str]:
    """
    Map swarm TaskComplexity to Hive Mind complexity name.
    
    Args:
        swarm_complexity: Swarm TaskComplexity enum
        
    Returns:
        Hive Mind complexity name or None
    """
    # Direct name mapping
    if hasattr(swarm_complexity, 'name'):
        return swarm_complexity.name
    return str(swarm_complexity)


def format_hive_mind_result(hive_result: Dict) -> Dict:
    """
    Format Hive Mind result for FSM consumption.
    
    Args:
        hive_result: Raw Hive Mind result
        
    Returns:
        Formatted result dict
    """
    if not hive_result:
        return {
            "success": False,
            "output": "Hive Mind returned no result",
            "phases": [],
            "error": "Empty result"
        }
    
    return {
        "success": hive_result.get("success", False),
        "output": hive_result.get("output", ""),
        "phases": hive_result.get("phases_completed", []),
        "agents_used": hive_result.get("agents_used", []),
        "duration": hive_result.get("total_duration", 0),
        "tokens": hive_result.get("total_tokens", 0),
        "error": hive_result.get("error")
    }
