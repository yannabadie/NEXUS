# NEXUS V8.2.0 - Session de développement

**Généré**: 2025-12-09
**Contexte**: Post-vérification roadmap - 7 tâches complétées, 7 restantes

---

## Contexte

Tu es Claude, collaborateur de NEXUS V8.0 TRUE HIVE MIND.
La roadmap a été vérifiée - 7 tâches complétées, 7 restantes.

### Étapes Complétées ✅

| Version | Tâche | Preuves |
|---------|-------|---------|
| V8.0.1 | Hot-Swap Lead Agent | `stagnation_detector.py`, `orchestrator.py:387` |
| V8.1.6 | Thread-Safe Parallel | `async_adapter.py`, `session_uuid` dans drivers |
| V8.1.8 | Dynamic Spawn Brainstorm | `repl.py:spawn_agent()`, `brainstorm.py:mode="prompt"` |
| V8.1.8-B | Model Selection | `agent_invoker.py:245-247`, `InferenceConfig` |
| V8.1.9 | RAG Commands | `commands.py`, `repl.py:handle_rag_command()` |
| V8.2.0-pre | SuccessMemory Hook | `orchestrator.py:455`, `success_adapter.py` |
| V8.2.0-pre | UUID Propagation | `agent_metrics.py:105`, `agent_loader.py:140` |

---

## Objectif de cette session

Implémenter les étapes suivantes par priorité:

### 1. V8.0.2 - Fix 16 tests flaky [P1] (~4h)

**Fichiers à créer/modifier:**
- `.github/workflows/ci.yml` (NOUVEAU)
- `tests/test_llm_context_isolation.py:37` (fix AUTO_SKIP)
- `requirements-dev.txt` (NOUVEAU si absent)

**Actions:**
1. Lire `tests/test_llm_context_isolation.py` pour comprendre AUTO_SKIP
2. Créer CI workflow avec `SKIP_LLM_TESTS=1`
3. Améliorer le skip conditionnel pour tests LLM réels

---

### 2. V8.2.0a - Unified Analysis Adapter [P2] (~5h)

**Fichiers à créer:**
- `core/adapters/__init__.py` (NOUVEAU)
- `core/adapters/analysis_adapter.py` (NOUVEAU)

**Actions:**
1. Créer le dossier `core/adapters/`
2. Implémenter `AnalysisAdapter` avec mapping bidirectionnel
3. Intégrer dans Memory Boost flow (`mode_selector.py`)
4. Tests unitaires

**Code de référence:**
```python
# core/adapters/analysis_adapter.py (NOUVEAU)
from core.swarm.task_analyzer import TaskAnalysis, TaskComplexity
from core.hive_mind.types import IndependentAnalysis

class AnalysisAdapter:
    """Bidirectional adapter between Swarm and HiveMind analysis types."""

    COMPLEXITY_MAP = {
        "trivial": TaskComplexity.TRIVIAL,
        "simple": TaskComplexity.SIMPLE,
        "moderate": TaskComplexity.MODERATE,
        "complex": TaskComplexity.COMPLEX,
        "expert": TaskComplexity.EXPERT,
    }

    @classmethod
    def to_task_analysis(cls, hive: IndependentAnalysis, raw_input: str) -> TaskAnalysis:
        complexity_str = str(hive.complexity_assessment).lower()
        complexity = next(
            (v for k, v in cls.COMPLEXITY_MAP.items() if k in complexity_str),
            TaskComplexity.MODERATE
        )
        return TaskAnalysis(
            complexity=complexity,
            raw_input=raw_input,
            confidence=getattr(hive, 'confidence', 0.5)
        )
```

---

### 3. V8.2.0c - RedTeam Post-Spawn [P2] (~4h)

**Fichiers à modifier:**
- `core/interface/repl.py` (spawn_agent)
- `core/config.py` (REDTEAM_SPAWN_MANDATORY)

**Actions:**
1. Ajouter config `redteam_spawn_mandatory`
2. Intégrer RedTeamValidator dans spawn_agent()
3. Logging des scores d'alignement

---

### 4. V8.0.3 - EPHEMERAL Sessions [P2] (~4h)

**Fichiers à modifier:**
- `core/swarm/task_analyzer.py` (fast-track)
- `core/swarm/hybrid_swarm_engine.py`

**Actions:**
1. Activer SessionMode.EPHEMERAL pour complexity < 0.15
2. Skip RAG pour tâches EPHEMERAL
3. Tests de performance (<2s pour TRIVIAL)

---

## Contraintes

- NE PAS casser les fonctionnalités existantes
- Commits atomiques avec messages descriptifs
- Tests pour chaque nouvelle fonctionnalité
- Suivre le pattern de la codebase existante

## Références

- `ROADMAP.md` sections V8.0.2, V8.0.3, V8.2.0a, V8.2.0c
- `docs/ARCHITECTURE_MAP_V8.1.md` pour architecture globale
- `CODEBASE_SNAPSHOT.md` pour structure fichiers

## Commencer par

Lis d'abord `tests/test_llm_context_isolation.py` pour comprendre le problème des tests flaky.
