# NEXUS V10 ROADMAP - The Path to Singularity

**Version**: 10.2 | **Updated**: 2025-12-16

---

## 🎯 Vision

Transform NEXUS from prototype to **deployable collaborative intelligence** with a modern interactive frontend that reflects its power.

---

## ✅ Phase 1: UI Backend Resurrection (COMPLETE)

- [x] Externalize DASHBOARD_URL (`event_bus.py`, `telemetry.py`)
- [x] Fix absolute workspace path (`dashboard_server.py`)
- [x] Clean README.md (remove duplicates)
- [ ] Security: Replace `allow_origins=["*"]`

## ✅ Phase 2: Documentation Reset (COMPLETE)

- [x] Archive `ROADMAP.md` → `archive/ROADMAP_V8.md`
- [x] Clean `README.md` (V10 only)
- [x] Fix `INSTALLATION.md` hardcoded path
- [x] Create documentation audit report

## ✅ Phase 2.5: V10.1 Architecture Fixes (COMPLETE)

> **Added 2025-12-13** - Critical session_uuid propagation fixes

- [x] HiveMind session_uuid → ALL 7 phases propagated
- [x] Agent-as-Tool session_uuid (`agent_tools.py`)
- [x] AgentInvoker.invoke_spawned_agent session_uuid
- [x] Documentation: FSM/HiveMind/Swarm architecture
- [x] JSON parse robustness (`ast.literal_eval` fallback)
- [x] ANSI colors fix for Windows

**Commits**: `39ad8f2`, `4cc64dc`, `2524d8c`

---

## 🚧 Phase 3: Core Stabilization (In Progress)

- [ ] Exception audit (435 `except:` blocks)
- [ ] Complete async driver migration
- [ ] Test suite cleanup (consolidate 19 E2E files)
- [ ] CI/CD workflow fixes

---

## 🆕 Phase 3.6: DEEP_AUDIT Resolutions (NEW - 2025-12-17)

> **Source**: Extracted from `DEEP_AUDIT.md` (Technical Audit Report)

### Priority 1: Split Monolithic Files 🔴

| File | Size | Resolution |
|------|------|------------|
| `fsm_handlers.py` | 74.7KB | Split → `fsm/handlers/*.py` |
| `repl.py` | 72.6KB | Split → `repl_core.py`, `repl_parser.py`, `repl_display.py` |
| `tool_manager.py` | 62.1KB | Split → `execution/tools/*.py` |
| `mode_executors.py` | 46.9KB | Split → one file per mode |

### Priority 2: Exception Audit 🟡

| File | `except` Blocks | Action |
|------|-----------------|--------|
| `tool_manager.py` | 40 | Add specific exceptions + logging |
| `repl.py` | 30 | Remove bare `except:` blocks |
| `dashboard_server.py` | 27 | Fix WebSocket error masking |
| `fsm_handlers.py` | 26 | Add state machine error logging |

### Priority 3: Wire Missing Features 🟢

| Feature | Location | Effort | Status |
|---------|----------|--------|--------|
| Wire EPHEMERAL | `session_manager.py` | 1 day | ✅ DONE |
| Enable Fast Path | `fsm_handlers.py` | 1 day | ✅ DONE |
| Rate Limiting | `core/api/rate_limiter.py` | 2 days | ✅ DONE |
| Recovery Manager | `core/hive_mind/saga_manager.py` | 3 days | ✅ DONE (V10.2) |

### Priority 4: Security Hardening 🔒

- [ ] Input validation layer before tool execution
- [ ] Path canonicalization in `path_guardian.py`
- [ ] Rate limiting on bash tool execution

---

## 🆕 Phase 3.5: Mined Ideas from Legacy Docs (NEW - 2025-12-16)

> **Source**: Extracted from `ROADMAP_HIVE_MIND_LEGACY.md` (114KB) and `ROADMAP_V8.md` (129KB)
> See [MINED_IDEAS.md](docs/MINED_IDEAS.md) for full details.

### Quick Wins 🟢 (1-2 days each)

