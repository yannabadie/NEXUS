# Plan de Remédiation V11 - Post-Analyse v3/v4

**Date:** 2025-12-15
**Statut:** PRÊT À EXÉCUTER
**Contexte:** Post-audit v3 (F1-F30) et v4 (F31-F33) vs V10 fixes
**Objectif:** Corriger les failles restantes avant déploiement CEREBRO UI

---

## Résumé Exécutif

### Statut Post-V10

| Catégorie | Total | Corrigées V10 | Restantes |
|-----------|-------|---------------|-----------|
| Raisonnement (F1-F17) | 17 | 14 | 3 |
| Sync/Async (F18-F23) | 6 | 3 | 3 |
| Isolation (F24-F30) | 7 | 0 | 7 |
| Architecture CLI (F31-F33) | 3 | 0 | 3 (long-term) |
| **TOTAL** | **33** | **17** | **16** |

### Failles DÉJÀ CORRIGÉES en V10

| ID | Description | Commit |
|----|-------------|--------|
| F1 | Task Analyzer - Context-aware classification | 023c2b7 |
| F2 | Fast Path - Input validation | 023c2b7 |
| F3 | Light CFL pour SIMPLE tasks | 023c2b7 |
| F4 | Parallel Executor - ConflictDetector | 023c2b7 |
| F6 | JSON Parsing - Smart quote replacement | 023c2b7 |
| F7 | Negotiation - Adaptive max_turns | 023c2b7 |
| F8 | CFL Validation - Default to False | 023c2b7 |
| F9 | Session Manager - Explicit logging | 023c2b7 |
| F10 | Checkpoint Recovery - LLM context | 023c2b7 |
| F11 | MisalignmentDetector + escalation | 023c2b7 |
| F12 | Context Window - CRITICAL truncation | 023c2b7 |
| F13 | Semantic alignment validation | 023c2b7 |
| F14 | Termination - INCOMPLETE status | 023c2b7 |
| F15 | Artifact verification (partial) | 023c2b7 |
| F18 | Nested Event Loops - Correct pattern | (already correct) |
| F21 | Driver Async Bridge - asyncio.to_thread | (already correct) |
| F23 | Blackboard - AsyncRWLock | (already correct) |

---

## Failles RESTANTES à Corriger

### CRITIQUE (Bloquant UI WebSocket)

#### F27: Path Injection dans session_id
**Fichier:** `core/session/home_isolator.py:96`
**Problème:** Pas de validation de session_id → path traversal possible (CWE-22)
```python
# AVANT (VULNERABLE)
isolated_home = self.homes_dir / session_id  # NO VALIDATION

# APRÈS
isolated_home = self.homes_dir / self._sanitize_session_id(session_id)
```
**Impact UI:** Vulnérabilité de sécurité si session_id vient d'input utilisateur
**Effort:** 0.5j

#### F16: Rate Limiter - Méthode acquire() manquante
**Fichier:** `core/api/rate_limiter.py`, `core/swarm/executors/base.py:356`
**Problème:** `base.py` appelle `rate_limiter.acquire()` qui n'existe pas
```python
# Bug: base.py:356 calls:
await rate_limiter.acquire(timeout=60.0)
# But APIRateLimiter only has: acquire_async(), acquire_sync()
```
**Impact UI:** RuntimeError en mode PARALLEL avec rate limiting
**Effort:** 1j (+ coordinated acquisition for parallel)

#### F20: Threading Lock dans Async
**Fichier:** `core/orchestration/sync_bridge.py:172, 362, 464`
**Problème:** `threading.RLock` utilisé dans méthodes async → bloque event loop
```python
# AVANT
self._lock = RLock()  # Threading lock
async def sync_checkpoint(self, ...):
    with self._lock:  # BLOCKING!

# APRÈS
self._async_lock = AsyncRWLock()
async def sync_checkpoint(self, ...):
    async with self._async_lock.write():  # NON-BLOCKING
```
**Impact UI:** Event loop bloqué si WebSocket et checkpoint concurrent
**Effort:** 1j

---

### HAUTE (Recommandé avant UI)

#### F17: Circuit Breaker Non Partagé
**Fichier:** `core/resilience/circuit_breaker.py:263-296`
**Problème:** Pas de circuit breaker hiérarchique/global
**Impact UI:** Cascade failure si problème réseau global
**Effort:** 1j

#### F26: Race Condition Creation/Cleanup
**Fichier:** `core/session/home_isolator.py:158-169`
**Problème:** Pas de reference counting, cleanup unsafe
**Impact UI:** Fichiers supprimés pendant utilisation
**Effort:** 1j

#### F25: Silent Fallback Sans Isolation
**Fichier:** `core/swarm/session_manager.py:421-449`
**Problème:** get_isolated_env() retourne None silencieusement
**Impact UI:** Contexte partagé sans warning
**Effort:** 0.5j

#### F5: Stagnation Detector
**Fichier:** `core/fsm/stagnation_detector.py`
**Problème:** Seuil 0.8 trop strict, pas de semantic progress
**Impact UI:** Brainstorming interrompu prématurément
**Effort:** 1j

---

### MOYENNE (Post-UI)

#### F19: Deprecated asyncio.get_event_loop()
**Fichiers:** 18+ fichiers
**Problème:** Deprecated en Python 3.10+
**Impact UI:** DeprecationWarnings, errors en Python 3.12+
**Effort:** 1j (migration progressive)

