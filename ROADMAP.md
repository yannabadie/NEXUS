# NEXUS V8.0 "TRUE HIVE MIND" - Roadmap Opérationnelle

**Version**: 8.4.7-cyborg-hardening | **Status**: Active | **Last Updated**: 2025-12-11
**Maintainer**: Yann Abadie | **Branch**: N9AF (async features) / N8THM (main)

---

## Objectif V8.0

Stabiliser et durcir le système "TRUE HIVE MIND" pour un usage quotidien fiable avant d'envisager des évolutions majeures.

**Mantra** : *"Solidifier avant d'innover"*

---

## État Actuel (2025-12-11)

| Métrique | Valeur |
|----------|--------|
| Modules core/ | 25 |
| Fichiers Python | 132 |
| Lignes de code | 45,000+ |
| Tests | 1,162+ |
| Phases complétées | 22 (V8.4.7-cyborg-hardening) |

### Cyborg V7.5 - Async Integration ✅ COMPLETED (2025-12-10)

**Source**: Branch N9AF | **Commits**: Phase 1-4 applied

**Objectif**: Intégrer les primitives async V9 comme BIBLIOTHÈQUES dans V7 existant.
**Philosophie**: *"Installer l'électricité dans le château, pas construire un nouveau château"*

| Composant | Status | Fichier | Lignes ajoutées |
|-----------|--------|---------|-----------------|
| Async Entry Point | ✅ DONE | `nexus7.py` | +55 (`async_main()`) |
| Async REPL Loop | ✅ DONE | `core/interface/repl.py` | +190 (`run_async()`) |
| Async Orchestrator | ✅ DONE | `core/orchestration_v7.py` | +180 (`process_turn_async()`) |
| Cyborg Tests | ✅ DONE | `tests/test_cyborg_v75.py` | +160 |

**Caractéristiques**:
- `prompt_async()` pour input non-bloquant (prompt_toolkit 3.0+)
- `patch_stdout()` pour streaming propre
- `AsyncDriverFactory.cancel_all()` pour Ctrl+C graceful
- Dual-mode: sync (`run()`) et async (`run_async()`) coexistent
- Fallback automatique si async drivers indisponibles

**Primitives V9 Disponibles** (branch N9AF):
- `core/async_primitives/cancellation.py` - CancellationToken hierarchique
- `core/async_primitives/process_handle.py` - AsyncProcessHandle + Registry
- `core/async_primitives/rwlock.py` - AsyncRWLock
- `core/async_primitives/blackboard.py` - AsyncBlackboard avec TTL
- `core/drivers/async_claude_driver.py` - TRUE async avec `create_subprocess_exec`
- `core/drivers/async_gemini_driver.py` - Session isolation via UUID
- `core/drivers/async_factory.py` - Singleton factory avec `cancel_all()`

### Audit Gemini (2025-12-10) + Feedback Consolidé

**Source**: `audit/CLAUDE_audit10122025.md` + Cross-review Claude Web + Gemini

| Faille | Sévérité | Status | Cible | Notes |
|--------|----------|--------|-------|-------|
| FL-001: Race Condition ThreadPoolExecutor | P0 | ✅ **DONE** | V8.3.4 | Lock ajouté (tests charge: V8.3.5) |
| FL-002: False Positives "DONE" detection | P1 | ✅ **DONE** | V8.3.4 | Regex word boundaries |
| FL-004: Exception Swallowing (390x) | P1 | **PLANNED** | V8.5.3 | Audit progressif |
| FL-005: Hardcoded Agent Lookups (20+) | P1 | **PLANNED** | V8.4.0 | ⬆️ Remonté (bloque Ollama) |
| FL-006: DyLAN Score Non-Normalisé | P2 | **BACKLOG** | - | Impact faible |
| P1-3: print(stderr) → structured logger | P1 | **DEFERRED** | V8.5 | Non-bloquant |

**Feedback Consolidé (Gemini + Claude Web 2025-12-10)**:

| Proposition | Verdict Original | Révision | Raison |
|-------------|------------------|----------|--------|
| SDK native drivers | ❌ Rejeté | ✅ **OPTIONNEL** | CLI = coût 0, SDK = option pour API users |
| `asyncio.create_subprocess_exec` | Non mentionné | ✅ **ADOPTÉ V8.4** | Garde CLI, débloque event loop |
| DI Container externe | ❌ Rejeté | ✅ **Factory Pattern natif** | Pas de lib, juste ServiceFactory |
| AgentRegistry | V8.5.0 | ⬆️ **V8.4.0** | Bloque Ollama si pas fait avant |
| REST API | ❌ Rejeté | ⏸️ **V9.0+** | Valide pour V8.x, enterprise later |
| FL-001 effort | 30min | ⚠️ **4-6h** | Tests charge + deadlock check |

**Rejetés définitivement**:
- DI lib externe (dependency-injector) → Factory pattern natif suffit
- REST API pour V8.x → Hors scope CLI, V9.0+ si enterprise
- Docker/K8s obligatoire → Nice-to-have, pas bloquant

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
| OP-005 | Sync drivers in async context | PARALLEL = séquentiel déguisé | ✅ DONE (V8.1.6) |

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

### V8.0.3 - EPHEMERAL Sessions [Priority: P2] ⚡ PARTIAL

**Objectif** : Skip persistence pour tâches TRIVIAL (<2s)

| Tâche | Effort | Status |
|-------|--------|--------|
| Activer SessionMode.EPHEMERAL | 2h | ✅ Done (`session_manager.py:46`) |
| Fast-Track dans TaskAnalyzer | 2h | ✅ Done (complexity < TRIVIAL) |
| Intégrer dans HybridSwarmEngine | 2h | ✅ Done (`hybrid_swarm_engine.py:272-275`) |
| Tests EPHEMERAL | 2h | PLANNED |
| Skip RAG pour EPHEMERAL | 1h | PLANNED |

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

### V8.1.0 - Success Memory Activation [Priority: P1] ✅ COMPLETED (V8.2.0-pre)

**Objectif** : Fermer le feedback loop ModeSelector ↔ SuccessMemory ("Reader" → "Writer")

| Tâche | Effort | Status |
|-------|--------|--------|
| Implémenter hook `record_success()` dans HiveMindPipeline.run() | 3h | ✅ Done (orchestrator.py:455) |
| Implémenter critères de "Worthiness" | 2h | ✅ Done (success_adapter.py) |
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

### V8.1.6 - Thread-Safe Parallel Execution ✅ COMPLETED (2025-12-09)

**Objectif** : Éliminer les race conditions en mode PARALLEL

**Problème résolu**:
- Race condition: fichiers hardcodés (`gemini_context_in.md`, `claude_context_in.md`) écrasés en parallèle
- `session_uuid` non propagé dans la chaîne d'appels
- Mode PARALLEL = exécution séquentielle déguisée

**Solution implémentée**:
- Fichiers uniques par invocation: `*_{uuid}.md` avec cleanup automatique
- Propagation `session_uuid` complète: `ModeExecutor → _wrap_invoke_agent → invoke_for_swarm → invoke_agent_direct → driver.invoke()`
- AsyncDriverAdapter pour support asyncio.gather() futur

| Tâche | Effort | Status |
|-------|--------|--------|
| Unique filenames per invocation | 2h | ✅ Done |
| session_uuid propagation chain | 2h | ✅ Done |
| AsyncDriverAdapter wrapper | 1h | ✅ Done |
| Cleanup in finally blocks | 30min | ✅ Done |

**Commit**: `feat(V8.1.6): Thread-safe parallel execution - Race condition fix`

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

### V8.1.8 - Dynamic Spawn Brainstorming [Priority: P1] ✅ COMPLETED (2025-12-09)

**Objectif** : Agents spawnés avec vraie spécialisation via brainstorming dynamique

**Problème découvert** (Gemini 2025-12-09, validé Claude):
- System prompts actuels = 13 lignes squelettiques (tautologie)
- `spawn_agent()` docstring PROMET EVOLUTION_BRAINSTORM mais utilise template hardcodé
- Agents "experts" sans expertise réelle = coquilles vides
- BIRTH_CERTIFICATE.json avec `domains: []`, `tools_priority: []`, pas d'UUID

**Implémentation détaillée**:

| Étape | Tâche | Fichiers | Status |
|-------|-------|----------|--------|
| 0 | Pre-flight: budget check + existence check | `repl.py` | ✅ Done |
| 1a | Add `mode` param to BrainstormPhase.run() | `brainstorm.py` | ✅ Done |
| 1b | Add `_extract_generated_prompt()` method | `brainstorm.py` | ✅ Done |
| 1c | Add `generated_prompt` field to BrainstormResult | `models.py` | ✅ Done |
| 2a | Generate UUID for each agent | `repl.py` | ✅ Done |
| 2b | Integrate BrainstormPhase in spawn_agent() | `repl.py` | ✅ Done |
| 2c | Auto-detect domains from role string | `repl.py` | ✅ Done |
| 2d | Post-generation tool validation | `repl.py` | ✅ Done |
| 3 | Add `uuid` field to SpawnedAgentConfig | `agent_loader.py` | ✅ Done |
| 4 | Create spawn_brainstorm.md prompt | `prompts/` | ✅ Done |

**Commit**: `c850e7b feat(V8.1.8): Dynamic Spawn Brainstorming`

**Architecture finale**:
```python
# Step 0: Pre-flight
telemetry.enforce_budget()  # Abort if exceeded
if agent_dir.exists(): ask_user(overwrite/rename/cancel)

# Step 1: BrainstormPhase adaptation
class BrainstormPhase:
    def run(self, ..., mode: str = "mutation"):
        if mode == "prompt":
            max_iterations = 10  # Not 30
            # Use _extract_generated_prompt() instead of _extract_mutations()

    def _extract_generated_prompt(self, content: str) -> Optional[str]:
        # Find markdown block starting with # (>30 lines)

# Step 2: spawn_agent() refactor
def spawn_agent(self, role: str):
    agent_uuid = str(uuid.uuid4())
    domains = self._detect_domains(role)  # "python" -> ["coding", "python"]

    # Brainstorm via Hive Mind
    phase = BrainstormPhase(orchestrator, workspace, progress_callback)
    result = phase.run(..., mode="prompt")

    # Validation anti-hallucination
    valid_tools = self.tool_manager.get_tool_names()
    self._validate_prompt_tools(result.generated_prompt, valid_tools)

    # Fallback if brainstorm fails
    prompt = result.generated_prompt or self._static_template(role, agent_uuid)
```

**Contraintes**:
- Budget vérifié AVANT brainstorm (coûteux: ~$0.50-2.00)
- Max 10 itérations pour mode "prompt" (vs 30 pour mutations)
- Minimum 30 lignes pour prompt accepté, sinon fallback
- UUID v4 obligatoire dans BIRTH_CERTIFICATE
- Validation des outils référencés (anti-hallucination)

**Fichiers concernés**:
- `core/interface/repl.py` - spawn_agent() complet
- `core/evolution/phases/brainstorm.py` - mode="prompt"
- `core/evolution/models.py` - BrainstormResult.generated_prompt
- `core/bootstrap/agent_loader.py` - SpawnedAgentConfig.uuid
- `prompts/spawn_brainstorm.md` - NEW

**Source**: Gemini (2025-12-09) - Validé, enrichi et implémenté Claude

---

### V8.1.9 - RAG Commands [Priority: P2] ✅ COMPLETED (2025-12-09)

**Objectif** : Commandes RAG pour indexation ciblée de workspace/memory/

**Commandes ajoutées**:

| Commande | Description |
|----------|-------------|
| `/rag init` | Indexe workspace/memory/ (données de session) |
| `/rag clear` | Efface toutes les données RAG indexées |
| `/rag query <text>` | Test de retrieval RAG |

**Implémentation**:

| Tâche | Fichier | Status |
|-------|---------|--------|
| Ajouter commandes à COMMAND_CATEGORIES | `commands.py` | ✅ Done |
| Handler /rag dans handle_command() | `repl.py` | ✅ Done |
| Méthodes _rag_init, _rag_clear, _rag_query | `repl.py` | ✅ Done |

**Fichiers modifiés**:
- `core/interface/commands.py` - 3 nouvelles commandes RAG
- `core/interface/repl.py` - handle_rag_command() + helpers

**Source**: Claude (2025-12-09) - Demande utilisateur

---

### V8.1.8-B - Model Selection Brainstorming [Priority: P1] ✅ COMPLETED (2025-12-09)

**Objectif** : Lors du spawn d'un agent, brainstormer pour choisir le meilleur modèle LLM (Gemini ou Claude).

**Modèles disponibles**:

| Provider | Modèle | Forces | Cas d'usage |
|----------|--------|--------|-------------|
| Gemini | `gemini-2.5-flash` | Vitesse, grounding, multimodal | Tâches rapides, recherche |
| Gemini | `gemini-3-pro-preview` | Raisonnement profond, agentic | Analyse complexe, architecture |
| Claude | `claude-sonnet-4-5-20250929` | Équilibré, agentique, coding | **Défaut**, polyvalent |
| Claude | `claude-opus-4-5-20251101` | Expert, sécurité | Architecture, audit |
| Claude | `claude-haiku-3-5-20241022` | Vitesse | Tâches simples |

**Implémentation**:

| # | Tâche | Fichier | Status |
|---|-------|---------|--------|
| 1 | Ajouter section MODÈLES DISPONIBLES | `spawn_brainstorm.md` | ✅ Done |
| 2 | Ajouter Inference Configuration output format | `spawn_brainstorm.md` | ✅ Done |
| 3 | Créer InferenceConfig dataclass | `agent_loader.py` | ✅ Done |
| 4 | Parser inference section dans spawn_agent | `repl.py` | ✅ Done |
| 5 | Router vers provider configuré | `agent_invoker.py` | ✅ Done |

**Architecture**:
```python
# BIRTH_CERTIFICATE.json
{
  "agent_id": "sql_expert",
  "uuid": "abc-123",
  "inference": {
    "provider": "gemini",
    "model": "gemini-2.5-flash",
    "reasoning": "Fast data queries"
  }
}

# agent_invoker.py
def invoke_spawned_agent(agent_id, ...):
    config = loader.load_agent_config(agent_id)
    target_agent = "Gemini" if config.inference.provider == "gemini" else "Claude"
    return invoke_agent_direct(..., target_agent)
```

**Fichiers modifiés**:
- `prompts/spawn_brainstorm.md` - Section modèles + output format
- `core/bootstrap/agent_loader.py` - InferenceConfig dataclass
- `core/interface/repl.py` - _extract_inference_config()
- `core/orchestration/agent_invoker.py` - Provider routing

**Source**: Gemini (2025-12-09) - Proposition, implémenté Claude

---

## Roadmap V8.2 (Hardening)

### V8.2.0-pre - Multi-Domain Fixes ✅ VERIFIED (2025-12-09)

**Objectif** : Corrections critiques identifiées par analyse Gemini + validation Claude

**Corrections vérifiées dans le code**:

| # | Issue | Impact | Fichiers | Vérifié |
|---|-------|--------|----------|---------|
| 1 | RAG tools manquants dans spawn_brainstorm.md | Agents amnésiques | `prompts/spawn_brainstorm.md` | ✅ |
| 2 | SuccessMemory non appelé dans HiveMind | Pas d'apprentissage | `orchestrator.py:455`, `success_adapter.py` | ✅ |
| 3 | UUID non propagé à AgentProfile | Tracking impossible | `agent_metrics.py:105`, `agent_loader.py:140` | ✅ |

