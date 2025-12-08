# NEXUS V8.0 CODEBASE SNAPSHOT
# Ground Truth Reference for External LLM Analysis

**Generated**: 2025-12-08 | **Version**: 8.0.1 | **Lines of Code**: 42,831
**Purpose**: Prevent LLM hallucinations by providing verified codebase facts

---

## TABLE OF CONTENTS

1. [Module Structure](#1-module-structure)
2. [Critical Classes](#2-critical-classes)
3. [All Enums](#3-all-enums)
4. [All Dataclasses](#4-all-dataclasses)
5. [Critical Method Signatures](#5-critical-method-signatures)
6. [Inter-Module Dependencies](#6-inter-module-dependencies)
7. [DOES NOT EXIST (Anti-Hallucination)](#7-does-not-exist-anti-hallucination)
8. [Implementation Status](#8-implementation-status)
9. [Config Keys](#9-config-keys)
10. [Test Coverage](#10-test-coverage)

---

## 1. MODULE STRUCTURE

```
core/                           # 42,831 lines total
├── orchestration_v7.py         (783 lines)  # Main V7 orchestrator
├── config.py                   (189 lines)  # Configuration loader
├── KERNEL.py                   (35 lines)   # Immutable alignment
│
├── bootstrap/                  # Project initialization
│   ├── auto_bootstrap.py       (1115 lines) # Auto-generate NEXUS.md
│   └── agent_loader.py         (156 lines)  # Load spawned agents
│
├── drivers/                    # LLM API drivers
│   ├── gemini_driver_v7.py     (624 lines)  # Gemini CLI wrapper
│   └── claude_driver_hybrid.py (483 lines)  # Claude API wrapper
│
├── evolution/                  # Agent evolution system
│   ├── manager.py              (556 lines)  # Evolution orchestrator
│   ├── validator.py            (732 lines)  # Child validation
│   ├── tiered_validator.py     (562 lines)  # 5-tier validation
│   ├── evaluator.py            (542 lines)  # Fitness evaluation
│   ├── lineage.py              (443 lines)  # Parent-child tracking
│   ├── mutation_parser.py      (463 lines)  # Parse mutations
│   ├── rate_limiter.py         (71 lines)   # Evolution rate limits
│   ├── models.py               (145 lines)  # Evolution dataclasses
│   └── phases/                 # 5-phase evolution
│       ├── brainstorm.py       (242 lines)
│       ├── create.py           (302 lines)
│       └── promote.py          (222 lines)
│
├── execution/                  # Tool execution
│   ├── tool_manager.py         (1672 lines) # 11 core tools
│   ├── agent_tools.py          (510 lines)  # Agent-specific tools
│   └── dynamic_tools.py        (473 lines)  # Runtime tool creation
│
├── fsm/                        # Finite State Machine
│   ├── states.py               (106 lines)  # OrchestratorState enum
│   ├── stagnation_detector.py  (357 lines)  # Hot-Swap Lead support
│   ├── context.py              (100 lines)  # TaskExecutionContext
│   ├── panic_system.py         (105 lines)  # Panic handling
│   └── plan_health.py          (105 lines)  # Plan monitoring
│
├── governance/                 # Security & policy
│   ├── sandbox_policy.py       (231 lines)  # Sandbox rules
│   └── red_team/
│       ├── validator.py        (289 lines)  # Red team tests
│       └── alignment_tests.py  (112 lines)  # Alignment questions
│
├── hive_mind/                  # V8.0 TRUE HIVE MIND
│   ├── orchestrator.py         (653 lines)  # TrueHiveMind class
│   ├── types.py                (396 lines)  # 25+ dataclasses
│   ├── agent_registry.py       (285 lines)  # Spawned agent registry
│   ├── strategy_blacklist.py   (461 lines)  # Failed strategy tracking
│   ├── cost_estimator.py       (488 lines)  # Token cost estimation
│   ├── context_manager.py      (477 lines)  # Context prioritization
│   ├── user_interaction.py     (595 lines)  # Breakpoint handling
│   ├── adaptive_debate.py      (476 lines)  # Debate configuration
│   └── phases/                 # 7-phase pipeline
│       ├── phase_analysis.py       (500 lines)  # Phase 1
│       ├── phase_debate.py         (595 lines)  # Phase 2
│       ├── phase_architecture.py   (502 lines)  # Phase 3
│       ├── phase_execution.py      (513 lines)  # Phase 4
│       ├── phase_diagnosis.py      (439 lines)  # Phase 5
│       ├── phase_retry.py          (221 lines)  # Phase 6
│       └── phase_consolidation.py  (588 lines)  # Phase 7
│
├── interface/                  # User interface
│   ├── repl.py                 (2340 lines) # Interactive REPL
│   ├── commands.py             (412 lines)  # Slash commands
│   └── tutorial.py             (204 lines)  # Onboarding tutorial
│
├── logging/
│   └── logger_v7.py            (454 lines)  # Structured logging
│
├── mcp/                        # Model Context Protocol
│   ├── client.py               (529 lines)  # MCP client
│   ├── protocol.py             (473 lines)  # MCP dataclasses
│   └── registry.py             (172 lines)  # Server registry
│
├── memory/                     # Memory systems
│   ├── project_memory.py       (713 lines)  # RAG orchestrator
│   ├── success_memory.py       (798 lines)  # Success pattern storage
│   ├── auto_memory.py          (195 lines)  # Task-type memory
│   ├── types.py                (57 lines)   # Chunk dataclass
│   └── backends/
│       ├── base.py             (58 lines)   # MemoryBackend ABC
│       ├── dense.py            (275 lines)  # LanceDB + MiniLM
│       ├── tfidf.py            (106 lines)  # TF-IDF fallback
│       └── bm25.py             (138 lines)  # BM25 fallback
│
├── orchestration/              # V7 orchestration helpers
│   ├── fsm_handlers.py         (1091 lines) # State handlers
│   ├── agent_invoker.py        (383 lines)  # Agent invocation
│   ├── context_builder.py      (361 lines)  # Context construction
│   ├── swarm_bridge.py         (192 lines)  # Swarm integration
│   └── detectors.py            (178 lines)  # Pattern detectors
│
├── prompts/                    # System prompts
│   ├── manager.py              (156 lines)  # Prompt loading
│   └── *.md                    # Prompt templates
│
├── routing/
│   └── model_router.py         (217 lines)  # Opus/Sonnet/Flash routing
│
├── security/
│   ├── execution_policy.py     (821 lines)  # Command validation
│   ├── path_guardian.py        (209 lines)  # Path traversal protection
│   ├── integrity_monitor.py    (206 lines)  # File integrity
│   └── mutation_validator.py   (188 lines)  # Mutation safety
│
├── swarm/                      # Hybrid Swarm Engine
│   ├── hybrid_swarm_engine.py  (749 lines)  # Main swarm orchestrator
│   ├── mode_selector.py        (972 lines)  # Mode selection + memory
│   ├── mode_executors.py       (1071 lines) # 6 mode executors
│   ├── negotiation_protocol.py (627 lines)  # Agent negotiation
│   ├── task_analyzer.py        (518 lines)  # Task complexity
│   ├── session_manager.py      (669 lines)  # Session isolation
│   ├── agent_metrics.py        (626 lines)  # DyLAN metrics
│   ├── collaboration_modes.py  (234 lines)  # Mode definitions
│   └── task_completion_validator.py (319 lines)
│
├── synapse/                    # Legacy memory
│   ├── memory_v7.py            (381 lines)  # Compression
│   └── protocol_v7.py          (125 lines)  # Message types
│
├── telemetry/
│   ├── budget_tracker.py       (414 lines)  # USD budget tracking
│   ├── exporter.py             (432 lines)  # Telemetry export
│   └── metrics.py              (389 lines)  # Metric collection
│
├── ui/
│   └── console_v7.py           (218 lines)  # Console output
│
├── utils/
│   ├── atomic_store.py         (291 lines)  # Thread-safe JSON
│   ├── stream_parser.py        (196 lines)  # Parse LLM output
│   ├── json_extractor.py       (115 lines)  # Extract JSON from text
│   └── artifact_verifier.py    (163 lines)  # Verify file creation
│
└── workspace/
    ├── manager.py              (385 lines)  # Workspace management
    ├── models.py               (168 lines)  # Workspace models
    └── exceptions.py           (38 lines)   # Custom exceptions
```

---

## 2. CRITICAL CLASSES

### core/hive_mind/orchestrator.py
```python
class TrueHiveMind:                    # line 75
    """TRUE HIVE MIND V8.0 Orchestrator - 7-phase pipeline"""
    # Key attributes:
    #   self.gemini: GeminiDriverV7
    #   self.claude: ClaudeDriverV7
    #   self.state: HiveMindState
    #   self.stagnation_detector: StagnationDetector
    #   self._current_lead: str  # "gemini" or "claude"

@dataclass
class HiveMindResult:                  # line 60
    success: bool
    output: str
    state: HiveMindState
    phases_completed: list
    total_duration: float
    total_tokens: int
    agents_used: list
    agents_spawned: list
    artifacts_created: list
    knowledge_archived: int
    error: Optional[str] = None
```

### core/orchestration_v7.py
```python
class OrchestratorV7:                  # line 58
    """Main V7 FSM Orchestrator"""
    # Key attributes:
    #   self.state: OrchestratorState
    #   self.gemini_driver: GeminiDriverV7
    #   self.active_agent: str  # "Gemini" or "Claude"
    #   self.swarm_engine: HybridSwarmEngine
    #   self.hive_mind: TrueHiveMind
```

### core/swarm/hybrid_swarm_engine.py
```python
class HybridSwarmEngine:               # line 122
    """6-mode collaboration engine"""
    # Key methods:
    #   process_task(task, complexity) -> SwarmResult
    #   execute_turn(task, mode) -> Dict
```

### core/swarm/mode_selector.py
```python
class ModeSelector:                    # line 123
    """Selects collaboration mode with memory boost"""
    # Key attributes:
    #   self.success_memory: Optional[SuccessMemory]
    #   self.auto_memory: Optional[AutoMemory]
    # Key methods:
    #   select_mode(task_analysis) -> ModeProposal
    #   _apply_memory_boost(analysis, scores) -> Tuple  # line 614
```

### core/memory/success_memory.py
```python
class SuccessMemory:                   # line 101
    """Stores successful task patterns for future reference"""
    # Key methods:
    #   record_success(task_id, analysis, result, quality_score) -> SuccessEntry  # line 164
    #   get_best_mode_for_similar(query, min_similarity) -> Optional[Tuple]
    #   search_similar(query, k, min_similarity) -> List[SuccessEntry]
```

### core/fsm/stagnation_detector.py
```python
class StagnationDetector:              # line 25
    """Detects conversation stagnation, supports Hot-Swap Lead"""
    # Key methods:
    #   is_stagnant() -> bool
    #   should_swap_lead(current_lead, failure_count) -> bool      # line 308
    #   get_swap_recommendation(current_lead) -> dict              # line 325
    #   record_agent_failure(agent_id)                             # line 349
```

### core/drivers/gemini_driver_v7.py
```python
class GeminiDriverV7:                  # line 76
    """Gemini CLI wrapper with persistent session support"""
    # Key methods:
    #   invoke(context, task_type) -> Dict                         # line 122
    #   invoke_stream(context, task_type) -> Generator             # line 149
```

### core/drivers/claude_driver_hybrid.py
```python
class ClaudeDriverHybrid:              # line 71
    """Claude API wrapper with hybrid XML/natural language"""
    # Key methods:
    #   invoke(context) -> Dict                                    # line 97
    #   invoke_stream(context) -> Generator                        # line 231
    #   invoke_with_retry(context, max_retries) -> Dict            # line 444
```

### core/hive_mind/agent_registry.py
```python
class AgentRegistry:                   # line 47
    """Registry for SPAWNED agents (NOT Claude/Gemini providers)"""
    # Purpose: Track spawned specialist agents, prevent duplicates
    # Key methods:
    #   register_spawn(agent) -> str
    #   find_similar(capabilities) -> Optional[RegisteredAgent]
```

---

## 3. ALL ENUMS

### core/fsm/states.py
```python
class OrchestratorState(Enum):         # line 16
    IDLE = "idle"
    BRAINSTORMING = "brainstorming"
    EXECUTING_TOOL = "executing_tool"
    VALIDATING_CFL = "validating_cfl"
    WAITING_USER = "waiting_user"
    ERROR = "error"
    PANIC = "panic"
    SWARM_ANALYZING = "swarm_analyzing"
    SWARM_NEGOTIATING = "swarm_negotiating"
    SWARM_EXECUTING = "swarm_executing"
    EVOLUTION_BRAINSTORM = "evolution_brainstorm"
    HIVE_MIND = "hive_mind"
```

### core/hive_mind/types.py
```python
class HiveMindState(Enum):             # line 17
    HIVE_GATING = "hive_gating"
    HIVE_ANALYSIS = "hive_analysis"
    HIVE_DEBATE = "hive_debate"
    HIVE_ARCHITECTURE = "hive_architecture"
    HIVE_EXECUTION = "hive_execution"
    HIVE_DIAGNOSIS = "hive_diagnosis"
    HIVE_RETRY = "hive_retry"
    HIVE_CONSOLIDATION = "hive_consolidation"
    HIVE_COMPLETE = "hive_complete"
    HIVE_FAILED = "hive_failed"

class UserBreakpoint(Enum):            # line 63
    ANALYSIS_COMPLETE = "analysis_complete"
    DEBATE_RESOLVED = "debate_resolved"
    ARCHITECTURE_READY = "architecture_ready"
    EXECUTION_COMPLETE = "execution_complete"
    KNOWLEDGE_CONSOLIDATION = "knowledge_consolidation"

class RetentionDecision(Enum):         # line 71
    KEEP_PERMANENT = "keep_permanent"
    ARCHIVE_KNOWLEDGE = "archive_knowledge"
    MERGE_INTO_EXISTING = "merge_into_existing"
    DELETE = "delete"

class IssueSeverity(Enum):             # line 79
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class FailureType(Enum):               # line 87
    TOOL_ERROR = "tool_error"
    TIMEOUT = "timeout"
    VALIDATION_FAILED = "validation_failed"
    AGENT_DISAGREEMENT = "agent_disagreement"
    RESOURCE_EXHAUSTED = "resource_exhausted"
    EXTERNAL_SERVICE_FAILURE = "external_service_failure"
    UNKNOWN = "unknown"
```

### core/swarm/collaboration_modes.py
```python
class CollaborationMode(Enum):         # line 21
    PARALLEL = "parallel"
    SEQUENTIAL = "sequential"
    LEAD_SUPPORT = "lead_support"
    PING_PONG = "ping_pong"
    SPECIALIST = "specialist"
    RED_BLUE = "red_blue"
```

### core/swarm/task_analyzer.py
```python
class TaskComplexity(IntEnum):         # line 19
    TRIVIAL = 1
    SIMPLE = 2
    MODERATE = 3
    COMPLEX = 4
    EXPERT = 5

class TaskDomain(Enum):                # line 28
    CODING = "coding"
    RESEARCH = "research"
    WRITING = "writing"
    ANALYSIS = "analysis"
    DEBUGGING = "debugging"
    ARCHITECTURE = "architecture"
    TESTING = "testing"
    DOCUMENTATION = "documentation"
    DEVOPS = "devops"
    SECURITY = "security"
    DATA = "data"
    UNKNOWN = "unknown"
```

### core/swarm/session_manager.py
```python
class SessionStatus(str, Enum):        # line 32
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class SessionMode(str, Enum):          # line 41
    FRESH = "fresh"
    CONTINUE = "continue"
    BRANCH = "branch"
    EPHEMERAL = "ephemeral"            # EXISTS but NOT ACTIVATED
```

### core/swarm/hybrid_swarm_engine.py
```python
class SwarmPhase(Enum):                # line 64
    ANALYZING = "analyzing"
    NEGOTIATING = "negotiating"
    EXECUTING = "executing"
    VALIDATING = "validating"
    COMPLETE = "complete"
    FAILED = "failed"
```

### core/hive_mind/strategy_blacklist.py
```python
class FailureCategory(Enum):           # line 40
    TOOL_FAILURE = "tool_failure"
    VALIDATION_FAILURE = "validation_failure"
    TIMEOUT = "timeout"
    AGENT_ERROR = "agent_error"
    STAGNATION = "stagnation"
    EXTERNAL_SERVICE = "external_service"
    RESOURCE_EXHAUSTED = "resource_exhausted"
    UNKNOWN = "unknown"
```

### core/evolution/models.py
```python
class EvolutionPhaseStatus(Enum):      # line 13
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"
```

### core/routing/model_router.py
```python
class TaskType(Enum):                  # line 30
    BRAINSTORM = "brainstorm"
    REDTEAM = "redteam"
    ARCHITECT = "architect"
    EVOLUTION = "evolution"
    REASONING = "reasoning"
    RESEARCH = "research"
    ANALYSIS = "analysis"
    TOOL = "tool"
    VALIDATION = "validation"
    SIMPLE = "simple"
    FORMAT = "format"
```

### core/logging/logger_v7.py
```python
class LogLevel(Enum):                  # line 26
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class EventType(Enum):                 # line 35
    TOOL_EXECUTION = "tool_execution"
    AGENT_RESPONSE = "agent_response"
    STATE_TRANSITION = "state_transition"
    ERROR = "error"
    METRIC = "metric"
```

---

## 4. ALL DATACLASSES

### core/hive_mind/phases/phase_analysis.py (Phase Results)
```python
@dataclass AnalysisPhaseResult         # line 67
    gemini_analysis: IndependentAnalysis   # ⚠️ NOT .payload!
    claude_analysis: IndependentAnalysis
    comparison: AnalysisComparison
    needs_debate: bool
    skip_reason: Optional[str] = None
```

### core/hive_mind/types.py (25 dataclasses)
```python
@dataclass IndependentAnalysis         # line 104
@dataclass Disagreement                # line 131
@dataclass AnalysisComparison          # line 142
@dataclass DebateArgument              # line 158
@dataclass DebateResult                # line 172
@dataclass AgentSpec                   # line 192
@dataclass RAGConfig                   # line 204
@dataclass ExecutionStep               # line 213
@dataclass ExecutionPlan               # line 224
@dataclass AgentArchitecture           # line 233
@dataclass ExecutionIssue              # line 251
@dataclass MonitoredStepResult         # line 262
@dataclass FailureDiagnosis            # line 281
@dataclass RetryDecision               # line 310
@dataclass AgentRetention              # line 325
@dataclass KnowledgeEntry              # line 337
@dataclass KnowledgeConsolidation      # line 347
@dataclass BreakpointOption            # line 374
@dataclass BreakpointRequest           # line 383
@dataclass BreakpointResponse          # line 395
```

### core/swarm/*.py
```python
# task_analyzer.py:159
@dataclass TaskAnalysis:
    complexity: TaskComplexity
    domains: List[TaskDomain]
    primary_domain: TaskDomain
    requires_web: bool = False
    requires_code_execution: bool = False
    requires_deep_reasoning: bool = False
    requires_iteration: bool = False
    gemini_fit_score: float = 0.5
    claude_fit_score: float = 0.5
    raw_input: str = ""
    confidence: float = 0.5
    detected_keywords: List[str] = field(default_factory=list)
    # NOTE: PAS de champ 'reasoning' (contrairement à ModeProposal)

# mode_selector.py:57
@dataclass ModeProposal:
    mode: CollaborationMode            # NOTE: C'est .mode, PAS .recommended_mode
    confidence: float
    agent_assignments: List[AgentAssignment]
    reasoning: str                     # ModeProposal A un champ reasoning
    alternatives: List[Tuple[CollaborationMode, float]]
    timestamp: datetime

# mode_executors.py
@dataclass AgentResponse               # line 39
@dataclass ExecutionContext            # line 96
@dataclass ExecutionResult             # line 150

# session_manager.py
@dataclass AgentSession                # line 50
@dataclass TaskSession                 # line 98

# agent_metrics.py
@dataclass AgentInvocationResult       # line 51
@dataclass AgentProfile                # line 93
@dataclass AgentPool                   # line 161

# negotiation_protocol.py
@dataclass NegotiationMessage          # (in module)
@dataclass NegotiationResult           # (in module)
```

### core/memory/success_memory.py
```python
@dataclass SuccessEntry                # line 41
    task_id: str
    description: str
    complexity: str
    domains: List[str]
    primary_domain: Optional[str]
    swarm_mode: str
    lead_agent: Optional[str]
    support_agent: Optional[str]
    duration_seconds: float
    success: bool
    quality_score: float
    timestamp: str
    tags: List[str]
    embedding: Optional[List[float]] = None
```

### core/evolution/models.py
```python
@dataclass MutationProposal            # line 23
@dataclass ChildCreationResult         # line 37
@dataclass ValidationResult            # line 47
@dataclass EvaluationResult            # line 58
@dataclass PromotionResult             # line 70
@dataclass ArchiveResult               # line 80
@dataclass BrainstormResult            # line 89
@dataclass EvolutionResult             # line 99
@dataclass SpecializationResult        # line 116
@dataclass EvolutionStatus             # line 126
@dataclass EvolutionContext            # line 138
```

---

## 5. CRITICAL METHOD SIGNATURES

### TrueHiveMind.process_task()
```python
# core/hive_mind/orchestrator.py:235
async def process_task(
    self,
    task: str,
    complexity: TaskComplexity = TaskComplexity.MODERATE
) -> HiveMindResult:
```

### SuccessMemory.record_success()
```python
# core/memory/success_memory.py:164
def record_success(
    self,
    task_id: str,
    analysis: Any,           # TaskAnalysis
    result: Any,             # ExecutionResult or SwarmResult
    quality_score: Optional[float] = None
) -> SuccessEntry:
```

### ModeSelector._apply_memory_boost()
```python
# core/swarm/mode_selector.py:614
def _apply_memory_boost(
    self,
    analysis: TaskAnalysis,
    mode_scores: Dict[CollaborationMode, float]
) -> Tuple[Optional[CollaborationMode], Optional[Dict]]:
```

### StagnationDetector.get_swap_recommendation()
```python
# core/fsm/stagnation_detector.py:325
def get_swap_recommendation(self, current_lead: str) -> dict:
    # Returns: {"should_swap": bool, "new_lead": str, "reason": str, ...}
```

### HybridSwarmEngine.process_task()
```python
# core/swarm/hybrid_swarm_engine.py:193
def process_task(
    self,
    task: str,
    complexity: TaskComplexity = TaskComplexity.MODERATE,
    task_analysis: Optional[TaskAnalysis] = None
) -> Dict:
```

### GeminiDriverV7.invoke()
```python
# core/drivers/gemini_driver_v7.py:122
def invoke(
    self,
    context: str,
    session_uuid: Optional[str] = None  # ⚠️ NOT task_type!
) -> Dict:
    # Returns: {"sender": "Gemini", "content": str, "action_type": str, ...}
```

### ClaudeDriverHybrid.invoke()
```python
# core/drivers/claude_driver_hybrid.py:97
def invoke(self, context: str) -> Dict:
    # Returns: {"sender": "Claude", "content": str, "action_type": str, ...}
```

---

## 6. INTER-MODULE DEPENDENCIES

```
orchestration_v7.OrchestratorV7
├── imports hive_mind.TrueHiveMind
├── imports swarm.HybridSwarmEngine
├── imports fsm.StagnationDetector
├── imports drivers.GeminiDriverV7
├── imports drivers.ClaudeDriverHybrid
├── imports orchestration.FSMHandlers
├── imports orchestration.AgentInvoker
└── imports memory.ProjectMemory

hive_mind.TrueHiveMind
├── imports hive_mind.phases.* (7 phases)
├── imports hive_mind.AgentRegistry (spawned agents)
├── imports hive_mind.StrategyBlacklist
├── imports hive_mind.CostEstimator
├── imports hive_mind.UserInteractionHandler
├── imports fsm.StagnationDetector
└── uses drivers.GeminiDriverV7, ClaudeDriverHybrid

swarm.ModeSelector
├── imports memory.SuccessMemory (optional)
├── imports memory.AutoMemory (optional)
└── imports swarm.AgentPool

swarm.HybridSwarmEngine
├── imports swarm.ModeSelector
├── imports swarm.ModeExecutors (6 classes)
├── imports swarm.NegotiationProtocol
├── imports swarm.TaskAnalyzer
└── imports swarm.SessionManager
```

---

## 7. DOES NOT EXIST (Anti-Hallucination)

### Classes That DO NOT Exist
```
❌ HiveMindPipeline          → Use: TrueHiveMind
❌ AgentProvider             → Use: GeminiDriverV7, ClaudeDriverHybrid
❌ LLMProviderRegistry       → NOT IMPLEMENTED YET (planned V8.1.1)
❌ ProviderGuard             → NOT IMPLEMENTED YET (planned V8.1.4)
❌ IntentResolver            → NOT IMPLEMENTED YET (planned V8.1.5)
❌ SessionContext            → NOT IMPLEMENTED YET (planned V8.2.0)
```

### Methods/Fields That DO NOT Exist
```
❌ success_memory.record_async()      → Use: record_success() (sync)
❌ TrueHiveMind.run()                 → Use: process_task()
❌ HiveMindResult.dylan_score         → Field does not exist
❌ HiveMindResult.panic_recoveries    → Field does not exist
❌ TaskResult                         → Use: HiveMindResult or ExecutionResult
❌ TaskAnalysis.reasoning             → Field does NOT exist (ModeProposal has it)
❌ ModeProposal.recommended_mode      → Use: ModeProposal.mode
❌ subprocess.run in drivers          → Actually uses subprocess.Popen + threading
❌ AnalysisPhaseResult.payload        → Use: .gemini_analysis or .claude_analysis
❌ HiveMindState.HIVE_COMPLETE        → Use: HiveMindState.HIVE_SUCCESS
❌ GeminiDriverV7.invoke(task_type=)  → Use: invoke(context, session_uuid=)
```

### Files That DO NOT Exist
```
❌ core/static_map.py                 → Hardcoded lookups are in fsm_handlers.py
❌ core/hive_mind/pipeline.py         → Use: orchestrator.py
❌ core/agents/registry.py            → Use: hive_mind/agent_registry.py (spawned only)
❌ core/network/limiter.py            → NOT IMPLEMENTED YET
❌ core/context.py                    → NOT IMPLEMENTED YET (contextvars)
```

### Libraries NOT Currently Used
```
❌ aiolimiter                         → Not installed
❌ tenacity                           → Not installed
❌ contextvars                        → Not used (standard library, just not imported)
```

### AgentRegistry Clarification
```
⚠️ core/hive_mind/agent_registry.py EXISTS
   BUT it is for SPAWNED specialist agents, NOT for Claude/Gemini providers.

   Purpose: Track agents created via /spawn command
   NOT: A Provider Factory pattern for LLM drivers

   To abstract Claude/Gemini, need NEW: core/llm/provider_registry.py
```

---

## 8. IMPLEMENTATION STATUS

| Feature | Status | File | Line | Notes |
|---------|--------|------|------|-------|
| Hot-Swap Lead Agent | ✅ DONE | stagnation_detector.py | 308-357 | V8.0.1 |
| SuccessMemory.record_success | ✅ EXISTS | success_memory.py | 164 | Method exists |
| SuccessMemory write hook | ❌ NOT CALLED | - | - | No caller in pipeline |
| _apply_memory_boost | ✅ EXISTS | mode_selector.py | 614-685 | Reads from SuccessMemory |
| SessionMode.EPHEMERAL | ⚠️ EXISTS | session_manager.py | 46 | Enum exists, not activated |
| Fast-Track TRIVIAL | ❌ NOT IMPL | - | - | Planned V8.0.3 |
| LLMProviderRegistry | ❌ NOT IMPL | - | - | Planned V8.1.1 |
| Self-Healing Fallback | ❌ NOT IMPL | - | - | Planned V8.1.3 |
| Rate Limiting | ❌ NOT IMPL | - | - | Planned V8.1.4 |
| Async Driver Wrapper | ❌ NOT IMPL | - | - | Planned V8.1.6 (P1) |
| TaskAnalysis.reasoning | ❌ NOT IMPL | - | - | Planned V8.1.7 enhancement |
| contextvars Multi-Tenant | ❌ NOT IMPL | - | - | Planned V8.2.0 |

---

## 9. CONFIG KEYS

### core/config.py (selected keys)
```python
# Hive Mind
config.hive_mind_enabled: bool = True
config.hive_mind_moderate: bool = True
config.hive_mind_max_retries: int = 3
config.hive_mind_max_debate_turns: int = 10
config.hive_mind_min_debate_turns: int = 3
config.hive_mind_agreement_threshold: float = 0.85
config.hive_mind_budget_limit: int = 50000

# Swarm
config.swarm_enabled: bool = True
config.swarm_auto_route: bool = True
config.swarm_negotiation_enabled: bool = True
config.swarm_negotiation_max_turns: int = 4
config.swarm_default_mode: str = "ping_pong"
config.swarm_skip_trivial: bool = True
config.swarm_max_rounds: int = 6

# Model Routing
config.claude_opus_model: str = "claude-opus-4-5-20251101"
config.claude_sonnet_model: str = "claude-sonnet-4-5-20250929"
config.gemini_default_model: str = "gemini-3-pro-preview"
config.opus_task_types: list = ["brainstorm", "redteam", "architect", "evolution"]
config.sonnet_task_types: list = ["tool", "validation", "simple", "format"]

# Evolution
config.max_children_concurrent: int = 5
config.max_children_stable: int = 10
config.min_eval_hours: int = 24
config.red_team_mandatory: bool = False

# Memory
PROJECT_MEMORY_BACKEND: str = "dense"  # "dense", "tfidf", "bm25"
```

---

## 10. TEST COVERAGE

| Test File | Tests | Status | Coverage |
|-----------|-------|--------|----------|
| test_hot_swap_lead.py | 14 | ✅ PASS | StagnationDetector |
| test_llm_context_isolation.py | 16 | ⚠️ FLAKY | Real API calls |
| test_hybrid_swarm.py | 25 | ✅ PASS | HybridSwarmEngine |
| test_session_manager.py | 18 | ✅ PASS | SessionManager |
| test_agent_metrics.py | 12 | ✅ PASS | AgentPool/DyLAN |
| test_success_memory.py | 15 | ✅ PASS | SuccessMemory |
| test_mcp_client.py | 36 | ✅ PASS | MCPClient |

**Total**: 1,094 tests | **Pass Rate**: 98.5% (16 flaky)

---

## USAGE NOTES FOR EXTERNAL LLM

1. **Always check "DOES NOT EXIST" section before assuming a class/method exists**
2. **Line numbers are approximate** - search by class/method name for exact location
3. **HiveMindResult ≠ TaskResult** - Different dataclasses
4. **AgentRegistry is for spawned agents ONLY** - Not a Provider Factory
5. **record_success() is sync, not async** - No record_async() method
6. **SessionMode.EPHEMERAL exists but is not activated** - Just an enum value

---

*Generated by Claude for NEXUS V8.0 TRUE HIVE MIND*
*Last updated: 2025-12-08*
