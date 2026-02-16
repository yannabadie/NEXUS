# 🪐 NEXUS-NX-CG : PLAN DIRECTEUR D'INDUSTRIALISATION ET DE REFACTORING

**Cible d'exécution :** Agent Claude Code 4.6 Opus (Rôle : Staff AI Software Engineer)
**Date du plan :** 15 Février 2026
**Contexte :** NEXUS-NX-CG est un Orchestrateur Multi-Agents (Swarm OS) avancé. L'architecture conceptuelle est brillante, mais l'implémentation actuelle souffre de couplages toxiques (CLIs locales), de failles de typage critiques dans le RAG, d'une sécurité noyau permissive, et d'un manque de fondations CI/CD. L'objectif est de transformer ce prototype en un système Cloud-Native, API-First, déterministe et sécurisé.

## 🚨 MÉTA-DIRECTIVES SYSTÈME (RÈGLES D'ENGAGEMENT)
1. **RECHERCHE WEB OBLIGATOIRE (`[WEB-RESEARCH-REQUIRED]`) :** L'écosystème IA évolue chaque semaine. À chaque apparition de ce tag, tu **DOIS** utiliser tes outils de recherche web (ex: `google:search` ou via terminal) pour consulter la documentation officielle et les papiers de recherche de **fin 2025 / début 2026** avant de modifier le code. Ne te fie pas uniquement à tes poids d'entraînement.
2. **Exécution Séquentielle & TDD :** Travaille **strictement Phase par Phase, Epic par Epic**. Tu ne passes à l'Epic suivant que lorsque les critères d'acceptation sont remplis et que les tests unitaires / E2E de l'Epic courant sont au vert. Fais un commit git clair après chaque Epic.
3. **Zéro Régression "Golden Path" :** Ne casse pas le workflow principal d'orchestration ni l'outil `nexus_research.py`. Maintiens les fonctionnalités existantes tout en changeant leurs fondations.

---

## 🏗️ PHASE 0 : FONDATIONS CLOUD-READY & INDUSTRIALISATION
*Objectif : Rendre le projet reproductible, testable et empêcher les régressions silencieuses avant tout refactoring métier.*

