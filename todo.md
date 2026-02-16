# 🪐 NEXUS-NX-CG (V12.4) : PLAN DIRECTEUR DE REFACTORING ET D'INDUSTRIALISATION

**Cible d'exécution :** Agent Claude Code 4.6 Opus (Staff AI Software Engineer)
**Date du plan :** 15 Février 2026
**Contexte :** NEXUS-NX-CG est un Orchestrateur Multi-Agents (Swarm OS) avancé. Bien que l'architecture conceptuelle soit exceptionnelle (RAG hybride, FSM persistant, Saga Pattern, Auto-Évolution), l'implémentation actuelle souffre de couplages toxiques (CLIs locales), d'une volatilité d'état (RAM), de failles de sécurité (faux sandboxing) et de bugs de typage dans la mémoire. L'objectif est de transformer ce prototype en un système Cloud-Native, API-First, déterministe et sécurisé.

## 🚨 MÉTA-DIRECTIVES SYSTÈME (RÈGLES D'ENGAGEMENT)
1. **RECHERCHE WEB OBLIGATOIRE (`[WEB-RESEARCH-REQUIRED]`) :** L'écosystème IA évolue chaque semaine. À chaque apparition de ce tag, tu **DOIS** utiliser tes outils de recherche web (ex: `google:search` ou terminal) pour consulter la documentation officielle de **fin 2025 / début 2026** avant d'écrire du code. Ne te fie pas à tes poids d'entraînement statiques.
2. **Micro-Commits & Test-Driven Development (TDD) :** Tu as l'interdiction de tout refactoriser d'un coup. Travaille **Epic par Epic**. Pour chaque Epic, écris ou répare les tests d'abord. Fais un `git commit` clair après chaque Epic réussie.
3. **Immutabilité du KERNEL :** Le système de vérification cryptographique (`KERNEL.py`, `KERNEL_HASH.txt`, `runtime_integrity_check`) est inviolable. Si tu modifies le noyau pour des raisons de dette technique, tu dois mettre à jour le hash, mais ne désactive jamais la sécurité.
4. **Zéro Régression :** Ne supprime pas les fonctionnalités clés comme le `nexus_research.py` (Evidence Pack). Adapte-les aux nouvelles fondations.

---

## 🧹 PHASE 1 : HYGIÈNE DU REPO, FIX CRITIQUES ET DETTE TECHNIQUE
*Objectif : Éliminer les crashs silencieux, anticiper Python 3.14 et standardiser l'environnement.*

### Epic 1.1 : Fix Critique du RAG Hybride (Le Bug "Spotlighter")
* **Contexte :** Dans `core/memory/project_memory.py` (méthode `retrieve`), la branche "Spotlighter datamarking" tente d'assigner `chunk.score` et `chunk.metadata` à l'objet `Chunk`. Or, ces attributs n'existent pas dans la dataclass.
* **Action :** Étends la dataclass `Chunk` (dans `core/db/models.py` ou `core/memory/types.py`) pour inclure formellement `score: float | None = None` et `metadata: dict = field(default_factory=dict)`.
* **Action :** Modifie `core/memory/spotlighting.py` pour s'assurer que les objets modifiés le sont de manière immutable (via `dataclasses.replace`). Ajoute un test unitaire prouvant que l'HybridBackend fonctionne avec le Spotlighter activé.

### Epic 1.2 : Résolution de la Dette Technique (Python 3.12/3.14)
* **`[WEB-RESEARCH-REQUIRED]`** : Recherche "Python 3.14 deprecations datetime.utcnow ast.Str passlib crypt".
* **Action :** Remplace globalement toutes les occurrences de `datetime.utcnow()` par `datetime.now(timezone.utc)`.
* **Action :** Dans `core/evolution/mutation_parser.py` et autres parseurs d'AST, remplace `ast.Str` par `ast.Constant`.
* **Action :** Dans `core/security/password.py`, élimine `passlib` et `crypt`. Implémente le hachage de manière moderne via `bcrypt` ou `argon2-cffi`.

