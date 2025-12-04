# Memory Module - NEXUS V7.6 "HIVE MIND"

The "Cortex" of NEXUS - Learning from operational history (Phase 10).

## Role in Architecture

The Memory module implements **Auto-Memory**, a system that allows NEXUS to learn from its own operational history:
- **Record** success/failure patterns with context
- **Recognize** which Swarm modes work best for task types
- **Recommend** optimal configurations based on history
- **Avoid** repeating failed approaches

Unlike session memory (RAM via Blackboard), Auto-Memory **persists across restarts**.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    AUTO-MEMORY SYSTEM                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   ┌────────────────────────────────────────────────────────┐    │
│   │                    AutoMemory                          │    │
│   │                                                        │    │
│   │  RECORD              ANALYZE              RECOMMEND    │    │
│   │  ┌──────────┐       ┌──────────┐        ┌──────────┐  │    │
│   │  │ Success  │       │ Patterns │        │ Best Mode│  │    │
│   │  │ Failure  │  ───▶ │ Fitness  │  ───▶  │ Best Lead│  │    │
│   │  │ Context  │       │ Avoids   │        │ Confidence│ │    │
│   │  └──────────┘       └──────────┘        └──────────┘  │    │
│   └────────────────────────────────────────────────────────┘    │
│                              │                                   │
│                              ▼                                   │
│   ┌────────────────────────────────────────────────────────┐    │
│   │               workspace/memory/                         │    │
│   │  successes.jsonl │ failures.jsonl │ fitness_scores.json │    │
│   └────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

## Phase Status (V7.6)

| Phase | Feature | Status |
|-------|---------|--------|
| **Phase 10a** | Success Memory | ✅ COMPLETE |
| **Phase 10b** | Memory-Augmented Mode Selection | ✅ COMPLETE |

## Files

| File | Purpose | Key Classes |
|------|---------|-------------|
| `auto_memory.py` | Main implementation | `AutoMemory`, `MemoryEntry` |
| `success_memory.py` | Success pattern storage | `SuccessMemory` |
| `__init__.py` | Module exports | `get_auto_memory()` |

## Key Classes

### AutoMemory (auto_memory.py:41-330)

Main memory system with recording, analysis, and recommendation.

```python
from core.memory import get_auto_memory

memory = get_auto_memory()

# 1. Record success
memory.record_success(
    task_type="code_review",
    task_description="Review auth module security",
    swarm_mode="PING_PONG",
    lead_agent="claude",
    duration_seconds=45.0,
    score=0.9  # Quality score 0-1
)

# 2. Record failure
memory.record_failure(
    task_type="security_audit",
    task_description="Full codebase audit",
    swarm_mode="PARALLEL",
    lead_agent="gemini",
    duration_seconds=120.0,
    reason="timeout - task too complex for parallel"
)

# 3. Get recommendation
rec = memory.get_recommendation(task_type="code_review")
# Returns:
# {
#     "suggested_mode": "PING_PONG",
#     "suggested_lead": "claude",
#     "modes_to_avoid": ["PARALLEL"],
#     "confidence": 0.8,
#     "based_on_samples": 12
# }

# 4. Check if mode should be avoided
should_avoid = memory.should_avoid("security_audit", "PARALLEL")  # True
```

### MemoryEntry (auto_memory.py:27-38)

Dataclass for a single memory record.

```python
@dataclass
class MemoryEntry:
    timestamp: str
    task_type: str
    task_description: str
    swarm_mode: str
    lead_agent: str
    duration_seconds: float
    outcome: str  # "success" or "failure"
    reason: Optional[str] = None  # For failures
    score: Optional[float] = None  # Quality score 0-1
```

## Data Storage

All data persisted in `workspace/memory/`:

| File | Format | Content |
|------|--------|---------|
| `successes.jsonl` | JSONL | Successful task patterns |
| `failures.jsonl` | JSONL | Failed approaches (anti-patterns) |
| `fitness_scores.json` | JSON | Agent fitness by task type |

### Success Entry Example

