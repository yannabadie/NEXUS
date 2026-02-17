# 🪐 NEXUS-NX-CG (V12.4) : PLAN DIRECTEUR D'INDUSTRIALISATION ET D'OPTIMISATION DU HIVE MIND

**Cible d'exécution :** Agent Claude Code 4.6 Opus (Rôle : Staff AI Software Engineer)
**Date du plan :** 15 Février 2026
**Contexte :** NEXUS-NX-CG est un OS Agentique doté d'une architecture cognitive "Dual-System" : un **Hive Mind** (Système 2 : stratégique, délibératif en 7 phases) qui orchestre un **Swarm** (Système 1 : exécution tactique). L'objectif de ce plan est de stabiliser les fondations d'ingénierie (Cloud-Native, SDKs, Sandboxing), de corriger les failles critiques du RAG, et surtout d'optimiser le moteur cognitif (Hive Mind) pour garantir la résilience de la pensée (Sagas durables) et éviter l'explosion des coûts (Compression de contexte).

## 🚨 MÉTA-DIRECTIVES SYSTÈME (RÈGLES D'ENGAGEMENT)
1. **RECHERCHE WEB OBLIGATOIRE (`[WEB-RESEARCH-REQUIRED]`) :** L'écosystème IA évolue chaque semaine. À chaque apparition de ce tag, tu **DOIS** effectuer des recherches web sur la documentation officielle de **fin 2025 / début 2026** avant de coder.
2. **Exécution Séquentielle & TDD :** Travaille strictement Phase par Phase, Epic par Epic. Valide par des tests avant de passer à la suite.
3. **Intégrité du Hive Mind :** Les 7 phases de réflexion (`core/hive_mind/phases/`) ne doivent pas être aplaties. Leur structure conceptuelle est la force du projet. Tu dois optimiser la façon dont les données transitent entre elles.

---

## 🏗️ PHASE 0 : FONDATIONS CLOUD-READY & INDUSTRIALISATION
*Objectif : Mettre en place les "Quality Gates" pour éviter de refactoriser à l'aveugle.*

### Epic 0.1 : Package Management & Versioning
* **Action :** Initialise un `pyproject.toml` moderne avec un lock file (via `uv` ou `poetry`) pour garantir la reproductibilité.
* **Action :** Fige la version du projet à **V12.4.0** (nettoie les mentions à V8.3.1 ou V13.x dans les `.env` et le code).
* **Action :** Implémente un système de *Feature Flags* dans `core/config.py` (pour activer/désactiver le sandbox, le RAG hybride, ou la compression sémantique).

### Epic 0.2 : Quality Gates & "Golden Path" Headless
* **Action :** Crée un workflow CI `.github/workflows/ci.yml` avec 3 jobs bloquants : `unit-tests`, `lint-type-check` (ruff, mypy/pyright strict), et `docker-build`.
* **Action :** Refactorise `core/interaction/headless_provider.py`. L'entrée `--headless` doit être 100% déterministe (sans `prompt_toolkit`), avec une sortie `result.json` standardisée et un exit code strict (0 ou 1) pour l'intégration CI/CD.

---

## 🧠 PHASE 1 : OPTIMISATION COGNITIVE DU "HIVE MIND" ET SAGAS DURABLES
*Objectif : Sauver la mémoire, réduire les coûts de tokens et fiabiliser la délibération stratégique.*

### Epic 1.1 : Compression de Contexte Inter-Phases (Triage SLM)
* **`[WEB-RESEARCH-REQUIRED]`** : Recherche "LLM Context Compression techniques vLLM Ollama 2026".
* **Problème :** Le passage des phases d'analyse aux phases de débat et d'architecture accumule un historique brut gigantesque (Context Bloat).
* **Action :** Dans `core/hive_mind/context_manager.py`, implémente une "Compression d'État Sémantique". Avant de passer à la phase suivante, route l'historique vers un **SLM local** (ex: Llama-3/4 8B via API compatible OpenAI) pour en extraire une synthèse dense. Ne passe que cette synthèse aux modèles frontières (Claude/Gemini) de la phase suivante.

