# FSM Handlers Package

V10.2 modular split of `fsm_handlers.py` (74.7KB, 1711 lines).

## Structure

```
handlers/
├── __init__.py         # Re-exports FSMHandlers
├── base.py             # FSMHandlersMixin - shared helpers
├── fsm_handlers_v10.py # Thin wrapper (imports from original)
└── README.md           # This file
```

## Migration Status

| Handler Group | Status |
|---------------|--------|
| Idle/User | 🔄 Planned |
| Brainstorming | 🔄 Planned |
| Swarm | 🔄 Planned |
| Evolution | 🔄 Planned |
| HiveMind | 🔄 Planned |

## Usage

```python
# New modular import (works now, will improve later)
from core.orchestration.handlers import FSMHandlers

# Original import (still works)
from core.orchestration.fsm_handlers import FSMHandlers
```

## Next Steps

1. Extract handler methods into individual mixin files
2. Update fsm_handlers_v10.py to compose from mixins
3. Deprecate direct import from fsm_handlers.py
