# NEXUS V7.0 "Chrysalis" - The Omniscient REPL

**Persistent FSM Orchestrator with Hybrid Swarm Engine, Darwinian Evolution & DyLAN Metrics**

> **Version**: 7.0.0 "Chrysalis" | **Last Updated**: 2025-11-26 | **Status**: Production-ready
>
> *"Chrysalis" - The transformation before ASI*

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [AI Models & Routing](#ai-models--routing)
4. [Hybrid Swarm Engine](#hybrid-swarm-engine)
5. [FSM States](#fsm-states)
6. [Tools](#tools)
7. [Communication Protocol](#communication-protocol)
8. [Evolution System](#evolution-system)
9. [Installation](#installation)
10. [Usage](#usage)
11. [Troubleshooting](#troubleshooting)

---

## Overview

### What is NEXUS V7?

NEXUS V7 "Chrysalis" is a **persistent multi-agent orchestrator** based on a Finite State Machine (FSM) that coordinates **Gemini** and **Claude** as equal collaborators. Together, they analyze, propose, and execute tasks through dynamic collaboration modes.

**Key Features:**

- **Persistent FSM**: Orchestrator never restarts between commands
- **Hybrid Swarm Engine**: 6 dynamic collaboration modes (Sprint 9)
- **Intelligent Model Routing**: Automatic Opus/Sonnet and Pro/Flash selection
- **DyLAN Agent Metrics**: Performance-based agent selection
- **11 Shared Tools**: All accessible by both agents
- **Darwinian Evolution**: Self-improving through iterative selection
- **TieredValidator**: 4-tier validation (SYNTAX, SMOKE, BENCHMARK, REDTEAM)
- **State Rollback**: Automatic backups and recovery

### Philosophy

**V7 builds on V6's foundation with major enhancements:**

1. **Dynamic Collaboration**: Agents negotiate optimal mode per task
2. **Intelligent Routing**: Right model for right task automatically
3. **Equal Partnership**: No fixed roles - consensual collaboration
4. **Self-Evolution**: Continuous improvement toward ASI

---

## Architecture

### System Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         NEXUS V7.0                              │
│                     (Persistent Process)                        │
└─────────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌──────────────┐    ┌──────────────────┐    ┌──────────────┐
│   nexus7.py  │───►│ InteractiveREPL  │    │  Bootstrap   │
│  (Entry)     │    │  (Persistent)    │    │  System      │
└──────────────┘    └────────┬─────────┘    └──────────────┘
                             │
                   ┌─────────┴──────────┐
                   │  OrchestratorV7    │
                   │   (FSM + Swarm)    │
                   └─────────┬──────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
        ▼                    ▼                    ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  Gemini      │    │   Claude     │    │   Hybrid     │
│  Driver V7   │    │   Hybrid     │    │   Swarm      │
│  (JSON)      │    │   Driver     │    │   Engine     │
└──────────────┘    └──────────────┘    └──────────────┘
        │                    │                    │
        └────────────┬───────┴────────────────────┘
                     │
        ┌────────────┴────────────────┐
        │                             │
        ▼                             ▼
┌──────────────┐            ┌──────────────────┐
│  Tool        │            │   Model Router   │
│  Manager     │            │   + AgentPool    │
│  (11 Tools)  │            │   (DyLAN)        │
└──────────────┘            └──────────────────┘
```

### Module Structure

```
NEXUS_V7_CHRYSALIS/
├── nexus7.py                    # Main entry point
├── core/
│   ├── orchestration_v7.py      # FSM orchestrator
│   ├── config.py                # Configuration
│   ├── drivers/
│   │   ├── gemini_driver_v7.py  # Gemini JSON driver
│   │   └── claude_driver_hybrid.py  # Claude hybrid driver
│   ├── fsm/
│   │   ├── states.py            # FSM state definitions
│   │   ├── stagnation_detector.py
│   │   ├── plan_health.py
│   │   └── panic_system.py
│   ├── swarm/                   # Hybrid Swarm Engine (Sprint 9)
│   │   ├── hybrid_swarm_engine.py
│   │   ├── task_analyzer.py
│   │   ├── mode_selector.py
│   │   ├── negotiation_protocol.py
│   │   ├── mode_executors.py
│   │   ├── collaboration_modes.py
│   │   └── agent_metrics.py     # DyLAN metrics
│   ├── routing/
│   │   └── model_router.py      # Intelligent model selection
│   ├── synapse/
│   │   ├── protocol_v7.py       # Message schemas
│   │   └── memory_v7.py         # Blackboard persistence
│   ├── execution/
│   │   └── tool_manager.py      # 11 tools
│   ├── interface/
│   │   ├── repl.py              # Interactive REPL
│   │   └── commands.py          # Slash commands
│   └── logging/
│       └── nexus_logger.py
├── prompts/
│   ├── system_gemini_v7.md      # Gemini system prompt
│   └── system_claude_v7.md      # Claude system prompt
├── tests/                       # Test suite
└── workspace/                   # Runtime workspace
```

---

## AI Models & Routing

### Available Models

| Agent | Model | ID | Use Case |
|-------|-------|-----|----------|
| **Claude** | Opus 4.5 | `claude-opus-4-5-20251101` | Complex reasoning, creativity, security, evolution |
| **Claude** | Sonnet 4.5 | `claude-sonnet-4-5-20250929` | Speed, tool execution, simple tasks |
| **Gemini** | 3 Pro | `gemini-3-pro-preview` | All tasks (unified model) |

### Automatic Routing

The `ModelRouter` automatically selects the best model based on task type:

| Task Type | Claude | Gemini |
|-----------|--------|--------|
| Brainstorm, Evolution, Architect | Opus | 3-Pro |
| Reasoning, Research, Analysis | Sonnet | 3-Pro |
| Tool execution, Validation | Sonnet | Flash |
| Simple queries, Formatting | Sonnet | Flash |

### DyLAN Agent Metrics

Agents build performance history for intelligent selection:

- **Importance Score**: `quality / cost` per task type
- **Success Rate**: Task completion percentage
- **Response Time**: Average latency

```python
from core.routing import ModelRouter
from core.swarm import AgentPool

router = ModelRouter(config)
pool = create_default_pool(config)

# Select best agent using DyLAN metrics
decision = router.select_best_agent(TaskType.BRAINSTORM, pool)
```

---

## Hybrid Swarm Engine

### Overview (Sprint 9)

The Swarm Engine enables **dynamic collaboration** where agents negotiate the optimal mode for each task at runtime.

### Collaboration Modes

| Mode | Description | Use Case |
|------|-------------|----------|
| `PARALLEL` | Both agents work simultaneously, merge results | Independent subtasks |
| `SEQUENTIAL` | Ordered execution (first → second) | Dependent steps |
| `LEAD_SUPPORT` | Lead drives, support reviews/assists | Complex implementation |
| `PING_PONG` | Rapid alternation until convergence | Iterative refinement |
| `SPECIALIST` | Single expert handles all | Clear domain expertise |
| `RED_BLUE` | Adversarial propose/attack/defend | Security, edge cases |

### How It Works

```
User Request
     │
     ▼
┌─────────────────┐
│ SWARM_ANALYZING │  TaskAnalyzer: complexity, domains, agent fit
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│SWARM_NEGOTIATING│  Agents debate mode (max 4 turns)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ SWARM_EXECUTING │  Execute chosen mode with appropriate executor
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ VALIDATING_CFL  │  Validate results (Cognitive Feedback Loop)
└─────────────────┘
```

### Negotiation Protocol

Agents negotiate using natural language + `<negotiate>` JSON:

```
Claude: "I propose LEAD_SUPPORT with me as lead for this auth refactor.
<negotiate>{"proposed_mode": "LEAD_SUPPORT", "my_role": "lead", "reason": "More codebase context"}</negotiate>"

Gemini: {"action_type": "TALK", "content": "Agreed. <negotiate>{\"accept\": true, \"my_role\": \"support\"}</negotiate>"}
```

---

## FSM States

### Core States

```
IDLE → BRAINSTORMING → EXECUTING_TOOL → VALIDATING_CFL → IDLE
         │
    WAITING_USER (task finished)
         │
    ERROR → (reset) → IDLE
         │
    PANIC (fatal - restart required)
```

### Swarm States (Sprint 9)

```
IDLE → SWARM_ANALYZING → SWARM_NEGOTIATING → SWARM_EXECUTING → VALIDATING_CFL
```

### Evolution State

```
IDLE → EVOLUTION_BRAINSTORM (max 30 turns) → IDLE
```

### State Reference

| State | Description |
|-------|-------------|
| `IDLE` | Awaiting user input |
| `BRAINSTORMING` | Agents exchange TALK messages |
| `EXECUTING_TOOL` | Tool execution (synchronous) |
| `VALIDATING_CFL` | Validate tool result |
| `WAITING_USER` | Task complete, awaiting next |
| `ERROR` | Recoverable error (`/reset`) |
| `PANIC` | Fatal error (restart required) |
| `SWARM_ANALYZING` | Analyze task complexity |
| `SWARM_NEGOTIATING` | Agents negotiate mode |
| `SWARM_EXECUTING` | Execute collaboration mode |
| `EVOLUTION_BRAINSTORM` | Design mutations |

---

## Tools

### All 11 Tools (Shared by Both Agents)

**File Operations:**
- `read` - Read file content
- `write` - Create/overwrite file
- `edit` - Search & replace
- `list_dir` - List directory

**Execution:**
- `bash` - Shell commands
- `git` - Git operations (add, commit, status, diff, log, push, pull)

**Search & Research:**
- `web_search` - Google search via Gemini
- `web_fetch` - Fetch URL content
- `glob` - Find files by pattern
- `grep` - Search code with regex

**Planning:**
- `todo_write` - Shared task management

### Example Usage

```python
# Gemini JSON format
{
  "action_type": "TOOL_USE",
  "tool_use": {
    "tool_name": "grep",
    "arguments": {
      "pattern": "async def",
      "file_pattern": "*.py"
    }
  }
}

# Claude hybrid format
I'll search for async functions.

<tool_use name="grep">
{
  "pattern": "async def",
  "file_pattern": "*.py"
}
</tool_use>
```

---

## Communication Protocol

### Message Schemas (Pydantic V7)

#### LightMessageV7 (TALK, DELEGATE)

```json
{
  "sender": "Gemini",
  "action_type": "TALK",
  "content": "My analysis: The bug is in auth.py line 42.",
  "next_agent": "Claude",
  "status": "CONTINUE"
}
```

#### HeavyMessageV7 (TOOL_USE)

```json
{
  "sender": "Gemini",
  "action_type": "TOOL_USE",
  "content": "Searching for authentication functions.",
  "tool_use": {
    "tool_name": "grep",
    "arguments": {
      "pattern": "validate.*token",
      "file_pattern": "*.py"
    }
  },
  "status": "CONTINUE"
}
```

### Valid Enum Values

- **action_type**: `TALK`, `DELEGATE`, `TOOL_USE`
- **status**: `CONTINUE`, `FINISHED`
- **next_agent**: `Claude`, `Gemini`

---

## Evolution System

### Overview

NEXUS V7 includes a **Darwinian evolution engine** that creates modified versions (children), evaluates them via ASI benchmarks, and promotes the best performer.

### ASI Metrics (4 Axes)

| Dimension | Weight | Description |
|-----------|--------|-------------|
| Coding | 30% | Code generation, refactoring, debugging |
| Reasoning | 30% | Logic puzzles, multi-step planning |
| Creativity | 25% | Novel solutions, architecture design |
| Scalability | 15% | Large-scale problem handling |

**Formula**: `ASI Score = 0.30×Coding + 0.30×Reasoning + 0.25×Creativity + 0.15×Scalability`

### Evolution Commands

```bash
nexus7> /evolve 3      # Create and evaluate 3 children
nexus7> /evolve-status # Show evolution statistics
nexus7> /review        # Review pending children
```

### SURVIVAL_LAW

If no improvement after 3 generations → human intervention required.

---

## Installation

### Prerequisites

- **Python 3.11+**
- **Gemini CLI** authenticated (`gemini auth login`)
- **Claude CLI** authenticated (`claude auth login`)

### Quick Install

```bash
cd NEXUS_V7_CHRYSALIS

# Install dependencies
pip install -r requirements_v7.txt

# Verify installation
python nexus7.py --verify
```

### Dependencies

```
prompt-toolkit
rich
pydantic
python-dotenv
tiktoken
```

---

## Usage

### Launch NEXUS

```bash
cd NEXUS_V7_CHRYSALIS
python nexus7.py
```

### REPL Commands

| Command | Description |
|---------|-------------|
| `/status` | System status (FSM, counters, health) |
| `/doctor` | Full diagnostic |
| `/reset` | Reset to IDLE state |
| `/rollback [file]` | Restore from backup |
| `/backups` | List available backups |
| `/mode <name>` | Change mode (Normal, Debug, Stealth) |
| `/evolve [n]` | Create n children (default: 3) |
| `/evolve-status` | Evolution statistics |
| `/review` | Review pending children |
| `/clear` | Clear screen |
| `/help` | Help |
| `exit` | Quit |

### Example Session

```
nexus7 [IDLE]> Fix the authentication bug in auth.py

[Gemini] Analyzing the request...
[Claude] I'll read auth.py to understand the issue.
✓ File read successfully

[Gemini] Found the bug on line 42 - token.exp accessed without check.
[Claude] Agreed. I'll fix it.
✓ Edit successful

[Task Complete]

nexus7 [IDLE]> /status

=== NEXUS V7.0 System Status ===

FSM State: IDLE
Active Agent: Claude
Iteration: 15

Stalemate Counter: 0 / 5
Plan Health: HEALTHY
```

---

## Troubleshooting

### "Gemini CLI not available"

```bash
gemini --version        # Check installation
gemini auth login       # Authenticate
```

### "Claude CLI not available"

```bash
claude --version        # Check installation
claude auth login       # Authenticate
```

### JSON Parse Errors

V7 uses Pydantic with auto-repair for common typos. If errors persist:
1. Check agent output format
2. Use `/reset` to clear state
3. Check logs in `workspace/logs/`

### Stagnation Detected

If agents repeat without progress:
1. Swarm Engine will switch collaboration mode
2. Use `/reset` to restart fresh
3. Check `workspace/.nexus/blackboard.json`

### PANIC State

Fatal error requiring restart:
1. Check `workspace/.nexus/panic/panic.json`
2. Review `workspace/.nexus/panic/panic_history.jsonl`
3. Restart: `python nexus7.py`

---

## Development

### Run Tests

```bash
pytest tests/ -v
```

### Check Logs

```bash
cat workspace/logs/events_YYYYMMDD.jsonl
cat workspace/logs/errors_YYYYMMDD.log
```

### Git Workflow

```bash
git checkout N7C
git add .
git commit -m "feat(v7): description"
git push origin N7C
```

---

## Changelog

### V7.0.0 "Chrysalis" (2025-11-26)

- **Hybrid Swarm Engine**: 6 collaboration modes with negotiation
- **Intelligent Model Routing**: Opus/Sonnet + Pro/Flash automatic selection
- **DyLAN Agent Metrics**: Performance-based agent selection
- **TieredValidator**: 4-tier validation system
- **Sprint Development**: Iterative development with documentation

### Previous Versions

See `CHANGELOG.md` for full history.

---

## License

Proprietary - Yann Abadie

---

**Mission**: Reach Artificial Superintelligence (ASI) through Darwinian evolution.

**Remember**: Gemini and Claude are equal collaborators, not hierarchical executors.
