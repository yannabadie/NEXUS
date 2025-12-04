# Swarm Module - NEXUS V7.6 "HIVE MIND"

Hybrid Swarm Engine for dynamic multi-agent collaboration.

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

## Collaboration Modes (6 Active)

| Mode | Description | Use Case | Complexity Affinity |
|------|-------------|----------|---------------------|
| **PARALLEL** | Simultaneous work, merge results | Independent subtasks | 0.5 |
| **SEQUENTIAL** | Ordered execution (first → second) | Clear dependencies | 0.6 |
| **LEAD_SUPPORT** | Lead (80%) + Support (20%) | Dominant expertise | 0.7 |
| **PING_PONG** | Rapid alternation until convergence | Brainstorming, creativity | 0.6 |
| **SPECIALIST** | Single expert handles all | Exclusive expertise | 0.8 |
| **RED_BLUE** | Adversarial propose/attack/defend | Security, critical decisions | 1.0 |

### Mode Fallback Chain (Phase 8: Self-Healing)

```
PARALLEL    → SEQUENTIAL
RED_BLUE    → LEAD_SUPPORT
LEAD_SUPPORT → SPECIALIST
PING_PONG   → SEQUENTIAL
SEQUENTIAL  → SPECIALIST
SPECIALIST  → None (terminal)
```

When a mode fails, the engine automatically degrades to the fallback mode.

## Phase Status (V7.6)

| Phase | Description | Status |
|-------|-------------|--------|
| **Phase 7** | Session Isolation (SwarmSessionManager) | ✅ COMPLETE |
| **Phase 8** | Self-Healing Swarm (Fallback) | ✅ COMPLETE |
| **Phase 10a** | Success Memory | ✅ COMPLETE |
| **Phase 10b** | Memory-Augmented Mode Selection | ✅ COMPLETE |
| **Phase 10d** | Session-Aware Agent Selection | ✅ COMPLETE |
| **Phase 5b** | N-Agent Agnosticism (Spawned Agents) | ✅ COMPLETE |

## Files

| File | Purpose | Key Classes |
|------|---------|-------------|
| `collaboration_modes.py` | Mode definitions + fallback | `CollaborationMode`, `ModeCharacteristics` |
| `task_analyzer.py` | Task analysis | `TaskAnalyzer`, `TaskComplexity`, `TaskDomain` |
| `mode_selector.py` | Mode selection + session-aware | `ModeSelector`, `ModeProposal` |
| `negotiation_protocol.py` | Agent negotiation | `NegotiationProtocol`, `NegotiationResult` |
| `mode_executors.py` | Execution + self-healing | `ParallelExecutor`, `execute_with_fallback()` |
| `hybrid_swarm_engine.py` | Main engine | `HybridSwarmEngine`, `SwarmResult` |
| `agent_metrics.py` | DyLAN + session scoring | `AgentProfile`, `AgentPool` |
| `session_manager.py` | Session isolation | `SwarmSessionManager`, `TaskSession` |
| `atomic_store.py` | Thread-safe JSON | `AtomicJsonStore` |

## Key Classes

### HybridSwarmEngine

Main orchestration engine (hybrid_swarm_engine.py:111-787).

```python
from core.swarm import HybridSwarmEngine

engine = HybridSwarmEngine(
    agent_pool=agent_pool,
    model_router=router,
    config=config,
    invoke_agent=orchestrator._invoke_for_swarm,
    workspace_path=workspace_path
)

result = engine.process_task(
    task_input="Fix the auth bug",
    forced_mode=None,  # Or CollaborationMode.SPECIALIST
    skip_negotiation=False
)
```

**Pipeline**:
1. `ANALYZING` - TaskAnalyzer determines complexity/domains
2. `SELECTING` - ModeSelector picks optimal mode
3. `NEGOTIATING` - Agents debate via `<negotiate>` JSON
4. `EXECUTING` - ModeExecutor runs selected mode
5. Return `SwarmResult`

### Session-Aware Agent Selection (Phase 10d)

Hybrid scoring: DyLAN + Session Success Rate (mode_selector.py:546-617).

```python
# Formula
Score = (DyLAN_importance × 0.7) + (Session_success_rate × 0.3)

# Session bonus
HIGH_SESSION_BONUS = 0.08   # Success rate ≥ 0.8
MEDIUM_SESSION_BONUS = 0.05 # Success rate ≥ 0.6
LOW_SESSION_BONUS = 0.02    # Success rate ≥ 0.4
```

### Self-Healing Execution (Phase 8)

Automatic fallback on mode failure (mode_executors.py:351-433).

```python
from core.swarm import execute_with_fallback

result = execute_with_fallback(
    initial_mode=CollaborationMode.PARALLEL,
    context=execution_context,
    max_fallbacks=2
)

# If PARALLEL fails:
# 1. Create checkpoint
# 2. Fallback to SEQUENTIAL
# 3. If still fails: Fallback to SPECIALIST
# 4. Result metadata includes fallback_path
```

### SwarmSessionManager (Phase 7)

Session isolation for PARALLEL mode (session_manager.py).

```python
from core.swarm import SwarmSessionManager, generate_task_id

manager = SwarmSessionManager(workspace_path)

# Create task
task_id = generate_task_id()  # "task_20251204_151800_abc123"
manager.create_task(task_id, "PARALLEL")

# Get isolated session UUIDs
gemini_uuid = manager.get_or_create_session(task_id, "lead", "gemini")
claude_uuid = manager.get_or_create_session(task_id, "support", "claude")

# Pass to drivers: --resume {uuid}
```

