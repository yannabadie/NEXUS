"""
NEXUS V13.0 MEMORIA UNIVERSALIS Memory Module

Memory systems for NEXUS:
- AutoMemory: Learning from task execution patterns (V7.5)
- SuccessMemory: Swarm task success storage (V7.6 Phase 10a)
- ProjectMemory: Project knowledge RAG (V7.8 Phase 10c)
- Backend Abstraction: Pluggable retrieval backends (V7.9 Phase 10f)
- Dense Embeddings: Semantic retrieval (V7.9 Phase 10g)
- MemoryService: Service Layer for memory operations (V9.1)
- UniversalIngestor: Multi-format document ingestion (V13.0)
- RAGNamespaceManager: Multi-namespace RAG support (V13.0)
"""

from .auto_memory import AutoMemory, get_auto_memory, MemoryEntry
from .success_memory import SuccessMemory, SuccessEntry, get_success_memory
from .project_memory import ProjectMemory
from .types import Chunk, ScoredChunk, IndexStats

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

# V13.0 MEMORIA UNIVERSALIS: Multi-format ingestion
try:
    from .ingestors import UniversalIngestor, DOCLING_AVAILABLE
except ImportError:
    UniversalIngestor = None
    DOCLING_AVAILABLE = False

# V13.0 MEMORIA UNIVERSALIS: Multi-namespace RAG
from .namespace_manager import RAGNamespaceManager, NamespaceInfo

# V12.4 OPERATION PRISM: Multi-tenant memory isolation
from .tenant_memory import TenantMemoryService, DEFAULT_TENANT

# V12.4 COGNITIVE BOOST: Conversation history
from .conversation_store import (
    ConversationStore,
    ConversationSession,
    ConversationTurn,
    ConversationSummary,
    SearchResult as ConversationSearchResult,
)

# V12.4 COGNITIVE BOOST: Context Compressor
from .context_compressor import (
    ContextCompressor,
    CompressTurn,
    CompressionResult,
    ContextShift,
    get_compressor,
    reset_compressor,
)

# V12.4 COGNITIVE BOOST: Cache Manager
from .cache_manager import (
    CacheManager,
    CacheEntry,
    CacheStats,
    get_cache_manager,
    reset_cache_manager,
)

# V12.4 COGNITIVE BOOST: Memory Pressure Monitor
from .memory_pressure_monitor import (
    MemoryPressureMonitor,
    MemorySnapshot,
    EvictionEvent,
    PressureLevel,
    PressureStats,
    get_pressure_monitor,
    reset_pressure_monitor,
)

# V12.4 COGNITIVE BOOST: Memory Decay Scorer (Ebbinghaus forgetting curve)
from .decay_scorer import (
    MemoryDecayScorer,
    AccessRecord,
    DecayScorerStats,
    get_decay_scorer,
    reset_decay_scorer,
)

# V12.4 COGNITIVE BOOST: Context Window Tracker
from .context_window_tracker import (
    ContextWindowTracker,
    ContextUsageRecord,
    CompressionEvent,
    ContextTrackerStats,
    get_context_tracker,
    reset_context_tracker,
)

# V12.4 COGNITIVE BOOST: Pointer Memory (arxiv:2511.22729)
from .pointer_memory import (
    PointerMemory,
    Pointer,
    PointerStats,
    get_pointer_memory,
    reset_pointer_memory,
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
    "ScoredChunk",
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
    # V13.0 MEMORIA UNIVERSALIS
    "UniversalIngestor",
    "DOCLING_AVAILABLE",
    "RAGNamespaceManager",
    "NamespaceInfo",
    # V12.4 OPERATION PRISM: Multi-tenant
    "TenantMemoryService",
    "DEFAULT_TENANT",
    # V12.4 COGNITIVE BOOST: Conversation history
    "ConversationStore",
    "ConversationSession",
    "ConversationTurn",
    "ConversationSummary",
    "ConversationSearchResult",
    # V12.4 COGNITIVE BOOST: Context Compressor
    "ContextCompressor",
    "CompressTurn",
    "CompressionResult",
    "ContextShift",
    "get_compressor",
    "reset_compressor",
    # V12.4 COGNITIVE BOOST: Cache Manager
    "CacheManager",
    "CacheEntry",
    "CacheStats",
    "get_cache_manager",
    "reset_cache_manager",
    # V12.4 COGNITIVE BOOST: Memory Pressure Monitor
    "MemoryPressureMonitor",
    "MemorySnapshot",
    "EvictionEvent",
    "PressureLevel",
    "PressureStats",
    "get_pressure_monitor",
    "reset_pressure_monitor",
    # V12.4 COGNITIVE BOOST: Context Window Tracker
    "ContextWindowTracker",
    "ContextUsageRecord",
    "CompressionEvent",
    "ContextTrackerStats",
    "get_context_tracker",
    "reset_context_tracker",
    # V12.4 COGNITIVE BOOST: Memory Decay Scorer (Ebbinghaus curve)
    "MemoryDecayScorer",
    "AccessRecord",
    "DecayScorerStats",
    "get_decay_scorer",
    "reset_decay_scorer",
    # V12.4 COGNITIVE BOOST: Pointer Memory (arxiv:2511.22729)
    "PointerMemory",
    "Pointer",
    "PointerStats",
    "get_pointer_memory",
    "reset_pointer_memory",
]
