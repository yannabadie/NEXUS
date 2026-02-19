"""
NEXUS V12.4 - Memory Package

Consolidated memory components:
- memory: RAG, project memory, success memory, blacklists
- prompts: Prompt loading, versioning, optimization
- skills: Skill crystallization, experience distillation

P5.6 Phase 5: Package consolidation for reduced cognitive load.
"""

# Memory exports
from core.memory_pkg.memory import (
    AutoMemory,
    get_auto_memory,
    MemoryEntry,
    SuccessMemory,
    SuccessEntry,
    get_success_memory,
    SuccessMemoryV2,
    get_success_memory_v2,
    reset_success_memory_v2,
    StrategyBlacklistV2,
    BlacklistedStrategy,
    get_strategy_blacklist_v2,
    reset_strategy_blacklist_v2,
    ProjectMemory,
    Chunk,
    ScoredChunk,
    IndexStats,
    MemoryBackend,
    TfidfBackend,
    Bm25Backend,
    DenseBackend,
    BM25S_AVAILABLE,
    LANCEDB_AVAILABLE,
    SENTENCE_TRANSFORMERS_AVAILABLE,
    MemoryService,
    MemoryStatus,
    LearnResult,
    ForgetResult,
    QueryResult,
    UniversalIngestor,
    DOCLING_AVAILABLE,
    RAGNamespaceManager,
    NamespaceInfo,
)

# Prompts exports
from core.memory_pkg.prompts import (
    load_prompt,
    resolve_includes,
    PromptRegistry,
    PromptVersion,
    PromptEntry,
    PromptOptimizer,
    PromptAnalysis,
    PromptIssue,
    PromptStats,
    PromptOutcome,
    ConflictResult,
    get_optimizer,
    reset_optimizer,
)

# Skills exports
from core.memory_pkg.skills import (
    SkillCrystallizer,
    ToolCallRecord,
    ToolSequencePattern,
    CrystallizedSkill,
    get_crystallizer,
    reset_crystallizer,
    ExperienceDistiller,
    StrategicPrinciple,
    PrincipleCategory,
    DistillationResult,
    RetrievalResult,
    DistillerStats,
    get_experience_distiller,
    reset_experience_distiller,
)

__all__ = [
    # Memory
    "AutoMemory",
    "get_auto_memory",
    "MemoryEntry",
    "SuccessMemory",
    "SuccessEntry",
    "get_success_memory",
    "SuccessMemoryV2",
    "get_success_memory_v2",
    "reset_success_memory_v2",
    "StrategyBlacklistV2",
    "BlacklistedStrategy",
    "get_strategy_blacklist_v2",
    "reset_strategy_blacklist_v2",
    "ProjectMemory",
    "Chunk",
    "ScoredChunk",
    "IndexStats",
    "MemoryBackend",
    "TfidfBackend",
    "Bm25Backend",
    "DenseBackend",
    "BM25S_AVAILABLE",
    "LANCEDB_AVAILABLE",
    "SENTENCE_TRANSFORMERS_AVAILABLE",
    "MemoryService",
    "MemoryStatus",
    "LearnResult",
    "ForgetResult",
    "QueryResult",
    "UniversalIngestor",
    "DOCLING_AVAILABLE",
    "RAGNamespaceManager",
    "NamespaceInfo",
    # Prompts
    "load_prompt",
    "resolve_includes",
    "PromptRegistry",
    "PromptVersion",
    "PromptEntry",
    "PromptOptimizer",
    "PromptAnalysis",
    "PromptIssue",
    "PromptStats",
    "PromptOutcome",
    "ConflictResult",
    "get_optimizer",
    "reset_optimizer",
    # Skills
    "SkillCrystallizer",
    "ToolCallRecord",
    "ToolSequencePattern",
    "CrystallizedSkill",
    "get_crystallizer",
    "reset_crystallizer",
    "ExperienceDistiller",
    "StrategicPrinciple",
    "PrincipleCategory",
    "DistillationResult",
    "RetrievalResult",
    "DistillerStats",
    "get_experience_distiller",
    "reset_experience_distiller",
]

__version__ = "12.4.0"
