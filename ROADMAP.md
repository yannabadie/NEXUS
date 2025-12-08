# NEXUS V8.0 "TRUE HIVE MIND" - Roadmap Opérationnelle

**Version**: 8.0.1 | **Status**: Active | **Last Updated**: 2025-12-08
**Maintainer**: Yann Abadie | **Branch**: N8THM

---

## Objectif V8.0

Stabiliser et durcir le système "TRUE HIVE MIND" pour un usage quotidien fiable avant d'envisager des évolutions majeures.

**Mantra** : *"Solidifier avant d'innover"*

---

## État Actuel (2025-12-08)

| Métrique | Valeur |
|----------|--------|
| Modules core/ | 24 |
| Fichiers Python | 124 |
| Lignes de code | 42,831 |
| Tests | 1,094 (16 flaky) |
| Phases complétées | 15 |

### Composants Stables ✅

- **Swarm Engine** : 6 modes de collaboration fonctionnels
- **Hive Mind** : Pipeline 7 phases opérationnel
- **Project Memory** : RAG avec Dense backend (LanceDB + MiniLM)
- **MCP Client** : 36 tests, zero-dependency
- **Security** : SandboxPolicy, CodeValidator

### Gaps Opérationnels ⚠️

| ID | Gap | Impact | Priorité |
|----|-----|--------|----------|
| OP-001 | Hot-Swap Lead non intégré dans retry loop | Stagnation non récupérée | ✅ DONE (V8.0.1) |
| OP-002 | 16 tests flaky (context isolation) | CI instable | P1 |
| OP-003 | EPHEMERAL sessions non activé | Overhead sur tâches triviales | P2 |
| OP-004 | Phase 5b hardcoded lookups | Tech debt mineur | P3 |
| OP-005 | Sync drivers in async context | PARALLEL = séquentiel déguisé | P1 (NEW) |

---

## Roadmap V8.0.x (Stabilisation)

### V8.0.1 - Hot-Swap & Documentation ✅ COMPLETED (2025-12-08)

| Tâche | Status | Fichiers |
|-------|--------|----------|
| Hot-Swap Lead Agent | ✅ Done | `stagnation_detector.py`, `orchestrator.py` |
| KI-001 Documentation | ✅ Done | `docs/KNOWN_ISSUES.md` |
| Tests Hot-Swap | ✅ Done | `tests/test_hot_swap_lead.py` (14 tests) |

**Commits**: `15aff32`, `30b2032`

---

### V8.0.2 - Tests Stability [Priority: P1]

**Objectif** : 99%+ test pass rate

| Tâche | Effort | Status |
|-------|--------|--------|
| Fix auto-skip pour tests LLM réels | 2h | PLANNED |
| Add SKIP_LLM_TESTS=1 dans CI | 30min | PLANNED |
| CI/CD GitHub Actions setup | 4h | PLANNED |

**Analyse** (Gemini Deep Think + Claude verification):
- Les 16 tests flaky sont des **tests RÉELS** appelant l'API Gemini
- ≠ "State pollution" (conftest.py a déjà MockDriver/MockConfig)
- Fix: Améliorer `AUTO_SKIP` dans `test_llm_context_isolation.py:37`

**Fichiers concernés**:
- `tests/test_llm_context_isolation.py` (fix AUTO_SKIP logic)
- `.github/workflows/ci.yml` (NEW, avec SKIP_LLM_TESTS=1)
- `requirements-dev.txt` (NEW)

---

### V8.0.3 - EPHEMERAL Sessions [Priority: P2]

**Objectif** : Skip persistence pour tâches TRIVIAL (<2s)

| Tâche | Effort | Status |
|-------|--------|--------|
| Activer SessionMode.EPHEMERAL | 2h | PLANNED |
| Fast-Track dans TaskAnalyzer | 2h | PLANNED |
| Intégrer dans HybridSwarmEngine | 2h | PLANNED |
| Tests EPHEMERAL | 2h | PLANNED |

