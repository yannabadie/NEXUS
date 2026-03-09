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
[![Providers](https://img.shields.io/badge/providers-Claude%20%2B%20Gemini-orange.svg)](https://github.com/yannabadie/NEXUS)
[![License](https://img.shields.io/badge/license-MIT-purple.svg)](LICENSE)

**NEXUS is a deployable collaborative intelligence that specializes based on context.**

</div>

---

## Vision

> **"Two AIs working together surpass what each can do alone."**

NEXUS is not just a tool - it's a **deployable intelligence core** designed to be cloned into any project and become its dedicated AI collaborator.

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
| **HybridBackend RRF** | Reciprocal Rank Fusion for hybrid retrieval; publish metrics via the evaluation stack and evidence ledger |

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
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚                         NEXUS V12.4 ARCHITECTURE                    â”‚
â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¤
â”‚                                                                     â”‚
â”‚  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”     â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”     â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”           â”‚
â”‚  â”‚    USER     â”‚â”€â”€â”€â”€â–ºâ”‚    REPL     â”‚â”€â”€â”€â”€â–ºâ”‚    FSM      â”‚           â”‚
â”‚  â”‚   INPUT     â”‚     â”‚  Interface  â”‚     â”‚ Orchestratorâ”‚           â”‚
â”‚  â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜     â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜     â””â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”˜           â”‚
â”‚                                                  â”‚                   â”‚
â”‚                    â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”   â”‚
â”‚                    â”‚              HIVE MIND      â–¼               â”‚   â”‚
â”‚                    â”‚  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”   â”‚   â”‚
â”‚                    â”‚  â”‚ Phase 1: ANALYSIS      (Independent) â”‚   â”‚   â”‚
â”‚                    â”‚  â”‚ Phase 2: DEBATE        (If needed)   â”‚   â”‚   â”‚
â”‚                    â”‚  â”‚ Phase 3: ARCHITECTURE  (Plan)        â”‚   â”‚   â”‚
â”‚                    â”‚  â”‚ Phase 4: EXECUTION     (SwarmBridge) â”‚â”€â”€â–ºâ”‚   â”‚
â”‚                    â”‚  â”‚ Phase 5: DIAGNOSIS     (On failure)  â”‚   â”‚   â”‚
â”‚                    â”‚  â”‚ Phase 6: RETRY         (Adaptive)    â”‚   â”‚   â”‚
â”‚                    â”‚  â”‚ Phase 7: CONSOLIDATION (Merge)       â”‚   â”‚   â”‚
â”‚                    â”‚  â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜   â”‚   â”‚
â”‚                    â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜   â”‚
â”‚                                                  â”‚                   â”‚
â”‚                    â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â–¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”   â”‚
â”‚                    â”‚              SWARM ENGINE                   â”‚   â”‚
â”‚                    â”‚  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”   â”‚   â”‚
â”‚                    â”‚  â”‚ PARALLEL â”‚  â”‚PING_PONG â”‚  â”‚ RED_BLUE â”‚   â”‚   â”‚
â”‚                    â”‚  â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜  â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜  â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜   â”‚   â”‚
â”‚                    â”‚  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”   â”‚   â”‚
â”‚                    â”‚  â”‚SEQUENTIALâ”‚  â”‚LEAD_SUPP â”‚  â”‚SPECIALISTâ”‚   â”‚   â”‚
â”‚                    â”‚  â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜  â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜  â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜   â”‚   â”‚
â”‚                    â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜   â”‚
â”‚                                                  â”‚                   â”‚
â”‚  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”     â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”     â”Œâ”€â”€â”€â”€â”€â”€â–¼â”€â”€â”€â”€â”€â”€â”           â”‚
â”‚  â”‚   CEREBRO   â”‚â—„â”€â”€â”€â”€â”‚   MEMORY    â”‚â—„â”€â”€â”€â”€â”‚   TOOLS     â”‚           â”‚
â”‚  â”‚  Dashboard  â”‚     â”‚ RAG+Success â”‚     â”‚  21+ Tools  â”‚           â”‚
â”‚  â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜     â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜     â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜           â”‚
â”‚                                                                     â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
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
â”œâ”€â”€ core/                                # Core orchestration
â”‚   â”œâ”€â”€ orchestration_v7.py              # Main FSM orchestrator
â”‚   â”œâ”€â”€ drivers/                         # Gemini & Claude drivers
â”‚   â”œâ”€â”€ execution_pkg/                   # Tool execution layer + routing
â”‚   â”œâ”€â”€ fsm/                             # State machine (12 states)
â”‚   â”œâ”€â”€ intelligence/
â”‚   â”‚   â”œâ”€â”€ hive_mind/                   # 7-phase pipeline
â”‚   â”‚   â”œâ”€â”€ swarm/                       # 6 collaboration modes
â”‚   â”‚   â””â”€â”€ evolution/                   # Agent spawning
â”‚   â”œâ”€â”€ memory_pkg/memory/               # RAG + SuccessMemory
â”‚   â”œâ”€â”€ security_pkg/security/           # 7 security layers
â”‚   â”œâ”€â”€ foundation/                      # Agents, async primitives
â”‚   â”œâ”€â”€ synapse/                         # Message protocol & reliability
â”‚   â”œâ”€â”€ infrastructure/                  # Bootstrap, session, events, db
â”‚   â”œâ”€â”€ observability/                   # Telemetry, metrics, OTel, profiling
â”‚   â”œâ”€â”€ interface_pkg/                   # HITL, interaction, context
â”‚   â”œâ”€â”€ metagraph/                       # AST-based codebase intelligence
â”‚   â”œâ”€â”€ meta/                            # System introspection
â”‚   â””â”€â”€ ui/                              # Display components
â”œâ”€â”€ interface/                           # User interfaces
â”‚   â”œâ”€â”€ ui/cerebro/                      # React dashboard
â”‚   â””â”€â”€ cli/                             # REPL components
â”œâ”€â”€ prompts/                             # System prompts
â”œâ”€â”€ workspace/                           # Runtime data
â”‚   â”œâ”€â”€ agents/                          # Spawned agents
â”‚   â”œâ”€â”€ logs/                            # Event logs
â”‚   â””â”€â”€ .nexus/                          # RAG database
â”œâ”€â”€ tests/                               # Python test suite (see CI evidence ledger for current counts)
â”œâ”€â”€ docs/                                # Documentation
â”œâ”€â”€ PRODUCTS/                            # Delivery logs + product docs
â”œâ”€â”€ nexus7.py                            # Entry point
â”œâ”€â”€ KERNEL.py                            # Immutable alignment
â””â”€â”€ MISSION.md                           # Project mission
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

```
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚                    NEXUS RAG SYSTEM                         â”‚
â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¤
â”‚  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”    â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”                â”‚
â”‚  â”‚  MiniLM-L6-v2   â”‚    â”‚    BM25S        â”‚                â”‚
â”‚  â”‚  (Dense 384d)   â”‚    â”‚   (Sparse)      â”‚                â”‚
â”‚  â””â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”˜    â””â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”˜                â”‚
â”‚           â”‚                      â”‚                          â”‚
â”‚           â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜                          â”‚
â”‚                      â–¼                                      â”‚
â”‚           â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”                          â”‚
â”‚           â”‚ HybridBackend RRF   â”‚ See evaluation artifacts â”‚
â”‚           â”‚ (Reciprocal Rank    â”‚                          â”‚
â”‚           â”‚  Fusion)            â”‚                          â”‚
â”‚           â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜                          â”‚
â”‚                      â–¼                                      â”‚
â”‚           â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”                          â”‚
â”‚           â”‚  MemoryCoordinator  â”‚ Adaptive weights         â”‚
â”‚           â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜                          â”‚
â”‚                      â–¼                                      â”‚
â”‚           â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”                          â”‚
â”‚           â”‚     LanceDB         â”‚ .nexus/lancedb/          â”‚
â”‚           â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜                          â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
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

## Evidence & Compatibility

Current quality, coverage, build, smoke-test, and provider-compatibility signals are published per CI run in the `evidence-ledger` artifact generated by `NEXUS CI` on `NX-CG`.

- Machine-readable artifact: `artifacts/evidence-ledger.json`
- Human summary: `artifacts/evidence-ledger.md`
- Historical manual snapshot: `PRODUCTS/03_BASELINE.md`

Use the ledger instead of hardcoded README counts for exact test totals, pass/fail/skip counts, coverage, wheel/install status, and provider compatibility.

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

Built around Gemini + Claude provider backends, with compatibility tracked in CI evidence

</div>
