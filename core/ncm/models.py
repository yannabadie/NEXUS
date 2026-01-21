"""
NCM Models - NEXUS Completion Method

Dataclasses for NCM story management, crew assignment, and execution tracking.
Part of Phase 0: Meta-Bootstrapping implementation.
"""
from dataclasses import dataclass, field
from typing import List, Set, Dict, Optional, Any
from pathlib import Path
from datetime import datetime
from enum import Enum


class StoryPriority(str, Enum):
    """
    Story priority levels for execution ordering.

    Priority determines execution order (P0 → P1 → P2):
    - P0: Critical issues (40 HIGH security issues)
    - P1: High priority tech debt (God classes, type errors)
    - P2: Low priority cleanup (dead imports, docstrings)
    """
    P0 = "P0"
    P1 = "P1"
    P2 = "P2"


class IssueDomain(str, Enum):
    """
    Issue domains for skill-based crew assignment.

    Used by CrewManager to match stories with agent expertise:
    - REFACTORING: God class decomposition, code restructuring
    - SECURITY: Vulnerability fixes, hardcoded secrets
    - TESTING: Test writing, coverage improvement
    - EVOLUTION: Agent spawning, mutation generation
    - DOCUMENTATION: Docstrings, README updates
    - CLEANUP: Dead imports, unused code removal
    - TYPING: Type hint additions, mypy fixes
    """
    REFACTORING = "refactoring"
    SECURITY = "security"
    TESTING = "testing"
    EVOLUTION = "evolution"
    DOCUMENTATION = "documentation"
    CLEANUP = "cleanup"
    TYPING = "typing"


class StoryStatus(str, Enum):
    """
    Story execution status for tracking progress.

    Lifecycle: PENDING → IN_PROGRESS → (SUCCESS | FAILED | PARTIAL)
    - PENDING: Story in queue, not yet started
    - IN_PROGRESS: Currently executing via OrchestratorV7
    - SUCCESS: All files modified, tests pass
    - FAILED: Execution failed, see logs for details
    - PARTIAL: Some files modified, some failed (requires retry)
    """
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"


class SwarmMode(str, Enum):
    """
    Swarm collaboration modes for crew execution.

    Determines how agents collaborate on a story:
    - PARALLEL: Independent work, merge results (dead imports)
    - SEQUENTIAL: Ordered execution (type errors to avoid races)
    - LEAD_SUPPORT: Lead drives, support assists (God class refactoring)
    - PING_PONG: Rapid alternation until convergence (iterative fixes)
    - SPECIALIST: Single expert handles all (clear domain match)
    - RED_BLUE: Adversarial propose/attack/defend (security fixes)
    """
    PARALLEL = "PARALLEL"
    SEQUENTIAL = "SEQUENTIAL"
    LEAD_SUPPORT = "LEAD_SUPPORT"
    PING_PONG = "PING_PONG"
    SPECIALIST = "SPECIALIST"
    RED_BLUE = "RED_BLUE"


@dataclass
class Story:
    """
    A single work item (one or more related issues from audit report).

    Story Sharding Strategy:
    - God classes → 1 story per class (3 stories)
    - Security issues → 1 story per vulnerability (4 stories)
    - Dead imports → 1 story per module (~30 stories batched)
    - Type errors → 1 story per module (~80 stories batched)

    Total: 10,602 issues → ~500 stories

    Examples:
        Story(
            story_id="STORY-001",
            priority=StoryPriority.P1,
            domains={IssueDomain.REFACTORING},
            description="Refactor fsm_handlers.py (1838 LOC) into 12 handler files",
            target_files=[Path("core/fsm/fsm_handlers.py")],
            test_files=[Path("tests/test_fsm_handlers.py")],
        )
    """
    story_id: str
    priority: StoryPriority
    domains: Set[IssueDomain]
    description: str
    target_files: List[Path]
    test_files: List[Path]
    status: StoryStatus = StoryStatus.PENDING
    needs_human_review: bool = False
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    tokens_used: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CrewAssignment:
    """
    Agent assignment for a story (skill-matched crew).

    CrewManager assigns agents based on:
    - Skill matrix (story.domains ∩ agent.expertise)
    - Workload balancing (avoid overloading one agent)
    - Fault isolation (no conflicting file assignments)

    Example:
        CrewAssignment(
            story_id="STORY-001",
            agent_ids=["REFACTORING_AGENT_V1", "TESTING_AGENT_V1"],
            swarm_mode=SwarmMode.LEAD_SUPPORT,
            assigned_at=datetime.now(),
        )
    """
    story_id: str
    agent_ids: List[str]
    swarm_mode: SwarmMode
    assigned_at: datetime = field(default_factory=datetime.now)
    lead_agent_id: Optional[str] = None  # For LEAD_SUPPORT mode
    role_assignments: Dict[str, str] = field(default_factory=dict)  # agent_id → role


