# Swarm Module

Hybrid Swarm Engine for dynamic multi-agent collaboration in NEXUS V7.

## Overview

The Swarm module (Sprint 9) enables **dynamic collaboration mode selection** where agents negotiate the optimal way to work together for each task. Instead of fixed roles, agents adapt their collaboration style based on task complexity.

## Architecture

```
                         USER INPUT
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    HYBRID SWARM ENGINE                          │
│                                                                 │
│  ┌──────────────────┐   ┌──────────────────┐   ┌─────────────┐  │
│  │   TaskAnalyzer   │──▶│   ModeSelector   │──▶│ Negotiation │  │
│  │  • Complexity    │   │   • DyLAN scores │   │  Protocol   │  │
│  │  • Domains       │   │   • Mode scoring │   │  • Hybrid   │  │
│  └──────────────────┘   └──────────────────┘   └─────────────┘  │
│                                                      │          │
│                                                      ▼          │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    MODE EXECUTORS                        │   │
│  │  ┌──────────┐ ┌──────────┐ ┌────────────┐ ┌──────────┐  │   │
│  │  │ PARALLEL │ │SEQUENTIAL│ │LEAD_SUPPORT│ │PING_PONG │  │   │
│  │  └──────────┘ └──────────┘ └────────────┘ └──────────┘  │   │
│  │  ┌────────────┐ ┌──────────┐                             │   │
│  │  │ SPECIALIST │ │ RED_BLUE │                             │   │
│  │  └────────────┘ └──────────┘                             │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

## Collaboration Modes

| Mode | Description | Use Case |
|------|-------------|----------|
| **PARALLEL** | Simultaneous work, merge results | Independent subtasks |
| **SEQUENTIAL** | Ordered execution (first → second) | Clear dependencies |
| **LEAD_SUPPORT** | Lead (80%) + Support (20%) | Dominant expertise |
| **PING_PONG** | Rapid alternation until convergence | Brainstorming, creativity |
| **SPECIALIST** | Single expert handles all | Exclusive expertise |
| **RED_BLUE** | Adversarial propose/attack/defend | Security, critical decisions |

## Files

| File | Purpose | Key Classes |
|------|---------|-------------|
| `collaboration_modes.py` | Mode definitions | `CollaborationMode`, `ModeCharacteristics` |
| `task_analyzer.py` | Task analysis | `TaskAnalyzer`, `TaskComplexity`, `TaskDomain` |
| `mode_selector.py` | Mode selection | `ModeSelector`, `ModeProposal` |
| `negotiation_protocol.py` | Agent negotiation | `NegotiationProtocol`, `NegotiationResult` |
| `mode_executors.py` | Execution strategies | `ParallelExecutor`, `RedBlueExecutor`, etc. |
| `hybrid_swarm_engine.py` | Main engine | `HybridSwarmEngine`, `SwarmResult` |
| `agent_metrics.py` | DyLAN scoring | `AgentProfile`, `AgentPool` |

## Key Classes

### HybridSwarmEngine

Main orchestration engine.

```python
from core.swarm import HybridSwarmEngine, create_default_pool
from core.routing import ModelRouter
from core.config import Config

config = Config()
agent_pool = create_default_pool()
router = ModelRouter(config)

engine = HybridSwarmEngine(agent_pool, router, config)
result = engine.process_task("Fix the auth bug", blackboard)
```

**Methods**:
| Method | Description | Returns |
|--------|-------------|---------|
| `process_task(task, blackboard)` | Full task processing | `SwarmResult` |
| `analyze_task(task)` | Analyze complexity | `TaskAnalysis` |
| `select_mode(analysis)` | Select optimal mode | `ModeProposal` |
| `negotiate(proposal)` | Agent negotiation | `NegotiationResult` |
| `execute(mode, context)` | Execute mode | `ExecutionResult` |

### TaskAnalyzer

Analyzes task complexity and domains.

```python
from core.swarm import TaskAnalyzer, TaskComplexity, TaskDomain

analyzer = TaskAnalyzer()
analysis = analyzer.analyze("Fix the JWT validation bug in auth.py")

# TaskAnalysis:
#   complexity: TaskComplexity.MODERATE
#   domains: [TaskDomain.CODING, TaskDomain.SECURITY]
#   requires_web: False
#   requires_code_execution: True
#   gemini_fit_score: 0.6
#   claude_fit_score: 0.9
```

**Task Complexity Levels**:
| Level | Description | Negotiation |
|-------|-------------|-------------|
| `TRIVIAL` (1) | Single-step tasks | Skip |
| `SIMPLE` (2) | Basic operations | Minimal |
| `MODERATE` (3) | Standard tasks | Full |
| `COMPLEX` (4) | Multi-step planning | Extended |
| `EXPERT` (5) | Critical decisions | RED_BLUE |

**Task Domains**:
- `CODING` - Code writing/editing
- `RESEARCH` - Information gathering
- `ANALYSIS` - Code review, debugging
- `CREATIVE` - Design, brainstorming
- `DEBUGGING` - Bug investigation
- `SECURITY` - Security analysis

### ModeSelector

Selects optimal collaboration mode using DyLAN scores.

```python
from core.swarm import ModeSelector, AgentPool