### Epic 1.3 : Unification du Versioning et Éradication des Hardcodes
* **Action :** Fige la version officielle à **V12.4.0 "Cognitive Boost"**. Mets à jour `pyproject.toml`, `core/config.py`, `.env.example` et l'UI CEREBRO pour supprimer les références à la V8.3.1.
* **Action :** Nettoie `workspace_registry.json`. Supprime les chemins absolus spécifiques à Windows (`C:\...`). Implémente une résolution dynamique via `pathlib.Path` relative à la racine du projet. Supprime les appels `os.system('')` liés à ANSI.

### Epic 1.4 : Réparation de l'API CEREBRO
* **Action :** 17 tests échouent dans `tests/v11/` (Cortex/Keymaker/RBAC). Diagnostique et répare le cycle de vie (`lifespan`) de l'application FastAPI dans `core/api/cerebro/app.py`. Sécurise l'isolation des clients HTTPX asynchrones et des mocks Redis/JWT pour éviter les erreurs de type `RuntimeError: Event loop is closed`.

---

## 🔌 PHASE 2 : DÉCOUPLAGE DES CLIs ET MIGRATION CLOUD-NATIVE
*Objectif : Remplacer `subprocess.Popen` par des SDKs natifs pour permettre le déploiement SaaS.*

### Epic 2.1 : Intégration des SDKs Python Officiels (API-First)
* **`[WEB-RESEARCH-REQUIRED]`** : Recherche "Anthropic Python SDK messages API structured outputs streaming 2026" et "Google GenAI Python SDK Gemini 3 Pro 2026".
* **Action :** Crée une interface propre `LLMClient` dans `core/drivers/protocol.py`.
* **Action :** Implémente `core/drivers/anthropic_sdk_driver.py` et `core/drivers/google_genai_sdk_driver.py`. Implémente le *Function Calling* natif et le *Streaming* (Server-Sent Events) pour communiquer de manière fluide avec l'UI Cerebro.
* **Action :** Gère les clés d'API de manière centralisée dans `core/config.py`. Mets à jour `core/routing/model_router.py` pour utiliser ces SDKs. Déplace les anciens drivers CLI vers `core/drivers/legacy_cli/`.

### Epic 2.2 : Mode Headless Robuste pour l'Automatisation
* **Action :** Refactorise `core/interaction/headless_provider.py`. L'exécution via `python nexus7.py --headless --task "..."` doit s'exécuter **sans aucune** invite interactive TTY (bypasser `prompt_toolkit`), et générer un résultat JSON déterministe avec un `exit code` strict (0 ou 1) pour les CI/CD.

---

## 🧠 PHASE 3 : PERSISTANCE D'ÉTAT ET MULTI-TENANCY
*Objectif : Rendre le Swarm résilient aux crashs et isoler les utilisateurs.*

### Epic 3.1 : Event Sourcing de la FSM et Crash Recovery
* **`[WEB-RESEARCH-REQUIRED]`** : Recherche "Python distributed state machine event sourcing Redis 2026".
* **Problème :** L'état du FSM (`TaskExecutionContext`) est en RAM. Un crash détruit le travail en cours.
* **Action :** Connecte le FSM à `core/events/redis_bus.py`. À chaque transition d'état (ex: `IDLE` -> `BRAINSTORMING`), sérialise l'état et sauvegarde-le dans Redis.
* **Action :** Implémente un mécanisme de *Crash Recovery* au boot de `nexus7.py`. Le système doit détecter les sessions interrompues et proposer de les restaurer.

### Epic 3.2 : Isolation Multi-Tenant de la Mémoire
* **Action :** Dans `core/memory/project_memory.py` et le moteur LanceDB, force l'utilisation de `core/memory/namespace_manager.py`.
* **Action :** Lie le contexte JWT de FastAPI (Tenant ID / Workspace ID) aux requêtes d'indexation et de récupération. Un agent ne doit jamais pouvoir interroger l'index global en mode API sans le filtre de son locataire (Tenant).

