# Session NCM Phase 0.1 Implementation

**Date**: 2026-01-22
**Objectif**: Implémenter NCM Phase 0.1 - Core Components avec intégration OrchestratorV7
**Référence**: Plan NCM (misty-juggling-glacier.md)
**Durée estimée**: 1 semaine (Week 1 de Phase 0)

---

## Contexte

### Pourquoi ce Changement?

**Session précédente** (2026-01-21): Tentative d'utiliser CLIs externes (OpenCode, Kimi)
- **Résultat**: 23% de succès (7/30 stories)
- **Problèmes**: 77% d'échecs, timeouts, pas de contrôle sur modèles, NEXUS non utilisé

**Décision**: Revenir au plan NCM original (misty-juggling-glacier.md)
- **Architecture**: NCM = Client de OrchestratorV7 (pas des CLIs externes)
- **Stratégie**: Meta-Bootstrapping (NEXUS se corrige lui-même)
- **Validation**: Phase 0 stress tests AVANT production

---

## Phase 0.1 Objectifs (Week 1)

Implémenter 5 composants core selon le plan:

1. ✅ **NCMOrchestrator** (`core/ncm/orchestrator.py`)
   - Story queue coordinator
   - Invokes `OrchestratorV7.process_turn()` for each story
   - Token budget monitoring
   - State snapshots every 100 stories
   - Prompt refresh every 500 tool calls

