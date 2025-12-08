"""
NEXUS V7.9 - Memory Backends (Phase 10f + 10g)

Pluggable retrieval backends for ProjectMemory.

Available backends:
- TfidfBackend: Zero-dependency fallback (stdlib only)
- Bm25Backend: Better recall (~15%), requires bm25s
- DenseBackend: Semantic retrieval (~+10% recall), requires lancedb + sentence-transformers

Usage:
    from core.memory.backends import MemoryBackend, TfidfBackend, Bm25Backend, DenseBackend

    # Check availability and select best backend
    if DenseBackend.is_available():
        backend = DenseBackend(storage_path)  # Semantic search
    elif Bm25Backend.is_available():
        backend = Bm25Backend()  # Sparse lexical
    else:
        backend = TfidfBackend()  # Fallback

    backend.build_index(chunks)
    results = backend.retrieve(query_terms, chunks, limit=5, min_score=0.05, raw_query="...")
"""

from .base import MemoryBackend
from .tfidf import TfidfBackend
from .bm25 import Bm25Backend, BM25S_AVAILABLE, STEMMER_AVAILABLE
from .dense import DenseBackend, LANCEDB_AVAILABLE, SENTENCE_TRANSFORMERS_AVAILABLE

__all__ = [
    "MemoryBackend",
    "TfidfBackend",
    "Bm25Backend",
    "BM25S_AVAILABLE",
    "STEMMER_AVAILABLE",
    "DenseBackend",
    "LANCEDB_AVAILABLE",
    "SENTENCE_TRANSFORMERS_AVAILABLE",
]