**Pattern Fast-Track** (Gemini Deep Think):
```python
# core/swarm/task_analyzer.py
def analyze(self, request: str) -> TaskProfile:
    complexity = self._compute_complexity(request)
    if complexity < 0.15:  # Seuil TRIVIAL
        return TaskProfile(
            mode=SessionMode.EPHEMERAL,
            pipeline_depth=1,  # Direct: Input → Agent → Output
            priority=Priority.REALTIME
        )
```

**Fichiers concernés**:
- `core/swarm/session_manager.py` (SessionMode.EPHEMERAL existe, ligne 46)
- `core/swarm/task_analyzer.py` (add fast-track logic)
- `core/swarm/hybrid_swarm_engine.py` (ligne 274 - déjà préparé)

**Trade-off**: Pas d'enregistrement RAG pour tâches EPHEMERAL (amnésie volontaire)

**Source** : Gemini (2025-12-04), validé Gemini Deep Think (2025-12-08)

---

### V8.0.4 - Documentation Sync [Priority: P2]

**Objectif** : Documentation alignée avec code

| Tâche | Effort | Status |
|-------|--------|--------|
| Update CLAUDE.md (structure V8) | 2h | PLANNED |
| Archiver ROADMAP_HIVE_MIND.md obsolète | 30min | PLANNED |
| Générer module READMEs manquants | 4h | PLANNED |

---

## Roadmap V8.1 (Renforcement)

### V8.1.0 - Success Memory Activation [Priority: P1]

**Objectif** : Fermer le feedback loop ModeSelector ↔ SuccessMemory ("Reader" → "Writer")

| Tâche | Effort | Status |
|-------|--------|--------|
| Implémenter hook `record_success()` dans HiveMindPipeline.run() | 3h | PLANNED |
| Implémenter critères de "Worthiness" | 2h | PLANNED |
| Implémenter Decay à la lecture | 2h | PLANNED |
| Tests E2E memory feedback loop | 3h | PLANNED |

**Clarification** (Claude verification):
- `_apply_memory_boost()` **EXISTE DÉJÀ** (mode_selector.py:614-685)
- Utilise `success_memory.get_best_mode_for_similar()` avec semantic search
- **MANQUE**: L'écriture (record_success) n'est jamais appelée!

**Spécifications** (Gemini Deep Think v2 - CORRIGÉ par Claude):

**1. Hook Point** - Dans `TrueHiveMind.process_task()` ligne ~420:
```python
# core/hive_mind/orchestrator.py - après consolidation, avant return
# ATTENTION: analysis_result est AnalysisPhaseResult, PAS TaskAnalysis!

if execution_success and self.success_memory:
    # Adapter IndependentAnalysis → format compatible record_success
    pseudo_analysis = self._adapt_for_memory(analysis_result, task)
    quality = 1.0 - (retry_count * 0.1)  # Pénalité par retry
    self.success_memory.record_success(
        task_id=f"hive_{int(start_time)}",
        analysis=pseudo_analysis,
        result=execution_result,
        quality_score=max(0.1, quality)
    )
```

**⚠️ DÉCOUVERTE CRITIQUE** (Claude verification):
- `analysis_result` est `AnalysisPhaseResult` avec `IndependentAnalysis`
- `record_success()` attend `TaskAnalysis` (structure DIFFÉRENTE!)
- **BESOIN**: Méthode adapter `_adapt_for_memory()` pour convertir

**⚠️ CORRECTION Gemini Deep Think v3** (2025-12-08):
- Gemini proposait `TaskAnalysis(reasoning=...)` - CE CHAMP N'EXISTE PAS!
- Champs RÉELS de TaskAnalysis (task_analyzer.py:159-187):
  - `complexity`, `domains`, `primary_domain`
  - `requires_web`, `requires_code_execution`, `requires_deep_reasoning`, `requires_iteration`
  - `gemini_fit_score`, `claude_fit_score`, `confidence`
  - `raw_input`, `detected_keywords`