---

## 🛡️ PHASE 4 : SANDBOXING PHYSIQUE ET STANDARDS A2A
*Objectif : Isoler l'exécution de code malveillant et s'ouvrir aux autres orchestrateurs.*

### Epic 4.1 : Sandboxing OS-Level via MCP
* **`[WEB-RESEARCH-REQUIRED]`** : Recherche "E2B SDK python 2026 sandbox" ou "Docker SDK Python ephemeral containers for LLM code execution".
* **Action :** Refactorise `core/execution/handlers/bash_handler.py`. L'exécution de code généré par l'IA ne doit plus se faire sur l'hôte.
* **Action :** Déporte cette exécution vers des conteneurs Docker éphémères ou des MicroVMs E2B, isolés du réseau. L'Orchestrateur NEXUS doit communiquer avec ce Sandbox exclusivement via le protocole MCP.

### Epic 4.2 : Protocole A2A et Client MCP Dynamique
* **`[WEB-RESEARCH-REQUIRED]`** : Recherche "A2A Agent Protocol v0.3 Linux Foundation Python" et "MCP Client SDK Python 2026".
* **Action :** Implémente un Client MCP dynamique dans `core/mcp/client.py` permettant à NEXUS de découvrir et de s'interfacer de manière autonome avec des serveurs MCP externes.
* **Action :** Ajoute une "Agent Card JSON" A2A au Serveur MCP de NEXUS pour le rendre interopérable avec des frameworks externes.

---

## 🧬 PHASE 5 : ÉVOLUTION DÉTERMINISTE ET OBSERVABILITÉ
*Objectif : Empêcher l'hallucination lors de l'auto-amélioration et préparer la production.*

### Epic 5.1 : Fitness Function Mathématique pour l'Évolution
* **Problème :** Le `TieredValidator` utilise un LLM pour évaluer les mutations de code d'un autre LLM (risque de *Model Collapse*).
* **Action :** Refactorise `core/evolution/promote.py`. Une mutation ne peut être promue QUE SI :
  1. L'arbre syntaxique (AST) est compilable.
  2. L'exécution de `pytest tests/` retourne un `exit code 0` dans la Sandbox.
* **Action :** Mets à jour `LINEAGE.json` dynamiquement avec les hashs SHA256 parents/enfants à chaque promotion réussie.

### Epic 5.2 : OpenTelemetry (OTLP) et Conteneurisation
* **`[WEB-RESEARCH-REQUIRED]`** : Recherche "OpenTelemetry Python semantic conventions for LLM GenAI 2026".
* **Action :** Câble `core/telemetry/exporter.py` sur le SDK OpenTelemetry (réfère-toi à `OPENTELEMETRY_IMPLEMENTATION_GUIDE.md`). Trace les latences SDK, la consommation de tokens (`budget_tracker.py`), et les changements d'états FSM.
* **Action :** Crée un `Dockerfile` multi-stage pour le backend (NEXUS Core + CEREBRO API) et un pour le frontend (`interface/ui/cerebro`).
* **Action :** Crée un `docker-compose.yml` de production orchestrant `redis`, `nexus-backend`, et `nexus-frontend`.
* **Action :** Ajoute un `Makefile` à la racine (`make install`, `make test`, `make run-prod`).

---
**[FIN DU PLAN DIRECTEUR]**

**INSTRUCTIONS POUR CLAUDE CODE :**
Accuse réception de ce plan. Confirme que tu as bien compris l'interdiction de te fier uniquement à tes poids d'entraînement pour les technologies de 2026, et l'obligation de travailler méthodiquement Epic par Epic en mode TDD. 
Commence immédiatement par la **PHASE 1, Epic 1.1**. Fournis un rapport d'exécution des tests avant de demander l'autorisation de passer à l'Epic 1.2.