#### F22: Mixed Execute Patterns
**Fichier:** `core/swarm/executors/parallel_executor.py:241-262`
**Problème:** execute() sync deprecated mais existe encore
**Impact UI:** Confusion API
**Effort:** 0.5j

#### F24: Gemini CLI Hash Collision
**Fichier:** `core/session/home_isolator.py`
**Problème:** hash(CWD) collision possible
**Impact UI:** Session bleeding rare mais possible
**Effort:** 2j (investigation + fix)

#### F28: Environment Variables Non Propagées
**Fichier:** `core/session/home_isolator.py:76-131`
**Problème:** XDG/AppData vars non isolées
**Impact UI:** Config leakage sur Linux
**Effort:** 0.5j

#### F29: Disk Space Exhaustion
**Fichier:** `core/session/home_isolator.py`
**Problème:** Pas de quota/monitoring
**Impact UI:** Disk full en production longue
**Effort:** 1j

#### F30: Singleton Thread Safety
**Fichier:** `core/session/workspace_manager.py:368-396`
**Problème:** Legacy singleton sans lock
**Impact UI:** Race condition au startup
**Effort:** 0.5j

---

### ARCHITECTURALES (Long-terme)

| ID | Description | Impact | Effort |
|----|-------------|--------|--------|
| F31 | CLI-Bound Architecture | Performance non-optimale | 4-6 sem |
| F32 | Session CLI Coupling | Perte features si migration API | 2 sem |
| F33 | CLI Tools Dependency | Réimplémentation tools nécessaire | 3 sem |

**Recommandation:** Traiter après déploiement initial UI

---

## Angles Morts Spécifiques UI (CEREBRO)

Ces points ne sont pas dans les rapports v3/v4 mais critiques pour l'UI:

| ID | Risque | Fichier Cible | Priorité |
|----|--------|---------------|----------|
| UI-1 | WebSocket injection | api/websocket_handler.py | CRITIQUE |
| UI-2 | Tenant isolation WS | api/websocket_manager.py | CRITIQUE |
| UI-3 | Rate limiting WS | api/middleware/rate_limit.py | HAUTE |
| UI-4 | JWT mid-session expiry | api/auth/jwt_refresh.py | HAUTE |
| UI-5 | Event ordering | Frontend sequence_number | MOYENNE |
| UI-6 | Connection pooling | api/connection_manager.py | MOYENNE |

---

## Plan d'Exécution

### PHASE 1: CRITIQUE (Avant toute UI) - 3j

| Jour | Faille | Fichier | Action |
|------|--------|---------|--------|
| J1 | F27 | home_isolator.py | Sanitize session_id |
| J1 | F16 | rate_limiter.py, base.py | Fix acquire() + coordinated |
| J2 | F20 | sync_bridge.py | RLock → AsyncRWLock |
| J3 | Tests | - | Validation Phase 1 |

### PHASE 2: HAUTE (Avant release UI) - 4j

| Jour | Faille | Action |
|------|--------|--------|
| J4 | F17 | Hierarchical circuit breaker |
| J5 | F26, F25 | Reference counting + logging |
| J6 | F5 | Adaptive stagnation detector |
| J7 | Tests | Validation Phase 2 |

### PHASE 3: MOYENNE (Post-release) - 5j

| Jour | Faille | Action |
|------|--------|--------|
| J8 | F19 | Migration get_running_loop() |
| J9 | F22, F30 | Cleanup deprecated patterns |
| J10 | F24, F28 | Isolation improvements |
| J11 | F29 | Disk quota monitoring |
| J12 | Tests | Validation Phase 3 |

### PHASE 4: UI Integration - 5j

| Jour | Item | Action |
|------|------|--------|
| J13-14 | UI-1, UI-2 | WebSocket security |
| J15-16 | UI-3, UI-4 | Rate limiting + JWT |
| J17 | UI-5, UI-6 | Event ordering + pooling |

---

## Tests à Exécuter

```bash
# Après chaque phase
pytest tests/ -v --tb=short

# Tests spécifiques Phase 1
pytest tests/ -k "rate_limit or circuit or session or isolation" -v

# Tests spécifiques Phase 2
pytest tests/ -k "stagnation or cleanup or fallback" -v

# Régression complète
pytest tests/ -v --cov=core --cov-report=html
```

---

## Métriques de Succès

| Métrique | Objectif |
|----------|----------|
| Failles CRITIQUE | 0 restantes |
| Failles HAUTE | ≤ 2 restantes (architectural) |
| Tests coverage | ≥ 80% |
| No DeprecationWarnings | Python 3.11+ |
| WebSocket latency | < 100ms p95 |

---

## Sources

- [Multi-agent LLMs in 2025 - SuperAnnotate](https://www.superannotate.com/blog/multi-agent-llms)
- [Google Developers - Context-aware Multi-Agent Framework](https://developers.googleblog.com/architecting-efficient-context-aware-multi-agent-framework-for-production/)
- [Why Do Multi-Agent LLM Systems Fail? - arXiv](https://arxiv.org/html/2503.13657v1)
- [LangChain Blog - Multi-Agent Systems](https://blog.langchain.com/how-and-when-to-build-multi-agent-systems/)
- [ZenML - LLM Agents in Production](https://www.zenml.io/blog/llm-agents-in-production-architectures-challenges-and-best-practices)

---

*Document généré après analyse v3/v4 vs codebase actuelle post-V10*
