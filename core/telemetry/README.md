# Telemetry Module

System observability and metrics collection.

## Overview

Collects operational data to monitor NEXUS health and performance.

## Metrics Tracked

- **API Calls**: Token usage, latency, model distribution.
- **Swarm Activity**: Modes used, task completion rates.
- **Errors**: Exception types, stack traces.
- **Evolution**: Generation counts, mutation success rates.

## Files

| File | Purpose |
|------|---------|
| `metrics.py` | `TelemetryCollector` implementation |
| `__init__.py` | Exports |

## Storage

Metrics are stored in `workspace/telemetry.jsonl`. This format is log-rotation friendly and easy to parse.

## Usage

```python
from core.telemetry import TelemetryCollector

telemetry = TelemetryCollector(config)
telemetry.track_event(
    category="swarm",
    action="task_complete",
    details={"mode": "PARALLEL", "duration": 12.5}
)
```
