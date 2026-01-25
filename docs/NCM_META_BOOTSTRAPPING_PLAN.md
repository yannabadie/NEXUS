# NCM Meta-Bootstrapping Implementation Plan

**Project**: NEXUS V12.4 Completion via NCM Framework
**Approach**: Meta-Bootstrapping (Use NEXUS to build NCM, then NCM to finalize NEXUS)
**Timeline**: 8-13 weeks total (2-3 weeks prep + 6-10 weeks execution)
**Success Probability**: 70-80% (with mitigations)

---

## Executive Summary

**Goal**: Transform NEXUS from 82% → 95%+ production-ready by resolving 10,602 issues using its own multi-agent capabilities.

**Strategy**: Build NCM (NEXUS-Completion-Method) orchestration layer that leverages existing NEXUS capabilities (FSM, HiveMind, Swarm, RAG, Evolution) to coordinate 6 specialist agents working on story-sharded tasks.

**Key Principle**: NCM is a **client** of OrchestratorV7, not a replacement. It uses NEXUS's existing orchestration, delegation, and fault tolerance.

**Phases**:
- **Phase 0**: Pre-NCM Preparation (2-3 weeks) - Build NCM core + stress test
- **Phase 1**: Pilot (100 stories, 1 week) - Validate at small scale
- **Phase 2-3**: Scale-up (10,602 stories, 6-10 weeks) - Full execution

---

## Architecture Overview

### NCM as Client of NEXUS Core

```
┌────────────────────────────────────────────────────────┐
│  NCM Layer (NEW)                                       │
│  ┌──────────────────────────────────────────────────┐ │
│  │  NCMOrchestrator                                  │ │
│  │  - Story queue management                         │ │
│  │  - Crew assignment                                │ │
│  │  - Progress tracking                              │ │
│  └──────────────────────────────────────────────────┘ │
│                       ↓                                │
│  ┌──────────────────────────────────────────────────┐ │
│  │  Story → OrchestratorV7.process_turn()           │ │
│  │  (NCM invokes NEXUS for each story)              │ │
│  └──────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────┘
                        ↓
┌────────────────────────────────────────────────────────┐
│  NEXUS Core (EXISTING - No changes)                    │
│  ┌──────────────────────────────────────────────────┐ │
│  │  OrchestratorV7 (FSM Controller)                 │ │
│  │  - 12 states, event-driven process_turn          │ │
│  │  - Singleton with persistent state               │ │
│  └──────────────────────────────────────────────────┘ │
│  ┌──────────────────────────────────────────────────┐ │
│  │  HiveMind Pipeline (7 phases)                    │ │
│  │  - MODERATE+ complexity tasks                    │ │
│  │  - SwarmBridge delegation at Phase 4             │ │
│  └──────────────────────────────────────────────────┘ │
│  ┌──────────────────────────────────────────────────┐ │
│  │  Swarm Engine (6 modes)                          │ │
│  │  - PARALLEL, SEQUENTIAL, LEAD_SUPPORT, etc.     │ │
│  │  - DyLAN metrics tracking (AgentPool)           │ │
│  └──────────────────────────────────────────────────┘ │
│  ┌──────────────────────────────────────────────────┐ │
│  │  RAG System (HybridBackend RRF)                  │ │
│  │  │  Evolution (AgentService)                     │ │
│  │  │  Security (7 layers)                          │ │
│  └──────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────┘
```

**Why This Architecture?**
- ✅ Leverage existing orchestration (no duplication)
- ✅ All NEXUS capabilities available (Swarm, RAG, Evolution, Security)
- ✅ NCM focuses on story management, not low-level coordination
- ✅ Fault tolerance inherited from OrchestratorV7

---

## Phase 0: Pre-NCM Preparation (2-3 weeks)

**Goal**: Build NCM orchestration layer + validate with stress tests before touching the 10,602 real issues.

### 0.1 Core NCM Components (Week 1)

#### File: `core/ncm/orchestrator.py` (NEW)

**Purpose**: Story queue coordinator that invokes OrchestratorV7 for each story.

