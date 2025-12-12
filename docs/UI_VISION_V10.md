# NEXUS Web UI Vision - "The Glass Mind"

**Version**: Draft 1.0 | **Date**: 2025-12-12
**Objective**: Full-featured web UI with transparent self-awareness

---

## 🎯 Vision

> **"NEXUS should see itself thinking and choose its tools intelligently."**

The UI transforms NEXUS from a "black box" into a "glass mind" where:
1. **All features accessible** via intuitive web interface
2. **Self-awareness visible** (NEXUS knows what it can do)
3. **Intelligent tool selection** (brainstorm before action)
4. **Transparent orchestration** (see FSM, Swarm, HiveMind working)

---

## 📊 Current State Audit

### Dashboard Endpoints (46 total in dashboard_server.py)

| Category | Endpoints | Status |
|----------|-----------|--------|
| **Agents** | `/api/agents`, `/api/agents/spawn` | ✅ |
| **Workspaces** | `/api/workspaces`, `/api/workspace/switch` | ✅ |
| **Memory** | `/api/memory/vectors`, `/api/memory/upload` | ✅ |
| **Chat** | `/api/chat` | ✅ |
| **Evolution** | `/api/evolution/status`, `/api/evolve` | ✅ |
| **Telemetry** | `/api/telemetry`, `/ws/logs` | ✅ |
| **Code Map** | `/api/dependencies` | ✅ |
| **Doctor** | `/api/doctor` | ✅ |
| **Budget** | `/api/budget` | ✅ |

### Command Modules (9 in core/interface/commands/)

| Module | Commands | UI Status |
|--------|----------|-----------|
| `evolution.py` | /evolve, /spawn, /agents, /review, /evolve-status | Partial |
| `misc.py` | /doctor, /reset, /mode, /pool-stats, /bootstrap, /specialize | Missing |
| `swarm.py` | /swarm, /swarm-status | Missing |
| `memory.py` | /rag, /learn, /forget | Missing |
| `workspace.py` | /ws | Partial |
| `telemetry.py` | /export-telemetry | Missing |
| `registry.py` | Command registration | N/A |
| `system.py` | System commands | Missing |

### Missing from UI (Critical Gaps)

1. ❌ **Swarm Mode Selection** - No UI to trigger `/swarm`
2. ❌ **RAG Query** - No UI for `/rag` semantic search
3. ❌ **Mode Switching** - No UI for `/mode` (Normal, Evolution, etc.)
4. ❌ **Specialize** - No UI for `/specialize` mission
5. ❌ **Review Children** - No UI for `/review` workflow
6. ❌ **Learn/Forget** - No UI for memory management
7. ❌ **Self-Awareness Panel** - NEXUS doesn't display its capabilities

---

## 🧠 Self-Awareness Architecture

### Core Concept: "Metacognition Panel"

NEXUS should display its own capabilities and reasoning:

```
┌─────────────────────────────────────────────────────────────┐
│                    NEXUS SELF-AWARENESS                     │
├─────────────────────────────────────────────────────────────┤
│ 🧠 CAPABILITIES KNOWN:                                       │
│   • 11 Tools (read, write, grep, glob, run_shell...)        │
│   • 6 Swarm Modes (PARALLEL, SEQUENTIAL, LEAD_SUPPORT...)   │
│   • 2 Primary Agents (Gemini, Claude) + N Spawned           │
│   • RAG Memory (Dense/BM25/TF-IDF backends)                 │
│                                                              │
│ 🎯 CURRENT STATE:                                            │
│   FSM: BRAINSTORMING → HiveMind: Phase 3 → Swarm: PING_PONG │
│                                                              │
│ 💭 REASONING: "For this task I should use PARALLEL mode     │
│   because subtasks are independent. I'll involve Claude     │
│   for architecture and Gemini for research."                │
└─────────────────────────────────────────────────────────────┘
```

### Implementation: Self-Inventory Endpoint

```python
# NEW: /api/self-awareness
@app.get("/api/self-awareness")
async def get_self_awareness():
    return {
        "tools": tool_manager.list_tools(),           # 11 tools
        "swarm_modes": ["PARALLEL", "SEQUENTIAL", ...],
        "agents": registry.list_all(),                 # Primary + Spawned
        "memory_backends": ["dense", "bm25", "tfidf"],
        "fsm_state": orchestrator.current_state,
        "hive_mind_phase": hive_mind.current_phase,
        "current_swarm_mode": swarm_engine.current_mode,
        "dylan_scores": swarm_engine.get_scores()
    }
```

