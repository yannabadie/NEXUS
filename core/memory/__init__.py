"""
NEXUS V9.1 Memory Module

Memory systems for NEXUS:
- AutoMemory: Learning from task execution patterns (V7.5)
- SuccessMemory: Swarm task success storage (V7.6 Phase 10a)
- ProjectMemory: Project knowledge RAG (V7.8 Phase 10c)
- Backend Abstraction: Pluggable retrieval backends (V7.9 Phase 10f)
- Dense Embeddings: Semantic retrieval (V7.9 Phase 10g)
- MemoryService: Service Layer for memory operations (V9.1)
"""

from .auto_memory import AutoMemory, get_auto_memory, MemoryEntry
from .success_memory import SuccessMemory, SuccessEntry, get_success_memory
from .project_memory import ProjectMemory
from .types import Chunk, IndexStats

# V7.9 Phase 10f + 10g: Backend exports
from .backends import (
    MemoryBackend, TfidfBackend, Bm25Backend, DenseBackend,
    BM25S_AVAILABLE, LANCEDB_AVAILABLE, SENTENCE_TRANSFORMERS_AVAILABLE
)

# V9.1: Service Layer
from .service import (
    MemoryService,
    MemoryStatus,
    LearnResult,
    ForgetResult,
    QueryResult,
)

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
    # Backend Abstraction (V7.9 Phase 10f + 10g)
    "MemoryBackend",
    "TfidfBackend",
    "Bm25Backend",
    "DenseBackend",
    "BM25S_AVAILABLE",
    "LANCEDB_AVAILABLE",
    "SENTENCE_TRANSFORMERS_AVAILABLE",
    # Service Layer (V9.1)
    "MemoryService",
    "MemoryStatus",
    "LearnResult",
    "ForgetResult",
    "QueryResult",
]