**Implementation Pattern** (follows NEXUS singleton pattern):
```python
from pydantic import BaseModel, field_validator
from typing import List, Dict, Optional
from core.orchestration_v7 import OrchestratorV7
from core.ncm.models import Story, StoryStatus, CrewAssignment
import structlog

logger = structlog.get_logger(__name__)

class NCMOrchestrator:
    """
    NCM story queue coordinator.

    This is a CLIENT of OrchestratorV7, not a replacement.
    For each story, invokes orchestrator.process_turn(story.description).

    Responsibilities:
    - Story queue management (priority order)
    - Crew assignment (which agents for which story)
    - Progress tracking (stories completed/failed)
    - Token budget monitoring (blind spot #5 mitigation)
    - State snapshot every 100 stories (blind spot #6 mitigation)

    NOT responsible for:
    - Low-level agent coordination (OrchestratorV7 handles this)
    - Tool execution (OrchestratorV7 → HiveMind → Swarm)
    - Fault tolerance (inherited from OrchestratorV7)
    """

    def __init__(
        self,
        orchestrator: OrchestratorV7,
        workspace_path: Path,
        config: Dict
    ):
        """
        Initialize NCM orchestrator.

        Args:
            orchestrator: Existing OrchestratorV7 instance (singleton)
            workspace_path: NEXUS workspace root
            config: NCM configuration (story batch size, token limits, etc.)
        """
        self.orchestrator = orchestrator
        self.workspace_path = workspace_path
        self.config = config

        # Story queue (priority-ordered)
        self.story_queue: List[Story] = []
        self.completed: List[Story] = []
        self.failed: List[Story] = []

        # Crew assignments (story_id → agent_ids)
        self.assignments: Dict[str, CrewAssignment] = {}

        # Token budget tracking (blind spot #5 mitigation)
        self.tokens_used = 0
        self.token_limit = config.get("token_limit", 100_000_000)  # 100M default

        # Prompt refresh counter (blind spot #3 mitigation)
        self.tool_calls_since_refresh = 0
        self.refresh_interval = 500  # Every 500 tool calls

        logger.info("ncm_orchestrator_initialized",
                   story_count=len(self.story_queue),
                   token_limit=self.token_limit)

    async def execute_story(self, story: Story) -> StoryStatus:
        """
        Execute a single story by invoking OrchestratorV7.

        Args:
            story: Story to execute (with description, priority, assigned agents)

        Returns:
            StoryStatus with result (SUCCESS/FAILED/PARTIAL)

        Process:
            1. Assign crew (CrewManager.assign_agents)
            2. Acquire file locks (LockManager.acquire_locks)
            3. Invoke orchestrator.process_turn(story.description)
            4. Validate results (run tests for modified files)
            5. Update DyLAN metrics (AgentPool)
            6. Release locks
            7. Check prompt refresh (every 500 tool calls)
            8. Take state snapshot (every 100 stories)
        """
        logger.info("story_execution_start", story_id=story.story_id)

        try:
            # 1. Assign crew (blind spot #8 mitigation - skill matrix)
            crew = await self.crew_manager.assign_agents(story)
            self.assignments[story.story_id] = crew

            # 2. Acquire file locks (blind spot #2 mitigation)
            locks = await self.lock_manager.acquire_locks(story.target_files)

            # 3. Invoke OrchestratorV7 (NEXUS handles execution)
            result = await self.orchestrator.process_turn(
                user_input=story.description,
                context={
                    "ncm_story_id": story.story_id,
                    "ncm_assigned_agents": [a.agent_id for a in crew.agents]
                }
            )

            # 4. Validate results (blind spot #7 mitigation)
            validation = await self._validate_story_result(story, result)

            # 5. Update DyLAN metrics
            await self._update_agent_metrics(story, result, validation)

            # 6. Release locks
            await self.lock_manager.release_locks(locks)

            # 7. Check prompt refresh (blind spot #3 mitigation)
            self.tool_calls_since_refresh += result.get("tool_calls_count", 0)
            if self.tool_calls_since_refresh >= self.refresh_interval:
                await self._refresh_prompts()

            # 8. State snapshot (blind spot #6 mitigation)
            if len(self.completed) % 100 == 0:
                await self._take_state_snapshot()

            return validation.status

        except Exception as e:
            logger.error("story_execution_failed",
                        story_id=story.story_id,
                        error=str(e))
            story.status = StoryStatus.FAILED
            self.failed.append(story)
            return StoryStatus.FAILED
```

**Key Design Decisions**:
- NCM invokes `orchestrator.process_turn()` for each story (no low-level coordination)
- All mitigations integrated (locks, refresh, snapshots, validation, skill matrix)
- Follows NEXUS patterns: Pydantic models, structlog, async/await, type hints
- Google-style docstrings with Args/Returns

---

#### File: `core/ncm/story_shard.py` (NEW)

**Purpose**: Parse audit report → story queue with RAG context validation.

**Implementation Pattern**:
```python
from pydantic import BaseModel, field_validator
from typing import List, Dict, Optional
from pathlib import Path
import structlog

from core.ncm.models import Story, StoryPriority, IssueDomain
from core.memory.rag_system import MemoryManagerV7

logger = structlog.get_logger(__name__)

class StoryShardEngine:
    """
    Audit report parser → story queue.

    Responsibilities:
    - Parse audit report (ANALYSIS_EXHAUSTIVE_2026-01-21.md)
    - Create Story objects (one per issue or issue group)
    - RAG validation gate (blind spot #4 mitigation)
    - Priority assignment (P0/P1/P2)
    - Domain classification (CODING/SECURITY/TESTING/etc.)

    Story Sharding Strategy:
    - God classes → 1 story per class (3 stories)
    - Security issues → 1 story per vulnerability (4 stories)
    - Dead imports → 1 story per module (410 → ~30 stories)
    - Type errors → 1 story per module (2913 → ~80 stories)
    - Deprecation warnings → 1 story per pattern (398 → ~15 stories)

    Total: ~10,602 issues → ~500 stories (batched by module/pattern)
    """

    def __init__(
        self,
        audit_report_path: Path,
        rag_system: MemoryManagerV7,
        config: Dict
    ):
        """
        Initialize story sharding engine.

        Args:
            audit_report_path: Path to audit report markdown
            rag_system: NEXUS RAG system for context validation
            config: Sharding configuration (batch sizes, etc.)
        """
        self.audit_path = audit_report_path
        self.rag = rag_system
        self.config = config

        logger.info("story_shard_engine_initialized",
                   audit_path=str(audit_report_path))

    async def shard_audit_report(self) -> List[Story]:
        """
        Parse audit report into prioritized story queue.

        Returns:
            List of Story objects, priority-ordered (P0 → P1 → P2)

        Process:
            1. Parse audit report sections
            2. Group issues by module/pattern
            3. Create Story objects with descriptions
            4. RAG validation gate (verify context exists)
            5. Priority assignment (HIGH → P0, etc.)
            6. Domain classification (for crew assignment)
        """
        logger.info("story_sharding_start")

        # 1. Parse audit report
        audit_data = await self._parse_audit_report()

        # 2. Group issues
        issue_groups = self._group_issues(audit_data)

        # 3. Create stories
        stories = []
        for group in issue_groups:
            story = await self._create_story(group)

            # 4. RAG validation gate (blind spot #4 mitigation)
            rag_valid = await self._validate_rag_context(story)
            if not rag_valid:
                logger.warning("story_rag_validation_failed",
                              story_id=story.story_id,
                              target_files=story.target_files)
                # Still add story, but flag for human review
                story.needs_human_review = True

            stories.append(story)

        # 5. Priority sort (P0 → P1 → P2)
        stories.sort(key=lambda s: (s.priority.value, s.story_id))

        logger.info("story_sharding_complete",
                   total_stories=len(stories),
                   p0_count=sum(1 for s in stories if s.priority == StoryPriority.P0))

        return stories

    async def _validate_rag_context(self, story: Story) -> bool:
        """
        Validate that RAG system has context for story's target files.

        This prevents context poisoning (blind spot #4):
        - If RAG returns hallucinated code, story execution will fail
        - Validate that retrieved docs match actual file content

        Args:
            story: Story to validate

        Returns:
            True if RAG context is valid, False otherwise
        """
        for file_path in story.target_files:
            # Query RAG for file content
            rag_results = await self.rag.query(
                query=f"Show me the content of {file_path}",
                top_k=3
            )

            # Read actual file
            actual_content = Path(file_path).read_text()

            # Compare (fuzzy match - allow for whitespace differences)
            similarity = self._compute_similarity(
                rag_results[0].content,
                actual_content
            )

            if similarity < 0.8:  # 80% threshold
                logger.error("rag_context_mismatch",
                            file=file_path,
                            similarity=similarity)
                return False

        return True
```