**Adapter CORRIGÉ**:
```python
def _adapt_for_memory(self, analysis: 'IndependentAnalysis', raw_task: str) -> 'TaskAnalysis':
    from core.swarm.task_analyzer import TaskAnalysis, TaskComplexity, TaskDomain

    comp_str = str(getattr(analysis, "complexity_assessment", "moderate")).lower()
    complexity_map = {"trivial": TaskComplexity.TRIVIAL, "simple": TaskComplexity.SIMPLE,
                      "complex": TaskComplexity.COMPLEX, "expert": TaskComplexity.EXPERT}
    complexity = next((v for k, v in complexity_map.items() if k in comp_str), TaskComplexity.MODERATE)

    return TaskAnalysis(
        complexity=complexity,
        domains=[TaskDomain.UNKNOWN],
        primary_domain=TaskDomain.UNKNOWN,
        raw_input=raw_task,
        confidence=getattr(analysis, "confidence", 0.5)
        # Autres champs gardent leurs defaults
    )
```

**2. Critères de Worthiness** (adapté à HiveMindResult réel):
```python
def should_record(result: HiveMindResult, complexity) -> bool:
    return all([
        result.success == True,
        complexity > TaskComplexity.TRIVIAL,  # Pas les tâches simples
        len(result.phases_completed) >= 4,
        result.error is None
    ])
```

**3. Decay à la lecture** (obsolescence progressive) - VALIDE:
```python
# core/memory/success_memory.py - dans get_best_mode_for_similar()
effective_score = similarity * (1 / (1 + 0.05 * age_in_weeks))
```

**⚠️ CORRECTION Gemini Deep Think v4** (2025-12-08):
- Gemini proposait `analysis_result.payload` - CE CHAMP N'EXISTE PAS!
- Gemini proposait `HiveMindState.HIVE_COMPLETE` - C'EST `HIVE_SUCCESS`!

**Structure RÉELLE AnalysisPhaseResult** (phase_analysis.py:67):
```python
@dataclass
class AnalysisPhaseResult:
    gemini_analysis: IndependentAnalysis  # ← Utiliser ceci
    claude_analysis: IndependentAnalysis
    comparison: AnalysisComparison
    needs_debate: bool
    skip_reason: Optional[str] = None
    # PAS DE CHAMP .payload !
```

**Hook CORRIGÉ** (orchestrator.py ~ligne 438):
```python
# Capturer l'analyse dès Phase 1 (ligne ~272)
analysis_result = await self.phase_analysis.execute(task)
captured_analysis = analysis_result.gemini_analysis  # ✅ Pas .payload

# Hook avant return (ligne ~438)
if execution_success and self.success_memory:
    if len(phases_completed) >= 3:
        quality = 1.0 - (sum(1 for p in phases_completed if "retry" in str(p).lower()) * 0.15)
        if quality >= 0.7:
            swarm_analysis = self._adapt_analysis_for_memory(captured_analysis, task)
            self.success_memory.record_success(...)

self._set_state(HiveMindState.HIVE_SUCCESS)  # ✅ Pas HIVE_COMPLETE
return HiveMindResult(...)
```

**Fichiers concernés**:
- `core/hive_mind/orchestrator.py` - AJOUTER hook dans process_task()
- `core/memory/success_memory.py` - AJOUTER decay formula
- `core/swarm/mode_selector.py` - VÉRIFIER activation

---

### V8.1.1 - LLM Provider Registry [Priority: P2]

**Objectif** : Éliminer les hardcoded lookups (60+ occurrences trouvées)

| Tâche | Effort | Status |
|-------|--------|--------|
| Créer interface BaseLLMProvider | 2h | PLANNED |
| Implémenter LLMProviderRegistry | 3h | PLANNED |
| Wrapper Claude & Gemini drivers | 2h | PLANNED |
| Migration progressive | 4h | PLANNED |
| Tests regression | 2h | PLANNED |

