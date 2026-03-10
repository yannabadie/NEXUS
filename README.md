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
[![Providers](https://img.shields.io/badge/providers-multi--provider-orange.svg)](https://github.com/yannabadie/NEXUS/tree/NX-CG)
[![License](https://img.shields.io/badge/license-MIT-purple.svg)](LICENSE)

**NEXUS is a collaborative orchestration runtime for local-first research, MCP tooling, and multi-agent execution.**

</div>

---

## Vision

> **"Evidence beats branding."**

NEXUS ships a real REPL, a local evidence-pack CLI, an MCP server, and a CEREBRO API/UI surface. Treat maturity claims as untrusted unless they are backed by the current CI evidence ledger, live canaries, and reproducible evaluation artifacts.

```text
+----------------------+     collaboration      +----------------------+
| Provider Backend A   | <--------------------> | Provider Backend B   |
| compatible model     |                        | compatible model     |
+----------------------+                        +----------------------+
             \\                                           /
              \\                                         /
               +---------------------------------------+
               |      NEXUS orchestration runtime      |
               |  analyze, specialize, execute, learn  |
               +---------------------------------------+
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

### Flagship: Research CLI + Evidence Pack Generator
Local-first evidence-pack generation over indexed project files.
```bash
python nexus_research.py "How does ProjectMemory index files?" --mode mock --path core/memory_pkg/memory/project_memory.py
```
Outputs: `report.md`, `sources.json`, `trace.jsonl`, `reasoning_graph.mmd`, `metrics.json`, `manifest.sha256`

### Companion: MCP Server
MCP server exposing research + evidence pack generation.
```bash
python -m pip install mcp
nexus-mcp
```

Release guide: `PRODUCTS/RELEASE.md`  
Demo scripts: `scripts/demo_flagship.ps1`, `scripts/demo_companion.ps1`

---

## V12.4 Features

### COGNITIVE BOOST (Current)

| Component | Description |
|-----------|-------------|
| **Expanded Surface Area** | Cross-domain observability, analytics, workflow, and execution modules |
| **SDK Drivers** | Native Anthropic + Google GenAI SDKs with Prompt Caching |
| **Message Infrastructure** | Protocol, deduplicator, router, reliability tracker |
| **Cognitive Pipeline** | Phase coordination, consensus tracking, reasoning quality |
| **Security & Governance** | Event journal, access control, encryption, alignment journal |
| **StagnationPredictor** | Detects task stagnation with auto-recovery |
| **Hybrid Retrieval Backends** | `dense`, `bm25`, `tfidf`, plus a `HybridBackend` implementation; publish uplift claims only with evaluation artifacts |

### Previous Releases

| Version | Codename | Highlights |
|---------|----------|------------|
| V12.3 | SCALE-OUT | Multi-instance ready (Redis, distributed locks, Prometheus) |
| V12.2 | IRONCLAD | Security foundation (RBAC, AuditLogger, IntegrityMonitor) |
| V12.1 | RETINA | Production cockpit (CEREBRO dashboard, OpsView) |
| V12.0 | HIVE MIND | 7-phase pipeline, SwarmBridge delegation |

---

## Architecture

```text
+--------------------------------------------------------------------+
|                    NEXUS V12.4 ARCHITECTURE                        |
+--------------------------------------------------------------------+
| USER INPUT -> REPL Interface -> FSM Orchestrator                   |
|                               |                                    |
|                               v                                    |
|                    HIVE MIND (7 phases)                            |
|                    - Analysis                                       |
|                    - Debate                                         |
|                    - Architecture                                   |
|                    - Execution (SwarmBridge)                        |
|                    - Diagnosis                                      |
|                    - Retry                                          |
|                    - Consolidation                                  |
|                               |                                    |
|                               v                                    |
|                    SWARM ENGINE (6 modes)                          |
|                    - PARALLEL      - PING_PONG                     |
|                    - RED_BLUE      - SEQUENTIAL                    |
|                    - LEAD_SUPPORT  - SPECIALIST                    |
|                               |                                    |
|                +--------------+---------------+                    |
|                |                              |                    |
|                v                              v                    |
|           MEMORY (RAG + Success)        TOOLS (21+)                |
|                ^                              |                    |
|                |                              v                    |
|           CEREBRO Dashboard <------------ Runtime State            |
+--------------------------------------------------------------------+
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
| `/help` | Show command help |
| `/status` | System status |
| `/reset` | Reset orchestrator state |
| `/swarm <task>` | Execute a task through the Swarm Engine |
| `/swarm-status` | Show Swarm status and DyLAN metrics |
| `/spawn <role>` | Create a specialized agent |
| `/agents` | List registered agents |
| `/evolve [child_count]` | Trigger an evolution cycle |
| `/evolve-status` | Show evolution status |
| `/review` | Review evolved children |
| `/specialize <mission>` | Create a specialized spinoff |
| `/learn <path>` | Index a file or directory into Project Memory |
| `/forget <path>` | Remove a file or directory from Project Memory |
| `/memory-status` | Show Project Memory statistics |
| `/rag <init|clear|query <text>>` | Run RAG maintenance or retrieval commands |
| `/bootstrap [path]` | Generate `NEXUS.md` for a project |
| `/workspace ...` | Show, create, list, or switch workspaces |
| `/doctor` | Run diagnostics |
| `/telemetry` | View telemetry status or reports |
| `/budget` | View or adjust budget state |
| `/quit` | Exit the REPL |

---

## Project Structure

```text
NEXUS/
+-- core/                                # Core orchestration
|   +-- orchestration_v7.py              # Main FSM orchestrator
|   +-- drivers/                         # Gemini, Claude, OpenAI, DeepSeek, Kimi, MiniMax
|   +-- execution_pkg/                   # Tool execution layer + routing
|   +-- fsm/                             # State machine
|   +-- intelligence/
|   |   +-- hive_mind/                   # 7-phase pipeline
|   |   +-- swarm/                       # 6 collaboration modes
|   |   +-- evolution/                   # Agent spawning
|   +-- memory_pkg/memory/               # RAG + SuccessMemory
|   +-- security_pkg/security/           # Security and policy layers
|   +-- foundation/                      # Agents, async primitives
|   +-- synapse/                         # Message protocol & reliability
|   +-- infrastructure/                  # Bootstrap, session, events, db
|   +-- observability/                   # Telemetry, metrics, OTel, profiling
|   +-- interface_pkg/                   # REPL, MCP, HITL, interaction
|   +-- metagraph/                       # AST-based codebase intelligence
|   +-- meta/                            # System introspection
|   +-- ui/                              # Display components
+-- interface/                           # Frontend surfaces
|   +-- ui/cerebro/                      # React dashboard
+-- prompts/                             # System prompts
+-- workspace/                           # Runtime data
|   +-- agents/                          # Spawned agents
|   +-- logs/                            # Event logs
+-- .nexus/                              # Project-local retrieval store
+   +-- project_knowledge.json          # ProjectMemory JSON index
+   +-- lancedb/                        # Optional dense retrieval storage
+-- tests/                               # Python test suite
+-- docs/                                # Documentation
+-- PRODUCTS/                            # Delivery logs + product docs
+-- nexus7.py                            # Entry point
+-- KERNEL.py                            # Legacy governance / heredity artifact
+-- MISSION.md                           # Project mission
```

---

## Security - 7 Layers

| Layer | Component | Function |
|-------|-----------|----------|
| 1 | **Runtime Policy** | Capability and execution policy enforcement |
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

```text
+--------------------------------------------------------------+
|                    NEXUS PROJECT MEMORY                      |
+--------------------------------------------------------------+
| Storage root: NEXUS_ROOT/.nexus/                             |
| - project_knowledge.json                                     |
| - optional lancedb/                                          |
|                                                              |
| Backend selection: auto | hybrid | dense | bm25 | tfidf     |
| Backend selection now supports `hybrid` explicitly, and      |
| `auto` prefers fusion when the required backends exist.      |
+--------------------------------------------------------------+
```

- **Mock/local evidence-pack runs** require no external network calls
- **Storage path** is `NEXUS_ROOT/.nexus/`, not `workspace/.nexus/`
- **Supports**: `.py`, `.md`, `.txt`, `.yaml`, `.json`, `.toml`, plus document/image ingestion when optional ingestors are installed

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

## Evidence & Compatibility

Current quality, coverage, build, smoke-test, and provider-compatibility signals are published per CI run in the `evidence-ledger` artifact generated by `NEXUS CI` on `NX-CG`.

- Machine-readable artifact: `artifacts/evidence-ledger.json`
- Human summary: `artifacts/evidence-ledger.md`
- Historical manual snapshot: `PRODUCTS/03_BASELINE.md`

Use the ledger instead of hardcoded README counts for exact test totals, pass/fail/skip counts, coverage, wheel/install status, and smoke evidence. Routine CI provider compatibility is registry-backed and wiring-oriented, not a substitute for live end-to-end canaries.

---

## Contributing

1. Read [MISSION.md](MISSION.md) to understand the vision
2. Check [ROADMAP.md](ROADMAP.md) for strategic priorities only; use CI evidence for current status
3. Follow code style in [CLAUDE.md](CLAUDE.md)
4. See [AGENTS.md](AGENTS.md) for repo guidelines and commands
5. All PRs require tests

---

## License

MIT License - See [LICENSE](LICENSE) for details.

---

<div align="center">

**NEXUS V12.4.0 "COGNITIVE BOOST"**

*Collaborative Intelligence for Real-World Problems*

Built around Gemini + Claude provider backends, with compatibility tracked in CI evidence

</div>