@dataclass
class AgentSkill:
    """
    Agent skill matrix entry (expertise + performance metrics).

    Built from agent birth certificates:
    - workspace/ncm/agents/*/birth_certificate.json

    Used by CrewManager for intelligent crew assignment:
    - High expertise score → preferred for matching domains
    - High success rate → prioritized for P0 stories
    - Low avg_tokens → prioritized when nearing token budget

    Example:
        AgentSkill(
            agent_id="REFACTORING_AGENT_V1",
            expertise={IssueDomain.REFACTORING, IssueDomain.TYPING},
            success_rate=0.92,
            avg_tokens=45000,
            stories_completed=23,
        )
    """
    agent_id: str
    expertise: Set[IssueDomain]
    success_rate: float = 0.0
    avg_tokens: int = 0
    stories_completed: int = 0
    stories_failed: int = 0
    last_active: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidationResult:
    """
    Story validation result after execution.

    Validation phases (Blind Spot #7 mitigation):
    1. Syntax check (Python ast.parse)
    2. Import check (no circular imports)
    3. Type check (mypy --strict on modified files)
    4. Unit tests (pytest on test_files)
    5. Integration tests (pytest full suite if P0 story)

    Example:
        ValidationResult(
            story_id="STORY-001",
            passed=True,
            syntax_valid=True,
            imports_valid=True,
            types_valid=True,
            tests_passed=True,
            test_results={"passed": 12, "failed": 0},
        )
    """
    story_id: str
    passed: bool
    syntax_valid: bool = False
    imports_valid: bool = False
    types_valid: bool = False
    tests_passed: bool = False
    test_results: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    validated_at: datetime = field(default_factory=datetime.now)


@dataclass
class ExecutionMetrics:
    """
    NCM execution metrics for progress tracking.

    Tracked per phase (pilot, 2A, 2B, 3A, 3B):
    - Success rate (target: 95%+)
    - Token usage (budget: 100M total)
    - Stories per hour (baseline for projections)
    - Agent utilization (workload balancing)

    Example:
        ExecutionMetrics(
            phase="pilot",
            stories_total=100,
            stories_completed=94,
            stories_failed=6,
            success_rate=0.94,
            tokens_used=4200000,
        )
    """
    phase: str
    stories_total: int
    stories_completed: int = 0
    stories_failed: int = 0
    stories_partial: int = 0
    success_rate: float = 0.0
    tokens_used: int = 0
    avg_tokens_per_story: float = 0.0
    stories_per_hour: float = 0.0
    agent_utilization: Dict[str, float] = field(default_factory=dict)
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    duration_hours: float = 0.0


@dataclass
class StateSnapshot:
    """
    Blackboard state snapshot (Blind Spot #6 mitigation).

    Taken every 100 stories to prevent state corruption:
    - Full Blackboard state export
    - Story queue checkpoint
    - Agent metrics snapshot
    - Token budget remaining

    Restore mechanism:
    - If corruption detected → load last valid snapshot
    - If panic state → restore + retry last batch

    Example:
        StateSnapshot(
            snapshot_id="SNAP-100",
            stories_completed=100,
            blackboard_state={...},
            story_queue=[...],
            tokens_remaining=95800000,
        )
    """
    snapshot_id: str
    stories_completed: int
    blackboard_state: Dict[str, Any]
    story_queue: List[str]  # story_ids of pending stories
    agent_metrics: Dict[str, Dict[str, Any]]
    tokens_remaining: int
    created_at: datetime = field(default_factory=datetime.now)
    snapshot_path: Optional[Path] = None


@dataclass
class RAGValidationResult:
    """
    RAG context validation result (Blind Spot #4 mitigation).

    Validates RAG system has accurate context before story execution:
    1. Query RAG for target file content
    2. Compare with actual file content (fuzzy match)
    3. If similarity < 80% → flag for human review

    Prevents context poisoning:
    - Hallucinated code → story execution failure
    - Stale context → incorrect modifications

    Example:
        RAGValidationResult(
            story_id="STORY-001",
            valid=True,
            file_validations={
                "core/auth.py": 0.95,
                "tests/test_auth.py": 0.88,
            },
        )
    """
    story_id: str
    valid: bool
    file_validations: Dict[str, float] = field(default_factory=dict)  # file → similarity
    errors: List[str] = field(default_factory=list)
    validated_at: datetime = field(default_factory=datetime.now)


@dataclass
class NCMConfig:
    """
    NCM configuration parameters.

    Defaults:
    - story_batch_size: 50 (stories executed per batch)
    - agents_per_story: 2 (crew size)
    - token_limit: 100M (total budget)
    - refresh_interval: 500 (tool calls before prompt refresh)
    - snapshot_interval: 100 (stories per snapshot)
    - lock_timeout: 300.0 (seconds before deadlock)

    Example:
        NCMConfig(
            story_batch_size=50,
            agents_per_story=2,
            token_limit=100_000_000,
        )
    """
    story_batch_size: int = 50
    agents_per_story: int = 2
    token_limit: int = 100_000_000
    refresh_interval: int = 500
    snapshot_interval: int = 100
    lock_timeout: float = 300.0
    rag_similarity_threshold: float = 0.8
    max_retry_count: int = 3
    validation_mode: str = "strict"  # "strict" | "relaxed"
    parallel_execution: bool = False  # False for pilot, True for scale-up
    workspace_path: Path = field(default_factory=lambda: Path("workspace/ncm"))