⚠️ **ATTENTION**: `AgentRegistry` EXISTE DÉJÀ dans `core/hive_mind/agent_registry.py`
mais c'est pour les agents SPAWNED, pas pour Claude/Gemini providers.
→ Nouveau module: `core/llm/provider_registry.py`

**Pattern Provider Factory** (Gemini Deep Think - adapté):
```python
# core/llm/provider_registry.py (NOUVEAU)
class LLMProviderRegistry:
    _providers = {}

    @classmethod
    def register(cls, name):
        def decorator(provider_cls):
            cls._providers[name.lower()] = provider_cls
            return provider_cls
        return decorator

    @classmethod
    def get_provider(cls, name: str) -> "BaseLLMProvider":
        return cls._providers[name.lower()]()

# Usage: LLMProviderRegistry.get_provider("claude").invoke(...)
```

**Fichiers concernés** (60+ occurrences trouvées):
- `core/orchestration/fsm_handlers.py` (8)
- `core/utils/stream_parser.py` (10)
- `core/orchestration/agent_invoker.py` (4)
- `core/orchestration/context_builder.py` (3)
- `core/hive_mind/phases/phase_debate.py` (12)
- `core/hive_mind/phases/phase_execution.py` (3)
- Autres (20+)

**Référence**: KI-002 dans `docs/KNOWN_ISSUES.md`

---

### V8.1.2 - Monitoring & Observability [Priority: P2]

**Objectif** : Visibilité sur le comportement en production

| Tâche | Effort | Status |
|-------|--------|--------|
| Prometheus metrics exporter | 4h | PLANNED |
| Dashboard basique (Grafana JSON) | 2h | PLANNED |
| Alert on PANIC states | 2h | PLANNED |

**Métriques clés**:
- `nexus_tasks_total` (counter)
- `nexus_task_duration_seconds` (histogram)
- `nexus_swarm_mode_selected` (counter by mode)
- `nexus_hive_mind_phase_duration` (histogram by phase)

---

### V8.1.3 - Self-Healing Fallback [Priority: P2] (NEW)

**Objectif** : Robustesse "Bulletproof" via fallback automatique

| Tâche | Effort | Status |
|-------|--------|--------|
| Implémenter fallback PARALLEL → SEQUENTIAL | 3h | PLANNED |
| Fallback chain configurable | 2h | PLANNED |
| Logging des fallbacks | 1h | PLANNED |
| Tests chaos engineering | 3h | PLANNED |

**Pattern Self-Healing** (Gemini Deep Think):
```python
# core/swarm/hybrid_swarm_engine.py
async def execute_with_fallback(self, task, mode):
    fallback_chain = {
        "PARALLEL": ["SEQUENTIAL", "SPECIALIST"],
        "RED_BLUE": ["PING_PONG", "LEAD_SUPPORT"],
        "PING_PONG": ["SEQUENTIAL"]
    }
    try:
        return await self._execute_mode(task, mode)
    except (TimeoutError, RaceConditionError) as e:
        for fallback_mode in fallback_chain.get(mode, ["SEQUENTIAL"]):
            try:
                logger.warning(f"Fallback: {mode} → {fallback_mode}")
                return await self._execute_mode(task, fallback_mode)
            except Exception:
                continue
        raise PanicError("All fallbacks exhausted")
```

**Risque adressé**: Mode PARALLEL crash → PANIC (race conditions, timeouts)

**Source**: Gemini Deep Think (2025-12-08)

---

### V8.1.4 - Rate Limiting Partagé [Priority: P2] (NEW)

**Objectif** : Éviter 429 Too Many Requests en mode PARALLEL

| Tâche | Effort | Status |
|-------|--------|--------|
| Installer aiolimiter | 30min | PLANNED |
| Implémenter ProviderGuard | 3h | PLANNED |
| Intégrer dans AgentInvoker | 2h | PLANNED |
| Tests rate limiting | 2h | PLANNED |

