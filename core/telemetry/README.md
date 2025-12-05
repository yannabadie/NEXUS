# Telemetry Module - NEXUS V7.7 "HIVE MIND"

System observability, metrics collection, and budget management for NEXUS operations.

## Role in Architecture

The Telemetry module provides **operational observability** at the system level:
- **API Calls**: Token usage, latency, model distribution
- **Swarm Activity**: Modes used, task completion rates
- **Tool Executions**: Duration, success/failure rates
- **Errors**: Exception types, context
- **Evolution**: Generation counts, mutation success rates
- **Budget Tracking**: API costs, daily limits, warnings (Phase 14d)
- **Telemetry Export**: CSV export for external analysis (Phase 13c)

Unlike `core.logging` (technical events) and `core.memory` (functional outcomes), Telemetry focuses on **aggregate metrics** for system health monitoring.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    TELEMETRY SYSTEM                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   ┌────────────────────────────────────────────────────────┐    │
│   │              TelemetryCollector                        │    │
│   │                                                        │    │
│   │  record_api_call()     record_swarm_task()             │    │
│   │  record_tool_execution() record_error()                │    │
│   │  record_evolution()    get_session_summary()           │    │
│   └────────────────────────────────────────────────────────┘    │
│                              │                                   │
│                              ▼                                   │
│   ┌────────────────────────────────────────────────────────┐    │
│   │               workspace/telemetry.jsonl                 │    │
│   │   Event 1 → Event 2 → Event 3 → ... → Session Summary  │    │
│   └────────────────────────────────────────────────────────┘    │
│                                                                 │
│   MetricType: API_CALL │ SWARM_TASK │ TOOL_EXECUTION │ ERROR   │
│               SESSION  │ EVOLUTION                              │
└─────────────────────────────────────────────────────────────────┘
```

## Phase Status (V7.7)

| Phase | Feature | Status |
|-------|---------|--------|
| **Phase 13c** | Telemetry Export (`/telemetry export`) | ✅ COMPLETE |
| **Phase 14d** | Budget Cap (BudgetTracker) | ✅ COMPLETE |
| **Phase 16a** | `/budget` command | ✅ COMPLETE |

## Files

| File | Purpose | Key Classes |
|------|---------|-------------|
| `metrics.py` | Main metrics collection | `TelemetryCollector`, `MetricType` |
| `budget_tracker.py` | API cost tracking | `BudgetTracker`, `BudgetState` |
| `exporter.py` | CSV export & reports | `TelemetryExporter`, `TelemetryEvent` |
| `__init__.py` | Module exports | `get_telemetry()`, `BudgetTracker`, `TelemetryExporter` |

## Key Classes

### TelemetryCollector (metrics.py:75-294)

Thread-safe metrics collection with JSONL persistence.

```python
from core.telemetry import get_telemetry

telemetry = get_telemetry(config)

# 1. Record API call
telemetry.record_api_call(
    provider="gemini",
    model="gemini-3-pro-preview",
    tokens_in=1500,
    tokens_out=500,
    latency_seconds=0.8,
    success=True,
    task_type="brainstorm"
)

# 2. Record Swarm task
telemetry.record_swarm_task(
    mode="PING_PONG",
    rounds=3,
    duration_seconds=12.5,
    success=True,
    agents_used=["gemini", "claude"],
    negotiation_turns=2
)

# 3. Record tool execution
telemetry.record_tool_execution(
    tool_name="read",
    duration_seconds=0.05,
    success=True
)

# 4. Record error
telemetry.record_error(
    error_type="ParseError",
    message="Invalid JSON response",
    context={"agent": "gemini", "iteration": 5}
)

# 5. Get session summary
summary = telemetry.get_session_summary()
print(f"API Calls: {summary.total_api_calls}")
print(f"Tokens: {summary.total_tokens}")
```

### MetricType Enum (metrics.py:26-33)

```python
class MetricType(Enum):
    API_CALL = "api_call"           # Provider calls
    SWARM_TASK = "swarm_task"       # Swarm executions
    TOOL_EXECUTION = "tool_execution"  # Tool runs
    ERROR = "error"                 # Exceptions
    SESSION = "session"             # Session summary
    EVOLUTION = "evolution"         # Evolution cycles
```

### Dataclasses

#### APICallMetric (metrics.py:36-48)

```python
@dataclass
class APICallMetric:
    timestamp: str
    provider: str       # "gemini" or "claude"
    model: str          # "gemini-3-pro-preview", "claude-opus-4-5-..."
    tokens_in: int
    tokens_out: int
    latency_seconds: float
    success: bool
    task_type: Optional[str]  # "brainstorm", "tool", "validation"
    error: Optional[str]
```

#### SwarmTaskMetric (metrics.py:50-60)

```python
@dataclass
class SwarmTaskMetric:
    timestamp: str
    mode: str           # "PARALLEL", "PING_PONG", etc.
    rounds: int
    duration_seconds: float
    success: bool
    agents_used: List[str]
    negotiation_turns: int
```

#### SessionMetric (metrics.py:62-73)

```python
@dataclass
class SessionMetric:
    session_id: str
    start_time: str
    total_api_calls: int
    total_tokens: int
    total_errors: int
    swarm_tasks: int
    tool_executions: int
    duration_seconds: float