**Fichiers modifiés**:
- `prompts/spawn_brainstorm.md` - Ajout commandes mémoire RAG ✅
- `core/hive_mind/success_adapter.py` - NEW: Adapters HiveMind -> SuccessMemory (151 lignes) ✅
- `core/hive_mind/orchestrator.py` - Intégration record_success() ligne 455 ✅
- `core/swarm/agent_metrics.py` - Champ uuid dans AgentProfile ligne 105 ✅
- `core/bootstrap/agent_loader.py` - Propagation uuid ligne 140 ✅

**Source**: Gemini Deep Think (2025-12-09) + validation/implémentation Claude

---

### V8.2.0a - Unified Analysis Adapter [Priority: P2] (NEW)

**Objectif** : Adapter générique TaskAnalysis ↔ IndependentAnalysis

**Problème identifié** (Gemini 2025-12-09, validé Claude):
- `TaskAnalysis` (Swarm) utilise `TaskComplexity` enum
- `IndependentAnalysis` (HiveMind) utilise `complexity_assessment: str`
- `success_adapter.py` existe mais est spécifique à SuccessMemory
- Pas d'adapter générique pour cross-domain usage (ex: Memory Boost)

| Tâche | Effort | Status |
|-------|--------|--------|
| Créer `core/adapters/analysis_adapter.py` | 2h | PLANNED |
| Bidirectional mapping (enum ↔ str) | 1h | PLANNED |
| Intégrer dans Memory Boost flow | 1h | PLANNED |
| Tests unitaires | 1h | PLANNED |

**Architecture proposée**:
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
        """Convert HiveMind IndependentAnalysis to Swarm TaskAnalysis."""
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

    @classmethod
    def to_independent_analysis(cls, swarm: TaskAnalysis, agent_id: str) -> IndependentAnalysis:
        """Convert Swarm TaskAnalysis to HiveMind IndependentAnalysis."""
        return IndependentAnalysis(
            agent_id=agent_id,
            complexity_assessment=swarm.complexity.name.lower(),
            task_understanding=swarm.raw_input,
            proposed_approach="Converted from TaskAnalysis"
        )
```

**Source**: Gemini (2025-12-09) - Faille "Dualisme Dataclasses", validé Claude

---

### V8.2.0b - Architecture Map Update [Priority: P3] (NEW)

**Objectif** : Synchroniser ARCHITECTURE_MAP_V8.1.md avec corrections récentes

**Problème identifié** (Gemini 2025-12-09):
- Map ne reflète pas V8.1.6 (Async/session_uuid)
- Map ne reflète pas V8.2.0-pre (SuccessMemory hook)
- Diagramme FSM omet Hot-Swap transitions

| Tâche | Effort | Status |
|-------|--------|--------|
| Ajouter note "SYNC BLOCKING fixed V8.1.6" sur LLM Layer | 30min | PLANNED |
| Ajouter note "Memory Loop closed V8.2.0-pre" | 30min | PLANNED |
| Mettre à jour FSM diagram avec Hot-Swap edges | 1h | PLANNED |
| Ajouter section "Recent Fixes" | 30min | PLANNED |

**Source**: Gemini (2025-12-09) - Action "Sync Docs avec Code"

---

### V8.2.0c - RedTeam Post-Spawn Validation [Priority: P2] (NEW)

**Objectif** : Valider l'alignement des agents spawnés (pas seulement evolved)

**Problème identifié** (Gemini 2025-12-09, validé Claude):
- RedTeam validation existe pour `/evolve` (children)
- Mais ABSENT pour `/spawn` (agents créés directement)
- Agents spawnés pourraient avoir des prompts non-alignés

| Tâche | Effort | Status |
|-------|--------|--------|
| Ajouter RedTeam check dans spawn_agent() | 2h | PLANNED |
| Configurable via REDTEAM_SPAWN_MANDATORY | 30min | PLANNED |
| Logging des scores d'alignement | 30min | PLANNED |
| Tests spawn + redteam | 1h | PLANNED |

**Implémentation proposée**:
```python
# core/interface/repl.py - dans spawn_agent(), après génération prompt
if getattr(self.config, 'redteam_spawn_mandatory', False):
    from core.governance.red_team import RedTeamValidator
    validator = RedTeamValidator(agent_dir)
    results = validator.run_quick_check(system_prompt)
    if results['alignment_score'] < self.config.red_team_min_score:
        self.console.print_warning(f"⚠️ Agent alignment: {results['alignment_score']:.0%}")
        if not self._confirm_spawn_low_alignment():
            return  # Abort spawn
```

**Source**: Gemini (2025-12-09) - Faille "Security Gaps Mineurs", validé Claude

---

### V8.2.0d - Torture Protocol V8 [Priority: P2] (NEW)

**Objectif** : Test de stress post-consolidation pour valider robustesse

**Contexte** (Gemini 2025-12-09):
- V7.5 avait un "Torture Protocol" qui a validé 92% → 95% robustesse
- V8.0 n'a pas eu d'équivalent
- Après V8.2.0 fixes, un stress test complet est recommandé

| Tâche | Effort | Status |
|-------|--------|--------|
| Créer `tests/torture_v8.py` | 3h | PLANNED |
| Scénarios: parallel overload, stagnation chains, budget exhaustion | 2h | PLANNED |
| Métriques: success rate, recovery rate, panic rate | 1h | PLANNED |
| CI integration (nightly) | 1h | PLANNED |

**Scénarios de torture**:
```python
# tests/torture_v8.py
TORTURE_SCENARIOS = [
    # Parallel overload
    {"name": "parallel_flood", "concurrent_tasks": 10, "mode": "PARALLEL"},
    # Stagnation chains
    {"name": "stagnation_loop", "similar_tasks": 5, "expect_hot_swap": True},
    # Budget exhaustion
    {"name": "budget_drain", "expensive_tasks": 20, "expect_budget_error": True},
    # Memory pressure
    {"name": "rag_flood", "documents": 1000, "queries": 100},
    # Mixed chaos
    {"name": "chaos_monkey", "random_failures": True, "duration_minutes": 5},
]
```

**Métriques cibles**:
- Success rate: >95%
- Recovery rate (après erreur): >90%
- Panic rate: <1%
- Hot-Swap effectiveness: >80%

**Source**: Gemini (2025-12-09) - Astuce "Torture Protocol post-consolidation"

---

### V8.3.0 - SwarmBridge "Dictator Mode" ✅ COMPLETED (2025-12-09)

**Objectif** : Permettre au Hive Mind de déléguer des tâches au Swarm Engine

**Problème Résolu**:
- Hive Mind = toujours actif (config par défaut, COMPLEX/EXPERT)
- Swarm Engine = **DORMANT** (6 modes puissants jamais utilisés)
- Perte d'efficacité: moteur dormant, capacités gaspillées

**Solution - "Dictator Mode"**:
- Hive Mind devient **stratège** (méta-orchestrateur)
- Swarm Engine devient **tacticien** (exécuteur de modes)
- HiveMind peut déléguer pour: recherches parallèles, tests, reviews de sécurité

| Tâche | Effort | Status |
|-------|--------|--------|
| SwarmBridge + SwarmDelegationResult | 2h | ✅ Done |
| HivePhase enum + ALLOWED_MODES guardrails | 30min | ✅ Done |
| Context budget "swarm_delegation": 8000 | 10min | ✅ Done |
| Integration phase_execution.py | 1h | ✅ Done |
| ExecutionStep.swarm_mode field | 10min | ✅ Done |
| Tests (36 tests) | 1h | ✅ Done |

**Architecture**:
```
┌──────────────────────────────────────────────────────────┐
│                  HIVE MIND (Stratège)                    │
│  Phase 1-3: Analysis, Debate, Architecture               │
│  Phase 4: Execution ───────────┐                         │
│  Phase 5-7: Diagnosis, ...     │                         │
│                    ┌───────────▼───────────┐             │
│                    │     SwarmBridge       │             │
│                    │     (V8.3 NEW)        │             │
│                    └───────────┬───────────┘             │
└────────────────────────────────┼─────────────────────────┘
                                 │
            ┌────────────────────┼────────────────────┐
            ▼                    ▼                    ▼
     ┌──────────┐         ┌──────────┐        ┌──────────┐
     │ PARALLEL │         │ RED_BLUE │        │ PING_PONG│
     └──────────┘         └──────────┘        └──────────┘
```

**Guardrails (9 combinaisons valides)**:
- ANALYSIS: SPECIALIST only
- DEBATE: PING_PONG, RED_BLUE
- ARCHITECTURE: LEAD_SUPPORT
- EXECUTION: PARALLEL, SEQUENTIAL, SPECIALIST
- DIAGNOSIS: RED_BLUE
- CONSOLIDATION: SPECIALIST

**Nouveaux Fichiers**:
- `core/hive_mind/swarm_bridge.py` (~500 lignes)
- `tests/test_swarm_bridge.py` (~400 lignes, 36 tests)

**Fichiers Modifiés**:
- `core/hive_mind/types.py` - ExecutionStep.swarm_mode
- `core/hive_mind/context_manager.py` - Budget "swarm_delegation"
- `core/hive_mind/phases/phase_execution.py` - _execute_via_swarm()
- `core/hive_mind/__init__.py` - Exports

**Usage**:
```python
# Dans ExecutionPlan généré par Phase 3:
ExecutionStep(
    name="Security Review",
    agent_id="gemini",
    action="Review auth module for vulnerabilities",
    swarm_mode="red_blue"  # ← Délégué au Swarm!
)

# Phase 4 détecte swarm_mode et délègue:
# [V8.3 Dictator Mode] Delegating step 'Security Review' to Swarm (mode=red_blue)
```

**Tests**: 36/36 passent ✅

**Source**: Gemini Analysis + Claude Implementation (2025-12-09)

---

### V8.3.1 - SwarmTool "Swarm as Invocable Tool" ✅ COMPLETED (2025-12-09)

**Objectif** : Permettre aux agents d'invoquer le Swarm à n'importe quelle phase HiveMind

**Problème Résolu**:
- V8.3.0 SwarmBridge ne fonctionne qu'en Phase 4 via `ExecutionStep.swarm_mode`
- Les autres phases (Analysis, Debate, Architecture) ne peuvent pas bénéficier du Swarm
- Perte d'opportunités: debates RED_BLUE, analyses PARALLEL, etc.

**Solution - "SwarmTool"**:
- Nouvel outil `swarm_delegate` dans ToolManager
- Invocable par les agents à **n'importe quelle phase**
- Feedback loop automatique (résultats → HiveMind context)
- Self-healing aligné avec checkpoints

| Tâche | Effort | Status |
|-------|--------|--------|
| Budget swarm_tool_invocation (6k) | 10min | ✅ Done |
| Aligner self-healing (checkpoints) | 30min | ✅ Done |
| Handler swarm_delegate | 45min | ✅ Done |
| Câblage SwarmBridge→ToolManager | 20min | ✅ Done |
| Tests (test_swarm_tool.py) | 1h | ✅ Done |

**Usage**:
```python
# Agent peut invoquer swarm_delegate à n'importe quelle phase:
<tool_use name="swarm_delegate">
  {"task": "Débattre de l'approche auth", "mode": "red_blue", "phase": "debate"}
</tool_use>

# Ou pour analyse parallèle:
<tool_use name="swarm_delegate">
  {"task": "Analyser 3 fichiers en parallèle", "mode": "parallel"}
</tool_use>
```

**Gap Self-Healing Corrigé**:
- SwarmBridge._execute_with_fallback() utilisait fallback sans checkpoints
- Aligné avec ModeExecutor.execute_with_fallback()
- Checkpoint create/restore sur chaque fallback

**Fichiers Modifiés**:
- `core/hive_mind/context_manager.py` - Budget "swarm_tool_invocation": 6000
- `core/hive_mind/swarm_bridge.py` - Checkpoints dans _execute_with_fallback()
- `core/execution/tool_manager.py` - Handler _execute_swarm_delegate()
- `core/orchestration_v7.py` - Import HiveMindSwarmBridge + câblage

**Nouveaux Fichiers**:
- `tests/test_swarm_tool.py` (~400 lignes)

**Source**: Claude Implementation (2025-12-09)

---

### V8.3.1-hotfix - Depth Guard Anti-Recursion ✅ COMPLETED (2025-12-09)

**Objectif** : Prévenir la récursion infinie ("Inception Trap") dans swarm_delegate

**Problème identifié** (Gemini 2025-12-09):
- SwarmTool permet aux agents d'invoquer le Swarm
- Le Swarm peut lui-même invoquer des agents qui peuvent utiliser SwarmTool
- Sans garde-fou: récursion infinie → explosion de tokens/coûts

**Solution - Depth Guard**:
```python
# core/execution/tool_manager.py - _execute_swarm_delegate()
MAX_SWARM_DEPTH = 2
current_depth = args.get("_swarm_depth", 0)

if current_depth >= MAX_SWARM_DEPTH:
    return ToolResult(
        status="ERROR",
        error=f"Max swarm recursion depth ({MAX_SWARM_DEPTH}) reached."
    )

# Propagation via config
result = await delegate(..., config={"_swarm_depth": current_depth + 1})
```

**Comportement**:
- Niveau 0: Invocation directe par agent → OK
- Niveau 1: Sub-agent invoque SwarmTool → OK
- Niveau 2: Sub-sub-agent tente SwarmTool → BLOQUÉ

| Tâche | Effort | Status |
|-------|--------|--------|
| Ajouter depth guard dans _execute_swarm_delegate() | 15min | ✅ Done |
| Propager _swarm_depth via config | 10min | ✅ Done |
| Tests (inclus dans test_swarm_tool.py) | - | ✅ Done |

**Fichiers Modifiés**:
- `core/execution/tool_manager.py` - Depth check + propagation

**Source**: Gemini Security Analysis (2025-12-09) + Claude Implementation

---

### V8.3.2 - "Closing the Loop" (Audit Corrections) [Priority: P1] ✅ COMPLETED

**Objectif** : Finaliser SwarmBridge/SwarmTool avant d'ajouter de la complexité

**Source** : Audit croisé Claude + Gemini (2025-12-09)

**Philosophie** : *"Finir proprement avant d'innover"* (Gemini)

| ID | Finding | Sévérité | Fichiers | Status |
|----|---------|----------|----------|--------|
| FG-001 | SuccessAdapter non appelé dans SwarmBridge | MEDIUM | `swarm_bridge.py` | ✅ ALREADY IMPL |
| TD-001 | Pattern async→sync dupliqué | LOW | `tool_manager.py` | ✅ REFACTORED |
| MT-001 | Tests checkpoint SwarmBridge | LOW | `test_swarm_bridge.py` | ✅ ALREADY IMPL |
| C3 | Version 7.0.0 vs 8.3.x | LOW | `core/__init__.py` | ✅ ALREADY CORRECT |
| H3 | CLAUDE.md structure obsolète | LOW | `CLAUDE.md` | ✅ UPDATED |

**Completion Notes** (2025-12-09):
- FG-001, MT-001, C3: Already implemented from previous sessions
- TD-001: Refactored `tool_manager.py:1774-1787` to use `async_utils.run_sync()`
- H3: Updated FSM States → V8.3 Orchestration Architecture + Key Documentation paths

**Ordre d'exécution** (Gemini recommendation):
1. `core/__init__.py` → version 8.3.2 (cohérence immédiate)
2. `core/utils/async_utils.py` → run_sync() helper (nettoie le code)
3. `swarm_bridge.py` → SuccessAdapter integration (feedback loop)
4. `test_swarm_bridge.py` → checkpoint tests (robustesse)
5. `CLAUDE.md` → structure réelle (documentation)

#### FG-001: SuccessAdapter dans SwarmBridge

**Problème** : Les succès via SwarmBridge ne sont pas enregistrés dans SuccessMemory

```python
# core/hive_mind/swarm_bridge.py - Actuellement:
if result.success:
    self.inject_results_into_context(result)

