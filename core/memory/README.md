# Memory Module (Auto-Memory)

The "Cortex" of NEXUS V7.5 HIVE MIND.

## Overview

The Memory module implements **Auto-Memory**, a system that allows NEXUS to learn from its own operational history. Unlike session memory (RAM), Auto-Memory persists across restarts and guides decision-making.

## Core Functions

1.  **Record Success/Failure**: Logs every task outcome with context (mode, agent, duration).
2.  **Pattern Recognition**: Aggregates statistics to identify which Swarm modes work best for specific task types.
3.  **Guidance**: Provides `get_recommendation()` to the Orchestrator before task execution.

## Architecture

```
Orchestrator -> AutoMemory -> [Record Success] -> successes.jsonl
             -> AutoMemory -> [Get Recommendation] -> "Use LEAD_SUPPORT"
```

## Files

| File | Purpose | Key Classes |
|------|---------|-------------|
| `auto_memory.py` | Main logic | `AutoMemory`, `MemoryEntry` |
| `__init__.py` | Singleton accessor | `get_auto_memory()` |

## Data Storage

All data is stored in `workspace/memory/`:
- `successes.jsonl`: Log of successful tasks.
- `failures.jsonl`: Log of failed tasks (errors, timeouts).
- `fitness_scores.json`: Aggregated performance stats for agents.

## Usage

```python
from core.memory import get_auto_memory

memory = get_auto_memory()

# 1. Get advice
rec = memory.get_recommendation(task_type="CODING")
print(f"Suggested Mode: {rec['suggested_mode']}")

# 2. Learn
memory.record_success(
    task_type="CODING",
    task_description="Refactor auth",
    swarm_mode="LEAD_SUPPORT",
    lead_agent="claude",
    duration_seconds=45.0
)
```

## Future Vision (V8)

- **Vector Search**: Index `task_description` for semantic retrieval ("How did I fix this error last time?").
- **GraphRAG**: Link memories to code symbols.
