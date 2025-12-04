# Swarm Module

Hybrid Swarm Engine for dynamic multi-agent collaboration in NEXUS V7.5 HIVE MIND.

## Overview

The Swarm module (Sprint 9) enables **dynamic collaboration mode selection** where agents negotiate the optimal way to work together for each task. Instead of fixed roles, agents adapt their collaboration style based on task complexity.

## Architecture

```
                         USER INPUT
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    HYBRID SWARM ENGINE                          │
│                                                                 │
│  ┌──────────────────┐   ┌──────────────────┐   ┌─────────────┐  │
│  │   TaskAnalyzer   │──▶│   ModeSelector   │──▶│ Negotiation │  │
│  │  • Complexity    │   │   • DyLAN scores │   │  Protocol   │  │
│  │  • Domains       │   │   • Mode scoring │   │  • Hybrid   │  │
│  └──────────────────┘   └──────────────────┘   └─────────────┘  │
│                                                      │          │
│                                                      ▼          │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    MODE EXECUTORS                        │   │
│  │  ┌──────────┐ ┌──────────┐ ┌────────────┐ ┌──────────┐  │   │
│  │  │ PARALLEL │ │SEQUENTIAL│ │LEAD_SUPPORT│ │PING_PONG │  │   │
│  │  └──────────┘ └──────────┘ └────────────┘ └──────────┘  │   │
│  │  ┌────────────┐ ┌──────────┐                             │   │
│  │  │ SPECIALIST │ │ RED_BLUE │                             │   │
│  │  └────────────┘ └──────────┘                             │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

## Collaboration Modes

| Mode | Description | Use Case |
|------|-------------|----------|
| **PARALLEL** | Simultaneous work, merge results | Independent subtasks |
| **SEQUENTIAL** | Ordered execution (first → second) | Clear dependencies |
| **LEAD_SUPPORT** | Lead (80%) + Support (20%) | Dominant expertise |
| **PING_PONG** | Rapid alternation until convergence | Brainstorming, creativity |
| **SPECIALIST** | Single expert handles all | Exclusive expertise |
| **RED_BLUE** | Adversarial propose/attack/defend | Security, critical decisions |

## Alignement ROADMAP V7.5+

| Phase ROADMAP | Impact sur ce module |
|---------------|---------------------|
| **Phase 7: Session Isolation** | `SwarmSessionManager` - Session UUIDs per task (COMPLETE) |
| **Phase 5b: N-Agent Agnosticism** | Spawned agents utilisables dans tous les modes (PENDING) |
| **Phase 8: Self-Healing** | Mode fallback automatique (PENDING) |

## Files

| File | Purpose | Key Classes |
|------|---------|-------------|
| `collaboration_modes.py` | Mode definitions | `CollaborationMode`, `ModeCharacteristics` |
| `task_analyzer.py` | Task analysis | `TaskAnalyzer`, `TaskComplexity`, `TaskDomain` |
| `mode_selector.py` | Mode selection | `ModeSelector`, `ModeProposal` |
| `negotiation_protocol.py` | Agent negotiation | `NegotiationProtocol`, `NegotiationResult` |
| `mode_executors.py` | Execution strategies | `ParallelExecutor`, `RedBlueExecutor`, etc. |
| `hybrid_swarm_engine.py` | Main engine | `HybridSwarmEngine`, `SwarmResult` |
| `agent_metrics.py` | DyLAN scoring | `AgentProfile`, `AgentPool` |
| `session_manager.py` | Phase 7: Session isolation | `SwarmSessionManager`, `TaskSession`, `AgentSession` |

## Key Classes

### HybridSwarmEngine

Main orchestration engine.

```python
from core.swarm import HybridSwarmEngine, create_default_pool
from core.routing import ModelRouter
from core.config import Config

config = Config()
agent_pool = create_default_pool()
router = ModelRouter(config)

