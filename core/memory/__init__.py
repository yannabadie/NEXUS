"""
NEXUS V7.8 HIVE MIND Memory Module

Memory systems for NEXUS:
- AutoMemory: Learning from task execution patterns (V7.5)
- SuccessMemory: Swarm task success storage (V7.6 Phase 10a)
- ProjectMemory: Project knowledge RAG (V7.8 Phase 10c)
"""

from .auto_memory import AutoMemory, get_auto_memory, MemoryEntry
from .success_memory import SuccessMemory, SuccessEntry, get_success_memory
from .project_memory import ProjectMemory, Chunk, IndexStats

__all__ = [
    # Auto-Memory (V7.5)
    "AutoMemory",
    "get_auto_memory",
    "MemoryEntry",
    # Success Memory (V7.6)
    "SuccessMemory",
    "SuccessEntry",
    "get_success_memory",
    # Project Memory RAG (V7.8 Phase 10c)
    "ProjectMemory",
    "Chunk",
    "IndexStats",
]
