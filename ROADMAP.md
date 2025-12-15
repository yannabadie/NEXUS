# NEXUS V11 "ASYNC CORE" - Roadmap Opérationnelle

**Version**: 11.4.0 | **Status**: Active | **Last Updated**: 2025-12-15
**Maintainer**: Yann Abadie | **Branch**: NX
**Focus**: Security Hardening, Async Migration, Python 3.12+ Compatibility

---

## État Actuel (V11.4)

| Métrique | Valeur |
|----------|--------|
| Architecture | Modulaire (Handlers) + Async Core |
| Sécurité | JWT/CORS Hardening (V11.3) |
| Async | Python 3.12+ Compatible (V11.4) |
| Tests | 2,144+ (216 async tests) |

### V11.4 - ASYNC Migration ✅ COMPLETED (2025-12-15)

**Objectif**: Compatibilité Python 3.12+ et préservation du contexte async.

| Tâche | Status | Notes |
|-------|--------|-------|
| **fsm_handlers.py** | ✅ Done | `run_coroutine_threadsafe()` préserve CancellationToken |
| **telemetry/service.py** | ✅ Done | Pattern async/sync corrigé |
| **bootstrap/service.py** | ✅ Done | Pattern async/sync corrigé |
| **repl.py** | ✅ Done | 4x `get_running_loop()` (deprecated fix) |
| **async_adapter.py** | ✅ Done | Pattern simplifié |
| **embedding_engine.py** | ✅ Done | `get_running_loop()` |

### V11.3 - HARDENING Phase 0 ✅ COMPLETED (2025-12-15)

**Objectif**: Sécuriser les secrets et la configuration CORS.

| Tâche | Status | Notes |
|-------|--------|-------|
| **JWT_SECRET** | ✅ Done | Via `NEXUS_JWT_SECRET` env var |
| **CORS Origins** | ✅ Done | Via `NEXUS_CORS_ORIGINS` env var |
| **.env.example** | ✅ Done | Section sécurité documentée |
| **Tests** | ✅ Done | 8 tests dans `tests/v11/test_hardening.py` |

---

## État Précédent (V9.6 Sprint 5.3)

| Métrique | Valeur |
|----------|--------|
| Architecture | Modulaire (Handlers) |
| Résilience | SystemHealth + ContextScope |
| Swarm | Dictator Mode + SwarmTool |
| Connectivité | MCP Server (Client & Server) |
| Tests | 1,200+ |

### V9.6 - Refactoring & Resilience ✅ COMPLETED (2025-12-13)

**Objectif**: Sortir de la dette technique du "God Object" ToolManager et durcir la résilience.

| Tâche | Status | Notes |
|-------|--------|-------|
| **Modular Tool Handlers** | ✅ Done | `core/execution/handlers/` (Bash, File, Git, etc.) |
| **SystemHealth** | ✅ Done | Monitoring unifié (`core/resilience/`) |
| **ContextScope** | ✅ Done | Isolation des contextes d'exécution |
| **Swarm Dictator Mode** | ✅ Done | Forçage de mode via HiveMind |
| **Swarm as Tool** | ✅ Done | Invocation récursive contrôlée (`swarm_delegate`) |
| **MCP Server** | ✅ Done | `core/mcp/server.py` (FastMCP implementation) |

---

## Roadmap V9.7 - The Missing Links (Connectivité & Résilience)

**Objectif**: Transformer NEXUS d'un outil CLI isolé en une plateforme connectée et auto-réparatrice.

### V9.7.1 - Résilience Active (Hot-Swap Actuation) [P1]
*L'intelligence de détection existe, mais l'action manque.*

| Tâche | Status | Description |
|-------|--------|-------------|
| **Câblage Stagnation** | 📝 To Do | Connecter `StagnationDetector` aux `ModeExecutors` |
| **Hot-Swap Logic** | 📝 To Do | Implémenter l'échange de rôle Lead/Support en temps réel dans `lead_support_executor.py` |
| **Recovery Strategy** | 📝 To Do | Définir la stratégie de reprise après un swap (rollback contexte ?) |

### V9.7.2 - Maintenance Automatisée (Agent Reaper) [P2]
*Le workspace s'encrasse avec le temps.*

| Tâche | Status | Description |
|-------|--------|-------------|
| **Agent Reaper** | 📝 To Do | Garbage Collection des agents dans `workspace/agents/` |
| **Retention Policy** | 📝 To Do | Règles basées sur le score DyLAN et la date de dernière utilisation |
| **Archivage** | 📝 To Do | Compression/Archivage des agents "morts" avant suppression |

### V9.7.3 - API REST (FastAPI) [P2]
*Sortir du terminal pour permettre des interfaces Web.*

| Tâche | Status | Description |
|-------|--------|-------------|
| **FastAPI Wrapper** | 📝 To Do | Exposer `HybridSwarmEngine.process_task` via HTTP |
| **Webhooks** | 📝 To Do | Notifier des systèmes externes (CI/CD, Slack) |
| **Auth Middleware** | 📝 To Do | Sécurisation basique des endpoints |

---

## Roadmap V9.8 - Observabilité & Sécurité

### V9.8.1 - Observabilité Standardisée (OTLP) [P2]
*Remplacer les logs JSONL propriétaires par un standard industriel.*

| Tâche | Status | Description |
|-------|--------|-------------|
| **OTLP Exporter** | 📝 To Do | Implémenter un exportateur OpenTelemetry dans `core/telemetry/` |
| **Langfuse Integration** | 📝 To Do | Tracage distribué des chaînes de pensée (CoT) et coûts |
| **Distributed Tracing** | 📝 To Do | Visualisation "Waterfall" des interactions Swarm |

### V9.8.2 - Sécurité Enterprise (Sandboxing) [P3]
*Dépasser la sécurité "niveau Python".*

| Tâche | Status | Description |
|-------|--------|-------------|
| **Docker Sandbox** | 📝 To Do | Exécuter les outils Bash/Python dans des conteneurs éphémères |
| **Resource Limits** | 📝 To Do | Limites CPU/RAM strictes par agent |

---

## Vision V10 - Cognition Visionnaire (Long Terme)

### V10.1 - Graph of Thought (GoT)
*Dépasser la pensée linéaire.*
- Implémentation d'une structure de raisonnement en graphe pour les tâches EXPERT.
- Exploration parallèle de multiples branches de solution.

### V10.2 - Skill Crystallization (Auto-Spécialisation)
*L'apprentissage ultime.*
- **Concept**: Si une séquence d'outils réussit 3 fois, elle est compilée en un nouvel outil natif.
- **Auto-Spawn**: Création automatique d'agents spécialistes sans intervention humaine basée sur les succès répétés (`SuccessMemory`).

---

## Historique / Legacy (V8.x)

| Version | Feature | Status |
|---------|---------|--------|
| V8.0.1 | Hot-Swap Detection | ✅ Done |
| V8.0.3 | Ephemeral Sessions | ✅ Done |
| V8.1.6 | Thread-Safe Parallel | ✅ Done |
| V8.1.8 | Dynamic Spawn | ✅ Done |
| V8.3.0 | SwarmBridge | ✅ Done |
| V8.5.0 | Adaptive Fallback | ✅ Done |

---
*Généré par NEXUS PRIME - Synchronisation V9.6*