**Architecture Double Verrou** (Gemini Deep Think v2 - Pure asyncio):
```python
# core/drivers/guard.py (NOUVEAU)
# ZERO dépendance externe - asyncio standard lib uniquement

import asyncio
import time

class ProviderGuard:
    """TokenBucket per-provider avec asyncio pur."""
    _buckets = {
        "claude": {"tokens": 50.0, "rate": 0.83, "last": time.time(), "lock": asyncio.Lock()},
        "gemini": {"tokens": 60.0, "rate": 1.00, "last": time.time(), "lock": asyncio.Lock()}
    }

    @classmethod
    async def acquire(cls, provider: str):
        p = cls._buckets.get(provider.lower())
        if not p: return True

        async with p["lock"]:
            now = time.time()
            elapsed = now - p["last"]
            p["tokens"] = min(50, p["tokens"] + (elapsed * p["rate"]))
            p["last"] = now

            if p["tokens"] < 1:
                wait_time = (1 - p["tokens"]) / p["rate"]
                await asyncio.sleep(wait_time + 0.1)
                p["tokens"] = 0
            else:
                p["tokens"] -= 1
```

**Config par défaut**:
- Claude: ~50 RPM (rate=0.83 tokens/sec)
- Gemini: ~60 RPM (rate=1.00 tokens/sec)

**Backoff dans drivers**: Boucle `while` + `try/except` sur 429, `asyncio.sleep(2**attempt)`

**Source**: Gemini Deep Think v2 (2025-12-08) - Validé Claude

---

### V8.1.5 - Intent Resolver (Phase 5b Cleanup) [Priority: P3] (NEW)

**Objectif** : Remplacer les `if "keyword" in msg` par un routeur intelligent

| Tâche | Effort | Status |
|-------|--------|--------|
| Créer IntentResolver (3 layers) | 4h | PLANNED |
| Migrer fsm_handlers.py | 3h | PLANNED |
| Tests intent resolution | 2h | PLANNED |

**⚠️ CLARIFICATION** (Claude verification):
`commands.py` existe DÉJÀ avec `COMMAND_CATEGORIES` pour les commandes système !
```python
# core/interface/commands.py (EXISTE - ligne 58)
COMMAND_CATEGORIES = {
    "⚙️ System": {"/reset", "/status", "/stop", "/help"},
    "🔧 Debug": {"/context", "/state", "/blackboard"},
    ...
}
```

**Le VRAI problème** (60+ occurrences trouvées):
- `if "gemini" in agent_id.lower()` → Hardcoded provider checks
- `if mode.lower() == "claude"` → String comparisons fragiles
- Ces patterns sont dans `fsm_handlers.py`, `stream_parser.py`, `phase_debate.py`, etc.

**Architecture Hybrid Intent Resolver** (Gemini Deep Think - adapté):
```python
# core/fsm/intent_resolver.py (NOUVEAU - complète commands.py)
class IntentResolver:
    """Routeur à 3 étages pour résolution d'intentions."""

    def __init__(self, project_memory: ProjectMemory):
        self.project_memory = project_memory
        self._lru_cache = LRUCache(maxsize=100)

        # Layer 1: Fast-Path - RÉUTILISE commands.py
        from core.interface.commands import COMMAND_CATEGORIES
        self._fast_map = {
            cmd: Intent.SYSTEM_COMMAND
            for cmds in COMMAND_CATEGORIES.values()
            for cmd in cmds
        }

    def resolve(self, user_input: str) -> Intent:
        # Layer 1: Fast-Path (O(1))
        if user_input.startswith("/"):
            cmd = user_input.split()[0]
            if cmd in self._fast_map:
                return self._fast_map[cmd]

        # Layer 2: LRU Cache
        if cached := self._lru_cache.get(user_input):
            return cached

        # Layer 3: Semantic (RAG)
        intent = self._semantic_resolve(user_input)
        self._lru_cache.put(user_input, intent)
        return intent
```