### Epic 1.2 : Structured Outputs et Éradication des Parseurs
* **`[WEB-RESEARCH-REQUIRED]`** : Recherche "Anthropic API structured outputs strict schema 2026" et "Google GenAI SDK structured outputs".
* **Action :** Supprime `core/hive_mind/json_parser.py`. 
* **Action :** Modifie les prompts et les appels aux modèles dans `core/hive_mind/phases/` pour exiger le mode **Structured Outputs** natif des APIs. Les contrats de sortie de chaque phase (ex: le plan de la `phase_architecture`) doivent être garantis mathématiquement par l'API du provider via un schéma Pydantic strict.

### Epic 1.3 : Sagas Durables et Transactions de Compensation
* **`[WEB-RESEARCH-REQUIRED]`** : Recherche "Python distributed Saga pattern event sourcing Redis 2026".
* **Problème :** Le `saga_manager.py` perd son état si le processus crash. De plus, il ne sait pas annuler les effets de bord physiques du Swarm.
* **Action (Durabilité) :** Câble le `saga_manager.py` sur `core/events/redis_bus.py`. Chaque transition de phase doit publier un événement immuable (`StateSnapshotEvent`) dans Redis (mode Append-Only). Au boot, `nexus7.py` doit pouvoir lire cet historique pour faire un *Resume* du Hive Mind.
* **Action (Compensation) :** Modifie le contrat des Tools d'écriture du Swarm. Chaque action destructrice doit générer un objet `CompensationAction` (le diff inverse). En cas d'échec (passage en `phase_diagnosis`), le `saga_manager` doit exécuter ces compensations pour rollback proprement l'environnement.

### Epic 1.4 : Persistance Stratégique
* **Action :** Connecte `strategy_blacklist.py` et `success_adapter.py` à la `ProjectMemory` (LanceDB). Les impasses et les succès découverts lors des phases 6 et 7 doivent être vectorisés pour que la phase 1 (`Analysis`) des futures sessions ne répète pas les mêmes erreurs.

---

## 🧹 PHASE 2 : CONTRAT RAG ET HYGIÈNE DU NOYAU
*Objectif : Corriger le bug critique de hachabilité en mémoire et blinder le Kernel.*

### Epic 2.1 : RAG Model Contract (Fix Critique "Spotlighter")
* **Problème :** `HybridBackend` utilise la dataclass `Chunk` (qui contient un `Set` mutable) comme clé de dict. Crash garanti. `Spotlighter` tente d'y injecter des attributs inexistants (`score`, `metadata`).
* **Action :** Sépare le modèle de données :
  1. `Chunk` : Immuable (`@dataclass(frozen=True)`), identifié par `chunk_id: str`. Remplace `Set[str]` par `frozenset[str]`.
  2. `RetrievedChunk` : Hérite de `Chunk` (ou wrappe), et ajoute `score: float`, `metadata: dict`.
* **Action :** Modifie `Spotlighter` et les backends pour n'utiliser que `RetrievedChunk`. Modifie `HybridBackend` pour utiliser `chunk_id` (string) comme clé de dictionnaire.

### Epic 2.2 : Dette Python 3.14 et Hachage Argon2id
* **`[WEB-RESEARCH-REQUIRED]`** : Recherche "Python 3.14 deprecations ast.Str datetime.utcnow" et "argon2-cffi OWASP RFC 9106 2026".
* **Action :** Remplace `datetime.utcnow()` par `datetime.now(timezone.utc)` et `ast.Str` par `ast.Constant` partout.
* **Action :** Supprime `passlib` et migre `core/security/password.py` vers `argon2-cffi` (standards OWASP).

### Epic 2.3 : Sécurisation du Root-of-Trust (Fail-Closed)
* **Action :** Modifie `verify_kernel_integrity()` dans `KERNEL.py`. Si `KERNEL_HASH.txt` est absent, le système **DOIT** faire un `sys.exit(1)` immédiat (*Fail-Closed*). Il ne doit plus jamais recréer le hash de lui-même.

---

## 🔌 PHASE 3 : SDKs NATIFS ET SANDBOXING OS-LEVEL
*Objectif : Remplacer les CLIs par des SDKs cloud-ready et sécuriser l'exécution de code du Swarm.*

