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
[![Claude](https://img.shields.io/badge/Claude-Opus_4.6-orange.svg)](https://anthropic.com)
[![Gemini](https://img.shields.io/badge/Gemini-3_Pro-blue.svg)](https://ai.google.dev)
[![License](https://img.shields.io/badge/license-MIT-purple.svg)](LICENSE)

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
│    ┌─────────────┐              ┌─────────────┐            │
│    │   GEMINI    │◄────────────►│   CLAUDE    │            │
│    │   3 Pro     │  Collaborate │  Opus 4.6   │            │
│    └─────────────┘              └─────────────┘            │
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
# Clone NEXUS
git clone https://github.com/yannabadie/NEXUS.git
cd NEXUS
git checkout NX-CG

# Install dependencies
python -m pip install -r requirements.txt

# Verify + launch
python nexus7.py --verify
python nexus7.py
```

```
nexus7> Hello! Analyze this project and help me understand it.
[NEXUS collaborates between Gemini and Claude to analyze your codebase]
```

---

## Products (NX-CG)

### Flagship: Research CLI + Evidence Pack
Local-first research that turns a question into traceable artifacts.
```bash
python nexus_research.py "How does ProjectMemory index files?" --mode mock --path core/memory/project_memory.py
```
Outputs: `report.md`, `sources.json`, `trace.jsonl`, `reasoning_graph.mmd`, `metrics.json`, `manifest.sha256`

### Companion: MCP Server
MCP server exposing research + evidence pack generation.
```bash
python -m pip install mcp
python -m core.mcp.server
```

Release guide: `PRODUCTS/RELEASE.md`  
Demo scripts: `scripts/demo_flagship.ps1`, `scripts/demo_companion.ps1`

---

## V12.4 Features

### COGNITIVE BOOST (Current)

| Component | Description |
|-----------|-------------|
| **125+ New Modules** | Cross-domain observability, analytics, and performance tracking |
| **SDK Drivers** | Native Anthropic + Google GenAI SDKs with Prompt Caching |
| **Message Infrastructure** | Protocol, deduplicator, router, reliability tracker |
| **Cognitive Pipeline** | Phase coordination, consensus tracking, reasoning quality |
| **Security & Governance** | Event journal, access control, encryption, alignment journal |
| **StagnationPredictor** | Detects task stagnation with auto-recovery |
| **HybridBackend RRF** | Reciprocal Rank Fusion for +15% RAG recall |

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
│   ├── synapse/                 # Message protocol & reliability
│   ├── session/                 # Session management & analytics
│   ├── resilience/              # Resilience & recovery patterns
│   ├── reasoning/               # Reasoning quality & evaluation
│   ├── governance/              # Ethics & alignment tracking
│   ├── routing/                 # Model routing & optimization
│   ├── telemetry/               # Metrics, OTel, profiling
│   ├── bootstrap/               # Startup analytics
│   ├── events/                  # Event bus & analytics
│   ├── db/                      # Database & query tracking
│   ├── interaction/             # HITL & quality tracking
│   ├── mcp/                     # MCP client & discovery
│   ├── context/                 # Tenant context & audit
│   ├── meta/                    # System introspection
│   ├── skills/                  # Skill crystallization
│   └── api/                     # REST API (CEREBRO)
├── interface/                   # User interfaces
│   ├── ui/cerebro/              # React dashboard
│   └── cli/                     # REPL components
├── prompts/                     # System prompts
├── workspace/                   # Runtime data
│   ├── agents/                  # Spawned agents
│   ├── logs/                    # Event logs
│   └── .nexus/                  # RAG database
├── tests/                       # 2500+ tests
├── docs/                        # Documentation
├── PRODUCTS/                    # Delivery logs + product docs
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

- Python 3.11+
- Optional: Gemini/Claude CLIs + API keys for online usage
- Optional: Node.js 22+ for Cerebro UI
- Optional: MCP SDK (`python -m pip install mcp`) for the companion server
- Optional: Redis (for multi-instance), PostgreSQL (for persistence)

```bash
pip install -r requirements.txt
```

---

## Test Status

```
Latest full run: 2026-02-15
Tests collected: 2500+
Test files: 200
Results: All passing
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
4. See [AGENTS.md](AGENTS.md) for repo guidelines and commands
5. All PRs require tests

---

## License

MIT License - See [LICENSE](LICENSE) for details.

---

<div align="center">

**NEXUS V12.4 "COGNITIVE BOOST"**

*Collaborative Intelligence for Real-World Problems*

Built with Gemini 3 Pro + Claude Opus 4.6

</div>