**Relation avec V8.1.1** (LLM Provider Registry):
- V8.1.1 élimine `if "gemini" in` pour les PROVIDERS
- V8.1.5 élimine `if "keyword" in` pour les INTENTS utilisateur
- Les deux sont complémentaires mais distincts

**Source**: Gemini Deep Think (2025-12-08) + Claude corrections

---

### V8.1.6 - Async Driver Wrapper [Priority: P1] (NEW - Gemini Deep Think v3)

**Objectif** : Éliminer le blocage event loop quand async appelle sync

**Problème découvert** (Claude verification 2025-12-08):
- `TrueHiveMind.process_task()` est **async** (orchestrator.py:235)
- Mais les drivers `GeminiDriverV7.invoke()` et `ClaudeDriverHybrid.invoke()` sont **sync**
- Même avec `Popen` + threading, les méthodes bloquent jusqu'à completion
- En mode PARALLEL, un seul agent s'exécute à la fois (pas de vrai parallélisme)

**Note**: Gemini Deep Think affirmait "subprocess.run blocks" - c'est `Popen` en réalité, mais le problème de blocage reste valide.

| Tâche | Effort | Status |
|-------|--------|--------|
| Créer wrapper async pour drivers | 4h | PLANNED |
| Utiliser `asyncio.create_subprocess_exec` | 3h | PLANNED |
| Ou `loop.run_in_executor()` pour Popen | 2h | PLANNED |
| Tests parallelisme réel | 2h | PLANNED |

**⚠️ CORRECTION Gemini Deep Think v4** (2025-12-08):
- Gemini proposait `task_type` comme paramètre - C'EST `session_uuid`!
- Signature correcte: `invoke(context: str, session_uuid: Optional[str] = None)`

**Option A - run_in_executor** (moins invasif):
```python
# core/drivers/async_wrapper.py
import asyncio
from typing import Optional

async def invoke_async(driver, context: str, session_uuid: Optional[str] = None) -> Dict:
    """Wrapper async pour drivers sync - PRESERVES session_uuid parameter."""
    loop = asyncio.get_event_loop()
    # Utilise functools.partial pour passer session_uuid
    from functools import partial
    return await loop.run_in_executor(
        None,
        partial(driver.invoke, context, session_uuid=session_uuid)
    )
```

**Option B - asyncio.create_subprocess_exec** (plus propre):
```python
async def invoke_async(self, context: str, session_uuid: Optional[str] = None) -> Dict:
    """True async subprocess - no event loop blocking."""
    # Write context to file (same as sync version)
    context_file = self.io_buffer / "gemini_context_in.md"
    context_file.write_text(context, encoding="utf-8")

    # Build command with session_uuid if provided
    cmd = [self.cli_path, "-m", self.model, "-p", f"@{context_file}", "-o", "json"]
    if session_uuid:
        cmd.extend(["--session", session_uuid])

    proc = await asyncio.create_subprocess_exec(
        *cmd,
        cwd=str(self.workspace_path),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await proc.communicate()
    return self._parse_output(stdout.decode())
```

**Impact**: Mode PARALLEL passera de "séquentiel déguisé" à "vrai parallèle"

**Fichiers concernés**:
- `core/drivers/gemini_driver_v7.py` - Ajouter `invoke_async()`
- `core/drivers/claude_driver_hybrid.py` - Ajouter `invoke_async()`
- `core/hive_mind/orchestrator.py` - Utiliser les wrappers async

**Source**: Gemini Deep Think v3 (2025-12-08) - Validé Claude

---

### V8.1.7 - TaskAnalysis.reasoning Field [Priority: P3] (NEW - Enhancement)

**Objectif** : Ajouter traçabilité du raisonnement dans TaskAnalysis

**Contexte**:
- Gemini Deep Think a proposé `TaskAnalysis(reasoning=...)`
- Le champ N'EXISTE PAS actuellement
- MAIS c'est une bonne idée pour la traçabilité

