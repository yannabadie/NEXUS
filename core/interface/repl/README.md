# REPL Package

V10.2 modular split of `repl.py` (74.3KB, 1743 lines).

## Structure

```
repl/
├── __init__.py           # Re-exports InteractiveNexusV7
├── repl_v10.py           # Wrapper module
├── workspace_helpers.py  # /workspace command helpers (120 lines)
├── telemetry_helpers.py  # /telemetry command helpers (140 lines)
├── budget_helpers.py     # /budget command helpers (130 lines)
├── evolution_helpers.py  # /evolve command helpers (130 lines)
└── README.md             # This file
```

## Module Contents

| Module | Functions |
|--------|-----------|
| `workspace_helpers` | `list_workspaces`, `get_workspace_info`, `validate_workspace_name` |
| `telemetry_helpers` | `format_telemetry_report`, `export_telemetry_csv`, `calculate_cost_trend` |
| `budget_helpers` | `format_budget_status`, `validate_credit_amount`, `estimate_remaining_tasks` |
| `evolution_helpers` | `format_evolution_status`, `format_fitness_scores`, `should_auto_evolve` |

## Usage

```python
# Main class import
from core.interface.repl import InteractiveNexusV7

# Helper functions
from core.interface.repl.workspace_helpers import list_workspaces
from core.interface.repl.budget_helpers import format_budget_status
```