engine = HybridSwarmEngine(agent_pool, router, config)
result = engine.process_task("Fix the auth bug", blackboard)
```

**Methods**:
| Method | Description | Returns |
|--------|-------------|---------|
| `process_task(task, blackboard)` | Full task processing | `SwarmResult` |
| `analyze_task(task)` | Analyze complexity | `TaskAnalysis` |
| `select_mode(analysis)` | Select optimal mode | `ModeProposal` |
| `negotiate(proposal)` | Agent negotiation | `NegotiationResult` |
| `execute(mode, context)` | Execute mode | `ExecutionResult` |

### TaskAnalyzer

Analyzes task complexity and domains.

```python
from core.swarm import TaskAnalyzer, TaskComplexity, TaskDomain

analyzer = TaskAnalyzer()
analysis = analyzer.analyze("Fix the JWT validation bug in auth.py")

# TaskAnalysis:
#   complexity: TaskComplexity.MODERATE
#   domains: [TaskDomain.CODING, TaskDomain.SECURITY]
#   requires_web: False
#   requires_code_execution: True
#   gemini_fit_score: 0.6
#   claude_fit_score: 0.9
```

**Task Complexity Levels**:
| Level | Description | Negotiation |
|-------|-------------|-------------|
| `TRIVIAL` (1) | Single-step tasks | Skip |
| `SIMPLE` (2) | Basic operations | Minimal |
| `MODERATE` (3) | Standard tasks | Full |
| `COMPLEX` (4) | Multi-step planning | Extended |
| `EXPERT` (5) | Critical decisions | RED_BLUE |

**Task Domains**:
- `CODING` - Code writing/editing
- `RESEARCH` - Information gathering
- `ANALYSIS` - Code review, debugging
- `CREATIVE` - Design, brainstorming
- `DEBUGGING` - Bug investigation
- `SECURITY` - Security analysis

### ModeSelector

Selects optimal collaboration mode using DyLAN scores.

```python
from core.swarm import ModeSelector, AgentPool

selector = ModeSelector(agent_pool)
proposal = selector.select_mode(analysis, available_agents)

# ModeProposal:
#   mode: CollaborationMode.LEAD_SUPPORT
#   confidence: 0.85
#   agent_assignments: {
#       "lead": "Claude",
#       "support": "Gemini"
#   }
```

### NegotiationProtocol

Hybrid negotiation (natural language + JSON).

```python
from core.swarm import NegotiationProtocol

protocol = NegotiationProtocol(
    max_turns=4,
    consensus_threshold=0.6
)

result = protocol.run_negotiation(
    task_analysis,
    initial_proposal,
    invoke_agent_callback
)

# NegotiationResult:
#   status: NegotiationStatus.CONSENSUS
#   selected_mode: CollaborationMode.LEAD_SUPPORT
#   final_assignments: {...}
#   negotiation_history: [...]
```

**Negotiation Message Format**:
```
Gemini: "For this debugging task, I suggest LEAD_SUPPORT mode.
Claude has strong Python expertise, so they should lead.

<negotiate>
{
  "proposed_mode": "lead_support",
  "proposed_lead": "Claude",
  "confidence": 0.85
}
</negotiate>"
```

### Mode Executors

Each mode has a dedicated executor.

```python
from core.swarm import get_executor, CollaborationMode

executor = get_executor(CollaborationMode.PARALLEL)
result = executor.execute(context)
```

**Executor Types**:

| Executor | Mode | Strategy |
|----------|------|----------|
| `ParallelExecutor` | PARALLEL | ThreadPoolExecutor, merge results |
| `SequentialExecutor` | SEQUENTIAL | First → Second, chain outputs |
| `LeadSupportExecutor` | LEAD_SUPPORT | Lead produces, Support reviews |
| `PingPongExecutor` | PING_PONG | Alternate until convergence |
| `SpecialistExecutor` | SPECIALIST | Single agent handles all |
| `RedBlueExecutor` | RED_BLUE | Propose → Attack → Defend |

### AgentPool & AgentProfile

DyLAN-based agent metrics and selection.

```python
from core.swarm import AgentPool, AgentProfile, create_default_pool

pool = create_default_pool()

# Get agent
claude = pool.get_agent("claude_primary")

# Record performance
claude.record_invocation(
    task_type="coding",
    success=True,
    latency=2.5,
    quality_score=0.9
)

# Get importance score for task
importance = claude.get_task_importance("coding")
# 0.95 (high due to good history)
```

## Swarm Flow

```
1. USER INPUT
   │
   ▼