```

## Data Storage

All metrics stored in `workspace/telemetry.jsonl`:

### JSONL Event Format

```json
{
  "type": "api_call",
  "session_id": "20251204_103022",
  "timestamp": "2025-12-04T10:30:22.123456Z",
  "data": {
    "provider": "gemini",
    "model": "gemini-3-pro-preview",
    "tokens_in": 1500,
    "tokens_out": 500,
    "latency_seconds": 0.8,
    "success": true,
    "task_type": "brainstorm"
  }
}
```

### Session Summary Entry

```json
{
  "type": "session",
  "session_id": "20251204_103022",
  "timestamp": "2025-12-04T11:45:00.000000Z",
  "data": {
    "session_id": "20251204_103022",
    "start_time": "2025-12-04T10:30:22",
    "total_api_calls": 45,
    "total_tokens": 125000,
    "total_errors": 2,
    "swarm_tasks": 8,
    "tool_executions": 23,
    "duration_seconds": 4478.0
  }
}
```

## Thread Safety

TelemetryCollector uses `threading.Lock` for thread-safe writes (metrics.py:100, 125):

```python
def _write_event(self, event_type: MetricType, data: Dict[str, Any]):
    with self._lock:  # Thread-safe write
        with open(self.output_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(event, ensure_ascii=False) + '\n')
```

## Integration Points

### Orchestrator Integration

```python
# In orchestration_v7.py
from core.telemetry import get_telemetry

class OrchestratorV7:
    def __init__(self):
        self.telemetry = get_telemetry(self.config)

    def _invoke_agent(self, agent, task):
        start = time.time()
        result = agent.invoke(task)
        self.telemetry.record_api_call(
            provider=agent.name,
            model=agent.model,
            latency_seconds=time.time() - start,
            success=result.success
        )
```

### Swarm Integration

```python
# In hybrid_swarm_engine.py
telemetry.record_swarm_task(
    mode=selected_mode.name,
    rounds=execution_result.rounds,
    duration_seconds=execution_result.duration,
    success=execution_result.success,
    agents_used=[a.id for a in participants]
)
```

### Export Commands (Phase 13c)

```bash
nexus> /telemetry           # Show report (last 7 days)
nexus> /telemetry status    # Detailed stats
nexus> /telemetry export    # Export to CSV (all time)
nexus> /telemetry export 7  # Export last 7 days
```

### BudgetTracker (budget_tracker.py) - Phase 14d

Thread-safe API cost tracking with daily limits and warnings.

```python
from core.telemetry import BudgetTracker

tracker = BudgetTracker(workspace_path=Path("workspace"))

# Record API cost
tracker.record_cost(
    provider="claude",
    model="claude-opus-4-5",
    tokens_in=1000,
    tokens_out=500
)

# Get budget status
stats = tracker.get_stats()
# {'spent_today_usd': 0.05, 'limit_usd': 50.0, 'remaining_usd': 49.95, ...}

# Warning levels
warning = tracker.get_warning_level()
# None (< 80%), "warning" (80-90%), "critical" (> 90%)

# Emergency operations
tracker.add_credit(25.0)   # Add $25 to limit
tracker.reset_daily()      # Reset counters
```

### Budget Command (Phase 16a)

```bash
nexus> /budget              # Show status with progress bar
nexus> /budget reset        # Reset daily counter (with confirmation)
nexus> /budget add 10       # Add $10 emergency credit
nexus> /budget history      # Show recent API calls (24h)
```

**Budget Display Example**:
```
╔══════════════════════════════════════════════════════════════╗
║                    💰 BUDGET STATUS                          ║
╚══════════════════════════════════════════════════════════════╝

  [████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░] 25.0%

  💸 Spent Today:    $12.5000
  📊 Daily Limit:    $50.00
  💰 Remaining:      $37.5000

  📞 API Calls:      45
  📅 Reset Date:     2025-12-05
```

## Configuration

```bash
# In config or .env
TELEMETRY_ENABLED=True      # Default: True
TELEMETRY_FILE=workspace/telemetry.jsonl  # Default path

# Budget settings
DAILY_BUDGET_LIMIT=50.0     # Default: $50/day
BUDGET_WARNING_THRESHOLD=0.80   # 80% = warning
BUDGET_CRITICAL_THRESHOLD=0.90  # 90% = critical
```

## Singleton Access

```python
from core.telemetry import get_telemetry

# First call creates instance
telemetry = get_telemetry(config)

# Subsequent calls return same instance
telemetry = get_telemetry()  # Same collector
```

## Difference from Other Modules

| Aspect | Logging (core.logging) | Memory (core.memory) | Telemetry (core.telemetry) |
|--------|------------------------|----------------------|---------------------------|
| **Tracks** | Technical events | Functional outcomes | Aggregate metrics |
| **Granularity** | Per-event | Per-task | Per-session |
| **Purpose** | Debugging | Learning | Monitoring |
| **Persistence** | Log files (rotated) | JSONL (permanent) | JSONL (permanent) |
| **Used by** | Developers | Mode selection | Operations |

## Future Vision (V8)

- **OTLP Export**: OpenTelemetry protocol integration
- **Langfuse Integration**: LLM-specific observability
- **Dashboards**: Real-time metrics visualization
- **Alerting**: Threshold-based notifications

## See Also

- [Interface Module](../interface/README.md) - `/budget` and `/telemetry` commands
- [Logging Module](../logging/README.md) - Technical event logging
- [Memory Module](../memory/README.md) - Functional outcome tracking
- [Swarm Module](../swarm/README.md) - Swarm task metrics source
