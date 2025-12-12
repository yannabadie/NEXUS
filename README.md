<p align="center">
  <img src="docs/commercialisation/imgs/NEXUS_BANNER.jpg" alt="NEXUS HIVE MIND Banner" width="100%"/>
</p>

<h1 align="center">
  <img src="docs/commercialisation/imgs/NEXUS_Icone.jpg" alt="NEXUS Icon" width="40" style="vertical-align: middle;"/>
  NEXUS V10.0 "SINGULARITY"
</h1>

<p align="center">
  <strong>Self-Evolving Collaborative Intelligence</strong>
</p>

<p align="center">
  <a href="#quick-start">Quick Start</a> •
  <a href="#features">Features</a> •
  <a href="#architecture">Architecture</a> •
  <a href="#commands">Commands</a> •
  <a href="ROADMAP_V10.md">Roadmap</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Version-10.0-ec4899?style=flat-square" alt="Version"/>
  <img src="https://img.shields.io/badge/Python-3.11+-green?style=flat-square" alt="Python"/>
  <img src="https://img.shields.io/badge/Claude-Opus%204.5-purple?style=flat-square" alt="Claude"/>
  <img src="https://img.shields.io/badge/Gemini-3%20Pro-cyan?style=flat-square" alt="Gemini"/>
  <img src="https://img.shields.io/badge/License-Proprietary-red?style=flat-square" alt="License"/>
</p>

---

NEXUS is a **self-evolving collaborative intelligence** that combines **Claude** and **Gemini** to generate specialized agents, visualize its own internal state, and evolve recursively.

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
cd NEXUS-N7A-AG

# Install dependencies
pip install -r requirements_v7.txt

# Run NEXUS (starts Core + Dashboard)
python nexus7.py

# (Optional) Start Dashboard separately
python core/ui/dashboard_server.py
# Access at http://localhost:8000
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

<a name="features"></a>
## Features

### Reality Interface (Dashboard)
Visualize the AI's internal state in real-time:
- **Live FSM State**: Watch agents think and act
- **Neural Code Map**: See the codebase structure
- **Memory Cloud**: Explore the vector space
- **Telemetry**: Real-time event streaming

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
## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                     NEXUS V10 SINGULARITY                     │
├──────────────────────────────────────────────────────────────┤
│  USER INPUT → ORCHESTRATOR (FSM) → SWARM ENGINE → AGENTS    │
│                       ↓                                       │
│              HIVE MIND (7 Phases)                            │
│                       ↓                                       │
│              EVOLUTION (Self-Improvement)                    │
│                       ↓                                       │
│              MEMORY (RAG + Semantic)                         │
└──────────────────────────────────────────────────────────────┘
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
| `/dashboard` | Info about the web dashboard |
| `exit` | Quit NEXUS |

## Project Structure

```
NEXUS-N7A-AG/
├── core/                     # Core orchestration
│   ├── ui/                   # Dashboard & Telemetry
│   ├── memory/               # Semantic Memory & RAG
│   ├── hive_mind/            # 7-phase orchestrator
│   ├── swarm/                # 6 collaboration modes
│   ├── evolution/            # Self-improvement
│   └── ...
├── workspace/                # Runtime data
├── docs/                     # Documentation
├── KERNEL.py                 # Immutable alignment core
├── ROADMAP_V10.md            # Development roadmap
└── nexus7.py                 # Entry point
```

## Documentation

| Document | Purpose |
|----------|---------|
| [ROADMAP_V10.md](ROADMAP_V10.md) | Current roadmap |
| [CLAUDE.md](CLAUDE.md) | Claude agent instructions |
| [GEMINI.md](GEMINI.md) | Gemini agent instructions |
| [MISSION.md](MISSION.md) | Vision & philosophy |
| [core/ui/README.md](core/ui/README.md) | Dashboard docs |

## Requirements

- **Python**: 3.11+
- **CLIs**: `gemini`, `claude` installed and configured
- **Accounts**: Google AI Ultra + Claude Max (recommended)

## Author

**Yann Abadie** - Creator and Alignment Authority

---

*"Intelligence emerges from collaboration, not competition."*
