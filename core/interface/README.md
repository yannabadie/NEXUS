# Module: Interface - NEXUS V9.0 User Interaction Layer

**Version**: 9.0 (TRUE HIVE MIND)
**Last Updated**: 2025-12-11
**Phase 16**: Developer Experience (DX) - COMPLETE

---

## Role Architectural

User interaction layer for NEXUS V9.0. Provides REPL, categorized slash commands, interactive tutorial, budget management, and Strategy Pattern command system.

---

## Alignement ROADMAP V7.5+ / V9.0

| Phase ROADMAP | Impact sur ce module |
|---------------|---------------------|
| **Phase 13c** | Telemetry commands (`/telemetry`, `/telemetry export`) |
| **Phase 10d** | Workspace commands (`/workspace new`, `/workspace switch`) |
| **Phase 16a** | `/budget` command with subcommands (COMPLETE) |
| **Phase 16b** | Categorized help with 5 categories (COMPLETE) |
| **Phase 16c** | Interactive tutorial `/tutorial` + `/quickstart` (COMPLETE) |
| **V9.0** | CommandRegistry singleton + Strategy Pattern commands |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                           USER                                   │
│                             │                                    │
│                             ▼                                    │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │                        REPL                              │   │
│   │  ┌──────────────┐   ┌────────────────────────────────┐  │   │
│   │  │ Input Parser │──▶│      Command Router            │  │   │
│   │  └──────────────┘   │  • COMMAND_CATEGORIES (5)      │  │   │
│   │                     │  • Slash commands (25+)        │  │   │
│   │                     │  • Exit commands               │  │   │
│   │                     └────────────────────────────────┘  │   │
│   │                                │                         │   │
│   │    ┌───────────┬───────────────┼───────────┬──────────┐ │   │
│   │    ▼           ▼               ▼           ▼          ▼ │   │
│   │ ┌───────┐ ┌─────────┐ ┌────────────┐ ┌────────┐ ┌─────┐│   │
│   │ │Budget │ │Tutorial │ │Orchestrator│ │Telemetry│ │Swarm││   │
│   │ │Handler│ │ Runner  │ │            │ │ Export │ │Tasks││   │
│   │ └───────┘ └─────────┘ └────────────┘ └────────┘ └─────┘│   │
│   └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Components

### 1. Command Categories (`commands.py`) - Phase 16b

**Categorized command structure** replacing flat SLASH_COMMANDS.

```python
from core.interface.commands import COMMAND_CATEGORIES, get_help_message

# 5 categories
COMMAND_CATEGORIES = {
    "🐝 Collaboration": {"/swarm", "/swarm-status", "/pool-stats", ...},
    "🧬 Evolution": {"/evolve", "/spawn", "/agents", "/specialize", ...},
    "📊 Monitoring": {"/budget", "/telemetry", "/status", ...},
    "📁 Workspace": {"/workspace", "/bootstrap", ...},
    "⚙️ System": {"/help", "/tutorial", "/chat", "/doctor", ...},
}

# Get formatted help
help_text = get_help_message()  # ASCII-art categorized help
```

**Key Functions**:

| Function | Purpose |
|----------|---------|
| `get_help_message()` | Generate categorized ASCII help |
| `get_category_for_command(cmd)` | Find category for command |
| `is_slash_command(input)` | Check if input starts with `/` |
| `is_exit_command(input)` | Check for exit/quit/q |
| `parse_command(input)` | Split into (command, args) |

### 2. Interactive Tutorial (`tutorial.py`) - Phase 16c

**5-step interactive guide** for new users.

```python
from core.interface.tutorial import InteractiveTutorial, TUTORIAL_STEPS

# Run full tutorial
tutorial = InteractiveTutorial()
completed = tutorial.run(print_fn=console.print)

# Quick start (non-interactive)
quickstart = tutorial.get_quick_start()
```

**Tutorial Steps**:

| Step | Title | Suggested Command |
|------|-------|-------------------|
| 1 | Bienvenue HIVE MIND | - |
| 2 | Mode Swarm | `/swarm "Analyse ce projet"` |
| 3 | Budget & Télémétrie | `/budget` |
| 4 | Workspace | `/workspace` |
| 5 | Evolution | `/evolve-status` |

