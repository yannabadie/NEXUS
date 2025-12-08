"""
NEXUS V7.9 - Memory Backends (Phase 10f)

Pluggable retrieval backends for ProjectMemory.

Available backends:
- TfidfBackend: Zero-dependency fallback (stdlib only)
- Bm25Backend: Better recall (~15%), requires bm25s

Usage:
    from core.memory.backends import MemoryBackend, TfidfBackend, Bm25Backend

    # Check availability
    if Bm25Backend.is_available():
        backend = Bm25Backend()
    else:
        backend = TfidfBackend()

    backend.build_index(chunks)
    results = backend.retrieve(query_terms, chunks, limit=5, min_score=0.05)
"""

from .base import MemoryBackend
from .tfidf import TfidfBackend
from .bm25 import Bm25Backend, BM25S_AVAILABLE, STEMMER_AVAILABLE

__all__ = [
    "MemoryBackend",
    "TfidfBackend",
    "Bm25Backend",
    "BM25S_AVAILABLE",
    "STEMMER_AVAILABLE",
]
