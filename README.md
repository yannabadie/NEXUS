# NEXUS HIVE MIND

<div align="center">

```
    _   __   ______  __  __  __  __   _____
   / | / /  / ____/ / / / / / / / /  / ___/
  /  |/ /  / __/   / /_/ / / / / /   \__ \
 / /|  /  / /___  / __  / / /_/ /   ___/ /
/_/ |_/  /_____/ /_/ /_/  \____/   /____/

       COLLABORATIVE INTELLIGENCE CORE
              V12.4 "COGNITIVE BOOST"
```

[![Version](https://img.shields.io/badge/version-12.4-blue.svg)](CHANGELOG.md)
[![Python](https://img.shields.io/badge/python-3.11+-green.svg)](https://python.org)
[![Claude](https://img.shields.io/badge/Claude-Opus_4.5-orange.svg)](https://anthropic.com)
[![Gemini](https://img.shields.io/badge/Gemini-3_Pro-blue.svg)](https://ai.google.dev)
[![License](https://img.shields.io/badge/license-MIT-purple.svg)](LICENSE)

**Version**: 12.4.0 | **Status**: Active | **Last Updated**: 2025-12-22
**Maintainer**: Yann Abadie | **Branch**: NX
**Focus**: Product Polish, Generative UI, Robustness

**NEXUS is a deployable collaborative intelligence that specializes based on context.**

</div>

---

## Vision

> **"Two AIs working together surpass what each can do alone."**

NEXUS is not just a tool - it's a **deployable intelligence core** designed to be cloned into any project and become its dedicated AI collaborator.

```
┌─────────────────────────────────────────────────────────────┐
│                    NEXUS CORE POWER                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│    ┌─────────────┐              ┌───────────────────────────┐            │
│    │   GEMINI    │◄────────────►│  CO-PILOT (DeepSeek/Claude)│           │
│    │   Primary   │  Collaborate │  DeepSeek-R1 / Claude 3.5  │           │
│    └─────────────┘              └───────────────────────────┘            │
│           │                            │                    │
│           └──────────┬─────────────────┘                    │
│                      ▼                                      │
│           ┌─────────────────────┐                          │
│           │  COLLABORATIVE      │                          │
│           │  INTELLIGENCE       │                          │
│           │  > Analyze          │                          │
│           │  > Specialize       │                          │
│           │  > Execute          │                          │
│           │  > Evolve           │                          │
│           └─────────────────────┘                          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Quick Start

```bash
# Clone NEXUS into your project
git clone https://github.com/your-org/nexus.git

# Install dependencies
pip install -r requirements.txt

# Launch with Docker (Recommended)
docker compose up --build

# Launch Locally (Python)
pip install -r requirements.txt
python nexus7.py
```

```
nexus7> /status
[System Online]
  > Primary: Gemini-3-Pro (Online)
  > Co-Pilot: DeepSeek-R1 (Online)
```

```
nexus7> Hello! Analyze this project and help me understand it.
[NEXUS collaborates between Gemini and Claude to analyze your codebase]
```

---

## V12.4 Features

### COGNITIVE BOOST (Current)

| Component | Description |
|-----------|-------------|
| **StagnationPredictor** | Detects task stagnation (thresholds 0.15/0.25/0.40) with auto-recovery |
| **HybridBackend RRF** | Reciprocal Rank Fusion (Dense + BM25S) for +15% RAG recall |
| **MemoryCoordinator** | Adaptive domain weights with EMA learning |
| **OutputGuard DialogueAct** | Dialogue act classification to reduce false positives |
| **SSRF Protection** | OWASP blocklist for web_fetch security |

### Previous Releases

| Version | Codename | Highlights |
|---------|----------|------------|
| V12.3 | SCALE-OUT | Multi-instance ready (Redis, distributed locks, Prometheus) |
| V12.2 | IRONCLAD | Security foundation (RBAC, AuditLogger, IntegrityMonitor) |
| V12.1 | RETINA | Production cockpit (CEREBRO dashboard, OpsView) |
| V12.0 | HIVE MIND | 7-phase pipeline, SwarmBridge delegation |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         NEXUS V12.4 ARCHITECTURE                    │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐           │
│  │    USER     │────►│    REPL     │────►│    FSM      │           │
│  │   INPUT     │     │  Interface  │     │ Orchestrator│           │
│  └─────────────┘     └─────────────┘     └──────┬──────┘           │
│                                                  │                   │
│                    ┌─────────────────────────────┼───────────────┐   │
│                    │              HIVE MIND      ▼               │   │
│                    │  ┌──────────────────────────────────────┐   │   │
│                    │  │ Phase 1: ANALYSIS      (Independent) │   │   │
│                    │  │ Phase 2: DEBATE        (If needed)   │   │   │
│                    │  │ Phase 3: ARCHITECTURE  (Plan)        │   │   │
│                    │  │ Phase 4: EXECUTION     (SwarmBridge) │──►│   │
│                    │  │ Phase 5: DIAGNOSIS     (On failure)  │   │   │
│                    │  │ Phase 6: CONSOLIDATION (Merge)       │   │   │
│                    │  │ Phase 7: COMPLETION    (Final)       │   │   │
│                    │  └──────────────────────────────────────┘   │   │
│                    └─────────────────────────────────────────────┘   │
│                                                  │                   │
│                    ┌─────────────────────────────▼───────────────┐   │
│                    │              SWARM ENGINE                   │   │
│                    │  ┌──────────┐  ┌──────────┐  ┌──────────┐   │   │
│                    │  │ PARALLEL │  │PING_PONG │  │ RED_BLUE │   │   │
│                    │  └──────────┘  └──────────┘  └──────────┘   │   │
│                    │  ┌──────────┐  ┌──────────┐  ┌──────────┐   │   │
│                    │  │SEQUENTIAL│  │LEAD_SUPP │  │SPECIALIST│   │   │
│                    │  └──────────┘  └──────────┘  └──────────┘   │   │
│                    └─────────────────────────────────────────────┘   │
│                                                  │                   │
│  ┌─────────────┐     ┌─────────────┐     ┌──────▼──────┐           │
│  │   CEREBRO   │◄────│   MEMORY    │◄────│   TOOLS     │           │
│  │  Dashboard  │     │ RAG+Success │     │  21+ Tools  │           │
│  └─────────────┘     └─────────────┘     └─────────────┘           │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Swarm Engine - 6 Collaboration Modes

| Mode | Description | Use Case |
|------|-------------|----------|
| **PARALLEL** | Both agents work simultaneously, merge results | Independent subtasks |
| **SEQUENTIAL** | Ordered execution (first -> second) | Dependent steps |
| **LEAD_SUPPORT** | Lead drives, support reviews/assists | Complex implementation |
| **PING_PONG** | Rapid alternation until convergence | Iterative refinement |
| **SPECIALIST** | Single expert handles all | Clear domain expertise |
| **RED_BLUE** | Adversarial propose/attack/defend | Security, edge cases |

```bash
nexus7> /swarm parallel "Analyze auth.py and security.py simultaneously"
nexus7> /swarm red_blue "Review this PR for security vulnerabilities"
```

---

## Agent Factory

NEXUS can spawn specialized agents that coexist and collaborate:

```bash
nexus7> /spawn security_expert "Expert in OWASP Top 10 and secure coding"
[Creating agent: security_expert]
[Agent spawned in workspace/agents/security_expert/]

nexus7> /spawn db_specialist "PostgreSQL and query optimization expert"
[Creating agent: db_specialist]
[Agent spawned in workspace/agents/db_specialist/]

nexus7> /list-agents
Agents:
  - security_expert (active)
  - db_specialist (active)
```

---

## Commands

| Command | Description |
|---------|-------------|
| `/help` | Show all commands |
| `/status` | System status |
| `/reset` | Reset conversation |
| `/swarm <mode> <task>` | Explicit swarm mode |
| `/spawn <name> <mission>` | Create specialized agent |
| `/evolve` | Trigger evolution cycle |
| `/specialize <mission>` | Create project spinoff |
| `/learn <path>` | Add to RAG memory |
| `/forget <path>` | Remove from RAG memory |
| `/rag <query>` | Direct RAG search |
| `/memory-status` | RAG statistics |
| `/cerebro start` | Launch CEREBRO dashboard |
| `/opsview` | Production metrics cockpit |
| `/metrics` | Export Prometheus metrics |
| `/audit` | Run security audit |

---

## Project Structure

```
NEXUS/
├── core/                        # Core orchestration
│   ├── orchestration_v7.py      # Main FSM orchestrator
│   ├── drivers/                 # Gemini & Claude drivers
│   ├── execution/               # Tool execution layer
│   ├── fsm/                     # State machine (11 states)
│   ├── hive_mind/               # 7-phase pipeline
│   ├── swarm/                   # 6 collaboration modes
│   ├── memory/                  # RAG + SuccessMemory
│   ├── security/                # 7 security layers
│   ├── evolution/               # Agent spawning
│   └── api/                     # REST API (CEREBRO)
├── interface/                   # User interfaces
│   ├── ui/cerebro/              # React dashboard
│   └── cli/                     # REPL components
├── prompts/                     # System prompts
├── workspace/                   # Runtime data
│   ├── agents/                  # Spawned agents
│   ├── logs/                    # Event logs
│   └── .nexus/                  # RAG database
├── tests/                       # 1200+ tests
├── docs/                        # Documentation
├── nexus7.py                    # Entry point
├── KERNEL.py                    # Immutable alignment
└── MISSION.md                   # Project mission
```

---

## Security - 7 Layers

| Layer | Component | Function |
|-------|-----------|----------|
| 1 | **KERNEL.py** | Immutable alignment rules |
| 2 | **InputGuard** | Input validation & sanitization |
| 3 | **OutputGuard** | Output filtering (DialogueAct V12.4) |
| 4 | **ExecutionPolicy** | Tool permission enforcement |
| 5 | **RBAC** | Role-based access control (V12.2) |
| 6 | **AuditLogger** | Complete action logging (V12.2) |
| 7 | **IntegrityMonitor** | Critical file hash verification (V12.2) |

Additional protections:
- **SSRF Blocklist** (V12.4): OWASP-compliant for web_fetch
- **Spotlighting Defense**: RAG context injection protection

---

## Memory System

```
┌─────────────────────────────────────────────────────────────┐
│                    NEXUS RAG SYSTEM                         │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐    ┌─────────────────┐                │
│  │  MiniLM-L6-v2   │    │    BM25S        │                │
│  │  (Dense 384d)   │    │   (Sparse)      │                │
│  └────────┬────────┘    └────────┬────────┘                │
│           │                      │                          │
│           └──────────┬───────────┘                          │
│                      ▼                                      │
│           ┌─────────────────────┐                          │
│           │ HybridBackend RRF   │ +15% recall              │
│           │ (Reciprocal Rank    │                          │
│           │  Fusion)            │                          │
│           └──────────┬──────────┘                          │
│                      ▼                                      │
│           ┌─────────────────────┐                          │
│           │  MemoryCoordinator  │ Adaptive weights         │
│           └──────────┬──────────┘                          │
│                      ▼                                      │
│           ┌─────────────────────┐                          │
│           │     LanceDB         │ .nexus/lancedb/          │
│           └─────────────────────┘                          │
└─────────────────────────────────────────────────────────────┘
```

- **100% Local** after first model download (22MB)
- **No data leaves machine** - full privacy
- **Supports**: .py, .md, .txt, .yaml, .json, .toml + more in V13

---

## Requirements

- Python 3.13+
- API Keys: `GOOGLE_API_KEY`, `DEEPSEEK_API_KEY` (or `ANTHROPIC_API_KEY`)
- Optional: Redis 7 (for Swarm State), Docker (for containerization)

### Configuration (.env)
```bash
# Core
GOOGLE_API_KEY=...
DEEPSEEK_API_KEY=...

# Co-Pilot Mode (DeepSeek R1 or Claude)
NEXUS_CO_PILOT=DEEPSEEK
NEXUS_DEEPSEEK_MODEL=deepseek-reasoner 
```

```bash
pip install -r requirements.txt
```

---

## Test Status

```
Tests: 1200+
Coverage: ~85%
Critical paths: 100% covered
```

```bash
pytest tests/ -v
pytest tests/ --cov=core --cov-report=html
```

---

## Contributing

1. Read [MISSION.md](MISSION.md) to understand the vision
2. Check [ROADMAP.md](ROADMAP.md) for current priorities
3. Follow code style in [CLAUDE.md](CLAUDE.md)
4. All PRs require tests

---

## License

MIT License - See [LICENSE](LICENSE) for details.

---

<div align="center">

**NEXUS V12.4 "COGNITIVE BOOST"**

*Collaborative Intelligence for Real-World Problems*

Built with Gemini 3 Pro + Claude Opus 4.5

</div>
