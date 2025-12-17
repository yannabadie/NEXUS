"""
NEXUS V10.2 - Execution Result Helpers

Extracted helper functions for execution results.

Usage:
    from core.swarm.executors.result_helpers import (
        format_execution_result,
        calculate_total_tokens
    )
"""

from typing import List, Dict, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger("nexus.executors.result")


def calculate_total_tokens(agent_outputs: List[Dict]) -> int:
    """
    Calculate total tokens used across all outputs.
    
    Args:
        agent_outputs: List of agent output dicts
        
    Returns:
        Total token count
    """
    return sum(o.get("tokens_used", 0) for o in agent_outputs)


def calculate_total_time(agent_outputs: List[Dict]) -> float:
    """
    Calculate total execution time.
    
    Args:
        agent_outputs: List of agent output dicts
        
    Returns:
        Total time in seconds
    """
    return sum(o.get("time_seconds", 0.0) for o in agent_outputs)


def format_execution_result(
    mode: str,
    status: str,
    final_output: str,
    agent_outputs: List[Dict],
    rounds: int
) -> Dict:
    """
    Format execution result as dict.
    
    Args:
        mode: Execution mode name
        status: Execution status
        final_output: Final merged output
        agent_outputs: List of agent outputs
        rounds: Total rounds executed
        
    Returns:
        Formatted result dict
    """
    return {
        "mode": mode,
        "status": status,
        "final_output": final_output,
        "rounds": rounds,
        "total_tokens": calculate_total_tokens(agent_outputs),
        "total_time": calculate_total_time(agent_outputs),
        "agent_outputs": [
            {
                "agent": o.get("agent_id", "unknown"),
                "status": o.get("status", "success"),
                "tokens": o.get("tokens_used", 0),
                "time": o.get("time_seconds", 0.0)
            }
            for o in agent_outputs
        ]
    }


def merge_parallel_outputs(
    outputs: List[Dict],
    strategy: str = "best"
) -> str:
    """
    Merge outputs from parallel execution.
    
    Args:
        outputs: List of agent output dicts with content
        strategy: Merge strategy (best, concatenate, first)
        
    Returns:
        Merged output string
    """
    if not outputs:
        return ""
    
    contents = [o.get("content", "") for o in outputs if o.get("content")]
    
    if not contents:
        return ""
    
    if strategy == "first":
        return contents[0]
    
    if strategy == "concatenate":
        return "\n\n---\n\n".join(contents)
    
    # Default: "best" - return longest as heuristic
    return max(contents, key=len)


def get_execution_summary(result: Dict) -> str:
    """
    Get human-readable execution summary.
    
    Args:
        result: Execution result dict
        
    Returns:
        Summary string
    """
    mode = result.get("mode", "unknown")
    status = result.get("status", "unknown")
    rounds = result.get("rounds", 0)
    tokens = result.get("total_tokens", 0)
    time_s = result.get("total_time", 0.0)
    
    return (
        f"Mode: {mode} | Status: {status} | "
        f"Rounds: {rounds} | Tokens: {tokens} | Time: {time_s:.2f}s"
    )


def should_retry(status: str, error: Optional[str] = None) -> bool:
    """
    Determine if execution should be retried.
    
    Args:
        status: Execution status
        error: Error message if any
        
    Returns:
        True if should retry
    """
    # Don't retry successful executions
    if status in ["completed", "converged"]:
        return False
    
    # Don't retry certain errors
    if error:
        no_retry_errors = [
            "rate limit",
            "quota exceeded",
            "authentication",
            "unauthorized"
        ]
        for e in no_retry_errors:
            if e.lower() in error.lower():
                return False
    
    return True