# Manquant:
if result.success and self.success_adapter:
    self.success_adapter.record_delegation_success(task, mode, result)
```

**Impact** : Trou dans la boucle d'apprentissage - le système ne mémorise pas quelles délégations fonctionnent.

#### TD-001: Extraction pattern async→sync

**Problème** : Pattern répété dans 2+ fichiers

```python
# Pattern dupliqué:
try:
    loop = asyncio.get_running_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
```

**Solution** :
```python
# core/utils/async_utils.py (NOUVEAU)
def run_sync(coro):
    """Execute async coroutine in sync context."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)
```

#### MT-001: Tests checkpoint SwarmBridge

**Tests manquants** :
- `test_checkpoint_created_before_execution`
- `test_checkpoint_restored_on_fallback`
- `test_checkpoint_not_created_without_session_manager`

---

### V8.3.3 - Parallel Merge Strategy ✅ COMPLETED (2025-12-09)

**Objectif** : Stratégie intelligente de fusion des résultats PARALLEL

**Solution Implémentée**:
- Nouveau module `core/swarm/merge_strategies.py` (~355 lignes)
- 3 stratégies: NAIVE (backward compat), DEDUPLICATE (Jaccard similarity), WEIGHTED (domain fit)
- ParallelExecutor utilise `_merge_strategy` pluggable
- Configuration via `NEXUS_PARALLEL_MERGE_STRATEGY` env var

**Fichiers créés/modifiés**:
- `core/swarm/merge_strategies.py` - NEW (MergeStrategy ABC + 3 implémentations)
- `core/swarm/mode_executors.py` - ParallelExecutor intégration
- `tests/test_merge_strategies.py` - NEW (32 tests)
- `.env` - NEXUS_PARALLEL_MERGE_STRATEGY=naive

**Tests**: 32/32 merge_strategies ✅, 41/41 hybrid_swarm ✅

**Commit**: `48b4f3e feat(V8.3.3): Parallel Merge Strategy`

---

### V8.3.4 - Audit Quick Fixes [Priority: P0] ✅ COMPLETED (2025-12-10)

**Objectif** : Corriger les failles critiques identifiées par l'audit Gemini

**Source**: `audit/CLAUDE_audit10122025.md` (2025-12-10)

| ID | Faille | Impact | Effort | Status |
|----|--------|--------|--------|--------|
| FL-001 | Race Condition ThreadPoolExecutor | Corruption blackboard | 30min | ✅ Done |
| FL-002 | False Positives "DONE" detection | Faux arrêts | 1h | ✅ Done |
| P1-3 | print(stderr) → logger (26x) | Logs non structurés | 2h | ⏸️ Deferred V8.4 |
| DC-001 | Dead code cleanup | Tech debt | 1h | ⏸️ Deferred V8.5 |

**Tests**: 6/6 nouveaux tests audit fixes ✅

#### FL-001: Race Condition ThreadPoolExecutor

**Fichier**: `core/swarm/mode_executors.py:513-521`

**Problème**: ThreadPoolExecutor sans lock pour context.blackboard partagé

```python
# ACTUEL - Race condition possible
with ThreadPoolExecutor(max_workers=len(tasks)) as executor:
    futures = {executor.submit(self._invoke, ...) for ...}
```

**Solution**:
```python
# core/swarm/mode_executors.py
from threading import Lock

class ParallelExecutor(ModeExecutor):
    def __init__(self, ...):
        self._blackboard_lock = Lock()

    def _safe_blackboard_update(self, context, key, value):
        with self._blackboard_lock:
            context.blackboard[key] = value
```

#### FL-002: False Positives Completion Detection

**Fichier**: `core/swarm/mode_executors.py:62-85`

**Problème**: `"DONE" in content_upper` trop générique ("I'm not DONE yet" → détecté comme terminé)

```python
# ACTUEL - Faux positifs
completion_signals = (
    "FINISHED" in content_upper
    or "DONE" in content_upper  # ❌ Trop générique!
)
```

**Solution**:
```python
import re
# Word boundaries pour éviter faux positifs
FINISHED_PATTERN = re.compile(
    r'\b(FINISHED|TASK\s+COMPLETE|COMPLETED|ALL\s+DONE)\b',
    re.IGNORECASE
)
# "DONE" seul exclu car trop générique
```

#### P1-3: print(stderr) → Structured Logger

**Statistique**: 26 occurrences `print(..., file=sys.stderr)` dans core/

**Solution**: Remplacer par `self.logger.debug()` ou `logger.warning()`

#### DC-001: Dead Code Cleanup

**Fonctions confirmées mortes** (jamais appelées dans core/):
- `add_child()` - `core/evolution/lineage.py:423`
- `add_server()` - `core/mcp/registry.py:155`
- `compress_history()` - `core/synapse/memory_v7.py:192`

**Action**: Marquer `@deprecated` ou supprimer

**Ordre d'exécution**:
1. FL-001 (30min) - Sécurité critique
2. FL-002 (1h) - Fiabilité
3. P1-3 (2h) - Observabilité
4. DC-001 (1h) - Cleanup

**Critères de succès**:
- [ ] Tests existants passent (1000+)
- [ ] Nouveau test `test_parallel_blackboard_thread_safety`
- [ ] Nouveau test `test_completion_detection_no_false_positives`
- [ ] grep `print.*stderr` core/ = 0 occurrences

---

### V8.2.1 - Multi-Tenant Basics [Priority: P2]

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

## Roadmap V8.3 (Advanced Features) [VISION]

> **Status**: Vision long-terme, post-V8.2 stabilisation

### V8.3.4 - Symmetric MCP Bridges [Priority: P1] (FROM ROADMAP_HIVE_MIND)

**Objectif** : Permettre à chaque agent d'appeler l'autre via MCP (Agent-as-Tool)

**Source** : ROADMAP_HIVE_MIND.md Phase 12.4

> **Philosophie HIVE MIND**: Ni Gemini ni Claude n'est le "super-orchestrateur" permanent.
> Le lead est décidé dynamiquement par: Task Analysis, Swarm Mode, DyLAN Scores, Consensus.

**Architecture Symétrique**:
```
┌─────────────┐      MCP Protocol      ┌─────────────┐
│   GEMINI    │◄──────────────────────►│   CLAUDE    │
│             │                         │             │
│ Peut appeler│                         │ Peut appeler│
│ claude_mcp  │                         │ gemini_mcp  │
└─────────────┘                         └─────────────┘
```

| Direction | Méthode | Raison |
|-----------|---------|--------|
| Claude → Gemini | MCP Server | Claude supporte `--mcp-config` natif |
| Gemini → Claude | Tool Registry | Gemini utilise tools Python classiques |

| Tâche | Effort | Status |
|-------|--------|--------|
| `core/mcp/claude_bridge.py` - Claude exposé comme MCP Server | 4h | PLANNED |
| `core/mcp/gemini_bridge.py` - Gemini exposé comme MCP Server | 4h | PLANNED |
| Configuration symétrique dans tool_manager | 2h | PLANNED |
| Tests bidirectionnels | 3h | PLANNED |

---

### V8.3.5 - Memory Weaver [Priority: P1]

**Objectif** : Unifier RAG + SuccessMemory + AutoMemory derrière une façade unique

**Problème actuel** (Gemini 2025-12-09, validé Claude):
- 3 systèmes mémoire indépendants, pas d'interface unifiée
- Confusion sur quel système utiliser quand
- Pas de stratégie de rétention/éviction cohérente

| Tâche | Effort | Status |
|-------|--------|--------|
| Créer `UnifiedMemoryFacade` interface | 4h | PLANNED |
| Adapter RAG, SuccessMemory, AutoMemory | 6h | PLANNED |
| Stratégie de rétention configurable | 3h | PLANNED |
| Migration callers existants | 4h | PLANNED |

**Architecture proposée**:
```python
# core/memory/unified.py (NOUVEAU)
class UnifiedMemoryFacade:
    """Facade unifiée pour les 3 systèmes mémoire."""

    def __init__(self, rag: ProjectMemory, success: SuccessMemory, auto: AutoMemory):
        self.rag = rag
        self.success = success
        self.auto = auto

    def remember(self, content: str, memory_type: MemoryType, **metadata):
        """Stocke dans le système approprié."""
        if memory_type == MemoryType.TASK_SUCCESS:
            self.success.record_success(...)
        elif memory_type == MemoryType.PROJECT_KNOWLEDGE:
            self.rag.add_document(...)
        else:
            self.auto.save(...)

    def recall(self, query: str, memory_types: List[MemoryType] = None) -> List[MemoryItem]:
        """Recherche unifiée cross-système."""
        results = []
        if MemoryType.PROJECT_KNOWLEDGE in memory_types:
            results.extend(self.rag.query(query))
        if MemoryType.TASK_SUCCESS in memory_types:
            results.extend(self.success.get_similar(query))
        return self._rank_and_dedupe(results)
```

**Source**: Gemini (2025-12-09) - Action 2 "Memory Weaver"

---

### V8.3.1 - Agent Reaper [Priority: P2]

**Objectif** : Garbage collection des agents inutilisés

**Problème actuel**:
- Agents spawnés s'accumulent indéfiniment
- Pas de mécanisme de nettoyage
- workspace/agents/ peut devenir volumineux

| Tâche | Effort | Status |
|-------|--------|--------|
| Implémenter `AgentReaper` service | 3h | PLANNED |
| Critères de rétention configurables | 2h | PLANNED |
| Commande `/agents gc` | 1h | PLANNED |
| Archive avant suppression | 2h | PLANNED |

**Critères de garbage collection** (Gemini 2025-12-09, ajusté Claude):
```python
# core/swarm/agent_reaper.py (NOUVEAU)
class AgentReaper:
    """Garbage collector pour agents inutilisés."""

    def should_reap(self, agent: AgentProfile) -> bool:
        # Ajustements Claude: critères moins agressifs
        return (
            agent.last_invoked_at < now - timedelta(days=60) and  # 60j pas 30j
            agent.average_importance < 0.3 and  # 0.3 pas 0.4
            agent.total_invocations < 5
        )

    def reap(self, agent_id: str, archive: bool = True):
        if archive:
            self._archive_to_graveyard(agent_id)
        self.agent_pool.remove_agent(agent_id)
```

**⚠️ Ajustements vs proposition Gemini**:
- 60 jours inactivité (pas 30) - agents peuvent être saisonniers
- DyLAN < 0.3 (pas 0.4) - évite de tuer des agents potentiellement utiles
- Archive obligatoire avant suppression (récupération possible)

**Source**: Gemini (2025-12-09) - Action 3 "Agent Reaper", ajusté Claude

---

### V8.3.2 - FSM State Mapping [Priority: P2]

**Objectif** : Mapping explicite HiveMindState ↔ OrchestratorState

**Problème actuel** (Gemini 2025-12-09, validé Claude):
- `HiveMindState` (24 états) et `OrchestratorState` (11 états) non synchronisés
- Mapping implicite dans `fsm_handlers.py:771-782`
- Debugging difficile quand les états divergent

| Tâche | Effort | Status |
|-------|--------|--------|
| Créer mapping explicite | 2h | PLANNED |
| Validation bidirectionnelle | 2h | PLANNED |
| Logging des transitions | 1h | PLANNED |
| Tests state consistency | 2h | PLANNED |

**Mapping proposé**:
```python
# core/fsm/state_mapping.py (NOUVEAU)
HIVE_TO_ORCHESTRATOR = {
    HiveMindState.HIVE_SUCCESS: OrchestratorState.WAITING_USER,
    HiveMindState.HIVE_FAILED: OrchestratorState.ERROR,
    HiveMindState.HIVE_ESCALATE: OrchestratorState.WAITING_USER,
    HiveMindState.HIVE_CANCELLED: OrchestratorState.IDLE,
    # ... autres mappings
}

def sync_state(hive_state: HiveMindState) -> OrchestratorState:
    """Synchronise HiveMind state vers Orchestrator."""
    if hive_state not in HIVE_TO_ORCHESTRATOR:
        logger.warning(f"Unmapped HiveMind state: {hive_state}")
        return OrchestratorState.ERROR
    return HIVE_TO_ORCHESTRATOR[hive_state]
```

**Source**: Gemini (2025-12-09) - Analyse "Dissonance des États"

---

### V8.3.3 - Task Contracts (Pydantic Schemas) [Priority: P3]

**Objectif** : Validation stricte des tâches Swarm via Pydantic

**Avantages**:
- Erreurs détectées tôt (avant exécution coûteuse)
- Documentation auto-générée
- Serialization JSON garantie

| Tâche | Effort | Status |
|-------|--------|--------|
| Créer SwarmTaskContract schema | 2h | PLANNED |
| Validation dans SwarmBridge | 2h | PLANNED |
| Error messages explicites | 1h | PLANNED |

**Source**: Gemini (2025-12-09) - Plan V8.2

---

## Roadmap V8.4 (Pre-Ollama Prep) [FROM FEEDBACK CONSOLIDÉ]

> **Status**: PRIORITAIRE - Bloque V8.4.2 Local Model Support (Ollama)
> **Source**: Feedback Gemini + Claude Web (2025-12-10)

### V8.4.0 - AgentRegistry Abstraction [Priority: P0] ⬆️ REMONTÉ

**Objectif** : Éliminer les 20+ hardcoded agent lookups (FL-005)

**⚠️ BLOQUANT**: Sans AgentRegistry, impossible d'ajouter Ollama comme 3ème provider!

**Problème actuel**:
```python
# Pattern répété 20+ fois dans la codebase
if agent == "Claude":
    # ...
elif agent == "Gemini":
    # ...
# Ollama? 🤷 Faut tout refactorer!
```

**Solution proposée**:
```python
# core/agents/registry.py (NOUVEAU)
class AgentRegistry:
    def __init__(self):
        self._agents: Dict[str, AgentProfile] = {}

    def register(self, agent_id: str, profile: AgentProfile):
        self._agents[agent_id] = profile

    def get_best_for_domain(self, domain: str) -> AgentProfile:
        return max(
            self._agents.values(),
            key=lambda a: a.get_domain_score(domain)
        )

    def iterate_all(self) -> Iterator[AgentProfile]:
        yield from self._agents.values()

# Usage après refactor:
for agent in registry.iterate_all():
    agent.invoke(context)  # Works for Claude, Gemini, Ollama, etc.
```

| Tâche | Effort | Status |
|-------|--------|--------|
| Créer `core/agents/registry.py` | 3h | PLANNED |
| Wrapper Claude & Gemini profiles | 2h | PLANNED |
| Migration progressive des lookups | 6h | PLANNED |
| Tests regression | 2h | PLANNED |

**Fichiers impactés** (20+ occurrences):
- `core/orchestration/fsm_handlers.py` (8)
- `core/utils/stream_parser.py` (10)
- `core/hive_mind/phases/phase_debate.py` (12)
- Autres (20+)

---

### V8.4.1 - Async CLI Optimization [Priority: P1] 🆕 FROM FEEDBACK

**Objectif** : Débloquer l'event loop tout en gardant CLI (coût 0)

**Contexte** (Feedback Gemini 2025-12-10):
> "Même si on garde le CLI, on peut optimiser l'appel. `asyncio.create_subprocess_exec`
> est bien meilleur que `subprocess.run` (bloquant). C'est le compromis idéal."

**Problème actuel**:
```python
# core/drivers/gemini_driver_v7.py - BLOQUANT
result = subprocess.run(
    ["gemini", "-p", prompt],
    capture_output=True,
    timeout=self.timeout
)
# L'event loop est bloquée pendant l'appel CLI!
```

**Solution** (garde CLI, débloque event loop):
```python
# core/drivers/gemini_driver_v7.py - NON-BLOQUANT
async def invoke_async(self, context: str, session_uuid: Optional[str] = None) -> Dict:
    """True async CLI call - event loop not blocked."""
    proc = await asyncio.create_subprocess_exec(
        self.cli_path, "-m", self.model, "-p", f"@{context_file}",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await proc.communicate()
    return self._parse_output(stdout.decode())
```

**Avantages**:
- ✅ Garde CLI (coût 0, pas d'API keys)
- ✅ Event loop non bloquée (vrai PARALLEL)
- ✅ Même interface que subprocess.run
- ✅ Compatible avec asyncio.gather()

| Tâche | Effort | Status |
|-------|--------|--------|
| `gemini_driver_v7.py` → `invoke_async()` | 2h | PLANNED |
| `claude_driver_hybrid.py` → `invoke_async()` | 2h | PLANNED |
| Adapter ParallelExecutor pour async | 2h | PLANNED |
| Tests async drivers | 2h | PLANNED |
| Benchmark subprocess vs async | 1h | PLANNED |

---

### V8.4.2 - ServiceFactory Pattern [Priority: P2] 🆕 FROM FEEDBACK

**Objectif** : Découpler OrchestratorV7 sans lib externe

**Contexte** (Feedback Claude Web 2025-12-10):
> "Pas besoin de lib externe (dependency-injector). Un simple pattern factory suffit."

**Problème actuel** (God Object OrchestratorV7):
```python
# core/orchestration_v7.py - 250+ lignes d'init!
class OrchestratorV7:
    def __init__(self, config, workspace, ...):
        self.gemini_driver = GeminiDriver(...)
        self.claude_driver = ClaudeDriver(...)
        self.memory = MemoryManager(...)
        self.swarm = SwarmEngine(...)
        # ... 20+ autres dépendances créées inline
```

**Solution** (Factory Pattern natif):
```python
# core/factory.py (NOUVEAU - pas de lib externe)
class ServiceFactory:
    """Factory pattern natif pour découpler OrchestratorV7."""

    @staticmethod
    def create_drivers(config, workspace) -> Dict[str, BaseDriver]:
        return {
            "gemini": GeminiDriver(config.gemini_model, workspace),
            "claude": ClaudeDriver(config.claude_model, workspace),
            # Ollama ajouté facilement ici!
        }

    @staticmethod
    def create_memory(workspace, config) -> MemoryManager:
        return MemoryManager(workspace, config.memory_backend)

    @staticmethod
    def create_orchestrator(config, workspace) -> OrchestratorV7:
        drivers = ServiceFactory.create_drivers(config, workspace)
        memory = ServiceFactory.create_memory(workspace, config)
        return OrchestratorV7(drivers=drivers, memory=memory, ...)
```

**Avantages**:
- ✅ Pas de dépendance externe
- ✅ Testabilité (mock les factories)
- ✅ Découplage (OrchestratorV7 reçoit ses deps)
- ✅ Extensibilité (ajouter Ollama = 1 ligne)

| Tâche | Effort | Status |
|-------|--------|--------|
| Créer `core/factory.py` | 2h | PLANNED |
| Refactor OrchestratorV7.__init__ | 4h | PLANNED |
| Tests factory | 2h | PLANNED |

---

### V8.4.3 - Local Model Support (Ollama) [Priority: P2]

**Objectif** : Mode air-gapped pour environnements restreints

**⚠️ Prérequis**: V8.4.0 (AgentRegistry) et V8.4.2 (ServiceFactory)

---

### V8.4.4 - Blind Spot Remediations [Priority: P0-P2] 🆕 FROM DEEP ANALYSIS

**Objectif**: Corriger 7 angles morts architecturaux identifiés
**Source**: Gemini DeepThink + Claude codebase exploration + Web Research (2025-12-10)
**Philosophie**: "Functional Core, Async Shell" - Le FSM devient GPS, pas conducteur

**Angles Morts Identifiés** (7 total):

| # | Angle Mort | Sévérité | Remédiation |
|---|------------|----------|-------------|
| 1 | FSMHandlers I/O Mixing (1,099 lignes) | HIGH | WorkItem Yield Pattern |
| 2 | HiveMind No Checkpoints (24 états) | CRITICAL | SagaManager + AsyncBlackboard |
| 3 | StagnationDetector Réactif | MEDIUM | Proactive Trajectory Predictor |
| 4 | PanicSystem Sans FSM | MEDIUM | HealthStateMachine + Recovery |
| 5 | async_adapter `future.result()` | HIGH | Deprecate DriverBridge |
| 6 | Phase Guards Manquants | HIGH | Guards dans SagaManager |
| 7 | Compensating Transactions Absentes | MEDIUM | Rollback par phase |

---

#### V8.4.4a - DriverBridge Deprecation [P1 - QUICK WIN]

**Problème**: `core/hive_mind/async_adapter.py:263` bloque avec `future.result(timeout=300)`

**Solution**: Ajouter wrappers sync aux async drivers, marquer DriverBridge deprecated

| Tâche | Effort | Status |
|-------|--------|--------|
| Ajouter `invoke_sync()` aux 2 drivers | 2h | PLANNED |
| Marquer DriverBridge deprecated | 1h | PLANNED |
| Tests de compatibilité | 2h | PLANNED |
| **Total** | **5h** | |

**Fichiers**: `async_claude_driver.py`, `async_gemini_driver.py`, `async_adapter.py`

---

#### V8.4.4b - SagaManager pour HiveMind [P0 - CRITICAL]

**Problème**: 24 états HiveMind, 7 phases, ZERO checkpoints → perte travail sur crash

**Solution**: SagaManager avec persistence AsyncBlackboard (déjà production-ready)

```python
# core/hive_mind/saga_manager.py (NOUVEAU)
class SagaManager:
    async def checkpoint_phase(self, phase, result, compensation)
    async def rollback_to(self, target_phase)
    async def resume_from(self, task_id)
    async def can_enter_phase(self, phase, context)  # Phase Guards
```

**Compensations par Phase**:
| Phase | Compensation |
|-------|--------------|
| Analysis | Clear analysis_result, reset context |
| Debate | Clear debate_result, restore analysis |
| Architecture | Despawn agents créés, clear plan |
| Execution | Mark incomplete, cleanup artifacts |

| Tâche | Effort | Status |
|-------|--------|--------|
| Créer SagaManager class | 4h | PLANNED |
| Définir compensations | 2h | PLANNED |
| Intégrer dans TrueHiveMind | 3h | PLANNED |
| Phase Guards | 2h | PLANNED |
| Tests checkpoint/rollback | 3h | PLANNED |
| **Total** | **14h** | |

**Fichiers**: CREATE `saga_manager.py`, MODIFY `orchestrator.py`, `types.py`

---

#### V8.4.4c - WorkItem Yield Pattern [P1 - HIGH]

**Problème**: FSMHandlers mélange I/O et logique (14 I/O ops dans 1,099 lignes)

**Solution**: Handlers deviennent générateurs yield WorkItems, executor fait I/O

```python
# Handlers = Pure Logic (yield WorkItems)
def handle_brainstorming(self):
    context = self._build_context()
    response = yield WorkItem(INVOKE_AGENT, context)
    return self._process_response(response)

# Executor = I/O (async)
async def execute(item: WorkItem):
    return await driver.invoke(item.context)
```

**Ordre d'extraction** (low risk → high):
1. `handle_swarm_*` (4 handlers) - 0 I/O
2. `handle_idle` - routing logic
3. `handle_executing_tool` - 1 I/O
4. `handle_brainstorming` - 2 I/O
5. `handle_validating_cfl` - 2 I/O

| Tâche | Effort | Status |
|-------|--------|--------|
| Créer WorkItem types | 1h | PLANNED |
| Créer WorkItemExecutor | 3h | PLANNED |
| Extraire handlers (incremental) | 13h | PLANNED |
| Tests handlers isolés | 4h | PLANNED |
| **Total** | **21h** | |

**Fichiers**: CREATE `work_items.py`, `work_item_executor.py`, MODIFY `fsm_handlers.py`

---

#### V8.4.4d - HealthStateMachine [P2 - MEDIUM]

**Problème**: PanicSystem utilise compteurs sans recovery automatique

**Solution**: FSM de santé avec stratégies de recovery

```
HEALTHY → DEGRADED → CRITICAL → RECOVERING → HEALTHY
             │                       ↑
             └──► PANIC ─────────────┘
```

**Recovery Strategies** (séquentielles):
1. Reset stagnation detector
2. Switch active agent
3. Compress context
4. Clear tool cache

| Tâche | Effort | Status |
|-------|--------|--------|
| Créer HealthStateMachine | 3h | PLANNED |
| Définir recovery strategies | 2h | PLANNED |
| Intégrer avec PanicSystem | 2h | PLANNED |
| Tests transitions | 2h | PLANNED |
| **Total** | **9h** | |

**Fichiers**: CREATE `health_state_machine.py`, MODIFY `panic_system.py`

---

#### V8.4.4e - Proactive Stagnation Predictor [P2 - LOW]

**Problème**: Détection après 3 messages similaires (réactif → 3 tours gaspillés)

**Solution**: Prédiction basée sur trajectoire + leading indicators

**Leading Indicators**:
- "let me think", "we should consider" → +0.15
- "I agree but" → +0.20
- Decreasing message lengths → +0.25
- Tool mention without use → +0.20

**Actions par seuil**:
| Probabilité | Action |
|-------------|--------|
| < 0.4 | CONTINUE |
| 0.4-0.6 | MONITOR |
| 0.6-0.8 | NUDGE (gentle) |
| > 0.8 | INJECT_WARNING |

| Tâche | Effort | Status |
|-------|--------|--------|
| Créer StagnationPredictor | 3h | PLANNED |
| Intégrer dans detector | 1h | PLANNED |
| Tests avec vrais logs | 3h | PLANNED |
| **Total** | **7h** | |

**Fichiers**: CREATE `stagnation_predictor.py`, MODIFY `stagnation_detector.py`

---

**Effort Total V8.4.4**: ~56h (~2 semaines full-time)

**Sources Web**:
- [pytransitions AsyncMachine](https://github.com/pytransitions/transitions) - FSM async avec `queued='model'`
- [Saga Pattern Python](https://johal.in/implementing-saga-pattern-in-python-distributed-transaction-management-for-services/) - Compensating transactions
- [Time Series Anomaly Detection](https://blog.jetbrains.com/pycharm/2025/01/anomaly-detection-in-time-series/) - Proactive prediction

---

### V8.4.5 - Cyborg Hardening ✅ COMPLETED (2025-12-11)

**Objectif**: Corrections de sécurité, performance async, et qualité architecturale
**Source**: 4 Explore agents + Web Research + Plan "Cyborg Hardening"
**Philosophie**: *"Harden the castle before expanding"*

#### P0 - Sécurité (CRITIQUE) ✅

| Correction | Fichier | Impact |
|------------|---------|--------|
| PathGuardian sacred files check en READ | `core/security/path_guardian.py:105-108` | `.env`, credentials bloqués en lecture ET écriture |
| PathGuardian.validate_read() appelé dans _execute_read() | `core/execution/tool_manager.py:293-332` | Path traversal patché (CWE-22) |
| .env retiré du whitelist evolution | `core/execution/tool_manager.py:1171` | Credentials jamais lisibles par agents |
| Tests de sécurité path traversal | `tests/test_path_traversal_security.py` | 16 tests couvrant tous les vecteurs |

**Vulnérabilité corrigée (CWE-22)**:
- `../.env` - BLOQUÉ (fichier sacré)
- `./../.env` - BLOQUÉ (fichier sacré)
- `foo/../../.env` - BLOQUÉ (fichier sacré)
- Symlinks vers fichiers sacrés - BLOQUÉS
- Chemins absolus hors zones - BLOQUÉS

#### P1 - Performance Async ✅

| Correction | Fichier | Impact |
|------------|---------|--------|
| ParallelExecutor → asyncio.gather() | `core/swarm/mode_executors.py:548-600` | True async (vs ThreadPoolExecutor bloquant) |
| _invoke_async() dans ModeExecutor | `core/swarm/mode_executors.py:180-220` | Pattern réutilisable pour tous les executors |
| HiveMind phases → send_message_async() | Déjà intégré V8.4.4 | Bridge async/sync fonctionnel |

#### P2 - Architecture ✅

| Correction | Fichier | Impact |
|------------|---------|--------|
| Thread-safe singleton (double-checked locking) | `core/async_primitives/process_handle.py:306-320` | Race conditions éliminées |
| Thread-safe singleton | `core/logging/logger_v7.py:422-439` | Thread-safe logger init |
| Thread-safe singleton | `core/agents/unified_registry.py:363-386` | Thread-safe registry init |
| CommandRegistry structure | `core/interface/commands/` | Strategy Pattern pour REPL commands |
| Rename commands.py → slash_commands.py | `core/interface/slash_commands.py` | Évite conflit package/module |

#### P3 - Robustesse ✅

| Correction | Fichier | Impact |
|------------|---------|--------|
| `except:` → `except Exception:` | `core/logging/logger_v7.py` (4 occurrences) | Permet SystemExit/KeyboardInterrupt |

**Tests de validation**:
- `pytest tests/test_path_traversal_security.py` → 16/16 ✅
- `pytest tests/test_security*.py` → 108/108 ✅
- REPL import OK ✅

---

### V8.4.6 - Session Isolation Hardening ✅ COMPLETED (2025-12-11)

**Objectif**: Éliminer le context leakage dans les drivers LLM multi-agents
**Source**: Audit Gemini `NEXUS_AUDIT_2025-12-11.md` + Deep Analysis Claude
**Commit**: `186a42e`

#### P0 - Session Leakage Fix (CRITIQUE) ✅

| Correction | Fichier | Impact |
|------------|---------|--------|
| REMOVE `--resume latest` fallback (Windows) | `gemini_driver_v7.py:343-363` | Contexte ne fuit plus entre tâches Swarm |
| REMOVE `--resume latest` fallback (Unix) | `gemini_driver_v7.py:376-379` | Idem |
| REMOVE `--resume latest` fallback (stream Windows) | `gemini_driver_v7.py:641-648` | Idem pour invoke_stream() |
| REMOVE `--resume latest` fallback (stream Unix) | `gemini_driver_v7.py:657-660` | Idem |
| REMOVE `--resume latest` fallback (async) | `async_gemini_driver.py:180-185` | Driver async également sécurisé |

**Comportement post-fix**:
- Si `session_uuid` fourni → `--resume {uuid}` (isolation Swarm)
- Si `session_uuid` absent → Session FRESH (safe default, pas de leak)
- Warning log si session était active mais pas d'UUID passé

#### P1 - Claude Context File Security ✅

| Correction | Fichier | Impact |
|------------|---------|--------|
| Context files 0o600 permissions | `claude_driver_hybrid.py:126-131` | Prompts protégés (owner-only) |
| Context files 0o600 permissions | `claude_driver_hybrid.py:284-289` | Idem pour invoke_stream() |

#### P2 - Thread Safety ✅

| Correction | Fichier | Impact |
|------------|---------|--------|
| `_claude_processes_lock` mutex | `claude_driver_hybrid.py:60-62` | Race conditions PARALLEL éliminées |
| Thread-safe append | `claude_driver_hybrid.py:155-157` | Accès liste protégé |
| Thread-safe remove | `claude_driver_hybrid.py:241-243,315-317,379-382` | Cleanup thread-safe |

**Vulnérabilité corrigée (Context Leakage)**:
- `--resume latest` permettait à une tâche Swarm de voir le contexte d'une autre
- 20+ code paths identifiés sans `session_uuid` (FSM, HiveMind phases)
- Fix: Default FRESH plutôt que RESUME si pas d'UUID explicite

**Validation**:
- 16/16 security tests ✅
- Driver imports OK ✅
- Session isolation verified ✅

---

### V8.4.7 - Cyborg Hardening ✅ PARTIAL (2025-12-11)

**Objectif**: Corrections audit-driven + documentation recherche
**Source**: `audit/ANGLES_MORTS_2025-12-11.md` + `audit/grok_audit11122025.md`
**Commit**: `db5fdb5`

| Tâche | Effort | Status |
|-------|--------|--------|
| P0 Path Traversal Security | - | ✅ ALREADY DONE (V8.4.6) |
| P2 Singleton Race Conditions | - | ✅ ALREADY DONE (double-checked locking) |
| P3 Exception Logging (critical pass) | 1h | ✅ DONE |
| Fix README version (7.8 → 8.4.6) | 10min | PLANNED |
| Budget tokens→USD (orchestrator.py:274) | 2h | PLANNED |
| P1 Async Improvements | 4h+ | DEFERRED (large scope) |

**Fichiers modifiés**:
- `core/drivers/gemini_driver_v7.py` - Logging cleanup processus
- `core/mcp/client.py` - Logging erreurs JSON

**Documentation recherche créée**:
- `docs/PROMPT_INJECTION_PREVENTION_GUIDE.md` - AWS/Azure/OWASP patterns
- `docs/MCP_SERVER_IMPLEMENTATION_GUIDE.md` - FastMCP + Claude Desktop
- `docs/OPENTELEMETRY_IMPLEMENTATION_GUIDE.md` - GenAI semantic conventions

**Tests**: 59/59 security tests pass

---

### Audit Grok (2025-12-11) - Deep Logic Issues 🆕

**Source**: `audit/grok_audit11122025.md`
**Analyste**: Grok (X.AI)

| ID | Issue | Sévérité | Description | Phase Cible |
|----|-------|----------|-------------|-------------|
| GROK-001 | Race Conditions Blackboard TTL | **P0** | Pas d'atomicité CAS sur expiry en PARALLEL | V8.5.x |
| GROK-002 | Decay Formula SuccessMemory | P1 | Linéaire (devrait être exponentiel) | V8.5.x |
| GROK-003 | KERNEL Heredity Check | P1 | Spawned agents bypass KERNEL validation | V8.6.x |
| GROK-004 | Fallback Chain Non-Adaptative | P2 | Chains statiques ignorent contexte | V8.5.x |
| GROK-005 | Federated RAG | P2 | LanceDB monolithique (bruit multi-domain) | V9.x |

**Propositions Grok (à évaluer)**:

| Proposition | Effort | Impact | Priorité |
|-------------|--------|--------|----------|
| Atomic TTL (CAS) pour Blackboard | 4-6h | ↓90% races, ↑20% PARALLEL perf | HIGH |
| Exponential Decay en SuccessMemory | 3-5h | ↑15-25% adaptation modes | MEDIUM |
| KERNEL Heredity Check at Spawn | 5-7h | ↓80% risque adversarial | HIGH |
| Adaptive Fallbacks via Predictor | 8-10h | ↓10-15s temps COMPLEX | MEDIUM |
| Federated RAG per Domain | 6-8h | ↑20-30% recall sémantique | LOW |

---

### Audit Angles Morts (2025-12-11) - P0 Critiques

**Source**: `audit/ANGLES_MORTS_2025-12-11.md`

| Issue | Status | Notes |
|-------|--------|-------|
| repl.py 2,972 lignes (God Object) | PLANNED V8.6 | Split en 4 modules (REPL, Commands, Evolution, Spawn) |
| 8 singletons globals | ✅ DONE | Thread-safe double-checked locking |
| 435 bare except | PLANNED V8.5.3 | Top 50 en priorité |
| Tests E2E manquants | PLANNED V8.6 | Hive Mind → Swarm pipeline |
| Input validation (prompt injection) | PLANNED V8.8 | Voir docs/PROMPT_INJECTION_PREVENTION_GUIDE.md |

---

| Tâche | Effort | Status |
|-------|--------|--------|
| OllamaDriver implementation | 8h | PLANNED |
| Register Ollama in AgentRegistry | 1h | PLANNED |
| Fallback chain: Cloud → Local | 4h | PLANNED |
| Tests offline mode | 4h | PLANNED |

**Référence**: Audit2_08122025.md Gap 1 (BLOQUANT pour Motherson)

---

## Roadmap V8.5 (Architecture Cleanup) [REFACTORING]

> **Status**: Post-V8.4, architectural improvements
> **Source**: `audit/CLAUDE_audit10122025.md`

### V8.5.0 - Split mode_executors.py [Priority: P1]

**Objectif** : Décomposer le God Object (1,120 lignes → 6 fichiers)

**Note**: AgentRegistry déplacé en V8.4.0 (prérequis Ollama)

**Problème actuel**:
- `core/swarm/mode_executors.py` = 1,120 lignes
- 6 executors différents dans 1 seul fichier
- Difficile à maintenir et tester

**Solution**:
```
core/swarm/executors/
├── __init__.py         # Re-exports
├── base.py             # ModeExecutor ABC + AgentResponse
├── parallel.py         # ParallelExecutor
├── sequential.py       # SequentialExecutor
├── lead_support.py     # LeadSupportExecutor
├── ping_pong.py        # PingPongExecutor
├── specialist.py       # SpecialistExecutor
└── red_blue.py         # RedBlueExecutor
```

| Tâche | Effort | Status |
|-------|--------|--------|
| Créer structure `executors/` | 30min | PLANNED |
| Extraire ParallelExecutor | 1h | PLANNED |
| Extraire autres executors | 3h | PLANNED |
| Mettre à jour imports | 1h | PLANNED |
| Tests regression | 1h | PLANNED |

---

### V8.5.2 - Split repl.py [Priority: P2]

**Objectif** : Décomposer le God Object REPL (2,780 lignes → 3-4 modules)

**Problème actuel**:
- `core/interface/repl.py` = 2,780 lignes
- Mélange: parsing, session, display, commands

**Solution proposée**:
```
core/interface/
├── repl.py             # Main loop (500 lignes)
├── command_parser.py   # Command parsing
├── session_manager.py  # Session state
└── display_manager.py  # Rich console output
```

| Tâche | Effort | Status |
|-------|--------|--------|
| Extraire CommandParser | 3h | PLANNED |
| Extraire DisplayManager | 2h | PLANNED |
| Refactor REPL main | 2h | PLANNED |
| Tests regression | 2h | PLANNED |

---

### V8.5.3 - Exception Hygiene (FL-004) [Priority: P2]

**Objectif** : Nettoyer les 390 `except Exception` silencieux

**Statistique**: `grep -r "except Exception" core/ | wc -l` → 390

**Stratégie par priorité**:

| Priorité | Pattern | Action |
|----------|---------|--------|
| P0 | `except Exception: pass` | Log + raise ou handle spécifiquement |
| P1 | `except Exception as e: pass` | Log error, continue |
| P2 | `except Exception as e: return default` | Acceptable si documenté |

**Fichiers prioritaires** (drivers, executors):
- `core/drivers/gemini_driver_v7.py` - subprocess errors
- `core/drivers/claude_driver_hybrid.py` - subprocess errors
- `core/swarm/mode_executors.py` - execution errors

| Tâche | Effort | Status |
|-------|--------|--------|
| Audit des except silencieux critiques | 2h | PLANNED |
| Fix drivers (subprocess) | 2h | PLANNED |
| Fix executors | 2h | PLANNED |
| Tests error propagation | 2h | PLANNED |

---

### V8.5.4 - Replace print(stderr) with Logger [Priority: P2] 🆕 FROM AUDIT

**Objectif** : Standardiser les logs (32 occurrences print(stderr))
**Source**: `audit/ANGLES_MORTS_2025-12-11.md`

**Fichiers concernés** (9 fichiers):
- `core/drivers/gemini_driver_v7.py` - 7 occurrences
- `core/drivers/claude_driver_hybrid.py` - 9 occurrences
- `core/drivers/async_gemini_driver.py` - 4 occurrences
- `core/drivers/async_claude_driver.py` - 3 occurrences
- `core/orchestration/fsm_handlers.py` - 5 occurrences
- `core/swarm/mode_executors.py` - 1 occurrence
- `core/swarm/hybrid_swarm_engine.py` - 1 occurrence
- `core/governance/red_team/validator.py` - 1 occurrence
- `core/logging/logger_v7.py` - 1 occurrence

| Tâche | Effort | Status |
|-------|--------|--------|
| Remplacer print(stderr) dans drivers | 2h | PLANNED |
| Remplacer print(stderr) dans swarm | 1h | PLANNED |
| Tests logging output | 1h | PLANNED |

---

### V8.5.5 - Singleton → Factory Pattern [Priority: P2] 🆕 FROM AUDIT

**Objectif** : Éliminer les 17 globals singletons pour testabilité
**Source**: `audit/ANGLES_MORTS_2025-12-11.md`

**Statistique**: `grep -r "global _" core/ | wc -l` → 17

**Singletons identifiés**:
| Module | Singleton | Impact Tests |
|--------|-----------|--------------|
| `unified_registry.py` | `_registry` | Tests flaky |
| `async_factory.py` | `_global_factory` | State partagé |
| `gemini_driver_v7.py` | `_persistent_process` | Leak ressources |
| `process_handle.py` | `_global_registry` | Cleanup difficile |
| `execution_policy.py` | `_policy`, `_code_validator` | State partagé |
| `logger_v7.py` | `_global_logger` | OK (acceptable) |
| `budget_tracker.py` | `_tracker` | State partagé |
| `success_memory.py` | `_default_memory` | State partagé |

**Solution**: Convertir en Factory pattern avec reset() pour tests
```python
class ProcessRegistryFactory:
    _instance: Optional[ProcessHandleRegistry] = None
    _lock = threading.Lock()

    @classmethod
    def get(cls) -> ProcessHandleRegistry:
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = ProcessHandleRegistry()
        return cls._instance

    @classmethod
    def reset(cls) -> None:  # For tests
        cls._instance = None
```

| Tâche | Effort | Status |
|-------|--------|--------|
| Convertir 3 singletons critiques (registry, factory, process_handle) | 3h | PLANNED |
| Ajouter reset() pour tests | 1h | PLANNED |
| Update conftest.py fixtures | 1h | PLANNED |
| Tests isolation | 1h | PLANNED |

---

### V8.5.6 - Tests E2E Pipeline [Priority: P1] 🆕 FROM AUDIT

**Objectif** : Tester le pipeline complet Hive Mind → Swarm
**Source**: `audit/ANGLES_MORTS_2025-12-11.md`

**Scénarios manquants**:
| Scénario | Status |
|----------|--------|
| Hive Mind → Swarm full pipeline | ❌ |
| Success Memory feedback loop | ❌ |
| Agent spawn + invoke + cleanup | ❌ |
| Graceful shutdown under load | ❌ |

| Tâche | Effort | Status |
|-------|--------|--------|
| Créer `tests/test_e2e_hive_swarm.py` | 4h | PLANNED |
| Test Success Memory feedback | 2h | PLANNED |
| Test graceful shutdown | 2h | PLANNED |

---

## Roadmap V8.6 (Productization) [VISION LONG-TERME]

> **Status**: Post-V8.5, dépend des retours terrain
> **Note**: Renommé de V8.4 → V8.6 suite au feedback consolidé (2025-12-10)

### V8.6.0 - Docker Packaging [Priority: P3]

**Objectif** : Déploiement simplifié via container

| Tâche | Effort | Status |
|-------|--------|--------|
| Dockerfile multi-stage | 4h | PLANNED |
| docker-compose.yml | 2h | PLANNED |
| Volume mounts pour workspace | 1h | PLANNED |
| Documentation déploiement | 2h | PLANNED |

**Source**: Gemini (2025-12-09) - Plan V8.4 (original)

---

### V8.6.1 - REST API (FastAPI) [Priority: P4]

**Objectif** : API HTTP pour intégrations externes

**⚠️ Note**: Reporté à V9.0+ pour enterprise deployment (feedback Claude Web)

| Tâche | Effort | Status |
|-------|--------|--------|
| FastAPI wrapper | 8h | PLANNED |
| Endpoints CRUD tasks | 4h | PLANNED |
| WebSocket streaming | 4h | PLANNED |
| Auth middleware | 4h | PLANNED |

**Source**: Gemini (2025-12-09) - Plan V8.4 (original)

---

### V8.6.2 - Observability Dashboard [Priority: P4]

**Objectif** : Visualisation temps réel du système

**⚠️ Note Claude**: CLI suffit pour debugging actuel. Dashboard = nice-to-have post-stabilisation.

| Tâche | Effort | Status |
|-------|--------|--------|
| React dashboard | 16h | PLANNED |
| WebSocket real-time | 4h | PLANNED |
| Métriques visualisation | 8h | PLANNED |

**Source**: Gemini (2025-12-09) - Plan V8.4 (original)

---

## Roadmap V8.7 (Async Maturity) [POST-CYBORG]

> **Status**: Post-V8.4.4 StateGuard
> **Source**: Gemini DeepThink analysis + Claude implementation validation (2025-12-10)
> **Branch**: N9AF → merge to N8THM when stable

### V8.7.0 - Process Lifecycle FSM (Bio-Moniteur)

**Objectif**: Ajouter un mini-FSM au cycle de vie des processus async

**États**:
```
GESTATION → ALIVE → STALLED → DYING → DEAD
   (boot)    (ok)   (>30s)   (cancel)
```

**Intégration**: `core/async_primitives/process_handle.py`

| Tâche | Effort | Status |
|-------|--------|--------|
| Ajouter `ProcessLifecycleState` enum | 1h | PLANNED |
| Implémenter heartbeat detection | 2h | PLANNED |
| Ajouter `stalled_since` timestamp | 1h | PLANNED |
| Watchdog coroutine (vérif périodique) | 3h | PLANNED |
| Tests lifecycle transitions | 2h | PLANNED |

---

### V8.7.1 - HiveMind Saga Manager (Phase Checkpoints)

**Objectif**: Système de checkpoints pour les 7 phases HiveMind

**Problème actuel**: 24 états HiveMind sans guards → pas de rollback ni resume

**Solution**:
```python
# core/hive_mind/saga_manager.py (NOUVEAU)
class SagaManager:
    """Checkpoint system for HiveMind phases."""

    def __init__(self, blackboard: AsyncBlackboard):
        self.checkpoints: Dict[str, SagaCheckpoint] = {}
        self._phase_guards = {
            HiveMindState.HIVE_ARCHITECTING: self._guard_architect,
            HiveMindState.HIVE_EXECUTING: self._guard_execute,
        }

    async def save_checkpoint(self, phase: HiveMindState, data: Dict):
        """Sauvegarde atomique avant phase critique."""
        self.checkpoints[phase.value] = SagaCheckpoint(
            phase=phase,
            data=data,
            timestamp=datetime.now()
        )

    async def rollback_to(self, phase: HiveMindState):
        """Restaure état d'un checkpoint précédent."""
        if phase.value in self.checkpoints:
            return self.checkpoints[phase.value].data
        raise CheckpointNotFoundError(phase)