**Key Features**:
- RAG validation gate prevents context poisoning (blind spot #4)
- Groups issues to reduce story count (10,602 → ~500)
- Priority-ordered queue (P0 → P1 → P2)
- Domain classification for crew assignment

---

#### File: `core/ncm/crew_manager.py` (NEW)

**Purpose**: Agent assignment with skill matrix (blind spot #8 mitigation).

**Implementation Pattern**:
```python
from pydantic import BaseModel
from typing import List, Dict, Set
from pathlib import Path
import structlog

from core.ncm.models import Story, CrewAssignment, AgentSkill, IssueDomain
from core.agents.agent_service import AgentService

logger = structlog.get_logger(__name__)

class CrewManager:
    """
    Agent assignment with skill matrix.

    Responsibilities:
    - Skill matrix (agent → domains they excel at)
    - Crew assignment (story → best agents)
    - Fault isolation (agents can't interfere with each other)
    - Workload balancing (avoid overloading one agent)

    Blind Spot #8 Mitigation:
    - REFACTORING_AGENT should NOT handle security stories
    - SECURITY_AGENT should NOT handle dead imports
    - Crew assignment based on story.domains → agent.expertise
    """

    def __init__(
        self,
        agent_service: AgentService,
        config: Dict
    ):
        """
        Initialize crew manager.

        Args:
            agent_service: NEXUS AgentService (for agent spawning/listing)
            config: Crew configuration (max agents per story, etc.)
        """
        self.agent_service = agent_service
        self.config = config

        # Skill matrix (agent_id → expertise domains)
        self.skill_matrix: Dict[str, Set[IssueDomain]] = {}
        self._build_skill_matrix()

        logger.info("crew_manager_initialized",
                   agents=len(self.skill_matrix))

    def _build_skill_matrix(self):
        """
        Build skill matrix from agent birth certificates.

        Reads workspace/ncm/agents/*/birth_certificate.json
        and extracts specialization.expertise fields.
        """
        agents_dir = Path("workspace/ncm/agents")
        for agent_dir in agents_dir.iterdir():
            if not agent_dir.is_dir():
                continue

            cert_path = agent_dir / "birth_certificate.json"
            if not cert_path.exists():
                continue

            cert = json.loads(cert_path.read_text())
            agent_id = cert["agent_id"]
            expertise = cert["specialization"]["expertise"]

            # Map expertise → IssueDomain
            domains = self._map_expertise_to_domains(expertise)
            self.skill_matrix[agent_id] = domains

            logger.debug("agent_skill_matrix_entry",
                        agent_id=agent_id,
                        domains=list(domains))

    async def assign_agents(self, story: Story) -> CrewAssignment:
        """
        Assign best agents for story based on skill matrix.

        Args:
            story: Story to assign agents for

        Returns:
            CrewAssignment with agent_ids and swarm_mode

        Algorithm:
            1. Score each agent (overlap between story.domains and agent.expertise)
            2. Select top N agents (N = config.agents_per_story, default 2)
            3. Determine swarm mode based on story complexity
            4. Check fault isolation (no conflicting assignments)
        """
        logger.info("crew_assignment_start", story_id=story.story_id)

        # 1. Score agents
        scores = {}
        for agent_id, agent_domains in self.skill_matrix.items():
            overlap = len(story.domains & agent_domains)
            scores[agent_id] = overlap

        # 2. Select top N
        top_agents = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        selected = [agent_id for agent_id, _ in top_agents[:2]]

        # 3. Determine swarm mode
        swarm_mode = self._determine_swarm_mode(story, selected)

        # 4. Fault isolation check
        conflicts = await self._check_conflicts(story, selected)
        if conflicts:
            logger.warning("crew_assignment_conflicts",
                          story_id=story.story_id,
                          conflicts=conflicts)
            # Fallback: use SEQUENTIAL mode to avoid race conditions
            swarm_mode = "SEQUENTIAL"

        assignment = CrewAssignment(
            story_id=story.story_id,
            agent_ids=selected,
            swarm_mode=swarm_mode
        )

        logger.info("crew_assignment_complete",
                   story_id=story.story_id,
                   agents=selected,
                   mode=swarm_mode)

        return assignment

    def _determine_swarm_mode(
        self,
        story: Story,
        agents: List[str]
    ) -> str:
        """
        Determine best swarm mode for story + agents.

        Rules:
        - Security stories → RED_BLUE (propose/attack)
        - God class refactoring → LEAD_SUPPORT (complex implementation)
        - Dead imports → PARALLEL (independent files)
        - Type errors → SEQUENTIAL (avoid races)
        """
        if IssueDomain.SECURITY in story.domains:
            return "RED_BLUE"
        elif IssueDomain.REFACTORING in story.domains:
            return "LEAD_SUPPORT"
        elif IssueDomain.CLEANUP in story.domains:
            return "PARALLEL"
        else:
            return "SEQUENTIAL"  # Safe default
```

**Key Features**:
- Skill matrix prevents agent mismatch (blind spot #8)
- Fault isolation checks prevent file races
- Swarm mode selection based on story type
- Workload balancing

---

#### File: `core/ncm/locks.py` (NEW)

**Purpose**: File locking layer (blind spot #2 mitigation).

**Implementation Pattern**:
```python
import asyncio
from pathlib import Path
from typing import List, Set
import structlog

logger = structlog.get_logger(__name__)

class LockManager:
    """
    File locking layer to prevent race conditions.

    Blind Spot #2 Mitigation:
    - Multiple agents working on same file → conflicts
    - Use advisory locks (asyncio.Lock per file path)
    - Timeout mechanism (avoid deadlock)

    Example:
        async with lock_manager.acquire_lock("core/auth.py"):
            # Only one agent can modify this file
            await edit_file("core/auth.py", ...)
    """

    def __init__(self, timeout: float = 300.0):
        """
        Initialize lock manager.

        Args:
            timeout: Lock acquisition timeout in seconds (default 5 min)
        """
        self.locks: Dict[Path, asyncio.Lock] = {}
        self.timeout = timeout

        logger.info("lock_manager_initialized", timeout=timeout)

    async def acquire_locks(
        self,
        file_paths: List[Path]
    ) -> List[asyncio.Lock]:
        """
        Acquire locks for multiple files.

        Args:
            file_paths: Files to lock

        Returns:
            List of acquired locks

        Raises:
            TimeoutError: If any lock not acquired within timeout
        """
        locks_to_acquire = []
        for path in file_paths:
            if path not in self.locks:
                self.locks[path] = asyncio.Lock()
            locks_to_acquire.append((path, self.locks[path]))

        acquired = []
        try:
            for path, lock in locks_to_acquire:
                await asyncio.wait_for(
                    lock.acquire(),
                    timeout=self.timeout
                )
                acquired.append(lock)
                logger.debug("lock_acquired", file=str(path))

            return acquired

        except asyncio.TimeoutError:
            # Release already-acquired locks
            for lock in acquired:
                lock.release()
            logger.error("lock_timeout", files=[str(p) for p, _ in locks_to_acquire])
            raise

    async def release_locks(self, locks: List[asyncio.Lock]):
        """Release acquired locks."""
        for lock in locks:
            lock.release()
```

**Key Features**:
- Advisory locks per file path
- Timeout mechanism (avoid deadlock)
- Bulk acquire/release

---

#### File: `core/ncm/models.py` (NEW)

**Purpose**: Pydantic models for NCM data structures.

```python
from pydantic import BaseModel, field_validator
from typing import List, Set, Optional
from enum import Enum
from pathlib import Path

class StoryPriority(str, Enum):
    """Story priority levels."""
    P0 = "P0"  # Critical (40 HIGH issues)
    P1 = "P1"  # High priority (tech debt)
    P2 = "P2"  # Low priority (cleanup)

class IssueDomain(str, Enum):
    """Issue domains for crew assignment."""
    REFACTORING = "refactoring"
    SECURITY = "security"
    TESTING = "testing"
    EVOLUTION = "evolution"
    DOCUMENTATION = "documentation"
    CLEANUP = "cleanup"

class StoryStatus(str, Enum):
    """Story execution status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"  # Some files modified, some failed

class Story(BaseModel):
    """
    A single work item (one or more related issues).

    Examples:
    - "Refactor fsm_handlers.py (1838 LOC) into 12 handler files"
    - "Fix JWT secret generation (hardcoded secret)"
    - "Remove dead imports from core/orchestration/*.py"
    """
    story_id: str  # "STORY-001"
    priority: StoryPriority
    domains: Set[IssueDomain]  # For crew assignment
    description: str  # Detailed task description for agents
    target_files: List[Path]  # Files to modify
    test_files: List[Path]  # Tests to validate (blind spot #7)
    status: StoryStatus = StoryStatus.PENDING
    needs_human_review: bool = False  # RAG validation failed

    @field_validator('story_id')
    @classmethod
    def validate_story_id(cls, v: str) -> str:
        """Ensure story_id format."""
        if not v.startswith("STORY-"):
            raise ValueError(f"story_id must start with 'STORY-', got {v}")
        return v

class CrewAssignment(BaseModel):
    """Agent assignment for a story."""
    story_id: str
    agent_ids: List[str]  # ["REFACTORING_AGENT_V1", "TESTING_AGENT_V1"]
    swarm_mode: str  # "PARALLEL", "LEAD_SUPPORT", etc.
    assigned_at: str  # ISO timestamp

class AgentSkill(BaseModel):
    """Agent skill matrix entry."""
    agent_id: str
    expertise: Set[IssueDomain]
    success_rate: float  # DyLAN metric
    avg_tokens: int  # Efficiency metric
```

---

### 0.2 Evolution System Completion (Week 1)

**Findings from Explore Agent 2**:
- `EvolutionManager` has TODOs at lines 177, 512, 552
- `AgentService` has complete implementations for all needed functionality
- Solution: Delegate from EvolutionManager to AgentService

#### File: `core/evolution/manager.py` (MODIFY)

**Line 177 - `brainstorm_specialist()`**:
```python
# BEFORE (TODO)
def brainstorm_specialist(self, mission: str) -> Dict:
    # TODO: Implement brainstorming logic
    pass

# AFTER (Delegation to AgentService)
async def brainstorm_specialist(
    self,
    mission: str,
    parent_id: str
) -> Dict:
    """
    Brainstorm specialist agent prompt via AgentService.

    Args:
        mission: Specialization mission (e.g., "Expert in FastAPI security")
        parent_id: Parent agent ID (for lineage tracking)

    Returns:
        Dict with agent_id, prompt, specialization

    Delegates to:
        AgentService._brainstorm_agent_prompt() (lines 245-312 in agent_service.py)
    """
    logger.info("brainstorm_specialist_start", mission=mission)

    # Delegate to AgentService
    agent_data = await self.agent_service._brainstorm_agent_prompt(
        mission=mission,
        parent_lineage={"parent_id": parent_id}
    )

    return agent_data
```

**Line 512 - `run_specialization()`**:
```python
# BEFORE (TODO)
def run_specialization(self, agent_data: Dict) -> str:
    # TODO: Implement specialization
    pass

# AFTER (Delegation to AgentService)
async def run_specialization(self, agent_data: Dict) -> str:
    """
    Run specialization via AgentService.spawn().

    Args:
        agent_data: Result from brainstorm_specialist()

    Returns:
        agent_id of spawned agent

    Delegates to:
        AgentService.spawn() (lines 158-243 in agent_service.py)
    """
    logger.info("run_specialization_start",
               agent_id=agent_data.get("agent_id"))

    # Delegate to AgentService
    agent_id = await self.agent_service.spawn(
        mission=agent_data["mission"],
        parent_id=agent_data["parent_id"],
        expertise=agent_data.get("expertise", []),
        tools=agent_data.get("tools", [])
    )

    return agent_id
```

**Line 552 - Track `last_evolution`**:
```python
# BEFORE (TODO)
def track_last_evolution(self, agent_id: str):
    # TODO: Track last evolution time
    pass

# AFTER (Read from LINEAGE.json)
def track_last_evolution(self, agent_id: str) -> Optional[str]:
    """
    Track last evolution time from LINEAGE.json.

    Args:
        agent_id: Agent to check

    Returns:
        ISO timestamp of last evolution, or None if never evolved

    Reads:
        workspace/.nexus/LINEAGE.json → agents[agent_id].activated_at
    """
    lineage_path = self.workspace_path / ".nexus" / "LINEAGE.json"
    if not lineage_path.exists():
        return None

    lineage = json.loads(lineage_path.read_text())
    agent_entry = lineage.get("agents", {}).get(agent_id)

    if not agent_entry:
        return None

    return agent_entry.get("activated_at")
```

**Verification**: Unit tests for all 3 functions.

---

### 0.3 Mitigations Implementation (Week 2)

#### Blind Spot #3: Prompt Refresh System

**File**: `core/ncm/prompt_refresh.py` (NEW)

```python
import structlog
from typing import Dict
from pathlib import Path

logger = structlog.get_logger(__name__)

class PromptRefreshSystem:
    """
    Refresh agent prompts every 500 tool calls.

    Blind Spot #3 Mitigation:
    - Long-running execution → prompt drift/decay
    - Stale context → hallucinations
    - Solution: Reload system prompts from disk every 500 tool calls
    """

    def __init__(self, prompts_dir: Path, refresh_interval: int = 500):
        self.prompts_dir = prompts_dir
        self.refresh_interval = refresh_interval
        self.tool_calls_count = 0
        self.prompt_cache: Dict[str, str] = {}

        logger.info("prompt_refresh_system_initialized",
                   interval=refresh_interval)

    async def refresh_if_needed(self) -> bool:
        """
        Check if refresh needed and reload prompts.

        Returns:
            True if refresh occurred, False otherwise
        """
        if self.tool_calls_count >= self.refresh_interval:
            await self._reload_prompts()
            self.tool_calls_count = 0
            return True
        return False

    async def _reload_prompts(self):
        """Reload all prompts from disk."""
        logger.info("prompt_refresh_start")

        for prompt_file in self.prompts_dir.glob("*.md"):
            agent_name = prompt_file.stem
            new_prompt = prompt_file.read_text()
            self.prompt_cache[agent_name] = new_prompt

            logger.debug("prompt_reloaded", agent=agent_name)

        logger.info("prompt_refresh_complete",
                   prompts_reloaded=len(self.prompt_cache))
```

#### Blind Spot #5: Token Budget Monitor

**File**: `core/ncm/token_monitor.py` (NEW)

```python
class TokenBudgetMonitor:
    """
    Monitor token usage and alert before exceeding budget.

    Blind Spot #5 Mitigation:
    - 10,602 stories × 45k tokens/story = 477M tokens (exceeds budget)
    - Solution: Track tokens per story, alert at thresholds
    """

    def __init__(self, budget: int = 100_000_000):
        self.budget = budget
        self.used = 0
        self.thresholds = [0.5, 0.75, 0.9]  # Alert at 50%, 75%, 90%

    async def track_usage(self, story_id: str, tokens: int):
        """Track tokens used for a story."""
        self.used += tokens

        pct_used = self.used / self.budget
        for threshold in self.thresholds:
            if pct_used >= threshold:
                logger.warning("token_budget_threshold",
                              threshold=threshold,
                              used=self.used,
                              budget=self.budget)
                self.thresholds.remove(threshold)  # Alert once
```

#### Blind Spot #6: State Snapshot System

**File**: `core/ncm/snapshot.py` (NEW)

```python
class StateSnapshotSystem:
    """
    Take Blackboard snapshots every 100 stories.

    Blind Spot #6 Mitigation:
    - Multi-week execution → Blackboard grows unbounded
    - Memory leak/corruption risk
    - Solution: Snapshot + restore mechanism
    """

    async def take_snapshot(self, blackboard: AsyncBlackboard, story_count: int):
        """Save Blackboard state to disk."""
        snapshot_path = self.snapshots_dir / f"snapshot_{story_count}.json"

        state = await blackboard.export_state()
        snapshot_path.write_text(json.dumps(state, indent=2))

        logger.info("state_snapshot_saved",
                   path=str(snapshot_path),
                   stories_completed=story_count)
```

---

### 0.4 Stress Testing (Week 2-3)

**Goal**: Validate NCM with 1000 stories + 6 agents before touching real issues.

#### File: `tests/ncm/test_ncm_stress.py` (NEW)

```python
import pytest
from tests.torture.base import TortureBase, MetricsCollector
from core.ncm.orchestrator import NCMOrchestrator

class TestNCMStress(TortureBase):
    """
    Stress test NCM with 1000 stories + 6 agents.

    Success Criteria:
    - 95% story completion rate
    - 90% recovery from failures
    - <1% panic rate
    - No deadlocks
    - No file races
    """

    @pytest.mark.asyncio
    async def test_1000_stories_6_agents(self):
        """
        Execute 1000 synthetic stories with 6 agents.

        Synthetic Story Examples:
        - "Add docstring to function X in file Y"
        - "Fix type hint for parameter Z in module W"
        - "Remove unused import A from file B"

        Chaos Injections:
        - 10% stories have race condition potential
        - 5% stories timeout (simulated)
        - 2% stories corrupt Blackboard (simulated)
        """
        # Generate 1000 synthetic stories
        stories = self._generate_synthetic_stories(count=1000)

        # Initialize NCM
        ncm = NCMOrchestrator(...)

        # Execute with chaos injectors
        results = []
        for story in stories:
            # Inject chaos (10% race, 5% timeout, 2% corruption)
            if random.random() < 0.10:
                self.inject_race_condition(story)
            if random.random() < 0.05:
                self.inject_timeout(story)
            if random.random() < 0.02:
                self.inject_corruption(story)

            result = await ncm.execute_story(story)
            results.append(result)

        # Analyze results
        metrics = MetricsCollector.analyze(results)

        # Assert success criteria
        assert metrics.success_rate >= 0.95, f"Success rate {metrics.success_rate} < 95%"
        assert metrics.recovery_rate >= 0.90, f"Recovery {metrics.recovery_rate} < 90%"
        assert metrics.panic_rate < 0.01, f"Panic rate {metrics.panic_rate} >= 1%"

        # No deadlocks
        assert not metrics.deadlocks, f"Deadlocks detected: {metrics.deadlocks}"

        # No file races
        assert not metrics.file_races, f"File races detected: {metrics.file_races}"
```

**Run Command**:
```bash
pytest tests/ncm/test_ncm_stress.py -v --log-cli-level=INFO
```

**Pass Criteria**: All assertions pass, no deadlocks, no file races.

---

### 0.5 Phase 0 Deliverables

**Code Artifacts** (NEW):
- `core/ncm/orchestrator.py` - Story queue coordinator
- `core/ncm/story_shard.py` - Audit report parser
- `core/ncm/crew_manager.py` - Agent assignment with skill matrix
- `core/ncm/locks.py` - File locking layer
- `core/ncm/models.py` - Pydantic models
- `core/ncm/prompt_refresh.py` - Prompt refresh system
- `core/ncm/token_monitor.py` - Token budget monitor
- `core/ncm/snapshot.py` - State snapshot system

**Code Artifacts** (MODIFIED):
- `core/evolution/manager.py` - Complete TODOs (lines 177, 512, 552)

**Tests** (NEW):
- `tests/ncm/test_ncm_orchestrator.py` - Unit tests for NCMOrchestrator
- `tests/ncm/test_story_shard.py` - Unit tests for StoryShardEngine
- `tests/ncm/test_crew_manager.py` - Unit tests for CrewManager
- `tests/ncm/test_locks.py` - Unit tests for LockManager
- `tests/ncm/test_ncm_stress.py` - Stress test (1000 stories + 6 agents)

**Documentation** (NEW):
- `docs/NCM_PHASE0_COMPLETION_REPORT.md` - Phase 0 results

**Success Criteria**:
- ✅ All unit tests pass (pytest tests/ncm/)
- ✅ Stress test passes (95% success, 90% recovery, <1% panic)
- ✅ No deadlocks, no file races
- ✅ Token budget monitor functional
- ✅ Prompt refresh system functional
- ✅ State snapshot system functional
- ✅ Evolution TODOs completed (manager.py)

**Timeline**: 2-3 weeks (160-240 hours with 2 agents)

---

## Phase 1: Pilot (100 Stories, 1 Week)

**Goal**: Validate NCM at small scale with real issues (not synthetic).

### 1.1 Story Selection (Day 1)

**Select 100 low-risk stories from audit report**:
- 30 dead import removals (P2 - safest)
- 30 type hint additions (P2 - low risk)
- 20 docstring additions (P2 - no logic changes)
- 15 simple refactorings (P2 - small functions)
- 5 security fixes (P1 - hardcoded secrets only)

**Criteria**:
- No God class refactoring (too complex for pilot)
- No critical security fixes (reserve for later)
- Single-file modifications only (avoid multi-file races)
- Full test coverage exists (validation easy)

### 1.2 Execution (Day 2-5)

**Process**:
```bash
# Generate story queue (100 stories)
python -m core.ncm.story_shard --limit=100 --priority=P2

# Execute NCM
python nexus7.py
nexus7> /ncm pilot --stories=100

# NCM will:
# 1. Load story queue (100 stories)
# 2. Assign crews (CrewManager)
# 3. Execute stories sequentially (one at a time for pilot)
# 4. Validate after each story (run tests)
# 5. Track metrics (tokens, success rate, failures)
```

**Human Checkpoints**:
- After 10 stories: Review results, adjust if needed
- After 50 stories: Mid-pilot review
- After 100 stories: Full pilot review

### 1.3 Validation (Day 6-7)

**Metrics to Track**:
- Success rate (target: 90%+)
- Stories per hour (baseline for Phase 2-3)
- Token usage per story (actual vs estimate)
- Failure modes (categorize errors)
- Agent utilization (which agents most effective)

**Deliverable**: `docs/NCM_PILOT_REPORT.md` with:
- 100 stories executed
- Success rate achieved
- Failure analysis
- Recommended adjustments for Phase 2
- Go/No-Go decision

**Go Criteria**:
- Success rate ≥ 80% (lower threshold for pilot)
- No critical bugs introduced
- Test suite still passes (2371 tests)
- Token usage within budget

---

## Phase 2-3: Scale-Up (10,602 Issues, 6-10 Weeks)

**Goal**: Execute full NCM workflow at production scale.

### 2.1 Incremental Scaling Strategy

**Phase 2A (Week 1-2): 500 Stories (P2 - Low Risk)**
- Dead imports: 410 → 0
- Simple type hints: 500 → 0
- Docstrings: 124 → 0

**Phase 2B (Week 3-4): 1000 Stories (P1 - Medium Risk)**
- Type errors (simple): 1000 → 0
- Deprecation warnings (datetime.utcnow): 200 → 0
- Dead code (high confidence): 200 → 0

**Phase 3A (Week 5-7): 2000 Stories (P1 - High Risk)**
- God class refactoring (3 classes → 21 files)
- Type errors (complex): 1913 → 0
- Deprecation warnings (LanceDB): 198 → 0
- Dead code (medium confidence): 652 → 0

**Phase 3B (Week 8-10): Remaining (P0 + P1)**
- Security fixes (40 HIGH issues)
- Evolution system completion
- Final cleanup
- Full validation

### 2.2 Execution Pattern

**Daily Routine**:
```bash
# Morning: Start NCM batch
python nexus7.py
nexus7> /ncm execute --batch-size=50 --priority=P2

# NCM runs autonomously throughout the day
# Human monitors logs in real-time:
tail -f workspace/logs/ncm_YYYYMMDD.jsonl

# Evening: Review results
nexus7> /ncm status
# Example output:
# Stories completed today: 47/50 (94% success)
# Stories failed: 3 (see workspace/logs/ncm_failures.jsonl)
# Token usage: 2.1M / 100M budget (2.1%)
# Next batch: 50 stories (P2 - type hints)
```

**Weekly Review**:
- Run full test suite (pytest tests/)
- Review failure logs
- Adjust crew assignments if needed
- Update token budget projections
- Human checkpoint: Go/No-Go for next week

### 2.3 Failure Recovery Protocol

**When Story Fails**:
1. NCM logs failure to `workspace/logs/ncm_failures.jsonl`
2. Story marked as `FAILED`, moved to end of queue
3. Human reviews failure log
4. Decision:
   - Retry with different crew → NCM retries
   - Escalate to human → Human fixes manually
   - Skip (not critical) → Story archived

**When Tests Fail**:
1. NCM stops execution immediately
2. Rollback last story (git revert)
3. Alert human (critical failure)
4. Human investigates and fixes
5. NCM resumes after fix

### 2.4 Success Criteria

**Phase 2-3 Complete When**:
- ✅ 10,602 issues → 0 (100% completion target, 95% acceptable)
- ✅ Test suite passes (2371 tests, 0 failures)
- ✅ Mypy strict passes (0 type errors)
- ✅ Pylint score 10.0/10.0
- ✅ No security vulnerabilities (0 HIGH)
- ✅ Score 82% → 95%+ (achievement unlocked)

**Deliverables**:
- `docs/NCM_EXECUTION_REPORT.md` - Full execution summary
- `workspace/ncm/logs/` - Complete execution logs
- `workspace/ncm/metrics/` - Token usage, success rates, agent metrics
- Updated `LINEAGE.json` - Agent evolution history
- Updated `workspace/.nexus/blackboard.json` - Final state

---

## Verification & Quality Assurance

### Test Suite Validation

**After Each Phase**:
```bash
# Full test suite
pytest tests/ -v --cov=core --cov-report=html

# Target: 2371 tests pass, 0 failures
# Coverage: 85% → 90%+ (Phase 3 goal)
```

**After Each 100 Stories**:
```bash
# Quick smoke tests (critical paths only)
pytest tests/test_orchestration_v7.py tests/test_hybrid_swarm.py -v

# Target: <5 min runtime, 100% pass
```

### Code Quality Checks

**After Phase 2-3 Complete**:
```bash
# Mypy strict
mypy core/ --strict
# Target: 0 errors

# Pylint
pylint core/ --rcfile=.pylintrc
# Target: 10.0/10.0

# Vulture (dead code)
vulture core/ --min-confidence 80
# Target: 0 dead code

# Autoflake (dead imports)
autoflake --check core/**/*.py
# Target: 0 dead imports

# Black (formatting)
black --check core/
# Target: All files formatted

# isort (import sorting)
isort --check core/
# Target: All imports sorted
```

### Security Audit

**After Phase 3B Complete**:
```bash
# Safety (dependency vulnerabilities)
safety check --json

# Bandit (security linter)
bandit -r core/ -f json

# Target: 0 vulnerabilities, 0 HIGH issues
```

### Documentation Completeness

**After Phase 3A Complete**:
```bash
# Check docstring coverage
interrogate core/ -v

# Target: 100% coverage (124 missing → 0)
```

---

## Risk Mitigations Summary

**All 8 Blind Spots Addressed**:

| Blind Spot | Mitigation | Implementation |
|------------|-----------|----------------|
| #1 Coordination Complexity | Leverage OrchestratorV7 | NCM as client (not replacement) |
| #2 File Races | File locking layer | `core/ncm/locks.py` (asyncio.Lock) |
| #3 Prompt Decay | Refresh every 500 calls | `core/ncm/prompt_refresh.py` |
| #4 RAG Context Poisoning | Validation gate | `story_shard.py._validate_rag_context()` |
| #5 Token Budget Exhaustion | Monitor + alert | `core/ncm/token_monitor.py` |
| #6 State Corruption | Snapshots every 100 stories | `core/ncm/snapshot.py` |
| #7 Test Regression Cascades | Validate after each story | `orchestrator.py._validate_story_result()` |
| #8 Agent Skill Mismatch | Skill matrix + crew assignment | `core/ncm/crew_manager.py` |

**Additional Mitigations**:
- Incremental scaling (100 → 500 → 1000 → 2000 → 10,602)
- Human checkpoints (weekly reviews)
- Failure recovery protocol (retry/escalate/skip)
- Stress testing before production (1000 stories)
- Full test validation (pytest after each phase)

---

## Success Probability Assessment

**After Mitigations**:
- **Phase 0 Success**: 95% (stress tests validate all mitigations)
- **Pilot Success**: 85% (100 low-risk stories)
- **Phase 2 Success**: 80% (scaling challenges)
- **Phase 3 Success**: 70% (complex issues like God classes)
- **Overall Success**: 70-80% (10,602 issues → 95%+ resolution)

**Definition of Success**:
- NOT 100% automated perfection (unrealistic)
- BUT 95%+ issues resolved autonomously
- WITH human checkpoints preventing disasters
- AND production-ready NEXUS V12.5 at end

---

## Timeline Summary

| Phase | Duration | Stories | Outcome |
|-------|----------|---------|---------|
| **Phase 0** | 2-3 weeks | 0 (stress tests) | NCM core + validation |
| **Phase 1** | 1 week | 100 (pilot) | Go/No-Go decision |
| **Phase 2A** | 2 weeks | 500 (P2) | Low-risk cleanup |
| **Phase 2B** | 2 weeks | 1000 (P1) | Medium-risk fixes |
| **Phase 3A** | 3 weeks | 2000 (P1) | High-risk refactoring |
| **Phase 3B** | 2 weeks | Remaining | Security + final cleanup |
| **Total** | **12-16 weeks** | **10,602** | **NEXUS V12.5 Production-Ready** |

**Critical Path**:
1. Phase 0 completion (stress tests pass) → Phase 1 starts
2. Pilot success (80%+ completion) → Phase 2 starts
3. Weekly reviews (no critical failures) → Continue scaling
4. Test suite passes (after each phase) → Next phase approved

---

## Appendices

### A. File Structure After Phase 0

```
NEXUS/
├── core/
│   ├── ncm/                              # NEW
│   │   ├── __init__.py
│   │   ├── orchestrator.py               # Story queue coordinator
│   │   ├── story_shard.py                # Audit report parser
│   │   ├── crew_manager.py               # Agent assignment
│   │   ├── locks.py                      # File locking
│   │   ├── models.py                     # Pydantic models
│   │   ├── prompt_refresh.py             # Prompt refresh system
│   │   ├── token_monitor.py              # Token budget monitor
│   │   └── snapshot.py                   # State snapshots
│   ├── evolution/
│   │   └── manager.py                    # MODIFIED (TODOs completed)
│   └── [existing modules unchanged]
├── tests/
│   └── ncm/                              # NEW
│       ├── test_ncm_orchestrator.py
│       ├── test_story_shard.py
│       ├── test_crew_manager.py
│       ├── test_locks.py
│       └── test_ncm_stress.py            # 1000 stories stress test
├── workspace/
│   └── ncm/
│       ├── agents/                       # EXISTING (6 agents)
│       ├── logs/                         # NEW (execution logs)
│       ├── metrics/                      # NEW (token usage, success rates)
│       └── snapshots/                    # NEW (Blackboard snapshots)
├── docs/
│   ├── NCM_ARCHITECTURE.md               # EXISTING
│   ├── NCM_IMPACT_ANALYSIS.md            # EXISTING
│   ├── NCM_PHASE0_COMPLETION_REPORT.md   # NEW
│   ├── NCM_PILOT_REPORT.md               # NEW (after Phase 1)
│   └── NCM_EXECUTION_REPORT.md           # NEW (after Phase 2-3)
```

### B. Code Patterns Reference

**All NCM code follows NEXUS patterns**:
- ✅ Pydantic BaseModel with field_validator for all data structures
- ✅ Google-style docstrings (Args, Returns, Raises)
- ✅ Type hints (100% coverage)
- ✅ Structlog for logging (with context dicts)
- ✅ Async/await for I/O operations
- ✅ No external dependencies (standard library only)

**Example Template**:
```python
from pydantic import BaseModel, field_validator
from typing import List, Dict, Optional
from pathlib import Path
import structlog

logger = structlog.get_logger(__name__)

class MyDataModel(BaseModel):
    """Brief description.

    Longer description if needed.
    """
    field_name: str

    @field_validator('field_name')
    @classmethod
    def validate_field(cls, v: str) -> str:
        """Validate field_name."""
        if not v:
            raise ValueError("field_name cannot be empty")
        return v

class MyComponent:
    """Brief description.

    Responsibilities:
    - Responsibility 1
    - Responsibility 2

    NOT responsible for:
    - Thing 1 (delegated to X)
    - Thing 2 (handled by Y)
    """

    def __init__(self, config: Dict):
        """
        Initialize component.

        Args:
            config: Configuration dict with keys X, Y, Z
        """
        self.config = config
        logger.info("component_initialized", config_keys=list(config.keys()))

    async def my_method(self, param: str) -> Dict:
        """
        Brief description of what method does.

        Args:
            param: Description of parameter

        Returns:
            Dict with keys 'result', 'status'

        Raises:
            ValueError: If param is invalid
        """
        logger.info("method_start", param=param)

        # Implementation

        logger.info("method_complete", result=result)
        return result
```

### C. Human Checkpoints

**Weekly Review Template**:
```markdown
## NCM Weekly Review - Week N

**Date**: YYYY-MM-DD
**Phase**: Phase 2A / 2B / 3A / 3B
**Stories This Week**: X/Y (Z% success)

### Metrics
- Stories completed: X
- Stories failed: Y
- Token usage: Z M / 100M budget (W%)
- Test suite status: PASS/FAIL
- Agent utilization: [breakdown by agent]

### Failures Analysis
- [List failed stories with failure modes]
- [Root cause analysis]
- [Recommended actions]

### Adjustments Needed
- [ ] Crew assignments (if agent mismatch)
- [ ] Token budget (if exceeding projections)
- [ ] Story priorities (if bottlenecks)
- [ ] Human escalation (if critical bugs)

### Decision
- [ ] Continue as planned
- [ ] Adjust strategy (specify)
- [ ] Pause for investigation
```

---

## Next Steps After Plan Approval

**Immediate (Today)**:
1. User reviews this plan
2. User approves/modifies
3. Exit plan mode → Implementation begins

**Week 1 (Phase 0 Start)**:
1. Create `core/ncm/` directory structure
2. Implement `models.py` (Pydantic models)
3. Implement `orchestrator.py` (NCM core)
4. Implement `story_shard.py` (audit parser)

**Week 2 (Phase 0 Continue)**:
1. Implement `crew_manager.py` (skill matrix)
2. Implement `locks.py` (file locking)
3. Complete evolution TODOs (manager.py)
4. Implement mitigation systems (refresh, monitor, snapshot)

**Week 3 (Phase 0 Validation)**:
1. Write unit tests for all NCM components
2. Write stress test (1000 stories + 6 agents)
3. Run stress test, analyze results
4. Fix any issues found
5. Phase 0 completion report

**Week 4 (Phase 1 Pilot)**:
1. Generate 100-story pilot queue
2. Execute pilot
3. Human checkpoints (10, 50, 100 stories)
4. Pilot report + Go/No-Go decision

**Weeks 5-16 (Phase 2-3 Scale-Up)**:
1. Incremental scaling (500 → 1000 → 2000 → 10,602)
2. Weekly human reviews
3. Failure recovery as needed
4. Final validation (tests, quality, security)

---

**END OF PLAN**

**Plan Status**: Ready for user approval
**Estimated Implementation Time**: 12-16 weeks
**Success Probability**: 70-80%
**Key Risks**: Mitigated via stress testing, incremental scaling, human checkpoints

**Approval Request**: Ready to exit plan mode and begin Phase 0 implementation?
