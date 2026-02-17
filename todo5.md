# 🧬 NEXUS-NX-CG : MASTER TOPOLOGY, AUDIT & EXECUTION DIRECTIVES
**Date Système** : 16 Février 2026 (Europe/Paris)
**Cible d'Exécution** : Claude Code 4.6 Opus (Agent d'Ingénierie & d'Orchestration)
**Classification** : AGI-OS (Artificial General Intelligence Operating System) / Distributed Cognitive Framework

## 1. VISION PRODUIT & ARCHITECTURE GLOBALE
NEXUS-NX-CG n'est pas un simple orchestrateur LLM. C'est un **Système d'Exploitation Cognitif** basé sur une architecture d'intelligence en essaim (Swarm), du raisonnement non-linéaire (Graph of Thought) et de l'auto-évolution darwinienne. 

Le système se décline actuellement en **3 produits exécutables** adossés à une stack d'opérations :
1. **Le Produit Principal (REPL "NEXUS7")** : `nexus7.py`. Démarre l'`OrchestratorV7` (FSM persistant) pour une session continue. Gère le workspace et les commandes en temps réel.
2. **Le "Flagship" (Research CLI)** : `nexus_research.py`. Ingère un repo en local via RAG et génère un "Evidence Pack" traçable (`report.md`, `sources.json`, `trace.jsonl`, `reasoning_graph.mmd`, `manifest.sha256`).
3. **Le "Companion" (Serveur MCP)** : `core/mcp/server.py`. Expose NEXUS en tant que serveur Model Context Protocol pour une intégration native dans les IDE (VSCode, Cursor) ou clients (Claude Desktop).
4. **La Stack Ops (Infrastructure)** : `docker-compose.yml` déploie un bus Redis (état/événements), le backend NEXUS (Headless) via FastAPI/Uvicorn, et le service CEREBRO (API WebSocket/REST sécurisée par JWT/Argon2).

---

## 2. CARTOGRAPHIE EXHAUSTIVE DES SOUS-SYSTÈMES (TOPOLOGIE)

### 2.1. Le Cerveau Central : FSM & OrchestratorV7 (`core/orchestration/`, `core/fsm/`)
* **Machine à États Finis (FSM)** : Boucle principale transitant par des états stricts (`IDLE`, `WAITING_USER`, `BRAINSTORMING`, `EXECUTING_TOOL`, `VALIDATING_CFL`, `ERROR`, `PANIC`).
* **Validation CFL (Cognitive Feedback Loop)** : Après l'utilisation d'un outil, le système boucle sur `VALIDATING_CFL` pour s'auto-évaluer avant de rendre la main ou de passer à l'étape suivante.
* **Mécanismes de Survie** : `stagnation_predictor.py` détecte les boucles infinies. `panic_system.py` force l'hibernation. L'état est persistant via *Event Sourcing* pour le crash-recovery.

### 2.2. L'Esprit de Ruche : Swarm Intelligence (`core/swarm/`, `core/hive_mind/`)
* **Topologies d'Exécution (`executors/`)** : Le `mode_selector.py` déploie des dynamiques de groupe :
  * *Parallel* (Map-Reduce cognitif).
  * *Ping-Pong* (Dialectique Thèse/Antithèse).
  * *Red/Blue* (Adversarial : Builder vs Hacker).
  * *Lead/Support* & *Specialist* (Hiérarchique).
* **Sagas & Négociation** : Les agents débattent (`adaptive_debate.py`) jusqu'au consensus (`consensus_tracker.py`). `saga_manager.py` permet des rollbacks (`compensation.py`) si un plan complexe échoue.

### 2.3. L'Hippocampe : Mémoire RAG Multi-Couches (`core/memory/`)
* **ProjectMemory (RAG "Local-First")** : 
  * *Chunking intelligent* : Par Abstract Syntax Tree (`class`/`def`) en Python ou `Headers` en Markdown.
  * *Ingestion* : Supporte `Docling` pour les PDF/DOCX/XLSX.
  * *Backends dégradables* : LanceDB (Dense) → BM25 → TF-IDF (via `hybrid.py`).
* **AutoMemory & Compression** : `context_compressor.py` résume l'historique pour préserver la fenêtre de contexte. `success_memory.py` trace les victoires pour le meta-apprentissage.

