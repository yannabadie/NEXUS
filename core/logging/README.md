# Logging Module

Structured logging for NEXUS V7.

## Overview

Provides structured event logging with:
- **JSON Lines format** for events
- **Error logging** with tracebacks
- **Event correlation** for debugging

## Files

| File | Purpose | Key Classes |
|------|---------|-------------|
| `logger_v7.py` | Logging implementation | `NexusLogger` |
| `__init__.py` | Module exports | - |

## Key Class

### NexusLogger

```python
from core.logging import NexusLogger
from pathlib import Path

logger = NexusLogger(workspace_path=Path("./workspace"))

# Log event
logger.log_event(
    event_type="AGENT_INVOCATION",
    agent="Gemini",
    action="TALK",
    details={"content": "Analysis..."}
)

# Log error
logger.log_error(
    error_type="PARSE_ERROR",
    message="Invalid JSON",
    traceback="..."
)
```

## Log Files

```
workspace/logs/
├── events_20251126.jsonl    # Daily events
├── errors_20251126.log      # Error log
└── debug_20251126.log       # Debug (if LOG_LEVEL=DEBUG)
```

## Event Format

```json
{
  "timestamp": "2025-11-26T14:30:00",
  "event_type": "AGENT_INVOCATION",
  "agent": "Gemini",
  "action": "TALK",
  "details": {"content": "..."},
  "correlation_id": "abc123"
}
```

## Configuration

```bash
LOG_LEVEL=DEBUG    # DEBUG, INFO, WARNING, ERROR
UI_VERBOSE=True    # Show detailed output
```

## See Also

- [Core README](../README.md) - Architecture overview
