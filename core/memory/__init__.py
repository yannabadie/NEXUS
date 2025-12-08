"""
NEXUS V7.9 Memory Module

Memory systems for NEXUS:
- AutoMemory: Learning from task execution patterns (V7.5)
- SuccessMemory: Swarm task success storage (V7.6 Phase 10a)
- ProjectMemory: Project knowledge RAG (V7.8 Phase 10c)
- Backend Abstraction: Pluggable retrieval backends (V7.9 Phase 10f)
"""

from .auto_memory import AutoMemory, get_auto_memory, MemoryEntry
from .success_memory import SuccessMemory, SuccessEntry, get_success_memory
from .project_memory import ProjectMemory
from .types import Chunk, IndexStats

# V7.9 Phase 10f: Backend exports
from .backends import MemoryBackend, TfidfBackend, Bm25Backend, BM25S_AVAILABLE

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
    # Backend Abstraction (V7.9 Phase 10f)
    "MemoryBackend",
    "TfidfBackend",
    "Bm25Backend",
    "BM25S_AVAILABLE",
]
