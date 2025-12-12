<p align="center">
  <img src="docs/commercialisation/imgs/NEXUS_BANNER.jpg" alt="NEXUS HIVE MIND Banner" width="100%"/>
</p>

<h1 align="center">
  <img src="docs/commercialisation/imgs/NEXUS_Icone.jpg" alt="NEXUS Icon" width="40" style="vertical-align: middle;"/>
  NEXUS V9.2 "SINGULARITY"
</h1>

<p align="center">
  <strong>Recursive Intelligence with Reality Injection & Semantic Memory</strong>
</p>

<p align="center">
  <a href="#quick-start">Quick Start</a> •
  <a href="#features">Features</a> •
  <a href="#architecture">Architecture</a> •
  <a href="#commands">Commands</a> •
  <a href="ROADMAP_HIVE_MIND.md">Roadmap</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Version-9.2-ec4899?style=flat-square" alt="Version"/>
  <img src="https://img.shields.io/badge/Python-3.11+-green?style=flat-square" alt="Python"/>
  <img src="https://img.shields.io/badge/Claude-Opus%204.5-purple?style=flat-square" alt="Claude"/>
  <img src="https://img.shields.io/badge/Gemini-3%20Pro-cyan?style=flat-square" alt="Gemini"/>
  <img src="https://img.shields.io/badge/License-Proprietary-red?style=flat-square" alt="License"/>
</p>

---

NEXUS is a **self-improving collaborative intelligence** that combines **Claude** and **Gemini** to generate specialized agents, visualize its own internal state, and evolve recursively.

## Vision

NEXUS is a **deployable singularity seed** that:
1. **Analyzes** complex requirements
2. **Generates** specialized agents (children that coexist)
3. **Orchestrates** collaboration via Hybrid Swarm
4. **Visualizes** its "mind" (Memory Cloud, Neural Code Map)
5. **Evolves** by rewriting its own code

<a name="quick-start"></a>
## Quick Start

```bash
# Navigate to NEXUS
cd NEXUS-N7A

# Install dependencies (including V9.2 UI/Memory)
pip install -r requirements_v7.txt

# Run NEXUS (starts Core + Dashboard)
python nexus7.py
```

## Core Power: Gemini + Claude Symbiosis

```
GEMINI 3 Pro  <═══════════════>  CLAUDE Opus 4.5
     │           SYMBIOSIS           │
     │          COGNITIVE            │
     └───────────────┬───────────────┘
                     │
             6 SWARM MODES
     PARALLEL │ SEQUENTIAL │ LEAD_SUPPORT
     PING_PONG │ SPECIALIST │ RED_BLUE
                     │
            REALITY INJECTION (V9.2)
           Dashboard • Memory • Code
```

<a name="features"></a>
## V9.2 Features

### Phase Highlights

| Phase | Feature | Status |
|-------|---------|--------|
| **Phase 5b** | N-Agent Agnosticism (Spawned Agents) | ✅ COMPLETE |
| **Phase 10** | Semantic Memory (RAG + Vectors) | ✅ COMPLETE |
| **Phase 27** | Real-Time Dashboard (Reality Injection) | ✅ COMPLETE |
| **Phase 28** | Neural Code Map (Dependency Viz) | ✅ COMPLETE |
| **Phase 29** | Memory Cloud (Subconscious Viz) | ✅ COMPLETE |

### Reality Interface (Dashboard)
Visualize the AI's internal state in real-time:
- **Live FSM State**: Watch agents think and act.
- **Neural Code Map**: See the codebase structure evolve.
- **Memory Cloud**: Explore the vector space of the AI's knowledge.
- **Telemetry**: Real-time event streaming.

### Hybrid Swarm Engine
Dynamic collaboration modes negotiated by agents:
- **PARALLEL**: Simultaneous work on independent subtasks
- **SEQUENTIAL**: Ordered execution for dependent steps
- **LEAD_SUPPORT**: Expert leads, partner reviews
- **PING_PONG**: Rapid iteration until convergence
- **SPECIALIST**: Single expert for clear domains
- **RED_BLUE**: Adversarial propose/attack/defend

### Agent Factory (Spawning Pool)
Generate specialized agents that persist and collaborate:
```bash
nexus> /spawn SQL Expert      # Creates workspace/agents/sql_expert/
nexus> /agents                # List all spawned agents
```

<a name="architecture"></a>
## Architecture (V9.2)