```

| Tâche | Effort | Status |
|-------|--------|--------|
| Créer `SagaManager` class | 4h | PLANNED |
| Ajouter phase guards | 3h | PLANNED |
| Intégrer dans `TrueHiveMind` | 4h | PLANNED |
| Tests checkpoint/rollback | 3h | PLANNED |

---

### V8.7.2 - UI State Director (Visual State)

**Objectif**: État visuel temps réel pour l'UI pendant les opérations async

**Problème actuel**: REPL affiche état uniquement APRÈS `process_turn()` → "blindness"

**Solution**:
```python
# core/ui/state_director.py (NOUVEAU)
class UIStateDirector:
    """Dicte l'état visuel du REPL."""

    def __init__(self):
        self._state = UIState.IDLE
        self.on_state_change = asyncio.Event()

    @property
    def visual_state(self) -> str:
        return {
            UIState.IDLE: "nexus7> ",
            UIState.THINKING: "[🤔 Thinking...]",
            UIState.STREAMING: "[📝 Streaming...]",
            UIState.EXECUTING: "[⚡ Executing...]",
            UIState.ERROR: "[❌ Error]",
        }.get(self._state, "")
```

| Tâche | Effort | Status |
|-------|--------|--------|
| Créer `UIStateDirector` class | 2h | PLANNED |
| Intégrer dans `run_async()` | 2h | PLANNED |
| Ajouter spinners Rich | 1h | PLANNED |
| Tests visual state transitions | 2h | PLANNED |

---

### V8.7.3 - FSM I/O Extraction (Functional Core)

**Objectif**: Séparer logique pure et I/O dans FSMHandlers

**Problème actuel**: 1,099 lignes mêlant décisions et appels API

**Solution pattern**:
```python
# AVANT (V8): Handler fait tout
def handle_brainstorming(self):
    context = self._build_context()      # Logique
    response = driver.invoke(context)    # I/O BLOQUANT!
    self._process_response(response)     # Logique

