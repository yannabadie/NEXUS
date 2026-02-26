# NEXUS Core Module

## Synopsis

The **core** module is the heart of NEXUS V12.4 "COGNITIVE BOOST" - a multi-agent orchestration system enabling collaborative intelligence between Gemini and Claude. It implements a persistent FSM (Finite State Machine) orchestrator that coordinates agent interactions through three orchestration layers: FSM (low-level state management), HiveMind (7-phase strategic pipeline), and Swarm Engine (6 collaboration modes).

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         NEXUS CORE ARCHITECTURE                          │
├─────────────────────────────────────────────────────────────────────────┤
│  ┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐  │
│  │   User Input     │───▶│   FSM Layer      │───▶│   Complexity     │  │
│  │   (REPL/API)     │    │   (12 States)    │    │   Assessment     │  │
│  └──────────────────┘    └────────┬─────────┘    └────────┬─────────┘  │
│                                   │                        │            │
│           ┌───────────────────────┼────────────────────────┘            │
│           ▼                       ▼                                     │
│  ┌──────────────────┐    ┌──────────────────┐                          │
│  │   BRAINSTORMING  │    │   HiveMind       │  MODERATE+ Complexity    │
│  │   (Simple Tasks) │    │   (7 Phases)     │                          │
│  └────────┬─────────┘    └────────┬─────────┘                          │
│           │                       │                                     │
│           │              ┌────────▼─────────┐                          │
│           │              │   SwarmBridge    │  Phase 4 Delegation      │
│           │              └────────┬─────────┘                          │
│           │                       │                                     │
│           └───────────┬───────────┘                                     │
│                       ▼                                                 │
│           ┌──────────────────────┐                                     │
│           │    Swarm Engine      │  6 Collaboration Modes              │
│           │    (Negotiation)     │                                     │
│           └──────────┬───────────┘                                     │
│                      │                                                  │
│           ┌──────────▼───────────┐                                     │
│           │   Agent Drivers      │  Gemini + Claude                    │
│           │   (JSON/XML)         │                                     │
│           └──────────────────────┘                                     │
└─────────────────────────────────────────────────────────────────────────┘
```

## Component Map

| Component | Path | Purpose |
|-----------|------|---------|
| **OrchestratorV7** | `orchestration_v7.py` | Main FSM controller, persistent singleton |
| **ServiceFactory** | `factory.py` | Context-aware service instantiation |
| **NexusConfig** | `config.py` | Configuration management |
| **Constants** | `constants.py` | TIMEOUTS, RETRY_LIMITS, SAGA_LIMITS |

## Submodule Overview

| Module | Purpose | Key Exports |
|--------|---------|-------------|
| [drivers/](drivers/README.md) | LLM driver abstraction layer | `AsyncClaudeDriver`, `AsyncGeminiDriver`, `DriverProtocol` |
| [fsm/](fsm/README.md) | Finite State Machine components | `OrchestratorState`, `TaskExecutionContext`, `HealthStateMachine` |
| [hive_mind/](hive_mind/README.md) | 7-phase collaborative pipeline | `TrueHiveMind`, `HiveMindState`, `SwarmBridge` |
| [swarm/](swarm/README.md) | 6-mode collaboration engine | `HybridSwarmEngine`, `CollaborationMode`, `TaskAnalyzer` |
| [execution/](execution/README.md) | Tool execution layer | `ToolManager`, `AgentToolRegistry`, `ExecutionEngine` |
| [memory/](memory/README.md) | RAG + persistent memory | `ProjectMemory`, `SuccessMemory`, `Blackboard` |
| [synapse/](synapse/README.md) | Agent communication protocol | `LightMessageV7`, `HeavyMessageV7` |
| [security/](security/README.md) | Governance & sandboxing | `KERNEL`, `ExecutionPolicy`, `SandboxPolicy` |
| [routing/](routing/README.md) | Model routing intelligence | `ModelRouter`, task-based model selection |
| [evolution/](evolution/README.md) | Agent spawning & mutation | `EvolutionEngine`, specialization |
| [orchestration/](orchestration/README.md) | FSM handlers & invokers | `AgentInvoker`, state handlers |

## Three-Layer Orchestration

### Layer 1: FSM (12 States)
Low-level state machine managing basic orchestration flow:
- `IDLE` → `BRAINSTORMING` → `EXECUTING_TOOL` → `VALIDATING_CFL` → `IDLE`
- Special states: `SWARM_*`, `HIBERNATE`, `ERROR`, `PANIC`

### Layer 2: HiveMind (7 Phases)
High-level strategic pipeline for MODERATE+ complexity tasks:
1. **Analysis** - Independent analysis by both agents
2. **Debate** - Resolve disagreements through argumentation
3. **Architecture** - Design execution plan
4. **Execution** - Execute with monitoring (SwarmBridge delegation)
5. **Diagnosis** - Failure root cause analysis
6. **Retry** - Adaptive retry decision
7. **Consolidation** - Knowledge archival

### Layer 3: Swarm Engine (6 Modes)
Dynamic collaboration where agents negotiate optimal mode:
- `PARALLEL` - Simultaneous work, merge results
- `SEQUENTIAL` - Ordered execution
- `LEAD_SUPPORT` - 80% lead / 20% support
- `PING_PONG` - Rapid alternation
- `SPECIALIST` - Single expert
- `RED_BLUE` - Adversarial review

## Key Interfaces

### OrchestratorV7
```python
class OrchestratorV7:
    """Main persistent FSM controller. Created once at startup."""

    def process_turn(user_input: Optional[str]) -> Dict
    async def process_turn_async(user_input: Optional[str]) -> Dict
    def reset_to_idle(clear_task: bool = True)
    def get_system_status() -> Dict
