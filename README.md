# NEXUS V7.5 "HIVE MIND"

**A Collaborative Intelligence Core for Specialized Agent Generation**

NEXUS is a multi-agent orchestration platform that combines Claude and Gemini to create a **collaborative intelligence** capable of generating and coordinating specialized agents for complex tasks.

## Vision

NEXUS is not a tool toward ASI - it's a **deployable collaborative intelligence** that:
1. **Analyzes** complex requirements
2. **Generates** specialized agents (children that coexist)
3. **Orchestrates** their collaboration via Hybrid Swarm
4. **Evolves** by selecting the best configurations

## Quick Start

```bash
# Navigate to active version
cd NEXUS_V7_CHRYSALIS

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
```

## Key Features

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
| `exit` | Quit NEXUS |

## Project Structure

```
NEXUS-N7A/
├── core/                     # Core orchestration
│   ├── drivers/              # Claude & Gemini interfaces
│   ├── fsm/                  # Finite State Machine
│   ├── swarm/                # Hybrid Swarm Engine
│   ├── evolution/            # Agent generation
│   └── ...
├── prompts/                  # System prompts
├── workspace/                # Runtime data
│   └── agents/               # Spawned specialists
├── docs/                     # Documentation
│   └── archive/              # Archived roadmaps
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
| [docs/NEXUS_V7.5_AUDIT_REPORT.md](docs/NEXUS_V7.5_AUDIT_REPORT.md) | Architecture audit (CHRYSALIS-SYNC) |

### Module Documentation (V7.5)
| Module | README |
|--------|--------|
| core/evolution/ | [Evolution & Agent Factory](core/evolution/README.md) |
| core/evolution/phases/ | [Evolution Pipeline Phases](core/evolution/phases/README.md) |
| core/bootstrap/ | [Project Analysis & Agent Discovery](core/bootstrap/README.md) |
| core/swarm/ | [Hybrid Swarm Engine](core/swarm/README.md) |
| core/synapse/ | [Memory & Protocol](core/synapse/README.md) |
| core/security/ | [Defense-in-Depth](core/security/README.md) |
| workspace/ | [Runtime Directory](workspace/README.md) |

## Requirements

- **Python**: 3.11+
- **CLIs**: `gemini`, `claude` installed and configured
- **Accounts**: Google AI Ultra + Claude Max (recommended)

## Principles

1. **Collaboration over Hierarchy**: Gemini + Claude are equal partners
2. **Coexistence over Replacement**: Spawned agents persist alongside parent
3. **Simplicity over Complexity**: Operation Ockham (remove before adding)
4. **Security First**: KERNEL.py immutable, SandboxPolicy enforced

## Author

**Yann Abadie** - Creator and Alignment Authority

---

*"Intelligence emerges from collaboration, not competition."*