## Task Analysis

### Complexity Levels

| Level | Value | Description | Negotiation |
|-------|-------|-------------|-------------|
| `TRIVIAL` | 1 | Single-step tasks | Skip |
| `SIMPLE` | 2 | Basic operations | Minimal |
| `MODERATE` | 3 | Standard tasks | Full |
| `COMPLEX` | 4 | Multi-step planning | Extended |
| `EXPERT` | 5 | Critical decisions | RED_BLUE |

### Task Domains

| Domain | Description | Agent Affinity |
|--------|-------------|----------------|
| `CODING` | Code writing/editing | Claude |
| `RESEARCH` | Information gathering | Gemini |
| `ANALYSIS` | Code review, debugging | Both |
| `CREATIVE` | Design, brainstorming | Both |
| `DEBUGGING` | Bug investigation | Claude |
| `SECURITY` | Security analysis | Both |

## Negotiation Protocol

Hybrid format: Natural language + `<negotiate>` JSON.

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

**Constraints**:
- Max 4 turns
- Consensus threshold: 0.6
- Fallback to initial proposal on timeout

## Dormant DNA: Graph of Thought (GoT)

**Status**: DORMANT - Full implementation exists but never activated.

**Location**: `hybrid_swarm_engine.py:605-786`

**Implementation**:
```python
_GOT_AVAILABLE = False  # Disabled via lazy import
try:
    from core.reasoning import GraphOfThought, ThoughtGraph, ThoughtNode
    _GOT_AVAILABLE = True
except ImportError:
    pass
```

**Available Methods** (not called in process_task):
| Method | Lines | Purpose |
|--------|-------|---------|
| `should_use_got()` | 605-626 | Returns True for COMPLEX/EXPERT tasks |
| `decompose_with_got()` | 628-670 | Creates ThoughtGraph with sub-problems |
| `_generate_sub_problems()` | 672-726 | Domain-specific decomposition (4-8 subs) |
| `execute_thought_graph()` | 728-772 | Executes each node through swarm |
| `get_got_summary()` | 778-786 | Extracts final answer |

**Activation Path**:
1. Implement `core/reasoning/` module with `GraphOfThought` class
2. Set `SWARM_GOT_ENABLED=True` in config
3. Call `engine.decompose_with_got()` for COMPLEX+ tasks

**Design Intent**: Decompose expert-level tasks into sub-problems, execute each through swarm, merge results.

## Configuration

```bash
# Core
SWARM_ENABLED=True                  # Enable swarm engine
SWARM_AUTO_ROUTE=True               # Auto-route MODERATE+ tasks
SWARM_NEGOTIATION=True              # Enable negotiation phase
SWARM_NEGOTIATION_TURNS=4           # Max negotiation rounds
SWARM_DEFAULT_MODE=ping_pong        # Fallback mode
SWARM_MAX_ROUNDS=6                  # Max execution rounds

# Session (Phase 7)
SWARM_SESSION_RETENTION_HOURS=24    # Session cleanup age

# Self-Healing (Phase 8)
SWARM_MAX_FALLBACKS=2               # Max fallback attempts

# GoT (Dormant)
SWARM_GOT_ENABLED=False             # Graph of Thought activation
```

## Usage Examples

### Basic Task Processing

```python
from core.swarm import HybridSwarmEngine

result = engine.process_task("Review the auth module security")

print(f"Mode: {result.mode}")        # RED_BLUE
print(f"Status: {result.status}")    # SUCCESS
print(f"Outputs: {result.outputs}")  # [proposal, attack, defend, ...]
```

### Force Specific Mode

```python
result = engine.process_task(
    "Write unit tests",
    forced_mode=CollaborationMode.SPECIALIST
)
```

### Skip Negotiation

```python
result = engine.process_task(
    "Quick fix",
    skip_negotiation=True  # Use initial proposal directly
)
```

## Swarm Flow

```
1. USER INPUT
   │
   ▼
2. ANALYZING (TaskAnalyzer)
   │ Complexity: MODERATE-EXPERT
   │ Domains: [CODING, SECURITY]
   ▼
3. SELECTING (ModeSelector)
   │ Mode: LEAD_SUPPORT
   │ Agents: Claude(lead), Gemini(support)
   ▼
4. NEGOTIATING (NegotiationProtocol) [Optional]
   │ Max 4 turns, consensus or fallback
   ▼
5. EXECUTING (ModeExecutor)
   │ With self-healing fallback if needed
   ▼
6. VALIDATING_CFL (FSM)
   │ Cross-validation of results
   ▼
7. IDLE
```

## Dependencies

### Internal
- `core.config` - Swarm configuration
- `core.synapse` - Message schemas (LightMessageV7/HeavyMessageV7)
- `core.routing` - Model selection
- `core.memory` - SuccessMemory (Phase 10b)
- `core.fsm` - State transitions

### External
- `concurrent.futures` - PARALLEL execution
- `dataclasses` - Data structures
- `threading.RLock` - Thread safety

## See Also

- [FSM Module](../fsm/README.md) - State machine (SWARM_* states reserved)
- [Memory Module](../memory/README.md) - SuccessMemory for session scoring
- [Drivers Module](../drivers/README.md) - Session UUID passing
- [Synapse Module](../synapse/README.md) - Message schemas
