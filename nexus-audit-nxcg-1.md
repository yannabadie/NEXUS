# NEXUS NX-CG — Plan de Remédiation Exhaustif

**Date**: 17 février 2026  
**Réf. audit**: `nexus-audit-nxcg.md`  
**Branche cible**: `NX-CG` (commit `8a489fe`)  
**Auteur**: Claude Opus 4.6  

---

## Table des matières

1. [Vue d'ensemble et priorisation](#1-vue-densemble-et-priorisation)
2. [P1.1 — Décomposition de l'OrchestratorV7](#2-p11--décomposition-de-lorchestrateurv7)
3. [P1.2 — Élimination des duplications systémiques](#3-p12--élimination-des-duplications-systémiques)
4. [P1.3 — Consolidation des Rate Limiters](#4-p13--consolidation-des-rate-limiters)
5. [P2.1 — Métacognition adaptative](#5-p21--métacognition-adaptative)
6. [P2.2 — Consolidation de la couche mémoire](#6-p22--consolidation-de-la-couche-mémoire)
7. [P2.3 — Nettoyage du code mort](#7-p23--nettoyage-du-code-mort)
8. [P2.4 — Réduction de la surface documentaire](#8-p24--réduction-de-la-surface-documentaire)
9. [P2.5 — Consolidation des packages core/](#9-p25--consolidation-des-packages-core)
10. [P2.6 — Optimisation du fast path](#10-p26--optimisation-du-fast-path)
11. [Matrice de risque et dépendances](#11-matrice-de-risque-et-dépendances)
12. [Calendrier d'exécution recommandé](#12-calendrier-dexécution-recommandé)
13. [Critères de validation](#13-critères-de-validation)

---

## 1. Vue d'ensemble et priorisation

### Matrice effort/impact

| ID | Chantier | Impact | Effort | Risque régression | Sprint |
|----|----------|--------|--------|-------------------|--------|
| P1.1 | Décomposer OrchestratorV7 | 🔴 Critique | Élevé | Élevé | 1-2 |
| P1.2 | Éliminer duplications legacy/v2 | 🔴 Critique | Moyen | Moyen | 1 |
| P1.3 | Consolider Rate Limiters | 🟠 Élevé | Faible | Faible | 1 |
| P2.1 | Métacognition adaptative | 🟡 Moyen | Faible | Faible | 2 |
| P2.2 | Consolider couche mémoire | 🟡 Moyen | Moyen | Moyen | 2-3 |
| P2.3 | Nettoyer code mort | 🟢 Hygiène | Faible | Nul | 1 |
| P2.4 | Réduire surface docs | 🟢 Hygiène | Faible | Nul | 1 |
| P2.5 | Consolider packages core/ | 🟡 Moyen | Élevé | Moyen | 3 |
| P2.6 | Optimiser fast path | 🟡 Moyen | Faible | Faible | 2 |

### Ordre d'exécution recommandé

```
Sprint 1 (Fondations)     Sprint 2 (Optimisation)     Sprint 3 (Consolidation)
─────────────────────     ──────────────────────      ──────────────────────
P2.3 Code mort            P1.1 OrchestratorV7         P2.2 Mémoire
P2.4 Docs cleanup         P2.1 Métacognition          P2.5 Packages
P1.2 Duplications         P2.6 Fast path
P1.3 Rate limiters
```

**Logique** : Sprint 1 élimine le bruit (code mort, doublons) pour réduire la surface avant les refactors structurels du Sprint 2. Sprint 3 attaque les chantiers les plus lourds une fois le terrain nettoyé.

---

## 2. P1.1 — Décomposition de l'OrchestratorV7

### Diagnostic

| Attribut | Valeur |
|----------|--------|
| Fichier | `core/orchestration_v7.py` |
| Lignes | 1224 |
| Responsabilités | FSM, routing, contexte, guards, mémoire, exécution |
| Violation | Single Responsibility Principle (SRP) |
| Risque | Point de défaillance unique, état en RAM non récupérable |

### Plan d'action

#### Étape 1 : Cartographie des responsabilités internes

Avant toute modification, analyser le fichier et identifier les blocs fonctionnels :

```
Commande d'analyse :
grep -n "def \|class \|async def " core/orchestration_v7.py | head -60
```

Responsabilités attendues à extraire :

| Bloc | Méthodes probables | Nouveau module cible |
|------|-------------------|---------------------|
| Gestion FSM | `_check_fsm_transition`, `_transition_state` | `core/orchestration/state_handler.py` |
| Routing | `_determine_route`, `_is_fast_path` | `core/orchestration/task_router.py` |
| Construction contexte | `_build_context`, `_inject_memory` | `core/orchestration/context_builder.py` (existe déjà) |
| Guards sécurité | `_check_input_guards`, `_check_output_guards` | `core/orchestration/guard_pipeline.py` |
| Exécution | `_execute`, `_run_hive_mind`, `_run_direct` | `core/orchestration/task_executor.py` |
| Gestion session | `_init_session`, `_save_state` | Déléguer à `core/session/` existant |

#### Étape 2 : Extraction progressive (sans big-bang)

**Principe** : Extraire un bloc à la fois, en gardant des méthodes de délégation dans `OrchestratorV7` pour ne pas casser les appelants.

**Ordre d'extraction** (du moins risqué au plus risqué) :

1. **GuardPipeline** (risque le plus bas, logique isolée)
2. **TaskRouter** (logique de décision pure, pas d'état)
3. **StateHandler** (encapsule la FSM, attention aux effets de bord)
4. **TaskExecutor** (le plus risqué, touche à l'exécution)

Pour chaque extraction :

```python
# Pattern de migration progressive

# 1. Créer le nouveau module
# core/orchestration/guard_pipeline.py
class GuardPipeline:
    """Pipeline de vérification input/output."""
    
    def __init__(self, input_guard: InputGuard, output_guard: OutputGuard):
        self.input_guard = input_guard
        self.output_guard = output_guard
    
    def check_input(self, user_input: str) -> None:
        """Vérifie l'input. Lève SecurityError si rejeté."""
        self.input_guard.validate(user_input)
    
    def check_output(self, result: str) -> str:
        """Filtre l'output. Retourne le résultat nettoyé."""
        return self.output_guard.sanitize(result)


# 2. Modifier OrchestratorV7 pour déléguer
class OrchestratorV7:
    def __init__(self, ...):
        # ... existant ...
        self.guard_pipeline = GuardPipeline(self.input_guard, self.output_guard)
    
    # Ancienne méthode reste mais délègue
    def _check_input_guards(self, user_input: str):
        return self.guard_pipeline.check_input(user_input)


# 3. Après validation, supprimer les anciennes méthodes inline
```

#### Étape 3 : Orchestrateur final (cible)

```python
# core/orchestration_v7.py — VERSION CIBLE (~80-100 lignes)

class OrchestratorV7:
    """Médiateur léger. Toute logique est déléguée."""
    
    def __init__(self, injector: DependencyInjector):
        self.fsm = injector.get(StateHandler)
        self.router = injector.get(TaskRouter)
        self.ctx_builder = injector.get(ContextBuilder)
        self.guards = injector.get(GuardPipeline)
        self.executor = injector.get(TaskExecutor)
        self.telemetry = injector.get(TelemetryService)
    
    async def process_turn(self, user_input: str) -> TurnResult:
        """Point d'entrée unique pour un tour de conversation."""
        with self.telemetry.trace("process_turn"):
            # 1. Sécurité entrée
            self.guards.check_input(user_input)
            
            # 2. Transition FSM
            state = self.fsm.transition(user_input)
            
            # 3. Construction contexte
            ctx = await self.ctx_builder.build(user_input, state)
            
            # 4. Routing
            route = self.router.route(user_input, state, ctx)
            
            # 5. Exécution
            result = await self.executor.execute(route, ctx)
            
            # 6. Sécurité sortie
            clean_result = self.guards.check_output(result)
            
            # 7. Mise à jour FSM post-exécution
            self.fsm.post_execution(state, clean_result)
            
            return clean_result
```

#### Tests de validation

```bash
# Baseline avant refactor : capturer l'état des tests
pytest tests/ -x --tb=short > baseline_tests.txt 2>&1
pytest tests/test_hive_mind_orchestrator.py -v > baseline_orchestrator.txt 2>&1

# Après chaque extraction : vérifier la non-régression
pytest tests/test_hive_mind_orchestrator.py tests/test_integration.py tests/test_global_integration.py -v

# Tests spécifiques au nouveau module
pytest tests/ -k "guard" -v  # pour GuardPipeline
pytest tests/ -k "router or routing" -v  # pour TaskRouter
pytest tests/ -k "fsm" -v  # pour StateHandler
```

#### Fichiers impactés

| Fichier | Action |
|---------|--------|
| `core/orchestration_v7.py` | Réduire de 1224 à ~100 lignes |
| `core/orchestration/guard_pipeline.py` | **Créer** |
| `core/orchestration/task_router.py` | **Créer** |
| `core/orchestration/state_handler.py` | **Créer** |
| `core/orchestration/task_executor.py` | **Créer** |
| `core/orchestration/context_builder.py` | Vérifier et enrichir (existe déjà) |
| `core/orchestration/dependency_injector.py` | Enregistrer les nouveaux services |
| `core/orchestration/__init__.py` | Exporter les nouveaux modules |
| `tests/test_hive_mind_orchestrator.py` | Adapter les imports |
| `tests/test_global_integration.py` | Vérifier la non-régression |

#### Critère de succès

- [ ] `OrchestratorV7` < 150 lignes
- [ ] Chaque module extrait a ses propres tests unitaires
- [ ] `pytest tests/ -x` : 0 régression
- [ ] Temps de traitement d'un turn identique (±5%)

---

## 3. P1.2 — Élimination des duplications systémiques

### Diagnostic

| Duplication | Fichier legacy | Fichier V2/cible | Action |
|-------------|---------------|-----------------|--------|
| SuccessMemory | `core/memory/success_memory.py` | `core/memory/success_memory_v2.py` | Migrer → V2, supprimer legacy |
| StrategyBlacklist | `core/memory/strategy_blacklist.py` | `core/memory/strategy_blacklist_v2.py` | Migrer → V2, supprimer legacy |
| ModeExecutors | `core/swarm/mode_executors.py` | `core/swarm/executors/*.py` (6 fichiers) | Supprimer mode_executors.py |
| SwarmBridge | `core/hive_mind/swarm_bridge.py` | `core/orchestration/swarm_bridge.py` | Consolider en un seul |
| Drivers legacy | `core/drivers/legacy/claude_driver_hybrid.py` | `core/drivers/anthropic_sdk_driver.py` | Supprimer legacy/ |
| Drivers legacy | `core/drivers/legacy/gemini_driver_v7.py` | `core/drivers/google_genai_sdk_driver.py` | Supprimer legacy/ |

### Plan d'action par duplication

#### 3.1 SuccessMemory

```bash
# Étape 1 : Identifier tous les imports de la version legacy
grep -rn "from.*success_memory import\|from.*success_memory " core/ tests/ --include="*.py" | grep -v "success_memory_v2"

# Étape 2 : Remplacer chaque import
# FROM: from core.memory.success_memory import SuccessMemory
# TO:   from core.memory.success_memory_v2 import SuccessMemoryV2 as SuccessMemory

# Étape 3 : Vérifier la compatibilité d'interface
# Si V2 a une interface différente, créer un adaptateur temporaire

# Étape 4 : Supprimer le fichier legacy
# rm core/memory/success_memory.py

# Étape 5 : Renommer V2 (optionnel, pour clarté)
# mv core/memory/success_memory_v2.py core/memory/success_memory.py
```

```python
# Si incompatibilité d'interface, adaptateur temporaire :
# core/memory/success_memory.py (remplace l'ancien, wrapper du V2)
from core.memory.success_memory_v2 import SuccessMemoryV2

class SuccessMemory(SuccessMemoryV2):
    """Alias de compatibilité. Sera supprimé au prochain sprint."""
    pass
```

#### 3.2 StrategyBlacklist

Même processus que 3.1 :

```bash
grep -rn "from.*strategy_blacklist import\|from.*strategy_blacklist " core/ tests/ --include="*.py" | grep -v "strategy_blacklist_v2"
```

#### 3.3 ModeExecutors monolithique

```bash
# Vérifier si mode_executors.py est encore importé
grep -rn "from.*mode_executors import\|import mode_executors" core/ tests/ --include="*.py"

# Si aucun import → suppression directe
# Si des imports existent → rediriger vers executors/
```

```python
# core/swarm/mode_executors.py — REMPLACEMENT (si imports existent)
"""
DEPRECATED: Utilisez core.swarm.executors directement.
Ce fichier sera supprimé au prochain sprint.
"""
import warnings
warnings.warn(
    "core.swarm.mode_executors est deprecated. "
    "Importez depuis core.swarm.executors.",
    DeprecationWarning,
    stacklevel=2
)
from core.swarm.executors import *  # noqa: F401,F403
```

#### 3.4 SwarmBridge (double localisation)

```bash
# Déterminer lequel est le "vrai"
wc -l core/hive_mind/swarm_bridge.py core/orchestration/swarm_bridge.py

# Vérifier les imports
grep -rn "swarm_bridge" core/ --include="*.py" | grep -v "__pycache__"
```

**Règle de décision** :
- Si `hive_mind/swarm_bridge.py` est le plus utilisé → le garder, supprimer `orchestration/swarm_bridge.py`
- Si les deux sont utilisés avec des rôles différents → renommer pour lever l'ambiguïté

#### 3.5 Drivers legacy

```bash
# Vérifier les imports des drivers legacy
grep -rn "legacy" core/drivers/ --include="*.py"
grep -rn "claude_driver_hybrid\|gemini_driver_v7" core/ tests/ --include="*.py"

# Si aucun import externe au dossier legacy/ → suppression du dossier
# rm -rf core/drivers/legacy/
```

### Fichiers impactés (consolidé)

| Action | Fichiers |
|--------|----------|
| **Supprimer** | `core/memory/success_memory.py` (après migration) |
| **Supprimer** | `core/memory/strategy_blacklist.py` (après migration) |
| **Supprimer** | `core/swarm/mode_executors.py` (après redirection) |
| **Supprimer** | `core/drivers/legacy/` (dossier entier) |
| **Supprimer ou consolider** | `core/hive_mind/swarm_bridge.py` OU `core/orchestration/swarm_bridge.py` |
| **Modifier** | Tous les fichiers qui importent les modules legacy |
| **Modifier** | `core/memory/__init__.py`, `core/swarm/__init__.py`, `core/drivers/__init__.py` |

### Tests de validation

```bash
# Après chaque suppression
pytest tests/ -x --tb=short
# Vérifier qu'aucun ImportError ne survient
python -c "import core; print('OK')"
```

### Critère de succès

- [ ] 0 fichier legacy dans `core/memory/`
- [ ] 0 fichier dans `core/drivers/legacy/`
- [ ] `mode_executors.py` supprimé
- [ ] Un seul `swarm_bridge.py`
- [ ] `grep -r "DEPRECATED" core/ --include="*.py"` retourne 0 résultat
- [ ] `pytest tests/ -x` : 0 régression

---

## 4. P1.3 — Consolidation des Rate Limiters

### Diagnostic

4 implémentations distinctes de rate limiting :

| Localisation | Usage | Scope |
|-------------|-------|-------|
| `core/resilience/rate_limiter.py` | Protection générale | Système |
| `core/security/rate_limiter.py` | Sécurité | Endpoints |
| `core/api/rate_limiter.py` | API Cerebro | HTTP |
| `core/evolution/rate_limiter.py` | Evolution pipeline | Mutations |

### Plan d'action

#### Étape 1 : Analyse des interfaces

```bash
# Extraire les signatures de chaque rate limiter
for f in core/resilience/rate_limiter.py core/security/rate_limiter.py core/api/rate_limiter.py core/evolution/rate_limiter.py; do
    echo "=== $f ==="
    grep -n "class \|def " "$f"
done
```

#### Étape 2 : Conception du rate limiter unifié

```python
# core/resilience/rate_limiter.py — VERSION UNIFIÉE

from enum import Enum
from dataclasses import dataclass
from typing import Optional
import time
import asyncio


class RateLimitScope(Enum):
    """Scope d'application du rate limiter."""
    SYSTEM = "system"          # Protection générale
    API = "api"                # Endpoints HTTP
    SECURITY = "security"      # Brute-force protection
    EVOLUTION = "evolution"    # Pipeline de mutation
    PROVIDER = "provider"     # Appels LLM externes


@dataclass
class RateLimitConfig:
    """Configuration d'un rate limiter."""
    scope: RateLimitScope
    max_requests: int
    window_seconds: float
    burst_multiplier: float = 1.5  # Tolérance de burst
    backoff_base: float = 1.0      # Base pour backoff exponentiel


class UnifiedRateLimiter:
    """Rate limiter unique paramétrable par scope."""
    
    # Configurations par défaut par scope
    DEFAULTS = {
        RateLimitScope.SYSTEM: RateLimitConfig(
            scope=RateLimitScope.SYSTEM,
            max_requests=100,
            window_seconds=60
        ),
        RateLimitScope.API: RateLimitConfig(
            scope=RateLimitScope.API,
            max_requests=60,
            window_seconds=60
        ),
        RateLimitScope.SECURITY: RateLimitConfig(
            scope=RateLimitScope.SECURITY,
            max_requests=5,
            window_seconds=300,
            backoff_base=2.0
        ),
        RateLimitScope.EVOLUTION: RateLimitConfig(
            scope=RateLimitScope.EVOLUTION,
            max_requests=10,
            window_seconds=3600
        ),
        RateLimitScope.PROVIDER: RateLimitConfig(
            scope=RateLimitScope.PROVIDER,
            max_requests=30,
            window_seconds=60
        ),
    }
    
    def __init__(self, config: Optional[RateLimitConfig] = None,
                 scope: RateLimitScope = RateLimitScope.SYSTEM):
        self.config = config or self.DEFAULTS[scope]
        self._requests: list[float] = []
        self._lock = asyncio.Lock()
    
    async def acquire(self, key: str = "default") -> bool:
        """Tente d'acquérir un slot. Retourne False si limité."""
        async with self._lock:
            now = time.monotonic()
            # Purger les requêtes hors fenêtre
            cutoff = now - self.config.window_seconds
            self._requests = [t for t in self._requests if t > cutoff]
            
            if len(self._requests) >= self.config.max_requests:
                return False
            
            self._requests.append(now)
            return True
    
    async def wait_and_acquire(self, key: str = "default",
                                max_wait: float = 30.0) -> bool:
        """Attend un slot disponible avec backoff."""
        attempt = 0
        while attempt < 10:
            if await self.acquire(key):
                return True
            wait = min(
                self.config.backoff_base * (2 ** attempt),
                max_wait
            )
            await asyncio.sleep(wait)
            attempt += 1
        return False


# Factory pour compatibilité avec le code existant
def create_rate_limiter(scope: RateLimitScope,
                         **overrides) -> UnifiedRateLimiter:
    """Crée un rate limiter avec configuration par scope."""
    config = UnifiedRateLimiter.DEFAULTS[scope]
    for k, v in overrides.items():
        if hasattr(config, k):
            setattr(config, k, v)
    return UnifiedRateLimiter(config=config, scope=scope)
```

#### Étape 3 : Migration des imports

```python
# core/security/rate_limiter.py — REMPLACEMENT
"""DEPRECATED: Utilisez core.resilience.rate_limiter.UnifiedRateLimiter"""
from core.resilience.rate_limiter import (
    UnifiedRateLimiter as RateLimiter,
    RateLimitScope,
    create_rate_limiter,
)
__all__ = ["RateLimiter", "RateLimitScope", "create_rate_limiter"]

# Idem pour core/api/rate_limiter.py et core/evolution/rate_limiter.py
```

#### Étape 4 : Mise à jour des consommateurs

```bash
# Identifier tous les consommateurs
grep -rn "RateLimiter\|rate_limiter" core/ --include="*.py" | grep -v "__pycache__" | grep -v "test_"
```

Pour chaque consommateur, remplacer :
```python
# AVANT
from core.security.rate_limiter import RateLimiter
limiter = RateLimiter(max_requests=5)

# APRÈS
from core.resilience.rate_limiter import create_rate_limiter, RateLimitScope
limiter = create_rate_limiter(RateLimitScope.SECURITY, max_requests=5)
```

### Fichiers impactés

| Fichier | Action |
|---------|--------|
| `core/resilience/rate_limiter.py` | **Réécrire** (version unifiée) |
| `core/security/rate_limiter.py` | **Remplacer** par re-export deprecated |
| `core/api/rate_limiter.py` | **Remplacer** par re-export deprecated |
| `core/evolution/rate_limiter.py` | **Remplacer** par re-export deprecated |
| `core/api/cerebro/rate_limit.py` | Mettre à jour les imports |
| `tests/test_rate_limiter.py` | Adapter + ajouter tests par scope |
| `tests/test_provider_rate_limiter.py` | Adapter |

### Critère de succès

- [ ] 1 seule classe `UnifiedRateLimiter`
- [ ] 3 fichiers réduits à des re-exports deprecated
- [ ] Tous les tests rate_limiter passent
- [ ] `pytest tests/ -x` : 0 régression

---

## 5. P2.1 — Métacognition adaptative

### Diagnostic

Le `MetacognitiveMonitor` effectue un scoring TF-IDF sur **chaque** step de raisonnement, y compris les tâches triviales (list files, status checks). Overhead inutile.

### Plan d'action

#### Étape 1 : Ajouter l'estimation de complexité

```python
# core/reasoning/task_complexity.py — NOUVEAU FICHIER

from enum import IntEnum
from typing import Set


class TaskComplexity(IntEnum):
    TRIVIAL = 0    # ls, status, help
    SIMPLE = 1     # single-step, factual
    MODERATE = 2   # multi-step, needs context
    COMPLEX = 3    # multi-agent, debate, research


# Marqueurs heuristiques
COMPLEX_MARKERS: Set[str] = {
    "analyse", "analyze", "compare", "create", "debug", "refactor",
    "research", "investigate", "design", "architect", "optimize",
    "benchmark", "audit", "review", "plan", "strateg"
}

TRIVIAL_COMMANDS: Set[str] = {
    "/help", "/status", "/agents", "/memory", "/quit", "/exit",
    "/workspace", "/model", "/budget", "/health"
}


def estimate_complexity(task: str) -> TaskComplexity:
    """Estimation heuristique rapide de la complexité d'une tâche."""
    task_lower = task.strip().lower()
    
    # Commandes slash → trivial
    if task_lower.startswith("/"):
        return TaskComplexity.TRIVIAL
    
    # Très court et sans marqueur complexe → trivial
    if len(task_lower) < 30 and not any(m in task_lower for m in COMPLEX_MARKERS):
        return TaskComplexity.TRIVIAL
    
    # Court sans marqueur → simple
    if len(task_lower) < 100 and not any(m in task_lower for m in COMPLEX_MARKERS):
        return TaskComplexity.SIMPLE
    
    # Présence de marqueurs complexes → moderate ou complex
    marker_count = sum(1 for m in COMPLEX_MARKERS if m in task_lower)
    if marker_count >= 3 or len(task_lower) > 500:
        return TaskComplexity.COMPLEX
    
    if marker_count >= 1:
        return TaskComplexity.MODERATE
    
    return TaskComplexity.SIMPLE
```

#### Étape 2 : Modifier le MetacognitiveMonitor

```python
# core/reasoning/metacognitive_monitor.py — MODIFICATION

from core.reasoning.task_complexity import TaskComplexity, estimate_complexity


class MetacognitiveMonitor:
    
    def __init__(self, ..., min_complexity: TaskComplexity = TaskComplexity.MODERATE):
        # ... existant ...
        self.min_complexity = min_complexity
        self._bypassed_count = 0
    
    def should_monitor(self, task: str) -> bool:
        """Décide si le monitoring est nécessaire pour cette tâche."""
        complexity = estimate_complexity(task)
        if complexity < self.min_complexity:
            self._bypassed_count += 1
            return False
        return True
    
    async def score_step(self, result, task: str = ""):
        """Score un step si la complexité le justifie."""
        if task and not self.should_monitor(task):
            return None  # Bypass
        # ... logique existante ...
```

#### Étape 3 : Intégrer dans le Swarm Engine

```python
# core/swarm/hybrid_swarm_engine.py — MODIFICATION

# Dans la méthode execute() ou équivalent :
async def execute(self, task: str, mode: CollaborationMode, ...):
    result = await self._run_executor(task, mode)
    
    # Monitoring conditionnel
    if self.metacognitive_monitor and self.metacognitive_monitor.should_monitor(task):
        await self.metacognitive_monitor.score_step(result, task=task)
    
    return result
```

### Fichiers impactés

| Fichier | Action |
|---------|--------|
| `core/reasoning/task_complexity.py` | **Créer** |
| `core/reasoning/metacognitive_monitor.py` | **Modifier** (ajouter should_monitor) |
| `core/swarm/hybrid_swarm_engine.py` | **Modifier** (conditionner le monitoring) |
| `core/hive_mind/phases/phase_execution.py` | **Modifier** (si monitoring inline) |
| `core/reasoning/__init__.py` | Exporter TaskComplexity |
| `tests/test_metacognitive_monitor.py` | Ajouter tests bypass |
| `tests/test_task_complexity.py` | **Créer** |

### Critère de succès

- [ ] Tâches triviales ("<50 chars, pas de marqueur") : 0 appel TF-IDF
- [ ] Tâches complexes : monitoring normal
- [ ] Latence REPL pour commandes simples réduite de 15-30%
- [ ] `pytest tests/ -x` : 0 régression

---

## 6. P2.2 — Consolidation de la couche mémoire

### Diagnostic

| Composant | Type | Statut |
|-----------|------|--------|
| `backends/tfidf.py` | Backend retrieval | Actif |
| `backends/bm25.py` | Backend retrieval | Actif |
| `backends/dense.py` | Backend retrieval | Actif ? |
| `backends/hybrid.py` | Backend retrieval | Méta-backend |
| `backends/base.py` | Interface | Base class |
| `adaptive_focus.py` | Service | ? |
| `adaptive_memory_organizer.py` | Service | ? |
| `auto_memory.py` | Service | Actif |
| `cache_manager.py` | Service | Actif |
| `context_compressor.py` | Service | Actif |
| `context_window_tracker.py` | Service | Actif |
| `conversation_store.py` | Service | Actif |
| `coordinator.py` | Service | Orchestrateur mémoire |
| `decay_scorer.py` | Service | Actif |
| `embedding_engine.py` | Service | Actif |
| `memory_pressure_monitor.py` | Service | ? |
| `namespace_manager.py` | Service | Actif |
| `plan_context_filter.py` | Service | ? |
| `pointer_memory.py` | Service | ? |
| `project_memory.py` | Service | Actif |
| `service.py` | Service | Point d'entrée |
| `spotlighting.py` | Service | ? |
| `strategy_blacklist_v2.py` | Service | Actif |
| `success_memory_v2.py` | Service | Actif |
| `tenant_memory.py` | Service | Multi-tenant |
| `types.py` | Types | Actif |

**= 26 fichiers** dans `core/memory/` (hors `__init__.py` et `ingestors/`).

### Plan d'action

#### Étape 1 : Audit d'utilisation réelle

```bash
# Pour chaque fichier de core/memory/, vérifier s'il est importé quelque part
for f in $(ls core/memory/*.py | grep -v __init__ | grep -v __pycache__); do
    module=$(basename "$f" .py)
    count=$(grep -rn "$module" core/ tests/ --include="*.py" | grep -v "$f" | grep -v __pycache__ | wc -l)
    echo "$count imports: $module"
done | sort -rn
```

#### Étape 2 : Supprimer les modules non importés

Tout module avec 0 imports externes = code mort → supprimer.

#### Étape 3 : Créer la façade MemoryFacade

```python
# core/memory/facade.py — NOUVEAU FICHIER

from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from enum import Enum

from core.memory.backends.base import MemoryBackend
from core.memory.backends.hybrid import HybridBackend
from core.memory.backends.tfidf import TFIDFBackend
from core.memory.context_compressor import ContextCompressor
from core.memory.decay_scorer import DecayScorer


class BackendType(Enum):
    TFIDF = "tfidf"
    BM25 = "bm25"
    DENSE = "dense"
    HYBRID = "hybrid"


@dataclass
class MemoryConfig:
    backend_type: BackendType = BackendType.TFIDF
    compression: bool = True
    temporal_decay: bool = True
    max_context_tokens: int = 4000
    decay_half_life_hours: float = 168  # 1 semaine


class MemoryFacade:
    """Point d'entrée unique pour toutes les opérations mémoire.
    
    Remplace l'usage direct de project_memory, success_memory, etc.
    par une interface unifiée.
    """
    
    def __init__(self, config: MemoryConfig = MemoryConfig()):
        self.config = config
        self.backend = self._create_backend(config.backend_type)
        self.compressor = ContextCompressor() if config.compression else None
        self.decay = DecayScorer() if config.temporal_decay else None
    
    def _create_backend(self, backend_type: BackendType) -> MemoryBackend:
        factories = {
            BackendType.TFIDF: lambda: TFIDFBackend(),
            BackendType.HYBRID: lambda: HybridBackend(),
        }
        factory = factories.get(backend_type)
        if not factory:
            raise ValueError(f"Backend {backend_type} non disponible")
        return factory()
    
    async def store(self, content: str, metadata: Optional[Dict] = None) -> str:
        """Stocke un souvenir."""
        if self.compressor:
            content = await self.compressor.compress(content)
        return await self.backend.store(content, metadata or {})
    
    async def recall(self, query: str, k: int = 5,
                     namespace: Optional[str] = None) -> List[Dict[str, Any]]:
        """Rappelle les souvenirs pertinents."""
        results = await self.backend.search(query, k=k * 2)
        if self.decay:
            results = self.decay.rerank(results)
        return results[:k]
    
    async def get_context(self, query: str,
                           max_tokens: Optional[int] = None) -> str:
        """Retourne un contexte formaté pour injection dans un prompt."""
        max_t = max_tokens or self.config.max_context_tokens
        results = await self.recall(query, k=10)
        
        context_parts = []
        token_count = 0
        for r in results:
            text = r.get("content", "")
            tokens = len(text) // 4  # estimation
            if token_count + tokens > max_t:
                break
            context_parts.append(text)
            token_count += tokens
        
        return "\n---\n".join(context_parts)
```

#### Étape 4 : Migration progressive

Le `coordinator.py` et `service.py` existants peuvent être modifiés pour utiliser `MemoryFacade` en interne, sans casser les API publiques.

### Fichiers impactés

| Fichier | Action |
|---------|--------|
| `core/memory/facade.py` | **Créer** |
| `core/memory/coordinator.py` | **Modifier** (utiliser facade en interne) |
| `core/memory/service.py` | **Modifier** (déléguer à facade) |
| `core/memory/*.py` (modules morts) | **Supprimer** après audit d'imports |
| `core/memory/__init__.py` | Exporter MemoryFacade |
| `tests/test_memory_facade.py` | **Créer** |

### Critère de succès

- [ ] `MemoryFacade` fournit store/recall/get_context
- [ ] Modules non importés supprimés
- [ ] `pytest tests/ -k memory -v` : 0 régression
- [ ] Nombre de fichiers dans `core/memory/` réduit d'au moins 30%

---

## 7. P2.3 — Nettoyage du code mort

### Inventaire du code mort identifié

| Élément | Justification | Action |
|---------|--------------|--------|
| `rust/nexus_core/` | Squelette Cargo.toml + lib.rs vide, non compilé, non importé | **Supprimer** le dossier |
| `core/drivers/legacy/` | Drivers Claude/Gemini obsolètes remplacés par SDK drivers | **Supprimer** (après P1.2) |
| `core/native/_fallback.py` | Fallback pour bridge Rust inexistant | **Supprimer** si Rust supprimé |
| `core/native/__init__.py` | Package contenant uniquement le fallback | **Supprimer** si fallback supprimé |
| `todo.md`, `todo2.md`, `todo3.md`, `todo4.md`, `todomig.md` | 5 fichiers TODO fragmentés | **Consolider** en un seul `TODO.md` |
| `prompt.txt` | Prompt Gemini temporaire (tracé dans git status comme untracked) | **Ajouter au .gitignore** ou supprimer |
| `test_run_output.txt` | Output de test temporaire (untracked) | **Ajouter au .gitignore** |

### Plan d'action

```bash
# Ordre d'exécution (séquentiel, chaque step est un commit)

# Step 1 : Supprimer Rust (0 dépendance)
rm -rf rust/
git add -A && git commit -m "chore: remove unused Rust skeleton (nexus_core)"

# Step 2 : Supprimer core/native/ (après vérification)
grep -rn "core.native\|from core import native" core/ tests/ --include="*.py"
# Si 0 résultat :
rm -rf core/native/
git add -A && git commit -m "chore: remove unused native bridge fallback"

# Step 3 : Consolider les TODOs
cat todo.md todo2.md todo3.md todo4.md todomig.md > TODO.md
rm todo.md todo2.md todo3.md todo4.md todomig.md
git add -A && git commit -m "chore: consolidate 5 TODO files into one"

# Step 4 : Nettoyer .gitignore
echo -e "\n# Temporary files\nprompt.txt\ntest_run_output.txt\nrepomix-output.*" >> .gitignore
git add .gitignore && git commit -m "chore: add temporary files to .gitignore"

# Step 5 : Vérification
pytest tests/ -x --tb=short
python -c "import core; print('Import OK')"
```

### Fichiers impactés

| Action | Fichiers |
|--------|----------|
| **Supprimer** | `rust/nexus_core/Cargo.toml`, `rust/nexus_core/src/lib.rs` |
| **Supprimer** | `core/native/_fallback.py`, `core/native/__init__.py` |
| **Supprimer** | `todo.md`, `todo2.md`, `todo3.md`, `todo4.md`, `todomig.md` |
| **Créer** | `TODO.md` (consolidé) |
| **Modifier** | `.gitignore` |

### Critère de succès

- [ ] `rust/` n'existe plus
- [ ] `core/native/` n'existe plus (si non importé)
- [ ] 1 seul fichier TODO
- [ ] `python -c "import core"` : pas d'erreur
- [ ] `pytest tests/ -x` : 0 régression

---

## 8. P2.4 — Réduction de la surface documentaire

### Diagnostic

~80 fichiers markdown répartis entre :
- `docs/` : ~60 fichiers (guides, audits, sessions, architecture, commercialisation)
- Racine : `AGENTS.md`, `ARCHITECTURE_MAP.md`, `CHANGELOG.md`, `CLAUDE.md`, `GEMINI.md`, `INVARIANTS.md`, `MISSION.md`, `README.md`, `ROADMAP.md`
- `memory-bank/` : 7 fichiers (contexte projet pour AI coding assistants)
- `PRODUCTS/` : 12 fichiers (planification produit)

### Problèmes identifiés

1. **Docs de session datées** : `docs/sessions/SESSION_*.md`, `docs/SESSION_2026-02-17_*.md` — ce sont des logs de travail, pas de la documentation. Ils polluent la navigation.

2. **Audits multiples non consolidés** : `docs/AUDIT_REPORT.md`, `docs/AUDIT_2026-02-17.md`, `docs/NEXUS_ARCHITECTURE_AUDIT_V12.md`, `docs/meta_analysis_v12.4.1.md`, `docs/minimax_audit/` — 5+ documents d'audit qui se chevauchent.

3. **Double maintenance README** : `docs/ARCHITECTURE_MAP.md` vs `ARCHITECTURE_MAP.md` à la racine.

### Plan d'action

```bash
# Step 1 : Archiver les logs de session
mkdir -p docs/archive/sessions
mv docs/sessions/SESSION_*.md docs/archive/sessions/
mv docs/SESSION_2026-02-17_*.md docs/archive/sessions/
git add -A && git commit -m "docs: archive session logs"

# Step 2 : Consolider les audits
mkdir -p docs/archive/audits
mv docs/AUDIT_REPORT.md docs/archive/audits/
mv docs/NEXUS_ARCHITECTURE_AUDIT_V12.md docs/archive/audits/
mv docs/meta_analysis_v12.4.1.md docs/archive/audits/
# Garder docs/AUDIT_2026-02-17.md comme audit de référence actuel
git add -A && git commit -m "docs: archive superseded audit reports"

# Step 3 : Résoudre les doublons
# Comparer les deux ARCHITECTURE_MAP
diff ARCHITECTURE_MAP.md docs/ARCHITECTURE_MAP.md
# Garder celui de la racine (plus visible), supprimer le doublon docs/
rm docs/ARCHITECTURE_MAP.md
git add -A && git commit -m "docs: remove duplicate ARCHITECTURE_MAP"

# Step 4 : Index de documentation
# Mettre à jour docs/INDEX.md pour refléter la structure nettoyée
```

### Structure documentaire cible

```
docs/
├── INDEX.md                           # Index maître
├── guides/
│   ├── ARCHITECTURE_OVERVIEW.md       # Pour les nouveaux contributeurs
│   ├── INSTALLATION.md
│   ├── SECURITY_MODEL.md
│   └── TROUBLESHOOTING.md
├── architecture/
│   ├── CLASS_DIAGRAMS.md
│   ├── DEPENDENCY_GRAPH.md
│   ├── GLOBAL_ARCHITECTURE.md
│   └── WORKFLOWS_MAP.md
├── api/
│   └── API_REFERENCE.md
├── AUDIT_2026-02-17.md                # Audit de référence actuel
├── KNOWN_ISSUES.md
├── CHANGELOG.md
├── commercialisation/                 # Business docs
├── archive/                           # Tout le reste
│   ├── sessions/
│   ├── audits/
│   └── legacy/
└── research/
```

### Critère de succès

- [ ] `docs/` contient < 30 fichiers actifs (hors archive/)
- [ ] 0 doublon entre racine et `docs/`
- [ ] `docs/INDEX.md` à jour
- [ ] Logs de session archivés

---

## 9. P2.5 — Consolidation des packages core/

### Diagnostic

37 packages dans `core/`. Plusieurs sont fonctionnellement proches et pourraient être fusionnés :

| Groupe fonctionnel | Packages actuels | Package cible |
|-------------------|-----------------|---------------|
| Orchestration | `orchestration/`, `orchestration_v7.py`, `routing/`, `execution/` | `core/orchestration/` |
| Intelligence | `reasoning/`, `hive_mind/`, `swarm/` | Garder séparés (cohésion forte) |
| Mémoire | `memory/`, `synapse/` | `core/memory/` |
| Observabilité | `telemetry/`, `logging/`, `audit/`, `events/` | `core/observability/` |
| Sécurité | `security/`, `governance/` | `core/security/` |
| Interface | `interface/`, `interaction/`, `ui/` | `core/interface/` |
| Infra | `resilience/`, `async_primitives/`, `utils/`, `native/` | `core/infra/` |

### Plan d'action

**ATTENTION** : Ce chantier est le plus risqué. Il ne doit être exécuté qu'APRÈS les Sprints 1 et 2, quand la base est stabilisée.

#### Fusions recommandées (faible risque)

**Fusion 1** : `synapse/` → `memory/`

```bash
# synapse/ contient des protocoles de message et de mémoire
# Vérifier les frontières
grep -rn "from core.synapse" core/ tests/ --include="*.py" | wc -l
# Si < 20 imports → migration gérable

# Déplacer les fichiers
mv core/synapse/*.py core/memory/synapse/
# Mettre à jour tous les imports
find core/ tests/ -name "*.py" -exec sed -i 's/from core\.synapse/from core.memory.synapse/g' {} +
```

**Fusion 2** : `audit/` + `events/` → `observability/`

```bash
mkdir -p core/observability
mv core/audit/*.py core/observability/audit/
mv core/events/*.py core/observability/events/
mv core/telemetry/*.py core/observability/telemetry/
mv core/logging/*.py core/observability/logging/
```

**Fusion 3** : `interaction/` → `interface/`

```bash
# interaction/ et interface/ ont des rôles proches
mv core/interaction/*.py core/interface/interaction/
```

#### Ce qu'il ne faut PAS fusionner

- `hive_mind/` et `swarm/` : cohésion forte, responsabilités distinctes (stratégie vs tactique)
- `reasoning/` : domaine autonome, ne dépend que des drivers
- `memory/` et `reasoning/` : couplage faible, garder séparés

### Impact estimé

| Métrique | Avant | Après |
|----------|-------|-------|
| Packages dans core/ | 37 | ~25 |
| Imports à modifier | - | ~100-200 |
| Risque régression | - | Moyen |

### Critère de succès

- [ ] `core/` contient ≤ 25 packages
- [ ] 0 import cassé
- [ ] `pytest tests/ -x` : 0 régression
- [ ] Chaque package restant a ≥ 3 fichiers (pas de packages d'un seul fichier)

---

## 10. P2.6 — Optimisation du fast path

### Diagnostic

Le fast path (bypass de HiveMind pour les tâches simples) existe mais son déclenchement n'est pas documenté. Pour les commandes triviales, traverser le pipeline complet (Guard → FSM → Context → Router → HiveMind 7 phases → Swarm → Driver → Monitor → Guard) est un overhead de latence perceptible.

### Plan d'action

#### Étape 1 : Documenter le fast path existant

```bash
# Trouver la logique de fast path
grep -rn "fast.path\|fast_path\|FastPath\|direct.*route\|simple.*task" core/orchestration* core/routing/ --include="*.py"
```

#### Étape 2 : Renforcer le fast path

```python
# core/routing/fast_path.py — NOUVEAU ou ENRICHI

from typing import Optional
from core.reasoning.task_complexity import estimate_complexity, TaskComplexity


class FastPathDecider:
    """Décide si une requête peut bypasser le pipeline HiveMind."""
    
    # Commandes slash → toujours fast path
    SLASH_COMMANDS = {"/help", "/status", "/agents", "/quit", "/exit",
                      "/memory", "/workspace", "/model", "/budget",
                      "/health", "/swarm", "/evolution"}
    
    def should_fast_path(self, user_input: str) -> bool:
        """Retourne True si la requête ne nécessite pas HiveMind."""
        stripped = user_input.strip()
        
        # Commandes slash
        if any(stripped.lower().startswith(cmd) for cmd in self.SLASH_COMMANDS):
            return True
        
        # Estimation de complexité
        complexity = estimate_complexity(stripped)
        if complexity <= TaskComplexity.SIMPLE:
            return True
        
        return False
    
    def get_fast_path_driver(self, user_input: str) -> Optional[str]:
        """Retourne le driver à utiliser pour le fast path, ou None."""
        if not self.should_fast_path(user_input):
            return None
        # Pour les commandes simples, utiliser le driver principal
        return "primary"
```

#### Étape 3 : Intégrer dans l'orchestrateur

```python
# Dans OrchestratorV7 (ou son successeur TaskRouter)
async def process_turn(self, user_input: str) -> TurnResult:
    self.guards.check_input(user_input)
    
    # Fast path check
    if self.fast_path.should_fast_path(user_input):
        result = await self._execute_fast(user_input)
    else:
        state = self.fsm.transition(user_input)
        ctx = await self.ctx_builder.build(user_input, state)
        route = self.router.route(user_input, state, ctx)
        result = await self.executor.execute(route, ctx)
    
    return self.guards.check_output(result)
```

### Fichiers impactés

| Fichier | Action |
|---------|--------|
| `core/routing/fast_path.py` | **Créer** ou enrichir |
| `core/orchestration_v7.py` | **Modifier** (intégrer fast path en amont) |
| `core/reasoning/task_complexity.py` | Réutilisé (créé en P2.1) |
| `tests/test_fast_path.py` | **Enrichir** |

### Critère de succès

- [ ] Commandes slash : 0 appel à HiveMind
- [ ] Requêtes < 30 chars sans marqueurs complexes : fast path
- [ ] Latence REPL pour commandes simples < 500ms (hors réseau)
- [ ] `pytest tests/ -x` : 0 régression

---

## 11. Matrice de risque et dépendances

### Dépendances entre chantiers

```
P2.3 (Code mort)  ──┐
P2.4 (Docs)       ──┤── Sprint 1 (indépendants)
P1.3 (Rate limiters)┤
P1.2 (Duplications)─┘
                     │
                     ▼
P1.1 (Orchestrator) ─┬── Sprint 2 (dépend du nettoyage Sprint 1)
P2.1 (Métacognition) ┤
P2.6 (Fast path)   ──┘
       │                  
       │ P2.1 crée task_complexity.py utilisé par P2.6
       │ P1.1 restructure l'orchestrateur où P2.6 s'intègre
       │
       ▼
P2.2 (Mémoire) ──────┬── Sprint 3 (dépend de P1.2 pour les doublons mémoire)
P2.5 (Packages)  ─────┘
       │
       │ P2.5 ne peut se faire qu'après stabilisation complète
```

### Matrice de risque

| Chantier | Risque régression | Risque perf | Risque fonctionnel | Mitigation |
|----------|-------------------|-------------|-------------------|------------|
| P1.1 | 🔴 Élevé | 🟡 Moyen | 🔴 Élevé | Extraction progressive, tests à chaque step |
| P1.2 | 🟡 Moyen | 🟢 Nul | 🟡 Moyen | Grep exhaustif des imports avant suppression |
| P1.3 | 🟢 Faible | 🟢 Nul | 🟢 Faible | Re-exports deprecated pour compatibilité |
| P2.1 | 🟢 Faible | 🟢 Positif | 🟢 Faible | Bypass conditionnel, pas de changement de logique |
| P2.2 | 🟡 Moyen | 🟡 Moyen | 🟡 Moyen | Façade en surcouche, pas de remplacement direct |
| P2.3 | 🟢 Nul | 🟢 Nul | 🟢 Nul | Vérification d'imports avant chaque suppression |
| P2.4 | 🟢 Nul | 🟢 Nul | 🟢 Nul | Archivage, pas de suppression |
| P2.5 | 🔴 Élevé | 🟢 Nul | 🟡 Moyen | À faire en dernier, imports sed/replace |
| P2.6 | 🟢 Faible | 🟢 Positif | 🟢 Faible | Ajout conditionnel, pas de changement existant |

---

## 12. Calendrier d'exécution recommandé

### Sprint 1 — Nettoyage (3-5 jours)

| Jour | Chantier | Livrables |
|------|----------|-----------|
| J1 | P2.3 Code mort | `rust/` supprimé, TODOs consolidés, .gitignore nettoyé |
| J1 | P2.4 Docs | Sessions archivées, doublons résolus, INDEX.md à jour |
| J2-J3 | P1.2 Duplications | Legacy supprimés, V2 en place, imports migrés |
| J3 | P1.3 Rate limiters | UnifiedRateLimiter en place, 3 re-exports deprecated |
| J4-J5 | Tests + stabilisation | `pytest tests/ -x` : 0 fail, revue des imports |

**Commit de checkpoint Sprint 1** : tag `NX-CG-sprint1-clean`

### Sprint 2 — Refactoring structurel (5-8 jours)

| Jour | Chantier | Livrables |
|------|----------|-----------|
| J1 | P2.1 Métacognition | `task_complexity.py` créé, monitoring conditionnel actif |
| J2 | P2.6 Fast path | FastPathDecider intégré, commandes slash bypassent HiveMind |
| J3-J7 | P1.1 OrchestratorV7 | GuardPipeline extrait (J3), TaskRouter extrait (J4), StateHandler extrait (J5-J6), TaskExecutor extrait (J7) |
| J8 | Tests + stabilisation | Non-régression complète |

**Commit de checkpoint Sprint 2** : tag `NX-CG-sprint2-refactor`

### Sprint 3 — Consolidation profonde (5-7 jours)

| Jour | Chantier | Livrables |
|------|----------|-----------|
| J1-J2 | P2.2 Mémoire | Audit d'imports, MemoryFacade créée, modules morts supprimés |
| J3-J5 | P2.5 Packages | Fusion synapse→memory, audit+events→observability, interaction→interface |
| J6-J7 | Tests + stabilisation + docs | Non-régression, ARCHITECTURE_MAP.md mis à jour |

**Commit de checkpoint Sprint 3** : tag `NX-CG-sprint3-consolidated`

---

## 13. Critères de validation

### Validation continue (à chaque commit)

```bash
# Script de validation à exécuter avant chaque commit
#!/bin/bash
set -e

echo "=== Import check ==="
python -c "import core; print('Core import OK')"

echo "=== Tests rapides ==="
pytest tests/ -x --tb=short -q

echo "=== Pas de deprecated oublié ==="
deprecated_count=$(grep -r "DEPRECATED" core/ --include="*.py" | grep -v __pycache__ | wc -l)
echo "Deprecated markers: $deprecated_count"

echo "=== Structure check ==="
echo "Packages dans core/: $(find core/ -maxdepth 1 -type d | wc -l)"
echo "Fichiers dans core/memory/: $(find core/memory/ -name '*.py' | wc -l)"
echo "Lignes orchestration_v7.py: $(wc -l < core/orchestration_v7.py)"
```

### Métriques cibles finales

| Métrique | Avant | Cible Sprint 1 | Cible Sprint 2 | Cible Sprint 3 |
|----------|-------|----------------|----------------|----------------|
| Fichiers source total | 953 | 940 | 944 (+4 nouveaux) | 910 |
| Packages dans core/ | 37 | 36 (-native/) | 36 | ~25 |
| Lignes orchestration_v7.py | 1224 | 1224 | ~100 | ~100 |
| Rate limiters distincts | 4 | 1 (+3 deprecated) | 1 | 1 |
| Doublons legacy/V2 | 6 | 0 | 0 | 0 |
| Fichiers TODO | 5 | 1 | 1 | 1 |
| Docs actifs (hors archive) | ~80 | ~50 | ~50 | ~40 |
| Tests passants | baseline | = baseline | = baseline | = baseline |

### Definition of Done par chantier

Chaque chantier est considéré **terminé** quand :

1. ✅ Le code est commité avec un message conventionnel (`feat:`, `refactor:`, `chore:`)
2. ✅ `pytest tests/ -x` passe sans régression
3. ✅ `python -c "import core"` ne lève pas d'erreur
4. ✅ Les fichiers supprimés ne sont plus référencés nulle part
5. ✅ Le CHANGELOG.md est mis à jour
6. ✅ Les critères de succès spécifiques au chantier (listés dans chaque section) sont tous cochés

---

*Plan généré par Claude Opus 4.6 — basé sur l'audit `nexus-audit-nxcg.md` du 17/02/2026*