### 2.4. Le Cortex : Raisonnement & Évolution (`core/reasoning/`, `core/evolution/`)
* **Graph of Thought (GoT)** : `graph_of_thought.py` génère des arbres d'hypothèses. `thought_evaluator.py` élague les hallucinations.
* **Évolution Darwinienne** : Déclenchée après 50 "successful turns". `auto_specializer.py` mute le code source des agents. L'`agent_reaper.py` purge les faibles, `promote.py` sauvegarde les forts dans `lineage.json`.

### 2.5. Le Système Nerveux : Synapse & Asynchrone (`core/synapse/`, `core/async_primitives/`)
* **Protocole Synapse** : Routage ultra-rapide via `message_router.py` et `redis_bus.py`.
* **Noyau Rust** : `rust/nexus_core/` (En cours d'intégration) pour déporter la gestion asynchrone hors du GIL Python.

### 2.6. Immunité, Sécurité & Outils (`core/security/`, `core/execution/`)
* **Sécurité LLM-Native** : Implémentation OWASP LLM01:2025. `input_guard.py` bloque l'injection.
* **Red Team** : `red_team/validator.py` audite l'alignement éthique (`ethics.py`) des agents.
* **Handlers** : `bash_handler.py`, `sandbox_handler.py`, `dynamic_tools.py` (qui forge ses propres scripts).

---

## 3. SÉQUENCES D'EXÉCUTION (RUNTIME FLOWS)

### 3.1. Séquence REPL "Tâche Classique"
```mermaid
sequenceDiagram
  participant U as User
  participant R as REPL (InteractiveNexusV7)
  participant O as OrchestratorV7 (FSM)
  participant H as FSMHandlers
  participant L as LLM Driver (Gemini/Claude)
  participant T as ToolManager

  U->>R: message
  R->>O: process_turn(user_input)
  O->>O: KERNEL runtime check / input guard
  O->>H: handle_<state>()
  H->>L: invoke(context)
  L-->>H: structured message (action/status)
  alt action = TOOL_USE
    H->>T: execute(tool, args)
    T-->>H: tool_result
    H->>L: CFL validate(tool_result)
    L-->>H: continue/finish
  end
  H-->>O: result + next state
  O-->>R: {state, output, finished}
  R-->>U: streaming / display

  sequenceDiagram
  participant U as User/Caller
  participant C as nexus_research.py
  participant M as ProjectMemory
  participant FS as Filesystem

  U->>C: run_research(question, paths, backend)
  C->>M: ProjectMemory(root, backend)
  loop index paths
    C->>M: index_directory/index_file
    M->>FS: read files / chunk
  end
  C->>M: retrieve(question, limit, min_score)
  M-->>C: scored chunks
  C->>FS: write report.md + sources.json + trace.jsonl + graph.mmd + metrics.json
  C->>FS: write manifest.sha256
  C-->>U: output paths

  4. DETTE TECHNIQUE & VULNÉRABILITÉS CRITIQUES (À RÉSOUDRE)
Config Drift (Bloquant) : Le code revendique la version 12.4.0 "COGNITIVE BOOST", mais .env.example impose NEXUS_VERSION=8.3.1 et des flags obsolètes. Provoquera des crashs silencieux au déploiement.

Syndrome "Creator-Centric" (Bloquant OSS/B2B) : Le KERNEL.py et la configuration imposent des invariants d'obéissance ("Yann") et des emails hardcodés. Incompatible avec une distribution publique.

Absence de Packaging (UX Dégradée) : Lancement via des scripts Python isolés. Il manque un pip install standard et un "First-run wizard".

Infinite Token Burn (Coûts) : L'orchestration Swarm + FSM génère un volume massif de requêtes. Le Prompt Caching natif (Claude/Gemini) manque à l'appel, et le cache sémantique (response_cache.py) n'est pas utilisé pour court-circuiter l'API.

Sandboxing Exécutif Poreux (Sécurité) : sandbox_handler.py utilise des sous-processus locaux. L'exécution de code généré par l'IA nécessite une isolation physique réelle (MicroVMs).

Research CLI Inachevé (Produit) : L'Evidence Pack génère d'excellentes sources, mais le report.md ne fait que lister des notes. Il manque la phase de synthèse.

Dérive Génétique (Catastrophic Drift) : Sans validation humaine (HITL), l'évolution Darwinienne au runtime peut lobotomiser le système.

Le Goulet du GIL Python : Gérer la FSM, les verrous distribués et Redis en Python pur causera des interblocages sous forte charge.

5. PLAN D'ACTION D'INGÉNIERIE (PHASES D'EXÉCUTION)
@Claude Code 4.6 Opus : Ta mission est de transformer ce projet en un produit "Enterprise-Ready". Exécute ces chantiers séquentiellement. Vérifie chaque étape avant de passer à la suivante.

🟢 PHASE 1 : HYGIÈNE PRODUIT, CONFIG DRIFT & PACKAGING
Fix Drift Config : Aligne .env.example et les feature flags avec core/config.py (Version 12.4.0).

Agnosticisme du KERNEL : Supprime les invariants "Creator-centric" ("Yann") du KERNEL. Introduis un système de "Profil/Tenant" via les variables d'environnement (Mode Personal vs Mode Community/Enterprise).

Packaging Python : Scinde logiquement le projet dans pyproject.toml (nexus-core, nexus-products) pour permettre un pip install nexus-hivemind. Définis des points d'entrée CLI explicites (nexus-repl, nexus-research, nexus-mcp).

First-Run Wizard (Doctor) : Crée un module config_doctor.py appelé au démarrage pour vérifier les clés API, la présence de Redis, des drivers, et des dépendances (Docling, BM25).

🟡 PHASE 2 : FINALISATION DES PRODUITS (CLI, MCP, OBSERVABILITÉ)
Research CLI (--synthesize) : Modifie scripts/nexus_research.py. Ajoute un paramètre --synthesize. Le script doit prendre l'Evidence Pack généré, faire un appel LLM, et produire un rapport synthesis.md avec des citations inline pointant précisément vers sources.json.

Standardisation Evidence Pack : Étends cette fonctionnalité pour que toute exécution critique de tool-use ou de Swarm génère un mini-pack d'audit (trace.jsonl + manifest.sha256).

Stabilisation Serveur MCP : Dans core/mcp/server.py, verrouille et versionne les schémas d'outils (nexus_research, nexus_brainstorm). Gère la concurrence multi-clients selon la spec MCP officielle.

Observabilité OTel : Active core/telemetry/otel_provider.py. Connecte les endpoints FastAPI (CEREBRO) pour exposer l'état du FSM, l'agent actif, et /health.

🟠 PHASE 3 : OPTIMISATION DES COÛTS & CACHING
Prompt Caching API : Dans les SDK Drivers (claude_driver_hybrid.py, gemini_driver_v7.py), implémente l'utilisation explicite du Prompt Caching (Anthropic cache_control et Gemini context caching). Marque le System Prompt, le Tool Registry et les données figées de ProjectMemory comme cacheables.

Semantic Cache Local : Refactore core/drivers/response_cache.py en cache vectoriel. Si une étape du GoT/FSM est sémantiquement similaire à >95% à un appel passé, sers la réponse en cache sans appel réseau.

Kill Switch Budgétaire : Relie le core/telemetry/budget_tracker.py au core/fsm/panic_system.py. Force le model_router.py à replier toutes les tâches non-critiques vers le ollama_driver.py (Local/Gratuit) dès que 80% du quota de session est atteint.

🔴 PHASE 4 : HARD-SANDBOXING & GOUVERNANCE HITL
Isolation de l'Exécution : Réécris core/execution/handlers/sandbox_handler.py. L'exécution doit se faire dans des conteneurs éphémères (Docker DIND "Drop-and-Destroy" ou MicroVMs Firecracker). Applique strictement la sandbox_policy.py (réseau coupé, FS restreint).

Output Guard (DLP) : Étends core/security/output_guard.py pour scanner les sorties des outils et prévenir l'exfiltration de données avant le retour au LLM.

Gouvernance HITL de l'Évolution : Modifie core/evolution/manager.py. Gèle la promotion automatique des agents mutés. Introduis l'état PENDING_HITL_APPROVAL via core/interaction/hitl_persistence.py. Une mutation doit être validée manuellement (CLI/Cerebro) avant d'intégrer lineage.json.

🟣 PHASE 5 : KERNEL OFFLOADING (Performance Asynchrone)
Noyau Rust : Active rust/nexus_core/src/lib.rs.

Déportation : Déplace la logique asynchrone complexe (core/synapse/message_router.py, core/async_primitives/redis_bus.py, rwlock.py) vers Rust via tokio et redis-rs.

Bindings : Expose ces fonctions via PyO3/Maturin. Python ne doit plus servir qu'à orchestrer la FSM et gérer les appels LLM, supprimant le problème du GIL.

[FIN DU MANIFESTE. CLAUDE CODE, DÉBUTE IMMÉDIATEMENT LA PHASE 1 : FIX DU CONFIG DRIFT ET DU KERNEL.]