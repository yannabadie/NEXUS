# NEXUS V8.0 "TRUE HIVE MIND" - Roadmap Opérationnelle

**Version**: 8.3.2 | **Status**: Active | **Last Updated**: 2025-12-09
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

### V8.3.2 - "Closing the Loop" (Audit Corrections) [Priority: P1] (IN PROGRESS)

**Objectif** : Finaliser SwarmBridge/SwarmTool avant d'ajouter de la complexité

**Source** : Audit croisé Claude + Gemini (2025-12-09)

**Philosophie** : *"Finir proprement avant d'innover"* (Gemini)

| ID | Finding | Sévérité | Fichiers | Status |
|----|---------|----------|----------|--------|
| FG-001 | SuccessAdapter non appelé dans SwarmBridge | MEDIUM | `swarm_bridge.py` | PLANNED |
| TD-001 | Pattern async→sync dupliqué | LOW | `tool_manager.py`, `repl.py` | PLANNED |
| MT-001 | Tests checkpoint SwarmBridge | LOW | `test_swarm_bridge.py` | PLANNED |
| C3 | Version 7.0.0 vs 8.3.x | LOW | `core/__init__.py` | PLANNED |
| H3 | CLAUDE.md structure obsolète | LOW | `CLAUDE.md` | PLANNED |

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

### V8.3.3 - Parallel Merge Strategy [Priority: P2] (PLANNED)

**Objectif** : Stratégie intelligente de fusion des résultats PARALLEL

**Problème identifié** (Gemini 2025-12-09):
- Mode PARALLEL: 2 agents travaillent en parallèle
- Fusion actuelle: concat naïf (résultats collés bout à bout)
- Risque "Tour de Babel": informations contradictoires, redondances, incohérences

**Solution proposée - merge_strategy**:

```python
# core/hive_mind/types.py - ExecutionStep
@dataclass
class ExecutionStep:
    name: str
    agent_id: str
    action: str
    swarm_mode: Optional[str] = None
    merge_strategy: Optional[str] = None  # V8.3.2: "concat" | "consensus" | "summary"
```

**Stratégies**:

| Strategy | Description | Use Case |
|----------|-------------|----------|
| `concat` | Concaténation simple (défaut actuel) | Résultats indépendants |
| `consensus` | LLM identifie points d'accord/désaccord | Analyses divergentes |
| `summary` | LLM synthétise en résumé cohérent | Réduction de contexte |

**Implémentation prévue**:

```python
# core/hive_mind/phases/phase_execution.py
async def _merge_parallel_results(
    self,
    results: List[Dict],
    strategy: str = "concat"
) -> str:
    if strategy == "concat":
        return "\n---\n".join(r["output"] for r in results)

    elif strategy == "consensus":
        prompt = f"""
        Analyze these {len(results)} parallel results:
        {json.dumps(results, indent=2)}

        Identify:
        1. Points of agreement
        2. Points of disagreement
        3. Unique insights from each
        """
        return await self._invoke_synthesis_llm(prompt)

    elif strategy == "summary":
        prompt = f"Synthesize into coherent summary:\n{results}"
        return await self._invoke_synthesis_llm(prompt)
```

| Tâche | Effort | Status |
|-------|--------|--------|
| Ajouter merge_strategy à ExecutionStep | 10min | PLANNED |
| Implémenter _merge_parallel_results() | 2h | PLANNED |
| Configurer stratégie par défaut | 30min | PLANNED |
| Tests merge strategies | 1h | PLANNED |

**Fichiers concernés**:
- `core/hive_mind/types.py` - Nouveau champ merge_strategy
- `core/hive_mind/phases/phase_execution.py` - Logique de merge
- `core/hive_mind/swarm_bridge.py` - Propagation stratégie

**Source**: Gemini Security Analysis "Tour de Babel" (2025-12-09)

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

### V8.3.0 - Memory Weaver [Priority: P1]

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

## Roadmap V8.4 (Productization) [VISION LONG-TERME]

> **Status**: Post-V8.3, dépend des retours terrain

### V8.4.0 - Docker Packaging [Priority: P2]

**Objectif** : Déploiement simplifié via container

| Tâche | Effort | Status |
|-------|--------|--------|
| Dockerfile multi-stage | 4h | PLANNED |
| docker-compose.yml | 2h | PLANNED |
| Volume mounts pour workspace | 1h | PLANNED |
| Documentation déploiement | 2h | PLANNED |

**Source**: Gemini (2025-12-09) - Plan V8.4

---

### V8.4.1 - REST API (FastAPI) [Priority: P3]

**Objectif** : API HTTP pour intégrations externes

**⚠️ Prérequis**: Stabiliser core V8.2 avant d'exposer une API

| Tâche | Effort | Status |
|-------|--------|--------|
| FastAPI wrapper | 8h | PLANNED |
| Endpoints CRUD tasks | 4h | PLANNED |
| WebSocket streaming | 4h | PLANNED |
| Auth middleware | 4h | PLANNED |

**Source**: Gemini (2025-12-09) - Plan V8.4

---

### V8.4.2 - Observability Dashboard [Priority: P4]

**Objectif** : Visualisation temps réel du système

**⚠️ Note Claude**: CLI suffit pour debugging actuel. Dashboard = nice-to-have post-stabilisation.

| Tâche | Effort | Status |
|-------|--------|--------|
| React dashboard | 16h | PLANNED |
| WebSocket real-time | 4h | PLANNED |
| Métriques visualisation | 8h | PLANNED |

**Source**: Gemini (2025-12-09) - Plan V8.4

---

## Ideas Backlog (Non-Priorisé)

> Idées intéressantes mais non planifiées. À réévaluer post-V8.2.

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
| 16 | **V8.3.2 "Closing the Loop"** | V8.3.2 | 4h | **IN PROGRESS** |
| 16a | └─ C3: Version sync | V8.3.2 | 10min | **NEXT** |
| 16b | └─ TD-001: async_utils.py | V8.3.2 | 30min | PLANNED |
| 16c | └─ FG-001: SuccessAdapter SwarmBridge | V8.3.2 | 1h | PLANNED |
| 16d | └─ MT-001: Checkpoint tests | V8.3.2 | 1h | PLANNED |
| 16e | └─ H3: CLAUDE.md update | V8.3.2 | 1h | PLANNED |
| 17 | Parallel Merge Strategy | V8.3.3 | 3h | PLANNED |
| 18 | RedTeam Post-Spawn | V8.2.0c | 2h | PLANNED |

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
