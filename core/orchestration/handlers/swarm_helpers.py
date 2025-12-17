"""
NEXUS V10.2 - Swarm State Helpers

Extracted helper functions for swarm-related FSM handlers.

Usage:
    from core.orchestration.handlers.swarm_helpers import (
        format_swarm_result,
        get_swarm_mode_description
    )
"""

from typing import Dict, Optional, List
import logging

logger = logging.getLogger("nexus.handlers.swarm")


# Swarm mode descriptions for user feedback
SWARM_MODE_DESCRIPTIONS = {
    "PARALLEL": "Both agents working independently",
    "SEQUENTIAL": "Agents working in sequence",
    "LEAD_SUPPORT": "Lead agent with support from secondary",
    "PING_PONG": "Alternating contributions",
    "SPECIALIST": "Domain specialist handling task",
    "RED_BLUE": "Adversarial review mode",
}


def get_swarm_mode_description(mode: str) -> str:
    """
    Get human-readable description for swarm mode.
    
    Args:
        mode: Swarm mode name
        
    Returns:
        Description string
    """
    return SWARM_MODE_DESCRIPTIONS.get(mode, f"Mode: {mode}")


def format_swarm_result(swarm_result: Dict, truncate_at: int = 1000) -> str:
    """
    Format swarm execution result for display.
    
    Args:
        swarm_result: Raw swarm result dict
        truncate_at: Max output length
        
    Returns:
        Formatted result string
    """
    if not swarm_result:
        return "No result from swarm"
    
    mode = swarm_result.get("mode", "unknown")
    output = swarm_result.get("output", "")
    
    # Truncate if needed
    if len(output) > truncate_at:
        output = output[:truncate_at] + "\n... [truncated]"
    
    mode_desc = get_swarm_mode_description(mode)
    return f"[{mode_desc}]\n\n{output}"


def extract_swarm_metrics(swarm_result: Dict) -> Dict:
    """
    Extract metrics from swarm execution result.
    
    Args:
        swarm_result: Swarm result dict
        
    Returns:
        Metrics dict
    """
    analysis = swarm_result.get("analysis", {})
    execution = swarm_result.get("execution", {})
    
    return {
        "mode": swarm_result.get("mode", "unknown"),
        "rounds": execution.get("rounds", 0) if isinstance(execution, dict) else 0,
        "consensus_reached": swarm_result.get("consensus", False),
        "agents_used": execution.get("agents", []) if isinstance(execution, dict) else [],
        "complexity": analysis.get("complexity", "unknown") if isinstance(analysis, dict) else "unknown",
    }


def should_use_swarm(complexity_value: int, swarm_enabled: bool = True) -> bool:
    """
    Determine if task should use swarm mode.
    
    Args:
        complexity_value: Task complexity (1-5)
        swarm_enabled: Whether swarm is enabled in config
        
    Returns:
        True if should use swarm
    """
    # MODERATE (3) or higher → swarm
    return swarm_enabled and complexity_value >= 3