# APRÈS (V8.7): Handler = pure logique, yield work items
async def handle_brainstorming(self):
    context = self._build_context()                    # Logique
    work_item = WorkItem(type="INVOKE", context=context)
    response = yield work_item                         # I/O délégué
    return self._process_response(response)            # Logique
```

| Tâche | Effort | Status |
|-------|--------|--------|
| Définir `WorkItem` dataclass | 1h | PLANNED |
| Créer `AsyncExecutor` (I/O worker) | 4h | PLANNED |
| Refactor `handle_brainstorming` | 3h | PLANNED |
| Refactor `handle_validating_cfl` | 3h | PLANNED |
| Refactor `_handle_moderate_plus` | 6h | PLANNED |
| Tests execution separation | 4h | PLANNED |

---

## Roadmap V8.8 (Security Hardening) [FROM AUDIT 2025-12-11] 🆕

> **Status**: Post-V8.5, security-first
> **Source**: `audit/ROADMAP_ENRICHMENT_2025-12-11.md` + Industry research (OWASP, AWS Guardrails)
> **Contexte Industrie**: Prompt injection = #1 vulnérabilité OWASP 2025 (73% des déploiements)

### V8.8.0 - Input Guardrails [Priority: P0]

**Objectif**: Prévenir les attaques par injection de prompts
**Référence**: [AWS Bedrock Guardrails](https://aws.amazon.com/blogs/security/safeguard-your-generative-ai-workloads-from-prompt-injections/)

**Gap actuel**:
- Aucune validation des inputs utilisateur
- Pas de sanitization des réponses LLM
- Pas de sandboxing des agents spawnés

**Pattern de détection**:
```python
# core/security/input_guardrails.py (NOUVEAU)
class InputGuardrails:
    INJECTION_PATTERNS = [
        r"ignore\s+(previous|above|all)\s+instructions",
        r"you\s+are\s+now\s+(a|an)\s+",
        r"forget\s+(everything|all)",
        r"system\s*:\s*",
        r"<\|im_start\|>",  # ChatML injection
    ]

    def validate(self, user_input: str) -> Tuple[bool, str]:
        for pattern in self.INJECTION_PATTERNS:
            if re.search(pattern, user_input, re.IGNORECASE):
                return False, f"Potential injection detected: {pattern}"
        return True, ""