### Epic 3.1 : Contrats LLM Provider (API-First & Prompt Caching)
* **`[WEB-RESEARCH-REQUIRED]`** : Recherche "Anthropic Python SDK Prompt Caching 2026".
* **Action :** Crée une interface abstraite `LLMClient` (Streaming SSE, Structured Outputs, Retries).
* **Action :** Implémente `AnthropicSDKDriver` et active absolument le **Prompt Caching** (vital pour réduire les coûts des instructions système massives du Hive Mind). Implémente `GoogleGenAIDriver`.
* **Action :** Déplace les anciens `claude_driver_hybrid.py` (basés sur `subprocess.Popen`) dans `core/drivers/legacy_cli/`.

### Epic 3.2 : Sandboxing Physique des Exécuteurs
* **`[WEB-RESEARCH-REQUIRED]`** : Recherche "E2B SDK python 2026 code execution sandbox".
* **Action :** Le `bash_handler.py` exécuté sur l'hôte est une vulnérabilité critique. **Désactive-le par défaut**.
* **Action :** Déporte l'exécution des outils shell/code du Swarm vers des conteneurs éphémères (E2B ou conteneurs Docker), isolés du réseau, interrogés via RPC.

---

## 🌐 PHASE 4 : INTEROPÉRABILITÉ (A2A/MCP) ET OBSERVABILITÉ
*Objectif : Standardiser la communication des agents et monitorer le Hive Mind.*

### Epic 4.1 : Frontières d'Interopérabilité (A2A vs MCP)
* **`[WEB-RESEARCH-REQUIRED]`** : Recherche "A2A Agent Protocol v0.3 Linux Foundation Python" et "MCP Client SDK Python 2026".
* **Règle :** A2A = Interopérabilité entre Agents. MCP = Interopérabilité avec des Outils.
* **Action :** NEXUS expose **A2A** : Implémente l'Agent Card A2A pour permettre à d'autres orchestrateurs de soumettre des tâches complexes au Hive Mind de NEXUS.
* **Action :** NEXUS consomme **MCP** : Finalise le client MCP dynamique (`core/mcp/client.py`) pour que le Swarm puisse découvrir dynamiquement des serveurs d'outils externes.

### Epic 4.2 : Fitness Function Déterministe (Évolution) ✅ DONE
* **✅ DONE:** Created `core/evolution/fitness.py` with `DeterministicFitness` class
* **✅ DONE:** Implemented 5 deterministic checks: Syntax (delegated), Linter (ruff), Type Check (mypy), Security (bandit), Tests (pytest)
* **✅ DONE:** Integrated into `TieredValidator` as Tier 1.5 quality checks
* **✅ DONE:** 25 comprehensive tests in `tests/test_evolution_fitness.py` (all passing)
* **Implementation:** DeterministicFitness replaces LLM-as-a-judge to prevent model collapse
* **Modes:** Strict (fail-fast) and Non-Strict (run all checks)
* **Graceful degradation:** If tools missing, validation continues but quality checks skipped

### Epic 4.3 : OpenTelemetry & Déploiement
* **`[WEB-RESEARCH-REQUIRED]`** : Recherche "OpenTelemetry Python Semantic Conventions GenAI 2026".
* **Action :** Câble `core/telemetry/exporter.py` sur le SDK officiel OTel. Trace en priorité les Spans temporels de chaque phase du Hive Mind.
* **Action :** Crée un `docker-compose.prod.yml` prêt pour la production incluant : NEXUS Backend (API Cerebro), CEREBRO Frontend (Vite), Redis, et un collecteur OTel.

---
**[FIN DU PLAN DIRECTEUR]**

**INSTRUCTIONS POUR CLAUDE CODE 4.6 OPUS :**
1. **Accuse réception** de ce plan directeur.
2. **Confirme ta compréhension** de l'architecture "Dual-System" de NEXUS (Hive Mind cognitif stratégique vs Swarm tactique).
3. **Confirme ta compréhension** de l'urgence de l'Epic 1.1 (Compression de Contexte Inter-Phases via SLM) pour éviter l'explosion de la fenêtre de contexte, et de l'Epic 1.3 (Sagas Durables et Compensation) pour la résilience.
4. **Confirme ta compréhension** du bug critique de hachabilité de la dataclass `Chunk` (Epic 2.1).
5. **Démarre la Phase 0 (Epic 0.1)**. Travaille Epic par Epic en mode TDD. Documente tes recherches Web pour les technos 2026 avant de commiter.