| # | Feature | Description | Status |
|---|---------|-------------|--------|
| 1 | **Fast Path** | Bypass FSM for trivial inputs (hello, thanks, ok) | ✅ DONE (config.py) |
| 2 | **EPHEMERAL Sessions** | Skip persistence for TRIVIAL tasks | ✅ WIRED |
| 3 | **Cold Storage** | Save raw history before LLM compression | ❌ TODO |
| 4 | **Rate Limiting** | TokenBucket per-provider (Claude 50 RPM, Gemini 60 RPM) | ✅ DONE (api/rate_limiter.py) |
| 5 | **TaskAnalysis.reasoning** | Add traceability field to TaskAnalysis | ❌ TODO |
| 6 | **Unified Analysis Adapter** | Bidirectional TaskAnalysis ↔ IndependentAnalysis | ❌ TODO |

### Medium Effort 🟡 (3-5 days each)

| # | Feature | Description | Status |
|---|---------|-------------|--------|
| 7 | **Recovery Manager** | Auto-recover from PANIC state via checkpoints | ❌ TODO |
| 8 | **Session Branching** | Claude `--fork-session` for PARALLEL isolation | ❌ TODO |
| 9 | **Intent Resolver** | 3-layer router (Fast-Path, LRU Cache, Semantic RAG) | ❌ TODO |
| 10 | **RedTeam Post-Spawn** | Validate alignment of spawned agents | ❌ TODO |
| 11 | **Prometheus Metrics** | `nexus_tasks_total`, `nexus_task_duration_seconds`, etc. | ❌ TODO |
| 12 | **Torture Protocol V8** | Stress test: parallel_flood, stagnation_loop, chaos_monkey | ❌ TODO |

### Long Term 🔴 (1+ week)

| # | Feature | Description | Status |
|---|---------|-------------|--------|
| 13 | **Shared Memory Files** | `workspace/.nexus/shared_memory/` for cross-agent handover | ❌ TODO |
| 14 | **BM25S Retrieval** | Replace TF-IDF with BM25S for +15% recall | ❌ TODO |
| 15 | **Memory Backend Abstraction** | Strategy pattern for swappable backends | ❌ TODO |
| 16 | **Agent Session Persistence** | Spawned agents remember past tasks via UUID | ❌ TODO |
| 17 | **Agent-as-MCP-Tool** | Agents invoke each other as MCP tools | ❌ TODO |

## 🔴 Phase 4: Interactive Frontend (NEW - V10 GATE)

> **CRITICAL**: This phase is REQUIRED to validate V10 release

### 4.1 Current State

| Component | Status | Tech |
|-----------|--------|------|
| Backend API | ✅ Ready | FastAPI + WebSocket |
| Static HTML | ⚠️ Basic | `nexus_dashboard.html` |
| React/Next.js Frontend | ❌ Missing | N/A |

### 4.2 Frontend Requirements

