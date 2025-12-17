"""
NEXUS V10.2 - Execution Context Helpers

Extracted helper functions for execution context management.

Usage:
    from core.swarm.executors.context_helpers import (
        format_task_context,
        build_continuation_prompt
    )
"""

from typing import Dict, Optional, List
import logging

logger = logging.getLogger("nexus.executors.context")


def format_task_context(
    task_input: str,
    role: str,
    round_num: int = 0,
    previous_output: str = None,
    agent_assignments: Dict[str, str] = None
) -> str:
    """
    Format task context for agent invocation.
    
    Args:
        task_input: Original task description
        role: Agent's role (lead, support, etc.)
        round_num: Current round number
        previous_output: Output from previous round
        agent_assignments: Role to agent mapping
        
    Returns:
        Formatted context string
    """
    lines = [f"## Task\n{task_input}"]
    
    # Add role information
    if role:
        lines.append(f"\n## Your Role: {role.upper()}")
    
    # Add round info if not first round
    if round_num > 0:
        lines.append(f"\n## Round: {round_num + 1}")
    
    # Add previous output if available
    if previous_output:
        lines.append(f"\n## Previous Output\n{previous_output[:2000]}")
    
    return "\n".join(lines)


def build_continuation_prompt(
    original_task: str,
    previous_outputs: List[str],
    current_agent: str,
    instructions: str = None
) -> str:
    """
    Build continuation prompt for multi-round execution.
    
    Args:
        original_task: Original task description
        previous_outputs: List of previous round outputs
        current_agent: Current agent identifier
        instructions: Additional instructions
        
    Returns:
        Continuation prompt string
    """
    lines = [f"## Original Task\n{original_task}"]
    
    # Add previous outputs summary
    if previous_outputs:
        lines.append("\n## Progress So Far")
        for i, output in enumerate(previous_outputs[-3:]):  # Last 3 rounds
            lines.append(f"\n### Round {i + 1}\n{output[:1000]}")
    
    # Add instructions
    if instructions:
        lines.append(f"\n## Instructions\n{instructions}")
    else:
        lines.append("\n## Instructions\nContinue the task from where the previous round left off.")
    
    return "\n".join(lines)


def build_review_prompt(
    original_task: str,
    lead_output: str,
    reviewer_role: str = "support"
) -> str:
    """
    Build review prompt for lead-support mode.
    
    Args:
        original_task: Original task
        lead_output: Lead agent's output
        reviewer_role: Reviewer's role
        
    Returns:
        Review prompt string
    """
    return f"""## Original Task
{original_task}

## Lead Agent's Work
{lead_output[:3000]}

## Your Role: {reviewer_role.upper()}
Review the lead agent's work:
1. Check for correctness and completeness
2. Identify any issues or improvements
3. Either approve or suggest specific changes
"""


def format_parallel_merge_prompt(
    task: str,
    outputs: List[Dict[str, str]]
) -> str:
    """
    Format prompt for merging parallel outputs.
    
    Args:
        task: Original task
        outputs: List of {agent: output} dicts
        
    Returns:
        Merge prompt string
    """
    lines = [f"## Task\n{task}\n\n## Parallel Agent Outputs\n"]
    
    for i, output in enumerate(outputs, 1):
        agent = output.get("agent", f"Agent {i}")
        content = output.get("content", "")[:1500]
        lines.append(f"### {agent}\n{content}\n")
    
    lines.append("\n## Merge Instructions")
    lines.append("Synthesize the above outputs into a single coherent response.")
    lines.append("Take the best elements from each while avoiding redundancy.")
    
    return "\n".join(lines)


def get_agent_role_for_round(
    round_num: int,
    agents: List[str],
    mode: str = "ping_pong"
) -> str:
    """
    Determine agent role for a given round.
    
    Args:
        round_num: Current round number (0-indexed)
        agents: List of available agents
        mode: Execution mode
        
    Returns:
        Agent identifier for this round
    """
    if not agents:
        return "unknown"
    
    if mode == "ping_pong":
        return agents[round_num % len(agents)]
    elif mode == "sequential":
        return agents[min(round_num, len(agents) - 1)]
    else:
        return agents[0]