```

### ServiceFactory
```python
# Context-aware service creation
from core import create_orchestrator

orch = create_orchestrator(
    workspace_path=Path("workspace"),
    config=config,
    gemini_info={"model": "gemini-3-pro-preview"},
    claude_info={"model": "claude-opus-4-6-20250116"}
)
```

## Complexity Routing

```
User Input → TaskAnalyzer → Complexity Assessment
                               │
    ┌──────────────────────────┼──────────────────────────┐
    │                          │                          │
 TRIVIAL               SIMPLE/MODERATE              COMPLEX/EXPERT
 Fast Path             Brainstorming                   HiveMind
 (regex)               + Swarm Auto                    7 Phases
```

## Dependencies

### Internal
- `core.fsm.*` - State machine
- `core.drivers.*` - LLM drivers
- `core.hive_mind.*` - Strategic pipeline
- `core.swarm.*` - Collaboration engine
- `core.memory.*` - RAG & persistence
- `core.execution.*` - Tool execution
- `core.security.*` - Governance

### External
- `pydantic` - Validation
- `tiktoken` - Token counting
- `python-dotenv` - Configuration
- Standard library (asyncio, pathlib, json)

## Entry Points

1. **REPL**: `nexus7.py` → Creates `OrchestratorV7`
2. **REST API**: `core/api/cerebro/` → Session-based orchestrator
3. **Commands**: `core/interface/commands/` → Invoke methods

## Configuration

```bash
# .env configuration
NEXUS_VERSION=12.4.0
NEXUS_CODENAME="COGNITIVE BOOST"
SWARM_AUTO_ROUTE=True
HIVE_MIND_ENABLED=True
```

## Version History

- **V7.0** - FSM Persistent architecture
- **V8.0** - TRUE HIVE MIND (7-phase pipeline)
- **V9.0** - Async-first drivers
- **V10.0** - PRISM multi-tenant
- **V11.0** - SYNCHROTRON abstraction layer
- **V12.0** - IRONCLAD security + RETINA monitoring
- **V12.4** - COGNITIVE BOOST (current)