```
┌─────────────────────────────────────────────────────────────┐
│                    NEXUS Dashboard V10                       │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   AGENTS     │  │   SWARM      │  │   MEMORY     │      │
│  │   (Live)     │  │   (DyLAN)    │  │   (Vectors)  │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                                                              │
│  ┌────────────────────────────────────────────────────┐     │
│  │              HIVE MIND PIPELINE                     │     │
│  │  Phase 1 → 2 → 3 → 4 → 5 → 6 → 7  (Real-time)     │     │
│  └────────────────────────────────────────────────────┘     │
│                                                              │
│  ┌────────────────────────────────────────────────────┐     │
│  │              CHAT / COMMAND + STREAMING            │     │
│  └────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

### 4.3 Technical Implementation

| Component | Tech Choice | Justification |
|-----------|-------------|---------------|
| Framework | **Next.js 15** | SSR + API routes + TypeScript |
| Real-time | **WebSocket** | Already in `dashboard_server.py` |
| Charts | **Recharts** | Real-time + React integration |
| State | **Zustand** | Lightweight, WebSocket-friendly |
| UI | **shadcn/ui + Tremor** | Modern, dark-mode ready |
| Streaming | **react-use-websocket** | LLM output streaming |

### 4.4 Key Features

1. **Agent Constellation** - Live view of Gemini/Claude/Spawned agents
2. **Swarm Mode Visualization** - PARALLEL/PING_PONG/RED_BLUE animated
3. **HiveMind Phase Tracker** - Progress through 7 phases with details
4. **LLM Streaming Chat** - Real-time token display
5. **Evolution Lineage Tree** - Mutations and children visualization
6. **Budget/Telemetry Dashboard** - Cost tracking, performance metrics

### 4.5 Effort Estimate

| Task | Days |
|------|------|
| Next.js scaffold + WebSocket setup | 2 |
| Agent/Swarm/HiveMind panels | 3 |
| Chat + streaming integration | 2 |
| Evolution visualization | 2 |
| Polish + dark mode | 1 |
| **Total** | **10 days** |

---

## 🔮 Phase 5: Strategic Intelligence Hub (Post-V10)

*Extracted from `docs/architecture/VISION_V9_SINGULARITY.md`*

### 5.1 The Four Feedback Loops

> NEXUS is not a tool—it's an organism that evolves based on its successes and failures.

| Loop | From | To | Data Flow |
|------|------|----|-----------| 
| **Loop 1** | Swarm Execution | Evolution | DyLAN scores → Mutation fitness |
| **Loop 2** | Hive Mind Failures | Evolution | Blacklist → Mutation avoidance |
| **Loop 3** | Success Memory | Mode Selection | Past wins → Mode boost |
| **Loop 4** | Execution Patterns | Auto-Spawn | Domain excellence → Specialization |

### 5.2 Key Components to Build

| Component | Description | Effort |
|-----------|-------------|--------|
| `intelligence_hub.py` | Central brain connecting 4 memory systems | 5-7d |
| `closed_loop.py` | Monotonic improvement guarantee | 4-5d |
| `auto_spawn.py` | Data-driven agent spawning | 3-4d |
| `unified_memory.py` | Consolidate 3 memory systems | 4-5d |

---

## 📊 Success Metrics

| Metric | V9 | V10.0 | V10.1 |
|--------|-----|-------|-------|
| UI works on fresh clone | ❌ | ✅ | ✅ |
| session_uuid propagation | ⚠️ | ⚠️ | ✅ |
| Agent-as-Tool context | ⚠️ | ⚠️ | ✅ |
| Modern Frontend | ❌ | ❌ | 🎯 Target |
| Mutation Success Rate | ~30% | ~30% | > 40% |

---

## 🏗️ Architecture (V10.1 Clarified)

```
USER INPUT
    │
    ▼
┌────────────────────────────────────────────────────────┐
│  OrchestratorV7 (FSM - 1076 lines)                     │
│  ├── TRIVIAL/SIMPLE → Direct Agent → Response         │
│  │                                                      │
│  └── MODERATE+ ──────────────────────────────────────┐ │
│                                                        │ │
│  ┌──────────────────────────────────────────────────┐ │ │
│  │  TrueHiveMind (692 lines)                        │ │ │
│  │  session_uuid = uuid.uuid4()                     │ │ │
│  │  Phase 1-7 → session_uuid propagated             │ │ │
│  │       │                                          │ │ │
│  │       └── SwarmBridge → HybridSwarmEngine        │ │ │
│  │                  (856 lines)                     │ │ │
│  └──────────────────────────────────────────────────┘ │ │
│                                                        │ │
│  Agent-as-Tool (V10.1) ────────────────────────────── │ │
│  execute_agent_tool(session_uuid) → invoke_spawned    │ │
└────────────────────────────────────────────────────────┘ │
```

---

## 📚 Research Foundation

| Source | Key Insight |
|--------|-------------|
| [arXiv:2412.17149v1](https://arxiv.org/html/2412.17149v1) | Closed-loop refinement pattern |
| [Mem0 Paper](https://arxiv.org/pdf/2504.19413) | Production-ready long-term memory |
| [SuperAGI Self-Healing](https://superagi.com/top-5-agentic-ai-trends-in-2025-from-multi-agent-collaboration-to-self-healing-systems/) | Multi-agent recovery patterns |

---

## ⚠️ Known Limitations

| Issue | Status | Workaround |
|-------|--------|------------|
| Code 130 FatalCancellationError | Gemini CLI limitation | Limit file access to `workspace/` |
| Swarm-as-Tool session fragmentation | By design | Document behavior |
| Ephemeral sessions not recoverable | By design | For TRIVIAL tasks only |

---

*Updated 2025-12-13 by Claude + Gemini (V10.1 session_uuid fixes complete)*
*Frontend phase added as V10 release gate*
