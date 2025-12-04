# FSM Module - NEXUS V7.6 "HIVE MIND"

Finite State Machine components for NEXUS V7 orchestration.

## Overview

The FSM module implements the state machine that governs NEXUS operation:
- **State definitions** and transitions (11 states total)
- **TRANSITION_MATRIX** - Complete state machine specification
- **VALIDATING_CFL** - Cognitive Feedback Loop validation
- **Panic recovery** system for fatal errors
- **Stagnation detection** for loop prevention
- **Plan health monitoring**
- **TaskExecutionContext** - Immutable execution context (Phase 0d)

## State Diagram (from TRANSITION_MATRIX)

```mermaid
stateDiagram-v2
    [*] --> IDLE

    IDLE --> BRAINSTORMING: user_input

    BRAINSTORMING --> EXECUTING_TOOL: tool_use
    BRAINSTORMING --> WAITING_USER: finished
    BRAINSTORMING --> ERROR: stagnation

    EXECUTING_TOOL --> VALIDATING_CFL: tool_completed

    VALIDATING_CFL --> IDLE: success + finished
    VALIDATING_CFL --> BRAINSTORMING: success + continue
    VALIDATING_CFL --> BRAINSTORMING: failure (retry)
    VALIDATING_CFL --> ERROR: stalemate

    WAITING_USER --> BRAINSTORMING: user_input

    ERROR --> IDLE: /reset
    ERROR --> PANIC: timeout

    PANIC --> [*]: restart required

    state "EVOLUTION_BRAINSTORM" as evo
    IDLE --> evo: /evolve
    evo --> IDLE: mutations_complete

    note right of SWARM_ANALYZING: [RESERVED] Sprint 9
    note right of SWARM_NEGOTIATING: Bypassed by process_with_swarm()
    note right of SWARM_EXECUTING: Full FSM integration planned
```

## TRANSITION_MATRIX (states.py:143-188)

The complete FSM specification from source code:

```python
TRANSITION_MATRIX = {
    OrchestratorState.IDLE: {
        "user_input": OrchestratorState.BRAINSTORMING
    },
    OrchestratorState.BRAINSTORMING: {
        "tool_use": OrchestratorState.EXECUTING_TOOL,
        "finished": OrchestratorState.WAITING_USER,
        "stagnation": OrchestratorState.ERROR
    },
    OrchestratorState.EXECUTING_TOOL: {
        "tool_completed": OrchestratorState.VALIDATING_CFL
    },
    OrchestratorState.VALIDATING_CFL: {
        "success": OrchestratorState.IDLE,
        "failure": OrchestratorState.BRAINSTORMING,
        "stalemate": OrchestratorState.ERROR
    },
    OrchestratorState.WAITING_USER: {
        "user_input": OrchestratorState.BRAINSTORMING
    },
    OrchestratorState.ERROR: {
        "reset": OrchestratorState.IDLE,
        "timeout": OrchestratorState.PANIC
    },
    OrchestratorState.PANIC: {
        # No transitions - session restart required
    },
    # RESERVED: Swarm FSM states (Sprint 9)
    OrchestratorState.SWARM_ANALYZING: {
        "analysis_complete": OrchestratorState.SWARM_NEGOTIATING,
        "skip_negotiation": OrchestratorState.SWARM_EXECUTING,
        "error": OrchestratorState.ERROR
    },
    OrchestratorState.SWARM_NEGOTIATING: {
        "consensus": OrchestratorState.SWARM_EXECUTING,
        "timeout": OrchestratorState.SWARM_EXECUTING,
        "error": OrchestratorState.ERROR
    },
    OrchestratorState.SWARM_EXECUTING: {
        "execution_complete": OrchestratorState.VALIDATING_CFL,
        "continue": OrchestratorState.SWARM_EXECUTING,
        "error": OrchestratorState.ERROR
    }
}
```

## Files

| File | Purpose | Key Classes |
|------|---------|-------------|
| `states.py` | State enum + TRANSITION_MATRIX | `OrchestratorState`, `TransitionGuard` |
| `context.py` | Immutable execution context | `TaskExecutionContext` |
| `panic_system.py` | Error recovery | `PanicSystem`, `PanicEvent` |
| `stagnation_detector.py` | Loop detection | `StagnationDetector` |
| `plan_health.py` | Plan monitoring | `PlanHealthMonitor` |
| `__init__.py` | Module exports | - |

## OrchestratorState Enum

### Active States (7)