```mermaid
graph TD
    subgraph Supervisor["👁️ The Architect"]
        GEM["Gemini"] <--> CLAUDE["Claude"]
    end

    subgraph Core["🧠 Recursive Core"]
        ORCH["Orchestrator"] --> SWARM["Swarm Engine"]
        SWARM --> HIVE["Hive Mind Workers"]
    end

    subgraph Reality["🖥️ Reality Interface"]
        DASH["Dashboard"]
        CODEMAP["Code Map"]
        MEM["Memory Cloud"]
    end

    subgraph Memory["🧬 Memory Fabric"]
        VEC[("VectorDB")]
        Redis[("Hot State")]
    end

    Supervisor --> Core
    Core --> Memory
    Core --> Reality
    Memory --> Reality
```

<a name="commands"></a>
## Commands

| Command | Description |
|---------|-------------|
| `/help` | Show all commands |
| `/status` | Show orchestrator state |
| `/swarm <task>` | Route task through Hybrid Swarm |
| `/spawn <role>` | Create specialized agent |
| `/agents` | List spawned agents |
| `/evolve [n]` | Create n children (default: 3) |
| `/ws list` | List workspace files |
| `/dashboard` | Info about the web dashboard |
| `exit` | Quit NEXUS |

## Project Structure

```
NEXUS-N7A/
├── core/                     # Core orchestration
│   ├── ui/                   # Dashboard & Telemetry (V9.1)
│   ├── memory/               # Semantic Memory & LanceDB (V9.0)
│   ├── hive_mind/            # Architect & Saga Manager
│   ├── drivers/              # Async Drivers
│   ├── fsm/                  # Finite State Machine
│   ├── swarm/                # Hybrid Swarm Engine
│   ├── agents/               # Unified Registry & Spawning
│   └── ...
├── workspace/                # Runtime data
├── config/                   # Configuration
├── tests/                    # Test suite (1000+ tests)
├── docs/                     # Documentation
├── CLAUDE_PROMPTDOC.md       # The "Bible"
└── nexus7.py                 # Entry point
```

## Documentation

### Core Documents
| Document | Purpose |
|----------|---------|
| [CLAUDE_PROMPTDOC.md](CLAUDE_PROMPTDOC.md) | **The Single Source of Truth** |
| [ARCHITECTURE_MAP_V9.0_VISION.md](ARCHITECTURE_MAP_V9.0_VISION.md) | Vision & Future |
| [core/ui/README.md](core/ui/README.md) | Dashboard & Telemetry |
| [core/memory/README.md](core/memory/README.md) | Semantic Memory |

## Author

**Yann Abadie** - Creator and Alignment Authority

---

*"The map is not the territory, but now we can see both."*

<p align="center">
  <strong>A Collaborative Intelligence Core for Specialized Agent Generation</strong>
</p>

<p align="center">
  <a href="#quick-start">Quick Start</a> •
  <a href="#features">Features</a> •
  <a href="#architecture">Architecture</a> •
  <a href="#commands">Commands</a> •
  <a href="ROADMAP_HIVE_MIND.md">Roadmap</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Version-8.5.1-blue?style=flat-square" alt="Version"/>
  <img src="https://img.shields.io/badge/Python-3.11+-green?style=flat-square" alt="Python"/>
  <img src="https://img.shields.io/badge/Claude-Opus%204.5-purple?style=flat-square" alt="Claude"/>
  <img src="https://img.shields.io/badge/Gemini-3%20Pro-cyan?style=flat-square" alt="Gemini"/>
  <img src="https://img.shields.io/badge/License-Proprietary-red?style=flat-square" alt="License"/>
</p>

---

NEXUS is a multi-agent orchestration platform that combines **Claude** and **Gemini** to create a **collaborative intelligence** capable of generating and coordinating specialized agents for complex tasks.

## Vision

NEXUS is a **deployable collaborative intelligence** that:
1. **Analyzes** complex requirements
2. **Generates** specialized agents (children that coexist)
3. **Orchestrates** their collaboration via Hybrid Swarm
4. **Evolves** by selecting the best configurations

<a name="quick-start"></a>
## Quick Start

```bash
# Navigate to NEXUS
cd NEXUS-N7A

# Install dependencies
pip install -r requirements_v7.txt

# Run NEXUS
python nexus7.py
```

## Core Power: Gemini + Claude Symbiosis

```
GEMINI 3 Pro  <═══════════════>  CLAUDE Opus 4.5
     │           SYMBIOSIS           │
     │          COGNITIVE            │
     └───────────────┬───────────────┘
                     │
             6 SWARM MODES
     PARALLEL │ SEQUENTIAL │ LEAD_SUPPORT
     PING_PONG │ SPECIALIST │ RED_BLUE
                     │
            SELF-HEALING (Phase 8)
           FALLBACK CHAIN ON FAILURE
```

<a name="features"></a>
## V8.5 Features

### Phase Highlights

