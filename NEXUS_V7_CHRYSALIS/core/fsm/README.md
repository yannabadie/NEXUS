# FSM Module

Finite State Machine components for NEXUS V7 orchestration.

## Overview

The FSM module implements the state machine that governs NEXUS operation, including:
- **State definitions** and transitions
- **Panic recovery** system for fatal errors
- **Stagnation detection** for loop prevention
- **Plan health monitoring**

## Architecture

```
                     ┌─────────────────────────────────────────────┐
                     │              FSM CONTROLLER                 │
                     └─────────────────────────────────────────────┘
                                          │
        ┌──────────────┬──────────────┬───┴───┬───────────────────┐
        ▼              ▼              ▼       ▼                   ▼
┌──────────────┐ ┌──────────────┐ ┌────────────┐ ┌────────────┐ ┌─────────┐
│    IDLE      │ │ BRAINSTORM   │ │  EXECUTE   │ │  VALIDATE  │ │  PANIC  │
│              │─▶│              │─▶│    TOOL    │─▶│    CFL     │ │         │
└──────────────┘ └──────────────┘ └────────────┘ └────────────┘ └─────────┘
        ▲                                               │               │
        └───────────────────────────────────────────────┴───────────────┘

                     ┌─────────────────────────────────────────────┐
                     │           SWARM STATES (Sprint 9)           │
                     └─────────────────────────────────────────────┘
                     ANALYZING ──▶ NEGOTIATING ──▶ EXECUTING
```

## Files

| File | Purpose | Key Classes |
|------|---------|-------------|
| `states.py` | State enum definition | `OrchestratorState` |
| `panic_system.py` | Error recovery | `PanicSystem`, `PanicEvent` |
| `stagnation_detector.py` | Loop detection | `StagnationDetector` |
| `plan_health.py` | Plan monitoring | `PlanHealthChecker` |
| `__init__.py` | Module exports | - |

## Key Classes

### OrchestratorState

Enum defining all possible FSM states.

```python
from core.fsm import OrchestratorState

# Core states
OrchestratorState.IDLE              # Waiting for user input
OrchestratorState.BRAINSTORMING     # Agents discussing
OrchestratorState.EXECUTING_TOOL    # Tool in progress
OrchestratorState.VALIDATING_CFL    # Validating tool result
OrchestratorState.WAITING_USER      # Task complete
OrchestratorState.ERROR             # Recoverable error
OrchestratorState.PANIC             # Fatal error

# Evolution states
OrchestratorState.EVOLUTION_BRAINSTORM  # Agents designing mutations

# Swarm states (V7 Sprint 9)
OrchestratorState.SWARM_ANALYZING       # Task analysis
OrchestratorState.SWARM_NEGOTIATING     # Mode negotiation
OrchestratorState.SWARM_EXECUTING       # Mode execution
```

### PanicSystem

Handles fatal errors and recovery.

**Purpose**: Track error patterns, trigger panic mode, log for analysis.

```python
from core.fsm import PanicSystem

panic = PanicSystem(workspace_path)

# Record an error
panic.record_event(
    error_type="CLI_CRASH",
    context={"agent": "Gemini", "error": "Timeout"},
    severity="CRITICAL"
)

# Check if panic mode needed
if panic.should_panic(consecutive_errors=5):
    # Transition to PANIC state
    ...

# Reset after recovery
panic.reset()
```

**Panic Events**:
| Type | Severity | Trigger |
|------|----------|---------|
| `CLI_CRASH` | CRITICAL | CLI process failed |
| `PARSE_ERROR` | HIGH | JSON/XML parsing failed repeatedly |
| `STAGNATION` | MEDIUM | Repetitive responses detected |
| `TIMEOUT` | HIGH | Response timeout exceeded |
| `CORRUPTION` | CRITICAL | State file corrupted |

### StagnationDetector

Detects when agents are stuck in loops.

**Purpose**: Prevent infinite back-and-forth with identical responses.