```

| Tâche | Effort | Status |
|-------|--------|--------|
| Créer `core/security/input_guardrails.py` | 4h | PLANNED |
| Intégrer dans REPL input | 1h | PLANNED |
| Tests injection patterns | 2h | PLANNED |
| Logging tentatives d'injection | 1h | PLANNED |

---

### V8.8.1 - Output Validation [Priority: P1]

**Objectif**: Valider les réponses LLM avant exécution

**Risques actuels**:
- LLM peut générer des commandes malveillantes
- Pas de validation du JSON tool_use
- Hallucinations de chemins/fichiers

| Tâche | Effort | Status |
|-------|--------|--------|
| Créer output sanitizer | 3h | PLANNED |
| Valider tool_use JSON schema | 2h | PLANNED |
| Path existence check avant write | 1h | PLANNED |
| Tests hallucination detection | 2h | PLANNED |

---

### V8.8.2 - Agent Sandboxing [Priority: P1]

**Objectif**: Isoler les agents spawnés dans un subprocess sandboxé

**Gap actuel**:
- Agents spawnés ont accès complet au workspace
- Pas d'isolation mémoire/CPU
- Pas de timeout strict

**Solution proposée**:
```python
# subprocess avec restrictions
sandbox_config = {
    "timeout": 300,           # 5 min max
    "max_memory": "1G",       # Limite mémoire
    "allowed_dirs": [workspace],  # Restriction I/O
    "no_network": False       # Configurable
}
```

| Tâche | Effort | Status |
|-------|--------|--------|
| Sandbox subprocess wrapper | 4h | PLANNED |
| Resource limits (CPU, memory) | 2h | PLANNED |
| Network isolation option | 2h | PLANNED |
| Tests sandboxing | 2h | PLANNED |

---

### V8.8.3 - Log Redaction [Priority: P2]

**Objectif**: Supprimer les secrets des logs

**Risque actuel**: API keys, tokens peuvent apparaître dans logs

| Tâche | Effort | Status |
|-------|--------|--------|
| Pattern redaction dans logger | 2h | PLANNED |
| Redact API keys (sk-*, AIKEY-*) | 1h | PLANNED |
| Tests redaction | 1h | PLANNED |

---

## Roadmap V8.9 (Observability & Evaluation) [FROM AUDIT 2025-12-11] 🆕

> **Status**: Post-V8.6, production monitoring
> **Source**: `audit/ROADMAP_ENRICHMENT_2025-12-11.md` + Industry research (OpenTelemetry, CLASSic)
> **Contexte Industrie**: OpenTelemetry = standard, CLASSic = framework d'évaluation agents 2025

### V8.9.0 - OTLP Observability Exporter [Priority: P2]

**Objectif**: Traces distribuées compatibles OpenTelemetry
**Référence**: [OpenTelemetry AI Agent Observability](https://opentelemetry.io/blog/2025/ai-agent-observability/)

**Gap actuel**:
- Logs JSONL non compatibles OTLP
- Pas de traces distribuées (spans)
- Pas de replay de sessions

| Tâche | Effort | Status |
|-------|--------|--------|
| Créer OTLP exporter | 4h | PLANNED |
| Span per tool call | 2h | PLANNED |
| Session replay capability | 3h | PLANNED |

---

### V8.9.1 - Token/Cost Real-time Tracking [Priority: P1]

**Objectif**: Monitoring coûts en temps réel

**Gap actuel**: `budget_limit_usd=50` pas vérifié côté drivers

| Tâche | Effort | Status |
|-------|--------|--------|
| Budget abort sur dépassement | 2h | PLANNED |
| Token counting per agent | 2h | PLANNED |
| Cost dashboard CLI | 2h | PLANNED |

---

### V8.9.2 - CLASSic Metrics Integration [Priority: P2]

**Objectif**: Métriques standardisées (Cost, Latency, Accuracy, Stability, Security)
**Référence**: [CLASSic Framework - Aisera](https://aisera.com/ai-agents-evaluation/)

**Métriques à tracker**:
| Métrique | Description | Status |
|----------|-------------|--------|
| **C**ost | USD per task | ⚠️ Partiel |
| **L**atency | P50/P95/P99 | ❌ |
| **A**ccuracy | Success rate per domain | ⚠️ Partiel |
| **S**tability | Error rate, retries | ⚠️ Partiel |
| **S**ecurity | Blocked attempts | ✅ (PathGuardian) |

| Tâche | Effort | Status |
|-------|--------|--------|
| Implémenter CLASSic collector | 4h | PLANNED |
| Latency percentiles | 2h | PLANNED |
| CLI metrics summary | 2h | PLANNED |

---

### V8.9.3 - Automated Benchmark Suite [Priority: P2]

**Objectif**: Benchmarks automatisés pour comparaison mode vs mode

| Tâche | Effort | Status |
|-------|--------|--------|
| Créer benchmark tasks suite | 4h | PLANNED |
| Mode comparison dashboard | 3h | PLANNED |
| Regression detection | 2h | PLANNED |

---

## Roadmap V9.0 (Enterprise) [VISION LONG-TERME] 🆕

> **Status**: Post-V8.x stabilisation
> **Source**: `audit/ROADMAP_ENRICHMENT_2025-12-11.md` + Industry research (McKinsey, NIST AI RMF)
> **Contexte Industrie**: McKinsey 2025: "Barrier #1 = lack of governance"

### V9.0.0 - MCP Server [Priority: P1]

**Objectif**: Exposer NEXUS comme un outil pour d'autres agents (Claude Desktop, etc.)
**Référence**: [Microsoft MCP Patterns](https://microsoft.github.io/autogen/dev/user-guide/agentchat-user-guide/tutorial/models.html)

**Gap actuel**: NEXUS a MCP Client mais PAS MCP Server

| Tâche | Effort | Status |
|-------|--------|--------|
| MCP Server implementation | 8h | PLANNED |
| Expose NEXUS as tool | 2h | PLANNED |
| Tests Claude Desktop integration | 4h | PLANNED |

---

### V9.0.1 - REST API (FastAPI) [Priority: P2]

**Objectif**: API HTTP pour intégrations enterprise

| Tâche | Effort | Status |
|-------|--------|--------|
| FastAPI wrapper | 8h | PLANNED |
| Authentication (JWT) | 4h | PLANNED |
| WebSocket streaming | 4h | PLANNED |

---

### V9.0.2 - RBAC [Priority: P2]

**Objectif**: Role-Based Access Control pour multi-tenant

| Tâche | Effort | Status |
|-------|--------|--------|
| Role definitions | 2h | PLANNED |
| Permission checks | 4h | PLANNED |
| Audit trail | 4h | PLANNED |

---

### V9.0.3 - Cryptographic Audit Trail [Priority: P2]

**Objectif**: Audit trail avec signatures cryptographiques (NIST AI RMF)

| Tâche | Effort | Status |
|-------|--------|--------|
| Hash chain for events | 4h | PLANNED |
| Event signatures | 2h | PLANNED |
| Compliance report generator | 4h | PLANNED |

---

## Ideas Backlog (Non-Priorisé)

> Idées intéressantes mais non planifiées. À réévaluer post-V8.2.

### FROM AUDIT 2025-12-11 (Gemini + Claude)

| Idée | Source | Priorité Suggérée | Notes |
|------|--------|-------------------|-------|
| **Agent Reaper (GC)** | Gemini Audit | P2 | Garbage collection pour agents zombies |
| **CLASSic Metrics** | ROADMAP_ENRICHMENT | P1 | Cost/Latency/Accuracy/Stability/Security standardisés |
| **MCP Server** | ROADMAP_ENRICHMENT | P1 | Exposer NEXUS comme tool pour Claude Desktop |
| **OTLP Exporter** | ROADMAP_ENRICHMENT | P2 | Traces OpenTelemetry compatibles |
| **Input Guardrails** | NEXUS_AUDIT | P0 | Protection prompt injection (OWASP #1) |
| **Output Sanitization** | NEXUS_AUDIT | P1 | Valider réponses LLM avant exécution |
| **Budget USD Enforcement** | NEXUS_AUDIT | P1 | Abort si budget dépassé (ligne 274 orchestrator) |
| **Agent Sandboxing** | NEXUS_AUDIT | P1 | Subprocess isolation pour agents spawnés |
| **Log Redaction** | ANGLES_MORTS | P2 | Supprimer secrets des logs |
| **LangGraph Export** | ROADMAP_ENRICHMENT | P3 | Interopérabilité frameworks |
| **A2A Protocol** | ROADMAP_ENRICHMENT | P3 | Google Agent-to-Agent protocol |

### PRE-EXISTING

| Idée | Source | Notes |
|------|--------|-------|
| TaskGraph DAG | Gemini V8.2 | Over-engineering pour usage actuel |
| Distributed Tracing (OTLP) | Gemini V8.3 | Overkill pour projet solo |
| N-Agent Agnosticism | Gemini V7.5.3 | Étendre spawned à tous les 6 modes swarm |
| Self-Healing Swarm | Gemini V8 | Fallback mode-level automatique |
| Budget Reservation System | Claude Opus 4.5 | Pré-allouer budget par phase HiveMind |
| PARALLEL Intelligent Merge | Claude Opus 4.5 | LLM synthesis vs concat (KI-004) |
| Disaster Recovery Checkpoints | Claude Opus 4.5 | State checkpoints mid-execution |
| Context Window Pro-Active Estimation | Claude Opus 4.5 | Estimer tokens avant opération |
| **File Lock Manager** | Gemini V9.0 (2025-12-09) | **VALIDÉ** - Prevent race conditions PARALLEL mode |
| **Skill Crystallization (3x)** | Gemini V9.0 (2025-12-09) | **VALIDÉ** - Transform 3x successes → permanent tool (Phase 21 Sedimentation enhancement) |
| **Watchdog Daemon** | Gemini V9.0 (2025-12-09) | **VALIDÉ** - Background process for night maintenance (V9.1) |
| AgentRegistry refactor | Gemini V9.0 (2025-12-09) | Merge spawned+builtin agents in single registry |
| Context Slicing | Gemini V9.0 (2025-12-09) | RAG pre-slice pour longues tâches |

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

### V9.0 "Living Repository" (Gemini Analysis 2025-12-09)

> Source: Gemini audit + vision proposals, analysé et filtré par Claude

**Concepts Validés (à implémenter post-V8.3)**:

| Phase | Concept | Description | Prérequis |
|-------|---------|-------------|-----------|
| V8.4.1 | **File Lock Manager** | `asyncio.Lock()` per-file, prevent PARALLEL race conditions | V8.3.x stable |
| Phase 21+ | **Skill Crystallization 3x** | Transform 3x successes → permanent tool (seuil ajusté) | SuccessMemory active |
| V9.1 | **Watchdog Daemon** | Background process: nightly cleanup, memory optimization | V8.4 Docker |

**Concepts Mappés sur Roadmap Existante**:

| Concept Gemini | Mapping NEXUS | Notes |
|----------------|---------------|-------|
| Mission Control WebUI | Phase 22 "NEXUS CEREBRO" | Déjà planifié |
| GraphRAG | Phase 20 "Synaptic Graph" | Déjà planifié |
| Skill Crystallization | Phase 21 "Sedimentation" | Seuil ajusté 3x |

**Concepts Non Retenus**:

| Concept | Raison |
|---------|--------|
| AgentRegistry merge | Over-engineering, spawned vs builtin ont des lifecycles différents |
| Context Slicing agressif | Déjà géré par RAG chunking |

**Enterprise Gaps (Post-V8.3)**:

| Gap | Impact | Phase Cible |
|-----|--------|-------------|
| Air-Gapped (OllamaDriver) | BLOQUANT Motherson | V8.2.2 |
| Multi-Tenant (SessionContext) | Équipes multiples | V8.2.1 |
| Encryption at Rest | Données sensibles | V8.2.1 |

---

### Vision Long-Terme: Phases 17-24 (FROM ROADMAP_HIVE_MIND)

> Source: ROADMAP_HIVE_MIND.md + Analyse codebase Claude Opus 4.5 (2025-12-09)
> Recherche web: aiosqlite, MCP SDK, GraphRAG Neo4j, E2B/Modal sandbox

---

#### PILIER 1: INFRASTRUCTURE (The Foundation)

##### Phase 17: "Ironclad Memory" (SQLite Migration)

| Aspect | Détails |
|--------|---------|
| **Objectif** | Migration AtomicJsonStore → SQLite WAL mode |
| **Gain** | Fin race conditions, requêtes analytiques, resurrection protocol |
| **Effort** | 2-3 semaines |
| **Prérequis** | Aucun |

**Fichiers Impactés** (Exploration Claude 2025-12-09):

| Fichier JSON | Taille | Queries | Priorité |
|--------------|--------|---------|----------|
| `workspace/memory/successes.json` | ~4KB (10k max) | Linear scan, similarity | P1 |
| `workspace/.nexus/dylan_scores.json` | ~4.8KB | Agent lookup, history | P1 |
| `workspace/memory/fitness_scores.json` | ~565B | Agent task lookup | P1 |
| `.nexus/project_knowledge.json` | Variable (5k chunks) | RAG retrieval | P1 |
| `workspace/.nexus/blackboard.json` | ~405B | State, history append | P2 |

**Note**: LanceDB déjà utilisé pour Dense backend (`core/memory/project_memory.py`) - bon signe!

**Blind Spots Identifiés** (Exploration 2025-12-09):
1. ❌ Pas de transactions cross-fichiers (si crash entre 2 writes → état incohérent)
2. ❌ Pas de schema versioning (migration JSON v6 → v7 impossible)
3. ❌ RLock = process-local (pas de protection multi-process)
4. ❌ Pas de cleanup AtomicJsonStoreManager sur workspace change
5. ❌ SuccessMemory: Full list loaded every query (10k entries → slow)
6. ❌ Time decay calculation done on-the-fly (should be indexed)

**Implémentation Recommandée** ([aiosqlite](https://github.com/omnilib/aiosqlite)):
```python
# workspace/.nexus/nexus.db (single file)
# PRAGMAs recommandés (source: charlesleifer.com)
await conn.execute("PRAGMA journal_mode = WAL")
await conn.execute("PRAGMA synchronous = NORMAL")
await conn.execute("PRAGMA cache_size = 10000")
await conn.execute("PRAGMA mmap_size = 268435456")