**TutorialStep Dataclass**:
```python
@dataclass
class TutorialStep:
    title: str
    explanation: str
    suggested_command: Optional[str] = None
    tip: Optional[str] = None
```

### 3. REPL (`repl.py`)

**Main interaction loop** with Phase 16 handlers.

**New Phase 16 Methods**:

| Method | Command | Description |
|--------|---------|-------------|
| `handle_budget_command(args)` | `/budget` | Budget management |
| `_budget_show_status(tracker)` | `/budget` | Display progress bar |
| `_budget_reset(tracker)` | `/budget reset` | Reset with confirmation |
| `_budget_add_credit(tracker, amount)` | `/budget add <n>` | Add emergency credit |
| `_budget_show_history()` | `/budget history` | Show recent API calls |
| `run_tutorial()` | `/tutorial` | Launch interactive tutorial |
| `show_quickstart()` | `/quickstart` | Show quick start guide |
| `toggle_chat_mode()` | `/chat` | Toggle chat-only mode |

---

## Commands Reference

### 🐝 Collaboration

| Command | Description |
|---------|-------------|
| `/swarm <task>` | Route task through Hybrid Swarm Engine (6 modes) |
| `/swarm-status` | Show current swarm mode and DyLAN metrics |
| `/swarm-fsm <task>` | Route task via FSM states (debug mode) |
| `/pool-stats` | Show agent pool DyLAN importance scores |

### 🧬 Evolution

| Command | Description |
|---------|-------------|
| `/evolve [count]` | Create and evaluate child generations (default: 3) |
| `/evolve-status` | Show evolution stats and stagnation counter |
| `/review` | Review and evaluate pending children |
| `/specialize <mission>` | Create specialized NEXUS spinoff |
| `/spawn <role>` | Create specialized agent (e.g., `/spawn SQL Expert`) |
| `/agents` | List all spawned agents |

### 📊 Monitoring

| Command | Description |
|---------|-------------|
| `/status` | Show orchestrator state, agent, iteration |
| `/telemetry` | Show telemetry report (last 7 days) |
| `/telemetry status` | Show detailed telemetry stats |
| `/telemetry export [days]` | Export telemetry to CSV |
| `/budget` | Show budget status (spent, limit, remaining) |
| `/budget reset` | Reset daily budget counter (with confirmation) |
| `/budget add <amount>` | Add emergency credit to budget |
| `/budget history` | Show recent API costs (last 10 calls) |

### 📁 Workspace

| Command | Description |
|---------|-------------|
| `/workspace` | Show current workspace info |
| `/workspace new [name]` | Create new workspace, archive current |
| `/workspace list` | List all workspaces |
| `/workspace switch <name>` | Switch to another workspace |
| `/bootstrap [path]` | Analyze project and generate NEXUS.md |

### ⚙️ System

| Command | Description |
|---------|-------------|
| `/clear` | Clear terminal screen |
| `/reset` | Reset orchestrator to IDLE state |
| `/doctor` | Run system diagnostics |
| `/mode <name>` | Change mode (Normal, InProjectImprovement) |
| `/chat` | Enter chat-only mode (no tools) |
| `/help` | Show categorized help message |
| `/tutorial` | Interactive guide for new users (5 steps) |
| `/quickstart` | Quick start summary (5 min read) |
| `exit` | Exit NEXUS |

---

## Files

| File | Purpose | Key Exports |
|------|---------|-------------|
| `repl.py` | Main REPL loop | `REPL`, `run_repl()` |
| `commands.py` | Categorized commands | `COMMAND_CATEGORIES`, `get_help_message()` |
| `tutorial.py` | Interactive tutorial | `InteractiveTutorial`, `TUTORIAL_STEPS` |
| `commands/registry.py` | **V9.0** Strategy Pattern commands | `CommandRegistry`, `get_registry()` |
| `commands/system.py` | **V9.0** System commands | `StatusCommand`, `HelpCommand`, `QuitCommand` |
| `__init__.py` | Module exports | All public APIs |

---

## CommandRegistry V9.0 (Strategy Pattern)