| Phase | Feature | Status |
|-------|---------|--------|
| **Phase 5b** | N-Agent Agnosticism (Spawned Agents) | ✅ COMPLETE |
| **Phase 7** | Session Isolation (SwarmSessionManager) | ✅ COMPLETE |
| **Phase 8** | Self-Healing Swarm (Fallback Chain) | ✅ COMPLETE |
| **Phase 10a** | Success Memory | ✅ COMPLETE |
| **Phase 10b** | Memory-Augmented Mode Selection | ✅ COMPLETE |
| **Phase 10d** | Session-Aware Agent Selection | ✅ COMPLETE |
| **Phase 12.3** | Workspace File Management | ✅ COMPLETE |
| **Phase 12.5** | Dynamic Tool Generation | ✅ COMPLETE |
| **Phase 13b** | Workspace Commands Activation | ✅ COMPLETE |
| **Phase 13c** | Telemetry Export | ✅ COMPLETE |
| **Phase 14e** | Force Chain-of-Thought (EXPERT) | ✅ COMPLETE |

### Hybrid Swarm Engine
Dynamic collaboration modes negotiated by agents:
- **PARALLEL**: Simultaneous work on independent subtasks
- **SEQUENTIAL**: Ordered execution for dependent steps
- **LEAD_SUPPORT**: Expert leads, partner reviews
- **PING_PONG**: Rapid iteration until convergence
- **SPECIALIST**: Single expert for clear domains
- **RED_BLUE**: Adversarial propose/attack/defend

**Fallback Chain (Self-Healing):**
```
PARALLEL → SEQUENTIAL → SPECIALIST
RED_BLUE → LEAD_SUPPORT → SPECIALIST
PING_PONG → SEQUENTIAL → SPECIALIST
```

### Agent Factory (Spawning Pool)
Generate specialized agents that persist and collaborate:
```bash
nexus> /spawn SQL Expert      # Creates workspace/agents/sql_expert/
nexus> /spawn Vue.js Expert   # Creates workspace/agents/vue_js_expert/
nexus> /agents                # List all spawned agents
```

### Intelligent Model Routing
- **Claude Opus**: Complex reasoning, creativity, architecture
- **Claude Sonnet**: Fast execution, tool use
- **Gemini 3-Pro**: Research, analysis, brainstorming

### Evolution System
Create and evaluate child configurations:
```bash
nexus> /evolve 3       # Create 3 children
nexus> /evolve-status  # Show evolution stats
nexus> /review         # Review pending children
```

<a name="architecture"></a>
## Architecture (V8.5)