```python
from core.fsm import StagnationDetector

detector = StagnationDetector(
    similarity_threshold=0.8,  # 80% similarity = stagnation
    window_size=5              # Check last 5 messages
)

# Check for stagnation
is_stagnant = detector.check(new_message)

if is_stagnant:
    # Force state transition or intervention
    ...

# Reset on new task
detector.reset()
```

**Detection Algorithm**:
1. Compute text similarity with recent messages
2. If similarity > threshold for N consecutive turns
3. Flag stagnation, suggest intervention

### PlanHealthChecker

Monitors plan execution health.

**Purpose**: Track plan progress, detect stuck tasks, suggest corrections.

```python
from core.fsm import PlanHealthChecker

checker = PlanHealthChecker()

# Update with task progress
checker.update_task(task_id="T1", status="in_progress", progress=0.5)

# Check health
health = checker.get_health()
# {
#     "overall_progress": 0.5,
#     "stuck_tasks": [],
#     "overdue_tasks": [],
#     "healthy": True
# }
```

## State Transitions

### Normal Flow
```
IDLE → BRAINSTORMING → EXECUTING_TOOL → VALIDATING_CFL → IDLE
```

### Swarm Flow (V7)
```
IDLE → SWARM_ANALYZING → SWARM_NEGOTIATING → SWARM_EXECUTING → VALIDATING_CFL → IDLE
```

### Evolution Flow
```
IDLE → EVOLUTION_BRAINSTORM → VALIDATING_CFL → IDLE
```

### Error Recovery
```
ANY_STATE → ERROR → (user /reset) → IDLE
ANY_STATE → PANIC → (restart session) → IDLE
```

## Transition Rules

| From State | Trigger | To State |
|------------|---------|----------|
| `IDLE` | User input | `BRAINSTORMING` or `SWARM_ANALYZING` |
| `BRAINSTORMING` | TOOL_USE action | `EXECUTING_TOOL` |
| `BRAINSTORMING` | FINISHED status | `WAITING_USER` |
| `EXECUTING_TOOL` | Tool complete | `VALIDATING_CFL` |
| `VALIDATING_CFL` | SUCCESS | `IDLE` or `BRAINSTORMING` |
| `VALIDATING_CFL` | FAILURE | `BRAINSTORMING` (retry) |
| `SWARM_ANALYZING` | Analysis complete | `SWARM_NEGOTIATING` |
| `SWARM_NEGOTIATING` | Consensus | `SWARM_EXECUTING` |
| `SWARM_EXECUTING` | Mode complete | `VALIDATING_CFL` |
| `ANY` | Error threshold | `ERROR` or `PANIC` |

## Configuration

Environment variables:
```bash
MAX_STALEMATE_COUNT=5              # Stalemates before panic
STAGNATION_SIMILARITY_THRESHOLD=0.8  # Similarity threshold
```

## Usage Example

```python
from core.fsm import OrchestratorState, PanicSystem, StagnationDetector
from pathlib import Path

# Initialize components
panic = PanicSystem(Path("./workspace"))
detector = StagnationDetector(similarity_threshold=0.8)

# State management
current_state = OrchestratorState.IDLE

def transition(new_state: OrchestratorState):
    global current_state
    print(f"Transition: {current_state.name} → {new_state.name}")
    current_state = new_state

# Example flow
transition(OrchestratorState.BRAINSTORMING)
# ... agent interaction ...
transition(OrchestratorState.EXECUTING_TOOL)
# ... tool execution ...
transition(OrchestratorState.VALIDATING_CFL)
# ... validation ...
transition(OrchestratorState.IDLE)
```

## Dependencies

### Internal
- `core.config` - Configuration parameters
- `core.logging` - Event logging

### External
- `enum` - State enumeration
- `difflib` - Text similarity (stagnation)

## See Also

- [Core README](../README.md) - Architecture overview
- [Swarm Module](../swarm/README.md) - Swarm states
- [Synapse Module](../synapse/README.md) - Message schemas
