# Logging Module

Structured logging for NEXUS V7.5.

## Overview

Provides event-based logging to tracking system behavior and errors.

## Log Files

All logs are stored in `workspace/logs/`:
- `events_YYYYMMDD.jsonl`: Structured event stream.
- `errors_YYYYMMDD.log`: Human-readable error traces.
- `debug_YYYYMMDD.log`: Detailed debugging info.

## Integration with Auto-Memory

While `core.logging` tracks *technical* events, `core.memory.AutoMemory` tracks *functional* outcomes (success/failure of tasks). The logger captures the low-level execution details that feed into high-level memory.