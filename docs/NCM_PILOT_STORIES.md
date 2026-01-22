# NCM Pilot Stories - Phase 1 Mini (10 Stories)

**Date**: 2026-01-22
**Target**: Test NCM + NEXUS real integration
**Stories**: 10 P2 simple stories (5 dead imports + 5 docstrings)

---

## Stories List

### PILOT-001: Remove unused import (CLEANUP)
**File**: `core/drivers/gemini_driver_v7.py`
**Task**: Remove unused 're' import from line ~15
**Domain**: CLEANUP
**Priority**: P2
**Expected Duration**: 1-2 min

**Command**:
```
Remove the unused 're' import from core/drivers/gemini_driver_v7.py around line 15
```

---

### PILOT-002: Remove unused import (CLEANUP)
**File**: `core/hive_mind/orchestrator.py`
**Task**: Remove unused 'time' import from line ~12
**Domain**: CLEANUP
**Priority**: P2
**Expected Duration**: 1-2 min

**Command**:
```
Remove the unused 'time' import from core/hive_mind/orchestrator.py around line 12
```

---

### PILOT-003: Remove unused import (CLEANUP)
**File**: `core/swarm/hybrid_swarm_engine.py`
**Task**: Remove unused 'os' import from line ~8
**Domain**: CLEANUP
**Priority**: P2
**Expected Duration**: 1-2 min

**Command**:
```
Remove the unused 'os' import from core/swarm/hybrid_swarm_engine.py around line 8
```

---

### PILOT-004: Remove unused import (CLEANUP)
**File**: `core/memory/backends/hybrid.py`
**Task**: Remove unused 'sys' import from line ~10
**Domain**: CLEANUP
**Priority**: P2
**Expected Duration**: 1-2 min

**Command**:
```
Remove the unused 'sys' import from core/memory/backends/hybrid.py around line 10
```

---

### PILOT-005: Remove unused import (CLEANUP)
**File**: `core/execution/tool_manager.py`
**Task**: Remove unused 'json' import from line ~14
**Domain**: CLEANUP
**Priority**: P2
**Expected Duration**: 1-2 min

**Command**:
```
Remove the unused 'json' import from core/execution/tool_manager.py around line 14
```

---

### PILOT-006: Add module docstring (DOCUMENTATION)
**File**: `core/drivers/protocol.py`
**Task**: Add docstring to DriverProtocol class
**Domain**: DOCUMENTATION
**Priority**: P2
**Expected Duration**: 2-3 min

**Command**:
```
Add a comprehensive docstring to the DriverProtocol class in core/drivers/protocol.py explaining its purpose and usage
```

---

### PILOT-007: Add method docstring (DOCUMENTATION)
**File**: `core/ncm/locks.py`
**Task**: Add docstring to LockManager.__init__ method
**Domain**: DOCUMENTATION
**Priority**: P2
**Expected Duration**: 2-3 min

**Command**:
```
Add a docstring to the LockManager.__init__ method in core/ncm/locks.py with Args description
```

---

### PILOT-008: Add function docstring (DOCUMENTATION)
**File**: `core/swarm/negotiation_protocol.py`
**Task**: Add docstring to negotiate_mode function
**Domain**: DOCUMENTATION
**Priority**: P2
**Expected Duration**: 2-3 min

**Command**:
```
Add a comprehensive docstring to the negotiate_mode function in core/swarm/negotiation_protocol.py with Args, Returns, and description
```

---

### PILOT-009: Add method docstring (DOCUMENTATION)
**File**: `core/memory/backends/bm25.py`
**Task**: Add docstring to BM25Backend.query method
**Domain**: DOCUMENTATION
**Priority**: P2
**Expected Duration**: 2-3 min

**Command**:
```
Add a docstring to the BM25Backend.query method in core/memory/backends/bm25.py with Args and Returns
```

---

### PILOT-010: Add class docstring (DOCUMENTATION)
**File**: `core/execution/handlers/base.py`
**Task**: Add docstring to BaseHandler class
**Domain**: DOCUMENTATION
**Priority**: P2
**Expected Duration**: 2-3 min

**Command**:
```
Add a comprehensive docstring to the BaseHandler class in core/execution/handlers/base.py explaining its purpose and interface
```

---

## Execution Plan

### Option A: Manual Execution (Recommended)
Execute each story one by one in NEXUS REPL:

```
nexus7> [paste command from above]
```

Track results manually and note success/failure.

### Option B: Automated Script
Run the pilot script:

```bash
python scripts/ncm_pilot.py
```

Note: Requires OrchestratorV7 instance (run from within NEXUS session).

---

## Success Criteria

- **80%+ completion rate** (8/10 stories)
- **No syntax errors** introduced
- **Tests still pass** after changes
- **Average duration** < 3 min/story

---

## Tracking Results

| Story | Status | Duration | Notes |
|-------|--------|----------|-------|
| PILOT-001 | ⏳ | - | - |
| PILOT-002 | ⏳ | - | - |
| PILOT-003 | ⏳ | - | - |
| PILOT-004 | ⏳ | - | - |
| PILOT-005 | ⏳ | - | - |
| PILOT-006 | ⏳ | - | - |
| PILOT-007 | ⏳ | - | - |
| PILOT-008 | ⏳ | - | - |
| PILOT-009 | ⏳ | - | - |
| PILOT-010 | ⏳ | - | - |

**Legend**: ⏳ Pending | ✅ Success | ❌ Failed | ⚠️ Partial