| State | Description | Triggers |
|-------|-------------|----------|
| `IDLE` | Awaiting user input (initial state) | Session start, task complete |
| `BRAINSTORMING` | Agents exchange TALK messages | User input received |
| `EXECUTING_TOOL` | Nexus Core executes tool (synchronous) | Agent requests TOOL_USE |
| `VALIDATING_CFL` | **CFL** - Agent validates tool result | Tool execution complete |
| `WAITING_USER` | Task finished, awaiting next input | Agent sends FINISHED status |
| `ERROR` | Recoverable error (use `/reset`) | Parse errors, stagnation |
| `PANIC` | Fatal error (restart required) | Circuit breaker triggered |

### Special State (1)

| State | Description | Limit |
|-------|-------------|-------|
| `EVOLUTION_BRAINSTORM` | Agents debate mutation design | 30 turns max |

### Reserved States (3) - Sprint 9

| State | Description | Status |
|-------|-------------|--------|
| `SWARM_ANALYZING` | Task complexity analysis | **[RESERVED]** |
| `SWARM_NEGOTIATING` | Mode negotiation (max 4 turns) | Bypassed by `process_with_swarm()` |
| `SWARM_EXECUTING` | Execute negotiated mode | Full FSM integration planned |

**Note**: Swarm states exist but are bypassed in V7.6. The Hybrid Swarm Engine operates via `process_with_swarm()` which handles state internally.

## VALIDATING_CFL State (Critical)

The **Cognitive Feedback Loop** (CFL) state is where tool results are validated.

### Purpose
- Cross-validation: The OTHER agent validates the tool result
- Fast timeout: 60s (validation should be quick)
- Prevents invalid tool results from proceeding

### Implementation (orchestration_v7.py:957-1043)

```python
# === STATE: VALIDATING_CFL ===
elif self.state == OrchestratorState.VALIDATING_CFL:
    # CFL timeout (shorter than brainstorming)
    cfl_timeout = getattr(self.config, 'cfl_timeout', 60)

    # Invoke validating agent
    if self.active_agent == "Claude":
        driver = self._get_claude_driver(TaskType.VALIDATION, timeout_override=cfl_timeout)
        response = driver.invoke(context)
    else:
        response = self.gemini_driver.invoke(context)

    # Validation signals (heuristic detection)
    content = message.get("content", "")
    validation_success = (
        "✓" in content or
        "success" in content.lower() or
        "successfully" in content.lower()
    )

    # Three outcomes:
    if task_finished:
        # → IDLE (task complete)
        self._transition_to(OrchestratorState.IDLE)
    elif validation_success:
        # → BRAINSTORMING (continue with agent swap)
        self.active_agent = "Claude" if self.active_agent == "Gemini" else "Gemini"
        self._transition_to(OrchestratorState.BRAINSTORMING)
    else:
        # → BRAINSTORMING (retry with fresh perspective)
        self.active_agent = "Claude" if self.active_agent == "Gemini" else "Gemini"
        self._transition_to(OrchestratorState.BRAINSTORMING)
```

### Validation Signals

| Signal | Detection | Result |
|--------|-----------|--------|
| Task Finished | `status == "FINISHED"` or "task complete" in content | → IDLE |
| Success | "✓" or "success" in content | → BRAINSTORMING (agent swap) |
| Failure | "✗" or "error" in content | → BRAINSTORMING (agent swap, stalemate check) |
| Neutral | No explicit signal | Assumed success |

## TransitionGuard Class

Guards for FSM transitions (states.py:105-140).

```python
class TransitionGuard:
    @staticmethod
    def can_start_brainstorming(user_input: str) -> bool:
        """User input valid for brainstorming"""
        return bool(user_input and user_input.strip())

    @staticmethod
    def can_execute_tool(message: dict) -> bool:
        """Message contains valid tool request"""
        return (
            message.get("action_type") == "TOOL_USE" and
            "tool_use" in message and
            message["tool_use"] is not None
        )

    @staticmethod
    def is_task_finished(message: dict) -> bool:
        """Task marked as finished"""
        return message.get("status") == "FINISHED"

    @staticmethod
    def should_switch_agent(message: dict, current_agent: str) -> bool:
        """Agent requests switch to partner"""
        next_agent = message.get("next_agent")
        return next_agent and next_agent != current_agent

    @staticmethod
    def is_brainstorm_message(message: dict) -> bool:
        """Message is TALK (not action)"""
        return message.get("action_type") in ["TALK", "DELEGATE"]
```

## TaskExecutionContext (Phase 0d)

Immutable context for thread-safe PARALLEL mode execution (context.py:12-104).

