# NEXUS V8.2.0 - Session de Développement

**Généré**: 2025-12-09
**Contexte**: Post-vérification roadmap complète - 8 tâches complétées, 11+ restantes

---

## Contexte

Tu es Claude, collaborateur de NEXUS V8.0 TRUE HIVE MIND.
La roadmap a été vérifiée contre le code réel.

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
| V8.0.3 | EPHEMERAL Sessions | `session_manager.py:46,272-275` (PARTIAL - mode activé pour TRIVIAL) |

---

## Objectif de cette session

Implémenter les étapes suivantes par priorité:

### 1. V8.0.2 - Fix 16 tests flaky [P1] (~4h)

**Problème**: Les 16 tests flaky sont des tests RÉELS appelant l'API Gemini.
AUTO_SKIP existe déjà (`tests/test_llm_context_isolation.py:32-37`) mais pas de CI workflow.

**Fichiers à créer/modifier:**
- `.github/workflows/ci.yml` (NOUVEAU)
- `requirements-dev.txt` (NOUVEAU si absent)

**Actions:**
1. Vérifier que AUTO_SKIP fonctionne (`SKIP_LLM_TESTS=1`)
2. Créer CI workflow GitHub Actions avec `SKIP_LLM_TESTS=1`
3. Ajouter matrix Python 3.11/3.12/3.13

**Exemple CI workflow:**
```yaml
name: NEXUS CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ['3.11', '3.12', '3.13']
    env:
      SKIP_LLM_TESTS: 1
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      - run: pip install -r requirements.txt -r requirements-dev.txt
      - run: python -m pytest tests/ -v --tb=short
```

---

### 2. V8.1.0 - Decay Formula SuccessMemory [P1] (~2h)

**Problème**: `record_success()` existe mais pas de decay à la lecture.
Les vieux succès ont le même poids que les récents.

**Fichier à modifier:**
- `core/memory/success_memory.py` - méthode `get_best_mode_for_similar()`

**Formule à implémenter:**
```python
def _apply_decay(self, similarity: float, record_timestamp: datetime) -> float:
    """Apply time decay to similarity score."""
    age_weeks = (datetime.now() - record_timestamp).days / 7
    decay_factor = 1 / (1 + 0.05 * age_weeks)
    return similarity * decay_factor
```

---

### 3. V8.2.0a - Unified Analysis Adapter [P2] (~3h)

**Problème**: `TaskAnalysis` (Swarm) et `IndependentAnalysis` (HiveMind) incompatibles.
`success_adapter.py` existe mais spécifique à SuccessMemory.

**Fichiers à créer:**
- `core/adapters/__init__.py` (NOUVEAU)
- `core/adapters/analysis_adapter.py` (NOUVEAU)

**Code de référence:**
```python
# core/adapters/analysis_adapter.py
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

### 4. V8.2.0c - RedTeam Post-Spawn [P2] (~2h)

**Problème**: RedTeam validation existe pour `/evolve` mais pas pour `/spawn`.

**Fichiers à modifier:**
- `core/interface/repl.py` (spawn_agent)
- `core/config.py` (REDTEAM_SPAWN_MANDATORY)

**Actions:**
1. Ajouter config `redteam_spawn_mandatory: bool = False`
2. Intégrer RedTeamValidator dans spawn_agent() après génération prompt
3. Logging des scores d'alignement

---

### 5. V8.0.3 - EPHEMERAL Sessions Completion [P2] (~2h)

**État actuel**: Mode EPHEMERAL existe et est activé pour TRIVIAL tasks.
**Manque**: Skip RAG pour tâches EPHEMERAL, métriques de performance.

**Fichiers à modifier:**
- `core/swarm/hybrid_swarm_engine.py` - Skip RAG injection pour EPHEMERAL
- Tests de performance (<2s pour TRIVIAL)

---

### 6. V8.2.0d - Torture Protocol V8 [P2] (~4h)

**Fichier à créer:**
- `tests/torture_v8.py` (NOUVEAU)

**Scénarios de base:**
```python
TORTURE_SCENARIOS = [
    {"name": "parallel_flood", "concurrent_tasks": 10, "mode": "PARALLEL"},
    {"name": "stagnation_loop", "similar_tasks": 5, "expect_hot_swap": True},
    {"name": "budget_drain", "expensive_tasks": 20, "expect_budget_error": True},
]
```

---

## Contraintes

- NE PAS casser les fonctionnalités existantes
- Commits atomiques avec messages descriptifs
- Tests pour chaque nouvelle fonctionnalité
- Suivre le pattern de la codebase existante

## Références

- `ROADMAP.md` - Source de vérité pour les tâches
- `docs/ARCHITECTURE_MAP_V8.1.md` - Architecture globale
- `CODEBASE_SNAPSHOT.md` - Structure fichiers

## Commencer par

**Option A**: CI/CD (V8.0.2) - Impact immédiat sur stabilité
**Option B**: Decay Formula (V8.1.0) - Améliore apprentissage SuccessMemory
**Option C**: Unified Adapter (V8.2.0a) - Unifie types Swarm/HiveMind

---

## Prochaines Sessions (Backlog)

| Priorité | Version | Tâche | Effort |
|----------|---------|-------|--------|
| P2 | V8.1.1 | LLM Provider Registry | 8h |
| P2 | V8.1.3 | Self-Healing Fallback | 6h |
| P2 | V8.1.4 | Rate Limiting (ProviderGuard) | 5h |
| P3 | V8.1.5 | Intent Resolver | 6h |
| P3 | V8.1.7 | TaskAnalysis.reasoning field | 2h |
| P3 | V8.2.0b | Architecture Map Update | 2h |