### Epic 0.1 : Package Management & Environnement
* **Action :** Initialise un fichier `pyproject.toml` moderne. Définis les dépendances strictes avec un lock file (via `uv` ou `poetry`) pour garantir la reproductibilité. Sépare les dépendances `[main]`, `[dev]`, et `[test]`.
* **Action :** Instaure une règle de Semantic Versioning. Fige la version du projet à **V12.4.0** (nettoie les mentions éparses à V8.3.1 ou V13.x dans les `.env` et le code).
* **Action :** Implémente un système de *Feature Flags* dans `core/config.py` (pour activer/désactiver le sandbox, le datamarking RAG, l'Hybrid backend de façon sécurisée).

### Epic 0.2 : Quality Gates & Pipeline CI
* **Action :** Crée un workflow `.github/workflows/ci.yml` contenant 3 jobs obligatoires et bloquants :
  1. `unit-tests` (pytest avec pytest-cov).
  2. `lint-type-check` (ruff, mypy/pyright en mode strict).
  3. `docker-build` (validation de la compilation d'une image de base).

### Epic 0.3 : Golden Path E2E Headless Minimal
* **Action :** Refactorise `core/interaction/headless_provider.py`. L'entrée `nexus --headless` doit être 100% déterministe : pas de TTY bloquant (désactivation de `prompt_toolkit`), et sortie JSON standardisée (`result.json`) avec *exit codes* POSIX stricts.
* **Action :** Crée un test E2E minimal qui fait booter le système sans outillage risqué pour valider l'intégrité de l'orchestrateur de base.

---

## 🧹 PHASE 1 : CONTRAT DE DONNÉES RAG, HYGIÈNE ET ROOT-OF-TRUST
*Objectif : Corriger les crashs latents liés aux modèles de données et blinder la sécurité du noyau.*

### Epic 1.1 : RAG Model Contract (Fix Critique Spotlighter & HybridBackend)
* **Problème :** `HybridBackend._compute_rrf_scores` utilise la dataclass `Chunk` comme clé de dictionnaire. Or, `Chunk` contient un `Set` mutable (non hachable), ce qui provoquera un crash au runtime. De plus, `Spotlighter` tente d'injecter `score` et `metadata` dans `Chunk` qui ne les possède pas.
* **Action :** Sépare strictement le modèle de données en deux :
  1. `Chunk` : Contenu indexé stable (immuable avec `@dataclass(frozen=True)`, identifié par `chunk_id: str`. Remplace `Set[str]` par `frozenset[str]`).
  2. `RetrievedChunk` (ou `ScoredChunk`) : Wrappe ou hérite de `Chunk`, et ajoute `score: float`, `metadata: dict`, `backend: str`.
* **Action :** Corrige `HybridBackend` pour utiliser `chunk.chunk_id` (string) comme clé de dictionnaire.
* **Action :** Modifie tous les backends pour retourner des `List[RetrievedChunk]` et corrige `Spotlighter` pour n'opérer que sur ces objets via `dataclasses.replace` (sans mutation in-place). 
* **Validation :** Ajoute des tests unitaires de hachabilité et de fusion Dense+Sparse.

### Epic 1.2 : Dette Python 3.14 et Hachage Sécurisé (Argon2id)
* **`[WEB-RESEARCH-REQUIRED]`** : Recherche "Python 3.14 deprecations ast.Str datetime.utcnow" et "argon2-cffi OWASP RFC 9106 2026".
* **Action :** Remplace globalement `datetime.utcnow()` (déprécié) par `datetime.now(timezone.utc)`.
* **Action :** Dans les parseurs d'AST (`core/evolution/mutation_parser.py`), remplace `ast.Str` par `ast.Constant`.
* **Action :** Supprime les bibliothèques obsolètes `passlib` et `crypt` (retiré en 3.13). Migre le hachage des mots de passe de `core/security/password.py` vers `argon2-cffi` en respectant les recommandations OWASP (ex: itérations >= 2, mémoire >= 19 MiB).

### Epic 1.3 : Sécurisation du Root-of-Trust (Fail-Closed)
* **Problème :** `verify_kernel_integrity()` recrée le hash s'il est absent. C'est un *Fail-Open* inacceptable en production.
* **Action :** Modifie le KERNEL. Si `KERNEL_HASH.txt` est absent, corrompu ou illisible, le système **DOIT** faire un `sys.exit(1)` immédiat et logguer une erreur critique (*Fail-Closed*).

---

## 🛡️ PHASE 2 : SANDBOXING OS-LEVEL (SÉCURITÉ CRITIQUE)
*Objectif : Isoler l'exécution de code malveillant sur l'hôte, pré-requis avant d'exposer l'API ou de "cloudifier" le système.*

### Epic 2.1 : Sandboxing Physique (Safe Default)
* **`[WEB-RESEARCH-REQUIRED]`** : Recherche "E2B SDK python 2026 code execution sandbox" ou "Docker SDK Python ephemeral isolated containers".
* **Action :** Le `bash_handler.py` exécuté sur l'hôte est un danger absolu. **Désactive-le par défaut** en production.
* **Action :** Déporte l'exécution des outils de code/shell vers des conteneurs éphémères isolés (E2B ou Docker). L'accès réseau de cette sandbox doit être coupé par défaut. L'orchestrateur NEXUS ne doit communiquer avec la sandbox que via RPC.

---

## 🔌 PHASE 3 : DÉCOUPLAGE DES CLIs ET STABILISATION API
*Objectif : Remplacer `subprocess.Popen` par des SDKs natifs pour permettre le streaming, les appels structurés et le déploiement SaaS.*

### Epic 3.1 : Contrats LLM Provider et SDKs Officiels
* **`[WEB-RESEARCH-REQUIRED]`** : Recherche "Anthropic Python SDK structured outputs strict prompt caching 2026" et "Google GenAI Python SDK 2026".
* **Action :** Définis une interface abstraite `LLMClient` (Streaming tokens, Streaming tool-calls, Structured Outputs en mode strict, Retries/Backoff avec classification d'erreurs).
* **Action :** Remplace les appels CLI par `AnthropicSDKDriver` (implémentant le *Prompt Caching* pour économiser du contexte) et `GoogleGenAIDriver`. Déplace les anciens drivers CLI vers `core/drivers/legacy/`.
* **Action :** Ajoute un "Capabilities Registry" pour que le routeur sache quel LLM supporte le caching, les images ou le JSON schema strict.

### Epic 3.2 : Provider Contract Tests & Réparation API CEREBRO
* **Action :** Écris des tests validant le respect du JSON Schema strict et le Function Calling, **sans appeler de vraies API** (utilise des mocks).
* **Action :** 17 tests API échouent dans `tests/v11/`. Répare le cycle de vie (`lifespan`) de FastAPI dans `core/api/cerebro/app.py`. Crée un *Test Profile* strict (bus in-memory, fake auth, fake drivers) pour que l'API soit 100% testable localement.

### Epic 3.3 : Observabilité OpenTelemetry (OTel GenAI)
* **`[WEB-RESEARCH-REQUIRED]`** : Recherche "OpenTelemetry Python Semantic Conventions for GenAI 2026".
* **Action :** Supprime les logs JSONL maison. Instrumente `core/telemetry/exporter.py` avec le SDK officiel OpenTelemetry.
* **Action :** Trace au minimum : Les appels LLM (latence, tokens in/out, erreurs), les transitions d'état FSM, et les exécutions dans la Sandbox (spans).

---

## 💾 PHASE 4 : EVENT SOURCING FSM ET TRIAGE SLM
*Objectif : Rendre le Swarm résilient aux crashs et optimiser les coûts cognitifs.*

### Epic 4.1 : Persistance d'État (FSM) via Event Sourcing
* **Problème :** Sauvegarder l'état écrasé dans Redis n'est pas fiable (non-idempotent, pas de "exactly-once").
* **Action :** Implémente un pattern d'*Event-Sourcing*. Chaque transition génère un `TransitionEvent` stocké en mode "Append-Only" dans Redis.
* **Action :** Implémente la logique de `replay` : au boot, `nexus7.py` doit pouvoir lire cet historique d'événements pour restaurer l'état exact (Resume) après un crash.

### Epic 4.2 : Policy-Driven Router et Triage SLM
* **`[WEB-RESEARCH-REQUIRED]`** : Recherche "vLLM OpenAI compatible server python client 2026" ou "Ollama Python client 2026".
* **Action :** Améliore le `ModelRouter` pour qu'il soit *Policy-Driven* (limites de budget €/jour, SLO de latence, politique de confidentialité).
* **Action :** Route les tâches classées `TRIVIAL` (vérification de syntaxe JSON, résumé de logs, diagnostic FSM) vers des SLMs locaux (ex: Llama-3 8B via un client compatible OpenAI/vLLM), réservant les modèles frontières pour l'orchestration stratégique.

---

## 🌐 PHASE 5 : INTEROPÉRABILITÉ (A2A/MCP) ET ÉVOLUTION DÉTERMINISTE
*Objectif : Insérer NEXUS dans l'écosystème global et ancrer son auto-amélioration de façon sûre.*

### Epic 5.1 : Frontières d'Interopérabilité (A2A vs MCP)
* **`[WEB-RESEARCH-REQUIRED]`** : Recherche "A2A Agent Protocol v0.3 Linux Foundation Python" et "MCP Model Context Protocol Python SDK 2026".
* **Règle Architecturale :** A2A = "Je suis un agent, parle-moi comme à un pair". MCP = "Je suis un serveur/client d'outils".
* **Action :** **NEXUS expose A2A (`Agent Server`) :** Implémente l'Agent Card A2A en well-known path pour permettre à d'autres agents de dialoguer avec le Swarm NEXUS (tasks, messages, SSE stream).
* **Action :** **NEXUS consomme MCP (`Tool Client`) :** Utilise le SDK Client MCP pour découvrir et consommer dynamiquement des serveurs d'outils externes (NE PAS confondre les deux usages).

### Epic 5.2 : Fitness Function Déterministe (Évolution)
* **Action :** Refactorise `core/evolution/promote.py`. Supprime l'évaluation LLM-as-a-judge (qui génère inévitablement du *Model Collapse* génétique). 
* **Action :** Une mutation de code (enfant) ne peut être promue que si elle passe une pipeline rigide et automatisée dans la Sandbox :
  1. Linter / Type-checker au vert (`mypy`, `ruff`).
  2. Scan de sécurité réussi (`bandit` / `semgrep`).
  3. L'exécution de la suite de tests `pytest` retourne un `exit code 0`.
  4. Respect d'un budget de performance (Temps d'exécution max des tests).

---
**[FIN DU PLAN DIRECTEUR]**

**INSTRUCTIONS POUR CLAUDE CODE 4.6 OPUS :**
1. **Accuse réception** de ce plan directeur.
2. **Confirme ta compréhension** de la nécessité absolue de la **Phase 0** avant de toucher au métier, du bug critique de hachabilité (`Chunk` mutable), et de l'impératif de sécurité "Fail-Closed" du KERNEL.
3. **Confirme** l'interdiction stricte de te fier uniquement à tes poids d'entraînement statiques et ton obligation d'exécuter les `[WEB-RESEARCH-REQUIRED]`.
4. **Confirme** ta compréhension des différences entre l'A2A (interop agents) et le MCP (interop outils).
5. **Démarre l'Epic 0.1**. À la fin de chaque Epic, génère un rapport des tests exécutés et attends de valider que la base de code est saine avant d'attaquer l'Epic suivant.