Architecture extensible pour commandes REPL via Strategy Pattern.

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    COMMAND REGISTRY V9.0                     │
├─────────────────────────────────────────────────────────────┤
│  User Input                                                  │
│       │                                                      │
│       ▼                                                      │
│  ┌──────────────────────────┐                               │
│  │   CommandRegistry        │  ← Singleton (thread-safe)    │
│  │   • register(command)    │                               │
│  │   • execute(input, ctx)  │                               │
│  │   • get_help_text()      │                               │
│  └──────────────────────────┘                               │
│       │                                                      │
│       ▼                                                      │
│  ┌────────────┬────────────┬────────────┐                   │
│  │  /status   │  /help     │  /quit     │                   │
│  │  Strategy  │  Strategy  │  Strategy  │                   │
│  └────────────┴────────────┴────────────┘                   │
│       │                                                      │
│       ▼                                                      │
│  CommandResult(status, message, data, continue_session)     │
└─────────────────────────────────────────────────────────────┘
```

### Usage

```python
from core.interface.commands import get_registry, CommandContext

# Get singleton registry
registry = get_registry()

# Create context
context = CommandContext(orchestrator=orch, config=config)

# Execute command
result = registry.execute("/status detail", context)
print(result.message)

# Add custom command
from core.interface.commands import Command, CommandResult, CommandStatus

class MyCommand(Command):
    @property
    def name(self) -> str:
        return "/mycommand"

    @property
    def description(self) -> str:
        return "My custom command"

    def execute(self, args: str, context: CommandContext) -> CommandResult:
        return CommandResult(
            status=CommandStatus.SUCCESS,
            message="Done!"
        )

registry.register(MyCommand())
```

### Thread-Safe Singleton

```python
# Dans commands/registry.py
_registry_instance: Optional[CommandRegistry] = None
_registry_lock: Optional[threading.Lock] = None

def get_registry() -> CommandRegistry:
    global _registry_instance, _registry_lock
    if _registry_lock is None:
        _registry_lock = threading.Lock()
    if _registry_instance is None:
        with _registry_lock:
            if _registry_instance is None:  # Double-checked locking
                _registry_instance = CommandRegistry()
    return _registry_instance
```

---

## Usage Examples

### Basic REPL

```python
from core.interface import run_repl
from core.config import Config

config = Config()
run_repl(config)  # Starts interactive session
```

### Command Parsing

```python
from core.interface.commands import (
    is_slash_command,
    parse_command,
    get_category_for_command,
    COMMAND_CATEGORIES
)

# Parse command
cmd, args = parse_command("/budget add 10")
# cmd = "/budget", args = "add 10"

# Find category
category = get_category_for_command("/budget")
# "📊 Monitoring"

# List all categories
for cat, commands in COMMAND_CATEGORIES.items():
    print(f"{cat}: {len(commands)} commands")
```

### Tutorial Integration

```python
from core.interface.tutorial import InteractiveTutorial

# Full interactive tutorial
tutorial = InteractiveTutorial()
completed = tutorial.run(
    print_fn=print,
    input_fn=input  # Optional, defaults to input()
)

if completed:
    print("Tutorial completed!")
else:
    print("Tutorial interrupted")

# Quick start only
print(tutorial.get_quick_start())
```

---

## Tests

```bash
# Phase 16 tests (21 tests)
pytest tests/test_phase16_dx.py -v

# Command categories tests
pytest tests/test_phase16_dx.py::TestCommandCategories -v

# Tutorial tests
pytest tests/test_phase16_dx.py::TestInteractiveTutorial -v

# Budget command tests
pytest tests/test_phase16_dx.py::TestBudgetCommand -v
```

---

## Dependencies

### Internal
- `core.orchestration_v7` - FSM orchestrator
- `core.config` - Configuration
- `core.ui` - Console output (Rich)
- `core.evolution` - For `/evolve` commands
- `core.telemetry` - For `/budget` and `/telemetry`

### External
- `rich` - Console formatting
- Standard library only for core

---

## See Also

- [Core README](../README.md) - Architecture overview
- [Evolution Module](../evolution/README.md) - Evolution commands
- [Telemetry Module](../telemetry/README.md) - Budget tracking
- [Swarm Module](../swarm/README.md) - Swarm commands
