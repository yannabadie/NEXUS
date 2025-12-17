# FSM Handlers Package

V10.2 modular split of `fsm_handlers.py` (74.7KB, 1711 lines).

## Structure

```
handlers/
├── __init__.py           # Re-exports FSMHandlers
├── base.py               # FSMHandlersMixin - shared helpers (110 lines)
├── fsm_handlers_v10.py   # Thin wrapper (imports from original)
├── idle_helpers.py       # Idle state helpers (110 lines)
├── brainstorm_helpers.py # Brainstorm state helpers (120 lines)
├── swarm_helpers.py      # Swarm state helpers (100 lines)
├── hive_mind_helpers.py  # Hive Mind routing helpers (100 lines)
└── README.md             # This file
```

## Module Contents

| Module | Functions |
|--------|-----------|
| `idle_helpers.py` | `get_trivial_response`, `validate_user_input`, `log_task_started` |
| `brainstorm_helpers.py` | `extract_tool_request`, `should_validate_tool`, `format_tool_result` |
| `swarm_helpers.py` | `format_swarm_result`, `extract_swarm_metrics`, `should_use_swarm` |
| `hive_mind_helpers.py` | `should_use_hive_mind`, `format_hive_mind_result` |

## Usage

```python
# Main class import (unchanged)
from core.orchestration.handlers import FSMHandlers

# Helper functions (pure, testable)
from core.orchestration.handlers.idle_helpers import get_trivial_response
from core.orchestration.handlers.swarm_helpers import should_use_swarm
```

## Progress

| Phase | Status |
|-------|--------|
| Phase 1: Foundation | ✅ Complete |
| Phase 2: Helper extraction | ✅ Complete |
| Phase 3: Wire to main class | ⏳ Pending |