selector = ModeSelector(agent_pool)
proposal = selector.select_mode(analysis, available_agents)

# ModeProposal:
#   mode: CollaborationMode.LEAD_SUPPORT
#   confidence: 0.85
#   agent_assignments: {
#       "lead": "Claude",
#       "support": "Gemini"
#   }
```

### NegotiationProtocol

Hybrid negotiation (natural language + JSON).

```python
from core.swarm import NegotiationProtocol

protocol = NegotiationProtocol(
    max_turns=4,
    consensus_threshold=0.6
)

result = protocol.run_negotiation(
    task_analysis,
    initial_proposal,
    invoke_agent_callback
)

# NegotiationResult:
#   status: NegotiationStatus.CONSENSUS
#   selected_mode: CollaborationMode.LEAD_SUPPORT
#   final_assignments: {...}
#   negotiation_history: [...]
```

**Negotiation Message Format**:
```
Gemini: "For this debugging task, I suggest LEAD_SUPPORT mode.
Claude has strong Python expertise, so they should lead.

<negotiate>
{
  "proposed_mode": "lead_support",
  "proposed_lead": "Claude",
  "confidence": 0.85
}
</negotiate>"
```

### Mode Executors

Each mode has a dedicated executor.

```python
from core.swarm import get_executor, CollaborationMode

executor = get_executor(CollaborationMode.PARALLEL)
result = executor.execute(context)
```

**Executor Types**:

| Executor | Mode | Strategy |
|----------|------|----------|
| `ParallelExecutor` | PARALLEL | ThreadPoolExecutor, merge results |
| `SequentialExecutor` | SEQUENTIAL | First → Second, chain outputs |
| `LeadSupportExecutor` | LEAD_SUPPORT | Lead produces, Support reviews |
| `PingPongExecutor` | PING_PONG | Alternate until convergence |
| `SpecialistExecutor` | SPECIALIST | Single agent handles all |
| `RedBlueExecutor` | RED_BLUE | Propose → Attack → Defend |

### AgentPool & AgentProfile

DyLAN-based agent metrics and selection.

```python
from core.swarm import AgentPool, AgentProfile, create_default_pool

pool = create_default_pool()

# Get agent
claude = pool.get_agent("claude_primary")

# Record performance
claude.record_invocation(
    task_type="coding",
    success=True,
    latency=2.5,
    quality_score=0.9
)

# Get importance score for task
importance = claude.get_task_importance("coding")
# 0.95 (high due to good history)
```

## Swarm Flow

```
1. USER INPUT
   │
   ▼
2. SWARM_ANALYZING
   │ TaskAnalyzer determines complexity, domains
   ▼
3. SWARM_NEGOTIATING
   │ Agents debate optimal mode via <negotiate> JSON
   │ Max 4 turns, consensus or fallback
   ▼
4. SWARM_EXECUTING
   │ Selected executor runs the mode
   │ Agents collaborate per mode rules
   ▼
5. VALIDATING_CFL
   │ Results validated
   ▼
6. IDLE
```

## Configuration

Environment variables:
```bash
SWARM_ENABLED=True                  # Enable swarm engine
SWARM_NEGOTIATION=True              # Enable negotiation
SWARM_NEGOTIATION_TURNS=4           # Max negotiation rounds
SWARM_DEFAULT_MODE=ping_pong        # Fallback mode
SWARM_SKIP_TRIVIAL=True             # Skip for trivial tasks
SWARM_MAX_ROUNDS=6                  # Max execution rounds
```

## Usage Example

```python
from core.swarm import (
    HybridSwarmEngine,
    create_default_pool,
    CollaborationMode
)
from core.routing import ModelRouter
from core.config import Config
from pathlib import Path

# Initialize
config = Config()
pool = create_default_pool()
router = ModelRouter(config)

engine = HybridSwarmEngine(pool, router, config)

# Process task
blackboard = {"state": {}, "messages": []}
result = engine.process_task(
    "Review the security of the auth module",
    blackboard
)

# Result
print(f"Mode used: {result.mode}")           # RED_BLUE
print(f"Status: {result.status}")            # SUCCESS
print(f"Agent outputs: {result.outputs}")    # [Claude proposal, Gemini attack, ...]
```

## Dependencies

### Internal
- `core.config` - Swarm configuration
- `core.synapse` - Message schemas
- `core.routing` - Model selection

### External
- `concurrent.futures` - Parallel execution
- `dataclasses` - Data structures

## See Also

- [Core README](../README.md) - Architecture overview
- [FSM Module](../fsm/README.md) - Swarm states
- [Routing Module](../routing/README.md) - Model selection
- [Hybrid Swarm Docs](../../docs/HYBRID_SWARM.md) - Detailed guide
