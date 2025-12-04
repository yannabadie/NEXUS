# Interface Module

User interaction layer for NEXUS V7.

## Overview

The Interface module provides:
- **REPL**: Interactive command loop
- **Slash commands**: System commands (`/status`, `/evolve`, etc.)
- **Mode management**: Normal, Chat, Evolution modes

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         USER                                │
│                           │                                 │
│                           ▼                                 │
│   ┌─────────────────────────────────────────────────────┐   │
│   │                      REPL                            │   │
│   │  ┌──────────────┐   ┌──────────────────────────┐    │   │
│   │  │ Input Parser │──▶│   Command Router          │    │   │
│   │  └──────────────┘   │  • Slash commands         │    │   │
│   │                     │  • Exit commands          │    │   │
│   │                     │  • Agent input            │    │   │
│   │                     └──────────────────────────┘    │   │
│   │                                │                     │   │
│   │         ┌──────────────────────┼──────────────┐      │   │
│   │         ▼                      ▼              ▼      │   │
│   │   ┌──────────┐          ┌──────────┐   ┌──────────┐  │   │
│   │   │ Commands │          │Orchestrat│   │  Console │  │   │
│   │   │ Handler  │          │   or     │   │  Output  │  │   │
│   │   └──────────┘          └──────────┘   └──────────┘  │   │
│   └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## Files

| File | Purpose | Key Classes |
|------|---------|-------------|
| `repl.py` | Main REPL loop | `REPL`, `run_repl()` |
| `commands.py` | Slash commands | `SLASH_COMMANDS`, `parse_command()` |
| `__init__.py` | Module exports | - |

## Key Functions

### REPL

Main interaction loop.

```python
from core.interface import run_repl
from core.config import Config

config = Config()
run_repl(config)  # Starts interactive session
```

### Slash Commands

Available commands:

| Command | Description |
|---------|-------------|
| `/help` | Show help message |
| `/status` | Show orchestrator state |
| `/doctor` | Run system diagnostics |
| `/reset` | Reset to IDLE state |
| `/clear` | Clear terminal |
| `/mode <name>` | Change mode |
| `/chat` | Enter chat-only mode |
| `/evolve [count]` | Create child generations |
| `/evolve-status` | Show evolution stats |
| `/pool-stats` | Show DyLAN metrics |
| `/review` | Review pending children |
| `/specialize <mission>` | Create specialized spinoff |
| `exit` | Exit NEXUS |

### Command Parsing

```python
from core.interface.commands import (
    is_slash_command,
    is_exit_command,
    parse_command,
    get_help_message
)

user_input = "/evolve 5"

if is_slash_command(user_input):
    cmd, args = parse_command(user_input)
    # cmd = "/evolve", args = ["5"]

if is_exit_command("quit"):
    # True - exits the REPL
    pass

help_text = get_help_message()
# "Available commands:\n  /help..."
```

## REPL Flow

```
1. Show banner and help
2. Loop:
   a. Read user input
   b. Check if slash command → execute
   c. Check if exit → break
   d. Pass to orchestrator
   e. Display response
   f. Continue until FINISHED or error
3. Save state and exit
```

## Modes

### Normal Mode
- Default operation
- Full agent collaboration
- Tool execution enabled

### Chat Mode (`/chat`)
- Conversation only
- No tool execution
- Quick Q&A

### Evolution Mode (`/evolve`)
- Child creation enabled
- GENERATION_ACTIVE writes permitted
- Extended brainstorming

## Evolution Commands

### `/evolve [count]`

Create and evaluate child generations.

```bash
nexus> /evolve 3
Creating 3 children...
Child 1: NEXUS_V7.5_CHILD_001 (Fitness: 0.78)
Child 2: NEXUS_V7.5_CHILD_002 (Fitness: 0.81)
Child 3: NEXUS_V7.5_CHILD_003 (Fitness: 0.79)

Winner: CHILD_002 (+3.8% improvement)
Review pending at PENDING_REVIEW.md
```

### `/evolve-status`

Show evolution statistics.

```bash
nexus> /evolve-status
Generation: 7.0
Stagnation Counter: 0/3
Last Evolution: 2025-11-26 14:30
Children Created: 12
Children Promoted: 3
```

### `/review`

Review pending children.

```bash
nexus> /review
=== PENDING REVIEW ===
Child: NEXUS_V7.0_CHILD_002
Fitness Score: 0.81 (+3.8%)
Changes: 5 files, 120 lines

[a]pprove / [r]eject / [d]etails?
```

## Configuration

Environment variables:
```bash
UI_VERBOSE=True      # Detailed output
LOG_LEVEL=DEBUG      # Logging verbosity
```

## Usage Example

```python
from core.interface import run_repl
from core.interface.commands import (
    is_slash_command,
    parse_command,
    SLASH_COMMANDS
)
from core.config import Config

# Check available commands
for cmd, desc in SLASH_COMMANDS.items():
    print(f"{cmd}: {desc}")

# Run REPL
config = Config()
run_repl(config)
```

## Dependencies

### Internal
- `core.orchestration_v7` - FSM orchestrator
- `core.config` - Configuration
- `core.ui` - Console output
- `core.evolution` - For `/evolve`

### External
- Standard library only

## See Also

- [Core README](../README.md) - Architecture overview
- [Evolution Module](../evolution/README.md) - Evolution commands
- [UI Module](../ui/README.md) - Console display