---

## 🖥️ UI Components Design

### 1. Mission Control (Home Tab)

```
┌─────────────────────────────────────────────────────────────┐
│  📍 MISSION CONTROL                                          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  [Chat Input: "Analyze the codebase for security issues"]   │
│                                                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │   NORMAL    │  │   SWARM     │  │  EVOLUTION  │         │
│  │    MODE     │  │    MODE     │  │    MODE     │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
│                                                              │
│  ⚡ Quick Actions:                                           │
│  [Spawn Agent] [Run Doctor] [Export Telemetry] [Specialize] │
└─────────────────────────────────────────────────────────────┘
```

### 2. Orchestration View (FSM + Swarm + HiveMind)

```
┌─────────────────────────────────────────────────────────────┐
│  🔄 ORCHESTRATION LIVE VIEW                                  │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  FSM STATE: [IDLE] → [BRAINSTORMING] → [EXECUTING] → [CFL]  │
│                          ↑ Current                          │
│                                                              │
│  HIVE MIND PIPELINE:                                        │
│  [1.Parse] → [2.Plan] → [3.Assign] → [4.Execute] → ...     │
│                             ↑ Phase 3                        │
│                                                              │
│  SWARM MODE: PING_PONG                                       │
│  ┌─────────┐  ←→  ┌─────────┐                               │
│  │ GEMINI  │      │ CLAUDE  │   Turn: 4                     │
│  │ DyLAN:85│      │ DyLAN:92│                               │
│  └─────────┘      └─────────┘                               │
└─────────────────────────────────────────────────────────────┘
```

### 3. Agent Factory Tab

```
┌─────────────────────────────────────────────────────────────┐
│  🤖 AGENT FACTORY                                            │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  PRIMARY AGENTS:                                             │
│  ┌───────────┐  ┌───────────┐                               │
│  │🟦 Gemini  │  │🟠 Claude  │                               │
│  │ Active    │  │ Active    │                               │
│  │ DyLAN: 85 │  │ DyLAN: 92 │                               │
│  └───────────┘  └───────────┘                               │
│                                                              │
│  SPAWNED SPECIALISTS:                                        │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐               │
│  │🟣 SQL     │  │🟣 Vue.js  │  │   + NEW   │               │
│  │  Expert   │  │  Expert   │  │  [Spawn]  │               │
│  │ Domains:  │  │ Domains:  │  │           │               │
│  │ database  │  │ frontend  │  │           │               │
│  └───────────┘  └───────────┘  └───────────┘               │
│                                                              │
│  [Filter: All | Active | Archived]                          │
└─────────────────────────────────────────────────────────────┘
```

### 4. Memory & RAG Tab

```
┌─────────────────────────────────────────────────────────────┐
│  🧬 MEMORY FABRIC                                            │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  SEARCH: [Query semantic memory...]          [Backend: Dense]│
│                                                              │
│  MEMORY CLOUD: (3D Vector Visualization)                     │
│  [Interactive Cytoscape/Three.js visualization]              │
│                                                              │
│  RECENT LEARNINGS:                                           │
│  • "auth.py security pattern" (2h ago)                      │
│  • "Vue composables" (1d ago)                                │
│                                                              │
│  [Learn New] [Forget Pattern] [Export Memory]                │
└─────────────────────────────────────────────────────────────┘
```

### 5. Evolution Tab