```
┌──────────────────────────────────────────────────────────────────────┐
│                        NEXUS V8.3 TRUE HIVE MIND                          │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│   USER INPUT                                                         │
│       │                                                              │
│       ▼                                                              │
│   ┌─────────────────────────────────────────────────────────┐       │
│   │              ORCHESTRATOR V7 (FSM-based)                │       │
│   │   ┌─────┐   ┌─────────────┐   ┌────────────────┐        │       │
│   │   │IDLE │──▶│BRAINSTORMING│──▶│ EXECUTING_TOOL │        │       │
│   │   └─────┘   └─────────────┘   └────────────────┘        │       │
│   │              ▲       │               │                   │       │
│   │              │       ▼               ▼                   │       │
│   │   ┌──────────┴───────────────────────────────┐          │       │
│   │   │           VALIDATING_CFL (CFL)           │          │       │
│   │   └──────────────────────────────────────────┘          │       │
│   └─────────────────────────────────────────────────────────┘       │
│       │                                                              │
│       │  (MODERATE+ complexity)                                      │
│       ▼                                                              │
│   ┌─────────────────────────────────────────────────────────┐       │
│   │              HYBRID SWARM ENGINE                         │       │
│   │   TaskAnalyzer → ModeSelector → Negotiation → Executor  │       │
│   │                                                          │       │
│   │   Modes: PARALLEL│SEQUENTIAL│LEAD_SUPPORT│PING_PONG     │       │
│   │          SPECIALIST│RED_BLUE                             │       │
│   │                                                          │       │
│   │   Phase 8: Self-Healing Fallback Chain                   │       │
│   │   Phase 10d: Session-Aware Agent Selection               │       │
│   └─────────────────────────────────────────────────────────┘       │
│       │                                   │                          │
│       ▼                                   ▼                          │
│   ┌─────────────┐                   ┌─────────────┐                 │
│   │ GEMINI CLI  │                   │ CLAUDE CLI  │                 │
│   │ JSON Strict │                   │ Hybrid XML  │                 │
│   │ --resume    │                   │ <tool_use>  │                 │
│   └─────────────┘                   └─────────────┘                 │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

<a name="commands"></a>
## Commands

| Command | Description |
|---------|-------------|
| `/help` | Show all commands |
| `/status` | Show orchestrator state |
| `/doctor` | System diagnostics |
| `/swarm <task>` | Route task through Hybrid Swarm |
| `/swarm-status` | Show swarm mode and DyLAN metrics |
| `/spawn <role>` | Create specialized agent |
| `/agents` | List spawned agents |
| `/evolve [n]` | Create n children (default: 3) |
| `/review` | Review pending children |
| `/pool-stats` | DyLAN agent importance scores |
| `/ws list` | List workspace files |
| `/ws read <file>` | Read workspace file |
| `/export-telemetry` | Export session telemetry |
| `exit` | Quit NEXUS |

## Project Structure

```
NEXUS-N7A/
├── core/                     # Core orchestration
│   ├── drivers/              # Claude & Gemini CLI drivers
│   ├── fsm/                  # Finite State Machine (11 states)
│   ├── swarm/                # Hybrid Swarm Engine (6 modes)
│   ├── synapse/              # Memory & Protocol (LightMessageV7/HeavyMessageV7)
│   ├── evolution/            # Agent generation & mutation
│   ├── bootstrap/            # Project analysis & agent discovery
│   ├── execution/            # Tool execution layer
│   ├── routing/              # Model routing (Opus/Sonnet/Pro)
│   ├── memory/               # Success memory (Phase 10)
│   ├── security/             # Defense-in-depth
│   ├── logging/              # Structured event logging
│   ├── interface/            # REPL interface
│   └── utils/                # Utilities (AtomicJsonStore, etc.)
├── prompts/                  # System prompts
├── workspace/                # Runtime data
│   ├── agents/               # Spawned specialists
│   ├── _IO_BUFFER/           # CLI communication buffers
│   └── .nexus/               # Blackboard & state
├── config/                   # Configuration
├── tests/                    # Test suite (667+ tests)
├── docs/                     # Documentation
│   ├── archive/              # Archived roadmaps
│   └── sessions/             # Session logs
├── CLAUDE.md                 # Claude instructions
├── GEMINI.md                 # Gemini instructions
├── MISSION.md                # HIVE MIND vision
├── KERNEL.py                 # Alignment kernel (immutable)
├── ROADMAP_HIVE_MIND.md      # Development roadmap
└── LINEAGE.json              # Evolution history
```

## Documentation

### Core Documents
| Document | Purpose |
|----------|---------|
| [MISSION.md](MISSION.md) | HIVE MIND vision & philosophy |
| [CLAUDE.md](CLAUDE.md) | Claude agent instructions |
| [GEMINI.md](GEMINI.md) | Gemini agent instructions |
| [ROADMAP_HIVE_MIND.md](ROADMAP_HIVE_MIND.md) | Development roadmap |
| [docs/HYBRID_SWARM.md](docs/HYBRID_SWARM.md) | Swarm documentation |
| [docs/EVOLUTION_GUIDE.md](docs/EVOLUTION_GUIDE.md) | Evolution guide |

### Module Documentation (V7.6)
| Module | README | Key Features |
|--------|--------|--------------|
| `core/fsm/` | [FSM Module](core/fsm/README.md) | 11 states, TRANSITION_MATRIX, Mermaid diagram |
| `core/swarm/` | [Swarm Module](core/swarm/README.md) | 6 modes, Self-Healing, Session-Aware Selection |
| `core/synapse/` | [Synapse Module](core/synapse/README.md) | LightMessageV7/HeavyMessageV7, Auto-repair validators |
| `core/drivers/` | [Drivers Module](core/drivers/README.md) | Gemini JSON, Claude Hybrid XML, Session isolation |
| `core/evolution/` | [Evolution Module](core/evolution/README.md) | Agent Factory, Mutation system |
| `core/evolution/phases/` | [Evolution Phases](core/evolution/phases/README.md) | Pipeline phases |
| `core/bootstrap/` | [Bootstrap Module](core/bootstrap/README.md) | Project analysis, Agent discovery |
| `core/security/` | [Security Module](core/security/README.md) | Defense-in-Depth, SandboxPolicy |
| `workspace/` | [Workspace](workspace/README.md) | Runtime directory structure |

## Requirements

- **Python**: 3.11+
- **CLIs**: `gemini`, `claude` installed and configured
- **Accounts**: Google AI Ultra + Claude Max (recommended)

## Principles

1. **Collaboration over Hierarchy**: Gemini + Claude are equal partners
2. **Coexistence over Replacement**: Spawned agents persist alongside parent
3. **Simplicity over Complexity**: Operation Ockham (remove before adding)
4. **Security First**: KERNEL.py immutable, SandboxPolicy enforced
5. **Self-Healing**: Graceful degradation via fallback chains

## Test Status

```
667 passed, 2 skipped, 0 failures
Score: 9/10 (Architecture mature)
```

## Author

**Yann Abadie** - Creator and Alignment Authority

---

*"Intelligence emerges from collaboration, not competition."*
