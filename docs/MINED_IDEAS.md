# Mined Ideas from Legacy Documentation

> Extracted: 2025-12-16
> Sources: ROADMAP_HIVE_MIND_LEGACY.md (114KB), ROADMAP_V8.md (129KB)

## Legend
- 🟢 EASY: 1-2 days
- 🟡 MEDIUM: 3-5 days  
- 🔴 HARD: 1+ week
- ✅ Implemented in codebase
- ❌ Not implemented yet

---

## High-Priority Ideas (Not Yet Implemented)

### 1. EPHEMERAL Session Mode 🟢
**Source**: Gemini proposal (lines 58-61, 776-789)
**Status**: ❌ Enum exists but not used

One-shot sessions without persistence for TRIVIAL tasks.
- Avoids `~/.gemini/tmp` saturation
- Faster response time

```python
class SessionMode(Enum):
    FRESH = "fresh"
    CONTINUE = "continue"
    BRANCH = "branch"
    EPHEMERAL = "ephemeral"  # ← NOT IMPLEMENTED
```

**Feasibility**: 🟢 EASY - Just add logic to use no `--resume` flag

---

### 2. Fast Path for Trivial Inputs 🟢
**Source**: Phase 9 (lines 557-587)
**Status**: ❌ Pattern exists but not wired

Bypass FSM entirely for greetings/confirmations.

```python
FAST_PATH_PATTERNS = [
    r"^(hello|hi|bonjour|salut|hey)\b",
    r"^(merci|thanks|thank you|thx)\b",
    r"^(ok|oui|yes|non|no|d'accord)\b",
    r"^(quit|exit|bye|au revoir)\b",
]
```

**Feasibility**: 🟢 EASY - Regex matching + single-agent response

---

### 3. Recovery Manager (PANIC → IDLE) 🟡
**Source**: Lines 438-512
**Status**: ❌ Not implemented

Currently PANIC requires manual restart. Could auto-recover.

```python
class RecoveryManager:
    def attempt_recovery(self, error_state, exception):
        if error_state == FSMState.PANIC:
            checkpoint = self.session_manager.get_latest_valid_checkpoint()
            if checkpoint:
                self.session_manager.restore_checkpoint(checkpoint)
                return RecoveryResult(success=True, new_state=FSMState.IDLE)
```

**Feasibility**: 🟡 MEDIUM - Requires checkpointing infra

---

### 4. Session Branching for PARALLEL Mode 🟡
**Source**: Claude proposal (lines 855-893)
**Status**: ❌ Not fully implemented

Use Claude's `--fork-session` for parallel branches.

```
Task A ─┬─ Branch 1 (Agent 1) ──┬─ Merge
        │   session_uuid_1      │
        └─ Branch 2 (Agent 2) ──┘
            session_uuid_2
```

**Feasibility**: 🟡 MEDIUM - Claude supports natively, Gemini needs simulation

---

### 5. Shared Memory Files (Protocol 2) 🟢
**Source**: Lines 808-817
**Status**: ❌ Design exists, not implemented

```
workspace/.nexus/shared_memory/
├── task_abc123/
│   ├── gemini_research.md
│   ├── claude_analysis.md
│   └── handover_summary.json
```

**Feasibility**: 🟢 EASY - File-based, no new dependencies

---

### 6. BM25S Sparse Retrieval 🟢
**Source**: Phase 10e (lines 1127-1161)
**Status**: ❌ Planned V7.8.2

Replace TF-IDF with BM25S for better retrieval (+15% recall).
- Zero new heavy dependencies (pure Python + scipy)

**Feasibility**: 🟢 EASY - Drop-in replacement

---

### 7. Agent-as-MCP-Tool 🔴
**Source**: Protocol 3 (lines 818-827)
**Status**: ❌ Future vision

```python
# Claude calls Gemini as MCP tool
result = mcp__gemini__research("query")

# Gemini calls Claude as MCP tool  
result = mcp__claude__analyze("context")
```

**Feasibility**: 🔴 HARD - Requires MCP server infrastructure

---

### 8. Memory Backend Abstraction 🟡
**Source**: Phase 10f (lines 1164-1199)
**Status**: ❌ Planned V7.9

Strategy pattern for swappable backends (TF-IDF, BM25, Dense, Hybrid).

**Feasibility**: 🟡 MEDIUM - Refactoring project_memory.py

---

### 9. Spawned Agent Session Persistence 🟢
**Source**: Claude proposal (lines 895-917)
**Status**: ❌ Not implemented

Add `session_persistence` to BIRTH_CERTIFICATE.json.

```json
{
  "session_persistence": {
    "enabled": true,
    "persistent_uuid": "spawned-sql-expert-uuid",
    "session_retention_days": 7
  }
}
```

**Feasibility**: 🟢 EASY - JSON schema extension

---

