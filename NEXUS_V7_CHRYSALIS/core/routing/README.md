# Routing Module

Intelligent model selection and routing for NEXUS V7.

## Overview

The Routing module provides dynamic model selection based on task type and complexity:
- **Claude routing**: Opus (complex) vs Sonnet (simple)
- **Gemini routing**: 3-Pro (reasoning) vs Flash (fast)
- **DyLAN integration**: Uses agent metrics for selection

## Architecture

```
                         TASK
                           │
                           ▼
┌──────────────────────────────────────────────┐
│               MODEL ROUTER                    │
│                                              │
│   ┌────────────────┐   ┌────────────────┐   │
│   │  Task Analysis │   │ Agent Metrics  │   │
│   │  • Type        │   │  • DyLAN scores│   │
│   │  • Complexity  │   │  • History     │   │
│   └───────┬────────┘   └───────┬────────┘   │
│           └──────────┬─────────┘            │
│                      ▼                      │
│            ┌──────────────────┐             │
│            │ Routing Decision │             │
│            └──────────────────┘             │
└──────────────────────────────────────────────┘
                       │
        ┌──────────────┴──────────────┐
        ▼                             ▼
┌───────────────────┐      ┌───────────────────┐
│      CLAUDE       │      │      GEMINI       │
│  ┌─────┐ ┌─────┐  │      │  ┌─────┐ ┌─────┐  │
│  │OPUS │ │SONN │  │      │  │ PRO │ │FLASH│  │
│  └─────┘ └─────┘  │      │  └─────┘ └─────┘  │
└───────────────────┘      └───────────────────┘
```

## Files

| File | Purpose | Key Classes |
|------|---------|-------------|
| `model_router.py` | Routing logic | `ModelRouter`, `TaskType`, `RoutingDecision` |
| `__init__.py` | Module exports | - |

## Key Classes

### ModelRouter

Main routing class for model selection.

```python
from core.routing import ModelRouter, TaskType
from core.config import Config

config = Config()
router = ModelRouter(config)

# Claude routing
claude_model = router.select_claude_model(TaskType.BRAINSTORM)
# "claude-opus-4-5-20251101"

claude_model = router.select_claude_model(TaskType.VALIDATION)
# "claude-sonnet-4-5-20250929"

# Gemini routing
gemini_model = router.select_gemini_model(TaskType.REASONING)
# "gemini-3-pro-preview"

gemini_model = router.select_gemini_model(TaskType.TOOL)
# "gemini-2.5-flash"
```

**Methods**:
| Method | Description | Returns |
|--------|-------------|---------|
| `select_claude_model(task_type)` | Select Claude model | `str` (model ID) |
| `select_gemini_model(task_type)` | Select Gemini model | `str` (model ID) |
| `route_task(task_type, agent)` | Full routing decision | `RoutingDecision` |
| `get_routing_reason(task_type)` | Explain routing | `str` |

### TaskType

Enum of task types for routing.

```python
from core.routing import TaskType

# Opus/Pro routed (complex tasks)
TaskType.BRAINSTORM     # Evolution brainstorming
TaskType.REDTEAM        # Security testing
TaskType.ARCHITECT      # Architecture decisions
TaskType.EVOLUTION      # Child mutation design
TaskType.REASONING      # Complex reasoning
TaskType.RESEARCH       # Web research
TaskType.ANALYSIS       # Deep analysis

# Sonnet/Flash routed (simple tasks)
TaskType.TOOL           # Tool execution
TaskType.VALIDATION     # Code validation
TaskType.SIMPLE         # Simple queries
TaskType.FORMAT         # Formatting
```

### RoutingDecision

Result of routing decision.

```python
from core.routing import RoutingDecision

decision = router.route_task(TaskType.BRAINSTORM, agent="claude")

# RoutingDecision:
#   model_id: "claude-opus-4-5-20251101"
#   task_type: TaskType.BRAINSTORM
#   reason: "Complex brainstorming requires Opus creativity"
#   is_opus: True
```

## Routing Rules

### Claude Models

| Task Type | Model | Reason |
|-----------|-------|--------|
| `BRAINSTORM` | Opus | Creativity, complex reasoning |
| `REDTEAM` | Opus | Security analysis depth |
| `ARCHITECT` | Opus | Architecture decisions |
| `EVOLUTION` | Opus | Mutation design complexity |
| `TOOL` | Sonnet | Speed for tool execution |
| `VALIDATION` | Sonnet | Fast validation |
| `SIMPLE` | Sonnet | Low-latency responses |
| `FORMAT` | Sonnet | Quick formatting |

### Gemini Models (V7 Sprint 6)

| Task Type | Model | Reason |
|-----------|-------|--------|
| `REASONING` | 3-Pro | Deep reasoning capabilities |
| `RESEARCH` | 3-Pro | Web research quality |
| `ANALYSIS` | 3-Pro | Comprehensive analysis |
| `BRAINSTORM` | 3-Pro | Creative ideation |
| `TOOL` | Flash | Fast tool use |
| `VALIDATION` | Flash | Quick validation |
| `SIMPLE` | Flash | Low latency |
| `FORMAT` | Flash | Fast formatting |

## Configuration

Environment variables:
```bash
# Model IDs
GEMINI_MODEL=gemini-3-pro-preview

# In config.py
claude_opus_model = "claude-opus-4-5-20251101"
claude_sonnet_model = "claude-sonnet-4-5-20250929"
gemini_pro_model = "gemini-3-pro-preview"
gemini_flash_model = "gemini-2.5-flash"

# Task type lists
opus_task_types = ["brainstorm", "redteam", "architect", "evolution"]
sonnet_task_types = ["tool", "validation", "simple", "format"]
gemini_pro_tasks = ["reasoning", "research", "analysis", "brainstorm"]
gemini_flash_tasks = ["simple", "format", "validation", "tool"]
```

## Usage Example

```python
from core.routing import ModelRouter, TaskType
from core.drivers import ClaudeDriverHybrid, GeminiDriverV7
from core.config import Config
from pathlib import Path

config = Config()
router = ModelRouter(config)
workspace = Path("./workspace")

# Route a brainstorming task
task_type = TaskType.BRAINSTORM

claude_model = router.select_claude_model(task_type)
claude = ClaudeDriverHybrid(config, workspace, model=claude_model)

gemini_model = router.select_gemini_model(task_type)
gemini = GeminiDriverV7(config, workspace, model=gemini_model)

# Both agents use their "Pro" models for complex brainstorming
```

## Dependencies

### Internal
- `core.config` - Model configuration
- `core.swarm` - AgentPool integration (optional)

### External
- `enum` - Task type enumeration
- `dataclasses` - RoutingDecision

## See Also

- [Core README](../README.md) - Architecture overview
- [Drivers Module](../drivers/README.md) - Model invocation
- [Swarm Module](../swarm/README.md) - DyLAN integration
