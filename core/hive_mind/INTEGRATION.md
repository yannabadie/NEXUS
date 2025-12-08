# TRUE HIVE MIND V8.0 - Integration Strategy

## Overview

This document describes how V8 Hive Mind integrates with existing V7 systems.

## Gating Logic

```
                    USER INPUT
                         │
                         ▼
                ┌─────────────────┐
                │  TaskAnalyzer   │
                └────────┬────────┘
                         │
         ┌───────────────┼───────────────┐
         │               │               │
      TRIVIAL         SIMPLE      MODERATE/COMPLEX/EXPERT
         │               │               │
         ▼               ▼               ▼
    ┌─────────┐    ┌─────────┐    ┌─────────────────┐
    │ FAST    │    │ SINGLE  │    │  GATE CHECK     │
    │ PATH    │    │ AGENT   │    │                 │
    └─────────┘    └─────────┘    └────────┬────────┘
                                           │
                    ┌──────────────────────┼──────────────────────┐
                    │                      │                      │
             MODERATE only          MODERATE (if              COMPLEX/EXPERT
             & hive_moderate=F      hive_moderate=T)
                    │                      │                      │
                    ▼                      ▼                      ▼
              ┌─────────────┐       ┌─────────────────┐    ┌─────────────────┐
              │ V7 SWARM    │       │ V8 HIVE MIND    │    │ V8 HIVE MIND    │
              │ (existing)  │       │ (new)           │    │ (new)           │
              └─────────────┘       └─────────────────┘    └─────────────────┘
```

## Component Relationships

### 1. Agent Management

| Existing | Hive Mind | Relationship |
|----------|-----------|--------------|
| `AgentPool` | `AgentRegistry` | **COMPLEMENTARY** |
| - DyLAN metrics | - Anti-duplication | Pool for metrics, Registry for spawn control |
| - select_best_for_task | - find_similar | Both needed |
| `SpawnedAgentLoader` | - | Registry CALLS loader |

**Integration**: `AgentRegistry` uses `AgentPool` for metrics, `SpawnedAgentLoader` for discovery.

### 2. Cost Tracking

| Existing | Hive Mind | Relationship |
|----------|-----------|--------------|
| `BudgetTracker` | `CostEstimator` | **COMPLEMENTARY** |
| - USD costs | - Token estimates | Estimator → Tracker |
| - Daily limits | - Operation affordability | Chain: estimate → budget check |

**Integration**: `CostEstimator.can_afford()` calls `BudgetTracker.can_spend()` for final check.

### 3. Negotiation vs Debate

| Existing | Hive Mind | Relationship |
|----------|-----------|--------------|
| `NegotiationProtocol` | `StrategicDebatePhase` | **DIFFERENT SCOPES** |
| - MODE selection | - APPROACH resolution | Do NOT mix |
| - XML `<negotiate>` | - JSON arguments | Different protocols |
| - Max 4 rounds | - 3-10 adaptive | Different dynamics |

**Integration**: Keep separate. Negotiation for Swarm mode selection, Debate for task approach.

### 4. Failure Handling

| Existing | Hive Mind | Relationship |
|----------|-----------|--------------|
| `StagnationDetector` | `StrategyBlacklist` | **CHAIN** |
| - Output similarity | - Strategy tracking | Stagnation → Blacklist |
| `PanicSystem` | `AdaptiveRetryPhase` | **ESCALATION** |

**Integration**: Stagnation feeds blacklist. Retry phase uses blacklist. Panic if max retries.

### 5. Memory

| Existing | Hive Mind | Relationship |
|----------|-----------|--------------|
| `ProjectMemory` | `HiveMindContextManager` | **INTEGRATION IN PLACE** |
| `SuccessMemory` | `KnowledgeConsolidation` | Consolidation WRITES to memories |
| `MemoryManagerV7` | - | Blackboard persistence |

**Integration**: Phase 7 archives to ProjectMemory. Already implemented.

## Configuration Keys

```python
# In NexusConfig (nexus_config.py)

# V8 Hive Mind Settings
hive_mind_enabled: bool = True           # Enable V8 Hive Mind
hive_mind_moderate: bool = True          # Route MODERATE to Hive Mind (user decision)
hive_mind_budget_limit: int = 50000      # Token budget per task
hive_mind_max_debate_turns: int = 10     # Max debate turns
hive_mind_breakpoints_enabled: bool = True  # User breakpoints
```

## FSM State Additions

Existing V7 states are PRESERVED. V8 adds new states:

```python
# In core/fsm/states.py - OrchestratorState enum

# V7 States (unchanged)
IDLE = "idle"
BRAINSTORMING = "brainstorming"
EXECUTING_TOOL = "executing_tool"
VALIDATING_CFL = "validating_cfl"
WAITING_USER = "waiting_user"
ERROR = "error"
PANIC = "panic"
EVOLUTION_BRAINSTORM = "evolution_brainstorm"
SWARM_ANALYZING = "swarm_analyzing"
SWARM_NEGOTIATING = "swarm_negotiating"
SWARM_EXECUTING = "swarm_executing"

# V8 States (new)
HIVE_GATING = "hive_gating"
HIVE_ANALYZING = "hive_analyzing"
HIVE_DEBATING = "hive_debating"
HIVE_ARCHITECTING = "hive_architecting"
HIVE_EXECUTING = "hive_executing"
HIVE_DIAGNOSING = "hive_diagnosing"
HIVE_RETRYING = "hive_retrying"
HIVE_CONSOLIDATING = "hive_consolidating"
HIVE_BREAKPOINT = "hive_breakpoint"
```

## Entry Point

**File**: `core/orchestration/fsm_handlers.py`
**Method**: `_handle_moderate_plus()`

```python
def _handle_moderate_plus(self, user_input: str, task_analysis) -> Dict:
    complexity = task_analysis.complexity

    # V8 HIVE MIND GATE
    if self._should_use_hive_mind(complexity):
        return self._route_to_hive_mind(user_input, task_analysis)

    # V7 Swarm (existing behavior)
    if self._orch.swarm_engine and getattr(self._orch.config, 'swarm_auto_route', True):
        # ... existing swarm code ...
```

## Files Modified

1. `core/orchestration/fsm_handlers.py` - Add gating logic
2. `core/fsm/states.py` - Add HIVE_* states
3. `nexus_config.py` - Add hive_mind_* settings
4. `core/orchestration_v7.py` - Initialize HiveMind components

## Files Added (already created)

- `core/hive_mind/` - Complete V8 module
- `core/hive_mind/phases/` - 7 phases implementation

## Migration Path

1. **Phase A**: Add gating (no behavior change for existing tasks)
2. **Phase B**: Enable for COMPLEX/EXPERT only (safe)
3. **Phase C**: Enable for MODERATE (user decision implemented)
4. **Phase D**: Deprecate V7 Swarm for complex tasks (future)