**Justification**:
- `ModeProposal` a un champ `reasoning` (mode_selector.py:66)
- `TaskAnalysis` devrait aussi expliquer POURQUOI cette analyse
- Utile pour debug et amélioration du TaskAnalyzer

| Tâche | Effort | Status |
|-------|--------|--------|
| Ajouter `reasoning: str = ""` à TaskAnalysis | 30min | PLANNED |
| Mettre à jour TaskAnalyzer.analyze() | 1h | PLANNED |
| Tests | 30min | PLANNED |

**Modification proposée**:
```python
# core/swarm/task_analyzer.py:159
@dataclass
class TaskAnalysis:
    complexity: TaskComplexity
    domains: List[TaskDomain]
    primary_domain: TaskDomain
    # ... existing fields ...
    reasoning: str = ""  # NEW: Explique le raisonnement de l'analyse
```

**Source**: Suggestion Gemini (hallucination transformée en amélioration)

---

## Roadmap V8.2 (Hardening)

### V8.2.0 - Multi-Tenant Basics [Priority: P2]

**Objectif** : Isolation par tenant pour usage équipe/entreprise

**Qu'est-ce que tenant_id ?**
Le `tenant_id` identifie une **organisation ou un projet isolé** dans une instance NEXUS partagée.
Exemples de tenants :
- `motherson-dev` : Équipe développement Motherson
- `motherson-qa` : Équipe QA Motherson (même entreprise, workspace différent)
- `yann-personal` : Workspace personnel
- `demo-2025` : Instance de démonstration

**Pourquoi Multi-Tenant ?**
En entreprise, plusieurs équipes peuvent utiliser le même serveur NEXUS.
Sans isolation :
- ❌ L'équipe A voit les fichiers de l'équipe B
- ❌ Le RAG retourne des résultats mélangés
- ❌ Un agent spawned peut accéder aux données d'un autre tenant

Avec Multi-Tenant :
- ✅ Chaque équipe a son propre `workspace_root`
- ✅ Le RAG filtre automatiquement par `tenant_id`
- ✅ Isolation stricte même en PARALLEL mode

| Tâche | Effort | Status |
|-------|--------|--------|
| Implémenter SessionContext via contextvars | 3h | PLANNED |
| Filtrage RAG par tenant_id | 2h | PLANNED |
| Filesystem isolation (workspace_root) | 3h | PLANNED |
| Propagation contexte aux agents spawned | 2h | PLANNED |

**Architecture contextvars** (Gemini Deep Think - validé pour Python 3.13):
```python
# core/context.py (NOUVEAU)
import contextvars
from dataclasses import dataclass
from pathlib import Path

current_session = contextvars.ContextVar("session_context")

@dataclass
class SessionContext:
    tenant_id: str
    permissions: list[str]
    workspace_root: Path

# Usage - thread-safe et async-safe
def get_tenant() -> str:
    return current_session.get().tenant_id
```

**Isolation**:
- RAG: `search(q, filter={"tenant": get_tenant()})`
- Filesystem: Outils utilisent `current_session.get().workspace_root` comme base
- Spawn: Contexte propagé automatiquement par Python + copie forcée

**Note**: `contextvars` non utilisé actuellement dans la codebase, mais c'est le pattern standard Flask/FastAPI

**Référence**: Audit2_08122025.md Gap 2

---

### V8.2.1 - Encryption at Rest [Priority: P3]

**Objectif** : Protection des données sensibles

| Tâche | Effort | Status |
|-------|--------|--------|
| EncryptedJsonStore wrapper | 4h | PLANNED |
| Migrate blackboard.json | 2h | PLANNED |
| Migrate birth certificates | 2h | PLANNED |

**Référence**: Audit2_08122025.md Gap 3

---

### V8.2.2 - Local Model Support [Priority: P3]

**Objectif** : Mode air-gapped pour environnements restreints

| Tâche | Effort | Status |
|-------|--------|--------|
| OllamaDriver implementation | 8h | PLANNED |
| Fallback chain: Cloud → Local | 4h | PLANNED |
| Tests offline mode | 4h | PLANNED |

