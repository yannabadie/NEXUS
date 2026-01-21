"""
NCM (NEXUS Completion Method) - Meta-Bootstrapping Framework

This package implements the NCM orchestration layer for completing NEXUS V12.4
by resolving 10,602 issues through story-based multi-agent collaboration.

Architecture:
    NCM is a CLIENT of OrchestratorV7, not a replacement. It uses NEXUS's
    existing orchestration capabilities (FSM, HiveMind, Swarm, RAG, Evolution)
    to coordinate specialized agents working on story-sharded tasks.

Key Components:
    - NCMOrchestrator: Story queue coordinator (invokes OrchestratorV7)
    - StoryShardEngine: Audit report parser → story queue
    - CrewManager: Skill-based agent assignment
    - LockManager: File locking to prevent races

Blind Spot Mitigations:
    #1: Coordination → Leverage OrchestratorV7
    #2: File Races → LockManager (advisory locks)
    #3: Prompt Decay → PromptRefreshSystem (every 500 tool calls)
    #4: RAG Poisoning → Validation gate in StoryShardEngine
    #5: Token Budget → TokenBudgetMonitor (alert at thresholds)
    #6: State Corruption → StateSnapshotSystem (every 100 stories)
    #7: Test Regression → Validation after each story
    #8: Skill Mismatch → CrewManager skill matrix

Usage:
    from core.ncm import NCMOrchestrator, NCMConfig

    config = NCMConfig(story_batch_size=50, token_limit=100_000_000)
    ncm = NCMOrchestrator(orchestrator=orch, workspace_path=Path("workspace"), config=config)

    # Execute pilot (100 stories)
    results = await ncm.execute_batch(story_count=100, priority="P2")

    # Check metrics
    metrics = ncm.get_metrics()
    print(f"Success rate: {metrics.success_rate:.2%}")
"""

from core.ncm.models import (
    StoryPriority,
    IssueDomain,
    StoryStatus,
    SwarmMode,
    Story,
    CrewAssignment,
    AgentSkill,
    ValidationResult,
    ExecutionMetrics,
    StateSnapshot,
    RAGValidationResult,
    NCMConfig,
)

__all__ = [
    # Enums
    "StoryPriority",
    "IssueDomain",
    "StoryStatus",
    "SwarmMode",
    # Dataclasses
    "Story",
    "CrewAssignment",
    "AgentSkill",
    "ValidationResult",
    "ExecutionMetrics",
    "StateSnapshot",
    "RAGValidationResult",
    "NCMConfig",
]

__version__ = "0.1.0"
__author__ = "NEXUS V12.4 - Claude & Gemini"
