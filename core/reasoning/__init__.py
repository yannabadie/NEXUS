"""
NEXUS V7 - Reasoning Module

Advanced reasoning patterns for complex problem-solving:
- Graph of Thought (GoT): Non-linear exploration with branching and merging
- Chain of Thought (CoT): Linear step-by-step reasoning
- Tree of Thought (ToT): Tree-based exploration with pruning

NOTE: GoT implementation is optional and loaded lazily by HybridSwarmEngine.
This module currently exports nothing - implementations pending.
To use GoT, create core/reasoning/graph_of_thought.py with the required classes.
"""

# V7 FIX: Make imports optional to avoid blocking the entire system
# GoT is a future enhancement, not required for core functionality

__all__ = []

# Lazy loading pattern - consumers should check availability:
# from core.reasoning import GOT_AVAILABLE
# if GOT_AVAILABLE:
#     from core.reasoning import GraphOfThought

GOT_AVAILABLE = False

try:
    from .graph_of_thought import (
        GraphOfThought,
        ThoughtNode,
        ThoughtGraph,
        ThoughtStatus,
        ThoughtType
    )
    GOT_AVAILABLE = True
    __all__ = [
        'GraphOfThought',
        'ThoughtNode',
        'ThoughtGraph',
        'ThoughtStatus',
        'ThoughtType',
        'GOT_AVAILABLE'
    ]
except ImportError:
    # GoT not implemented yet - this is OK
    GraphOfThought = None
    ThoughtNode = None
    ThoughtGraph = None
    ThoughtStatus = None
    ThoughtType = None
    __all__ = ['GOT_AVAILABLE']