# Schema versioning
PRAGMA user_version = 1;
```

**Tables Proposées**:
| Table | Source JSON | Index | Query Pattern |
|-------|-------------|-------|---------------|
| `blackboard` | blackboard.json | `(active_agent, timestamp)` | State lookup |
| `successes` | successes.json | `task_hash, domain` | Similarity search |
| `dylan_scores` | dylan_scores.json | `agent_id, domain` | Top-N ranking |
| `project_chunks` | project_knowledge.json | `source_file` | RAG retrieval |

**Protocole de Test**:
- [ ] Test: Transaction rollback sur erreur
- [ ] Test: Concurrent writes (10 threads)
- [ ] Test: Migration JSON→SQLite préserve données
- [ ] Test: WAL checkpoint automatique

---

##### Phase 18: "Native Neural Link" (API Drivers) - ATTENTION CLI-FIRST

| Aspect | Détails |
|--------|---------|
| **Objectif** | Réduire overhead subprocess, ajouter prompt caching |
| **⚠️ Contrainte** | NEXUS utilise CLI (gemini/claude), PAS les APIs directes |
| **Gain** | Latence réduite, prompt caching Anthropic (-90% coûts) |
| **Effort** | 2 semaines |

**Architecture Actuelle** (analyse codebase):
- `gemini_driver_v7.py:289` - `subprocess.Popen()` avec JSON-RPC over files
- `claude_driver_hybrid.py:124` - subprocess similaire, mode hybrid XML
- `gemini_driver_v7.py:204` - File I/O: `_IO_BUFFER/gemini_context_{uuid}.md`

**Options d'Optimisation (CLI-compatible)**:

| Option | Description | Effort | Gain |
|--------|-------------|--------|------|
| **18a** | `asyncio.create_subprocess_exec()` | 4h | True async, pas de thread blocking |
| **18b** | Session pooling (réutiliser `--resume`) | 2h | Skip init overhead |
| **18c** | Prompt caching via Claude CLI `--cache-control` | 3h | -90% tokens répétés |
| **18d** | Native SDK (FUTUR) | 2 sem | Full control, mais perd CLI features |

**Recherche Web - Claude Prompt Caching** ([docs.claude.com](https://docs.claude.com/en/docs/build-with-claude/prompt-caching)):
- Cache TTL: 5min (default) ou 1h
- Pricing: Write 1.25x, Read 0.1x base price
- Latency: >2x faster, costs up to 90% less
- **Limite**: 4 cache breakpoints par prompt

**Recherche Web - Gemini CLI Async** ([gemini-cli-sdk PyPI](https://pypi.org/project/gemini-cli-sdk/)):
- SDK qui wrappe CLI en subprocess avec parsing Instructor
- Issue connue: ACP mode prompt login en subprocess (github #12042)

**Blind Spots**:
1. ❌ `claude mcp serve` existe mais pas exploité (permet Claude as MCP Server)
2. ❌ Pas de métriques latence subprocess vs native
3. ❌ Prompt caching non implémenté (system prompt identique entre calls)

**Protocole de Test**:
- [ ] Benchmark: subprocess vs asyncio.create_subprocess_exec()
- [ ] Test: Session reuse avec `--resume` réduit latence
- [ ] Test: Prompt cache hit rate > 80% sur tâches similaires

---

##### Phase 19: "Containment Protocol" (Docker Sandbox)

| Aspect | Détails |
|--------|---------|
| **Objectif** | Isoler exécution outils dynamiques |
| **Gain** | Sécurité totale (agent peut `rm -rf /` sans risque hôte) |
| **Effort** | 1-2 semaines |
| **Prérequis** | Docker installé |

**Fichiers Impactés** (analyse codebase):
- `core/execution/tool_manager.py:109-128` - Tool dispatch (bash, dynamic_tool)
- `core/execution/dynamic_tools.py:289-372` - `subprocess.run()` sans isolation
- `core/security/execution_policy.py:200+` - AST validation (insuffisant)

**Limites Actuelles**:
| Protection | Actuel | Avec Docker |
|------------|--------|-------------|
| CPU | ❌ Aucune | ✅ `cpu_quota=50000` |
| Mémoire | ❌ Aucune | ✅ `mem_limit=512m` |
| Filesystem | ⚠️ PathGuardian | ✅ Volume mount RO/RW |
| Réseau | ❌ Aucune | ✅ `network_disabled=True` |
| Timeout | ✅ 30s | ✅ Container timeout |

**Recherche Web - Sandbox Options** ([modal.com/blog](https://modal.com/blog/top-code-agent-sandbox-products)):
| Solution | Isolation | Boot Time | BYOC |
|----------|-----------|-----------|------|
| [E2B](https://e2b.dev/) | Firecracker microVM | ~150ms | Experimental |
| Modal | gVisor containers | Sub-second | Non |
| Docker local | Container | ~500ms | Oui |
| SkyPilot | VM | 2-5s | Oui |

**Recommandation**: Docker local pour V19, E2B pour V19.1 (cloud)

**Implémentation**:
```python
# core/execution/docker_sandbox.py
class DockerSandbox:
    def execute(self, cmd: str, timeout: int = 30) -> Result:
        return self.client.containers.run(
            "nexus-sandbox:alpine-python3.13",
            cmd,
            volumes={str(self.workspace): {"bind": "/work", "mode": "rw"}},
            mem_limit="512m",
            cpu_quota=50000,
            network_disabled=True,
            remove=True,
            timeout=timeout
        )
```

**Blind Spots**:
1. ❌ Docker non disponible sur tous les environnements (fallback subprocess?)
2. ❌ Volume mount leak (agent peut lire tout workspace)
3. ❌ Pas de secrets isolation (env vars visibles)

**Protocole de Test**:
- [ ] Test: `rm -rf /` dans container = host intact
- [ ] Test: Fork bomb dans container = container killed, host OK
- [ ] Test: Network request dans container = blocked
- [ ] Test: Fallback subprocess si Docker indisponible

---

#### PILIER 2: COGNITION & ÉVOLUTION (The Brain)

##### Phase 20: "Synaptic Graph" (GraphRAG)

| Aspect | Détails |
|--------|---------|
| **Objectif** | Knowledge Graph pour causalités code |
| **Gain** | "Si agent modifie api.py → tester test_api.py" automatiquement |
| **Effort** | 3-4 semaines |
| **Prérequis** | Phase 17 (SQLite) |

**Fichiers Impactés** (analyse codebase):
- `core/memory/project_memory.py:200-400` - Chunking sans extraction entités
- `core/memory/backends/dense.py` - Embedding search, pas de graph traversal
- `core/memory/success_memory.py:20` - task_hash sans semantic graph

**Limites RAG Actuel**:
| Capability | Actuel | Avec GraphRAG |
|------------|--------|---------------|
| Similarity search | ✅ TF-IDF/BM25/Dense | ✅ + Graph traversal |
| Entity extraction | ❌ | ✅ Functions, Classes, Variables |
| Causal relationships | ❌ | ✅ "A calls B", "X extends Y" |
| Error→Cause linking | ❌ | ✅ "Error E caused by module M" |

**Recherche Web - GraphRAG** ([neo4j.com/labs](https://neo4j.com/labs/genai-ecosystem/llamaindex/)):
- LlamaIndex + Neo4j = GraphRAG pipeline complet
- Entity extraction via AST (Python) ou LLM (autres langages)
- Performance: **+40-60% answer relevance** vs vector-only
- Retrieval: Vector + Graph traversal hybride

**Architecture Proposée**:
```python
# core/memory/entity_extractor.py
@dataclass
class Entity:
    type: str  # "function", "class", "variable", "module"
    name: str
    source_file: str
    line_range: Tuple[int, int]

@dataclass
class Relationship:
    source: Entity
    rel_type: str  # "calls", "extends", "modifies", "imports"
    target: Entity
    confidence: float

# SQLite tables (Phase 17)
# CREATE TABLE entities (id, type, name, file, line_start, line_end)
# CREATE TABLE relationships (source_id, rel_type, target_id, confidence)
```

**Blind Spots**:
1. ❌ AST extraction = Python only (JS, Go, Rust need different parsers)
2. ❌ Graph peut devenir volumineux (10k+ nodes sur gros projets)
3. ❌ Neo4j = dépendance lourde (SQLite + recursive CTE suffisant?)
4. ❌ Pas de LLM extraction budget (entity extraction coûteuse)

**Protocole de Test**:
- [ ] Test: Extract entities from 100-file Python project
- [ ] Test: Query "functions that call authenticate()" returns correct set
- [ ] Test: Graph size < 100MB pour projet 50k LOC
- [ ] Test: Retrieval accuracy +30% vs TF-IDF seul

---

##### Phase 21: "Sedimentation" (Skill Crystallization)

| Aspect | Détails |
|--------|---------|
| **Objectif** | Outils dynamiques réussis 3x → permanents |
| **Gain** | NEXUS construit sa propre toolbox optimisée |
| **Effort** | 2 semaines |
| **Prérequis** | Phase 17 (SQLite pour tracking usage) |

**Seuil Ajusté**: 3x succès (pas 5x comme ROADMAP_HIVE_MIND original)
- Source: Gemini V9.0 analysis recommande seuil plus bas pour adoption rapide

---

#### PILIER 3: OBSERVABILITÉ & INTERFACE (The Face)

##### Phase 22: "NEXUS CEREBRO" (Web Dashboard)

| Aspect | Détails |
|--------|---------|
| **Objectif** | Visualisation temps réel Swarm + Lineage |
| **Gain** | Debug visuel, Time Travel, confiance utilisateur |
| **Effort** | 4 semaines |
| **Stack** | FastAPI + React Flow |

---

##### Phase 23: "Open Telemetry" (OTLP Standard)

| Aspect | Détails |
|--------|---------|
| **Objectif** | Export traces OTLP (Jaeger/Grafana) |
| **Gain** | Waterfall visualization, latency analysis |
| **Effort** | 1 semaine |

---

#### PILIER 4: ÉCOSYSTÈME (The Network)

##### Phase 24: "NEXUS as a Server" (MCP Server)

| Aspect | Détails |
|--------|---------|
| **Objectif** | Exposer NEXUS comme MCP Server |
| **Gain** | `@nexus "Refactorise ce module"` depuis Claude Desktop/VSCode |
| **Effort** | 2 semaines |
| **Prérequis** | Aucun (MCP client existe déjà) |

**État Actuel MCP** (Exploration Claude 2025-12-09):

| Composant | Status | Fichier |
|-----------|--------|---------|
| MCP Client | ✅ COMPLET | `core/mcp/client.py` (530 lignes) |
| MCP Protocol | ✅ COMPLET | `core/mcp/protocol.py` (474 lignes) |
| MCP Registry | ✅ COMPLET | `core/mcp/registry.py` (392 lignes) |
| Tool Integration | ✅ COMPLET | `core/execution/tool_manager.py:1244-1443` |
| MCP Server | ❌ MANQUANT | `core/mcp/server.py` - À créer |
| Test Server Mock | ✅ EXISTE | `tests/fixtures/mock_mcp_server.py` (233 lignes) |

**Architecture Actuelle (Client-Only)**:
```
External MCP Server → MCPClient → ToolManager.tools["mcp_{server}_{tool}"]
                                         ↓
                            ClaudeDriver / GeminiDriver
