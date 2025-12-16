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
| TaskScopedBlackboard | (partial) |

---

## Recommended Priority for ROADMAP_V10

1. **Fast Path** 🟢 - Immediate UX win
2. **EPHEMERAL mode** 🟢 - Performance + cleanup
3. **Cold Storage** 🟢 - Debug capability
4. **Shared Memory Files** 🟢 - Better handover
5. **BM25S Retrieval** 🟢 - Better RAG
6. **Recovery Manager** 🟡 - Resilience
7. **Session Branching** 🟡 - Better parallelism
8. **Memory Backend Abstraction** 🟡 - Extensibility
9. **Agent Persistence** 🟢 - Agent memory
10. **Agent-as-MCP-Tool** 🔴 - Future vision