**Référence**: Audit2_08122025.md Gap 1 (BLOQUANT pour Motherson)

---

## Vision Future (V9.0+)

> **Documentée séparément** : `docs/architecture/VISION_V9_SINGULARITY.md`

La V9.0 ("Self-Evolving Intelligence") ne sera envisagée qu'après :
1. V8.2 stable en production
2. Retours terrain (démo Motherson)
3. Test suite à 99%+ pass rate

**Concepts V9.0** (pour mémoire):
- Evolution Intelligence Hub
- Closed-Loop Refinement
- Auto-Specialization Engine
- Unified Memory Layer

---

## Priorités Immédiates (Cette Semaine)

| # | Tâche | Effort | Owner |
|---|-------|--------|-------|
| 1 | ~~Hot-Swap Lead Agent~~ | ~~4h~~ | ✅ Done |
| 2 | Fix 16 tests flaky | 4h | NEXT |
| 3 | CI/CD GitHub Actions | 4h | PLANNED |
| 4 | EPHEMERAL sessions | 4h | PLANNED |

---

## Métriques de Succès V8.x

| Métrique | V8.0 | Target V8.2 | Stratégie |
|----------|------|-------------|-----------|
| Test Pass Rate | 98.5% | 99.5% | Fix AUTO_SKIP + CI/CD |
| Hive Mind Success | ~75% | >90% | SuccessMemory activation |
| Task Completion (TRIVIAL) | ~45s | <2s | SessionMode.EPHEMERAL |
| Task Completion (COMPLEX) | ~45s | <30s | Pipeline depth optimization |
| PANIC Rate | ~5% | <1% | Self-Healing fallback |
| Code Coverage | N/A | 99% | Mocking strict I/O |
| Documentation Coverage | 60% | 90% | V8.0.4 sync |

**Source**: Gemini Deep Think Dashboard (2025-12-08)

---

## Known Issues

Voir `docs/KNOWN_ISSUES.md` pour la liste complète.

| ID | Titre | Sévérité | Status |
|----|-------|----------|--------|
| KI-001 | HuggingFace SSL on corporate | HIGH | DOCUMENTED |
| KI-002 | Phase 5b hardcoded lookups | LOW | DOCUMENTED |

---

## Changelog

| Date | Version | Changes |
|------|---------|---------|
| 2025-12-08 | 8.0.1h | Corrections Gemini v4: session_uuid (pas task_type), .gemini_analysis (pas .payload), HIVE_SUCCESS (pas HIVE_COMPLETE) |
| 2025-12-08 | 8.0.1g | V8.1.6 Async Drivers (OP-005), V8.1.7 TaskAnalysis.reasoning, corrections Gemini v3 |
| 2025-12-08 | 8.0.1f | Analyse Gemini Deep Think v3: 2 erreurs corrigées (TaskAnalysis.reasoning, ModeProposal.mode) |
| 2025-12-08 | 8.0.1e | Documentation tenant_id enrichie + V8.1.5 corrigé (commands.py existe) |
| 2025-12-08 | 8.0.1d | V8.1.0 adapter IndependentAnalysis→TaskAnalysis, V8.1.4 pure asyncio |
| 2025-12-08 | 8.0.1c | Corrections hallucinations Gemini (HiveMindPipeline→TrueHiveMind, AgentRegistry clarification) |
| 2025-12-08 | 8.0.1b | Enrichi avec Gemini Deep Think analysis (patterns, metrics, 5 nouvelles sections V8.1.x) |
| 2025-12-08 | 8.0.1 | Hot-Swap Lead Agent, KNOWN_ISSUES.md |
| 2025-12-07 | 8.0.0 | TRUE HIVE MIND baseline |

---

*Cette roadmap est opérationnelle. Pour la vision stratégique V9.0+, voir `docs/architecture/VISION_V9_SINGULARITY.md`*
