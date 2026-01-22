"""
NCM Tests - Unit tests for Phase 0.1 components.

This package contains unit tests for the NCM (NEXUS Code Modernization) framework.
Tests validate core components before stress testing and production deployment.

Test Structure:
    - test_models.py: Dataclass validation, field validators
    - test_locks.py: LockManager, deadlock prevention, timeouts
    - test_story_shard.py: StoryShardEngine, RAG validation
    - test_orchestrator.py: NCMOrchestrator basic functionality
    - test_ncm_stress.py: Stress test with 1000 synthetic stories (Phase 0.3)

Test Philosophy:
    - Fast unit tests (<1s each)
    - Mocked external dependencies (MemoryService, OrchestratorV7)
    - Focus on NCM logic, not NEXUS integration
    - Stress tests separate (tests/ncm/test_ncm_stress.py)
"""