```python
@dataclass(frozen=True)
class TaskExecutionContext:
    """Immutable context per task (replaces mutable self.active_agent)"""
    task_id: str
    current_agent: str  # "Gemini" or "Claude"
    iteration: int = 0
    tool_requesting_agent: Optional[str] = None
    validation_agent: Optional[str] = None
    objective: str = ""

    def with_agent(self, agent: str) -> 'TaskExecutionContext':
        """Return new context with changed agent (immutable)"""

    def swap_agent(self) -> 'TaskExecutionContext':
        """Return context with agent swapped"""

    def next_iteration(self) -> 'TaskExecutionContext':
        """Return context with incremented iteration"""
```

### Thread Safety

- **Problem**: `self.active_agent` is mutable global state
- **Solution**: Pass immutable context through call chain
- **Benefit**: Safe for PARALLEL Swarm mode with concurrent agent execution

## Support Classes

### PanicSystem

Manages critical error states (panic_system.py:12-200).

```python
panic = PanicSystem(workspace_path, max_stalemate=5, max_consecutive_errors=3)

# Record error
if panic.record_error("CFL_VALIDATION", str(e)):
    return self._trigger_panic(f"Too many errors")

# Check stalemate
if panic.check_stalemate():
    return self._trigger_panic("Stalemate detected")

# Reset counters
panic.reset_stalemate()
panic.reset_errors()
```

### StagnationDetector

Detects repetitive brainstorming (stagnation_detector.py:17-167).

```python
detector = StagnationDetector(
    similarity_threshold=0.8,  # 80% text similarity
    window_size=3,             # Last 3 messages
    min_matches=2              # 2+ similar pairs = stagnation
)

detector.add_message(message_content)

if detector.is_stagnant():
    # Inject warning to force agent decision
    warning = detector.get_stagnation_message()
```

### PlanHealthMonitor

Monitors strategic plan health (plan_health.py:10-195).

```python
monitor = PlanHealthMonitor()

status = monitor.check_health(strategic_plan)
# Returns: HEALTHY, WARNING, STAGNANT, or ZOMBIE

# ZOMBIE detection: all steps PENDING > 30 turns
```

## State Flows

### Normal Flow
```
IDLE → BRAINSTORMING → EXECUTING_TOOL → VALIDATING_CFL → IDLE
```

### Swarm Flow (via process_with_swarm, bypasses FSM states)
```
IDLE → [HybridSwarmEngine handles internally] → VALIDATING_CFL → IDLE
```

### Evolution Flow
```
IDLE → EVOLUTION_BRAINSTORM (30 turns max) → IDLE
```

### Error Recovery
```
ANY_STATE → ERROR → (/reset) → IDLE
ANY_STATE → PANIC → (restart session) → IDLE
```

## Configuration

| Variable | Default | Purpose |
|----------|---------|---------|
| `MAX_STALEMATE_COUNT` | 5 | Stalemates before panic |
| `CFL_TIMEOUT` | 60 | Validation timeout (seconds) |
| `STAGNATION_SIMILARITY_THRESHOLD` | 0.8 | Text similarity threshold |
| `EVOLUTION_MAX_TURNS` | 30 | Max brainstorm turns |

## Usage Example

```python
from core.fsm import OrchestratorState, TransitionGuard, TaskExecutionContext
from core.fsm import PanicSystem, StagnationDetector

# Initialize
panic = PanicSystem(workspace_path)
detector = StagnationDetector(similarity_threshold=0.8)

# Create immutable context
context = TaskExecutionContext(
    task_id="task_001",
    current_agent="Gemini",
    iteration=0,
    objective="Implement feature X"
)

# State management
current_state = OrchestratorState.IDLE

def transition(new_state: OrchestratorState):
    global current_state
    print(f"[FSM] {current_state.name} → {new_state.name}")
    current_state = new_state

# Use transition guards
if TransitionGuard.can_execute_tool(message):
    transition(OrchestratorState.EXECUTING_TOOL)
```

## Dependencies

### Internal
- `core.config` - Configuration parameters
- `core.logging` - Event logging
- `core.synapse` - Message protocol

### External
- `enum` - State enumeration
- `difflib` - Text similarity (stagnation)
- `dataclasses` - TaskExecutionContext
- `threading.RLock` - Thread safety

## See Also

- [Core README](../README.md) - Architecture overview
- [Swarm Module](../swarm/README.md) - Hybrid Swarm Engine
- [Synapse Module](../synapse/README.md) - Message schemas (LightMessageV7/HeavyMessageV7)
- [Drivers Module](../drivers/README.md) - Agent invocation