### 10. Cold Storage before Compression 🟢
**Source**: Lines 514-556
**Status**: ❌ Not implemented

Save raw history before LLM compression for debug/audit.

```
workspace/.nexus/
├── blackboard.json       # hot
├── events.jsonl          # warm  
└── cold_storage/         # cold
    └── 2025-12-04_pre_compress.json
```

**Feasibility**: 🟢 EASY - Simple file save before compress

---

## Already Implemented ✅

| Idea | Location |
|------|----------|
| AtomicJsonStore | core/utils/atomic_store.py |
| SwarmSessionManager | core/swarm/session_manager.py |
| SuccessMemory | core/memory/success_memory.py |
| ProjectMemory RAG | core/memory/project_memory.py |
| Thread-safe locks | memory_v7.py |
| SwarmBridge Dictator Mode | core/hive_mind/swarm_bridge.py |
| SwarmTool delegate | core/execution/tool_manager.py |
| Depth Guard Anti-Recursion | core/execution/tool_manager.py |
| Dynamic Spawn Brainstorming | core/interface/repl.py |

---

## Additional Ideas from ROADMAP_V8.md

### 11. Prometheus Metrics Exporter 🟡
**Source**: V8.1.2 (lines 370-386)
**Status**: ❌ Planned

```python
# Métriques clés
nexus_tasks_total (counter)
nexus_task_duration_seconds (histogram)
nexus_swarm_mode_selected (counter by mode)
nexus_hive_mind_phase_duration (histogram by phase)
```

**Feasibility**: 🟡 MEDIUM - Requires prometheus_client library

---

### 12. Rate Limiting with Token Bucket 🟢
**Source**: V8.1.4 (lines 426-478)
**Status**: ❌ Planned

Pure asyncio implementation (no external deps):
```python
class ProviderGuard:
    _buckets = {
        "claude": {"tokens": 50.0, "rate": 0.83},  # ~50 RPM
        "gemini": {"tokens": 60.0, "rate": 1.00}   # ~60 RPM
    }
```

**Feasibility**: 🟢 EASY - Pure Python implementation shown

---

### 13. Intent Resolver (3-Layer) 🟡
**Source**: V8.1.5 (lines 481-548)
**Status**: ❌ Planned

Replace `if "keyword" in msg` with intelligent router:
- Layer 1: Fast-Path (O(1) command lookup)
- Layer 2: LRU Cache
- Layer 3: Semantic (RAG)

**Feasibility**: 🟡 MEDIUM - Architecture well defined

---

### 14. TaskAnalysis.reasoning Field 🟢
**Source**: V8.1.7 (lines 629-662)
**Status**: ❌ Enhancement suggested

Add `reasoning: str = ""` to TaskAnalysis for traceability.

**Feasibility**: 🟢 EASY - Simple field addition

---

### 15. Unified Analysis Adapter 🟢
**Source**: V8.2.0a (lines 850-910)
**Status**: ❌ Planned

Bidirectional adapter between Swarm TaskAnalysis and HiveMind IndependentAnalysis.

**Feasibility**: 🟢 EASY - Mapping logic already defined

---

### 16. RedTeam Post-Spawn Validation 🟡
**Source**: V8.2.0c (lines 933-963)
**Status**: ❌ Planned

Validate alignment of spawned agents (not just evolved ones).
Config: `REDTEAM_SPAWN_MANDATORY=True`

**Feasibility**: 🟡 MEDIUM - RedTeam exists, needs integration

---

### 17. Torture Protocol V8 🟡
**Source**: V8.2.0d (lines 966-1006)
**Status**: ❌ Planned

Stress test scenarios:
- `parallel_flood` (10 concurrent tasks)
- `stagnation_loop` (tests hot-swap)
- `budget_drain` (20 expensive tasks)
- `chaos_monkey` (random failures)

Targets: >95% success rate, <1% panic rate

**Feasibility**: 🟡 MEDIUM - Test framework design complete

---

## Recommended Priority for ROADMAP_V10

### Quick Wins 🟢 (1-2 days each)
1. **Fast Path** - Immediate UX win
2. **EPHEMERAL mode** - Performance + cleanup
3. **Cold Storage** - Debug capability
4. **Rate Limiting** - Prevent 429 errors
5. **TaskAnalysis.reasoning** - Traceability
6. **Unified Analysis Adapter** - Cross-domain fix

### Medium Effort 🟡 (3-5 days each)
7. **Recovery Manager** - Resilience
8. **Session Branching** - Better parallelism
9. **Intent Resolver** - Cleaner routing
10. **RedTeam Post-Spawn** - Security
11. **Prometheus Metrics** - Observability
12. **Torture Protocol V8** - Validation

### Long Term 🔴 (1+ week)
13. **Agent-as-MCP-Tool** - Future vision
14. **Memory Backend Abstraction** - Extensibility