```json
{
  "timestamp": "2025-12-04T10:30:22",
  "task_type": "code_review",
  "task_description": "Review auth module security",
  "swarm_mode": "PING_PONG",
  "lead_agent": "claude",
  "duration_seconds": 45.0,
  "outcome": "success",
  "score": 0.9
}
```

### Fitness Scores Structure

```json
{
  "claude": {
    "tasks": {
      "code_review": {"scores": [0.9, 0.85, 0.95], "avg": 0.9},
      "debugging": {"scores": [0.8, 0.9], "avg": 0.85}
    },
    "overall": 0.875
  },
  "gemini": {
    "tasks": {
      "research": {"scores": [0.95, 0.9], "avg": 0.925},
      "code_review": {"scores": [0.7, 0.8], "avg": 0.75}
    },
    "overall": 0.84
  }
}
```

## Recommendation Algorithm

### Mode Suggestion (auto_memory.py:192-220)

```python
# For each mode used for this task type:
# 1. Sum weighted scores
# 2. Calculate average per mode
# 3. Return mode with highest average

mode_scores = defaultdict(float)
for entry in successes:
    mode = entry["swarm_mode"]
    score = entry["score"]
    mode_scores[mode] += score
# Return max(mode_avg)
```

### Avoidance Detection (auto_memory.py:249-265)

```python
# Mode is avoided if:
# - At least 3 samples
# - Failure rate > 50%

failure_rate = failures / (failures + successes)
return failure_rate > 0.5 and total >= 3
```

### Confidence Calculation

```python
# Confidence scales with sample count
# 10+ samples = full confidence
confidence = min(1.0, total_samples / 10)
```

## Integration with Swarm

The Memory module is integrated into ModeSelector (Phase 10b):

```python
# In mode_selector.py
recommendation = memory.get_recommendation(task_type)

if recommendation["confidence"] > 0.5:
    # Use memory-suggested mode
    selected_mode = recommendation["suggested_mode"]

    # Avoid known bad modes
    for mode in recommendation["modes_to_avoid"]:
        mode_scores[mode] *= 0.5  # Penalize
```

## Usage Example

### Full Workflow

```python
from core.memory import get_auto_memory
from core.swarm import HybridSwarmEngine

memory = get_auto_memory()

# Before task: Get recommendation
rec = memory.get_recommendation(task_type="debugging")
print(f"Suggested mode: {rec['suggested_mode']}")
print(f"Confidence: {rec['confidence']}")

# Execute task
result = engine.process_task(
    "Fix the auth bug",
    forced_mode=rec["suggested_mode"] if rec["confidence"] > 0.7 else None
)

# After task: Record outcome
if result.success:
    memory.record_success(
        task_type="debugging",
        task_description="Fix the auth bug",
        swarm_mode=result.mode,
        lead_agent=result.lead_agent,
        duration_seconds=result.duration
    )
else:
    memory.record_failure(
        task_type="debugging",
        task_description="Fix the auth bug",
        swarm_mode=result.mode,
        lead_agent=result.lead_agent,
        duration_seconds=result.duration,
        reason=result.error_message
    )
```

### Get Statistics

```python
stats = memory.get_stats()
# {
#     "total_successes": 45,
#     "total_failures": 12,
#     "success_rate": 0.789,
#     "task_types_tracked": ["code_review", "debugging", "research"],
#     "memory_files": {...}
# }
```

## Difference from Logging

| Aspect | Logging (core.logging) | Memory (core.memory) |
|--------|------------------------|----------------------|
| **Tracks** | Technical events | Functional outcomes |
| **Purpose** | Debugging/Observability | Learning/Optimization |
| **Persistence** | Log files (rotated) | JSONL (permanent) |
| **Used by** | Developers | Mode selection |

## Configuration

```bash
# Memory is always enabled (no config flag)
# Files stored in workspace/memory/
```

## Future Vision (V8)

- **Vector Search**: Semantic retrieval ("How did I fix this error before?")
- **GraphRAG**: Link memories to code symbols
- **Cross-project Learning**: Share patterns between NEXUS instances

## See Also

- [Swarm Module](../swarm/README.md) - Uses memory for mode selection
- [Logging Module](../logging/README.md) - Technical event tracking
- [Telemetry Module](../telemetry/README.md) - Metrics export