2. SWARM_ANALYZING
   │ TaskAnalyzer determines complexity, domains
   ▼
3. SWARM_NEGOTIATING
   │ Agents debate optimal mode via <negotiate> JSON
   │ Max 4 turns, consensus or fallback
   ▼
4. SWARM_EXECUTING
   │ Selected executor runs the mode
   │ Agents collaborate per mode rules
   ▼
5. VALIDATING_CFL
   │ Results validated
   ▼
6. IDLE
```

## Configuration

Environment variables:
```bash
SWARM_ENABLED=True                  # Enable swarm engine
SWARM_NEGOTIATION=True              # Enable negotiation
SWARM_NEGOTIATION_TURNS=4           # Max negotiation rounds
SWARM_DEFAULT_MODE=ping_pong        # Fallback mode
SWARM_SKIP_TRIVIAL=True             # Skip for trivial tasks
SWARM_MAX_ROUNDS=6                  # Max execution rounds
```

## Usage Example

```python
from core.swarm import (
    HybridSwarmEngine,
    create_default_pool,
    CollaborationMode
)
from core.routing import ModelRouter
from core.config import Config
from pathlib import Path

# Initialize
config = Config()
pool = create_default_pool()
router = ModelRouter(config)

engine = HybridSwarmEngine(pool, router, config)

# Process task
blackboard = {"state": {}, "messages": []}
result = engine.process_task(
    "Review the security of the auth module",
    blackboard
)

# Result
print(f"Mode used: {result.mode}")           # RED_BLUE
print(f"Status: {result.status}")            # SUCCESS
print(f"Agent outputs: {result.outputs}")    # [Claude proposal, Gemini attack, ...]
```

## SwarmSessionManager (Phase 7)

Session isolation to prevent "Context Bleeding" in PARALLEL mode.

**Problem**: Without isolation, parallel tasks share context and corrupt each other's state.

**Solution**: Each task gets a unique `task_id`, and each agent-role combination gets a unique `session_uuid`.

```python
from core.swarm import SwarmSessionManager, generate_task_id

# Initialize manager (persists to workspace/.nexus/session_registry.json)
manager = SwarmSessionManager(workspace_path)

# Create a task
task_id = generate_task_id()  # "task_20251204_151800_abc123"
manager.create_task(task_id, "PARALLEL")

# Get session UUIDs for each agent-role
gemini_uuid = manager.get_or_create_session(task_id, "lead", "gemini")
claude_uuid = manager.get_or_create_session(task_id, "support", "claude")

# Pass UUIDs to CLI drivers for session resumption
# gemini --resume {gemini_uuid}

# Complete task when done
manager.complete_task(task_id)

# Cleanup old completed tasks
manager.cleanup_completed(max_age_hours=24)
```

**Key Features**:
- **Atomic persistence** via `AtomicJsonStore` (no corruption)
- **Thread-safe** with `RLock` for concurrent access
- **Session modes**: FRESH, CONTINUE, BRANCH (fork from existing)
- **Crash recovery**: Registry survives restarts

**Session Flow**:
```
1. HybridSwarmEngine.process_task()
   │
2. SwarmSessionManager.create_task(task_id, mode)
   │
3. For each agent in task:
   │  SwarmSessionManager.get_or_create_session(task_id, role, agent_id)
   │  → Returns unique session_uuid
   │
4. ModeExecutor passes session_uuid to driver
   │  → CLI uses --resume {uuid} for isolation
   │
5. SwarmSessionManager.complete_task(task_id)
```

## Dependencies

### Internal
- `core.config` - Swarm configuration
- `core.synapse` - Message schemas
- `core.routing` - Model selection
- `core.utils` - AtomicJsonStore (Phase 7)

### External
- `concurrent.futures` - Parallel execution
- `dataclasses` - Data structures

## See Also

- [Core README](../README.md) - Architecture overview
- [FSM Module](../fsm/README.md) - Swarm states
- [Routing Module](../routing/README.md) - Model selection
- [Hybrid Swarm Docs](../../docs/HYBRID_SWARM.md) - Detailed guide