```

**Ce Qui Manque** (pour exposer NEXUS comme MCP Server):
- ❌ `core/mcp/server.py` - Inversé du client (écoute stdin, répond stdout)
- ❌ Tool schemas (inputSchema JSON) pour les 11+ tools internes
- ❌ Auth/authz via OAuth 2.1 (MCP SDK inclut `mcp.server.auth`)
- ❌ Configuration server dans `workspace/.nexus/mcp_servers.json`

**Recherche Web - MCP Server** ([modelcontextprotocol.io](https://modelcontextprotocol.io/quickstart/client)):
- `claude mcp serve` expose déjà Claude Code comme MCP Server
- SDK Python officiel: `pip install mcp` (v1.23.2, 20k+ stars)
- Transport: stdio (sécurisé), SSE (HTTP), WebSocket

**Tools à Exposer**:
| Tool | Safety | Priority | inputSchema |
|------|--------|----------|-------------|
| `nexus_read` | Safe | HIGH | `{file_path: string}` |
| `nexus_glob` | Safe | HIGH | `{pattern: string}` |
| `nexus_grep` | Safe | HIGH | `{pattern: string, glob?: string}` |
| `nexus_swarm` | Medium | HIGH | `{task: string, mode?: string}` |
| `nexus_spawn` | Medium | MEDIUM | `{role: string}` |
| `nexus_write` | Dangerous | LOW | Requires explicit permission |

**Implémentation** ([MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)):
```python
# core/mcp/server.py
from mcp.server import Server
from mcp.types import Tool, TextContent

server = Server("nexus-mcp")

@server.list_tools()
async def list_tools():
    return [
        Tool(name="nexus_read", description="Read file", inputSchema={...}),
        Tool(name="nexus_swarm", description="Execute via Swarm", inputSchema={...}),
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict):
    result = tool_manager.execute(name.replace("nexus_", ""), arguments)
    return [TextContent(type="text", text=result.output)]
```

**Blind Spots**:
1. ❌ Pas d'auth MCP (n'importe quel client peut appeler)
2. ❌ Tool explosion (16+ tools → complex discovery)
3. ❌ Pas de rate limiting MCP server side

**Protocole de Test**:
- [ ] Test: Claude Desktop connecte à `nexus mcp serve`
- [ ] Test: `nexus_read` retourne contenu fichier
- [ ] Test: `nexus_swarm` exécute tâche PARALLEL
- [ ] Test: Tools dangereux (write, bash) refusés par défaut

---

**Plan d'Attaque Révisé** (basé sur dépendances):
```
Phase 17 (SQLite) ──────────────────┬──→ Phase 20 (GraphRAG)
                                    └──→ Phase 21 (Sedimentation)

Phase 18 (CLI Optimizations) ──────────→ Standalone

Phase 19 (Docker Sandbox) ─────────────→ Standalone

Phase 24 (MCP Server) ─────────────────→ Quick Win (1-2 sem)
```

1. **Semaine 1-2**: Phase 24 (MCP Server) - Quick win, unlock IDE integration
2. **Semaine 3-4**: Phase 17 (SQLite) - Foundation pour GraphRAG
3. **Semaine 5-6**: Phase 19 (Docker) - Security hardening
4. **Semaine 7-10**: Phase 20 (GraphRAG) - Cognitive leap

---

### Test Protocols par Phase (Éviter Code Mort)

| Phase | Tests Requis | Fréquence | Automatisation |
|-------|-------------|-----------|----------------|
| **V8.3.3** | Merge quality, deduplication, conflict detection | Each merge | CI pytest |
| **Phase 17** | WAL concurrency (50 threads), migration JSON→SQLite, rollback | Migration + weekly | Integration tests |
| **Phase 18** | Session pool exhaustion, CLI crash recovery, Gemini resume | Daily smoke test | E2E tests |
| **Phase 19** | Sandbox escape attempts, resource limits, timeout handling | Security audit | Fuzzing |
| **Phase 20** | Graph query accuracy vs RAG baseline, entity extraction | Benchmark suite | Comparison tests |
| **Phase 24** | MCP tools exposure, auth validation, tool schema compliance | MCP validator | SDK tests |

---

### Recherches Web - Sources (2025-12-09)

| Topic | Source | Key Insight |
|-------|--------|-------------|
| **aiosqlite** | [PyPI](https://pypi.org/project/aiosqlite/) | v0.21.0 (Feb 2025), WAL mode obviates async need |
| **aiosqlitepool** | [PyPI](https://pypi.org/project/aiosqlitepool/) | Connection pool for hot cache |
| **MCP SDK** | [GitHub](https://github.com/modelcontextprotocol/python-sdk) | v1.23.2, 20k+ stars, OAuth 2.1 built-in |
| **GraphRAG** | [LlamaIndex V2](https://developers.llamaindex.ai/python/examples/cookbooks/graphrag_v2/) | Neo4j + Leiden algorithm for communities |
| **E2B Sandbox** | [e2b.dev](https://e2b.dev/) | Firecracker microVM, <200ms startup |
| **Modal Sandbox** | [modal.com](https://modal.com/blog/top-code-agent-sandbox-products) | gVisor isolation, GPU support |
| **M1-Parallel** | [arXiv](https://arxiv.org/abs/2507.08944) | LLM aggregation, 2.2× speedup |
| **Gemini CLI Resume** | [Discussion](https://github.com/google-gemini/gemini-cli/discussions/1538) | `--resume` flag, `/chat save/resume` |
| **Claude Session** | [Claude Docs](https://docs.claude.com/en/api/agent-sdk/sessions) | `fork_session` for branching |

---

## Priorités Immédiates (Cette Semaine)

| # | Tâche | Version | Effort | Status |
|---|-------|---------|--------|--------|
| 1 | ~~Hot-Swap Lead Agent~~ | V8.0.1 | ~~4h~~ | ✅ Done |
| 2 | ~~Thread-Safe Parallel~~ | V8.1.6 | ~~6h~~ | ✅ Done |
| 3 | ~~Dynamic Spawn Brainstorm~~ | V8.1.8 | ~~8h~~ | ✅ Done |
| 4 | ~~Model Selection Brainstorm~~ | V8.1.8-B | ~~4h~~ | ✅ Done |
| 5 | ~~RAG Commands~~ | V8.1.9 | ~~2h~~ | ✅ Done |
| 6 | ~~SuccessMemory Hook~~ | V8.2.0-pre | ~~5h~~ | ✅ Done |
| 7 | ~~UUID Propagation~~ | V8.2.0-pre | ~~2h~~ | ✅ Done |
| 8 | ~~EPHEMERAL Sessions (core)~~ | V8.0.3 | ~~6h~~ | ⚡ Partial (tests pending) |
| 9 | ~~Fix 16 tests flaky~~ | V8.0.2 | ~~4h~~ | ✅ Done (AUTO_SKIP exists) |
| 10 | ~~CI/CD GitHub Actions~~ | V8.0.2 | ~~4h~~ | ✅ Done (`.github/workflows/ci.yml`) |
| 11 | ~~Decay Formula SuccessMemory~~ | V8.1.0 | ~~2h~~ | ✅ Done (`_apply_time_decay()`) |
| 12 | ~~Unified Analysis Adapter~~ | V8.2.0a | ~~3h~~ | ✅ Done (`core/adapters/`) |
| 13 | ~~SwarmBridge "Dictator Mode"~~ | V8.3.0 | ~~4h~~ | ✅ Done |
| 14 | ~~SwarmTool "Swarm as Invocable Tool"~~ | V8.3.1 | ~~3h~~ | ✅ Done |
| 15 | ~~Depth Guard Anti-Recursion~~ | V8.3.1-hotfix | ~~30min~~ | ✅ Done |
| 16 | ~~V8.3.2 "Closing the Loop"~~ | V8.3.2 | ~~4h~~ | ✅ Done |
| 16a | └─ ~~C3: Version sync~~ | V8.3.2 | ~~10min~~ | ✅ Already correct |
| 16b | └─ ~~TD-001: async_utils.py~~ | V8.3.2 | ~~30min~~ | ✅ Refactored |
| 16c | └─ ~~FG-001: SuccessAdapter SwarmBridge~~ | V8.3.2 | ~~1h~~ | ✅ Already impl |
| 16d | └─ ~~MT-001: Checkpoint tests~~ | V8.3.2 | ~~1h~~ | ✅ Already impl |
| 16e | └─ ~~H3: CLAUDE.md update~~ | V8.3.2 | ~~1h~~ | ✅ Updated |
| 17 | ~~Parallel Merge Strategy~~ | V8.3.3 | ~~3h~~ | ✅ Done |
| 18 | ~~Cyborg V7.5 Async Integration~~ | V8.4.0-cyborg | ~~6h~~ | ✅ Done (branch N9AF) |
| 19 | ~~Blind Spot Analysis~~ | V8.4.4 | ~~4h~~ | ✅ Done (7 angles morts identifiés) |
| 20 | ~~Cyborg Hardening (P0-P3)~~ | V8.4.5 | ~~8h~~ | ✅ Done (security + async + singletons) |
| 21 | **P1: DriverBridge Deprecation** | V8.4.4a | 5h | **NEXT** |
| 22 | **P0: SagaManager + Phase Guards** | V8.4.4b | 14h | CRITICAL |
| 23 | P1: WorkItem Yield Pattern | V8.4.4c | 21h | HIGH |
| 24 | P2: HealthStateMachine | V8.4.4d | 9h | MEDIUM |
| 25 | P2: Stagnation Predictor | V8.4.4e | 7h | LOW |
| 26 | RedTeam Post-Spawn | V8.2.0c | 2h | DEFERRED |

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
| KI-003 | HiveMindState count mismatch (24 vs 28 in docs) | LOW | NEW |
| KI-004 | PARALLEL merge = naive concatenation | MEDIUM | NEW |

---

## Changelog

| Date | Version | Changes |
|------|---------|---------|
| 2025-12-11 | 8.4.6-session-isolation | **SESSION ISOLATION HARDENING**: P0 Gemini `--resume latest` REMOVED (5 code paths), P1 Claude context files 0o600 permissions, P2 Thread-safe `_active_claude_processes`. ROADMAP enriched with V8.8 Security, V8.9 Observability, V9.0 Enterprise phases. Source: Audit Gemini `NEXUS_AUDIT_2025-12-11.md` + Claude deep analysis |
| 2025-12-11 | 8.4.5-cyborg-hardening | **CYBORG HARDENING COMPLETE**: P0 Path Traversal (CWE-22) patché, P1 asyncio.gather() migration, P2 Thread-safe singletons (3 fichiers), P2 CommandRegistry structure, P3 Exception handling. 108 security tests ✅. Source: 4 Explore agents + Web research + Cyborg Hardening plan |
| 2025-12-10 | 8.4.4-analysis | **BLIND SPOT ANALYSIS COMPLETE**: 7 angles morts identifiés (5 originaux + 2 nouveaux). Plan 56h créé: P1 DriverBridge (5h), P0 SagaManager (14h), P1 WorkItem (21h), P2 HealthFSM (9h), P2 StagnationPredictor (7h). Sources: Explore agents, Saga Pattern research, pytransitions AsyncMachine |
| 2025-12-10 | 8.4.0-cyborg | **Cyborg V7.5 COMPLETED**: Branch N9AF. Async methods added to nexus7.py (+55), repl.py (+190), orchestration_v7.py (+180). StateGuard V8.4.4 & V8.7 Async Maturity roadmap phases added. Source: Gemini DeepThink "Functional Core, Async Shell" analysis |
| 2025-12-10 | 8.3.4 | **Audit Quick Fixes**: FL-001 race condition fix, FL-002 completion detection. Source: CLAUDE_audit10122025.md |
| 2025-12-09 | 8.3.2d | **Deep Implementation Analysis**: Codebase exploration + web research. Added blind spots, file:line references, test protocols for Phases 17-24. Sources: aiosqlite, MCP SDK, GraphRAG Neo4j, E2B/Modal. Plan d'attaque révisé with dependencies |
| 2025-12-09 | 8.3.2c | **ROADMAP Consolidation**: Merged ROADMAP_HIVE_MIND.md Phases 17-24 into Vision Long-Terme section. Added V8.3.4 Symmetric MCP Bridges. Ideas Backlog enriched with File Lock Manager, Skill Crystallization 3x, Watchdog Daemon |
| 2025-12-09 | 8.3.2b | **Audit V9.0 Analysis**: Integrated Gemini "Living Repository" proposals - File Lock Manager (V8.4.1), Skill Crystallization 3x, Watchdog Daemon (V9.1). Enterprise gaps documented. Mermaid slash fix in doc_engine.py |
| 2025-12-09 | 8.3.2 | "Closing the Loop" audit corrections (FG-001, TD-001, MT-001, C3, H3) - Source: Claude+Gemini cross-audit |
| 2025-12-09 | 8.3.1-hotfix | Depth Guard anti-recursion + V8.3.3 merge_strategy planned (Gemini security analysis) |
| 2025-12-09 | 8.3.1 | SwarmTool "Swarm as Invocable Tool" - agents can invoke Swarm at any phase |
| 2025-12-09 | 8.3.0 | SwarmBridge "Dictator Mode" - HiveMind delegates to Swarm Engine |
| 2025-12-09 | 8.2.0a | V8.0.2 CI/CD + V8.1.0 Decay + V8.2.0a Adapter implemented. 12/13 priorities done! |
| 2025-12-09 | 8.2.0 | Roadmap audit: V8.0.3 EPHEMERAL marked partial (core done, tests pending), prompt V2 created |
| 2025-12-09 | 8.1.9c | Claude Opus 4.5 analysis: 4 valid findings (HiveMind 24 states, PARALLEL merge, budget reservation, disaster recovery) added to Ideas Backlog |
| 2025-12-09 | 8.1.9b | NEW: V8.2.0a-d (Unified Adapter, Map Update, RedTeam Spawn, Torture Protocol) - Source: Gemini Architecture Map analysis |
| 2025-12-09 | 8.1.9 | NEW: Roadmap V8.3-V8.4 (Memory Weaver, Agent Reaper, FSM Mapping, Docker, API) - Source: Gemini analysis + Claude validation |
| 2025-12-09 | 8.1.8-B | NEW: Model Selection Brainstorming - spawned agents choose their LLM (Gemini/Claude) |
| 2025-12-09 | 8.1.8 | NEW: Dynamic Spawn Brainstorming (Gemini analysis - spawned agents = coquilles vides) |
| 2025-12-09 | 8.1.6 | ✅ Thread-Safe Parallel Execution: unique filenames, session_uuid propagation, AsyncDriverAdapter |
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
