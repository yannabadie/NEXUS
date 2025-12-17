"""
NEXUS V10.2 - Completion Detection Helpers

Extracted helper functions for detecting task completion.

Usage:
    from core.swarm.executors.completion_helpers import (
        is_task_complete,
        COMPLETION_PATTERN
    )
"""

import re
from typing import List
import logging

logger = logging.getLogger("nexus.executors.completion")

# V8.3.4 FL-002: Regex pattern for completion detection (word boundaries)
COMPLETION_PATTERN = re.compile(
    r'\b(FINISHED|TASK\s+COMPLETE|COMPLETED|ALL\s+DONE)\b',
    re.IGNORECASE
)

# Patterns indicating work is still ongoing
ONGOING_PATTERNS = [
    r'\bwill\s+(now|next|then)\b',
    r'\blet\s+me\s+(start|begin|first)\b',
    r'\bnext\s+step\b',
    r'\bstill\s+(need|have)\s+to\b',
    r'\bworking\s+on\b',
    r'\bin\s+progress\b',
]

# Compiled ongoing patterns
ONGOING_COMPILED = [re.compile(p, re.IGNORECASE) for p in ONGOING_PATTERNS]


def is_task_complete(content: str) -> bool:
    """
    Check if content signals task completion.
    
    Uses word boundaries to avoid false positives like "I'm not DONE yet".
    Also rejects if ongoing work indicators are present.
    
    Args:
        content: Agent output content
        
    Returns:
        True if task appears complete
    """
    if not content:
        return False
    
    # Check for completion markers
    has_completion = bool(COMPLETION_PATTERN.search(content))
    
    if not has_completion:
        return False
    
    # Check for ongoing work indicators (false positive prevention)
    for pattern in ONGOING_COMPILED:
        if pattern.search(content):
            logger.debug(f"Completion rejected - ongoing work detected")
            return False
    
    return True


def detect_completion_confidence(content: str) -> float:
    """
    Calculate confidence that task is complete.
    
    Args:
        content: Agent output content
        
    Returns:
        Confidence score (0.0-1.0)
    """
    if not content:
        return 0.0
    
    score = 0.0
    
    # Check completion markers
    if COMPLETION_PATTERN.search(content):
        score += 0.5
    
    # Check for summary/conclusion phrases
    summary_patterns = [
        r'\bin\s+summary\b',
        r'\bto\s+summarize\b',
        r'\bthe\s+result\s+is\b',
        r'\bhere\s+is\s+the\s+(final|complete)\b',
    ]
    
    for pattern in summary_patterns:
        if re.search(pattern, content, re.IGNORECASE):
            score += 0.15
    
    # Penalize ongoing work indicators
    for pattern in ONGOING_COMPILED:
        if pattern.search(content):
            score -= 0.3
    
    return max(0.0, min(1.0, score))


def extract_final_result(content: str) -> str:
    """
    Extract the final result from agent output.
    
    Args:
        content: Full agent output
        
    Returns:
        Extracted final result
    """
    # Look for explicit result markers
    markers = [
        r'FINAL\s+RESULT:?\s*(.+)',
        r'RESULT:?\s*(.+)',
        r'OUTPUT:?\s*(.+)',
        r'ANSWER:?\s*(.+)',
    ]
    
    for marker in markers:
        match = re.search(marker, content, re.IGNORECASE | re.DOTALL)
        if match:
            return match.group(1).strip()
    
    # Return last paragraph as fallback
    paragraphs = content.strip().split('\n\n')
    return paragraphs[-1] if paragraphs else content