2. ✅ **StoryShardEngine** (`core/ncm/story_shard.py`)
   - Parse audit report → story queue
   - RAG validation gate (blind spot #4 mitigation)
   - Priority assignment (P0/P1/P2)
   - Domain classification (CODING/SECURITY/TESTING/etc.)

3. ✅ **CrewManager** (`core/ncm/crew_manager.py`)
   - Agent assignment with skill matrix
   - Fault isolation (prevent file races)
   - Swarm mode selection (PARALLEL/SEQUENTIAL/LEAD_SUPPORT/etc.)
   - Workload balancing

4. ✅ **LockManager** (`core/ncm/locks.py`)
   - File locking layer (asyncio.Lock per file)
   - Timeout mechanism (avoid deadlock)
   - Blind spot #2 mitigation

5. ✅ **Pydantic Models** (`core/ncm/models.py`)
   - Story, StoryPriority, IssueDomain, StoryStatus
   - CrewAssignment, AgentSkill
   - Field validators

---

## Architecture NCM

```
┌────────────────────────────────────────────────────────┐
│  NCM Layer (NEW - Phase 0.1)                          │
│  ┌──────────────────────────────────────────────────┐ │
│  │  NCMOrchestrator                                  │ │
│  │  - Story queue management                         │ │
│  │  - Crew assignment (via CrewManager)             │ │
│  │  - Progress tracking                              │ │
│  └──────────────────────────────────────────────────┘ │
│                       ↓                                │
│  ┌──────────────────────────────────────────────────┐ │
│  │  Story → OrchestratorV7.process_turn()           │ │
│  │  (NCM invokes NEXUS for each story)              │ │
│  └──────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────┘
                        ↓
┌────────────────────────────────────────────────────────┐
│  NEXUS Core (EXISTING - No changes)                    │
│  - OrchestratorV7 (FSM Controller)                     │
│  - HiveMind Pipeline (7 phases)                        │
│  - Swarm Engine (6 modes)                              │
│  - RAG System (HybridBackend RRF)                      │
│  - Evolution (AgentService)                            │
│  - Security (7 layers)                                 │
└────────────────────────────────────────────────────────┘
```

**Key Principle**: NCM ne remplace PAS NEXUS, il l'utilise.

---

## Chronologie

### 2026-01-22 10:45 - Session Start

**Décision documentée**: Abandon de l'approche CLI externe
**Plan**: Implémenter Phase 0.1 selon misty-juggling-glacier.md

### 2026-01-22 10:50 - Création des fichiers de base

**À créer**:
- `core/ncm/models.py` - Pydantic models (Story, etc.)
- `core/ncm/orchestrator.py` - NCMOrchestrator
- `core/ncm/story_shard.py` - StoryShardEngine
- `core/ncm/crew_manager.py` - CrewManager
- `core/ncm/locks.py` - LockManager
- `core/ncm/prompt_refresh.py` - PromptRefreshSystem (blind spot #3)
- `core/ncm/token_monitor.py` - TokenBudgetMonitor (blind spot #5)
- `core/ncm/snapshot.py` - StateSnapshotSystem (blind spot #6)

---

## Code Patterns à Suivre

**NEXUS conventions (CRITICAL)**:
- ✅ Pydantic BaseModel with field_validator
- ✅ Google-style docstrings (Args, Returns, Raises)
- ✅ Type hints (100% coverage)
- ✅ Structlog for logging (with context dicts)
- ✅ Async/await for I/O operations
- ✅ No external dependencies (standard library only)

**Example Template** (from plan):
```python
from pydantic import BaseModel, field_validator
from typing import List, Dict, Optional
from pathlib import Path
import structlog

logger = structlog.get_logger(__name__)

class MyDataModel(BaseModel):
    """Brief description."""
    field_name: str

    @field_validator('field_name')
    @classmethod
    def validate_field(cls, v: str) -> str:
        """Validate field_name."""
        if not v:
            raise ValueError("field_name cannot be empty")
        return v
```

---

## Blind Spots Mitigations (8 Total)

Tous implémentés en Phase 0.1:

| Blind Spot | Mitigation | Implementation |
|------------|-----------|----------------|
| #1 Coordination Complexity | Leverage OrchestratorV7 | NCM as client (not replacement) |
| #2 File Races | File locking layer | `core/ncm/locks.py` (asyncio.Lock) |
| #3 Prompt Decay | Refresh every 500 calls | `core/ncm/prompt_refresh.py` |
| #4 RAG Context Poisoning | Validation gate | `story_shard.py._validate_rag_context()` |
| #5 Token Budget Exhaustion | Monitor + alert | `core/ncm/token_monitor.py` |
| #6 State Corruption | Snapshots every 100 stories | `core/ncm/snapshot.py` |
| #7 Test Regression Cascades | Validate after each story | `orchestrator.py._validate_story_result()` |
| #8 Agent Skill Mismatch | Skill matrix + crew assignment | `core/ncm/crew_manager.py` |

---

## Success Criteria (Phase 0.1)

**Code Artifacts Created**:
- [ ] `core/ncm/models.py` - Pydantic models
- [ ] `core/ncm/orchestrator.py` - NCMOrchestrator
- [ ] `core/ncm/story_shard.py` - StoryShardEngine
- [ ] `core/ncm/crew_manager.py` - CrewManager
- [ ] `core/ncm/locks.py` - LockManager
- [ ] `core/ncm/prompt_refresh.py` - PromptRefreshSystem
- [ ] `core/ncm/token_monitor.py` - TokenBudgetMonitor
- [ ] `core/ncm/snapshot.py` - StateSnapshotSystem

**Unit Tests Created**:
- [ ] `tests/ncm/test_ncm_orchestrator.py`
- [ ] `tests/ncm/test_story_shard.py`
- [ ] `tests/ncm/test_crew_manager.py`
- [ ] `tests/ncm/test_locks.py`

**All Tests Pass**:
- [ ] `pytest tests/ncm/ -v` (100% pass)

**Ready for Phase 0.2**:
- [ ] Evolution TODOs completed (manager.py lines 177, 512, 552)
- [ ] Mitigations implemented (8 blind spots)

---

## Next Steps After Phase 0.1

**Phase 0.2 (Week 2)**:
- Complete Evolution system (manager.py TODOs)
- Implement mitigations (refresh, monitor, snapshot)

**Phase 0.3 (Week 2-3)**:
- Stress test (1000 synthetic stories + 6 agents)
- Validate 95% success, 90% recovery, <1% panic
- No deadlocks, no file races

**Phase 1 (Week 4)**:
- Pilot with 100 real stories (low-risk)
- Go/No-Go decision

---

**Statut**: EN COURS - Implémentation Phase 0.1
**Dernière mise à jour**: 2026-01-22T10:50:00