```
┌─────────────────────────────────────────────────────────────┐
│  🧬 EVOLUTION CENTER                                         │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  LINEAGE TREE:                                               │
│  ┌─────────┐                                                │
│  │ Parent  │───┬──→ Child 1 (Fitness: 0.82) ✅ Promoted     │
│  │ V9.0    │   ├──→ Child 2 (Fitness: 0.71) 📝 Pending     │
│  └─────────┘   └──→ Child 3 (Fitness: 0.65) 🗄 Archived     │
│                                                              │
│  PENDING REVIEW: 2 children                                  │
│  [Review Now] [Auto-Promote] [Evolve +3]                     │
│                                                              │
│  MUTATIONS APPLIED:                                          │
│  • system_gemini.md: +ASI_AWARENESS_PROTOCOL                │
│  • swarm_engine.py: +self_healing_fallback                  │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔮 Intelligent Tool Selection (Brainstorm Phase)

### The Problem
Currently, NEXUS executes tools immediately. We need a **brainstorm phase** where NEXUS:
1. Analyzes the task complexity
2. Lists available tools
3. Decides which subset to use
4. Explains reasoning to user

### Solution: Pre-Execution Reasoning Panel

```
┌─────────────────────────────────────────────────────────────┐
│  💭 NEXUS IS THINKING...                                     │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  TASK: "Fix the authentication bug in auth.py"              │
│                                                              │
│  COMPLEXITY ANALYSIS: MODERATE                               │
│  DOMAINS: [security, python, debugging]                      │
│                                                              │
│  TOOLS I WILL USE:                                          │
│  ✅ grep (find auth patterns)                                │
│  ✅ read (view auth.py)                                      │
│  ✅ write (apply fix)                                        │
│  ❌ run_shell (not needed)                                   │
│  ❌ web_search (code is local)                               │
│                                                              │
│  SWARM MODE: LEAD_SUPPORT                                    │
│  LEAD: Claude (security expertise)                           │
│  SUPPORT: Gemini (code review)                               │
│                                                              │
│  [Proceed] [Modify Plan] [Cancel]                            │
└─────────────────────────────────────────────────────────────┘
```

### Implementation: Brainstorm-First Pipeline

```python
# New flow in HiveMind
async def process_task(self, task: str):
    # Phase 0: Self-Awareness Query
    capabilities = await self.get_capabilities()
    
    # Phase 1: Analyze Task
    analysis = await self.task_analyzer.analyze(task)
    
    # Phase 2: Brainstorm Tool Selection
    plan = await self.brainstorm_tools(task, capabilities, analysis)
    
    # Phase 3: Emit plan to UI for approval (optional)
    await self.telemetry.emit("PLAN_READY", plan)
    
    # Phase 4: Execute with selected tools only
    await self.execute_with_tools(plan.selected_tools)
```

---

## 📡 Real-Time Event Streaming

### WebSocket Events to Add

| Event | Data | UI Action |
|-------|------|-----------|
| `SELF_AWARENESS_UPDATE` | capabilities, state | Update Metacognition Panel |
| `BRAINSTORM_START` | task, domains | Show "Thinking..." overlay |
| `TOOL_SELECTION` | selected_tools, reasoning | Show Pre-Execution Panel |
| `SWARM_MODE_CHANGE` | new_mode, reason | Animate Swarm diagram |
| `HIVE_PHASE_CHANGE` | phase_number, phase_name | Highlight pipeline step |
| `AGENT_SPAWN` | agent_id, domains | Add to Agent Factory |
| `MEMORY_LEARN` | pattern, score | Add to Memory Feed |

---

## 🛠️ Implementation Roadmap

### Phase A: Foundation (1 week)

1. [ ] Add `/api/self-awareness` endpoint
2. [ ] Create Metacognition Panel component
3. [ ] Add missing command endpoints (/swarm, /rag, /specialize)
4. [ ] WebSocket events for new features

### Phase B: Orchestration View (1 week)

1. [ ] FSM state visualization (animated)
2. [ ] HiveMind pipeline display
3. [ ] Swarm mode diagram (Cytoscape)
4. [ ] DyLAN scores real-time update

### Phase C: Intelligent Selection (1 week)

1. [ ] Brainstorm-first pipeline in HiveMind
2. [ ] Pre-Execution Reasoning Panel
3. [ ] Tool selection visualization
4. [ ] User approval workflow (optional)

### Phase D: Full Feature Access (1 week)

1. [ ] Memory/RAG tab with search
2. [ ] Evolution center with lineage tree
3. [ ] Agent Factory spawn wizard
4. [ ] Settings & Configuration

---

## 🔍 Research References

| Source | Key Insight |
|--------|-------------|
| LangSmith | Detailed tracing, drill-down analysis |
| Galileo.ai | Graph-based agent decision paths |
| HackerNoon | Verification & override capabilities |
| CrewAI | Simple management UI for orchestration |
| arXiv:2412.17149 | Closed-loop refinement visualization |

---

## Success Metrics

| Metric | Current | Target |
|--------|---------|--------|
| Features accessible via UI | ~40% | 100% |
| Self-awareness visibility | 0% | Full |
| Brainstorm before action | Never | Always |
| User can override plan | No | Yes |

---

*This vision document proposes transforming NEXUS UI from a monitoring dashboard to a transparent, self-aware intelligence interface.*
