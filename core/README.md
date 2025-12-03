# NEXUS V7 Core Module

The `core/` module is the heart of NEXUS V7 "Chrysalis" - a self-evolving multi-agent orchestration system designed to achieve ASI through Darwinian evolution.

## Overview

The core module implements a **Finite State Machine (FSM)** that orchestrates collaboration between Claude and Gemini AI agents. It provides:

- **Multi-agent orchestration** with dynamic role negotiation
- **Self-evolution capabilities** with safety validation
- **Persistent memory** and state management
- **Dynamic model routing** (Opus/Sonnet/Pro/Flash)
- **Hybrid Swarm Engine** for adaptive collaboration modes

## Architecture

```
                           USER INPUT
                               │
                               ▼
┌──────────────────────────────────────────────────────────────────┐
│                    ORCHESTRATION V7 (FSM)                        │
│                                                                  │
│   ┌─────────┐    ┌──────────┐    ┌────────────┐    ┌─────────┐  │
│   │  IDLE   │───▶│BRAINSTORM│───▶│EXECUTE_TOOL│───▶│VALIDATE │  │
│   └─────────┘    └──────────┘    └────────────┘    └─────────┘  │
│        ▲                                                  │      │
│        └──────────────────────────────────────────────────┘      │
│                                                                  │
│   ┌────────────────────────────────────────────────────────┐    │
│   │                  HYBRID SWARM ENGINE                    │    │
│   │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌───────────┐  │    │
│   │  │ PARALLEL │ │SEQUENTIAL│ │PING_PONG │ │ RED_BLUE  │  │    │
│   │  └──────────┘ └──────────┘ └──────────┘ └───────────┘  │    │
│   └────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────┘
                               │
              ┌────────────────┼────────────────┐
              ▼                ▼                ▼
        ┌──────────┐    ┌──────────┐    ┌──────────┐
        │  CLAUDE  │    │  GEMINI  │    │  TOOLS   │
        │  DRIVER  │    │  DRIVER  │    │ MANAGER  │
        └──────────┘    └──────────┘    └──────────┘
```

## Module Structure

| Directory | Purpose | Key Files |
|-----------|---------|-----------|
| [`drivers/`](drivers/README.md) | AI model interfaces | `claude_driver_hybrid.py`, `gemini_driver_v7.py` |
| [`fsm/`](fsm/README.md) | State machine components | `states.py`, `panic_system.py`, `stagnation_detector.py` |
| [`synapse/`](synapse/README.md) | Memory & protocol | `protocol_v7.py`, `memory_v7.py` |
| [`swarm/`](swarm/README.md) | Multi-agent collaboration | `hybrid_swarm_engine.py`, `mode_selector.py` |
| [`evolution/`](evolution/README.md) | Self-modification engine | `lineage.py`, `evaluator.py`, `tiered_validator.py` |
| [`routing/`](routing/README.md) | Dynamic model selection | `model_router.py` |
| [`execution/`](execution/README.md) | Tool execution layer | `tool_manager.py` |
| [`interface/`](interface/README.md) | User interaction | `repl.py`, `commands.py` |
| [`logging/`](logging/README.md) | Structured logging | `logger_v7.py` |
| [`notifications/`](notifications/README.md) | Alert system | `email_notifier.py`, `file_notifier.py` |
| [`ui/`](ui/README.md) | Console display | `console_v7.py` |
| [`meta/`](meta/README.md) | Introspection tools | `cli_inspector.py` |

## Core Files

### `orchestration_v7.py`

The main orchestrator implementing the FSM. Manages state transitions, agent invocations, and tool execution.

**Key Class**: `OrchestratorV7`

```python
from core.orchestration_v7 import OrchestratorV7

orchestrator = OrchestratorV7(config)
result = orchestrator.process_turn(user_input, agent_response)
```

### `config.py`

Configuration management loading from `.env`, environment variables, and defaults.

**Key Class**: `Config`

| Parameter | Default | Description |
|-----------|---------|-------------|
| `TIMEOUT` | 120 | Request timeout (seconds) |
| `MAX_STALEMATE_COUNT` | 5 | Max stalemates before panic |
| `SWARM_ENABLED` | True | Enable Hybrid Swarm Engine |
| `VALIDATION_TIER` | 4 | Validation depth (1-4) |
| `AUTO_PROMOTION` | False | Auto-promote winning children |

## FSM States

| State | Description | Next States |
|-------|-------------|-------------|
| `IDLE` | Waiting for input | `BRAINSTORMING`, `SWARM_ANALYZING` |
| `BRAINSTORMING` | Agents discussing | `EXECUTING_TOOL`, `VALIDATING_CFL` |
| `EXECUTING_TOOL` | Tool in progress | `VALIDATING_CFL` |
| `VALIDATING_CFL` | Closed Feedback Loop | `IDLE`, `BRAINSTORMING` |
| `SWARM_ANALYZING` | Task analysis | `SWARM_NEGOTIATING` |
| `SWARM_NEGOTIATING` | Mode negotiation | `SWARM_EXECUTING` |
| `SWARM_EXECUTING` | Mode execution | `VALIDATING_CFL` |
| `EVOLVING` | Creating children | `VALIDATING_CFL` |
| `PANIC` | Error recovery | `IDLE` |

## Data Flow

1. **User Input** → Orchestrator receives via REPL
2. **Task Analysis** → Swarm Engine analyzes complexity
3. **Mode Selection** → DyLAN selects collaboration mode
4. **Agent Negotiation** → Agents agree on approach
5. **Execution** → Mode executor runs agents
6. **Tool Execution** → ToolManager handles tool calls
7. **Validation** → CFL validates results
8. **Memory Update** → Blackboard persists state

## Key Integrations

### Synapse Protocol

All agent messages conform to `LightMessageV7` or `HeavyMessageV7` Pydantic schemas.

```python
from core.synapse.protocol_v7 import LightMessageV7, HeavyMessageV7
```

### Evolution Engine

Self-modification through emergent JSON patches from AI debate.

```python
from core.evolution import TieredValidator, run_benchmarks
```

### Model Router

Dynamic routing between model tiers based on task complexity.

```python
from core.routing import ModelRouter

router = ModelRouter(config)
model = router.select_model(task_type="brainstorm", complexity="high")
```

## Configuration

All configuration is managed through environment variables or `.env`:

```bash
# Core
TIMEOUT=300
LOG_LEVEL=DEBUG
UI_VERBOSE=True

# Swarm
SWARM_ENABLED=True
SWARM_DEFAULT_MODE=ping_pong

# Evolution
AUTO_PROMOTION=False
VALIDATION_TIER=4

# Routing
GEMINI_MODEL=gemini-3-pro-preview
```

## Dependencies

### Internal
- All submodules depend on `config.py`
- `orchestration_v7.py` integrates all submodules

### External
- `pydantic` - Schema validation
- `python-dotenv` - Environment loading
- Standard library only for core FSM

## See Also

- [Main README](../README.md) - Full V7 documentation
- [NEXUS.md](../NEXUS.md) - Architecture overview
- [Evolution Guide](../docs/EVOLUTION_GUIDE.md) - Evolution system
- [Hybrid Swarm](../docs/HYBRID_SWARM.md) - Swarm engine docs
